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

from   Core.HomeoUniselectorUniformRandom import *
import unittest, numpy


class HomeoUniselectorUniformRandomTest(unittest.TestCase):
    """
    Test basic functioning of HomeoUniselectorUniformRandomTest:
       - values produced are always within bounds
       - values produced are always different
    """
    def setUp(self):
        self.uniselector = HomeoUniselectorUniformRandom()

    def testDefaultIntervalBounds(self):
        """
        Test uniselector's default values
        """
        self.assertTrue(self.uniselector.lowerBound == -1 and
                        self.uniselector.upperBound == 1)

    def testIntervalBounds(self):
        """
        "Interval bounds are always centered around 0, 
        i.e. lowerBound always = to upperBound negated"
        """
        for i in range(100):
            self.uniselector.lowerBound = numpy.random.uniform(-10, 10)
            self.assertTrue(self.uniselector.lowerBound == - self.uniselector.upperBound)
            self.uniselector.upperBound = numpy.random.uniform(-10, 10)
            self.assertTrue(self.uniselector.lowerBound == - self.uniselector.upperBound)

    def testProduceNewValue(self):
        """
        Test that new produced values are always different
        """
        tests = 1000
    
        "testing with default interval bounds: No repeated values"
        values = []
        for test in range(tests):
            newValue = self.uniselector.produceNewValue()
            values.append(newValue)
        self.assertTrue(len(set(values))  == tests)    


        "testing with random values for interval: No repeated values"
        for i in range(10):
            values = []
            self.uniselector.upperBound = numpy.random.uniform(-10, 10)
            for test in range(tests): 
                newValue = self.uniselector.produceNewValue()
                values.append(newValue)
            self.assertTrue(len(set(values)) == tests)    
                    
    def testValueWithinIntervalBounds(self):
        """
        New produced valued must always be within the uniselector's bounds
        """
        tests = 1000
        values = []

        for test in range(tests):
            values.append(self.uniselector.produceNewValue())

        self.assertTrue(max(values)  <= self.uniselector.upperBound)
        self.assertTrue(min(values) >= self.uniselector.lowerBound)             
        
    def testDefaultInterval(self):
        """
        Default interval is (-1, 1)
        """
        self.assertTrue(self.uniselector.lowerBound == -1 and
                        self.uniselector.upperBound == 1)       
  
    def tearDown(self):
        pass


  

if __name__ == "__main__":
    unittest.main()