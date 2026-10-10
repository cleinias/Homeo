'''
Regression tests for known bugs that change simulation results.

Each test states the behaviour the code should have.  While its bug is in
the code the test fails, so it is marked xfail(strict=True): the suite stays
green, and turns red as soon as the bug is fixed.  The marker is then removed
and the test guards the fix; the unmarked tests below are such guards.
'''
import os
import random
import shutil
import tempfile
import unittest

import numpy as np
import pytest

from Core.Homeostat import Homeostat
from Core.HomeoUnit import HomeoUnit
from Core.HomeoUnitNewtonian import HomeoUnitNewtonian
from Core.HomeoUniselectorContinuous import HomeoUniselectorContinuous
from Core.HomeoJIT import seed_jit_rng


def seedAll(seed):
    np.random.seed(seed)
    random.seed(seed)
    seed_jit_rng(seed)


def headlessHomeostat(units, seed, continuous=False):
    "A seeded, fully connected, headless homeostat of Newtonian units"
    seedAll(seed)
    HomeoUnit.clearNames()
    hom = Homeostat()
    hom.slowingFactor = 0
    hom.collectsData = False
    for i in range(units):
        unit = HomeoUnitNewtonian()
        unit.setRandomValues()
        if continuous:
            unit.uniselector = HomeoUniselectorContinuous()
        hom.addFullyConnectedUnit(unit)
    hom._headless = True
    for unit in hom.homeoUnits:
        unit._headless = True
    return hom


class HeadlessRunLoopTest(unittest.TestCase):

    def testOUDriftSurvivesStepping(self):
        "Stepping tick by tick (as the GA does) must evolve the OU weights as one runFor() does"
        ticks = 1500
        whole = headlessHomeostat(2, seed=3, continuous=True)
        whole.runFor(ticks)
        stepped = headlessHomeostat(2, seed=3, continuous=True)
        for i in range(ticks):
            stepped.runOnce()
        for a, b in zip(whole.homeoUnits, stepped.homeoUnits):
            np.testing.assert_allclose(a._jit_weights * a._jit_switches,
                                       b._jit_weights * b._jit_switches, atol=1e-9)

    def testChunkingDoesNotChangeTheTrajectory(self):
        "The same seed must give the same run whether it is run in one call or in chunks"
        whole = headlessHomeostat(4, seed=11)
        whole.runFor(2000)
        chunked = headlessHomeostat(4, seed=11)
        for end in (500, 1000, 1500, 2000):
            chunked.runFor(end)
        np.testing.assert_allclose([u.criticalDeviation for u in whole.homeoUnits],
                                   [u.criticalDeviation for u in chunked.homeoUnits], atol=1e-9)

    def testOULeavesManualConnectionsAlone(self):
        "In a headless OU run a 'manual' self-connection must keep its weight"
        hom = headlessHomeostat(2, seed=1, continuous=True)
        for unit in hom.homeoUnits:
            unit.uniselectorActive = True
            unit.criticalDeviation = 5.0            # stressed, so the OU noise is large
            unit.inputConnections[0].state = 'manual'
            unit._jit_dirty = True
        before = [u.inputConnections[0].weight * u.inputConnections[0].switch for u in hom.homeoUnits]
        hom.runFor(3000)
        for unit in hom.homeoUnits:
            unit.flushJitArrays()
        after = [u.inputConnections[0].weight * u.inputConnections[0].switch for u in hom.homeoUnits]
        np.testing.assert_allclose(before, after, atol=1e-12)


