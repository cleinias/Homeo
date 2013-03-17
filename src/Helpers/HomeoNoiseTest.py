'''
Created on Mar 15, 2013

@author: stefano
'''
from   Core.HomeoUnit import HomeoUnit
from   HomeoUniselector import *
from   HomeoDataCollector import *
from   Homeostat import *
from   HomeoNoise import  *
from   Helpers.General_Helper_Functions import *

import unittest,numpy



class HomeoNoiseTest(unittest.TestCase):
    """
    Testing the application of noise to the HomeUnit and HomeConnections
    """

    def setUp(self):
        "Set up the test with a Homeostat unit and a noise object"

        self.unit = HomeoUnit()
        self.noise = HomeoNoise()

    def testDegradingConstantLinearNoise(self):
        """
        Degrading constant linear noise must
        - always have the same value (constant)
        - the value is equal to the unit's noise (linear)
        - always have opposite sign to the signal (unit's critical deviation) (degrading)
        """

        values = []
        self.unit.setRandomValues()
        tests = 100
        self.noise = HomeoNoise.newWithCurrentandNoise(self.unit.criticalDeviation(), self.unit.noise())

        self.noise.constant() 
        self.noise.degrading() 
        self.noise.linear()

        for i in xrange(tests):
            values.append(self.noise.getNoise())
        values = sorted(values)
        "As noise is constant, sort produced noises and check only first and last are equal to unit's noise"
        self.assertTrue(len(values) == tests)
        self.assertTrue(numpy.sign(values[0]) == (numpy.sign(self.unit.criticalDeviation() * -1)))    # Noise is degrading the signal: opposite sign
        self.assertTrue(abs(values[0]) == self.unit.noise())
        self.assertTrue(abs(values[tests-1]) == (self.unit.noise()))


    def testDegradingConstantProportionalNoise(self):
        """
        Degrading constant proportional noise must
        - always have the same value (constant)
        - the value is equal to the unit's value times its noise (proportional)
        - always have opposite sign to the signal (unit's critical deviation) (degrading)
        """
       
        values = []
        self.unit.setRandomValues()
        tests = 100
        self.noise = HomeoNoise.newWithCurrentandNoise(self.unit.criticalDeviation(), self.unit.noise())

        self.noise.constant() 
        self.noise.degrading() 
        self.noise.proportional()

        for i in xrange(tests):
            values.append(self.noise.getNoise())
        values = sorted(values)


        self.assertTrue(len(values) == tests)
        self.assertTrue(numpy.sign(values[0]) == (numpy.sign(self.unit.criticalDeviation() * -1)))    # Noise is degrading the signal: opposite sign
        self assert:    ((values first abs) = ((unit noise)*unit criticalDeviation abs)).
        self assert:    ((values last abs) = ((unit noise)*unit criticalDeviation abs)).</body>


    def tearDown(self):
        pass


    def testName(self):
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()