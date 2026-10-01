'''Regression tests for the continuous (OU) uniselector in headless mode.

The OU uniselector silently did nothing in headless mode from its first commit
(629dfce, 2026-02-26) until 2026-10-01: HomeoUnit.selfUpdate() marked the JIT
arrays dirty after evolve_weights_jit() had modified them, so the next tick
rebuilt them from the untouched connection objects and discarded the step.
Since every batch run and every GA evaluation is headless, all OU results
produced in that window are frozen-weight results.
'''

import unittest
import numpy as np

from Core.Homeostat import Homeostat
from Core.HomeoUnitNewtonian import HomeoUnitNewtonian
from Core.HomeoUniselectorContinuous import HomeoUniselectorContinuous


def _twoUnitHomeostat(headless):
    "Two mutually connected Newtonian units with OU uniselectors."
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
        "The OU process must actually move the weights when headless."
        np.random.seed(42)
        hom = _twoUnitHomeostat(headless=True)
        hom.runFor(1)
        before = _signedWeights(hom)
        hom.runFor(2000)
        after = _signedWeights(hom)
        self.assertGreater(
            np.abs(after - before).max(), 1e-3,
            "headless OU weights did not change over 2000 ticks -- the JIT "
            "arrays are being discarded again (see this module's docstring)")

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
                           "headless OU drift is an order of magnitude below "
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
