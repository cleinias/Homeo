'''
Created on Feb 21, 2026

Test the Braitenberg 2_2 simulation using the internal HOMEO Khepera backend.
Requires Box2D, pyglet, and vrep packages to be installed.

@author: stefano
'''

import unittest
import threading
import tempfile
import shutil

try:
    from Simulator.SimulatorBackend import SimulatorBackendHOMEO
    from Simulator.HomeoExperiments import (initializeBraiten2_2,
                                             initializeBraiten2_2Pos,
                                             initializeBraiten2_2Neg)
    from RobotSimulator.HomeoUnitNewtonianTransduc import HomeoUnitNewtonianActuator, HomeoUnitInput
    _deps_available = True
except ImportError:
    _deps_available = False


@unittest.skipUnless(_deps_available, "Requires vrep, Box2D, and pyglet packages")
class Braiten2_2_HOMEO_Test(unittest.TestCase):
    """Tests for the Braitenberg 2_2 vehicle using the internal HOMEO backend."""

    def setUp(self):
        self.lock = threading.Lock()
        self.backend = SimulatorBackendHOMEO(lock=self.lock, robotName='Khepera')
        self._tmpdir = tempfile.mkdtemp()
        self.backend.kheperaSimulation.dataDir = self._tmpdir

    def tearDown(self):
        self.backend.quit()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_initialization_returns_homeostat(self):
        """initializeBraiten2_2 with HOMEO backend returns a working homeostat."""
        hom = initializeBraiten2_2(backendSimulator=self.backend)
        self.assertTrue(hom.isReadyToGo())

    def test_has_six_units(self):
        """The Braitenberg 2_2 homeostat has 6 units."""
        hom = initializeBraiten2_2(backendSimulator=self.backend)
        self.assertEqual(len(hom.homeoUnits), 6)

    def test_unit_types(self):
        """Two actuators, two HomeoUnitNewtonian (eyes), two HomeoUnitInput (sensors)."""
        hom = initializeBraiten2_2(backendSimulator=self.backend)
        actuators = [u for u in hom.homeoUnits if isinstance(u, HomeoUnitNewtonianActuator)]
        inputs = [u for u in hom.homeoUnits if isinstance(u, HomeoUnitInput)]
        self.assertEqual(len(actuators), 2)
        self.assertEqual(len(inputs), 2)

    def test_unit_names(self):
        """Units are named Left/Right Motor, Left/Right Eye, Left/Right Sensor."""
        hom = initializeBraiten2_2(backendSimulator=self.backend)
        names = {u.name for u in hom.homeoUnits}
        expected = {'Right Motor', 'Left Motor', 'Left Eye', 'Right Eye',
                    'Left Sensor', 'Right Sensor'}
        self.assertEqual(names, expected)

    def test_does_not_use_socket(self):
        """The HOMEO backend does not use sockets."""
        hom = initializeBraiten2_2(backendSimulator=self.backend)
        self.assertFalse(hom._usesSocket)

    def test_runs_without_error(self):
        """The homeostat runs for a number of steps without raising exceptions."""
        hom = initializeBraiten2_2(backendSimulator=self.backend)
        steps = 50
        hom.runFor(steps)
        self.assertEqual(hom.time, steps)

    def test_pos_convenience_wrapper(self):
        """initializeBraiten2_2Pos works with the HOMEO backend."""
        hom = initializeBraiten2_2Pos(backendSimulator=self.backend)
        self.assertTrue(hom.isReadyToGo())
        hom.runFor(10)
        self.assertEqual(hom.time, 10)

    def test_neg_convenience_wrapper(self):
        """initializeBraiten2_2Neg works with the HOMEO backend."""
        hom = initializeBraiten2_2Neg(backendSimulator=self.backend)
        self.assertTrue(hom.isReadyToGo())
        hom.runFor(10)
        self.assertEqual(hom.time, 10)

    def test_robot_position_accessible(self):
        """After running, the robot's body position can be read from the simulation."""
        hom = initializeBraiten2_2(backendSimulator=self.backend)
        sim = self.backend.kheperaSimulation
        robot = sim.allBodies['Khepera']

        hom.runFor(100)

        pos = robot.body.position
        self.assertIsInstance(pos[0], float)
        self.assertIsInstance(pos[1], float)

    def test_final_distance_from_target(self):
        """The backend can report distance from target after a run."""
        hom = initializeBraiten2_2(backendSimulator=self.backend)
        hom.runFor(50)
        distance = self.backend.finalDisFromTarget()
        self.assertIsInstance(distance, float)
        self.assertGreater(distance, 0)


if __name__ == "__main__":
    unittest.main()
