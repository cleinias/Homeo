'''
Created on Oct 13, 2026

@author: stefano

The homeostat's resets, used by the GUIs' reset buttons (review finding
CU-06).  A full reset gives the units default parameters and random values
but leaves them the units they were: their names, their headless mode, their
dt_fast, and a self-connection that stays manual, with the weight the
potentiometer says.  A time reset starts the clock again from the units'
present state: outputs that match the deviations, and a uniselector that
starts afresh.  The full reset handed the self-connections to the
uniselector, renamed the units and turned headless mode off; the time reset
zeroed the outputs and kept the uniselector's timer and count.
'''
from Core.Homeostat import Homeostat
from Core.HomeoUnit import HomeoUnit
from Core.HomeoUnitNewtonian import HomeoUnitNewtonian

import unittest

import numpy as np

NAMES = ['Left', 'Right', 'Up', 'Down']


def _homeostat(headless=False):
    np.random.seed(7)
    HomeoUnit.clearNames()
    hom = Homeostat()
    hom.slowingFactor = 0
    hom.collectsData = False
    for name in NAMES:
        unit = HomeoUnitNewtonian()
        unit.setRandomValues()
        unit.name = name
        unit.dt_fast = 0.5
        hom.addFullyConnectedUnit(unit)
    hom._headless = headless
    for unit in hom.homeoUnits:
        unit._headless = headless
    return hom


class ResetTest(unittest.TestCase):

    def testFullResetKeepsTheSelfConnectionsManual(self):
        hom = _homeostat()
        hom.fullReset()
        for unit in hom.homeoUnits:
            selfConnection = unit.inputConnections[0]
            self.assertIs(selfConnection.incomingUnit, unit)
            self.assertEqual(selfConnection.state, 'manual', unit.name)
            self.assertAlmostEqual(abs(selfConnection.weight * selfConnection.switch),
                                   unit.potentiometer)
            weight = selfConnection.weight
            unit.operateUniselector()
            self.assertEqual(selfConnection.weight, weight)

    def testFullResetKeepsTheUnits(self):
        for headless in (False, True):
            with self.subTest(headless=headless):
                hom = _homeostat(headless)
                hom.fullReset()
                self.assertEqual([u.name for u in hom.homeoUnits], NAMES)
                self.assertEqual([u._headless for u in hom.homeoUnits], [headless] * 4)
                self.assertEqual([u.dt_fast for u in hom.homeoUnits], [0.5] * 4)
                hom.runFor(5)

    def testFullResetKeepsTheUniselectors(self):
        "each unit keeps its kind of uniselector, on or off, with that kind's defaults"
        from Core.HomeoUniselectorContinuous import HomeoUniselectorContinuous
        from Core.HomeoUniselectorUniformRandom import HomeoUniselectorUniformRandom
        from Core.HomeoUniselectorAshby import HomeoUniselectorAshby
        hom = _homeostat()
        left, right, up, down = hom.homeoUnits
        left.uniselector = HomeoUniselectorContinuous()
        left.uniselector.tau_a = 50.0
        right.uniselector = HomeoUniselectorUniformRandom()
        up.uniselectorActive = False
        hom.fullReset()
        self.assertEqual([type(u.uniselector) for u in hom.homeoUnits],
                         [HomeoUniselectorContinuous, HomeoUniselectorUniformRandom,
                          HomeoUniselectorAshby, HomeoUniselectorAshby])
        self.assertEqual(left.uniselector.tau_a,
                         HomeoUniselectorContinuous.DefaultParameters['tau_a'])
        self.assertEqual([u.uniselectorActive for u in hom.homeoUnits],
                         [True, True, False, True])

    def testDefaultValuesKeepThePotentiometerInStep(self):
        hom = _homeostat()
        hom.restoreDefaultValuesForAllUnits()
        for unit in hom.homeoUnits:
            selfConnection = unit.inputConnections[0]
            self.assertAlmostEqual(abs(selfConnection.weight * selfConnection.switch),
                                   unit.potentiometer)

    def testTimeResetStartsFromThePresentState(self):
        hom = _homeostat()
        for unit in hom.homeoUnits:
            unit.uniselectorActive = True
        hom.runFor(300)
        self.assertGreater(sum(u.uniselectorTime for u in hom.homeoUnits), 0)
        deviations = [u.criticalDeviation for u in hom.homeoUnits]
        hom.timeReset()
        self.assertEqual(hom.time, 0)
        self.assertEqual([u.criticalDeviation for u in hom.homeoUnits], deviations)
        for unit in hom.homeoUnits:
            output = unit.currentOutput
            unit.computeOutput()
            self.assertEqual(output, unit.currentOutput, unit.name)
            self.assertEqual(unit.uniselectorTime, 0)
            self.assertEqual(unit.uniselectorActivationCount, 0)


if __name__ == '__main__':
    unittest.main()
