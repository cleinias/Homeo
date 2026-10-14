'''
Created on Oct 14, 2026

@author: stefano

TrajectoryGrapher's chart options (review findings HV-02, HV-11).
'''
import os
import tempfile
import unittest
from unittest import mock

import matplotlib
matplotlib.use('Agg')

from Helpers import TrajectoryGrapher as TG


def writeTraj(path, rows=((4.0, 4.0), (5.0, 5.0), (6.0, 6.5)), intensity=100.0, eyeLines=()):
    "A minimal .traj file, as RobotTrajectoryWriter writes them."
    with open(path, 'w') as f:
        f.write('# Position data for Homeo simulation run\n#\n#\n')
        f.write('# Sampled every 1 simulator steps, 2 steps per homeostat tick\n')
        f.write('# Light sources positioned at:\n')
        f.write('TARGET\t7.000000\t7.000000\t%f\tTrue\n' % intensity)
        for line in eyeLines:
            f.write(line)
        f.write("# Vehicle's initial position at:\n4.000000\t 4.000000\t0.0\n\n")
        f.write('# robot_x\trobot_y\theading\tlight_x\tlight_y\tdistance\n')
        for x, y in rows:
            f.write('%f\t%f\t0.0\t7.0\t7.0\t1.0\n' % (x, y))


class TrajectoryGrapherTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def path(self, name):
        return os.path.join(self.tmp.name, name)

    def ringRadius(self, *argv):
        "The radius main() draws the no-input ring at, for these arguments."
        with mock.patch.object(TG, '_drawNoInputBoundary') as ring:
            TG.main(['homeo-traj'] + list(argv) + ['-o', self.path('out.png')])
        return ring.call_args.args[2]

    def testOneFileHonoursTheSensorRange(self):
        '''--sensor-range reaches the chart of a single file too: until 14 Oct
        2026 it fell back to 10 there (HV-02).'''
        writeTraj(self.path('a.traj'))
        writeTraj(self.path('b.traj'))
        self.assertEqual(self.ringRadius(self.path('a.traj'), '--sensor-range', '0'), 0)
        self.assertEqual(self.ringRadius(self.path('a.traj'), '--sensor-range', '3'), 3)
        self.assertEqual(self.ringRadius(self.path('a.traj'), self.path('b.traj'),
                                         '--sensor-range', '3'), 3)


    def eyeLines(self, threshold, saturation=100.0, response='linear'):
        return ['# Eye radius ratio\t0.5\n'] + [
            '# Eye\t%s\tthreshold\t%f\tsaturation\t%f\tresponse\t%s\n'
            % (eye, threshold, saturation, response) for eye in ('leftEye', 'rightEye')]

    def testTheRingIsWhereTheEyesStopSeeing(self):
        '''By default the ring is drawn where the eyes stop seeing the light,
        sqrt(intensity / threshold), from the header or the run's JSON; no ring
        for eyes with threshold 0 or when nothing records it.  Until 14 Oct
        2026 it was always at 10 (HV-11).'''
        import json
        writeTraj(self.path('log.traj'), eyeLines=self.eyeLines(1.0, 400.0, 'log'))
        writeTraj(self.path('thr4.traj'), eyeLines=self.eyeLines(4.0))
        writeTraj(self.path('zero.traj'), eyeLines=self.eyeLines(0.0))
        writeTraj(self.path('none.traj'))
        writeTraj(self.path('json.traj'))
        with open(self.path('json.json'), 'w') as f:
            json.dump({'settings': {'eye_threshold': 4.0}}, f)
        for name, radius in (('log', 10.0), ('thr4', 5.0), ('zero', 0.0), ('none', 0.0),
                             ('json', 5.0)):
            with self.subTest(name):
                self.assertAlmostEqual(self.ringRadius(self.path(name + '.traj')), radius)
        self.assertEqual(self.ringRadius(self.path('log.traj'), '--sensor-range', '2'), 2)
        # several runs: the ring if they agree, none if not
        self.assertAlmostEqual(self.ringRadius(self.path('thr4.traj'), self.path('json.traj')), 5.0)
        self.assertEqual(self.ringRadius(self.path('thr4.traj'), self.path('log.traj')), 0.0)

    def testRunsRecordTheirEyes(self):
        '''A run's .traj header records its eyes, so its chart finds the ring.'''
        import glob
        from HomeoExperiments.KheperaExperiments import phototaxis_braitenberg2_direct as D
        os.environ['HOMEO_DATA_DIR'] = self.tmp.name
        self.addCleanup(os.environ.pop, 'HOMEO_DATA_DIR', None)
        r = D.run_headless(total_steps=20, quiet=True, seed=3, eye_response='log',
                           eye_saturation=0.5)
        r['backend'].kheperaSimulation.saveTrajectory()
        [traj] = glob.glob(os.path.join(self.tmp.name, '*', '*.traj'))
        header = TG.readDataFileHeader(traj)
        eyes = TG.readEyesFromHeader(header)
        self.assertEqual(eyes['leftEye'], (1.0, 400.0, 'log'))
        self.assertEqual(eyes['rightEye'], (1.0, 400.0, 'log'))
        self.assertIn('# Eye radius ratio\t0.5\n', header)
        self.assertAlmostEqual(TG.noInputRadius(header, TG.readLightsFromHeader(header)), 10.0)


    def testATruncatedLastRowIsDropped(self):
        '''A last line with no newline -- a run still being written -- may be cut
        mid-number: it is not the final position (HV-08).'''
        path = self.path('live.traj')
        writeTraj(path, rows=((4.0, 4.0), (6.5, 6.987654)))
        _, xy, nRows = TG.loadTrajectory(path)
        self.assertEqual((nRows, list(xy[-1])), (2, [6.5, 6.987654]))
        with open(path, 'a') as f:
            f.write('6.500000\t6.9')
        _, xy, nRows = TG.loadTrajectory(path)
        self.assertEqual((nRows, list(xy[-1])), (2, [6.5, 6.987654]))


if __name__ == '__main__':
    unittest.main()
