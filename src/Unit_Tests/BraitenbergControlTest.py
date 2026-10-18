# Copyright (C) 2026 Stefano Franchi
#
# This file is part of Homeo, a simulation of Ashby's homeostat and of
# homeostat-controlled robots.
#
# Homeo is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# Homeo is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with Homeo.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

'''
The non-adaptive Braitenberg 2 vehicle of phototaxis_braitenberg2_direct
(--fixed-weights): its eight wirings -- crossed (2b) or uncrossed (2a), each
with the four sign pairs, left eye first -- and the random start pose.
'''
import os
import subprocess
import sys
import tempfile
import unittest

import numpy as np

try:
    from HomeoExperiments.KheperaExperiments import phototaxis_braitenberg2_direct as D
    HAS_BOX2D = True
except ImportError:
    HAS_BOX2D = False


def _motor_inputs(hom):
    """{(sensor, motor): signed weight} for every ACTIVE sensor -> motor
       connection, plus {(motor, motor): signed weight} for active motor ->
       motor ones.  A HomeoConnection keeps the magnitude in `weight` and the
       sign in `switch`."""
    active = {}
    for u in hom.homeoUnits:
        if 'Motor' not in u.name:
            continue
        for c in u.inputConnections:
            if c.status and c.incomingUnit is not u:
                active[(c.incomingUnit.name, u.name)] = c.weight * c.switch
    return active


@unittest.skipUnless(HAS_BOX2D, "Box2D not installed — KheperaSimulator unavailable")
class ControlWiringTest(unittest.TestCase):

    def _build(self, wiring, signs, seed=7):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ['HOMEO_DATA_DIR'] = tmp
            try:
                hom, backend, _ = D.setup_phototaxis(seed=seed, fixed_weights=True,
                                                     wiring=wiring, signs=signs)
            finally:
                os.environ.pop('HOMEO_DATA_DIR', None)
            backend.kheperaSimulation.saveTrajectory()
        return hom, backend

    def testEachVariantWiresExactlyItsTwoConnections(self):
        "each of the 8 variants: the two intended connections, with their signs, and nothing else"
        w = D.CONTROL_CROSS_WEIGHT
        for wiring, pairs in (
                ('crossed', (('Left Sensor', 'Right Motor'), ('Right Sensor', 'Left Motor'))),
                ('uncrossed', (('Left Sensor', 'Left Motor'), ('Right Sensor', 'Right Motor')))):
            for signs in D.CONTROL_SIGNS:
                hom, _ = self._build(wiring, signs)
                expected = {pair: (w if sign == '+' else -w)
                            for pair, sign in zip(pairs, signs)}
                self.assertEqual(_motor_inputs(hom), expected, (wiring, signs))

    def testDefaultIsCrossedPlusPlus2b(self):
        "the default is crossed ++"
        hom, backend = self._build('crossed', '++')
        self.assertEqual(_motor_inputs(hom),
                         {('Left Sensor', 'Right Motor'): D.CONTROL_CROSS_WEIGHT,
                          ('Right Sensor', 'Left Motor'): D.CONTROL_CROSS_WEIGHT})
        self.assertEqual(backend.kheperaSimulation.experimentName,
                         'phototaxis_braitenberg2_direct_control_crossed_pp')

    def testBadWiringOrSignsAreRejected(self):
        with self.assertRaises(ValueError):
            self._build('sideways', '++')
        with self.assertRaises(ValueError):
            self._build('crossed', '+0')


