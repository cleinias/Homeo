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
Tests of the noise the simulation actually uses.

Units and connections draw their noise from
HomeoNoise.unitNoise and HomeoNoise.connNoise (Python path) and from their
copies _jit_unit_noise and _jit_conn_noise in Core/HomeoJIT.py (headless path).
All four are "distorting normal" noise: a Gaussian with standard deviation
bound/3, clipped to [-bound, bound], where bound is the unit's noise (linear),
or the connection's noise times |current| (proportional, and so 0 when the
current is 0).

Each test runs on a fixed random stream (see conftest.py), so the statistical
checks are deterministic; their tolerances are still set wide enough (5
standard errors) that a correct implementation passes for any stream.
'''
import unittest

import numpy as np

from Helpers.HomeoNoise import HomeoNoise
from Core.HomeoJIT import _jit_unit_noise, _jit_conn_noise

SAMPLES = 20000

# Clipping a normal at 3 sigma lowers its standard deviation slightly.
CLIPPED_STD_FACTOR = 0.9987


def unitSamples(function, noise):
    return np.array([function(noise) for i in range(SAMPLES)])


def connSamples(function, current, noise):
    return np.array([function(current, noise) for i in range(SAMPLES)])


class HomeoProductionNoiseTest(unittest.TestCase):

    def checkDistortingNormal(self, values, bound):
        "Values within the bound, centred on 0, with standard deviation bound/3"
        self.assertGreaterEqual(values.min(), -bound)
        self.assertLessEqual(values.max(), bound)
        sigma = bound / 3
        self.assertLessEqual(abs(values.mean()), 5 * sigma / np.sqrt(SAMPLES))
        # The sample standard deviation of a normal has standard error
        # sigma / sqrt(2n).
        self.assertAlmostEqual(values.std(), sigma * CLIPPED_STD_FACTOR,
                               delta=5 * sigma / np.sqrt(2 * SAMPLES))

    def testZeroNoiseGivesZero(self):
        for current in (-0.7, 0.0, 0.4):
            self.assertEqual(HomeoNoise.connNoise(current, 0), 0)
            self.assertEqual(_jit_conn_noise(current, 0.0), 0)
        self.assertEqual(HomeoNoise.unitNoise(0), 0)
        self.assertEqual(_jit_unit_noise(0.0), 0)

    def testUnitNoisePython(self):
        for noise in (0.05, 0.3):
            self.checkDistortingNormal(unitSamples(HomeoNoise.unitNoise, noise), noise)

    def testUnitNoiseJit(self):
        for noise in (0.05, 0.3):
            self.checkDistortingNormal(unitSamples(_jit_unit_noise, noise), noise)

    def testConnNoisePython(self):
        for current, noise in ((0.8, 0.1), (-0.25, 0.4)):
            self.checkDistortingNormal(connSamples(HomeoNoise.connNoise, current, noise),
                                       noise * abs(current))

    def testConnNoiseJit(self):
        for current, noise in ((0.8, 0.1), (-0.25, 0.4)):
            self.checkDistortingNormal(connSamples(_jit_conn_noise, current, noise),
                                       noise * abs(current))

    def testConnNoiseIsContinuousAtZeroCurrent(self):
        '''No noise on a connection carrying no current, as next to it: no
        jump to the full noise at exactly 0.'''
        for function in (HomeoNoise.connNoise, _jit_conn_noise):
            self.assertTrue(np.all(connSamples(function, 0.0, 0.2) == 0))
            self.assertLessEqual(np.abs(connSamples(function, 1e-9, 0.2)).max(), 0.2 * 1e-9)

    def testClippingHappens(self):
        "Draws beyond 3 sigma are clipped to the bound, not dropped or redrawn"
        # With noise 1, P(|z| > 3) is about 0.27%: some 54 of 20000 draws.
        for function in (HomeoNoise.unitNoise, _jit_unit_noise):
            values = unitSamples(function, 1.0)
            self.assertGreater(np.sum(np.abs(values) == 1.0), 10)
