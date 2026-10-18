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

from  Core.HomeoNeedleUnit import *
import unittest


class HomeoNeedleUnitTest(unittest.TestCase):
    '''
    Unit tests for the HomeoNeedleUnit class, which simply holds
    the parameters needed to compute the movement of the needle
    in a HomeoUnit 
    '''


    def setUp(self):
        pass

    def testClassDefaults(self):
        """test that  the class has its appropriate dictionary of Defaults and that the values are not empty."""
        defParam = HomeoNeedleUnit.DefaultParameters  #HomeoUnit class variables with all the defaults values"


        self.assertTrue('mass' in defParam)
        self.assertTrue('surfaceArea' in defParam)
        self.assertTrue('dragCoefficient' in defParam)

        self.assertTrue(defParam['mass'] is not None)
        self.assertTrue(defParam['surfaceArea'] is not None)
        self.assertTrue(defParam['dragCoefficient'] is not None)
        
    
    def testNeedleUnitInstanceHasDefaultValues(self):
        '''
        Test that a HomeoNeedleUnit has values accessible with implicit getters and setters
        '''
        
        needleUnit = HomeoNeedleUnit()
        
        needleUnit.mass = 10
        needleUnit.dragCoefficient = 100
        needleUnit.surfaceArea = 10
        
        self.assertTrue(needleUnit.mass == 10)
        self.assertTrue(needleUnit.surfaceArea == 10)
        self.assertTrue(needleUnit.dragCoefficient == 100)
        
    def tearDown(self):
        pass




if __name__ == "__main__":
    unittest.main()