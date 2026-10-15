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
    HomeoUnit.clearNames()
    return seed


# ---------------------------------------------------------------
#  Stability tracker
# ---------------------------------------------------------------

class StabilityTracker:
    '''Track whether all active units have stayed within bounds.

    Call check(tick) every tick, after the update that produced tick.  The
    homeostat is stable once no active unit has been critical for window
    consecutive ticks; a stable stretch begins at the first of those ticks.
    episodes lists every stable stretch as [onset, end] (end: its last
    uncritical tick so far); the measures are read off it:
    - stability_achieved_at: the onset of the first stretch (1 if the
      homeostat was stable from the start), None if never stable;
    - stable_since: the onset of the stretch in progress, None if not
      currently stable;
    - restabilisation(t, until): what a disturbance at t did (see there).
    Until 15 Oct 2026 (review finding SR-14) onsets were recorded one tick
    early and never before a burn-in of 200 ticks (a stretch from tick 1
    came out as 200), and the "last stability" reported was the latest
    tick minus window, not the onset of the stretch in progress.
    total_uniselector_firings counts only the firings of units that have an
    input their uniselector can re-draw; the others change nothing.
    '''

    def __init__(self, homeostat, window=200):
        self.hom = homeostat
        self.window = window
        self._run = 0
        self.episodes = []
        self.currently_stable = False
        self.total_uniselector_firings = 0

    @property
    def stability_achieved_at(self):
        return self.episodes[0][0] if self.episodes else None

    @property
    def stable_since(self):
        return self.episodes[-1][0] if self.currently_stable else None

    def restabilisation(self, t, until):
        '''What a disturbance at tick t did, judged up to tick until (the next
        disturbance, or the run's end): ('held', None) if a stable stretch
        begun by t lasted to until; ('restabilised', latency) if a stretch
        began after t and before until, latency ticks after t; ('never', None)
        otherwise.'''
        for onset, end in self.episodes:
            if onset <= t and end >= until:
                return ('held', None)
            if t < onset < until:
                return ('restabilised', onset - t)
        return ('never', None)

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
        if self._run == self.window:
            self.episodes.append([tick - self.window + 1, tick])
            self.currently_stable = True
        elif self._run > self.window:
            self.episodes[-1][1] = tick


# ---------------------------------------------------------------
#  Simple per-tick state logger for pure Ashby experiments
# ---------------------------------------------------------------

class AshbyStateLogger:
    '''Lightweight per-tick TSV logger for non-robotic Ashby experiments.

    Logs: tick, per-unit (critDev, output, velocity, uniselector_fired),
    and per-connection signed weights.  Row t is the state after the update
    of tick t: uniselector_fired is 1 if the unit's discrete uniselector fired
    in that update, so it shows in the same row as the deviation that
    triggered it (the update checks the deviation it has just computed) and
    the weights it drew.  A continuous (OU)
    uniselector never fires: 0 (review finding CD-12).
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

        # Update all active units, together
        hom.updateUnits()

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
    their connections, in both directions, are switched off.

    Creating units and connections draws from the random generators, so
    their state is saved and restored: the setup's later draws are the
    same with the slots as without, and a seed builds the GUI's homeostat
    exactly as the headless run's (until 14 Oct 2026 Exps 3, 4 and 5
    differed; SR-06).'''
    np_state, py_state = np.random.get_state(), random.getstate()
    try:
        for i in range(len(hom.homeoUnits), n_slots):
            unit = HomeoUnitNewtonian()
            unit.name = 'UNUSED_%d' % (i + 1)
            hom.addFullyConnectedUnit(unit)
            unit.disactivate()
    finally:
        np.random.set_state(np_state)
        random.setstate(py_state)
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
# Protocol (ticks): reversal R of 2->3, end of the run
EXP2_R, EXP2_END = 3000, 12000


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
    the uniselector) in 28.

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

