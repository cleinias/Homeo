'''
Created on Mar 11, 2013

@author: stefano
'''
from   HomeoUnit import *
from   HomeoUniselectorUniformRandom import *
from   Homeostat import *
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
            self.uniselector.restoreDefaults()
            self.assertTrue(self.uniselector.lowerBound == -1 and
                            self.uniselector.upperBound == 1)

    def testIntervalBounds(self):
        """
        "Interval bounds are always centered around 0, 
        i.e. lowerbounds always = to upperBound negated"
        """
        for i in xrange(100):
            self.uniselector.lowerBound(numpy.random.uniform(-10, 10))
            self.assertTrue(self.uniselector.lowerBound() == - self.uniselector.upperBound())
            self.uniselector.upperBound(numpy.random.uniform(-10, 10))
            self.assertTrue(self.uniselector.lowerBound() == - self.uniselector.upperBound())

    def testProduceNewValue(self):
        """
        Test that new produced values are always different
        """
        tests = 1000
    
        "testing with default interval bounds: No repeated values"
        values = []
        for test in xrange(tests):
            newValue = self.uniselector.produceNewValue()
            values.append(newValue)
        self.assertTrue(len(set(values))  == tests)    


        "testing with random values for interval: No repeated values"
        values = []
        for i in xrange(10): 
            self.uniselector.upperBound(numpy.random.uniform(-10, 10))
            for test in xrange(tests): 
                newValue = self.uniselector.produceNewValue()
                values.append(newValue)
                self.assertTrue(len(set(values)) == tests)    
                    
    def testValueWithinIntervalBounds(self):
        """
        New produced valued must always be within the uniselector's bounds
        """
        tests = 1000
        values = []

        for test in xrange(tests):
            values.append(self.uniselector.produceNewValue())

        self.assertTrue(max(values)  <= self.uniselector.upperBound())
        self.assertTrue(min(values) >= self.uniselector.lowerBound())                    
  
    def tearDown(self):
        pass


  

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()