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

'''Tests of the continuous uniselector in headless mode.

In headless mode evolve_weights_jit() moves the weights in the JIT arrays.
HomeoUnit.selfUpdate() must not mark the arrays dirty after that step: the
next tick would rebuild them from the untouched connection objects and
discard the step, and the continuous uniselector would silently do nothing.
Every batch run and every GA evaluation is headless.
'''

import unittest
import numpy as np

from Core.Homeostat import Homeostat
from Core.HomeoUnitNewtonian import HomeoUnitNewtonian
from Core.HomeoUniselectorContinuous import HomeoUniselectorContinuous


def _twoUnitHomeostat(headless):
    "Two mutually connected Newtonian units with continuous uniselectors."
    hom = Homeostat()
    HomeoUnitNewtonian.clearNames()
    for _ in range(2):
        u = HomeoUnitNewtonian()
        u.setRandomValues()
        u.uniselectorActive = True
        u.uniselector = HomeoUniselectorContinuous()
        u.maxDeviation = 10
        hom.addFullyConnectedUnit(u)
    hom.slowingFactor = 0
    hom.collectsData = False
    hom._headless = headless
    for u in hom.homeoUnits:
        u._headless = headless
        u.criticalDeviation = 5.0        # non-trivial stress, so sigma > sigma_base
        for c in u.inputConnections:
            c.state = 'uniselector'
            c.status = True
    return hom


def _signedWeights(hom):
    "Signed weights as the dynamics currently see them."
    out = []
    for u in hom.homeoUnits:
        if getattr(u, '_headless', False) and not getattr(u, '_jit_dirty', True):
            out += [float(w * s) for w, s in zip(u._jit_weights, u._jit_switches)]
        else:
            out += [c.switch * c.weight for c in u.inputConnections if c.isActive()]
    return np.array(out)


class HomeoUniselectorContinuousHeadlessTest(unittest.TestCase):

    def testWeightsEvolveInHeadlessMode(self):
        "The continuous uniselector must actually move the weights when headless."
        np.random.seed(42)
        hom = _twoUnitHomeostat(headless=True)
        hom.runFor(1)
        before = _signedWeights(hom)
        hom.runFor(2000)
        after = _signedWeights(hom)
        self.assertGreater(
            np.abs(after - before).max(), 1e-3,
            "headless continuous-uniselector weights did not change over 2000 ticks -- the JIT "
            "arrays are being discarded (see this module's docstring)")

    def testHeadlessAndNonHeadlessBothEvolve(self):
        "Headless must not be systematically quieter than non-headless."
        moves = {}
        for headless in (True, False):
            np.random.seed(42)
            hom = _twoUnitHomeostat(headless=headless)
            hom.runFor(1)
            before = _signedWeights(hom)
            hom.runFor(2000)
            moves[headless] = np.abs(_signedWeights(hom) - before).max()
        self.assertGreater(moves[True], moves[False] / 10.0,
                           "headless continuous-uniselector drift is an order of magnitude below "
                           "non-headless: %r" % moves)

    def testFlushJitArraysExposesEvolvedWeights(self):
        "flushJitArrays() must publish the evolved weights to the connections."
        np.random.seed(7)
        hom = _twoUnitHomeostat(headless=True)
        hom.runFor(2000)
        arrays = _signedWeights(hom)
        for u in hom.homeoUnits:
            u.flushJitArrays()
        conns = np.array([c.switch * c.weight
                          for u in hom.homeoUnits
                          for c in u.inputConnections if c.isActive()])
        np.testing.assert_allclose(conns, arrays, rtol=1e-9,
                                   err_msg="connection objects do not match the "
                                           "JIT arrays after flushJitArrays()")


if __name__ == '__main__':
    unittest.main()
