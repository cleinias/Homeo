'''
Log the initial and final conditions of a Homeostat to human-readable
(.log) and machine-readable (.json) files.

Each snapshot records the unit and connection parameters and the units'
dynamic state (deviation, velocity, uniselector timer and position, the
continuous uniselector's parameters), and the JSON file the environment
(Python, numpy, numba, Homeo commit); restore_homeostat_conditions puts a
homeostat back in a snapshot's state.  Not recorded: the random generators'
states, the Ashby uniselector's random matrix, and the robot's pose, so a
restored run continues the logged one only up to its noise.

@author: stefano
'''

import json
import os
import time
import numpy as np
from tabulate import tabulate


class _NumpyEncoder(json.JSONEncoder):
    """Handle NumPy types when serializing to JSON."""
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

try:
    from RobotSimulator.HomeoUnitNewtonianTransduc import (
        HomeoUnitNewtonianActuator, HomeoUnitAristotelianActuator, HomeoUnitInput)
    _has_transducer_classes = True
except ImportError:
    _has_transducer_classes = False


_CONTINUOUS_FIELDS = ('model', 'tau_a', 'theta', 'sigma_base', 'sigma_crit', 'dt',
                      'stress_exponent')


def _uniselector_state(unis):
    "The uniselector's kind and the state a restore needs (see _snapshot)."
    state = {'type': type(unis).__name__}
    if type(unis).__name__ == 'HomeoUniselectorContinuous':
        for key in _CONTINUOUS_FIELDS:
            state[key] = getattr(unis, '_' + key)
    if hasattr(unis, '_index'):                 # Ashby: its position in the matrix
        state['index'] = unis._index
    return state


def _environment():
    "What a run's numbers depend on besides the code's parameters."
    import platform
    import subprocess
    env = {'python': platform.python_version(), 'numpy': np.__version__,
           'host': platform.node()}
    try:
        import numba
        env['numba'] = numba.__version__
    except ImportError:
        env['numba'] = 'absent'             # the JIT functions run as plain Python
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        env['homeo'] = subprocess.run(['git', '-C', here, 'describe', '--always', '--dirty'],
                                      capture_output=True, text=True,
                                      timeout=5).stdout.strip() or 'unknown'
    except (OSError, subprocess.SubprocessError):
        env['homeo'] = 'unknown'
    return env


def _snapshot(homeostat):
    """Return a dict with 'units' and 'connections' lists."""

    '''In headless mode with a continuous (OU) uniselector the evolved weights
       live in each unit's JIT arrays, not on the connection objects.  Flush
       them first so the snapshot records the weights the run actually used.'''
    for u in homeostat.homeoUnits:
        if hasattr(u, 'flushJitArrays'):
            u.flushJitArrays()

    units = []
    for u in homeostat.homeoUnits:
        row = {
            'name': u.name,
            'type': type(u).__name__,
            'mass': u.mass,
            'viscosity': u.viscosity,
            'maxDeviation': u.maxDeviation,
            'criticalDeviation': u.criticalDeviation,
            'noise': u.noise,
            'potentiometer': u.potentiometer,
            'switch': u.switch,
            'uniselectorActive': u.uniselectorActive,
            'uniselectorTimeInterval': u.uniselectorTimeInterval,
            'critThreshold': u.critThreshold,
            'needleCompMethod': u.needleCompMethod,
            'status': u.status,
            'currentOutput': u.currentOutput,
            'uniselectorTime': u.uniselectorTime,
            'uniselector': _uniselector_state(u.uniselector),
        }
        if hasattr(u, '_dt_fast'):
            row['dt_fast'] = u._dt_fast
        if hasattr(u, '_currentVelocity'):
            row['currentVelocity'] = u._currentVelocity
        if _has_transducer_classes and isinstance(u, HomeoUnitNewtonianActuator):
            row['switchingRate'] = u._switchingRate
            row['maxSpeedFraction'] = u._maxSpeedFraction
            # Only when set, so logs of unbiased runs are unchanged.
            if getattr(u, '_speedBias', 0.0):
                row['speedBias'] = u._speedBias
        if _has_transducer_classes and isinstance(u, HomeoUnitAristotelianActuator):
            # Linear, no sigmoid: no switchingRate to record.
            row['maxSpeedFraction'] = u._maxSpeedFraction
            if u._speedBias:
                row['speedBias'] = u._speedBias
        if _has_transducer_classes and isinstance(u, HomeoUnitInput):
            row['alwaysPos'] = u.always_pos
        units.append(row)

    connections = []
    for u in homeostat.homeoUnits:
        for conn in u.inputConnections:
            connections.append({
                'unit': u.name,
                'from': conn.incomingUnit.name,
                'weight': conn.weight,
                'switch': conn.switch,
                'noise': conn.noise,
                'state': conn.state,
                'active': conn.status,
            })

    return {'units': units, 'connections': connections}


