'''
Test the Braitenberg 2_2 simulation using the internal HOMEO Khepera backend.
Requires Box2D and pyglet.

@author: stefano
'''

import unittest
import threading
import tempfile
import shutil

try:
    from Simulator.SimulatorBackend import SimulatorBackendHOMEO
    from Simulator.HomeoExperiments import (initializeBraiten2_2,
                                             initializeBraiten2_2Pos)
    from RobotSimulator.HomeoUnitNewtonianTransduc import HomeoUnitNewtonianActuator, HomeoUnitInput
    _deps_available = True
except ImportError:
    _deps_available = False


@unittest.skipUnless(_deps_available, "Requires Box2D and pyglet")
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

    def test_sensor_links_are_adaptive(self):
        """Every active link but the self-connections is under the uniselector,
        the sensor -> eye links included"""
        hom = initializeBraiten2_2(backendSimulator=self.backend)
        for name in ('Left Eye', 'Right Eye', 'Left Motor', 'Right Motor'):
            unit = [u for u in hom.homeoUnits if u.name == name][0]
            active = [c for c in unit.inputConnections[1:] if c.status]
            self.assertEqual(len(active), 1, name)
            self.assertEqual(active[0].state, 'uniselector', name)
        leftEye = [u for u in hom.homeoUnits if u.name == 'Left Eye'][0]
        self.assertEqual([c.incomingUnit.name for c in leftEye.inputConnections[1:] if c.status],
                         ['Left Sensor'])

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

    def test_raw_is_rejected_with_a_backend(self):
        """raw=True (inverted sensors) is refused, not silently ignored."""
        with self.assertRaises(ValueError):
            initializeBraiten2_2(raw=True, backendSimulator=self.backend)

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
        """The backend reports the robot's distance from the light (the GA's
        fitness) after a run: from where the robot is, not where it began."""
        hom = initializeBraiten2_2(backendSimulator=self.backend)
        sim = self.backend.kheperaSimulation
        start = sim.allBodies['Khepera'].body.position.copy()
        hom.runFor(50)
        robot = sim.allBodies['Khepera'].body.position
        target = sim.allBodies['TARGET'].position
        distance = self.backend.finalDisFromTarget()
        self.assertAlmostEqual(distance, (robot - target).length, places=9)
        self.assertNotEqual(tuple(robot), tuple(start))


if __name__ == "__main__":
    unittest.main()