# Exp 3 parameters (see setup_exp3_training)
EXP3_VISCOSITY = 10
EXP3_SELF_FEEDBACK_13 = (0.5, 1.0)
EXP3_SELF_FEEDBACK_2 = (0.2, 0.5)
EXP3_W23, EXP3_W31 = 0.2, 1.0
# Protocol (ticks; see Exp3Trainer)
EXP3_SETTLE, EXP3_BASELINE, EXP3_HOLD, EXP3_PUNISH, EXP3_WAIT = 1000, 100, 200, 400, 1000
EXP3_TESTS, EXP3_STROKE, EXP3_THRESHOLD = 10, -5.0, 0.5
EXP3_END = EXP3_SETTLE + EXP3_TESTS * (EXP3_BASELINE + EXP3_HOLD + EXP3_PUNISH + EXP3_WAIT)


def setup_exp3_training(seed=None, unused_slots=False):
    '''3 units in a ring 1->2->3->1, trained by punishment.

    "Three units were joined: 1 -> 2, 2 -> 3, 3 -> 1" and a trainer "acted
    on the rule that if the Homeostat did not respond to a forced movement
    of 1 by an opposite movement of 2, then the trainer would force 3 over
    to an extreme position" (DfB 8/9).  The trainer is Exp3Trainer.

    With 1 forced, 2's response depends only on 1->2 and 2's self-feedback,
    so the step-mechanism that training must change is 1->2, on unit 2's
    uniselector; unit 2 is driven critical through 3 -> 1 -> 2.  The other
    uniselectors are off (unit 1's would have nothing to re-draw).  Signs as
    in Fig. 8/9/1: 3 forced down moves 1 down, so 3->1 is positive (+1, so
    that 3 at its extreme pins 1); 2->3 is positive, and weak (0.2).

    Both the forbidden and the desired configuration are stable fields in
    the figure, so all three units need negative self-feedback (1 and 3:
    0.5-1; 2: 0.2-0.5), with p1 p2 p3 > |1->2| w23 w31.  The punishment then
    makes unit 2 critical only if 1->2 > 0.9 p2: a smaller positive 1->2 is
    a trap, stable and wrong, which no punishment can change.  1->2 starts
    in the forbidden band where the start is stable and S1's punishment
    acts, as in Ashby's run.  Strongly damped units.  Over 30 seeds the
    trainer produces Ashby's result in 14 (punished, then a change of 1->2,
    then the desired response without punishment), while the same tests
    without the trainer end in the desired response in 1.  7 runs end in
    the trap (each re-draw of 1->2 can land in it): a property of the linear
    Homeostat with this wiring rather than of the code.

    unused_slots: add an inactive unit 4 (for the GUI).

    Returns: (homeostat, seed, metadata)
    '''
    seed = _seed_rngs(seed)

    hom = Homeostat()
    p1 = np.random.uniform(*EXP3_SELF_FEEDBACK_13)
    p2 = np.random.uniform(*EXP3_SELF_FEEDBACK_2)
    p3 = np.random.uniform(*EXP3_SELF_FEEDBACK_13)
    unit1 = _make_unit('Unit_1', viscosity=EXP3_VISCOSITY, potentiometer=p1,
                       uniselector_active=False)
    unit2 = _make_unit('Unit_2', viscosity=EXP3_VISCOSITY, potentiometer=p2,
                       uniselector_active=True, uniselector_interval=100)
    unit3 = _make_unit('Unit_3', viscosity=EXP3_VISCOSITY, potentiometer=p3,
                       uniselector_active=False)
    for u in [unit1, unit2, unit3]:
        hom.addFullyConnectedUnit(u)
    if unused_slots:
        _add_unused_slots(hom)

    _disable_all_cross_connections(hom)
    _enable_connection(unit2, unit3, weight=EXP3_W23, state='manual')
    _enable_connection(unit3, unit1, weight=EXP3_W31, state='manual')
    # 1->2: unit 2's uniselector.  Ashby's start: forbidden (positive), the
    # ring stable, and large enough for the punishment to make 2 critical
    low = 0.9 * p2 / min(1.0, EXP3_W31 / p1)
    high = min(1.0, p1 * p2 * p3 / (EXP3_W23 * EXP3_W31))
    conn = _enable_connection(unit1, unit2, state='uniselector')
    conn.newWeight(np.random.uniform(low, high))

    metadata = {
        'experiment': 'Exp 3: Training by Punishment',
        'reference': 'DftB 8/9, Fig. 8/9/1',
        'topology': '3 units: 1->2 (unit 2\'s uniselector), 2->3 and 3->1 by hand; trainer acts on 3',
        'description': ('The operator forces 1 down; if 2 does not move the opposite '
                        'way, the trainer forces 3 to an extreme'),
    }
    return hom, seed, metadata