def _units_table(snapshot):
    """Format the units list as a tabulate grid."""

    # Determine if any actuator/input-specific columns are needed
    has_actuator = any('maxSpeedFraction' in u for u in snapshot['units'])
    has_input = any('alwaysPos' in u for u in snapshot['units'])

    headers = ['Name', 'Type', 'Mass', 'Viscosity', 'MaxDev', 'CritDev',
               'Noise', 'Potent.', 'Switch', 'Unisel', 'UniselTime',
               'CritThresh', 'CompMethod', 'Status', 'Output']
    if has_actuator:
        headers += ['SwitchRate', 'MaxSpeedFrac']
    if has_input:
        headers += ['AlwaysPos']

    rows = []
    for u in snapshot['units']:
        row = [u['name'], u['type'],
               round(u['mass'], 3), round(u['viscosity'], 3),
               round(u['maxDeviation'], 3), round(u['criticalDeviation'], 3),
               round(u['noise'], 4), round(u['potentiometer'], 3),
               u['switch'], u['uniselectorActive'], u['uniselectorTimeInterval'],
               round(u['critThreshold'], 3), u['needleCompMethod'],
               u['status'], round(u['currentOutput'], 6)]
        if has_actuator:
            row += [u.get('switchingRate', ''), u.get('maxSpeedFraction', '')]
        if has_input:
            row += [u.get('alwaysPos', '')]
        rows.append(row)

    return tabulate(rows, headers, tablefmt='grid')


def _connections_table(snapshot):
    """Format the connections list as a tabulate grid."""

    headers = ['Unit', 'From', 'Weight', 'Switch', 'Noise', 'State', 'Active']
    rows = []
    for c in snapshot['connections']:
        rows.append([c['unit'], c['from'],
                     round(c['weight'], 6), c['switch'],
                     round(c['noise'], 6), c['state'], c['active']])

    return tabulate(rows, headers, tablefmt='grid')


def log_homeostat_conditions(homeostat, filepath, label='', experiment_name=''):
    """Append a labelled snapshot of all unit and connection parameters to filepath.

    On the first call (file does not exist), a header with the experiment
    title and date/time is written before the snapshot.
    """

    write_header = not os.path.exists(filepath)
    snap = _snapshot(homeostat)
    with open(filepath, 'a') as f:
        if write_header and experiment_name:
            title = experiment_name.replace('_', ' ').title()
            f.write(title + '\n')
            f.write(time.strftime("%Y-%m-%d %H:%M:%S") + '\n\n')
        f.write('=' * 60 + '\n')
        f.write(label + '\n')
        f.write('=' * 60 + '\n\n')
        f.write('Units:\n')
        f.write(_units_table(snap) + '\n\n')
        f.write('Connections:\n')
        f.write(_connections_table(snap) + '\n\n')


def log_homeostat_conditions_json(homeostat, filepath, label='', experiment_name='',
                                  seed=None, settings=None):
    """Add a snapshot under label key in a JSON file.

    If the file already exists, the existing content is preserved
    and the new snapshot is added (or replaced) under the label key.
    The experiment title and date/time are stored as top-level fields.

    Parameters:
        seed:  RNG seed used for this run (written once on first call).
        settings: optional dict of run settings that are not unit state
               (e.g. stable_draws), written once under 'settings'.
    """

    snap = _snapshot(homeostat)

    data = {}
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            data = json.load(f)

    if experiment_name and 'experiment' not in data:
        data['experiment'] = experiment_name.replace('_', ' ').title()
        data['date'] = time.strftime("%Y-%m-%d %H:%M:%S")

    if seed is not None and 'seed' not in data:
        data['seed'] = seed

    if settings and 'settings' not in data:
        data['settings'] = dict(settings)

    if 'environment' not in data:
        data['environment'] = _environment()

    data[label] = snap

    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, cls=_NumpyEncoder)


