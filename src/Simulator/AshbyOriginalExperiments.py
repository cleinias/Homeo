'''
Replication of Ashby's 7 original Homeostat experiments from
*Design for a Brain* (2nd ed., 1960).

Each setup function returns (homeostat, seed, metadata_dict).
All seed both numpy.random and random before any stochastic initialization.

The event-driven run loop (run_with_events) replaces Homeostat.runFor()
when mid-run perturbations are needed (polarity reversal, stimulus
injection, constraint changes).

@author: stefano (with Claude)
'''

import os
import sys
import time
import random
import numpy as np

from Core.Homeostat import Homeostat
from Core.HomeoUnit import HomeoUnit
from Core.HomeoUnitNewtonian import HomeoUnitNewtonian
from Core.HomeoConnection import HomeoConnection
from Core.HomeoUniselectorAshby import HomeoUniselectorAshby
from Core.HomeoJIT import seed_jit_rng
from Helpers.HomeostatConditionLogger import (
    log_homeostat_conditions, log_homeostat_conditions_json)


# ---------------------------------------------------------------
#  RNG seeding helper
# ---------------------------------------------------------------

def _seed_rngs(seed):
    '''Seed both numpy.random and random.  If seed is None, generate one.
    Also clear unit name registry to allow repeated experiment creation.
    '''
    if seed is None:
        seed = int.from_bytes(os.urandom(4), 'big')
    np.random.seed(seed)
    random.seed(seed)
    seed_jit_rng(seed)          # numba's own stream, used by headless runs
    HomeoUnit.allNames.clear()
    return seed


# ---------------------------------------------------------------
#  Stability tracker
# ---------------------------------------------------------------

class StabilityTracker:
    '''Track whether all active units have stayed within bounds.

    Call check(tick) every tick.  stability_achieved_at will be set to the
    first tick at which window consecutive non-critical ticks were observed.
    total_uniselector_firings counts only the firings of units that have an
    input their uniselector can re-draw; the others change nothing.
    '''

    def __init__(self, homeostat, window=200, burn_in=None):
        self.hom = homeostat
        self.window = window
        self.burn_in = burn_in if burn_in is not None else window
        self._run = 0
        self.stability_achieved_at = None
        self.last_stability_at = None
        self.currently_stable = False
        self.total_uniselector_firings = 0

    def _is_critical(self, unit):
        '''Check if a unit's current deviation is beyond the critical threshold.

        Cannot use essentialVariableIsCritical() because it checks
        nextDeviation, which has been reset to 0 after selfUpdate().
        '''
        thresh = unit.critThreshold * unit.maxDeviation
        return (unit.criticalDeviation >= thresh or
                unit.criticalDeviation <= -thresh)

    def check(self, tick):
        any_critical = False
        for u in self.hom.homeoUnits:
            if u.isActive():
                if u.uniselectorActivated and has_adaptive_input(u):
                    self.total_uniselector_firings += 1
                if self._is_critical(u):
                    any_critical = True
        if not any_critical:
            self._run += 1
        else:
            self._run = 0
            self.currently_stable = False
        if self._run >= self.window:
            stable_since = tick - self.window
            if stable_since >= self.burn_in:
                if self.stability_achieved_at is None:
                    self.stability_achieved_at = stable_since
                self.last_stability_at = stable_since
                self.currently_stable = True


# ---------------------------------------------------------------
#  Simple per-tick state logger for pure Ashby experiments
# ---------------------------------------------------------------