@unittest.skipUnless(HAS_BOX2D, "Box2D not installed — KheperaSimulator unavailable")
class StartPoseTest(unittest.TestCase):

    def testStartRangeIsRespected(self):
        "random positions fall within the requested distance from the light"
        target = (7, 7)
        rng = np.random.default_rng(11)
        for _ in range(2000):
            x, y, heading = D.common.random_start_pose(target, True, (4.0, 8.0), rng=rng)
            d = np.hypot(x - target[0], y - target[1])
            self.assertTrue(4.0 <= d <= 8.0, d)
            self.assertTrue(0 <= heading < 360)

    def testDefaultRangeIsTwoToSix(self):
        "without a range, the draws are the 2-6 ones: heading, distance, bearing"
        pose = D.common.random_start_pose((7, 7), True, rng=np.random.default_rng(5))
        rng = np.random.default_rng(5)
        heading = rng.uniform(0, 360)
        d = rng.uniform(2.0, 6.0)
        bearing = rng.uniform(0, 2 * np.pi)
        self.assertEqual(pose, (7 + d * np.cos(bearing), 7 + d * np.sin(bearing), heading))

    def testSameSeedSamePoseWhateverTheWiring(self):
        "a seed fixes the start pose for every variant, so batches can be paired"
        poses = set()
        with tempfile.TemporaryDirectory() as tmp:
            os.environ['HOMEO_DATA_DIR'] = tmp
            try:
                for wiring in D.CONTROL_WIRINGS:
                    for signs in D.CONTROL_SIGNS:
                        r = D.run_headless(total_steps=500, quiet=True, seed=31,
                                           fixed_weights=True, wiring=wiring, signs=signs,
                                           random_start=True, start_range=(4.0, 8.0))
                        r['backend'].kheperaSimulation.saveTrajectory()
                        poses.add((round(r['start_x'], 12), round(r['start_y'], 12),
                                   round(r['start_heading'], 9)))
            finally:
                os.environ.pop('HOMEO_DATA_DIR', None)
        self.assertEqual(len(poses), 1, poses)


