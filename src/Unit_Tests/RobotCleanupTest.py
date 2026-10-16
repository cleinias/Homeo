'''
@author: stefano

The robot simulator's corner cases: a light on a receptor's axis, a sensor
behind the centre, a refused eye setting, the visualizer's wheel keys, an
error inside a world builder, sensors across a reset, and the robot units'
transducer properties.  Each test pins a behaviour that could crash a run or
go wrong silently.
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
    '''With the light straight along a receptor's facing, the cosine of the
    angle to it can round to 1.0000000000000002, which acos refuses with a
    ValueError: the eye still sees the light.'''

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
    '''addSensor (the K-Junior's eyes) faces a sensor behind the centre
    backward -- atan(y/x) alone cannot tell a rear position from a front
    one -- and turns it by its orientation.'''

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
        sim = self.world(robotModel='kjunior')
        robot = sim.allBodies['Khepera']
        for eye, sign in (('leftEye', 1), ('rightEye', -1)):
            px, py = robot.eyePoses[eye]                 # (right, forward)
            self.assertEqual(robot.sensors[eye].userData[eye + 'Angle'],
                             math.degrees(math.atan(-px / py)))
            self.assertAlmostEqual(robot.sensors[eye].userData[eye + 'Angle'], sign * 21.8858, 4)


class RefusedEyeSettingsTest(_WorldTest):
    '''setEyeSensitivity checks the new settings before storing them: a
    refused call leaves the eye as it was.'''

    def testARefusedCallLeavesTheEyeAsItWas(self):
        sim = self.world()
        robot = sim.allBodies['Khepera']
        robot.setEyeSensitivity('leftEye', threshold=2, saturation=50, response='linear')
        before = robot.eyeSettings()['leftEye']
        response = robot.eyeResponse('leftEye', 26)
        for bad in (dict(threshold=200), dict(threshold=0, response='log'),
                    dict(response='cubic'), dict(saturation=1)):
            with self.assertRaises(ValueError):
                robot.setEyeSensitivity('leftEye', **bad)
            self.assertEqual(robot.eyeSettings()['leftEye'], before, bad)
            self.assertEqual(robot.eyeResponse('leftEye', 26), response)
        robot.setEyeSensitivity('leftEye', saturation=26)          # an accepted call still works
        self.assertEqual(robot.eyeSettings()['leftEye'], (2.0, 26.0, 'linear'))


class VisualizerWheelKeysTest(_WorldTest):
    '''The visualizer's O/L and Q/A keys read getSpeed()'s dict by wheel
    name and drive the visualizer's own simulation (it has no robotName).'''

    def testTheKeysNudgeEachWheelByOneRadianPerSecond(self):
        from KheperaSimulator.KheperaSimulator import nudgeWheels
        sim = self.world()
        robot = sim.allBodies['Khepera']
        robot.setSpeed(0.5, 0.25)
        nudgeWheels(sim, 1, 0)                                   # O
        self.assertAlmostEqual(robot.getSpeed()['right'], 1.5 * robot.wheelRadius)
        self.assertAlmostEqual(robot.getSpeed()['left'], 0.25 * robot.wheelRadius)
        nudgeWheels(sim, 0, -1)                                  # A
        self.assertAlmostEqual(robot.getSpeed()['left'], -0.75 * robot.wheelRadius)
        self.assertAlmostEqual(robot.getSpeed()['right'], 1.5 * robot.wheelRadius)

    def testTheVisualizerKeysCallIt(self):
        "The key handler calls nudgeWheels with the visualizer's own simulation"
        import inspect
        from KheperaSimulator.KheperaSimulator import KheperaSimulationVisualizer
        source = inspect.getsource(KheperaSimulationVisualizer.on_key_press)
        self.assertNotIn('self.robotName', source)
        self.assertEqual(source.count('nudgeWheels(self.sim'), 4)


class WorldSetupErrorsTest(_WorldTest):
    '''A TypeError or AttributeError raised inside a world builder comes
    through setupWorld as it is, not as "Cannot run simulation without an
    experiment" or "Cannot find ... among my experiment setup methods".'''

    def testABuildersOwnErrorComesThrough(self):
        class Broken(KheperaSimulation):
            def brokenWorld(self):
                raise AttributeError('the real problem')
        sim = Broken()
        with self.assertRaisesRegex(AttributeError, 'the real problem'):
            sim.setupWorld('brokenWorld', self.dataDir)

    def testNoWorldAndAnUnknownWorldAreReported(self):
        with self.assertRaisesRegex(Exception, 'without an experiment'):
            KheperaSimulation().setupWorld(None, self.dataDir)
        with self.assertRaisesRegex(Exception, 'Cannot find \\*\\* noSuchWorld \\*\\*'):
            KheperaSimulation().setupWorld('noSuchWorld', self.dataDir)


class SensorsAcrossAResetTest(unittest.TestCase):
    '''A light or quality sensor made before backend.reset() reads the new
    robot, as the motors, which find the robot by name, drive it.'''

    def setUp(self):
        import os
        self.dataDir = tempfile.mkdtemp()
        self.oldDataDir = os.environ.get('HOMEO_DATA_DIR')
        os.environ['HOMEO_DATA_DIR'] = self.dataDir

    def tearDown(self):
        import os
        if self.oldDataDir is None:
            os.environ.pop('HOMEO_DATA_DIR', None)
        else:
            os.environ['HOMEO_DATA_DIR'] = self.oldDataDir
        shutil.rmtree(self.dataDir, ignore_errors=True)

    def backend(self, world):
        import threading
        from Simulator.SimulatorBackend import SimulatorBackendHOMEO
        b = SimulatorBackendHOMEO(lock=threading.Lock(), robotName='Khepera')
        b.setDataDir(self.dataDir)
        b.kheperaSimulation.setupWorld(world, self.dataDir)
        return b

    def testSensorsMadeBeforeAResetReadTheNewRobot(self):
        from HomeoExperiments.KheperaExperiments.phototaxis_common import set_start_pose
        b = self.backend('kheperaBraitenberg3c_HOMEO_World')
        sim = b.kheperaSimulation
        eyes = {side: b.getSensor(side) for side in ('left', 'right')}
        heat = {side: b.getQualitySensor(side + 'TempEye', 'temperature') for side in ('left', 'right')}
        set_start_pose(sim.allBodies['Khepera'], 6.5, 6.5, 45)
        before = {side: eyes[side].read() for side in eyes}
        b.reset()
        robot = sim.allBodies['Khepera']
        for side in ('left', 'right'):
            self.assertIs(eyes[side].robot, robot)
            self.assertEqual(eyes[side].read(), robot.getSensorRead(side + 'Eye'))
            self.assertNotEqual(eyes[side].read(), before[side])
            self.assertEqual(heat[side].read(),
                             robot.getSensorReadByQuality(side + 'TempEye', 'temperature'))

    def testASensorGivenTheRobotItselfReadsIt(self):
        from RobotSimulator.Transducer import HOMEO_LightSensor
        b = self.backend('kheperaBraitenberg2_HOMEO_World')
        robot = b.kheperaSimulation.allBodies['Khepera']
        eye = HOMEO_LightSensor('left', robot)
        self.assertIs(eye.robot, robot)
        self.assertEqual(eye.read(), robot.getSensorRead('leftEye'))


class _FakeTransducer(object):
    def __init__(self, value=0.5, top=2.0):
        self.value, self.top, self.acted = value, top, []
    def read(self):
        return self.value
    def range(self):
        return (-self.top, self.top) if self.top else (0, 1)
    def act(self):
        self.acted.append(self.funcParameters)


class TransducerPropertiesTest(unittest.TestCase):
    '''The robot units' transducer properties: HomeoUnitInput reads the
    transducer it is given, HomeoUnitNewtonianActuator takes a new one, and
    HomeoUnitAristotelianActuator's 'actuator' and 'transducer' are one.'''

    def testAnInputUnitReadsTheTransducerItIsGiven(self):
        from RobotSimulator.HomeoUnitNewtonianTransduc import HomeoUnitInput
        unit = HomeoUnitInput(transducer=_FakeTransducer(0.25, top=0))
        unit.transducer = _FakeTransducer(0.75, top=0)
        unit.selfUpdate()
        self.assertAlmostEqual(unit.criticalDeviation, 0.75 * unit.maxDeviation)

    def testANewtonianActuatorTakesANewTransducer(self):
        from RobotSimulator.HomeoUnitNewtonianTransduc import HomeoUnitNewtonianActuator
        unit = HomeoUnitNewtonianActuator(transducer=_FakeTransducer())
        new = _FakeTransducer(top=4.0)
        unit.transducer = new
        self.assertIs(unit.transducer, new)
        unit._maxSpeedFraction = 0.5            # set after construction, as the setups do
        unit.selfUpdate()
        self.assertEqual(unit._maxSpeed, 2.0)  # 4.0 x 0.5, computed at the first update
        self.assertEqual(len(new.acted), 1)

    def testAGivenMaxSpeedIsKept(self):
        from RobotSimulator.HomeoUnitNewtonianTransduc import HomeoUnitNewtonianActuator
        unit = HomeoUnitNewtonianActuator(transducer=_FakeTransducer(), maxSpeed=0.3)
        unit.selfUpdate()
        self.assertEqual(unit._maxSpeed, 0.3)

    def testAnAristotelianActuatorsTransducerAndActuatorAreOne(self):
        from RobotSimulator.HomeoUnitNewtonianTransduc import HomeoUnitAristotelianActuator
        first, second = _FakeTransducer(), _FakeTransducer()
        unit = HomeoUnitAristotelianActuator(transducer=first)
        self.assertIs(unit.actuator, first)
        unit.actuator = second
        self.assertIs(unit.transducer, second)
        unit.selfUpdate()
        self.assertEqual(len(second.acted), 1)
        self.assertEqual(first.acted, [])


if __name__ == '__main__':
    unittest.main()