class Exp3Trainer:
    '''The operator and the trainer of Fig. 8/9/1, as a tick_callback.

    After EXP3_SETTLE ticks, EXP3_TESTS times: the operator forces 1 down
    (holds it at EXP3_STROKE for EXP3_HOLD ticks, S in the figure).  2's
    response is its mean displacement from tick 50 of the hold on, less its
    drift over the EXP3_BASELINE ticks before (extrapolated).  "If the
    Homeostat did not respond to a forced movement of 1 by an opposite
    movement of 2" (response not above EXP3_THRESHOLD), the trainer holds 3
    at its extreme, -maxDeviation, for EXP3_PUNISH ticks (D).  Then it waits
    EXP3_WAIT ticks.  With punish=False the tests are run without the
    trainer (a control).

    sequence: per test, 'P' (punished) or 'd' (the desired response; 'f'
    for a wrong one in a control).  punishments: their ticks.
    changes_per_punishment: unit 2's uniselector changes from each
    punishment to the next test (the runaway can outlast the punishment).
    '''

    def __init__(self, punish=True):
        self.punish = punish
        self.sequence = []
        self.responses = []
        self.punishments = []
        self.changes_per_punishment = []
        self._phase, self._until = 'settle', EXP3_SETTLE
        self._baseline = []

    @staticmethod
    def _hold(unit, x):
        unit.criticalDeviation = x
        unit.currentVelocity = 0.0
        unit.computeOutput()

    def __call__(self, hom, tick):
        unit1, unit2, unit3 = hom.homeoUnits[:3]
        if self._phase == 'done':
            return
        if self._phase == 'baseline':
            self._baseline.append(unit2.criticalDeviation)
        elif self._phase == 'test':
            self._hold(unit1, EXP3_STROKE)
            t = tick - self._start
            if t >= 50:
                self._response.append(unit2.criticalDeviation - self._base - self._slope * (t + 1))
        elif self._phase == 'punish':
            self._hold(unit3, -unit3.maxDeviation)
        if tick + 1 < self._until:
            return
        # end of the phase: start the next one
        if self._phase in ('settle', 'wait'):
            if self._phase == 'wait' and self.sequence[-1] == 'P':
                self.changes_per_punishment.append(unit2.uniselectorActivationCount - self._count)
            if len(self.sequence) == EXP3_TESTS:
                self._phase = 'done'
                return
            self._phase, self._until = 'baseline', tick + 1 + EXP3_BASELINE
            self._baseline = []
        elif self._phase == 'baseline':
            self._slope = np.polyfit(np.arange(len(self._baseline)), self._baseline, 1)[0]
            self._base = unit2.criticalDeviation
            self._response = []
            self._phase, self._start, self._until = 'test', tick + 1, tick + 1 + EXP3_HOLD
        elif self._phase == 'test':
            response = float(np.mean(self._response))
            self.responses.append(response)
            if response > EXP3_THRESHOLD:
                self.sequence.append('d')
            elif self.punish:
                self.sequence.append('P')
                self.punishments.append(tick + 1)
                self._count = unit2.uniselectorActivationCount
                self._phase, self._until = 'punish', tick + 1 + EXP3_PUNISH
                return
            else:
                self.sequence.append('f')
            self._phase, self._until = 'wait', tick + 1 + EXP3_WAIT
        elif self._phase == 'punish':
            self._phase, self._until = 'wait', tick + 1 + EXP3_WAIT

    def trained(self, hom):
        '''Ashby's result: S1 punished, a punishment changed 1->2, the last
        three tests desired, and 1->2 negative at the end.'''
        unit1, unit2 = hom.homeoUnits[:2]
        conn = connection(unit2, unit1)
        return (self.sequence[:1] == ['P'] and any(self.changes_per_punishment) and
                self.sequence[-3:] == ['d'] * 3 and conn.weight * conn.switch < 0)


