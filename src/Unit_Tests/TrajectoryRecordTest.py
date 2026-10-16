'''
What a .traj file records (review findings HV-01, HV-06).

The header is written at the first simulator step, so it records the world
as the experiment set it up -- a darkness source's negative intensity, a
random start pose -- and a header line gives the sampling, in simulator steps
and steps per homeostat tick, from which TrajectoryGrapher computes ticks.
'''
import glob
import os
import tempfile
import unittest

from Helpers.RobotTrajectoryWriter import configureTrajectoryDefaults
from Helpers.TrajectoryGrapher import (loadTrajectory, readDataFileHeader, readInitPosFromHeader,
                                       readLightsFromHeader, ticksFromRows, _hasDarknessSource)
import HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct as D


class TrajectoryRecordTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ['HOMEO_DATA_DIR'] = self.tmp.name
        self.addCleanup(configureTrajectoryDefaults, 1, True)

    def tearDown(self):
        os.environ.pop('HOMEO_DATA_DIR', None)
        self.tmp.cleanup()

    def run_and_read(self, **kwargs):
        r = D.run_headless(quiet=True, seed=1, **kwargs)
        r['backend'].kheperaSimulation.saveTrajectory()
        path = r['backend'].kheperaSimulation.trajectoryWriter.posFile.name
        return r, path

    def testHeaderRecordsTheWorldAsSetUp(self):
        r, path = self.run_and_read(total_steps=500, report_interval=500, light_intensity=-100,
                                    random_start=True)
        header = readDataFileHeader(path)
        self.assertEqual(readLightsFromHeader(header)['TARGET'][2], -100.0)
        self.assertTrue(_hasDarknessSource(readLightsFromHeader(header)))
        x, y, heading = map(float, readInitPosFromHeader(header))
        self.assertAlmostEqual(x, r['start_x'], places=5)
        self.assertAlmostEqual(y, r['start_y'], places=5)
        self.assertAlmostEqual(heading, r['start_heading'] % 360, places=1)
        from Helpers.General_Helper_Functions import homeo_version
        self.assertIn('# Homeo\t%s' % homeo_version(), [l.rstrip('\n') for l in header])
        self.assertIn('# Robot model\tepuck2', [l.rstrip('\n') for l in header])

    def testTicksFromRows(self):
        for interval in (1, 10):
            with self.subTest(interval=interval):
                configureTrajectoryDefaults(interval=interval)
                r, path = self.run_and_read(total_steps=500, report_interval=500)
                header, _, rows = loadTrajectory(path)
                self.assertEqual(ticksFromRows(header, rows), r['steps_run'])

    def testOlderHeaders(self):
        "Files before 13 Oct 2026: 2 steps per tick; 'every N ticks' meant N steps"
        self.assertEqual(ticksFromRows(['# Position data\n'], 2000), 1000)
        self.assertEqual(ticksFromRows(['# Sampled every 100 ticks\n'], 1000), 50000)

    def testOneTripletPerSource(self):
        "The column line names a light_x, light_y, distance triplet per source"
        import threading
        import numpy as np
        import Simulator.HomeoExperiments as HE
        from Simulator.SimulatorBackend import SimulatorBackendHOMEO
        backend = SimulatorBackendHOMEO(lock=threading.Lock(), robotName='Khepera')
        backend.kheperaSimulation.dataDir = self.tmp.name
        setup = HE.initializeBraiten3c_GA_continuous_weightfree_fixed_v2   # the 3c world
        setup(np.full(setup.genomeSize, 0.5), backendSimulator=backend)
        sim = backend.kheperaSimulation
        for _ in range(3):
            sim.advanceSim()
        sim.saveTrajectory()
        lines = open(sim.trajectoryWriter.posFile.name).read().splitlines()
        columns = [l for l in lines if l.startswith('# robot_x')][0][2:].split('\t')
        rows = [l for l in lines if l and not l.startswith('#')
                and len(l.split()) > 2 and l.split()[0][0] in '-0123456789'][-1]
        self.assertGreater(len(sim.trajectoryWriter.lights), 1)
        self.assertEqual(len(columns), len(rows.split('\t')))


if __name__ == '__main__':
    unittest.main()
