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


def ouHomeostat(seed, headless, noise=True, units=2, inactive=(), unitClass=HomeoUnitNewtonian):
    """Fully connected units (two Newtonian ones by default) with OU
    uniselectors; the units numbered in inactive are switched off."""
    np.random.seed(seed)
    random.seed(seed)
    seed_jit_rng(seed)
    HomeoUnit.clearNames()
    hom = Homeostat()
    hom.slowingFactor = 0
    hom.collectsData = False
    for i in range(units):
        unit = unitClass()
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
    for i in inactive:
        hom.homeoUnits[i].disactivate()
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

    def testInactiveUnitsLinksAreLeftAloneByBothPaths(self):
        """A uniselector link from a switched-off unit carries nothing, and
        neither path evolves it, so the two still follow one trajectory"""
        ticks = 600
        runs = []
        for headless in (False, True):
            hom = ouHomeostat(9, headless=headless, noise=False, units=3, inactive=(2,))
            link = [c for c in hom.homeoUnits[0].inputConnections
                    if c.incomingUnit is hom.homeoUnits[2]][0]
            self.assertEqual(link.state, 'uniselector')
            self.assertTrue(link.isActive())
            before = link.weight * link.switch
            hom.runFor(ticks)
            for unit in hom.homeoUnits:
                unit.flushJitArrays()
            self.assertEqual(link.weight * link.switch, before)
            runs.append(hom)
        python, headless = runs
        for a, b in zip(python.homeoUnits[:2], headless.homeoUnits[:2]):
            self.assertAlmostEqual(a.criticalDeviation, b.criticalDeviation, delta=1e-9)
            np.testing.assert_allclose(signedWeights(a), signedWeights(b), atol=1e-9)

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

    def testHeadlessMatchesPythonPathForAshbysUnits(self):
        """The same for Ashby's own (Aristotelian) units, HomeoUnit, whose
        selfUpdate has its own headless OU branch.  The weights drift,
        through the JIT arrays."""
        ticks = 600
        python = ouHomeostat(9, headless=False, noise=False, unitClass=HomeoUnit)
        start = [signedWeights(unit) for unit in python.homeoUnits]
        python.runFor(ticks)
        headless = ouHomeostat(9, headless=True, noise=False, unitClass=HomeoUnit)
        headless.runFor(ticks)
        for unit in headless.homeoUnits:
            self.assertIs(type(unit), HomeoUnit)
            self.assertTrue(hasattr(unit, '_jit_weights'))       # the headless path ran
            unit.flushJitArrays()
        for a, b, w0 in zip(python.homeoUnits, headless.homeoUnits, start):
            self.assertGreater(np.abs(signedWeights(b) - w0).max(), 1e-3)
            self.assertAlmostEqual(a.criticalDeviation, b.criticalDeviation, delta=1e-9)
            np.testing.assert_allclose(signedWeights(a), signedWeights(b), atol=1e-9)


class ConnectionChangesBetweenRunsTest(unittest.TestCase):
    '''Changing a connection's state, noise or status between headless
    runFor() calls keeps the weights the uniselector evolved, as the Python
    path does; setAbsoluteWeight keeps the sign the run has now.  Noise off:
    the two paths of one seed follow the same trajectory.'''

    def changed(self, headless, change):
        "300 ticks, the change on every connection but the self-connections, one more tick"
        hom = ouHomeostat(3, headless, noise=False, units=3)
        hom.runFor(300)
        # (no flushJitArrays here: a script changes the connections as they are)
        evolved = [signedWeights(u) for u in hom.homeoUnits] if not headless else None
        for unit in hom.homeoUnits:
            for conn in unit.inputConnections[1:]:
                if change == 'state':
                    conn.state = 'manual'
                elif change == 'noise':
                    conn.noise = 0.0
                elif change == 'status':
                    conn.status = True
                else:
                    conn.setAbsoluteWeight(0.5)
        hom.runFor(301)
        for unit in hom.homeoUnits:
            unit.flushJitArrays()
        return hom, evolved

    def testTheEvolvedWeightsAreKept(self):
        for change in ('state', 'noise', 'status', 'absolute weight'):
            with self.subTest(change=change):
                python, _ = self.changed(False, change)
                headless, evolved = self.changed(True, change)
                for a, b in zip(python.homeoUnits, headless.homeoUnits):
                    np.testing.assert_allclose(signedWeights(a), signedWeights(b), atol=1e-9)
                python, evolved = self.changed(False, change)
                if change == 'state':                  # frozen: the weights stay
                    for unit, w in zip(python.homeoUnits, evolved):
                        np.testing.assert_allclose(signedWeights(unit), w, atol=1e-12)


def ashbyHomeostat(seed, headless, unitClass):
    """Three fully connected units with Ashby's discrete uniselector, firing
    often (critThreshold 0.05, interval 20), noise off."""
    np.random.seed(seed)
    random.seed(seed)
    seed_jit_rng(seed)
    HomeoUnit.clearNames()
    hom = Homeostat()
    hom.slowingFactor = 0
    hom.collectsData = False
    for i in range(3):
        unit = unitClass()
        unit.setRandomValues()
        unit.uniselectorActive = True
        unit.uniselectorTimeInterval = 20
        unit.critThreshold = 0.05
        hom.addFullyConnectedUnit(unit)
    for unit in hom.homeoUnits:
        unit.noise = 0
        for conn in unit.inputConnections:
            conn.noise = 0
    hom._headless = headless
    for unit in hom.homeoUnits:
        unit._headless = headless
    return hom


class DiscreteUniselectorParityTest(unittest.TestCase):
    '''With Ashby's discrete uniselector too, a headless run and a Python
    run of one seed fire at the same ticks and follow the same trajectory,
    for both unit classes.'''

    def testHeadlessMatchesPythonPath(self):
        for unitClass in (HomeoUnit, HomeoUnitNewtonian):
            with self.subTest(unitClass=unitClass.__name__):
                runs = []
                for headless in (False, True):
                    hom = ashbyHomeostat(4, headless, unitClass)
                    hom.runFor(2000)
                    for unit in hom.homeoUnits:
                        unit.flushJitArrays()
                    runs.append(hom)
                python, headless = runs
                counts = [u.uniselectorActivationCount for u in python.homeoUnits]
                self.assertGreater(min(counts), 5)                  # it does fire
                self.assertEqual([u.uniselectorActivationCount for u in headless.homeoUnits],
                                 counts)
                for a, b in zip(python.homeoUnits, headless.homeoUnits):
                    self.assertAlmostEqual(a.criticalDeviation, b.criticalDeviation, delta=1e-9)
                    np.testing.assert_allclose(signedWeights(a), signedWeights(b), atol=1e-9)
