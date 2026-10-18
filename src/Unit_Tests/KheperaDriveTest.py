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
The Khepera robot's drive: a differential drive.

With wheel speeds vR, vL (rad/s times the wheel radius) and wheel separation
L the robot moves forward at (vR + vL)/2 and turns at (vR - vL)/L, whatever
the speeds and the simulation step.  The motor transducers' range is the
robot's top speed, in the unit the robot's setters take.
'''
import math
import os
import shutil
import tempfile
import threading
import unittest

from KheperaSimulator.KheperaSimulator import KheperaSimulation, KheperaRobot


class KheperaDriveTest(unittest.TestCase):

    def setUp(self):
        self.dataDir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dataDir, ignore_errors=True)

    def simulation(self, timeStep=0.032):
        sim = KheperaSimulation(timeStep=timeStep)
        sim.setupWorld('kheperaBraitenberg2_HOMEO_World', self.dataDir)
        return sim, sim.allBodies['Khepera']

    def drive(self, right, left, seconds=4.0, timeStep=0.032, heading=0.0):
        "Run the robot with fixed wheel commands; return its displacement and turn"
        sim, robot = self.simulation(timeStep)
        robot.rotateTo(heading)
        robot.setSpeed(right, left)
        start, angle = robot.body.position.copy(), robot.body.angle
        for i in range(int(round(seconds / timeStep))):
            sim.advanceSim()
        sim.saveTrajectory()
        return robot, robot.body.position - start, robot.body.angle - angle

    def expected(self, robot, right, left, seconds, heading=0.0):
        clip = lambda v: max(-robot.maxSpeed, min(robot.maxSpeed, v))
        vR, vL = clip(right * robot.wheelRadius), clip(left * robot.wheelRadius)
        v, omega = (vR + vL) / 2, (vR - vL) / robot.wheelSeparation
        turn = omega * seconds
        if abs(turn) < 1e-12:
            return v * seconds * math.cos(heading), v * seconds * math.sin(heading), 0.0
        return (v / omega * (math.sin(heading + turn) - math.sin(heading)),
                -v / omega * (math.cos(heading + turn) - math.cos(heading)), turn)

    def assertFollows(self, right, left, timeStep=0.032, heading=0.0, seconds=4.0):
        robot, moved, turned = self.drive(right, left, seconds, timeStep, heading)
        ex, ey, eturn = self.expected(robot, right, left, seconds, heading)
        scale = max(math.hypot(ex, ey), 1e-3)
        self.assertAlmostEqual(moved[0], ex, delta=0.01 * scale, msg='x, commands %s, %s' % (right, left))
        self.assertAlmostEqual(moved[1], ey, delta=0.01 * scale, msg='y, commands %s, %s' % (right, left))
        # the heading is kept in (-pi, pi]: compare turns modulo a full turn
        self.assertAlmostEqual(math.remainder(turned - eturn, 2 * math.pi), 0,
                               delta=0.01 * max(abs(eturn), 0.01))

    def testSlowMotionAndLongTurnsAreExact(self):
        '''The pose is kept in double precision: slow motion far from the
        origin and turns at a large heading follow the arc exactly (Box2D's
        float32 state would round them by several per cent).'''
        for right, left, heading in ((0.002, 0.002, 0.0), (0.01, 0.01, 0.3),
                                     (0.03, 0.01, 1000.0), (0.11, 0.01, 3000.0)):
            with self.subTest(right=right, left=left, heading=heading):
                sim, robot = self.simulation()
                robot.moveTo((7.0, 7.0))
                robot.rotateTo(heading)
                x0, y0, h0 = robot.pose
                self.assertTrue(-math.pi < h0 <= math.pi)
                self.assertAlmostEqual(h0, math.remainder(heading, 2 * math.pi), places=12)
                robot.setSpeed(right, left)
                steps = 2000
                for i in range(steps):
                    sim.advanceSim()
                sim.saveTrajectory()
                ex, ey, eturn = self.expected(robot, right, left, steps * 0.032, h0)
                x, y, h = robot.pose
                self.assertAlmostEqual(x - x0, ex, delta=1e-9 * max(abs(ex), 1e-3))
                self.assertAlmostEqual(y - y0, ey, delta=1e-9 * max(abs(ey), 1e-3))
                self.assertAlmostEqual(math.remainder(h - h0 - eturn, 2 * math.pi), 0, delta=1e-9)
                # the body is the pose, rounded to float32 once
                self.assertAlmostEqual(robot.body.position[0], x, delta=1e-6)
                self.assertAlmostEqual(robot.body.position[1], y, delta=1e-6)

    def testStraight(self):
        for command in (0.05, 0.3, 1.0, 1.5):
            self.assertFollows(command, command)
            self.assertFollows(-command, -command, heading=1.0)

    def testSpinInPlace(self):
        for command in (0.1, 0.5, 1.5):
            self.assertFollows(command, -command)

    def testArcs(self):
        self.assertFollows(1.2, 0.4)
        self.assertFollows(0.2, 1.0, heading=-2.0)

    def testRightWheelFasterTurnsLeft(self):
        robot, moved, turned = self.drive(1.0, 0.5)
        self.assertGreater(turned, 0)              # counterclockwise
        self.assertGreater(moved[1], 0)

    def testIndependentOfTheTimeStep(self):
        for timeStep in (0.032, 1 / 60.0, 0.1):
            self.assertFollows(1.0, 0.3, timeStep=timeStep)

    def testTopSpeedIsTheTransducerRange(self):
        "The motors' range, passed back to the robot, drives it at its top speed"
        from RobotSimulator.Transducer import HOMEO_DiffMotor
        sim, robot = self.simulation()
        motors = [HOMEO_DiffMotor(wheel, 'Khepera', sim) for wheel in ('right', 'left')]
        for motor in motors:
            self.assertEqual(motor.range(), (-robot.maxWheelSpeed, robot.maxWheelSpeed))
            motor.funcParameters = motor.range()[1]
        start = robot.body.position.copy()
        for i in range(50):
            for motor in motors:
                motor.act()
            sim.tickAdvance()
        sim.saveTrajectory()
        speed = (robot.body.position - start).length / (sim.currentStep * sim.timeStep)
        self.assertAlmostEqual(speed, robot.maxSpeed, delta=0.01 * robot.maxSpeed)

    def testCommandsAboveTopSpeedAreClipped(self):
        robot, moved, turned = self.drive(10.0, 10.0, seconds=1.0)
        self.assertAlmostEqual(moved.length, robot.maxSpeed * 1.0, delta=0.01 * robot.maxSpeed)

    def testPoseSettersMoveTheWheels(self):
        sim, robot = self.simulation()
        robot.moveTo((2.0, 3.0))
        robot.rotateTo(math.pi / 2)
        for side, sign in (('left', 1), ('right', -1)):
            wheel = robot.wheels[side].body.position
            self.assertAlmostEqual(wheel[0], 2.0 - sign * robot.wheelSeparation / 2, places=5)
            self.assertAlmostEqual(wheel[1], 3.0, places=5)
        sim.saveTrajectory()

    def testSetSpeedSetsBothWheels(self):
        sim, robot = self.simulation()
        robot.setSpeed(1.0, -0.5)
        self.assertEqual(robot.getSpeed(), {'right': robot.wheelRadius, 'left': -0.5 * robot.wheelRadius})
        sim.saveTrajectory()
