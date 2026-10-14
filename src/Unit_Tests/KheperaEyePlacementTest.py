'''
Created on Oct 13, 2026

@author: stefano

Where the Khepera's eyes sit.  Each eye faces outward along its radius,
21.9 degrees off the heading, and sees 45 degrees either side of that axis.
On the rim, the two fields' inner edges crossed on the midline 0.1135 ahead
of the centre, 0.05 beyond the rim: a light in that wedge was seen by
neither eye, and a vehicle driving at the light stopped dead 0.11 from it
(research journal, 2026-10-03).  The eyes now sit half way in along their
radii (eyeRadiusRatio 0.5): same angles and fields, the wedge's tip inside
the body, and everything outside the body within 45 degrees of the heading
in view.  eyeRadiusRatio = 1 puts them back on the rim, for runs made
before 13 Oct 2026.
'''
from math import radians, sin, cos

import tempfile
import unittest

try:
    from Box2D import b2World
    from KheperaSimulator.KheperaSimulator import KheperaRobot, KheperaSimulation
    HAS_BOX2D = True
except ImportError:
    HAS_BOX2D = False


class Light(object):
    "A point light, as the robot reads one."
    def __init__(self, x, y):
        self.userData = {'lightPos': (x, 0, y), 'intensity': 100,
                         'attenVec': (0, 0, 1), 'ambRatio': 0}


@unittest.skipUnless(HAS_BOX2D, "Box2D not installed")
class KheperaEyePlacementTest(unittest.TestCase):

    def _robot(self, **kwargs):
        # at the origin, heading along +x (Box2D's angle 0): forward is +x,
        # left is +y
        # the worlds must outlive their bodies, or Box2D crashes
        world = b2World(gravity=(0, 0))
        self._worlds = getattr(self, '_worlds', []) + [world]
        return KheperaRobot(world, initialPose=(0, 0), **kwargs)

    def _seen(self, robot, bearing, distance):
        '''Irradiance on (left, right) eye from a light at distance from the
        centre, bearing degrees off the heading (positive to the left).'''
        b = radians(bearing)
        light = [Light(distance * cos(b), distance * sin(b))]
        return (robot.irradAtSensor('leftEye', light), robot.irradAtSensor('rightEye', light))

    def testNoBlindWedgeAhead(self):
        robot = self._robot()
        rim = robot.diameter / 2
        for bearing in range(-45, 46, 3):
            for k in range(1, 200):
                distance = rim + 0.0025 * k
                with self.subTest(bearing=bearing, distance=distance):
                    self.assertGreater(max(self._seen(robot, bearing, distance)), 0)

    def testALightDeadAheadIsSeenByBothEyes(self):
        robot = self._robot()
        for distance in (0.07, 0.09, 0.11, 1.0):
            left, right = self._seen(robot, 0, distance)
            self.assertGreater(left, 0)
            self.assertAlmostEqual(left, right)

    def testSameAnglesAsOnTheRim(self):
        inside, rim = self._robot(), self._robot(eyeRadiusRatio=1.0)
        for eye in ('leftEye', 'rightEye'):
            self.assertAlmostEqual(inside.sensors[eye].userData[eye + 'Angle'],
                                   rim.sensors[eye].userData[eye + 'Angle'])
            self.assertAlmostEqual(inside.sensors[eye].userData[eye + 'AngleRange'], 90)
        self.assertAlmostEqual(abs(inside.sensors['leftEye'].userData['leftEyeAngle']), 21.8858, places=3)

    def testHalfWayInAlongTheRadius(self):
        inside, rim = self._robot(), self._robot(eyeRadiusRatio=1.0)
        for eye in ('leftEye', 'rightEye'):
            x, y = inside.sensors[eye].shape.pos
            X, Y = rim.sensors[eye].shape.pos
            self.assertAlmostEqual(x, X / 2)
            self.assertAlmostEqual(y, Y / 2)

    def testOnTheRimTheWedgeIsBack(self):
        "eyeRadiusRatio = 1 reproduces the old eyes: a light 0.09 ahead is unseen"
        rim = self._robot(eyeRadiusRatio=1.0)
        self.assertEqual(self._seen(rim, 0, 0.09), (0, 0))

    def testTheSimulationPassesThePlacementOn(self):
        for ratio in (0.5, 1.0):
            simulation = KheperaSimulation(robotEyeRadiusRatio=ratio)
            self.assertEqual(simulation.robotEyeRadiusRatio, ratio)


@unittest.skipUnless(HAS_BOX2D, "Box2D not installed")
class Vehicle3cSensorPlacementTest(unittest.TestCase):
    '''The Vehicle 3c world's extra pairs (temperature, oxygen, organic) sit
    where the light eyes sit, with their field: one geometry for the four
    modalities, no blind wedge for any (research note "Khepera sensor
    placement for Vehicle 3c").  They sat on the rim at +/-45, +/-10 and
    +/-35 degrees, with wedges, and for temperature a blind strip.'''

    PAIRS = ('Eye', 'TempEye', 'OxyEye', 'OrgEye')

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.simulation = KheperaSimulation()
        self.simulation.setupWorld('kheperaBraitenberg3c_HOMEO_World', dataDir=self.tmp.name)
        self.addCleanup(self.simulation.trajectoryWriter.runOnce, transitionMessage='CLOSEFILE')
        self.robot = self.simulation.allBodies['Khepera']

    def testEveryPairSitsWhereTheEyesSit(self):
        for side in ('left', 'right'):
            eye = self.robot.sensors[side + 'Eye']
            for pair in self.PAIRS[1:]:
                sensor = self.robot.sensors[side + pair]
                with self.subTest(sensor=side + pair):
                    self.assertAlmostEqual(sensor.shape.pos[0], eye.shape.pos[0])
                    self.assertAlmostEqual(sensor.shape.pos[1], eye.shape.pos[1])
                    self.assertAlmostEqual(sensor.userData[side + pair + 'Angle'],
                                           eye.userData[side + 'EyeAngle'])
                    self.assertEqual(sensor.userData[side + pair + 'AngleRange'], 90)

    def testNoPairHasABlindWedgeAhead(self):
        body = self.robot.body
        rim = self.robot.diameter / 2
        for pair in self.PAIRS:
            for bearing in range(-45, 46, 5):
                for k in range(1, 60):
                    distance = rim + 0.005 * k
                    b = body.angle + radians(bearing)
                    light = [Light(body.position[0] + distance * cos(b),
                                   body.position[1] + distance * sin(b))]
                    seen = max(self.robot.irradAtSensor(side + pair, light)
                               for side in ('left', 'right'))
                    with self.subTest(pair=pair, bearing=bearing, distance=distance):
                        self.assertGreater(seen, 0)


if __name__ == '__main__':
    unittest.main()