class AshbyStateLogger:
    '''Lightweight per-tick TSV logger for non-robotic Ashby experiments.

    Logs: tick, per-unit (critDev, output, velocity, uniselector_fired),
    and per-connection signed weights.
    '''

    def __init__(self, homeostat, filepath, seed=None, log_interval=1):
        self._hom = homeostat
        self._interval = max(1, int(log_interval))
        self._units = [u for u in homeostat.homeoUnits if u.isActive()]
        self._unit_names = [u.name for u in self._units]

        # Build connection column info
        self._conn_keys = []
        self._conn_refs = []
        for unit in self._units:
            for conn in unit.inputConnections:
                if conn.isActive() and conn.incomingUnit.isActive():
                    col = 'w_%s<-%s' % (unit.name, conn.incomingUnit.name)
                    self._conn_keys.append(col)
                    self._conn_refs.append(conn)

        # Build column header
        cols = ['tick']
        for name in self._unit_names:
            cols += ['%s_critDev' % name, '%s_output' % name,
                     '%s_velocity' % name, '%s_unisel_fired' % name]
        cols += self._conn_keys
        self._columns = cols

        self._f = open(filepath, 'w')
        self._f.write('# AshbyExperimentLog v1\n')
        self._f.write('# date\t%s\n' % time.strftime('%Y-%m-%d %H:%M:%S'))
        if seed is not None:
            self._f.write('# seed\t%d\n' % seed)
        self._f.write('# n_units\t%d\n' % len(self._units))
        for unit in self._units:
            prefix = '# unit_%s' % unit.name
            self._f.write('%s_mass\t%.6f\n' % (prefix, unit.mass))
            self._f.write('%s_viscosity\t%.6f\n' % (prefix, unit.viscosity))
            self._f.write('%s_maxDeviation\t%.6f\n' % (prefix, unit.maxDeviation))
            self._f.write('%s_noise\t%.6f\n' % (prefix, unit.noise))
            self._f.write('%s_potentiometer\t%.6f\n' % (prefix, unit.potentiometer))
            self._f.write('%s_switch\t%d\n' % (prefix, unit.switch))
            self._f.write('%s_uniselectorActive\t%s\n' % (
                prefix, unit.uniselectorActive))
            self._f.write('%s_uniselectorTimeInterval\t%d\n' % (
                prefix, unit.uniselectorTimeInterval))
        self._f.write('\t'.join(self._columns) + '\n')
        self._f.flush()

    def log_tick(self, tick):
        if tick % self._interval != 0:
            return
        vals = ['%d' % tick]
        for unit in self._units:
            vals.append('%.6f' % unit.criticalDeviation)
            vals.append('%.6f' % unit.currentOutput)
            vals.append('%.6f' % unit.currentVelocity)
            vals.append('%d' % unit.uniselectorActivated)
        for conn in self._conn_refs:
            vals.append('%.6f' % (conn.weight * conn.switch))
        self._f.write('\t'.join(vals) + '\n')

    def flush(self):
        self._f.flush()

    def close(self):
        if self._f and not self._f.closed:
            self._f.flush()
            self._f.close()


# ---------------------------------------------------------------
#  Event-driven run loop
# ---------------------------------------------------------------

def run_with_events(hom, total_ticks, events=None, tick_callback=None,
                    state_logger=None, stability_tracker=None):
    '''Run homeostat with scheduled mid-run events.

    Parameters:
        hom:              Homeostat instance
        total_ticks:      total number of ticks to simulate
        events:           sorted list of (tick, callable(hom)) pairs
        tick_callback:    called every tick with (hom, tick) for custom logic
        state_logger:     AshbyStateLogger instance (optional)
        stability_tracker: StabilityTracker instance (optional)

    The loop replicates the logic of Homeostat.runFor() but adds event
    dispatch and per-tick callbacks.
    '''
    if events is None:
        events = []
    # Sort events by tick
    events = sorted(events, key=lambda e: e[0])
    event_idx = 0

    if hom.time is None:
        hom.time = 0

    # Log initial state (tick 0)
    if state_logger is not None:
        state_logger.log_tick(0)

    while hom.time < total_ticks:
        # Dispatch any events scheduled for this tick
        while event_idx < len(events) and events[event_idx][0] <= hom.time:
            events[event_idx][1](hom)
            event_idx += 1

        # Per-tick callback (e.g. for trainer logic)
        if tick_callback is not None:
            tick_callback(hom, hom.time)

        # Update all active units
        for unit in hom.homeoUnits:
            if hom.collectsData:
                hom.dataCollector.atTimeIndexAddDataUnitForAUnit(hom.time, unit)
            unit.time = hom.time
            if unit.isActive():
                unit.selfUpdate()

        hom.time += 1

        # Log state after update
        if state_logger is not None:
            state_logger.log_tick(hom.time)

        # Check stability
        if stability_tracker is not None:
            stability_tracker.check(hom.time)


# ---------------------------------------------------------------
#  Utility functions
# ---------------------------------------------------------------

def inject_stimulus(hom, unit_index, delta):
    '''The operator displaces a unit's needle by delta (within its range).'''
    unit = hom.homeoUnits[unit_index]
    unit.criticalDeviation = np.clip(unit.criticalDeviation + delta,
                                     -unit.maxDeviation, unit.maxDeviation)
    unit.computeOutput()


def has_adaptive_input(unit):
    '''True if the unit's uniselector has an input to re-draw: an active
    connection in the 'uniselector' state from an active unit.'''
    return any(conn.isActive() and conn.state == 'uniselector' and conn.incomingUnit.isActive()
               for conn in unit.inputConnections)


def connection(to_unit, from_unit):
    '''The connection from_unit -> to_unit (stored on to_unit).'''
    return find_connection(to_unit, from_unit)[1]


def reverse_link(hom, from_index, to_index):
    '''Reverse the polarity of the connection from_index -> to_index (the
    operator throwing a hand-controlled commutator).'''
    units = hom.homeoUnits
    conn = connection(units[to_index], units[from_index])
    conn.newWeight(conn.weight * conn.switch * -1)