@unittest.skipUnless(HAS_BOX2D, "Box2D not installed — KheperaSimulator unavailable")
class CommandLineTest(unittest.TestCase):
    """The options are validated before anything runs."""

    def _run(self, *args):
        src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with tempfile.TemporaryDirectory() as tmp:
            return subprocess.run(
                [sys.executable, '-m', 'HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct',
                 '--batch', '1', '--steps', '500', '--seed', '3', '--no-traj'] + list(args),
                cwd=src, env=dict(os.environ, HOMEO_DATA_DIR=tmp), capture_output=True,
                text=True, timeout=300)

    def testInvalidOptionsAreRejected(self):
        for args, message in (
                (('--fixed-weights', '--signs', '+0'), '--signs must be one of'),
                (('--signs', '+-'), 'apply only with --fixed-weights'),
                (('--uncrossed',), 'apply only with --fixed-weights'),
                (('--fixed-weights', '--start-range', '4', '8'), 'only with --random-start'),
                (('--fixed-weights', '--random-start', '--start-range', '8', '4'), '0 < MIN <= MAX')):
            r = self._run(*args)
            self.assertNotEqual(r.returncode, 0, args)
            self.assertIn(message, r.stderr + r.stdout, args)

    def testBatchCsvRecordsTheVariant(self):
        "the batch CSV names the variant and records wiring and signs"
        src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run(
                [sys.executable, '-m', 'HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct',
                 '--batch', '1', '--steps', '500', '--seed', '3', '--no-traj',
                 '--fixed-weights', '--uncrossed', '--signs', '-+',
                 '--random-start', '--start-range', '4', '8'],
                cwd=src, env=dict(os.environ, HOMEO_DATA_DIR=tmp), capture_output=True,
                text=True, timeout=300)
            self.assertEqual(r.returncode, 0, r.stderr[-1500:])
            import csv, glob
            csvs = glob.glob(os.path.join(tmp, '*', 'batch_direct_control_uncrossed_mp_*.csv'))
            self.assertEqual(len(csvs), 1, os.listdir(tmp))
            row = list(csv.DictReader(open(csvs[0])))[0]
            self.assertEqual((row['wiring'], row['signs']), ('uncrossed', '-+'))
            self.assertTrue(4.0 <= float(row['start_dist']) <= 8.0)

    def testInvalidMotorIsRejected(self):
        for args, message in ((('--motor', 'aristotelian'), 'only with --fixed-weights'),
                              (('--fixed-weights', '--motor', 'quantum'), '--motor must be one of')):
            r = self._run(*args)
            self.assertNotEqual(r.returncode, 0, args)
            self.assertIn(message, r.stderr + r.stdout, args)

    def testBatchCsvRecordsTheMotor(self):
        "an Aristotelian batch is named for its motor and records it"
        src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run(
                [sys.executable, '-m', 'HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct',
                 '--batch', '1', '--steps', '500', '--seed', '3', '--no-traj',
                 '--fixed-weights', '--motor', 'aristotelian', '--random-start', '--spin', '0.05'],
                cwd=src, env=dict(os.environ, HOMEO_DATA_DIR=tmp), capture_output=True,
                text=True, timeout=300)
            self.assertEqual(r.returncode, 0, r.stderr[-1500:])
            import csv, glob
            csvs = glob.glob(os.path.join(tmp, '*', 'batch_direct_control_arist_crossed_pp_cw0.05_*.csv'))
            self.assertEqual(len(csvs), 1, os.listdir(tmp))
            row = list(csv.DictReader(open(csvs[0])))[0]
            self.assertEqual(row['motor'], 'aristotelian')

    def testInvalidEyeOptionsAreRejected(self):
        for args, message in ((('--eye-response', 'cubic'), '--eye-response must be'),
                              (('--eye-response', 'log', '--eye-threshold', '0'), '> 0 for a log eye'),
                              (('--eye-saturation', '-1'), '--eye-saturation must be > 0')):
            r = self._run('--fixed-weights', *args)
            self.assertNotEqual(r.returncode, 0, args)
            self.assertIn(message, r.stderr + r.stdout, args)

    def testInvalidSpinIsRejected(self):
        for args, message in ((('--spin', 'fast'), '--spin needs a number'),
                              (('--spin', '1.5'), '|RATE| < 1')):
            r = self._run('--fixed-weights', *args)
            self.assertNotEqual(r.returncode, 0, args)
            self.assertIn(message, r.stderr + r.stdout, args)

    def testBatchCsvRecordsTheSpin(self):
        "a spinning batch is named for its spin and records it"
        src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run(
                [sys.executable, '-m', 'HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct',
                 '--batch', '1', '--steps', '500', '--seed', '3', '--no-traj',
                 '--fixed-weights', '--signs', '+-', '--random-start', '--spin', '0.05'],
                cwd=src, env=dict(os.environ, HOMEO_DATA_DIR=tmp), capture_output=True,
                text=True, timeout=300)
            self.assertEqual(r.returncode, 0, r.stderr[-1500:])
            import csv, glob
            csvs = glob.glob(os.path.join(tmp, '*', 'batch_direct_control_crossed_pm_cw0.05_*.csv'))
            self.assertEqual(len(csvs), 1, os.listdir(tmp))
            row = list(csv.DictReader(open(csvs[0])))[0]
            self.assertEqual(float(row['spin']), 0.05)
            jsons = glob.glob(os.path.join(tmp, '*', 'phototaxis_braitenberg2_direct_control_crossed_pm_cw0.05-*.json'))
            self.assertEqual(len(jsons), 1)


