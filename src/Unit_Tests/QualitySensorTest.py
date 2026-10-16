'''
@author: stefano

The Box2D Vehicle 3c world and its quality sensors, and the transducers after
a world reset.

The 3c world has five point sources of four qualities: a light, two heat
sources (one on the light), an oxygen and an organic-matter source.  Each
quality has its own pair of eyes, with the light eyes' receptors and field;
an eye reads only its own quality's sources.  The expected irradiances here
are computed from the e-puck2's receptor table and Webots' light model
(cosine law, inverse square, nothing from behind), independently of
KheperaRobot's own code.
'''
import math
import os
import shutil
import tempfile
import threading
import unittest

from KheperaSimulator.KheperaSimulator import KheperaRobot
from Simulator.SimulatorBackend import SimulatorBackendHOMEO
from HomeoExperiments.KheperaExperiments.phototaxis_common import set_start_pose

# The sources of the 3c world: name -> (quality, position, intensity)
SOURCES = {'LIGHT1': ('light', (7, 7), 100), 'TEMP1': ('temperature', (7, 7), 80),
           'TEMP2': ('temperature', (1, 7), 80), 'OXY1': ('oxygen', (2, 2), 100),
           'ORG1': ('organic', (6, 1), 100)}
# A quality's eye names, as the 3c setups wire them
EYES = {'light': ('leftEye', 'rightEye'), 'temperature': ('leftTempEye', 'rightTempEye'),
        'oxygen': ('leftOxyEye', 'rightOxyEye'), 'organic': ('leftOrgEye', 'rightOrgEye')}
POSES = [(4, 4, 45),           # facing the light (and TEMP1)
         (4, 4, 90),           # TEMP1 ahead right, TEMP2 ahead left
         (2.5, 2.5, -135),     # facing OXY1, the light straight behind
         (6, 1.6, -90),        # facing ORG1
         (4, 7, 180)]          # facing TEMP2


def expectedIrradiance(x, y, heading, eye, sources):
    '''The mean over the eye's two receptors of sum(I cos / d^2), each
    receptor seeing a source within 90 degrees of its facing.'''
    side = 'left' if eye.startswith('left') else 'right'
    receptors = KheperaRobot.EPUCK2['eyes'][side + 'Eye']
    h = math.radians(heading)
    total = 0.0
    for name in receptors:
        (fx, fy), facing = KheperaRobot.EPUCK2['receptors'][name]
        px = x + fx * math.cos(h) - fy * math.sin(h)
        py = y + fx * math.sin(h) + fy * math.cos(h)
        a = h + math.radians(facing)
        for source in sources:
            _, (sx, sy), intensity = SOURCES[source]
            dx, dy = sx - px, sy - py
            d = math.hypot(dx, dy)
            cos = (dx * math.cos(a) + dy * math.sin(a)) / d
            if cos >= 0:
                total += intensity * cos / d ** 2
    return total / len(receptors)


class _BackendTest(unittest.TestCase):

    def setUp(self):
        self.dataDir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dataDir, True)

    def backend(self, world):
        backend = SimulatorBackendHOMEO(lock=threading.Lock(), robotName='Khepera',
                                        dataDir=self.dataDir)
        backend.start(world)
        self.addCleanup(lambda: backend.kheperaSimulation.saveTrajectory())
        return backend