def reverse_connection(unit, conn_index):
    '''Flip the switch (polarity) of a specific connection.'''
    conn = unit.inputConnections[conn_index]
    conn.newWeight(conn.weight * conn.switch * -1)


def find_connection(unit, from_unit):
    '''Find the connection on unit coming from from_unit. Returns (index, conn).'''
    for i, conn in enumerate(unit.inputConnections):
        if conn.incomingUnit is from_unit:
            return i, conn
    return None, None


def ashby_matrix(units):
    '''Ashby's matrix A of the m -> 0 limit (DfB 19/11) for the given units:
    dx/dt is proportional to A x, A[i, j] the signed weight of j -> i over
    j's maxDeviation (Homeo's output scaling).  Inactive connections and
    connections from units outside the list count as 0.'''
    A = np.zeros((len(units), len(units)))
    for i, u in enumerate(units):
        for j, v in enumerate(units):
            conn = connection(u, v)
            if conn is not None and conn.isActive():
                A[i, j] = conn.weight * conn.switch / v.maxDeviation
    return A


def ashby_stable(A):
    '''Stable in the m -> 0 limit: every eigenvalue of A has negative real part.'''
    return bool(np.max(np.linalg.eigvals(A).real) < 0)


def _make_unit(name, mass=100, viscosity=None, noise=None,
               potentiometer=None, switch=-1,
               uniselector_active=True, uniselector_interval=100,
               maxDeviation=None, randomize_init=True):
    '''Create and configure a HomeoUnitNewtonian.

    Uses setRandomValues() to initialize the unit with random parameters
    (as Ashby's machine would be), then overrides specific values as needed.
    '''
    unit = HomeoUnitNewtonian()
    unit.setRandomValues()
    unit.name = name
    unit.mass = mass
    if viscosity is not None:
        unit.viscosity = viscosity
    if noise is not None:
        unit.noise = noise
    if potentiometer is not None:
        unit.potentiometer = potentiometer
    unit.switch = switch
    unit.uniselectorActive = uniselector_active
    unit.uniselectorTimeInterval = uniselector_interval
    if maxDeviation is not None:
        unit.maxDeviation = maxDeviation
    return unit


def _add_unused_slots(hom, n_slots=4):
    '''Fill the homeostat up to n_slots units with inactive ones (Ashby's
    machine had four units; the GUI shows four).  The unused units and all
    their connections, in both directions, are switched off.'''
    for i in range(len(hom.homeoUnits), n_slots):
        unit = HomeoUnitNewtonian()
        unit.name = 'UNUSED_%d' % (i + 1)
        hom.addFullyConnectedUnit(unit)
        unit.disactivate()
    for unit in hom.homeoUnits:
        for conn in unit.inputConnections:
            if not unit.isActive() or not conn.incomingUnit.isActive():
                conn.status = False


def _disable_all_cross_connections(hom):
    '''Disable all non-self connections in the homeostat.'''
    for unit in hom.homeoUnits:
        for i in range(1, len(unit.inputConnections)):
            unit.inputConnections[i].status = False


def _enable_connection(from_unit, to_unit, weight=None, state='uniselector',
                       noise=0.05):
    '''Enable and configure the connection from from_unit to to_unit.

    If weight is None, the connection keeps whatever random weight it
    was initialized with (appropriate for uniselector-controlled connections).
    If weight is given, it is set explicitly (appropriate for manual connections
    where the sign/magnitude matters).
    '''
    for conn in to_unit.inputConnections:
        if conn.incomingUnit is from_unit:
            if weight is not None:
                conn.newWeight(weight)
            conn.state = state
            conn.noise = noise
            conn.status = True
            return conn
    return None


# ===============================================================
#  EXPERIMENT 1: Basic Ultrastability (DftB 8/4, Fig. 8/4/1)
# ===============================================================

# Exp 1 parameters (see setup_exp1_basic_ultrastability)
EXP1_VISCOSITY = 10
EXP1_SELF_FEEDBACK_2 = (0.5, 1.0)
EXP1_HAND_12 = -1.0
# Protocol (ticks): operator displacements D of unit 2 and reversals R of 1->2
EXP1_DISPLACEMENT = 5.0
EXP1_D1, EXP1_R1, EXP1_D2, EXP1_R2, EXP1_D3, EXP1_END = 1000, 1500, 5000, 5500, 9000, 9600


