'''
@author: stefano

Chemical fields: a source's law (how its value falls off with distance),
direction-free (chemical) eyes, the chemotaxis world, the field laws the
Vehicle 3c world takes, and feeding from a field.  The expected values are
computed here from the laws' closed forms and the e-puck2's receptor table,
independently of KheperaRobot's code.
'''
import math
import os
import shutil
import tempfile
import threading
import unittest

from scipy.special import k0

from KheperaSimulator.KheperaSimulator import (KheperaRobot, KheperaSimulation, CHEMOTAXIS_FIELD,
                                               CHEMICAL_EYE_RANGE, checkFieldLaw)
from Simulator.SimulatorBackend import SimulatorBackendHOMEO
from Simulator.HomeoExperiments import add_battery_to_homeostat, FOOD_SOURCE_RADIUS
from HomeoExperiments.KheperaExperiments.phototaxis_common import set_start_pose


class Source(object):
    "Stands in for a source body"
    def __init__(self, intensity=100, law=None, position=(0, 0)):
        self.userData = {'intensity': intensity, 'attenVec': (0, 0, 1), 'ambRatio': 0,
                         'lightPos': (position[0], 0, position[1])}
        if law is not None:
            self.userData['law'] = law


def k0Field(r, length=2.0, radius=0.06, c0=100.0):
    return c0 if r <= radius else c0 * k0(r / length) / k0(radius / length)


def receptorPositions(x, y, heading, eye):
    "The world positions of an e-puck2 eye's receptors"
    h = math.radians(heading)
    for name in KheperaRobot.EPUCK2['eyes'][eye]:
        (fx, fy), _ = KheperaRobot.EPUCK2['receptors'][name]
        yield x + fx * math.cos(h) - fy * math.sin(h), y + fx * math.sin(h) + fy * math.cos(h)


class LawTest(unittest.TestCase):

    def testTheLaws(self):
        value = KheperaRobot.sourceValue
        self.assertEqual(value(Source(), 2.0), 25.0)                              # the light's
        self.assertEqual(value(Source(law={'law': 'inverse_square'}), 2.0), 25.0)
        k = Source(law=dict(CHEMOTAXIS_FIELD))
        for r in (0.0, 0.06, 0.5, 3.0):
            self.assertAlmostEqual(value(k, r), k0Field(r), places=10)
        g = Source(law={'law': 'gaussian', 'sigma': 2.0})
        self.assertAlmostEqual(value(g, 2.0), 100 * math.exp(-0.5))
        c = Source(law={'law': 'cone', 'radius': 8.0})
        self.assertAlmostEqual(value(c, 2.0), 75.0)
        self.assertEqual(value(c, 9.0), 0.0)

    def testBadLaws(self):
        for law in ({'law': 'plume'}, {'law': 'k0', 'length': 2.0}, {'law': 'gaussian', 'sigma': 0},
                    {'law': 'cone'}):
            with self.assertRaises(ValueError, msg=law):
                checkFieldLaw(law)


class _WorldTest(unittest.TestCase):

    def setUp(self):
        self.dataDir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dataDir, True)

    def backend(self, world, fieldLaws=None):
        backend = SimulatorBackendHOMEO(lock=threading.Lock(), robotName='Khepera',
                                        dataDir=self.dataDir)
        if fieldLaws:
            backend.kheperaSimulation.fieldLaws = fieldLaws
        backend.start(world)
        self.addCleanup(backend.kheperaSimulation.saveTrajectory)
        return backend


