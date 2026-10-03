'''
Created on Oct 2, 2026

@author: stefano

Trajectory files written by KheperaSimulation.  Every world-setting method
creates a new RobotTrajectoryWriter, which opens a file at once; setting a
world up again must close the previous writer's file, whether or not the
world was reset in between.
'''
import os
import tempfile
import unittest

try:
    from KheperaSimulator.KheperaSimulator import KheperaSimulation
    HAS_BOX2D = True
except ImportError:
    HAS_BOX2D = False


@unittest.skipUnless(HAS_BOX2D, "Box2D not installed — KheperaSimulator unavailable")
class TrajectoryFilesClosedTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.sim = KheperaSimulation()
        self.sim.setupWorld('kheperaBraitenberg2_HOMEO_World', self.tmp.name)

    def tearDown(self):
        self.sim.saveTrajectory()
        self.tmp.cleanup()

    def testSetupAgainClosesThePreviousFile(self):
        "a world set up again, without a reset, closes the previous writer's file"
        first = self.sim.trajectoryWriter
        self.sim.setupWorld()
        self.assertIsNot(self.sim.trajectoryWriter, first)
        self.assertTrue(first.posFile.closed)
        self.assertFalse(self.sim.trajectoryWriter.posFile.closed)

    def testResetClosesThePreviousFile(self):
        "resetWorld closes the previous writer's file too (as it always did)"
        first = self.sim.trajectoryWriter
        self.sim.resetWorld()
        self.assertTrue(first.posFile.closed)

    def testClosedFileKeepsItsContent(self):
        "closing on a new setup loses nothing: the header and every row are there"
        first = self.sim.trajectoryWriter
        for _ in range(5):
            self.sim.advanceSim()
        # Elsewhere: 'Unspecified' files are named to the second, so a second
        # setup within the same second would reopen -- and empty -- this one.
        with tempfile.TemporaryDirectory() as elsewhere:
            self.sim.setupWorld(dataDir=elsewhere)
            self.sim.saveTrajectory()
        with open(first.posFile.name) as f:
            lines = f.read().splitlines()
        self.assertTrue(lines[0].startswith('# Position data'))
        rows = [l for l in lines if l and not l.startswith('#') and l.count('\t') >= 5]
        self.assertEqual(len(rows), 5)


@unittest.skipUnless(HAS_BOX2D, "Box2D not installed — KheperaSimulator unavailable")
class DefaultDataDirTest(unittest.TestCase):
    """With no data directory given, trajectory files go to today's data
       directory -- never to the current directory, where they used to land as
       stray trajData-ID-Unspecified-*.traj files."""

    def setUp(self):
        self.data = tempfile.TemporaryDirectory()      # stands in for SimulationsData
        self.cwd = tempfile.TemporaryDirectory()       # wherever the run was started
        self._oldcwd = os.getcwd()
        self._oldenv = os.environ.get('HOMEO_DATA_DIR')
        os.environ['HOMEO_DATA_DIR'] = self.data.name
        os.chdir(self.cwd.name)

    def tearDown(self):
        os.chdir(self._oldcwd)
        if self._oldenv is None:
            os.environ.pop('HOMEO_DATA_DIR', None)
        else:
            os.environ['HOMEO_DATA_DIR'] = self._oldenv
        self.cwd.cleanup()
        self.data.cleanup()

    def testWorldWithoutDataDirWritesToTodaysDataDir(self):
        from Helpers.General_Helper_Functions import dated_data_dir
        sim = KheperaSimulation()
        sim.setupWorld('kheperaBraitenberg2_HOMEO_World')
        sim.saveTrajectory()
        self.assertEqual(os.listdir(self.cwd.name), [])
        self.assertEqual(os.path.dirname(sim.trajectoryWriter.posFile.name), dated_data_dir())
        self.assertTrue(dated_data_dir().startswith(self.data.name))

    def testBackendPassesItsDataDirOnBeforeTheWorldStarts(self):
        "SimulatorBackendHOMEO(dataDir=...) used to ignore its argument"
        from Simulator.SimulatorBackend import SimulatorBackendHOMEO
        with tempfile.TemporaryDirectory() as out:
            backend = SimulatorBackendHOMEO(robotName='Khepera', dataDir=out)
            backend.start('kheperaBraitenberg2_HOMEO_World')
            backend.kheperaSimulation.saveTrajectory()
            self.assertEqual(len(os.listdir(out)), 1)
        self.assertEqual(os.listdir(self.cwd.name), [])


if __name__ == "__main__":
    unittest.main()