class Vehicle3cWorldTest(_BackendTest):

    def setUp(self):
        super().setUp()
        self.b = self.backend('kheperaBraitenberg3c_HOMEO_World')
        self.robot = self.b.kheperaSimulation.allBodies['Khepera']

    def testTheSourcesByQuality(self):
        bodies = self.b.kheperaSimulation.allBodies
        found = {q: sorted(b.userData['name'] for b in bs)
                 for q, bs in self.robot.detectableSources.items()}
        self.assertEqual(found, {'light': ['LIGHT1'], 'temperature': ['TEMP1', 'TEMP2'],
                                 'oxygen': ['OXY1'], 'organic': ['ORG1']})
        self.assertEqual(self.robot.detectableLights, [bodies['LIGHT1']])
        self.assertIs(bodies['TARGET'], bodies['LIGHT1'])
        for name, (_, (x, y), intensity) in SOURCES.items():
            self.assertEqual(bodies[name].userData['lightPos'], (x, 0, y))
            self.assertEqual(bodies[name].userData['intensity'], intensity)

    def testEachEyeSeesOnlyItsQuality(self):
        '''Every quality's eyes read the irradiance of that quality's sources
        alone, summed over them, and the transducers read the eyes' response
        to it.'''
        for x, y, heading in POSES:
            set_start_pose(self.robot, x, y, heading)
            for quality, eyes in EYES.items():
                sources = [n for n, s in SOURCES.items() if s[0] == quality]
                for eye in eyes:
                    with self.subTest(pose=(x, y, heading), eye=eye):
                        bodies = self.robot.detectableSources[quality]
                        irradiance = self.robot.irradAtSensor(eye, bodies)
                        self.assertAlmostEqual(irradiance,
                                               expectedIrradiance(x, y, heading, eye, sources),
                                               delta=1e-9 + 1e-4 * irradiance)
                        response = self.robot.eyeResponse(eye, irradiance)
                        self.assertEqual(self.robot.getSensorReadByQuality(eye, quality), response)
                        self.assertEqual(self.b.getQualitySensor(eye, quality).read(), response)

    def testWhatThePosesShow(self):
        '''The poses above test what they are meant to: the two heat sources
        add up, and an eye facing a source of another quality reads nothing.'''
        read = lambda eye, q: self.robot.irradAtSensor(eye, self.robot.detectableSources[q])
        set_start_pose(self.robot, 4, 4, 90)
        heat = read('leftTempEye', 'temperature')
        self.assertGreater(expectedIrradiance(4, 4, 90, 'leftTempEye', ['TEMP2']), 0)
        self.assertAlmostEqual(heat, expectedIrradiance(4, 4, 90, 'leftTempEye', ['TEMP1'])
                               + expectedIrradiance(4, 4, 90, 'leftTempEye', ['TEMP2']),
                               delta=1e-4 * heat)
        set_start_pose(self.robot, 2.5, 2.5, -135)
        self.assertGreater(read('leftOxyEye', 'oxygen'), 1)
        for eye in ('leftEye', 'rightEye'):
            self.assertEqual(read(eye, 'light'), 0)
            self.assertEqual(self.robot.getSensorRead(eye), 0)
            self.assertEqual(self.b.getSensor(eye[:-3]).read(), 0)

    def testTheLightEyesIgnoreTheHeatOnTheLight(self):
        '''TEMP1 sits on the light: the light eyes, and the light sensor
        transducers, read the light's 100 alone; the right heat eye, which
        does not see TEMP2 (90 degrees to the left), TEMP1's 80.'''
        set_start_pose(self.robot, 4, 4, 45)
        for side in ('left', 'right'):
            light = self.robot.irradAtSensor(side + 'Eye', self.robot.detectableLights)
            heat = self.robot.irradAtSensor(side + 'TempEye',
                                            self.robot.detectableSources['temperature'])
            if side == 'right':
                self.assertAlmostEqual(heat, 0.8 * light)
            else:
                self.assertGreater(heat, 0.8 * light * 1.1)
            self.assertEqual(self.b.getSensor(side).read(),
                             self.robot.eyeResponse(side + 'Eye', light))


class SensorsAfterResetTest(_BackendTest):
    '''backend.reset() rebuilds the world: a new robot, at the start pose.
    Transducers made after it read and drive the new robot; a motor made
    before it still drives it (it finds the robot by name).  Every caller
    (the GA, the replays) rebuilds the homeostat, and so its transducers,
    after a reset.'''

    def testTransducersAfterAReset(self):
        b = self.backend('kheperaBraitenberg2_HOMEO_World')
        sim = b.kheperaSimulation
        old = sim.allBodies['Khepera']
        start = (old.body.position[0], old.body.position[1], math.degrees(old.body.angle))
        motor = b.getWheel('right')
        set_start_pose(old, 6.5, 6.5, 45)                  # close to the light, facing it
        near = b.getSensor('left').read()
        b.reset()
        robot = sim.allBodies['Khepera']
        self.assertIsNot(robot, old)
        self.assertAlmostEqual(robot.body.position[0], start[0])
        self.assertAlmostEqual(robot.body.position[1], start[1])
        self.assertAlmostEqual(math.degrees(robot.body.angle), start[2])
        for side in ('left', 'right'):
            self.assertEqual(b.getSensor(side).read(), robot.getSensorRead(side + 'Eye'))
            self.assertLess(b.getSensor(side).read(), near)
        motor.funcParameters = 1.0
        motor.act()
        self.assertEqual(robot.getSpeed()['right'], 1.0 * robot.wheelRadius)
        self.assertEqual(old.getSpeed()['right'], 0)


if __name__ == '__main__':
    unittest.main()
