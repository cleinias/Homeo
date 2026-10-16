'''
World stepping: the motors only set their wheel speeds and the world
advances once per homeostat tick, after every unit has updated, by
stepsPerTick steps.
'''
import os
import tempfile
import unittest

import HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct as D


class SynchronousSteppingTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ['HOMEO_DATA_DIR'] = self.tmp.name

    def tearDown(self):
        os.environ.pop('HOMEO_DATA_DIR', None)
        self.tmp.cleanup()

    def vehicle(self, spin=0.0):
        hom, backend, seed = D.setup_phototaxis(seed=3, fixed_weights=True, spin=spin)
        hom.slowingFactor = 0
        hom.collectsData = False
        hom._headless = True
        for unit in hom.homeoUnits:
            unit._headless = True
        self.addCleanup(backend.kheperaSimulation.saveTrajectory)
        return hom, backend.kheperaSimulation

    def testMotorsOnlySetSpeeds(self):
        "A motor command does not advance the world"
        from RobotSimulator.Transducer import HOMEO_DiffMotor
        hom, sim = self.vehicle()
        motors = [u for u in hom.homeoUnits if isinstance(getattr(u, 'transducer', None), HOMEO_DiffMotor)]
        self.assertEqual(len(motors), 2)
        for unit in motors:
            unit.transducer.funcParameters = 1.0
            unit.transducer.act()
        self.assertEqual(sim.currentStep, 0)

    def testOneTickIsStepsPerTickSteps(self):
        "A tick is two physics steps, both after all units have updated"
        hom, sim = self.vehicle()
        hom.runFor(100)
        self.assertEqual(sim.currentStep, 200)

    def testBothWheelsActOnTheSameSteps(self):
        "A pure spin turns in place exactly: no step sees one wheel's new command alone"
        hom, sim = self.vehicle(spin=0.05)
        robot = sim.allBodies['Khepera']
        D.set_start_pose(robot, heading=225)       # facing away from the light
        start = robot.body.position.copy()
        hom.runFor(200)
        self.assertLess((robot.body.position - start).length, 1e-6)
        self.assertNotEqual(robot.body.angle, 0)

    def testThereIsOneStepping(self):
        "No choice of stepping: neither the simulation nor the scripts take one"
        from KheperaSimulator.KheperaSimulator import KheperaSimulation
        from Simulator.SimulatorBackend import SimulatorBackendHOMEO
        with self.assertRaises(TypeError):
            KheperaSimulation(synchronousStepping=False)
        with self.assertRaises(TypeError):
            SimulatorBackendHOMEO(robotName='Khepera', synchronousStepping=False)
        with self.assertRaisesRegex(SystemExit, 'Unknown option'):
            D.common.parse_common_args(['x', '--async-stepping'])