@unittest.skipUnless(HAS_BOX2D, "Box2D not installed — KheperaSimulator unavailable")
class SpinTest(unittest.TestCase):
    """--spin: a constant, opposite wheel-speed offset on the two motors."""

    def _spin_in_the_dark(self, spin, ticks=1000):
        """Heading change (deg) and displacement over `ticks`, starting at the
           default position facing away from the light, so that only the spin
           can move the vehicle."""
        from math import degrees, hypot
        with tempfile.TemporaryDirectory() as tmp:
            os.environ['HOMEO_DATA_DIR'] = tmp
            backend = None              # unbound if the setup raises
            try:
                hom, backend, _ = D.setup_phototaxis(seed=7, fixed_weights=True, spin=spin)
                robot = backend.kheperaSimulation.allBodies['Khepera']
                D.set_start_pose(robot, heading=225)
                hom.slowingFactor = 0
                hom.collectsData = False
                hom._headless = True
                for u in hom.homeoUnits:
                    u._headless = True
                a0, x0, y0 = robot.body.angle, robot.body.position[0], robot.body.position[1]
                hom.runFor(ticks)
                self.assertEqual((robot.getSensorRead('leftEye'),
                                  robot.getSensorRead('rightEye')), (0, 0))
                return (degrees(robot.body.angle - a0),
                        hypot(robot.body.position[0] - x0, robot.body.position[1] - y0))
            finally:
                os.environ.pop('HOMEO_DATA_DIR', None)
                if backend is not None:
                    backend.kheperaSimulation.saveTrajectory()

    def testSpinTurnsInPlaceInTheRequestedDirection(self):
        "positive spin turns clockwise (heading decreases), negative counter-clockwise, in place"
        cw, cw_moved = self._spin_in_the_dark(0.05, ticks=250)
        ccw, ccw_moved = self._spin_in_the_dark(-0.05, ticks=250)
        still, still_moved = self._spin_in_the_dark(0.0, ticks=250)
        # differential-drive kinematics, e-puck2 (52 mm between the wheels,
        # top speed capped at 24.3 mm/s, motors at 0.8 of it): 0.137 deg/tick
        # (the K-Junior: 0.074); 250 ticks keep
        # the light, behind, in the eyes' unseen rear sector (88 degrees)
        self.assertAlmostEqual(cw, -34.3, delta=0.5)
        self.assertAlmostEqual(cw, -ccw, delta=0.5)
        self.assertEqual(still, 0.0)
        self.assertEqual(still_moved, 0.0)
        self.assertLess(max(cw_moved, ccw_moved), 0.01)

    def testSpinIsOppositeOnTheTwoMotorsAndNamed(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ['HOMEO_DATA_DIR'] = tmp
            try:
                hom, backend, _ = D.setup_phototaxis(seed=7, fixed_weights=True, spin=0.05)
            finally:
                os.environ.pop('HOMEO_DATA_DIR', None)
            backend.kheperaSimulation.saveTrajectory()
        units = {u.name: u for u in hom.homeoUnits}
        self.assertEqual((units['Left Motor']._speedBias, units['Right Motor']._speedBias),
                         (0.05, -0.05))
        self.assertEqual(backend.kheperaSimulation.experimentName,
                         'phototaxis_braitenberg2_direct_control_crossed_pp_cw0.05')
        self.assertEqual(D.spin_tag(0), '')
        self.assertEqual(D.spin_tag(-0.1), '_ccw0.1')

    def testWheelSpeedStaysWithinTheMotorLimit(self):
        "the bias is clipped: a wheel never exceeds the motor's max speed"
        with tempfile.TemporaryDirectory() as tmp:
            os.environ['HOMEO_DATA_DIR'] = tmp
            backend = None              # unbound if the setup raises
            try:
                hom, backend, _ = D.setup_phototaxis(seed=7, fixed_weights=True, spin=0.9)
                hom.slowingFactor = 0
                hom.collectsData = False
                hom._headless = True
                for u in hom.homeoUnits:
                    u._headless = True
                motors = [u for u in hom.homeoUnits if 'Motor' in u.name]
                for t in range(50, 2001, 50):   # the light is in view: it drives too
                    hom.runFor(t)
                    for m in motors:
                        # + 0.0005: the speed is rounded to 3 places after clipping
                        self.assertLessEqual(abs(m.transducer.funcParameters),
                                             m._maxSpeed + 0.0005)
            finally:
                os.environ.pop('HOMEO_DATA_DIR', None)
                if backend is not None:
                    backend.kheperaSimulation.saveTrajectory()

    def testSameSeedSamePoseWithOrWithoutSpin(self):
        "the spin draws nothing, so a spinning batch pairs with a non-spinning one"
        poses = set()
        with tempfile.TemporaryDirectory() as tmp:
            os.environ['HOMEO_DATA_DIR'] = tmp
            try:
                for spin in (0.0, 0.05):
                    r = D.run_headless(total_steps=500, quiet=True, seed=31, fixed_weights=True,
                                       random_start=True, start_range=(4.0, 8.0), spin=spin)
                    r['backend'].kheperaSimulation.saveTrajectory()
                    self.assertEqual(r['spin'], spin)
                    poses.add((r['start_x'], r['start_y'], r['start_heading']))
            finally:
                os.environ.pop('HOMEO_DATA_DIR', None)
        self.assertEqual(len(poses), 1, poses)


@unittest.skipUnless(HAS_BOX2D, "Box2D not installed — KheperaSimulator unavailable")
class AristotelianVehiclesTurnTest(unittest.TestCase):
    """Braitenberg's two excitatory vehicles with his memoryless motors do
       what he says: with the light 30 degrees to one side, 2b (crossed)
       turns toward it, 2a (uncrossed) away from it, on either side.  (The
       Newtonian vehicles' runs are PhototaxisBehaviourTest's.)"""

    def _bearings(self, wiring, motor, heading, ticks=1500):
        "The light's bearing from the robot's heading (deg, left > 0), before and after"
        from math import atan2, degrees, pi
        def bearing(body):
            to = atan2(D.TARGET_POS[1] - body.position[1], D.TARGET_POS[0] - body.position[0])
            return degrees((to - body.angle + pi) % (2 * pi) - pi)
        with tempfile.TemporaryDirectory() as tmp:
            os.environ['HOMEO_DATA_DIR'] = tmp
            backend = None              # unbound if the setup raises
            try:
                hom, backend, _ = D.setup_phototaxis(seed=7, fixed_weights=True, wiring=wiring,
                                                     signs='++', motor=motor)
                robot = backend.kheperaSimulation.allBodies['Khepera']
                D.set_start_pose(robot, heading=heading)
                before = bearing(robot.body)
                hom.slowingFactor = 0
                hom.collectsData = False
                hom._headless = True
                for u in hom.homeoUnits:
                    u._headless = True
                hom.runFor(ticks)
                return before, bearing(robot.body)
            finally:
                os.environ.pop('HOMEO_DATA_DIR', None)
                if backend is not None:
                    backend.kheperaSimulation.saveTrajectory()

    def testTwoBTurnsTowardTheLightAndTwoAAway(self):
        for motor in ('aristotelian',):
            for heading in (15, 75):            # the light 30 degrees left, then right
                with self.subTest(motor=motor, heading=heading):
                    before, after = self._bearings('crossed', motor, heading)
                    self.assertAlmostEqual(abs(before), 30, places=3)
                    self.assertLess(abs(after), 10)
                    before, after = self._bearings('uncrossed', motor, heading)
                    self.assertGreater(abs(after), 90)
                    self.assertEqual(after > 0, before > 0)       # turned away on its own side


@unittest.skipUnless(HAS_BOX2D, "Box2D not installed — KheperaSimulator unavailable")
class AristotelianMotorTest(unittest.TestCase):
    """--motor aristotelian: the true Braitenberg vehicle.  Each motor's output
       depends only on its sensor's reading on the previous tick -- no memory,
       no dynamics: s for an excitatory connection, 1 - s for an inhibitory one
       (Braitenberg's Vehicle 3: slowed down from a resting drive) -- and the
       wheel speed is linear in it."""

    def _run(self, wiring, signs, ticks, spin=0.0, heading=None, perturb_at=None):
        """Per tick: (sensor outputs before the tick, motor outputs and wheel
           speeds after it).  perturb_at: a tick before which both motors'
           deviations are set to arbitrary values, to show nothing carries over."""
        rows = []
        with tempfile.TemporaryDirectory() as tmp:
            os.environ['HOMEO_DATA_DIR'] = tmp
            backend = None              # unbound if the setup raises
            try:
                hom, backend, _ = D.setup_phototaxis(seed=7, fixed_weights=True, wiring=wiring,
                                                     signs=signs, spin=spin, motor='aristotelian')
                if heading is not None:
                    D.set_start_pose(backend.kheperaSimulation.allBodies['Khepera'], heading=heading)
                hom.slowingFactor = 0
                hom.collectsData = False
                hom._headless = True
                for u in hom.homeoUnits:
                    u._headless = True
                units = {u.name: u for u in hom.homeoUnits}
                for t in range(1, ticks + 1):
                    if t == perturb_at:
                        # A consistent state: the deviation AND the output that
                        # goes with it (the self-connection feeds back the output).
                        for name, dev in (('Left Motor', 7.3), ('Right Motor', -4.1)):
                            units[name].criticalDeviation = dev
                            units[name].computeOutput()
                    sensors = {n: units[n].currentOutput for n in ('Left Sensor', 'Right Sensor')}
                    hom.runFor(t)
                    rows.append((sensors,
                                 {n: units[n].currentOutput for n in ('Left Motor', 'Right Motor')},
                                 {n: units[n].transducer.funcParameters for n in ('Left Motor', 'Right Motor')},
                                 units))
            finally:
                os.environ.pop('HOMEO_DATA_DIR', None)
                if backend is not None:
                    backend.kheperaSimulation.saveTrajectory()
        return rows

    def testMotorOutputIsThePreviousSensorReading(self):
        "every wiring: out(t+1) = s(t) if excitatory, 1 - s(t) if inhibitory, exactly"
        lit = 0
        for wiring, pairs in (
                ('crossed', (('Left Sensor', 'Right Motor'), ('Right Sensor', 'Left Motor'))),
                ('uncrossed', (('Left Sensor', 'Left Motor'), ('Right Sensor', 'Right Motor')))):
            for signs in D.CONTROL_SIGNS:
                for sensors, motors, _, _ in self._run(wiring, signs, 150):
                    for (sensor, motor), sign in zip(pairs, signs):
                        expected = sensors[sensor] if sign == '+' else 1 - sensors[sensor]
                        self.assertAlmostEqual(motors[motor], expected, places=12,
                                               msg=(wiring, signs, sensor, motor))
                        lit += sensors[sensor] != 0
        self.assertGreater(lit, 1000)       # the light was really in view

    def testNoStateCarriesOverFromTickToTick(self):
        "an arbitrary deviation is gone after one tick: the motor has no memory"
        rows = self._run('crossed', '++', 30, perturb_at=20)
        sensors, motors = rows[19][0], rows[19][1]
        self.assertNotEqual(sensors['Left Sensor'], 0)
        self.assertAlmostEqual(motors['Right Motor'], sensors['Left Sensor'], places=12)
        self.assertAlmostEqual(motors['Left Motor'], sensors['Right Sensor'], places=12)

    def testWheelSpeedIsLinearWithTheNewtonianMax(self):
        "wheel speed = output x max speed, the max being the Newtonian vehicle's (0.8 of the range)"
        for _, motors, wheels, units in self._run('crossed', '++', 100):
            for name in ('Left Motor', 'Right Motor'):
                maxSpeed = units[name].transducer.range()[1] * 0.8
                self.assertAlmostEqual(wheels[name], motors[name] * maxSpeed, places=9)
        self.assertNotAlmostEqual(max(r[2]['Right Motor'] for r in self._run('crossed', '++', 100)), 0)

    def testSelfWeightCancelsTheState(self):
        "the self-weight is derived from the mass and the range: 1 + c/(m maxDev) = 0"
        units = self._run('crossed', '++', 1)[0][3]
        for name in ('Left Motor', 'Right Motor'):
            u = units[name]
            c = u.inputConnections[0].weight * u.inputConnections[0].switch
            self.assertEqual(u.mass, D.ARIST_MASS)
            self.assertAlmostEqual(1 + c / (u.mass * u.maxDeviation), 0.0, places=12)
            self.assertEqual(type(u).__name__, 'HomeoUnitAristotelianActuator')

    def testSpinIsTheSameWheelSpeedAsTheNewtonianOne(self):
        "in the dark, spin 0.05 sets the wheels to +-0.05 x the shared max speed"
        _, _, wheels, units = self._run('crossed', '++', 50, spin=0.05, heading=225)[-1]
        maxSpeed = units['Left Motor'].transducer.range()[1] * 0.8
        self.assertAlmostEqual(wheels['Left Motor'], 0.05 * maxSpeed, places=12)
        self.assertAlmostEqual(wheels['Right Motor'], -0.05 * maxSpeed, places=12)

    def testSixUnitsAndConstantOutputs(self):
        "Drive and Spin hold output 1 all run, with no inputs; only the intended links leave them"
        rows = self._run('crossed', '--', 200, spin=0.05)
        units = rows[-1][3]
        self.assertEqual(sorted(units), sorted(['Left Motor', 'Right Motor', 'Left Sensor',
                                                'Right Sensor', 'Drive', 'Spin']))
        for name in D.CONSTANT_UNITS:
            self.assertEqual(units[name].currentOutput, 1.0)
            self.assertFalse(any(c.status for c in units[name].inputConnections))
        links = {(c.incomingUnit.name, u.name): c.weight * c.switch
                 for u in units.values() for c in u.inputConnections
                 if c.status and c.incomingUnit.name in D.CONSTANT_UNITS}
        self.assertEqual(links, {('Drive', 'Left Motor'): 1.0, ('Drive', 'Right Motor'): 1.0,
                                 ('Spin', 'Left Motor'): 0.05, ('Spin', 'Right Motor'): -0.05})

    def testOnlyInhibitedMotorsGetTheDrive(self):
        "mixed signs: the inhibited motor has the drive, the excited one has not"
        units = self._run('crossed', '+-', 1)[0][3]
        # crossed +-: Left Sensor -> Right Motor (+), Right Sensor -> Left Motor (-)
        drive = {m: [c.status for c in units[m].inputConnections if c.incomingUnit.name == 'Drive'][0]
                 for m in ('Left Motor', 'Right Motor')}
        self.assertEqual(drive, {'Left Motor': True, 'Right Motor': False})

    def testInhibitedVehicleRacesInTheDark(self):
        "no light in view: inhibited motors run at full speed, excited ones stand still"
        _, _, wheels, units = self._run('crossed', '--', 20, heading=225)[-1]
        maxSpeed = units['Left Motor'].transducer.range()[1] * 0.8
        self.assertAlmostEqual(wheels['Left Motor'], maxSpeed, places=12)
        self.assertAlmostEqual(wheels['Right Motor'], maxSpeed, places=12)
        _, _, wheels, _ = self._run('crossed', '++', 20, heading=225)[-1]
        self.assertEqual((wheels['Left Motor'], wheels['Right Motor']), (0.0, 0.0))

    def testStartPoseDoesNotDependOnTheMotor(self):
        "the constant units draw nothing: a seed's start pose is the same for both motors"
        poses = set()
        with tempfile.TemporaryDirectory() as tmp:
            os.environ['HOMEO_DATA_DIR'] = tmp
            try:
                for motor in D.CONTROL_MOTORS:
                    for signs in ('++', '--'):
                        r = D.run_headless(total_steps=500, quiet=True, seed=20261009, fixed_weights=True,
                                           signs=signs, motor=motor, random_start=True,
                                           start_range=(2.0, 6.0), spin=0.05)
                        r['backend'].kheperaSimulation.saveTrajectory()
                        poses.add((r['start_x'], r['start_y'], r['start_heading']))
            finally:
                os.environ.pop('HOMEO_DATA_DIR', None)
        self.assertEqual(len(poses), 1, poses)

    def testNamesAndValidation(self):
        self.assertEqual(D.control_variant_name('crossed', '+-', 'aristotelian'), 'arist_crossed_pm')
        self.assertEqual(D.control_variant_name('crossed', '+-'), 'crossed_pm')
        with tempfile.TemporaryDirectory() as tmp:
            os.environ['HOMEO_DATA_DIR'] = tmp
            try:
                with self.assertRaises(ValueError):
                    D.setup_phototaxis(seed=1, motor='aristotelian')       # needs fixed_weights
                with self.assertRaises(ValueError):
                    D.setup_phototaxis(seed=1, fixed_weights=True, motor='quantum')
            finally:
                os.environ.pop('HOMEO_DATA_DIR', None)


if __name__ == "__main__":
    unittest.main()
