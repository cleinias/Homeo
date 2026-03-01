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
    HomeoUnit.allNames.clear()
    return seed


# ---------------------------------------------------------------
#  Stability tracker
# ---------------------------------------------------------------

class StabilityTracker:
    '''Track whether all active units have stayed within bounds.

    Call check(tick) every tick.  stability_achieved_at will be set to the
    first tick at which window consecutive non-critical ticks were observed.
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
                if u.uniselectorActivated:
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
    '''Add a fixed displacement to a unit's criticalDeviation.'''
    unit = hom.homeoUnits[unit_index]
    unit.criticalDeviation = unit.criticalDeviation + delta


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
#  EXPERIMENT 1: Basic Ultrastability (DftB 8/3--8/4)
# ===============================================================

def setup_exp1_basic_ultrastability(seed=None):
    '''4 fully connected units, all under uniselector control.

    Start from random parameters; observe that the system finds a stable
    field.  This replicates the basic Homeostat demonstration from
    Design for a Brain sec. 8/3--8/4, Figure 8/4/1.

    Returns: (homeostat, seed, metadata)
    '''
    seed = _seed_rngs(seed)

    hom = Homeostat()
    for i in range(4):
        unit = HomeoUnitNewtonian()
        unit.setRandomValues()
        unit.name = 'Unit_%d' % (i + 1)
        unit.uniselectorActive = True
        unit.uniselectorTimeInterval = 100
        hom.addFullyConnectedUnit(unit)

    metadata = {
        'experiment': 'Exp 1: Basic Ultrastability',
        'reference': 'DftB 8/3--8/4, Fig. 8/4/1',
        'topology': '4 fully connected units',
        'description': 'Start from random parameters, observe system finding stable field',
    }
    return hom, seed, metadata


# ===============================================================
#  EXPERIMENT 2: Self-Reorganization in 3-Unit Circle (DftB 8/5)
# ===============================================================

def setup_exp2_self_reorganization(seed=None):
    '''3 units in a ring: 1->2->3->1.

    Connection 3->1: fixed negative (manual).
    Connection 1->2: uniselector-controlled.
    Connection 2->3: hand-controlled (manual), will be reversed mid-run.

    Unit 1 = Motor (agent), has uniselector.
    Unit 2 = Sensor (agent), no uniselector.
    Unit 3 = Environment, no self-connection, no uniselector.

    The 4th unit is created but deactivated (Ashby's hardware had 4 slots).

    Returns: (homeostat, seed, metadata)
    '''
    seed = _seed_rngs(seed)

    hom = Homeostat()

    # Create 4 units (one will be inactive)
    unit1 = _make_unit('Motor', uniselector_active=True, uniselector_interval=100)
    unit2 = _make_unit('Sensor', uniselector_active=False)
    unit3 = _make_unit('Env', uniselector_active=False)
    unit4 = HomeoUnitNewtonian()
    unit4.name = 'UNUSED'

    for u in [unit1, unit2, unit3, unit4]:
        hom.addFullyConnectedUnit(u)

    # Deactivate unit 4
    unit4.disactivate()

    # Disable all cross-connections
    _disable_all_cross_connections(hom)

    # Disable env self-connection
    unit3.disactivateSelfConn()

    # Wire the ring: 1->2->3->1
    # Unit 1 receives from unit 3 (Env->Motor): fixed negative
    _enable_connection(unit3, unit1, weight=-0.5, state='manual')

    # Unit 2 receives from unit 1 (Motor->Sensor): uniselector-controlled
    _enable_connection(unit1, unit2, state='uniselector')

    # Unit 3 receives from unit 2 (Sensor->Env): hand-controlled, positive
    _enable_connection(unit2, unit3, weight=0.5, state='manual')

    metadata = {
        'experiment': 'Exp 2: Self-Reorganization (3-Unit Circle)',
        'reference': 'DftB 8/5, Fig. 8/5/1',
        'topology': '3 units in ring: Motor->Sensor->Env->Motor',
        'description': ('At reversal event, polarity of Sensor->Env '
                         'is flipped; uniselector on Motor->Sensor compensates'),
    }
    return hom, seed, metadata


def exp2_reversal_event(hom):
    '''Reverse polarity of the Sensor->Env connection (hand-controlled).'''
    unit3 = hom.homeoUnits[2]  # Env
    unit2 = hom.homeoUnits[1]  # Sensor
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

def setup_exp4_alternating_environments(seed=None):
    '''2 units with a hand-controlled commutator H that alternates polarity.

    One connection is under uniselector control, the other (H) is
    periodically reversed to simulate two alternating environments.
    The system must find parameter values stable for both polarities.

    Returns: (homeostat, seed, metadata)
    '''
    seed = _seed_rngs(seed)

    hom = Homeostat()

    unit1 = _make_unit('Unit_1', uniselector_active=True, uniselector_interval=100)
    unit2 = _make_unit('Unit_2', uniselector_active=True, uniselector_interval=100)

    for u in [unit1, unit2]:
        hom.addFullyConnectedUnit(u)

    # Unit 1 receives from Unit 2: uniselector-controlled (keep random weight)
    for conn in unit1.inputConnections:
        if conn.incomingUnit is unit2:
            conn.state = 'uniselector'

    # Unit 2 receives from Unit 1: hand-controlled (commutator H)
    for conn in unit2.inputConnections:
        if conn.incomingUnit is unit1:
            conn.state = 'manual'

    metadata = {
        'experiment': 'Exp 4: Alternating Environments',
        'reference': 'DftB 8/10, Fig. 8/10/1',
        'topology': '2 fully connected units, one connection hand-controlled (H)',
        'description': ('Periodically reverse H polarity; system must find '
                         'parameters stable for both polarities'),
    }
    return hom, seed, metadata


def make_alternation_events(interval=500, n_reversals=8):
    '''Return a list of events that reverse the commutator H periodically.

    H is the connection from Unit_1 to Unit_2 (index 1 in unit2.inputConnections).
    '''
    events = []
    for i in range(n_reversals):
        tick = (i + 1) * interval

        def reversal(hom, _i=i):
            unit2 = hom.homeoUnits[1]
            unit1 = hom.homeoUnits[0]
            for conn in unit2.inputConnections:
                if conn.incomingUnit is unit1:
                    conn.newWeight(conn.weight * conn.switch * -1)
                    break

        events.append((tick, reversal))
    return events


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
