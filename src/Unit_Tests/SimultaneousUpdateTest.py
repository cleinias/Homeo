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
The units of a homeostat advance together: within a tick every unit reads
the outputs the others had at the start of the tick.  Were units to update
one after another, each committing its output at once, a unit would read this
tick's output from the units before it in homeoUnits and last tick's from
those after it: results would depend on the order of the units, and two
identical, symmetric units would drift apart.
'''
from Core.Homeostat import Homeostat
from Core.HomeoUnit import HomeoUnit
from Core.HomeoUnitNewtonian import HomeoUnitNewtonian

import unittest

UNIT_CLASSES = (HomeoUnitNewtonian, HomeoUnit)


def _homeostat(unitClass, deviations, weights, order, headless):
    '''A noiseless homeostat without uniselectors.  deviations: the units'
    initial deviations, by name; weights[(a, b)]: the weight from unit a into
    unit b; order: the order in which the units are added.'''
    HomeoUnit.clearNames()
    units = {}
    for name in deviations:
        u = unitClass()
        u.name = name
        u.noise = 0
        u.uniselectorActive = False
        u.maxDeviation = 10
        units[name] = u
    hom = Homeostat()
    for name in order:
        hom.addFullyConnectedUnit(units[name])
    hom.slowingFactor = 0
    hom.collectsData = False
    hom._headless = headless
    for u in hom.homeoUnits:
        u._headless = headless
        u.criticalDeviation = deviations[u.name]
        u.computeOutput()
        for c in u.inputConnections:
            c.newWeight(weights[(c.incomingUnit.name, u.name)])
            c.noise = 0
            c.state = 'manual'
            c.status = True
    return hom


def _deviations(hom):
    return {u.name: u.criticalDeviation for u in hom.homeoUnits}


class SimultaneousUpdateTest(unittest.TestCase):

    def testSymmetricUnitsStayIdentical(self):
        deviations = {'A': 3.0, 'B': 3.0}
        weights = {('A', 'A'): -0.5, ('B', 'B'): -0.5,
                   ('A', 'B'): 0.8, ('B', 'A'): 0.8}
        for unitClass in UNIT_CLASSES:
            for headless in (False, True):
                with self.subTest(unitClass=unitClass.__name__, headless=headless):
                    hom = _homeostat(unitClass, deviations, weights, 'AB', headless)
                    for _ in range(20):
                        hom.runOnce()
                        d = _deviations(hom)
                        self.assertEqual(d['A'], d['B'], hom.time)
                    self.assertNotEqual(d['A'], 3.0)

    def testResultsDoNotDependOnTheUnitsOrder(self):
        deviations = {'A': 4.0, 'B': -2.0, 'C': 1.0, 'D': -6.0}
        values = [-0.6, 0.3, -0.4, 0.2, 0.3, -0.5, 0.2, -0.3,
                  0.4, -0.3, -0.7, 0.2, -0.2, 0.1, -0.3, -0.6]
        names = sorted(deviations)
        weights = {(a, b): values[4 * i + j]
                   for i, a in enumerate(names) for j, b in enumerate(names)}
        for unitClass in UNIT_CLASSES:
            for headless in (False, True):
                with self.subTest(unitClass=unitClass.__name__, headless=headless):
                    finals = []
                    for order in ('ABCD', 'DCBA', 'CADB'):
                        hom = _homeostat(unitClass, deviations, weights, order, headless)
                        hom.runFor(200)
                        finals.append(_deviations(hom))
                    # the same up to rounding: each unit sums its inputs in
                    # the order the units were added
                    for final in finals[1:]:
                        for name in names:
                            self.assertAlmostEqual(final[name], finals[0][name],
                                                   places=9, msg=name)

    def testEachUnitReadsTheOutputsOfTheTickBefore(self):
        # B reads only A, which moves under its self-connection: B's torque
        # is A's output at the start of the tick, not A's new one
        deviations = {'A': 5.0, 'B': 0.0}
        weights = {('A', 'A'): -0.5, ('B', 'B'): 0.0,
                   ('A', 'B'): 1.0, ('B', 'A'): 0.0}
        for headless in (False, True):
            with self.subTest(headless=headless):
                hom = _homeostat(HomeoUnit, deviations, weights, 'AB', headless)
                a, b = hom.homeoUnits
                start = a.currentOutput
                hom.runOnce()
                self.assertNotEqual(a.currentOutput, start)
                self.assertEqual(b.inputTorque, start)

    def testOutsideATickUnitsReadTheLiveOutputs(self):
        hom = _homeostat(HomeoUnit, {'A': 5.0, 'B': 0.0},
                         {('A', 'A'): 0.0, ('B', 'B'): 0.0,
                          ('A', 'B'): 1.0, ('B', 'A'): 0.0}, 'AB', False)
        hom.runOnce()
        a, b = hom.homeoUnits
        conn = [c for c in b.inputConnections if c.incomingUnit is a][0]
        a.currentOutput = 0.25
        self.assertEqual(conn.output(), 0.25)


if __name__ == '__main__':
    unittest.main()
