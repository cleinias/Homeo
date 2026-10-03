'''
Created on Oct 2, 2026

@author: stefano

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

    def testDefaultIsTheOriginal2b(self):
        "the default, crossed ++, is the vehicle --fixed-weights always built"
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
        np.random.seed(11)
        for _ in range(2000):
            x, y, heading = D._random_start_pose(target, True, (4.0, 8.0))
            d = np.hypot(x - target[0], y - target[1])
            self.assertTrue(4.0 <= d <= 8.0, d)
            self.assertTrue(0 <= heading < 360)

    def testDefaultRangeUnchanged(self):
        "without a range, the draws are exactly the old 2-6 ones"
        np.random.seed(5)
        new = D._random_start_pose((7, 7), True)
        np.random.seed(5)
        heading = np.random.uniform(0, 360)
        d = np.random.uniform(2.0, 6.0)
        bearing = np.random.uniform(0, 2 * np.pi)
        self.assertEqual(new, (7 + d * np.cos(bearing), 7 + d * np.sin(bearing), heading))

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


if __name__ == "__main__":
    unittest.main()