def setup_exp1_basic_ultrastability(seed=None, unused_slots=False):
    '''Two units, 1 <-> 2, as in Fig. 8/4/1 (DfB 8/4, Ashby's analogue of
    the crossed-muscle operations of Marina and Sperry).

    "The effect 1 -> 2 was hand-controlled, and 2 -> 1 was
    uniselector-controlled": 1->2 is set by hand (and reversed by the
    operator at R1 and R2); 2->1 is re-drawn by unit 1's uniselector.
    Before R1 the operator's upstroke of 2 moves 1 up, so 2->1 starts
    positive and 1->2 is negative (a stable, negative loop).  Each reversal
    makes the loop positive; unit 1's uniselector then changes 2->1 until
    the system is stable again, with 2->1 reversed: "This reversal
    compensated for the reversal of 1 -> 2".

    Ashby does not state the self-feedback.  Unit 1 (whose uniselector must
    act) has none and unit 2 has 0.5-1: then the field is stable if and only
    if the loop is negative, so every restabilising uniselector value is a
    compensating one.  With self-feedback on both units most reversals are
    simply absorbed; with it on unit 1 only, unit 1 settles inside its limits
    while 2 is pinned and nothing adapts.  Strongly damped units (Ashby's
    m -> 0, DfB 19/11).  Over 30 seeds the protocol of
    run_ashby_original_experiments.py gives Ashby's full sequence in 29.

    unused_slots: add inactive units up to four (for the GUI).

    Returns: (homeostat, seed, metadata)
    '''
    seed = _seed_rngs(seed)

    hom = Homeostat()
    unit1 = _make_unit('Unit_1', viscosity=EXP1_VISCOSITY,
                       uniselector_active=True, uniselector_interval=100)
    unit2 = _make_unit('Unit_2', viscosity=EXP1_VISCOSITY, uniselector_active=False,
                       potentiometer=np.random.uniform(*EXP1_SELF_FEEDBACK_2))
    for u in [unit1, unit2]:
        hom.addFullyConnectedUnit(u)
    if unused_slots:
        _add_unused_slots(hom)

    _disable_all_cross_connections(hom)
    unit1.disactivateSelfConn()

    # 2->1: re-drawn by unit 1's uniselector, starting positive
    conn = _enable_connection(unit2, unit1, state='uniselector')
    conn.newWeight(abs(conn.weight))
    # 1->2: hand-controlled, negative
    _enable_connection(unit1, unit2, weight=EXP1_HAND_12, state='manual')

    metadata = {
        'experiment': 'Exp 1: Basic Ultrastability',
        'reference': 'DftB 8/4, Fig. 8/4/1',
        'topology': '2 units: 1->2 hand-controlled, 2->1 on unit 1\'s uniselector',
        'description': ('Reverse 1->2 by hand (R1, R2); unit 1\'s uniselector '
                        'reverses 2->1 in compensation'),
    }
    return hom, seed, metadata


def exp1_reversal_event(hom):
    '''Reverse the polarity of the hand-controlled 1->2.'''
    reverse_link(hom, 0, 1)


def exp1_displacement_event(hom):
    '''The operator displaces unit 2 upward (D in Fig. 8/4/1).'''
    inject_stimulus(hom, 1, EXP1_DISPLACEMENT)


def exp1_events():
    '''Fig. 8/4/1\'s protocol: D1, R1, D2, R2, D3.  Reversals are 4000 ticks
    apart: a runaway takes some 1000-1600 ticks to reach the critical level.'''
    return [(EXP1_D1, exp1_displacement_event), (EXP1_R1, exp1_reversal_event),
            (EXP1_D2, exp1_displacement_event), (EXP1_R2, exp1_reversal_event),
            (EXP1_D3, exp1_displacement_event)]


# ===============================================================
#  EXPERIMENT 2: Self-Reorganization in 3-Unit Circle (DftB 8/5)
# ===============================================================

# Exp 2 parameters (see setup_exp2_self_reorganization)
EXP2_VISCOSITY = 10
EXP2_SELF_FEEDBACK = (0.5, 1.0)


