'''
Created on Oct 14, 2026

@author: stefano

The robot simulator's small defects (review findings RS-06 to RS-14, Phase H
of the 7 Oct 2026 review plan).  None of the fixes changes a run that used to
complete: each test pins the behaviour that used to crash or go wrong.
'''
import math
import shutil
import tempfile
import unittest

import numpy as np
from Box2D import b2Vec2, b2Rot

from KheperaSimulator.KheperaSimulator import KheperaSimulation
from Helpers.General_Helper_Functions import normalize


class _WorldTest(unittest.TestCase):

    def setUp(self):
        self.dataDir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dataDir, ignore_errors=True)

    def world(self, name='kheperaBraitenberg2_HOMEO_World', **kwargs):
        sim = KheperaSimulation(**kwargs)
        sim.setupWorld(name, self.dataDir)
        return sim


class LightOnTheEyeAxisTest(_WorldTest):
    '''RS-06: with the light straight along a receptor's facing, the cosine
    of the angle to it can round to 1.0000000000000002, which acos refused
    (a ValueError ended the run).'''

    def testALightOnTheAxisIsSeen(self):
        sim = self.world()
        robot = sim.allBodies['Khepera']
        light = robot.detectableLights[0]
        lightPos = b2Vec2(light.userData['lightPos'][0], light.userData['lightPos'][2])
        (rx, ry), facing = robot.eyeReceptors['rightEye'][0]
        overOne = 0
        for i in range(2000):
            x, y = 1 + (i % 63) * 0.1, 1 + (i // 63) * 0.1
            angle = 0.0
            for _ in range(5):                 # aim the receptor at the light
                position = b2Vec2(x, y) + b2Rot(angle) * b2Vec2(rx, ry)
                d = lightPos - position
                angle = math.atan2(d[1], d[0]) - math.radians(facing)
            robot.body.transform = ((x, y), angle)
            position = robot.body.position + b2Rot(robot.body.angle) * b2Vec2(rx, ry)
            eye = robot.body.angle + math.radians(facing)
            cosine = np.dot(normalize(lightPos - position), np.array([math.cos(eye), math.sin(eye)]))
            if cosine > 1:
                overOne += 1
                self.assertGreater(robot.irradAtSensor('rightEye', robot.detectableLights), 0)
        self.assertGreater(overOne, 0, 'no pose put the cosine over 1: the test checks nothing')


class SensorFacingTest(_WorldTest):
    '''RS-07: addSensor (the K-Junior's eyes) faced every sensor forward --
    atan(y/x) cannot tell a rear position from a front one -- and ignored its
    orientation.'''

    def robot(self):
        self.sim = self.world(robotModel='kjunior')      # kept: the robot's Box2D world is the sim's
        return self.sim.allBodies['Khepera']

    def testARearEyeFacesBackward(self):
        robot = self.robot()
        robot.addSensor((0.0, -0.03), 'rearEye')            # straight behind the centre
        self.assertAlmostEqual(abs(robot.sensors['rearEye'].userData['rearEyeAngle']), 180)
        robot.body.transform = ((5, 5), 0)                   # facing +x
        behind = [l for l in robot.detectableLights]
        for light in behind:
            light.userData['lightPos'] = (4.0, 0, 5.0)       # straight behind the robot
        self.assertGreater(robot.irradAtSensor('rearEye', behind), 0)
        self.assertEqual(robot.irradAtSensor('leftEye', behind), 0)

    def testTheOrientationTurnsTheSensor(self):
        robot = self.robot()
        robot.addSensor((0.0, 0.03), 'frontEye')
        robot.addSensor((0.0, 0.03), 'turnedEye', orientation=30)
        front = robot.sensors['frontEye'].userData['frontEyeAngle']
        self.assertAlmostEqual(robot.sensors['turnedEye'].userData['turnedEyeAngle'], front + 30)

    def testTheKJuniorEyesAreUnchanged(self):
        "Its eyes, in front at +/-21.9 degrees, keep their facings to the last bit"
        for ratio in (0.5, 1.0):
            sim = self.world(robotModel='kjunior', robotEyeRadiusRatio=ratio)
            robot = sim.allBodies['Khepera']
            for eye, sign in (('leftEye', 1), ('rightEye', -1)):
                px, py = robot.eyePoses[eye]                 # (right, forward)
                self.assertEqual(robot.sensors[eye].userData[eye + 'Angle'],
                                 math.degrees(math.atan(-px / py)))       # the old formula
                self.assertAlmostEqual(robot.sensors[eye].userData[eye + 'Angle'], sign * 21.8858, 4)


if __name__ == '__main__':
    unittest.main()
