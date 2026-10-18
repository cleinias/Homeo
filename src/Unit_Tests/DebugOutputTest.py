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
The units' debug output (debugMode) and uniselector report
(showUniselectorAction), both GUI toggles, print without crashing on their
format strings.  Each unit kind runs a few ticks with both on.
'''
import contextlib
import io
import unittest

from Core.Homeostat import Homeostat
from Core.HomeoUnit import HomeoUnit
from Core.HomeoUnitAristotelian import HomeoUnitAristotelian
from Core.HomeoUnitNewtonian import HomeoUnitNewtonian


class DebugOutputTest(unittest.TestCase):

    def runWithBothToggles(self, unitClass):
        hom = Homeostat()
        hom.slowingFactor = 0
        units = [unitClass() for i in range(3)]
        for unit in units:
            unit.setRandomValues()
            hom.addFullyConnectedUnit(unit)
            unit.toggleDebugMode()
            unit.toggleShowUniselectorAction()
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            hom.runFor(3)
            units[0].operateUniselector()
        self.assertEqual(hom.time, 3)
        return err.getvalue()

    def testHomeoUnit(self):
        text = self.runWithBothToggles(HomeoUnit)
        self.assertIn('Current Deviat. at time: 0 for unit', text)
        self.assertIn('new position at time: 1 for unit', text)
        self.assertIn('activated uniselector for unit', text)

    def testAristotelianUnit(self):
        text = self.runWithBothToggles(HomeoUnitAristotelian)
        self.assertIn('New position at time: 1 for unit', text)
        self.assertIn('activated uniselector for unit', text)

    def testNewtonianUnit(self):
        text = self.runWithBothToggles(HomeoUnitNewtonian)
        self.assertIn('activated uniselector for unit', text)


if __name__ == '__main__':
    unittest.main()