def setup_exp2_self_reorganization(seed=None):
    '''3 units in a ring: 1->2->3->1.

    Connection 3->1: fixed negative (manual): "a movement of 3 made 1 move
    in the opposite direction".
    Connection 1->2: uniselector-controlled.
    Connection 2->3: hand-controlled (manual), reversed mid-run (at R in
    Fig. 8/5/1), after Sperry's crossing of nerves to antagonist muscles.

    The units are named by Ashby's numbers only.  Ashby does not say which
    of them, if any, stands for an environment, and reading them as sensor,
    motor and environment led this setup astray before.

    Unit 1: no uniselector.
    Unit 2: has the uniselector; no self-connection.
    Unit 3: no uniselector.

    The parameters follow Ashby's own analysis of the machine (DfB 19/11):
    he lets the needle's inertia go to zero against the friction of the vane
    (m -> 0), so the units are strongly damped (viscosity 10).  Units 1 and 3
    have negative self-feedback of strength 0.5-1, which makes the starting
    ring stable for any 1->2 weight; unit 2 has none, so that when R turns
    the ring into a vicious circle unit 2 is driven to its limit and its
    uniselector acts (with self-feedback it settles inside its limits while
    1 and 3 are pinned, and nothing can adapt).  1->2 starts positive: in
    Ashby's starting state "2 followed 1".  Over 30 seeds this gives Ashby's
    sequence (stable, destabilised by R, restabilised with 1->2 reversed by
    the uniselector) in 27.

    A uniselector re-draws its own unit's input connections, so the
    uniselector that controls 1->2 is unit 2's ("the action 1 to 2 was
    uniselector controlled", DftB 8/5).  Unit 1's inputs are all fixed or
    hand-controlled, so its uniselector would have nothing to act on.

    The 4th unit is created but deactivated (Ashby's hardware had 4 slots).

    Returns: (homeostat, seed, metadata)
    '''
    seed = _seed_rngs(seed)

    hom = Homeostat()

    # Create 4 units (one will be inactive)
    unit1 = _make_unit('Unit_1', viscosity=EXP2_VISCOSITY, uniselector_active=False,
                       potentiometer=np.random.uniform(*EXP2_SELF_FEEDBACK))
    unit2 = _make_unit('Unit_2', viscosity=EXP2_VISCOSITY,
                       uniselector_active=True, uniselector_interval=100)
    unit3 = _make_unit('Unit_3', viscosity=EXP2_VISCOSITY, uniselector_active=False,
                       potentiometer=np.random.uniform(*EXP2_SELF_FEEDBACK))
    unit4 = HomeoUnitNewtonian()
    unit4.name = 'UNUSED'

    for u in [unit1, unit2, unit3, unit4]:
        hom.addFullyConnectedUnit(u)

    # Deactivate unit 4
    unit4.disactivate()

    # Disable all cross-connections
    _disable_all_cross_connections(hom)

    # Unit 2 has no self-feedback
    unit2.disactivateSelfConn()

    # Wire the ring: 1->2->3->1
    # Unit 1 receives from unit 3 (3->1): fixed negative
    _enable_connection(unit3, unit1, weight=-0.5, state='manual')

    # Unit 2 receives from unit 1 (1->2): controlled by unit 2's uniselector,
    # starting positive
    conn = _enable_connection(unit1, unit2, state='uniselector')
    conn.newWeight(abs(conn.weight))

    # Unit 3 receives from unit 2 (2->3): hand-controlled, positive
    _enable_connection(unit2, unit3, weight=0.5, state='manual')

    metadata = {
        'experiment': 'Exp 2: Self-Reorganization (3-Unit Circle)',
        'reference': 'DftB 8/5, Fig. 8/5/1',
        'topology': '3 units in ring: 1->2->3->1',
        'description': ('At reversal event, polarity of 2->3 '
                         "is flipped; unit 2's uniselector re-draws "
                         '1->2 and compensates'),
    }
    return hom, seed, metadata


def exp2_reversal_event(hom):
    '''Reverse polarity of the 2->3 connection (hand-controlled).'''
    unit3 = hom.homeoUnits[2]
    unit2 = hom.homeoUnits[1]
    _, conn = find_connection(unit2, unit3)
    if conn is None:
        # Connection is on unit3 receiving from unit2
        _, conn = find_connection(unit3, unit2)
    if conn is not None:
        # Reverse the connection by swapping to opposite sign
        for c in unit3.inputConnections:
            if c.incomingUnit is unit2:
                c.newWeight(c.weight * c.switch * -1)
                break


# ===============================================================
#  EXPERIMENT 3: Training by Punishment (DftB 8/9)
# ===============================================================

def setup_exp3_training(seed=None):
    '''3 units in a triangle with an external "trainer".

    Units: 1 (tested), 2 (tested), 3 (receives punishment).
    Connection 1->2: under uniselector control.
    Trainer rule: if 1 and 2 move in the same direction, force 3 to extreme.

    The "trainer" is implemented as a tick_callback.

    Returns: (homeostat, seed, metadata)
    '''
    seed = _seed_rngs(seed)

    hom = Homeostat()

    unit1 = _make_unit('Unit_1', uniselector_active=True, uniselector_interval=100)
    unit2 = _make_unit('Unit_2', uniselector_active=True, uniselector_interval=100)
    unit3 = _make_unit('Unit_3', uniselector_active=False)

    for u in [unit1, unit2, unit3]:
        hom.addFullyConnectedUnit(u)

    _disable_all_cross_connections(hom)

    # Wire: 1->2 (uniselector), 2->3 (manual), 3->1 (manual)
    _enable_connection(unit1, unit2, state='uniselector')
    _enable_connection(unit2, unit3, weight=0.5, state='manual')
    _enable_connection(unit3, unit1, weight=-0.5, state='manual')

    metadata = {
        'experiment': 'Exp 3: Training by Punishment',
        'reference': 'DftB 8/9, Fig. 8/9/1',
        'topology': '3 units: 1->2->3->1 with trainer T',
        'description': ('Trainer punishes when 1 and 2 move in same direction '
                         'by forcing 3 to extreme'),
    }
    return hom, seed, metadata