def make_trainer_callback(punishment_log=None, punish=True):
    '''Return (trainer, punishment ticks) for Exp 3; see Exp3Trainer.'''
    trainer = Exp3Trainer(punish=punish)
    if punishment_log is not None:
        trainer.punishments = punishment_log
    return trainer, trainer.punishments


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

# Exp 5 parameters (see setup_exp5_constraint)
EXP5_VISCOSITY = 10
# Negative self-feedback per unit: range of its strength, or None for none
EXP5_SELF_FEEDBACK = (None, None, (0.5, 1.0))
# Ashby's start: margin on the real parts of the eigenvalues (m -> 0), so
# that J's runaway reaches the critical level within the protocol's window
EXP5_START_MARGIN = 0.01
# Protocol (ticks): join the fibre at J, remove it at R
EXP5_J, EXP5_R, EXP5_END = 4000, 12000, 18000


def exp5_fibre_matrix(A):
    '''Ashby's m -> 0 matrix of units (1, 2, 3) with 1 and 2 joined: the pair,
    at y = x1 = x2, moves under the mean of the two units' torques.'''
    return np.array([[(A[0, 0] + A[0, 1] + A[1, 0] + A[1, 1]) / 2, (A[0, 2] + A[1, 2]) / 2],
                     [A[2, 0] + A[2, 1], A[2, 2]]])


def setup_exp5_constraint(seed=None, unused_slots=False):
    '''3 units, fully joined on uniselectors; at J the magnets of 1 and 2 are
    joined by a light glass fibre, and at R the fibre is removed.

    "Three units were joined together and were at first stable ... At J,
    the magnets of 1 and 2 were joined so that they could move only
    together.  The result of the constraint in this case was to make the
    system unstable.  But the instability evoked step-mechanism changes, and
    a new terminal field was found ... when, at R, the operator gently
    lifted the fibre away the system became unstable" (DfB 8/11).

    Ashby states neither the self-feedback nor which links were on
    uniselectors.  All six cross-connections are, with all three
    uniselectors on (the arrangement of DfB 8/3).  Units 1 and 2 have no
    self-feedback and unit 3 has 0.5-1 (the units whose uniselectors must
    act carry none, as in Exp 2): with strong self-feedback a field found
    under the fibre is almost always stable without it, and R shows
    nothing.  Ashby's start: the cross weights are drawn until the free
    field is stable and the field with the fibre is not (m -> 0 limit, with
    a margin so that J's runaway reaches the critical level in time),
    Ashby's "at first stable" and "in this case ... unstable".  Strongly
    damped units of equal mass (the fibre averages them).  Over 30 seeds
    the full sequence (stable, J destabilises, re-adapted with the fibre,
    R destabilises) appears in 23; in 7 more the field found with the fibre
    is stable without it as well.

    unused_slots: add an inactive unit 4 (for the GUI).

    Returns: (homeostat, seed, metadata)
    '''
    seed = _seed_rngs(seed)

    hom = Homeostat()
    units = []
    for i, strength in enumerate(EXP5_SELF_FEEDBACK):
        unit = _make_unit('Unit_%d' % (i + 1), viscosity=EXP5_VISCOSITY,
                          uniselector_active=True, uniselector_interval=100)
        hom.addFullyConnectedUnit(unit)
        if strength is None:
            unit.disactivateSelfConn()
        else:
            unit.potentiometer = np.random.uniform(*strength)
        units.append(unit)
    if unused_slots:
        _add_unused_slots(hom)

    # Ashby's start: stable while free, unstable with the fibre
    for attempt in range(100000):
        for u in units:
            for v in units:
                if u is not v:
                    connection(u, v).newWeight(np.random.uniform(-1, 1))
        A = ashby_matrix(units)
        free = np.max(np.linalg.eigvals(A).real)
        joined = np.max(np.linalg.eigvals(exp5_fibre_matrix(A)).real)
        if free < -EXP5_START_MARGIN and joined > EXP5_START_MARGIN:
            break

    metadata = {
        'experiment': 'Exp 5: Constraint (Glass Fibre)',
        'reference': 'DftB 8/11, Fig. 8/11/1',
        'topology': '3 fully connected units; at J units 1 and 2 joined by a fibre, at R freed',
        'description': ('Join units 1-2 at J; the system re-adapts with the fibre. '
                        'Remove it at R: unstable without it.'),
    }
    return hom, seed, metadata


