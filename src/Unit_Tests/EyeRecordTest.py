'''
The eyes of the direct phototaxis experiment, as configured and as recorded:
the saturation distance is computed against the
light's actual intensity, and runs record the eyes' actual threshold and
saturation, not the options as given.
'''
import json
import os
import tempfile
import unittest

import HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct as D


class EyeRecordTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ['HOMEO_DATA_DIR'] = self.tmp.name

    def tearDown(self):
        os.environ.pop('HOMEO_DATA_DIR', None)
        self.tmp.cleanup()

    def testSaturationAgainstTheLightsIntensity(self):
        for intensity in (50, -100):
            with self.subTest(intensity=intensity):
                hom, backend, _ = D.setup_phototaxis(seed=1, light_intensity=intensity,
                                                     eye_saturation=0.5)
                sim = backend.kheperaSimulation
                sim.saveTrajectory()
                ud = sim.allBodies['Khepera'].sensors['leftEye'].userData
                self.assertAlmostEqual(ud['leftEyeSaturation'], abs(intensity) / 0.25)
                self.assertAlmostEqual(sim.eyeConfig[1], abs(intensity) / 0.25)

    def testRunsRecordTheEyesAsConfigured(self):
        r = D.run_headless(total_steps=100, quiet=True, seed=1, eye_response='log',
                           eye_saturation=0.5)
        r['backend'].kheperaSimulation.saveTrajectory()
        self.assertEqual(r['eye_threshold'], 1.0)          # a log eye's default I0
        self.assertEqual(r['eye_response'], 'log')
        self.assertAlmostEqual(r['eye_saturation_irradiance'], 400.0)
        with open(r['json_path']) as f:
            settings = json.load(f)['settings']
        self.assertEqual(settings['eye_threshold'], 1.0)
        self.assertEqual(settings['light_intensity'], 100)


if __name__ == '__main__':
    unittest.main()
