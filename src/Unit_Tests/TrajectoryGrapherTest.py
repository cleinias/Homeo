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


if __name__ == '__main__':
    unittest.main()
