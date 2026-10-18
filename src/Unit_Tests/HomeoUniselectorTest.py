# Copyright (C) 2006-2026 Stefano Franchi
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
'''
from   Core.HomeoUniselector import *
from   Helpers.General_Helper_Functions import *

import unittest, string, random


class HomeoUniselectorTest(unittest.TestCase):


    def setUp(self):
        self.uniselector = HomeoUniselector()

    def tearDown(self):
        pass

    def testHomeoUniselectorClassType(self):
        """
        Test that HomeoUniselector knows its types include only itself and its subclasses 
        """
        currentClasses = []
        bogusClasses = []
        currentClasses.extend([class_.__name__ for class_ in withAllSubclasses(HomeoUniselector)])
        for bogusClass in range(5):
            newRandomName = ''.join(random.choice(string.ascii_lowercase) for x in range(10))
            bogusClasses.append(newRandomName)
        for currentClass in currentClasses:
            self.assertTrue(HomeoUniselector.includesType(currentClass))
        self.assertEqual(len(bogusClasses), 5)
        for bogusClass in bogusClasses:
            self.assertFalse(HomeoUniselector.includesType(bogusClass))

    def testIntervalBounds(self):
        """
        A HomeoUniselector's weights default to the interval [0, 1], and its
        bounds can be set (Ashby's uniselector keeps them at -1 and 1: see
        HomeoUniselectorAshbyTest.testIntervalBounds)
        """
        self.assertEqual((self.uniselector.lowerBound, self.uniselector.upperBound), (0, 1))
        self.uniselector.lowerBound = -0.5
        self.uniselector.upperBound = 2
        self.assertEqual((self.uniselector.lowerBound, self.uniselector.upperBound), (-0.5, 2))
                        
    def testHomeoUniselectorIsAbstractClass(self):
        '''
        The core method of HomeUniselector is advance, which is only defined in its subclasses
        '''
        self.assertRaises(SubclassResponsibility, self.uniselector.advance)
        
if __name__ == "__main__":
    unittest.main()