# Copyright (C) 2013-2026 Stefano Franchi
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
The Aristotelian unit: the needle's velocity, not its acceleration, follows
the force, and the medium's viscosity takes away a fraction of the force.
'''
from   Core.HomeoUnit import *
from   Core.HomeoUnitAristotelian import HomeoUnitAristotelian

import unittest, numpy


class HomeoUnitAristotelianTest(unittest.TestCase):


    def setUp(self):
        numpy.random.seed(5)
        self.unit = HomeoUnitAristotelian()
        self.unit.setRandomValues()
        self.unit.needleCompMethod = 'linear'
        self.maxViscosity = HomeoUnit.DefaultParameters['maxViscosity']


    def tearDown(self):
        pass

    def testDragIsTheViscousFractionOfTheForce(self):
        for viscosity in (0, 0.3 * self.maxViscosity, self.maxViscosity):
            self.unit.viscosity = viscosity
            for force in (-2.0, 0.0, 0.7):
                self.assertAlmostEqual(self.unit.dragOn(force),
                                       -force * viscosity / self.maxViscosity)

    def testVelocityIsTheNetForceOverTheMass(self):
        '''x(t+1) = x(t) + F (1 - viscosity / maxViscosity) / mass'''
        self.unit.criticalDeviation = 1.5
        self.unit.viscosity = 0.25 * self.maxViscosity
        mass = self.unit.needleUnit.mass
        for torque in (-3.0, 0.0, 0.4):
            self.assertAlmostEqual(self.unit.newNeedlePosition(torque),
                                   1.5 + torque * 0.75 / mass)

    def testNoForceNoMotion(self):
        '''With no force the needle stays where it is, however hard it was
        pushed before: an Aristotelian needle has no momentum.'''
        self.unit.criticalDeviation = self.unit.newNeedlePosition(5.0)
        position = self.unit.criticalDeviation
        self.assertEqual(self.unit.newNeedlePosition(0.0), position)

    def testFullViscosityStopsTheNeedle(self):
        self.unit.viscosity = self.maxViscosity
        self.unit.criticalDeviation = -0.8
        self.assertAlmostEqual(self.unit.newNeedlePosition(10.0), -0.8)

    def testSameStepAsAshbysUnit(self):
        '''The plain HomeoUnit's linear step is the same model: viscosity as
        a fraction of the force, velocity = force / mass.'''
        other = HomeoUnit()
        other.needleCompMethod = 'linear'
        other.viscosity = self.unit.viscosity
        other.needleUnit.mass = self.unit.needleUnit.mass
        other.criticalDeviation = self.unit.criticalDeviation = 0.3
        for torque in (-1.0, 0.25, 2.0):
            self.assertAlmostEqual(self.unit.newNeedlePosition(torque),
                                   other.newNeedlePosition(torque))


if __name__ == "__main__":
    unittest.main()
