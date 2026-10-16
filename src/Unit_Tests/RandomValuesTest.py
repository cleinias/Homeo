'''
@author: stefano

The random start of a unit, setRandomValues.  The needle's deviation is
drawn over the unit's whole range, +/-maxDeviation, not the output range,
and the output is the one that deviation gives: on the first tick every unit
feeds the others the output of its own needle.
'''
from Core.HomeoUnit import HomeoUnit
from Core.HomeoUnitNewtonian import HomeoUnitNewtonian

import unittest

import numpy as np


class RandomValuesTest(unittest.TestCase):

    def setUp(self):
        np.random.seed(6)
        HomeoUnit.clearNames()

    def _draws(self, unitClass, n=500, maxDeviation=None):
        units = []
        for _ in range(n):
            u = unitClass()
            if maxDeviation is not None:
                u.maxDeviation = maxDeviation
            u.setRandomValues()
            units.append(u)
        return units

    def testDeviationsCoverTheWholeRange(self):
        for unitClass in (HomeoUnit, HomeoUnitNewtonian):
            for maxDeviation in (None, 4.0, 25.0):
                with self.subTest(unitClass=unitClass.__name__, maxDeviation=maxDeviation):
                    units = self._draws(unitClass, maxDeviation=maxDeviation)
                    top = units[0].maxDeviation
                    deviations = np.array([u.criticalDeviation for u in units])
                    self.assertTrue(np.all(np.abs(deviations) <= top))
                    self.assertGreater(deviations.max(), 0.9 * top)
                    self.assertLess(deviations.min(), -0.9 * top)

    def testTheOutputIsTheDeviations(self):
        for unitClass in (HomeoUnit, HomeoUnitNewtonian):
            with self.subTest(unitClass=unitClass.__name__):
                for u in self._draws(unitClass, n=100):
                    drawn = u.currentOutput
                    u.computeOutput()
                    self.assertEqual(drawn, u.currentOutput)


if __name__ == '__main__':
    unittest.main()
