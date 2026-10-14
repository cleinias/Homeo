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

All of this is the K-Junior (model='kjunior'), the robot of every run before
14 Oct 2026.  The e-puck2, the robot since, has the eyes of EpuckEyesTest:
each a pair of the e-puck's light sensors, their irradiance averaged, each
with a LightSensor's 180-degree cosine field.
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
        return KheperaRobot(world, initialPose=(0, 0), **dict({'model': 'kjunior'}, **kwargs))

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
            simulation = KheperaSimulation(robotEyeRadiusRatio=ratio, robotModel='kjunior')
            self.assertEqual(simulation.robotEyeRadiusRatio, ratio)


@unittest.skipUnless(HAS_BOX2D, "Box2D not installed")
class EpuckEyesTest(KheperaEyePlacementTest.__base__):
    '''The e-puck2's eyes (the robot since 14 Oct 2026): the right eye is ls0
    and ls1, the left ls7 and ls6, at the positions and facing the
    directions of Webots' E-puck.proto; an eye's irradiance is the mean of
    its two sensors', each with the cosine law and nothing from behind.'''

    _robot = KheperaEyePlacementTest._robot
    _seen = KheperaEyePlacementTest._seen

    def epuck(self):
        return self._robot(model='epuck2')

    def testTheSensorsAreTheProtosOnes(self):
        robot = self.epuck()
        self.assertEqual(robot.eyeReceptors['rightEye'],
                         [((0.030, -0.010), -17.235), ((0.022, -0.025), -45.882)])
        self.assertEqual(robot.eyeReceptors['leftEye'],
                         [((0.030, 0.010), 17.143), ((0.022, 0.025), 45.791)])
        self.assertEqual(robot.eyeFieldOfView, 180)
        self.assertEqual((robot.diameter, robot.wheelRadius, robot.wheelSeparation),
                         (0.074, 0.020, 0.052))
        self.assertAlmostEqual(robot.maxSpeed, 0.0243322561)       # the cap

    def testAnEyeIsItsSensorsMean(self):
        robot = self.epuck()
        for bearing, distance in ((0, 1.0), (30, 2.0), (-70, 0.5), (120, 1.5)):
            b = radians(bearing)
            light = [Light(distance * cos(b), distance * sin(b))]
            for eye in ('leftEye', 'rightEye'):
                expected = 0
                for (x, y), facing in robot.eyeReceptors[eye]:
                    dx, dy = distance * cos(b) - x, distance * sin(b) - y
                    d = (dx ** 2 + dy ** 2) ** 0.5
                    c = (dx * cos(radians(facing)) + dy * sin(radians(facing))) / d
                    expected += max(c, 0) * 100 / d ** 2
                with self.subTest(bearing=bearing, eye=eye):
                    # Box2D keeps positions in single precision
                    self.assertAlmostEqual(robot.irradAtSensor(eye, light), expected / 2,
                                           delta=1e-6 * expected)

    def testWhatTheEyesSee(self):
        "both eyes see the front, one eye alone the sides, neither the rear 88 degrees"
        robot = self.epuck()
        left, right = self._seen(robot, 0, 1.0)
        self.assertGreater(left, 0)
        # The PROTO's sensors are not quite symmetric (ls0 faces -17.235
        # degrees, ls7 17.143; ls1 -45.882, ls6 45.791): 0.1% more on the left
        self.assertAlmostEqual(left, right, delta=0.002 * left)
        left, right = self._seen(robot, 100, 2.0)
        self.assertGreater(left, 0)
        self.assertEqual(right, 0)
        for bearing in (140, 180, -140):
            self.assertEqual(self._seen(robot, bearing, 2.0), (0, 0))

    def testNoBlindWedgeAhead(self):
        robot = self.epuck()
        rim = robot.diameter / 2
        for bearing in range(-45, 46, 3):
            for k in range(1, 200):
                distance = rim + 0.0025 * k
                with self.subTest(bearing=bearing, distance=distance):
                    self.assertGreater(max(self._seen(robot, bearing, distance)), 0)

    def testEyeRadiusRatioIsTheKJuniorsOnly(self):
        with self.assertRaises(ValueError):
            self._robot(model='epuck2', eyeRadiusRatio=0.5)


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
            for pair in self.PAIRS[1:]:
                with self.subTest(sensor=side + pair):
                    self.assertEqual(self.robot.eyeReceptors[side + pair],
                                     self.robot.eyeReceptors[side + 'Eye'])
                    self.assertEqual(self.robot.sensors[side + pair].userData[side + pair + 'AngleRange'],
                                     self.robot.eyeFieldOfView)

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