def restore_homeostat_conditions(homeostat, snapshot):
    """Put a homeostat in the state a snapshot (see _snapshot) records.

    The inverse of the snapshot: every field it logs is set back, matching
    units by name and connections by (unit, from) pair: each unit's mass,
    viscosity, maxDeviation, deviation, noise, potentiometer, uniselector
    activity and interval, critThreshold, needle method, status and output,
    an actuator's switchingRate, maxSpeedFraction and speedBias, an input
    unit's alwaysPos, and each connection's weight, switch, noise, state and
    status.  Connections come last, so the self-connection ends with its
    logged weight whatever the potentiometer did to it.  The unit's switch is
    the sign of its self-connection, so it is restored with the connection.

    Also the dynamic state the snapshot logs (since 13 Oct 2026; older
    snapshots lack it): dt_fast, the needle's velocity, the uniselector's
    timer and, if it is of the logged kind (else ValueError), the continuous
    uniselector's parameters or the Ashby uniselector's position.  Not
    logged, so not restored: the random generators' states, the Ashby
    uniselector's matrix, and the robot's pose.

    Returns the names of the snapshot's units missing from the homeostat
    (an empty list when everything was restored).
    """
    units = {u.name: u for u in homeostat.homeoUnits}
    missing = [row['name'] for row in snapshot['units'] if row['name'] not in units]
    for row in snapshot['units']:
        u = units.get(row['name'])
        if u is None:
            continue
        u.maxDeviation = row['maxDeviation']
        u.mass = row['mass']
        u.viscosity = row['viscosity']
        u.noise = row['noise']
        u.potentiometer = row['potentiometer']
        u.uniselectorActive = row['uniselectorActive']
        u.uniselectorTimeInterval = row['uniselectorTimeInterval']
        u.critThreshold = row['critThreshold']
        u.needleCompMethod = row['needleCompMethod']
        u.status = row['status']
        u.criticalDeviation = row['criticalDeviation']
        u.currentOutput = row['currentOutput']
        # Logged since 13 Oct 2026; older snapshots lack them
        if 'dt_fast' in row and hasattr(u, '_dt_fast'):
            u.dt_fast = row['dt_fast']
        if 'currentVelocity' in row and hasattr(u, '_currentVelocity'):
            u._currentVelocity = row['currentVelocity']
        if 'uniselectorTime' in row:
            u.uniselectorTime = row['uniselectorTime']
        unis = row.get('uniselector')
        if unis is not None:
            if unis['type'] != type(u.uniselector).__name__:
                raise ValueError('unit %s has a %s, the snapshot a %s' % (
                    u.name, type(u.uniselector).__name__, unis['type']))
            for key in _CONTINUOUS_FIELDS:
                if key in unis:
                    setattr(u.uniselector, '_' + key, unis[key])
            if 'index' in unis:
                # Snapshots made before CD-02 (13 Oct 2026) can hold 25, one
                # past the last row: the old switch had 26 positions.
                u.uniselector._index = unis['index'] % u.uniselector.matrix().shape[0]
        if 'switchingRate' in row:
            u._switchingRate = row['switchingRate']
        if 'maxSpeedFraction' in row:
            u._maxSpeedFraction = row['maxSpeedFraction']
            u._maxSpeed = None              # recomputed from the fraction
        if hasattr(u, '_speedBias'):
            u._speedBias = row.get('speedBias', 0.0)
        if 'alwaysPos' in row:
            u.always_pos = row['alwaysPos']
    saved = {(c['unit'], c['from']): c for c in snapshot['connections']}
    for u in homeostat.homeoUnits:
        for conn in u.inputConnections:
            c = saved.get((u.name, conn.incomingUnit.name))
            if c is None:
                continue
            conn.newWeight(c['weight'] * c['switch'])
            conn.noise = c['noise']
            conn.state = c['state']
            conn.status = c['active']
        u._jit_dirty = True
    return missing
