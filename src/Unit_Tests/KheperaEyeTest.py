'''
Created on Oct 3, 2026

@author: stefano

The Khepera robot's eyes.  irradAtSensor is physics -- the irradiance on the
eye, intensity x cos(angle) / d^2 inside its field of view, unclipped and with
no distance cut-off -- and eyeResponse is the eye: 0 up to its threshold, 1 from
its saturation on, linear or logarithmic (Weber-Fechner) in between.  The
transducer reports that response, so its range is (0, 1).
'''
import os
import tempfile
import unittest
from math import log, radians, cos, sqrt

try:
    from HomeoExperiments.KheperaExperiments import phototaxis_braitenberg2_direct as D
    HAS_BOX2D = True
except ImportError:
    HAS_BOX2D = False


@unittest.skipUnless(HAS_BOX2D, "Box2D not installed — KheperaSimulator unavailable")
class KheperaEyeTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ['HOMEO_DATA_DIR'] = self.tmp.name

    def tearDown(self):
        for backend in getattr(self, '_backends', []):
            backend.kheperaSimulation.saveTrajectory()
        os.environ.pop('HOMEO_DATA_DIR', None)
        self.tmp.cleanup()

    def _robot(self, **eyes):
        hom, backend, _ = D.setup_phototaxis(fixed_weights=True, seed=1, motor='aristotelian', **eyes)
        self._backends = getattr(self, '_backends', []) + [backend]
        return backend.kheperaSimulation.allBodies['Khepera'], backend

    def _face_light(self, robot, d):
        "Put the robot d units from the light at (7, 7), facing it."
        D.set_start_pose(robot, x=7 - d / sqrt(2), y=7 - d / sqrt(2), heading=45)

    def testIrradianceIsUnclippedAndHasNoDistanceCutoff(self):
        "irradAtSensor is physics: no clip at the old max value, no zero beyond the old 10 units"
        robot, _ = self._robot()
        self._face_light(robot, 0.3)
        self.assertGreater(robot.irradAtSensor('leftEye', robot.detectableLights), 100)
        self._face_light(robot, 15)
        far = robot.irradAtSensor('leftEye', robot.detectableLights)
        self.assertGreater(far, 0)
        self.assertAlmostEqual(far, 100 * cos(radians(21.8858)) / 15 ** 2, delta=0.01 * far)

    def testFieldOfViewStillApplies(self):
        "a light behind the eye gives no irradiance"
        robot, _ = self._robot()
        D.set_start_pose(robot, x=4, y=4, heading=225)
        self.assertEqual(robot.irradAtSensor('leftEye', robot.detectableLights), 0)

    def testDefaultEyeIsLinearSaturatingAt100(self):
        "default: linear, threshold 0, saturation 100 -- response = min(I, 100) / 100"
        robot, _ = self._robot()
        for d in (8, 3, 1.5, 0.5):
            self._face_light(robot, d)
            irr = robot.irradAtSensor('leftEye', robot.detectableLights)
            self.assertAlmostEqual(robot.getSensorRead('leftEye'), min(irr, 100) / 100, places=12)

    def testLinearAndLogResponses(self):
        robot, _ = self._robot()
        robot.setEyeSensitivity('leftEye', threshold=2, saturation=50, response='linear')
        self.assertEqual(robot.eyeResponse('leftEye', 1), 0.0)
        self.assertEqual(robot.eyeResponse('leftEye', 60), 1.0)
        self.assertAlmostEqual(robot.eyeResponse('leftEye', 26), 0.5, places=12)
        robot.setEyeSensitivity('leftEye', threshold=1, saturation=400, response='log')
        self.assertEqual(robot.eyeResponse('leftEye', 1), 0.0)
        self.assertEqual(robot.eyeResponse('leftEye', 400), 1.0)
        self.assertAlmostEqual(robot.eyeResponse('leftEye', 20), log(20) / log(400), places=12)
        # Weber: equal ratios of intensity give equal steps of response
        step = robot.eyeResponse('leftEye', 40) - robot.eyeResponse('leftEye', 20)
        self.assertAlmostEqual(robot.eyeResponse('leftEye', 80) - robot.eyeResponse('leftEye', 40),
                               step, places=12)

    def testInvalidSensitivityIsRefused(self):
        robot, _ = self._robot()
        with self.assertRaises(ValueError):
            robot.setEyeSensitivity('leftEye', threshold=0, response='log')
        with self.assertRaises(ValueError):
            robot.setEyeSensitivity('leftEye', threshold=200, saturation=100)
        with self.assertRaises(ValueError):
            robot.setEyeSensitivity('leftEye', response='cubic')

    def testTransducerReportsTheResponseOnAUnitScale(self):
        _, backend = self._robot()
        sensor = backend.getSensor('left')
        self.assertEqual(sensor.range(), (0, 1.0))

    def testConfigureEyesSetsSaturationByDistance(self):
        "--eye-saturation D saturates the eye at D units: Isat = intensity / D^2; a log eye gets threshold 1"
        robot, backend = self._robot(eye_saturation=0.5, eye_response='log')
        ud = robot.sensors['rightEye'].userData
        self.assertEqual((ud['rightEyeThreshold'], ud['rightEyeSaturation'], ud['rightEyeResponse']),
                         (1.0, 400.0, 'log'))
        self.assertEqual(D.eye_tag(0.5, None, 'log'), '_log_sat0.5')
        self.assertEqual(D.eye_tag(), '')
        self.assertIn('_log_sat0.5', backend.kheperaSimulation.experimentName)


if __name__ == "__main__":
    unittest.main()