def make_constraint_callback(a_idx=0, b_idx=1, active=False):
    '''Return (tick_callback, flag) for Ashby's glass fibre joining two units.

    The fibre transmits force: the joined magnets move as one body under the
    sum of both torques.  With equal masses that is exactly averaging their
    positions and velocities after each tick.  Set flag[0] to True to join
    (J) and to False to release (R).
    '''
    flag = [active]  # mutable container so events can toggle it

    def constrain(hom, tick):
        if flag[0]:
            a, b = hom.homeoUnits[a_idx], hom.homeoUnits[b_idx]
            x = (a.criticalDeviation + b.criticalDeviation) / 2
            v = (a.currentVelocity + b.currentVelocity) / 2
            for u in (a, b):
                u.criticalDeviation = x
                u.currentVelocity = v
                u.computeOutput()

    return constrain, flag


def exp5_events(flag):
    '''Join the fibre at J and remove it at R (flag from make_constraint_callback).'''
    return [(EXP5_J, lambda hom: flag.__setitem__(0, True)),
            (EXP5_R, lambda hom: flag.__setitem__(0, False))]


# ===============================================================
#  EXPERIMENT 6: Habituation (DftB 14/6)
# ===============================================================

# Exp 6 parameters, Fig. 14/6/1 (see setup_exp6_habituation)
EXP6_VISCOSITY = 10
EXP6_SELF_FEEDBACK = (0.08, 0.12)
EXP6_DISPLACEMENT = 8.0
EXP6_FIRST, EXP6_INTERVAL, EXP6_STIMULI = 1000, 4000, 10
EXP6_END = EXP6_FIRST + EXP6_STIMULI * EXP6_INTERVAL
# Fig. 14/6/2 (see setup_exp6b_habituation_ultrastable)
EXP6B_SELF_FEEDBACK = (0.05, 0.15)
EXP6B_DISPLACEMENT = 6.0
EXP6B_FIRST, EXP6B_INTERVAL = 500, 2000
EXP6B_END = EXP6B_FIRST + EXP6_STIMULI * EXP6B_INTERVAL


def setup_exp6_habituation(seed=None, unused_slots=False):
    '''Fig. 14/6/1: two units joined 1 -> 2 only, 1->2 on unit 2's uniselector.

    "Two units were joined 1 -> 2.  The effect of 1 on 2 was determined by
    2's uniselector, which changed position if 2 exceeded its critical
    states.  The operator then repeatedly disturbed 2 by moving 1, at D"
    (DfB 14/6).  While a value of 1->2 lets D drive 2 critical, the
    uniselector changes it; the first value for which D no longer does is
    "retained permanently", and 2's response to D stays small: habituation.

    There is no 2->1.  Unit 1's uniselector is off: it has nothing to
    re-draw.  Both units have weak negative self-feedback (0.08-0.12): their
    traces return to rest after each D, and with it about half the
    uniselector's values make D drive 2 critical (with stronger
    self-feedback D almost never does, and there is nothing to habituate).
    Strongly damped units.  Over 30 seeds, with ten D's of 8 every 4000
    ticks (long enough "for the system to come to equilibrium before the
    next application", 14/3), Ashby's result appears in 20; in 8 more the
    first value of 1->2 already gives a small response.

    For Fig. 14/6/2 (1 <-> 2, both on uniselectors) see
    setup_exp6b_habituation_ultrastable.

    unused_slots: add inactive units up to four (for the GUI).

    Returns: (homeostat, seed, metadata)
    '''
    seed = _seed_rngs(seed)

    hom = Homeostat()
    unit1 = _make_unit('Unit_1', viscosity=EXP6_VISCOSITY, uniselector_active=False,
                       potentiometer=np.random.uniform(*EXP6_SELF_FEEDBACK))
    unit2 = _make_unit('Unit_2', viscosity=EXP6_VISCOSITY,
                       uniselector_active=True, uniselector_interval=100,
                       potentiometer=np.random.uniform(*EXP6_SELF_FEEDBACK))
    for u in [unit1, unit2]:
        hom.addFullyConnectedUnit(u)
    if unused_slots:
        _add_unused_slots(hom)

    _disable_all_cross_connections(hom)
    # 1->2: unit 2's uniselector (keeps its random weight)
    _enable_connection(unit1, unit2, state='uniselector')

    metadata = {
        'experiment': 'Exp 6: Habituation',
        'reference': 'DftB 14/6, Fig. 14/6/1',
        'topology': '2 units joined 1->2, on unit 2\'s uniselector',
        'description': ('Repeatedly displace unit 1 by a fixed angle D; the first '
                        '1->2 for which D does not drive 2 critical is retained'),
    }
    return hom, seed, metadata


