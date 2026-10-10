'''
Headless runs with the continuous (OU) uniselector.

In headless mode a unit reads its connections from JIT arrays, and the OU
uniselector evolves those arrays, not the connection objects.  These tests
check that the two stay consistent: the arrays keep their evolution across
Homeostat.runFor() calls, changes made to the connections between calls
still reach the arrays, data collection records the weights the run used,
and a headless run follows the same trajectory as the Python path.
'''
import random
import unittest

import numpy as np

from Core.Homeostat import Homeostat
from Core.HomeoUnit import HomeoUnit
from Core.HomeoUnitNewtonian import HomeoUnitNewtonian
from Core.HomeoUniselectorContinuous import HomeoUniselectorContinuous
from Core.HomeoJIT import seed_jit_rng


def ouHomeostat(seed, headless, noise=True):
    "Two fully connected Newtonian units with OU uniselectors"
    np.random.seed(seed)
    random.seed(seed)
    seed_jit_rng(seed)
    HomeoUnit.clearNames()
    hom = Homeostat()
    hom.slowingFactor = 0
    hom.collectsData = False
    for i in range(2):
        unit = HomeoUnitNewtonian()
        unit.setRandomValues()
        unit.uniselector = HomeoUniselectorContinuous()
        unit.uniselectorActive = True
        hom.addFullyConnectedUnit(unit)
    for unit in hom.homeoUnits:
        if not noise:
            unit.noise = 0
            for conn in unit.inputConnections:
                conn.noise = 0
        unit.criticalDeviation = 0.95 * unit.maxDeviation   # stressed: large OU steps
    hom._headless = headless
    for unit in hom.homeoUnits:
        unit._headless = headless
    return hom


def signedWeights(unit):
    return np.array([c.weight * c.switch for c in unit.inputConnections])


class HomeostatHeadlessTest(unittest.TestCase):

    def testChangeBetweenRunsReachesTheArrays(self):
        "A weight set between runFor() calls is used, and the other weights keep their OU drift"
        hom = ouHomeostat(5, headless=True)
        hom.runFor(500)
        unit = hom.homeoUnits[0]
        drifted = unit._jit_weights * unit._jit_switches
        changed = unit._jit_conns.index(unit.inputConnections[1])
        unit.inputConnections[1].newWeight(-0.123)
        unit._sync_jit_arrays()                   # what the next runFor() does first
        synced = unit._jit_weights * unit._jit_switches
        self.assertAlmostEqual(synced[changed], -0.123)
        others = [i for i in range(len(synced)) if i != changed]
        np.testing.assert_allclose(synced[others], drifted[others])

    def testDataCollectionRecordsTheEvolvedWeights(self):
        "Recorded connection weights are the ones the headless OU run is using"
        hom = ouHomeostat(7, headless=True)
        hom.collectsData = True
        start = {u.name: signedWeights(u) for u in hom.homeoUnits}
        hom.runFor(400)
        last = max(hom.dataCollector.states)
        for unit in hom.homeoUnits:
            recorded = hom.dataCollector.states[last][unit.name].connectedTo
            recordedWeights = np.array([recorded[c.incomingUnit.name][0] * recorded[c.incomingUnit.name][1]
                                        for c in unit.inputConnections])
            self.assertFalse(np.allclose(recordedWeights, start[unit.name]),
                             'the recorded weights never moved')

    def testHeadlessMatchesPythonPath(self):
        "With noise off, headless and Python runs of one seed follow the same trajectory"
        ticks = 600
        python = ouHomeostat(9, headless=False, noise=False)
        python.runFor(ticks)
        headless = ouHomeostat(9, headless=True, noise=False)
        headless.runFor(ticks)
        for unit in headless.homeoUnits:
            unit.flushJitArrays()
        for a, b in zip(python.homeoUnits, headless.homeoUnits):
            self.assertAlmostEqual(a.criticalDeviation, b.criticalDeviation, delta=1e-9)
            np.testing.assert_allclose(signedWeights(a), signedWeights(b), atol=1e-9)
