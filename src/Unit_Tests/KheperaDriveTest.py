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

    def simulation(self, timeStep=0.032, drive='kinematic'):
        # The legacy drive exists only for the K-Junior
        sim = KheperaSimulation(timeStep=timeStep, robotDrive=drive,
                                robotModel='kjunior' if drive == 'legacy' else 'epuck2')
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
        self.assertAlmostEqual(turned, eturn, delta=0.01 * max(abs(eturn), 0.01))

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

    def testLegacyDriveIsKept(self):
        "The old wheel physics, for reproducing earlier runs: ~14% of the speed at low speed"
        sim, robot = self.simulation(drive='legacy')
        robot.setSpeed(0.5, 0.5)
        start = robot.body.position.copy()
        for i in range(125):
            sim.advanceSim()
        sim.saveTrajectory()
        ratio = (robot.body.position - start).length / (125 * 0.032 * 0.5 * robot.wheelRadius)
        self.assertAlmostEqual(ratio, 0.14, delta=0.03)

    def testUnknownDriveIsRejected(self):
        with self.assertRaises(ValueError):
            self.simulation(drive='tank')