def setup_exp6b_habituation_ultrastable(seed=None):
    '''Fig. 14/6/2: two units 1 <-> 2, both links on the uniselectors.

    "Both effects go through the uniselectors, so the whole is ultrastable.
    At each D the operator displaced 1's magnet through a constant distance.
    On the first 'stimulation', 2's response brought the system to its
    critical states, so the ultrastability found a new terminal field. The
    second stimulation again evoked the process. But the new terminal field
    was such that the displacement D no longer caused 2 to reach its
    critical states; so this field was retained" (DfB 14/6).

    Ashby's trace, a small D on a resting system sending both units to
    their limits, is that of an unstable field at rest, as a real magnet
    held by pivot friction can be.  A noisy simulation cannot rest in an
    unstable field: its ultrastable search finds a stable one before any
    D, which a modest D rarely drives critical (6 in 30 seeds show Ashby's
    result).  So here the units have no noise and start at rest at the
    centre: then 18 in 30 do, with D = 6 every 2000 ticks.  Weak negative
    self-feedback on both (0.05-0.15; with none, a 2-unit field is never
    asymptotically stable).  Strongly damped units.

    Returns: (homeostat, seed, metadata)
    '''
    seed = _seed_rngs(seed)

    hom = Homeostat()
    unit1 = _make_unit('Unit_1', viscosity=EXP6_VISCOSITY, noise=0,
                       uniselector_active=True, uniselector_interval=100,
                       potentiometer=np.random.uniform(*EXP6B_SELF_FEEDBACK))
    unit2 = _make_unit('Unit_2', viscosity=EXP6_VISCOSITY, noise=0,
                       uniselector_active=True, uniselector_interval=100,
                       potentiometer=np.random.uniform(*EXP6B_SELF_FEEDBACK))
    for u in [unit1, unit2]:
        hom.addFullyConnectedUnit(u)

    _disable_all_cross_connections(hom)
    _enable_connection(unit1, unit2, state='uniselector', noise=0)
    _enable_connection(unit2, unit1, state='uniselector', noise=0)
    for u in [unit1, unit2]:
        u.inputConnections[0].noise = 0
        u.criticalDeviation = 0
        u.currentVelocity = 0
        u.computeOutput()

    metadata = {
        'experiment': 'Exp 6b: Habituation of an ultrastable system',
        'reference': 'DftB 14/6, Fig. 14/6/2',
        'topology': '2 units 1<->2, both links on the uniselectors; no noise',
        'description': ('Repeatedly displace unit 1; the first field for which D '
                        'does not drive the system critical is retained'),
    }
    return hom, seed, metadata


