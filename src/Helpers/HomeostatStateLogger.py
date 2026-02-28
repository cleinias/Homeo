'''
Per-tick state logger for diagnosing Homeostat dynamics during
phototaxis experiments.

Produces a .statelog file: tab-separated values with a #-prefixed
metadata header.  Constant parameters (mass, viscosity, tau_a, etc.)
are written once in the header; per-tick columns capture deviation,
output, velocity, torque, stress, signed connection weights, OU sigma,
sensor readings, motor speeds, and robot position.

In headless mode the JIT arrays (_jit_weights, _jit_switches) are the
authoritative source of connection weights — the Connection objects may
be stale.  The logger detects headless mode and reads from JIT arrays.

Usage:
    logger = HomeostatStateLogger(hom, khepera_sim, filepath)
    # ... inside the main loop, after hom.runFor(tick):
    logger.log_tick(tick)
    # ... after the loop:
    logger.close()

@author: stefano
'''

import os
import time
import numpy as np
from math import sqrt, degrees


class HomeostatStateLogger:
    '''Log per-tick internal state of a Homeostat + robot to a TSV file.

    Constructor parameters:
        homeostat:    Homeostat instance
        khepera_sim:  KheperaSimulation instance (provides robot + target)
        filepath:     output .statelog path
        log_interval: only log every N-th tick (default 1 = every tick)
        target_pos:   (x, y) of the light source (default (7, 7))
    '''

    def __init__(self, homeostat, khepera_sim, filepath,
                 log_interval=1, target_pos=(7, 7)):
        self._hom = homeostat
        self._sim = khepera_sim
        self._robot = khepera_sim.allBodies['Khepera']
        self._target = target_pos
        self._interval = max(1, int(log_interval))
        self._headless = getattr(homeostat, '_headless', False)

        # Compute minimum dt_fast across all units for physical time column
        self._min_dt_fast = 1.0
        for u in homeostat.homeoUnits:
            dt = getattr(u, '_dt_fast', 1.0)
            if dt < self._min_dt_fast:
                self._min_dt_fast = dt

        # Ordered unit list (same order as homeostat.homeoUnits)
        self._units = list(homeostat.homeoUnits)
        self._unit_names = [u.name for u in self._units]

        # Build connection column info and JIT index mapping
        self._conn_keys = []       # list of "w_{unit}<-{from}" strings
        self._conn_sources = []    # list of (unit, conn) or (unit, jit_idx) tuples
        self._has_ou = []          # per-unit: True if unit has OU uniselector

        from Core.HomeoUniselectorContinuous import HomeoUniselectorContinuous

        for unit in self._units:
            has_ou = isinstance(getattr(unit, 'uniselector', None),
                                HomeoUniselectorContinuous)
            self._has_ou.append(has_ou)

            if self._headless and hasattr(unit, '_jit_incoming_units'):
                # Build mapping: JIT index -> connection identity
                active = [c for c in unit.inputConnections
                          if c.isActive() and c.incomingUnit.isActive()]
                for jit_idx, conn in enumerate(active):
                    col = 'w_%s<-%s' % (unit.name, conn.incomingUnit.name)
                    self._conn_keys.append(col)
                    self._conn_sources.append(('jit', unit, jit_idx))
            else:
                for conn in unit.inputConnections:
                    if conn.isActive() and conn.incomingUnit.isActive():
                        col = 'w_%s<-%s' % (unit.name, conn.incomingUnit.name)
                        self._conn_keys.append(col)
                        self._conn_sources.append(('conn', unit, conn))

        # Build column header
        cols = ['tick', 'phys_time', 'robot_x', 'robot_y', 'heading', 'distance',
                'left_sensor', 'right_sensor', 'left_speed', 'right_speed']
        for name in self._unit_names:
            cols += ['%s_critDev' % name, '%s_output' % name,
                     '%s_velocity' % name, '%s_torque' % name,
                     '%s_stress' % name]
        cols += self._conn_keys
        for i, name in enumerate(self._unit_names):
            if self._has_ou[i]:
                cols.append('sigma_%s' % name)
        self._columns = cols
        self._ncols = len(cols)

        # Open file and write header
        self._f = open(filepath, 'w')
        self._write_metadata_header()
        self._f.write('\t'.join(self._columns) + '\n')
        self._f.flush()

    def _write_metadata_header(self):
        '''Write #-prefixed metadata lines with constant parameters.'''
        f = self._f
        f.write('# HomeostatStateLog v1\n')
        f.write('# date\t%s\n' % time.strftime('%Y-%m-%d %H:%M:%S'))
        f.write('# log_interval\t%d\n' % self._interval)
        f.write('# target_x\t%.3f\n' % self._target[0])
        f.write('# target_y\t%.3f\n' % self._target[1])
        f.write('# headless\t%s\n' % self._headless)
        f.write('# min_dt_fast\t%.6f\n' % self._min_dt_fast)
        f.write('# n_units\t%d\n' % len(self._units))

        from Core.HomeoUniselectorContinuous import HomeoUniselectorContinuous

        for i, unit in enumerate(self._units):
            prefix = '# unit_%s' % unit.name
            f.write('%s_type\t%s\n' % (prefix, type(unit).__name__))
            f.write('%s_mass\t%.6f\n' % (prefix, unit.mass))
            f.write('%s_viscosity\t%.6f\n' % (prefix, unit.viscosity))
            f.write('%s_maxDeviation\t%.6f\n' % (prefix, unit.maxDeviation))
            dt_fast = getattr(unit, '_dt_fast', 1.0)
            f.write('%s_dt_fast\t%.6f\n' % (prefix, dt_fast))
            if self._has_ou[i]:
                unis = unit.uniselector
                f.write('%s_tau_a\t%.6f\n' % (prefix, unis._tau_a))
                f.write('%s_theta\t%.6f\n' % (prefix, unis._theta))
                f.write('%s_sigma_base\t%.6f\n' % (prefix, unis._sigma_base))
                f.write('%s_sigma_crit\t%.6f\n' % (prefix, unis._sigma_crit))
                f.write('%s_stress_exponent\t%.6f\n' % (
                    prefix, unis._stress_exponent))

    def log_tick(self, tick):
        '''Write one row of state data.  Call after all units have updated.'''
        if tick % self._interval != 0:
            return

        robot = self._robot
        rx = robot.body.position[0]
        ry = robot.body.position[1]
        heading = degrees(robot.body.angle) % 360
        dist = sqrt((rx - self._target[0])**2 + (ry - self._target[1])**2)
        l_sensor = robot.getSensorRead('leftEye')
        r_sensor = robot.getSensorRead('rightEye')
        l_speed = robot.leftSpeed
        r_speed = robot.rightSpeed

        phys_time = tick * self._min_dt_fast

        vals = ['%d' % tick,
                '%.6f' % phys_time,
                '%.6f' % rx, '%.6f' % ry,
                '%.3f' % heading, '%.6f' % dist,
                '%.6f' % l_sensor, '%.6f' % r_sensor,
                '%.6f' % l_speed, '%.6f' % r_speed]

        # Per-unit columns
        for unit in self._units:
            vals.append('%.6f' % unit.criticalDeviation)
            vals.append('%.6f' % unit.currentOutput)
            vals.append('%.6f' % unit.currentVelocity)
            vals.append('%.6f' % unit.inputTorque)
            vals.append('%.6f' % unit.stressLevel())

        # Connection weights (signed = weight * switch)
        for source in self._conn_sources:
            if source[0] == 'jit':
                _, unit, jit_idx = source
                w = unit._jit_weights[jit_idx] * unit._jit_switches[jit_idx]
            else:
                _, unit, conn = source
                w = conn.weight * conn.switch
            vals.append('%.6f' % w)

        # OU sigma columns
        for i, unit in enumerate(self._units):
            if self._has_ou[i]:
                stress = unit.stressLevel()
                sigma = unit.uniselector.sigma(stress)
                vals.append('%.6f' % sigma)

        self._f.write('\t'.join(vals) + '\n')

    def flush(self):
        '''Flush the output buffer to disk.'''
        self._f.flush()

    def close(self):
        '''Flush and close the log file.'''
        if self._f and not self._f.closed:
            self._f.flush()
            self._f.close()