class ChemotaxisWorldTest(_WorldTest):

    def setUp(self):
        super().setUp()
        self.b = self.backend('kheperaChemotaxis_HOMEO_World')
        self.sim = self.b.kheperaSimulation
        self.robot = self.sim.allBodies['Khepera']

    def testTheWorld(self):
        food = self.sim.allBodies['FOOD']
        self.assertIs(self.sim.allBodies['TARGET'], food)
        self.assertEqual(food.userData['quality'], 'organic')
        self.assertEqual(food.userData['lightPos'], (7, 0, 7))
        self.assertEqual(food.userData['law'], CHEMOTAXIS_FIELD)
        self.assertEqual(self.robot.detectableLights, [])
        self.assertEqual(self.sim.vehicleEyes, ('leftOrgEye', 'rightOrgEye', 'organic'))
        self.assertEqual(sorted(self.robot.directionFreeEyes()), ['leftOrgEye', 'rightOrgEye'])
        self.assertEqual(self.sim.fieldSettings(), {'FOOD': CHEMOTAXIS_FIELD})

    def testTheChemicalEyesSensitivity(self):
        threshold, saturation, response = self.robot.eyeSettings()['leftOrgEye']
        self.assertAlmostEqual(threshold, k0Field(CHEMICAL_EYE_RANGE))
        self.assertEqual((saturation, response), (100.0, 'log'))

    def testAChemicalEyeReadsTheFieldAtItsReceptors(self):
        for x, y, heading in ((4, 4, 0), (6.5, 6.2, 30), (8, 8, 45), (7.3, 6.6, 160)):
            set_start_pose(self.robot, x, y, heading)
            for eye in ('leftEye', 'rightEye'):
                expected = sum(k0Field(math.hypot(px - 7, py - 7))
                               for px, py in receptorPositions(x, y, heading, eye)) / 2
                name = eye.replace('Eye', 'OrgEye')
                # (Box2D keeps the body's position in single precision)
                self.assertAlmostEqual(self.robot.irradAtSensor(
                    name, self.robot.detectableSources['organic']), expected,
                    delta=1e-6 * expected)

    def testAChemicalEyeSensesASourceBehindIt(self):
        set_start_pose(self.robot, 8, 8, 45)          # the food straight behind
        left, right = self.sim.vehicleSensorReads()
        self.assertGreater(left, 0)
        self.assertGreater(right, 0)

    def testTheEyesAreEqualAtTheFood(self):
        set_start_pose(self.robot, 7, 7, 30)
        self.assertEqual(self.sim.vehicleSensorReads(), (1.0, 1.0))

    def testFeedingFromTheField(self):
        from Core.Homeostat import Homeostat
        add_battery_to_homeostat(Homeostat(), self.b, food_quality='organic')
        set_start_pose(self.robot, 5.5, 7, 0)
        self.assertAlmostEqual(self.robot.foodAtCentre(), k0Field(1.5), places=9)
        battery = self.robot.battery
        self.assertAlmostEqual(battery.recharge_factor * k0Field(1.0), battery.discharge_rate)
        self.assertAlmostEqual(battery.saturation, k0Field(FOOD_SOURCE_RADIUS))
        battery.level = 0.5
        set_start_pose(self.robot, 6, 7, 0)            # 1 from the food: break-even
        self.sim.tickAdvance()
        self.assertAlmostEqual(battery.level, 0.5, places=9)

    def testAnotherLengthOnRequest(self):
        b = self.backend('kheperaChemotaxis_HOMEO_World',
                         {'organic': {'law': 'k0', 'length': 1.0, 'radius': 0.06}})
        food = b.kheperaSimulation.allBodies['FOOD']
        self.assertAlmostEqual(KheperaRobot.sourceValue(food, 2.0),
                               k0Field(2.0, length=1.0), places=10)


class Vehicle3cFieldsTest(_WorldTest):

    def testAQualityWithAFieldHasChemicalEyes(self):
        law = {'law': 'gaussian', 'sigma': 3.0}
        b = self.backend('kheperaBraitenberg3c_HOMEO_World', {'organic': law})
        sim = b.kheperaSimulation
        robot = sim.allBodies['Khepera']
        self.assertEqual(sim.allBodies['ORG1'].userData['law'], law)
        self.assertNotIn('law', sim.allBodies['OXY1'].userData)
        self.assertEqual(sorted(robot.directionFreeEyes()), ['leftOrgEye', 'rightOrgEye'])
        set_start_pose(robot, 6, 3, 90)                # ORG1 (6, 1) straight behind
        self.assertGreater(robot.getSensorReadByQuality('leftOrgEye', 'organic'), 0)
        self.assertEqual(sim.vehicleEyes, ('leftEye', 'rightEye', 'light'))

    def testWithoutFieldsTheWorldIsAsItWas(self):
        robot = self.backend('kheperaBraitenberg3c_HOMEO_World').kheperaSimulation.allBodies['Khepera']
        self.assertEqual(robot.directionFreeEyes(), [])

    def testOnlyChemicalQualities(self):
        with self.assertRaises(ValueError):
            self.backend('kheperaBraitenberg3c_HOMEO_World', {'light': dict(CHEMOTAXIS_FIELD)})


class DirectionalEyesTest(unittest.TestCase):
    "A light eye seeing a source with a law: the law's fall-off times the cosine"

    def testADirectionalEyeOnAFieldSource(self):
        sim = KheperaSimulation()
        sim.dataDir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, sim.dataDir, True)
        sim.setupWorld('kheperaBraitenberg2_HOMEO_World')
        self.addCleanup(sim.saveTrajectory)
        robot, light = sim.allBodies['Khepera'], sim.allBodies['TARGET']
        set_start_pose(robot, 4, 4, 45)
        square = robot.irradAtSensor('leftEye', [light])
        light.userData['law'] = {'law': 'inverse_square'}
        self.assertEqual(robot.irradAtSensor('leftEye', [light]), square)
        light.userData['law'] = {'law': 'cone', 'radius': 100.0}
        cone = robot.irradAtSensor('leftEye', [light])
        self.assertGreater(cone, square)                # the cone falls off far more slowly


if __name__ == '__main__':
    unittest.main()
