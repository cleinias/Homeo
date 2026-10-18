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