def make_stimulus_events(unit_index=0, delta=EXP6_DISPLACEMENT, interval=EXP6_INTERVAL,
                         n_stimuli=EXP6_STIMULI, settle_first=EXP6_FIRST):
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
    '''Per stimulus D, until the next one: the peak response of the target
    unit, whether a unit whose uniselector can act reached a critical state
    (from 30 ticks after D, so that D itself does not count) and how many
    uniselector changes followed.  Call check(tick) every tick.

    Ashby's habituation (DfB 14/5-14/6): the D's that drive the system
    critical change the step-mechanisms, until a value is found for which D
    no longer does; that value is kept, and the response stays small.
    '''

    def __init__(self, hom, target_unit_index=1, stimulus_ticks=None):
        self.hom = hom
        self.target_idx = target_unit_index
        self.stimulus_ticks = sorted(stimulus_ticks or [])
        self.responses = []         # peak |x - x at D| of the target unit
        self.critical = []          # some active unit critical after D
        self.changes = []           # uniselector changes after D
        self._baseline = 0.0

    def _adaptive_units(self):
        return [u for u in self.hom.homeoUnits
                if u.isActive() and u.uniselectorActive and has_adaptive_input(u)]

    def _changes_so_far(self):
        return sum(u.uniselectorActivationCount for u in self._adaptive_units())

    def check(self, tick):
        unit = self.hom.homeoUnits[self.target_idx]
        if tick in self.stimulus_ticks:
            self._start = tick
            self._baseline = unit.criticalDeviation
            self._count = self._changes_so_far()
            self.responses.append(0.0)
            self.critical.append(False)
            self.changes.append(0)
        if self.responses:
            self.responses[-1] = max(self.responses[-1],
                                     abs(unit.criticalDeviation - self._baseline))
            if tick - self._start >= 30 and any(
                    abs(u.criticalDeviation) >= u.critThreshold * u.maxDeviation
                    for u in self._adaptive_units()):
                self.critical[-1] = True
            self.changes[-1] = self._changes_so_far() - self._count

    def retained_since(self):
        '''Index of the first D after the last one that caused a change
        (None if the last D caused one).'''
        last = max([i for i, n in enumerate(self.changes) if n], default=-1)
        return last + 1 if last + 1 < len(self.changes) else None

    def habituated(self, last=4):
        '''Ashby's result: some D caused a change, the last D's caused no
        critical state and no change, and the response to them is smaller
        than to the D's that caused changes.'''
        changed = [r for r, n in zip(self.responses, self.changes) if n]
        return bool(changed) and not any(self.critical[-last:]) and \
            not any(self.changes[-last:]) and \
            np.mean(self.responses[-last:]) < np.mean(changed)


# ===============================================================
#  EXPERIMENT 7: Multistable System (DftB 16/8)
# ===============================================================

# Exp 7 parameters (see setup_exp7_multistable)
EXP7_VISCOSITY = 10
EXP7_SELF_FEEDBACK_23 = (0.5, 1.0)
EXP7_HAND = 0.5
# Protocol (ticks): adapt, then test displacements of unit 1, +D, -D, +D, -D
EXP7_TEST, EXP7_TEST_GAP, EXP7_DISPLACEMENT = 20000, 750, 4.0
EXP7_END = EXP7_TEST + 4 * EXP7_TEST_GAP