def make_trainer_callback(punishment_log=None):
    '''Return a tick_callback implementing the trainer rule.

    Rule: if unit 1 and unit 2 moved in the same direction since last check,
    force unit 3 to maxDeviation (punishment).

    The trainer checks every `check_interval` ticks.
    '''
    state = {'prev_dev_1': None, 'prev_dev_2': None, 'punishment_count': 0}
    if punishment_log is None:
        punishment_log = []

    def trainer(hom, tick):
        u1 = hom.homeoUnits[0]
        u2 = hom.homeoUnits[1]
        u3 = hom.homeoUnits[2]

        d1 = u1.criticalDeviation
        d2 = u2.criticalDeviation

        if state['prev_dev_1'] is not None:
            delta1 = d1 - state['prev_dev_1']
            delta2 = d2 - state['prev_dev_2']
            # Same direction: both positive or both negative
            if delta1 * delta2 > 0 and (abs(delta1) > 0.01 and abs(delta2) > 0.01):
                # Punish: force unit 3 to extreme
                u3.criticalDeviation = u3.maxDeviation * 0.95
                state['punishment_count'] += 1
                punishment_log.append(tick)

        state['prev_dev_1'] = d1
        state['prev_dev_2'] = d2

    return trainer, punishment_log


# ===============================================================
#  EXPERIMENT 4: Alternating Environments (DftB 8/10)
# ===============================================================

# Exp 4 parameters (see setup_exp4_alternating_environments)
EXP4_VISCOSITY = 10
EXP4_SELF_FEEDBACK_1 = (0.2, 0.5)
EXP4_SELF_FEEDBACK_2 = (0.9, 1.0)
EXP4_H = 1.0
# Protocol (ticks): settle, then reverse H every interval
EXP4_SETTLE, EXP4_INTERVAL, EXP4_REVERSALS = 5000, 8000, 6
EXP4_END = EXP4_SETTLE + EXP4_REVERSALS * EXP4_INTERVAL + 1000


def setup_exp4_alternating_environments(seed=None, unused_slots=False):
    '''2 units with a hand-controlled commutator H that alternates polarity.

    "Let the Homeostat be arranged so that it is partly under uniselector-,
    and partly under hand-, control ... Select a commutator switch, and from
    time to time reverse its polarity" (DfB 8/10).  Ashby records units 1
    and 2 only; the arrangement follows Fig. 8/4/1: H is the hand-set 1->2
    (|H| = 1), and 2->1 is re-drawn by unit 1's uniselector.  Unit 2 has no
    input a uniselector could re-draw, so its uniselector is off.  The first
    field "terminal for both" values of H is retained.

    In Ashby's m -> 0 limit (DfB 19/11) the field is stable for both signs of
    H iff p1 p2 > |2->1| |H|, with p1, p2 the units' negative self-feedback:
    both units need some (unlike Exps 1 and 2).  Unit 2's self-feedback is
    at least 0.9 |H|: with less, after a reversal unit 2 can be pinned at its
    limit while unit 1 settles inside its own, and nothing adapts.  Strongly
    damped units.  Ashby's start: 2->1 is stable for the first position of H
    and unstable for the second, as in Fig. 8/10/1.  With reversals every
    8000 ticks (a runaway can take thousands of ticks to reach the critical
    level, and H must be "sustained long enough so that the change does not
    interrupt the process of trial and error") Ashby's sequence appears in
    20 of 30 seeds (stable before the first reversal, changes after it, a
    field stable for both H kept through at least three reversals).

    unused_slots: add inactive units up to four (for the GUI).

    Returns: (homeostat, seed, metadata)
    '''
    seed = _seed_rngs(seed)

    hom = Homeostat()
    p1 = np.random.uniform(*EXP4_SELF_FEEDBACK_1)
    p2 = np.random.uniform(*EXP4_SELF_FEEDBACK_2)
    unit1 = _make_unit('Unit_1', viscosity=EXP4_VISCOSITY, potentiometer=p1,
                       uniselector_active=True, uniselector_interval=100)
    unit2 = _make_unit('Unit_2', viscosity=EXP4_VISCOSITY, potentiometer=p2,
                       uniselector_active=False)
    for u in [unit1, unit2]:
        hom.addFullyConnectedUnit(u)
    if unused_slots:
        _add_unused_slots(hom)

    _disable_all_cross_connections(hom)
    # 1->2: the commutator H, hand-controlled
    _enable_connection(unit1, unit2, weight=EXP4_H, state='manual')
    # 2->1: unit 1's uniselector; Ashby's start: stable for this H, not for -H
    conn = _enable_connection(unit2, unit1, state='uniselector')
    q = p1 * p2 / EXP4_H
    conn.newWeight(-np.sign(EXP4_H) * np.random.uniform(min(q, 1), 1))

    metadata = {
        'experiment': 'Exp 4: Alternating Environments',
        'reference': 'DftB 8/10, Fig. 8/10/1',
        'topology': '2 units: 1->2 the commutator H (by hand), 2->1 on unit 1\'s uniselector',
        'description': ('Periodically reverse H; the first field stable for '
                         'both polarities is retained'),
    }
    return hom, seed, metadata


