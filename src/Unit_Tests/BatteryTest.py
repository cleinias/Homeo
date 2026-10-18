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
The robot's battery (KheperaSimulator.Battery): its metabolism, what an empty
battery does to the wheels, the food at the robot's centre, the tick in the
world's tickAdvance, and the end of a run when the robot dies.
'''
import os
import shutil
import tempfile
import threading
import unittest

from KheperaSimulator.Battery import Battery, DEPLETION_MODES
from Simulator.SimulatorBackend import SimulatorBackendHOMEO
from HomeoExperiments.KheperaExperiments.phototaxis_common import set_start_pose


class BatteryModelTest(unittest.TestCase):

    def testStartsFullAndDrains(self):
        b = Battery(capacity=2.0, discharge_rate=0.5, recharge_factor=0.0)
        self.assertEqual(b.level, 2.0)
        b.tick(0.0)
        self.assertAlmostEqual(b.level, 1.5)
        for _ in range(10):
            b.tick(0.0)
        self.assertEqual(b.level, 0.0)            # clamped at 0

    def testRechargeIsProportionalToFoodAndClamped(self):
        b = Battery(capacity=1.0, discharge_rate=0.1, recharge_factor=0.01)
        b.level = 0.5
        b.tick(20.0)                               # -0.1 + 0.2
        self.assertAlmostEqual(b.level, 0.6)
        b.tick(1000.0)
        self.assertEqual(b.level, 1.0)             # clamped at capacity

    def testSaturationCapsTheFood(self):
        b = Battery(discharge_rate=0.0, recharge_factor=0.01, saturation=5.0)
        b.level = 0.0
        b.tick(50.0)
        self.assertAlmostEqual(b.level, 0.05)

    def testNegativeFoodIsNone(self):
        b = Battery(discharge_rate=0.1, recharge_factor=1.0)
        b.tick(-3.0)
        self.assertAlmostEqual(b.level, 0.9)

    def testStatistics(self):
        b = Battery(capacity=1.0, discharge_rate=0.25, recharge_factor=0.0, critical_level=0.3)
        for _ in range(5):
            b.tick()
        # levels 0.75, 0.5, 0.25, 0, 0
        s = b.summary()
        self.assertAlmostEqual(s['battery_mean'], 0.3)
        self.assertEqual(s['battery_min'], 0.0)
        self.assertEqual(s['ticks_critical'], 3)
        self.assertEqual(s['ticks_empty'], 2)
        self.assertEqual(s['battery_ticks'], 5)
        self.assertTrue(s['alive'])
        self.assertIsNone(s['death_tick'])

    def testDeathAtZero(self):
        b = Battery(discharge_rate=0.4, recharge_factor=1.0, depletion='death')
        b.tick(); b.tick()
        self.assertTrue(b.alive)
        b.tick()                                   # 1 - 1.2: empty
        self.assertFalse(b.alive)
        self.assertEqual(b.deathTick, 3)
        b.tick(100.0)                              # the dead do not feed
        self.assertEqual(b.level, 0.0)
        self.assertEqual(b.motorEfficiency(), 0.0)

    def testMotorEfficiency(self):
        for mode in DEPLETION_MODES:
            b = Battery(depletion=mode, min_efficiency=0.1)
            self.assertEqual(b.motorEfficiency(), 1.0, mode)
        b = Battery(depletion='graded', min_efficiency=0.1)
        b.level = 0.5
        self.assertAlmostEqual(b.motorEfficiency(), 0.55)
        b = Battery(depletion='paralysis')
        b.level = 0.0
        self.assertEqual(b.motorEfficiency(), 0.0)
        b.level = 0.01                             # recovers once it holds charge
        self.assertEqual(b.motorEfficiency(), 1.0)
        b = Battery(depletion='none')
        b.level = 0.0
        self.assertEqual(b.motorEfficiency(), 1.0)

    def testBreakEven(self):
        rf = Battery.breakEvenRechargeFactor(1e-4, 50.0)
        b = Battery(discharge_rate=1e-4, recharge_factor=rf)
        b.level = 0.5
        b.tick(50.0)
        self.assertAlmostEqual(b.level, 0.5)

    def testRefusesBadParameters(self):
        for kwargs in (dict(capacity=0), dict(discharge_rate=-1), dict(critical_level=1.0),
                       dict(depletion='coma'), dict(min_efficiency=2), dict(saturation=0)):
            with self.assertRaises(ValueError, msg=kwargs):
                Battery(**kwargs)


class RobotBatteryTest(unittest.TestCase):
    "A battery on the Box2D robot in the Braitenberg 2 world (light of intensity 100 at (7, 7))"

    def setUp(self):
        self.dataDir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dataDir, True)
        self.backend = SimulatorBackendHOMEO(lock=threading.Lock(), robotName='Khepera',
                                             dataDir=self.dataDir)
        self.backend.start('kheperaBraitenberg2_HOMEO_World')
        self.sim = self.backend.kheperaSimulation
        self.addCleanup(self.sim.saveTrajectory)
        self.robot = self.sim.allBodies['Khepera']

    def testFoodAtCentreIsTheLightsInverseSquare(self):
        set_start_pose(self.robot, 4, 4, 0)
        self.assertAlmostEqual(self.robot.foodAtCentre(), 100 / 18)
        set_start_pose(self.robot, 4, 4, 180)      # whatever the heading
        self.assertAlmostEqual(self.robot.foodAtCentre(), 100 / 18)

    def testADarknessSourceDoesNotFeed(self):
        self.sim.allBodies['TARGET'].userData['intensity'] = -100
        self.assertEqual(self.robot.foodAtCentre(), 0.0)

    def testTheWorldTicksTheBatteryOncePerTick(self):
        self.robot.battery = Battery(discharge_rate=0.01, recharge_factor=0.0)
        for _ in range(3):
            self.sim.tickAdvance()
        self.assertEqual(self.robot.battery.ticks, 3)
        self.assertAlmostEqual(self.robot.battery.level, 0.97)

    def testFeedingNearTheLight(self):
        self.robot.battery = Battery(discharge_rate=0.01, recharge_factor=0.001)
        self.robot.battery.level = 0.5
        set_start_pose(self.robot, 6, 7, 0)        # 1 from the light: food 100
        self.sim.tickAdvance()
        self.assertAlmostEqual(self.robot.battery.level, 0.59, places=6)

    def testWheelsWithoutABatteryAreUnchanged(self):
        self.robot.setRightSpeed(1.0)
        self.assertAlmostEqual(self.robot.rightSpeed, self.robot.wheelRadius)

    def testAnEmptyBatteryParalysesTheWheels(self):
        self.robot.battery = Battery(depletion='paralysis')
        self.robot.battery.level = 0.0
        self.robot.setRightSpeed(1.0)
        self.robot.setLeftSpeed(1.0)
        self.assertEqual(self.robot.getSpeed(), {'right': 0.0, 'left': 0.0})

    def testGradedDepletionSlowsTheWheels(self):
        self.robot.battery = Battery(depletion='graded', min_efficiency=0.0)
        self.robot.battery.level = 0.25
        self.robot.setRightSpeed(1.0)
        self.assertAlmostEqual(self.robot.rightSpeed, 0.25 * self.robot.wheelRadius)

    def testDeathHaltsTheWorldAndTheHomeostat(self):
        from Core.Homeostat import Homeostat
        from Core.HomeoUnit import HomeoUnit
        from RobotSimulator.HomeoUnitNewtonianTransduc import HomeoUnitInput
        HomeoUnit.clearNames()
        hom = Homeostat()
        sensor = HomeoUnitInput(transducer=self.backend.getSensor('left'))
        hom.addFullyConnectedUnit(sensor)
        self.robot.battery = Battery(discharge_rate=0.125, recharge_factor=0.0, depletion='death')
        self.assertFalse(self.sim.halted)
        hom.runFor(100)
        self.assertTrue(self.sim.halted)
        self.assertEqual(self.robot.battery.deathTick, 8)
        self.assertEqual(hom.time, 8)
        hom.runFor(200)                            # a dead world runs no more
        self.assertEqual(hom.time, 8)