def setup_exp7_multistable(seed=None, unused_slots=False):
    '''3 units, 2 <-> 1 <-> 3, with bars that stop 2 and 3 from moving up.

    "To separate the effects of 2 and 3 on 1, bars were placed across the
    potentiometer dishes of 2 and 3 so that they could move only in the
    direction recorded as downwards ... If 1 was above the central line ...
    1 and 2 interacted, and 3 was independent; but if 1 was below the
    central line, then 1 and 3 interacted, and 2 was independent.  1 was set
    to act on 2 negatively and on 3 positively, while the effects 2 -> 1 and
    3 -> 1 were uniselector-controlled" (DfB 16/8).

    So 1->2 (-0.5) and 1->3 (+0.5) are set by hand; 2->1 and 3->1 are
    re-drawn by unit 1's uniselector, every step changing both, so that a
    step that cures one pair can spoil the other.  The bars are a tick
    callback (make_multistable_callback); the position-dependent coupling
    comes out of them, and no connection is switched.  There is no 2-3 link.
    Unit 1 (whose uniselector must act) has no self-feedback, units 2 and 3
    have 0.5-1 (they must return to the bar).  Strongly damped units; 2 and
    3 start at or below the bar.  The search stops only at values stable for
    both pairs, which in the m -> 0 limit means 2->1 > 0 and 3->1 < 0: a
    quarter of the uniselector's draws.  Over 30 seeds, with test
    displacements of unit 1 after 20000 ticks, Ashby's result appears in 22;
    in 6 more the first draw is already stable for both pairs.

    unused_slots: add an inactive unit 4 (for the GUI).

    Returns: (homeostat, seed, metadata)
    '''
    seed = _seed_rngs(seed)

    hom = Homeostat()
    unit1 = _make_unit('Unit_1', viscosity=EXP7_VISCOSITY,
                       uniselector_active=True, uniselector_interval=100)
    unit2 = _make_unit('Unit_2', viscosity=EXP7_VISCOSITY, uniselector_active=False,
                       potentiometer=np.random.uniform(*EXP7_SELF_FEEDBACK_23))
    unit3 = _make_unit('Unit_3', viscosity=EXP7_VISCOSITY, uniselector_active=False,
                       potentiometer=np.random.uniform(*EXP7_SELF_FEEDBACK_23))
    for u in [unit1, unit2, unit3]:
        hom.addFullyConnectedUnit(u)
    if unused_slots:
        _add_unused_slots(hom)

    _disable_all_cross_connections(hom)
    unit1.disactivateSelfConn()
    # 1->2 negative and 1->3 positive, by hand
    _enable_connection(unit1, unit2, weight=-EXP7_HAND, state='manual')
    _enable_connection(unit1, unit3, weight=+EXP7_HAND, state='manual')
    # 2->1 and 3->1: unit 1's uniselector (keep random weights)
    _enable_connection(unit2, unit1, state='uniselector')
    _enable_connection(unit3, unit1, state='uniselector')
    # 2 and 3 start at or below their bars
    for u in [unit2, unit3]:
        u.criticalDeviation = -abs(u.criticalDeviation)
        u.computeOutput()

    metadata = {
        'experiment': 'Exp 7: Multistable System',
        'reference': 'DftB 16/8, Fig. 16/8/1',
        'topology': ('3 units: 2<->1<->3; 1->2 (-) and 1->3 (+) by hand, 2->1 and 3->1 '
                     'on unit 1\'s uniselector; bars stop 2 and 3 above the centre'),
        'description': ('Unit 1 interacts with 2 above the centre and with 3 below; '
                        'the uniselector must find values stable for both pairs.'),
    }
    return hom, seed, metadata


def make_multistable_callback():
    '''Return a tick_callback implementing Ashby's bars for Exp 7.

    Units 2 and 3 (indices 1 and 2) can move only downwards from the centre:
    a needle pushed up stays at the bar (deviation 0, so no output), and its
    upward velocity is stopped.  It runs before the units update, so it
    holds the previous tick's result at the bar.
    '''

    def bars(hom, tick):
        for unit in hom.homeoUnits[1:3]:
            if unit.criticalDeviation > 0:
                unit.criticalDeviation = 0.0
                unit.currentVelocity = min(unit.currentVelocity, 0.0)
                unit.computeOutput()

    return bars


def exp7_test_events():
    '''The operator's test displacements of unit 1 after the adaptation:
    up (1 interacts with 2), down (with 3), up, down.'''
    return [(EXP7_TEST + k * EXP7_TEST_GAP,
             lambda hom, d=EXP7_DISPLACEMENT * (-1) ** k: inject_stimulus(hom, 0, d))
            for k in range(4)]


def exp7_pairs_stable(hom):
    '''Whether the pairs (1, 2) and (1, 3) are each stable, in Ashby's
    m -> 0 limit.'''
    unit1, unit2, unit3 = hom.homeoUnits[:3]
    return (ashby_stable(ashby_matrix([unit1, unit2])),
            ashby_stable(ashby_matrix([unit1, unit3])))