def exp4_reversal_event(hom):
    '''Reverse the commutator H (1->2).'''
    reverse_link(hom, 0, 1)


def make_alternation_events(interval=EXP4_INTERVAL, n_reversals=EXP4_REVERSALS,
                            start=EXP4_SETTLE):
    '''Return events that reverse the commutator H, the first at start and
    then every interval ticks.'''
    return [(start + i * interval, exp4_reversal_event) for i in range(n_reversals)]


def exp4_stable_for_both(hom):
    '''Whether the current field is stable for both positions of H, in
    Ashby's m -> 0 limit.'''
    units = hom.homeoUnits[:2]
    stable = []
    for i in range(2):
        stable.append(ashby_stable(ashby_matrix(units)))
        exp4_reversal_event(hom)
    return all(stable)


# ===============================================================
#  EXPERIMENT 5: Constraint / Glass Fibre (DftB 8/11)
# ===============================================================

def setup_exp5_constraint(seed=None):
    '''3 units, with units 1 and 2 constrained to move together
    (glass fibre) from the start.

    At a scheduled event, the constraint is removed, demonstrating
    that the adapted parameters depended on the constraint.

    Returns: (homeostat, seed, metadata)
    '''
    seed = _seed_rngs(seed)

    hom = Homeostat()

    unit1 = _make_unit('Unit_1', uniselector_active=True, uniselector_interval=100)
    unit2 = _make_unit('Unit_2', uniselector_active=True, uniselector_interval=100)
    unit3 = _make_unit('Unit_3', uniselector_active=True, uniselector_interval=100)

    for u in [unit1, unit2, unit3]:
        hom.addFullyConnectedUnit(u)

    metadata = {
        'experiment': 'Exp 5: Constraint (Glass Fibre)',
        'reference': 'DftB 8/11, Fig. 8/11/1',
        'topology': '3 fully connected units, 1 and 2 constrained to move together',
        'description': ('Join units 1-2 with constraint. Let stabilize. '
                         'Remove constraint at R to show instability.'),
    }
    return hom, seed, metadata


def make_constraint_callback(leader_idx=0, follower_idx=1, active=True):
    '''Return a tick_callback that forces the follower to track the leader.

    Call release_constraint_flag[0] = False to deactivate mid-run.
    '''
    flag = [active]  # mutable container so events can toggle it

    def constrain(hom, tick):
        if flag[0]:
            leader = hom.homeoUnits[leader_idx]
            follower = hom.homeoUnits[follower_idx]
            follower.criticalDeviation = leader.criticalDeviation
            follower.currentVelocity = leader.currentVelocity

    return constrain, flag


# ===============================================================
#  EXPERIMENT 6: Habituation (DftB 14/6)
# ===============================================================

def setup_exp6_habituation(seed=None):
    '''2 units joined: 1->2. Connection 1->2 under uniselector control.

    Repeatedly displace unit 1 by a fixed angle (stimulus D).
    Observe that unit 2's response amplitude decreases over trials.

    Returns: (homeostat, seed, metadata)
    '''
    seed = _seed_rngs(seed)

    hom = Homeostat()

    unit1 = _make_unit('Unit_1', uniselector_active=True, uniselector_interval=100)
    unit2 = _make_unit('Unit_2', uniselector_active=True, uniselector_interval=100)

    for u in [unit1, unit2]:
        hom.addFullyConnectedUnit(u)

    # Connection 1->2: uniselector-controlled (keep random weight)
    for conn in unit2.inputConnections:
        if conn.incomingUnit is unit1:
            conn.state = 'uniselector'

    # Connection 2->1: manual (fixed negative, feedback)
    for conn in unit1.inputConnections:
        if conn.incomingUnit is unit2:
            conn.newWeight(-0.3)
            conn.state = 'manual'

    metadata = {
        'experiment': 'Exp 6: Habituation',
        'reference': 'DftB 14/6, Figs. 14/6/1 and 14/6/2',
        'topology': '2 units joined: 1<->2',
        'description': ('Repeatedly displace unit 1 by fixed angle D; '
                         'observe unit 2 response amplitude diminishing'),
    }
    return hom, seed, metadata


