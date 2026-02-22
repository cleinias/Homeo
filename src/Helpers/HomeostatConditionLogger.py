'''
Log the initial and final conditions of a Homeostat to human-readable
(.log) and machine-readable (.json) files.

Each snapshot records all unit parameters and connection parameters
so that experiments are fully reproducible.

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
        HomeoUnitNewtonianActuator, HomeoUnitInput)
    _has_transducer_classes = True
except ImportError:
    _has_transducer_classes = False


def _snapshot(homeostat):
    """Return a dict with 'units' and 'connections' lists."""

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
        }
        if _has_transducer_classes and isinstance(u, HomeoUnitNewtonianActuator):
            row['switchingRate'] = u._switchingRate
            row['maxSpeedFraction'] = u._maxSpeedFraction
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
    has_actuator = any('switchingRate' in u for u in snapshot['units'])
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


def log_homeostat_conditions_json(homeostat, filepath, label='', experiment_name=''):
    """Add a snapshot under label key in a JSON file.

    If the file already exists, the existing content is preserved
    and the new snapshot is added (or replaced) under the label key.
    The experiment title and date/time are stored as top-level fields.
    """

    snap = _snapshot(homeostat)

    data = {}
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            data = json.load(f)

    if experiment_name and 'experiment' not in data:
        data['experiment'] = experiment_name.replace('_', ' ').title()
        data['date'] = time.strftime("%Y-%m-%d %H:%M:%S")

    data[label] = snap

    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, cls=_NumpyEncoder)
