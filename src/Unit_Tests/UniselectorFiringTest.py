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
When a discrete uniselector fires.  Like the relay of Ashby's homeostat it
fires as soon as the essential variable is critical, then at most once every
uniselectorTimeInterval ticks while it stays critical.  It watches every
tick, not one tick per interval: a needle critical on every tick but one
fires, and one that is not critical never does.
'''
from Core.HomeoUnit import HomeoUnit
from Core.HomeoUnitNewtonian import HomeoUnitNewtonian

import unittest
from unittest import mock

INTERVAL = 10
UNIT_CLASSES = (HomeoUnit, HomeoUnitNewtonian)


def _firings(unitClass, critical):
    '''The ticks at which a unit's uniselector fires, when its essential
    variable is critical at the ticks for which critical(t) is true.'''
    HomeoUnit.clearNames()
    unit = unitClass()
    unit.uniselectorActive = True
    unit.uniselectorTimeInterval = INTERVAL
    t = [0]

    def isCritical():
        return critical(t[0])

    fired = []
    with mock.patch.object(unit, 'essentialVariableIsCritical', isCritical), \
            mock.patch.object(unit, 'operateUniselector', lambda: fired.append(t[0])):
        for t[0] in range(5 * INTERVAL):
            unit.selfUpdate()
    return fired


class UniselectorFiringTest(unittest.TestCase):

    def testFiresAsSoonAsCritical(self):
        for unitClass in UNIT_CLASSES:
            with self.subTest(unitClass.__name__):
                self.assertEqual(_firings(unitClass, lambda t: t >= 3)[:1], [3])

    def testWhileCriticalFiresOncePerInterval(self):
        for unitClass in UNIT_CLASSES:
            with self.subTest(unitClass.__name__):
                self.assertEqual(_firings(unitClass, lambda t: True),
                                 [0, INTERVAL, 2 * INTERVAL, 3 * INTERVAL, 4 * INTERVAL])

    def testCriticalExceptOncePerIntervalFires(self):
        for unitClass in UNIT_CLASSES:
            with self.subTest(unitClass.__name__):
                fired = _firings(unitClass, lambda t: (t + 1) % INTERVAL != 0)
                self.assertGreaterEqual(len(fired), 4)

    def testNotCriticalNeverFires(self):
        for unitClass in UNIT_CLASSES:
            with self.subTest(unitClass.__name__):
                self.assertEqual(_firings(unitClass, lambda t: False), [])

    def testAfterACalmSpellFiresAtOnce(self):
        for unitClass in UNIT_CLASSES:
            with self.subTest(unitClass.__name__):
                fired = _firings(unitClass, lambda t: t == 2 or t == 25 or t == 26)
                self.assertEqual(fired, [2, 25])


if __name__ == '__main__':
    unittest.main()