def make_stimulus_events(unit_index=0, delta=5.0, interval=300,
                         n_stimuli=10, settle_first=500):
    '''Return events that inject repeated stimuli into a unit.

    First stimulus at tick settle_first, then every interval ticks.
    '''
    events = []
    for i in range(n_stimuli):
        tick = settle_first + i * interval

        def stimulus(hom, _delta=delta, _unit_index=unit_index):
            inject_stimulus(hom, _unit_index, _delta)

        events.append((tick, stimulus))
    return events


class ResponseMeasurer:
    '''Measure peak response amplitude of a target unit after each stimulus.

    Call check(tick) every tick.  After each stimulus, tracks the peak
    deviation of the target unit over a measurement window.
    '''

    def __init__(self, hom, target_unit_index=1, stimulus_ticks=None,
                 measure_window=100):
        self.hom = hom
        self.target_idx = target_unit_index
        self.stimulus_ticks = set(stimulus_ticks or [])
        self.measure_window = measure_window
        self.responses = []
        self._measuring = False
        self._measure_start = 0
        self._baseline = 0.0
        self._peak = 0.0

    def check(self, tick):
        unit = self.hom.homeoUnits[self.target_idx]
        dev = unit.criticalDeviation

        if tick in self.stimulus_ticks:
            self._measuring = True
            self._measure_start = tick
            self._baseline = dev
            self._peak = 0.0

        if self._measuring:
            amplitude = abs(dev - self._baseline)
            if amplitude > self._peak:
                self._peak = amplitude
            if tick - self._measure_start >= self.measure_window:
                self.responses.append(self._peak)
                self._measuring = False


# ===============================================================
#  EXPERIMENT 7: Multistable System (DftB 16/8)
# ===============================================================

def setup_exp7_multistable(seed=None):
    '''3 units: 2<->1<->3 with conditional connectivity.

    Units 2 and 3 are constrained to move only downward (one-directional).
    Unit 1 can move freely.  When unit 1 is "above the line" it interacts
    with unit 2; when "below" it interacts with unit 3.  The uniselector
    must find values that work for both configurations.

    In practice: connections 2->1 and 3->1 are always present, but
    the effects of 1 on 2 and 1 on 3 alternate depending on unit 1's sign.

    Returns: (homeostat, seed, metadata)
    '''
    seed = _seed_rngs(seed)

    hom = Homeostat()

    unit1 = _make_unit('Unit_1', uniselector_active=True, uniselector_interval=100)
    unit2 = _make_unit('Unit_2', uniselector_active=True, uniselector_interval=100)
    unit3 = _make_unit('Unit_3', uniselector_active=True, uniselector_interval=100)

    for u in [unit1, unit2, unit3]:
        hom.addFullyConnectedUnit(u)

    # 2->1: uniselector (keep random weight)
    _enable_connection(unit2, unit1, state='uniselector')

    # 3->1: uniselector (keep random weight)
    _enable_connection(unit3, unit1, state='uniselector')

    # 1->2 and 1->3: uniselector-controlled (will be toggled by callback)
    _enable_connection(unit1, unit2, state='uniselector')
    _enable_connection(unit1, unit3, state='uniselector')

    # Disable direct 2<->3 connections
    for conn in unit2.inputConnections:
        if conn.incomingUnit is unit3:
            conn.status = False
    for conn in unit3.inputConnections:
        if conn.incomingUnit is unit2:
            conn.status = False

    metadata = {
        'experiment': 'Exp 7: Multistable System',
        'reference': 'DftB 16/8, Fig. 16/8/1',
        'topology': '3 units: 2<->1<->3, conditional connectivity',
        'description': ('Unit 1 interacts with 2 or 3 depending on its position. '
                         'System must find parameters stable for both pairs.'),
    }
    return hom, seed, metadata


def make_multistable_callback():
    '''Return a tick_callback implementing conditional connectivity for Exp 7.

    When unit 1's deviation > 0 ("above the line"): 1<->2 active, 1<->3 inactive.
    When unit 1's deviation <= 0 ("below the line"): 1<->3 active, 1<->2 inactive.

    Also toggles the reverse connections (2->1, 3->1) so each subsystem
    is fully connected only when active.  This forces the uniselector to
    find parameters stable for both subsystem configurations.
    '''

    def callback(hom, tick):
        unit1 = hom.homeoUnits[0]
        unit2 = hom.homeoUnits[1]
        unit3 = hom.homeoUnits[2]

        above = unit1.criticalDeviation > 0

        # Toggle 1->2 and 2->1 (active when above)
        for conn in unit2.inputConnections:
            if conn.incomingUnit is unit1:
                conn.status = above
        for conn in unit1.inputConnections:
            if conn.incomingUnit is unit2:
                conn.status = above

        # Toggle 1->3 and 3->1 (active when below)
        for conn in unit3.inputConnections:
            if conn.incomingUnit is unit1:
                conn.status = not above
        for conn in unit1.inputConnections:
            if conn.incomingUnit is unit3:
                conn.status = not above

    return callback
