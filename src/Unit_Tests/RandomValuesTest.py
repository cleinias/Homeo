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