class NewtonianStabilityTest(unittest.TestCase):

    @pytest.mark.xfail(strict=True, reason='Stokes drag is integrated explicitly, '
                       'unstable when viscosity * dt_fast / mass > 2')
    def testDragDampsAtHighViscosity(self):
        "Under a constant torque, drag must hold the velocity near its terminal value F / viscosity"
        torque, viscosity = 0.1, 5.0
        HomeoUnit.clearNames()
        unit = HomeoUnitNewtonian()
        unit.uniselectorActive = False
        unit.noise = 0
        unit.potentiometer = 0
        unit.inputConnections[0].noise = 0
        unit.mass = 1
        unit.viscosity = viscosity
        unit.dt_fast = 1
        unit.maxDeviation = 1000
        source = HomeoUnit()
        source._currentOutput = 1.0
        unit.addConnectionUnitWeightPolarityNoiseState(source, torque, 1, 0, 'manual')
        # Check every step: a diverging needle soon hits its limit, where
        # clipping resets the velocity to 0 and hides the blow-up.
        speeds = []
        for i in range(30):
            unit.selfUpdate()
            speeds.append(abs(unit.currentVelocity))
        self.assertLess(max(speeds), 2 * torque / viscosity)


class AshbyExperimentWiringTest(unittest.TestCase):

    def assertSomeConnectionCanAdapt(self, hom):
        "Some active 'uniselector' connection must belong to a unit whose uniselector is on"
        adaptive = [(unit.name, conn.incomingUnit.name)
                    for unit in hom.homeoUnits if unit.isActive() and unit.uniselectorActive
                    for conn in unit.inputConnections
                    if conn.isActive() and conn.state == 'uniselector']
        self.assertTrue(adaptive, 'no connection that a working uniselector can change')

    def testExp2HeadlessCanAdapt(self):
        from Simulator.AshbyOriginalExperiments import setup_exp2_self_reorganization
        hom, seed, meta = setup_exp2_self_reorganization(1)
        self.assertSomeConnectionCanAdapt(hom)

    def testExp2GuiCanAdapt(self):
        from Simulator.HomeoExperiments import initializeAshbyExp2SelfReorganization
        self.assertSomeConnectionCanAdapt(initializeAshbyExp2SelfReorganization())


class KheperaTest(unittest.TestCase):

    def setUp(self):
        # Trajectory files go to a scratch directory, not SimulationsData.
        self.dataDir = tempfile.mkdtemp()
        self.oldDataDir = os.environ.get('HOMEO_DATA_DIR')
        os.environ['HOMEO_DATA_DIR'] = self.dataDir

    def tearDown(self):
        if self.oldDataDir is None:
            os.environ.pop('HOMEO_DATA_DIR', None)
        else:
            os.environ['HOMEO_DATA_DIR'] = self.oldDataDir
        shutil.rmtree(self.dataDir, ignore_errors=True)

    @pytest.mark.xfail(strict=True, reason='the wheel model moves the robot at ~14% of '
                       'the commanded speed in the homeostat range, ~83% above a threshold')
    def testWheelSpeedFollowsCommand(self):
        "Driving straight, the robot's speed must be close to the commanded wheel speed"
        from KheperaSimulator.KheperaSimulator import KheperaSimulation
        for command in (0.5, 5.0):
            sim = KheperaSimulation()
            sim.setupWorld('kheperaBraitenberg2_HOMEO_World', self.dataDir)
            robot = sim.allBodies['Khepera']
            robot.setRightSpeed(command)
            robot.setLeftSpeed(command)
            start = robot.body.position.copy()
            steps = 300
            for i in range(steps):
                sim.advanceSim()
            speed = (robot.body.position - start).length / (steps * sim.timeStep)
            self.assertAlmostEqual(speed / (command * robot.wheelRadius), 1.0, delta=0.2,
                                   msg='command %s rad/s' % command)

    @pytest.mark.xfail(strict=True, reason='since 7170286 the eye returns 0 for the '
                       "darkness source's negative irradiance, so --dark runs are blind")
    def testDarkRunsAreNotBlind(self):
        "Under a darkness source (negative intensity) the eyes must report something"
        from HomeoExperiments.KheperaExperiments import phototaxis_braitenberg2_direct as direct
        hom, backend, seed = direct.setup_phototaxis(seed=3, light_intensity=-100, fixed_weights=True)
        robot = backend.kheperaSimulation.allBodies['Khepera']
        reads = [robot.getSensorRead('leftEye'), robot.getSensorRead('rightEye')]
        backend.kheperaSimulation.saveTrajectory()
        self.assertTrue(any(read != 0 for read in reads), 'both eyes read 0 in the dark')
