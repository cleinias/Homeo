'''
Created on Mar 11, 2013

@author: stefano
'''
from   Core.HomeoUnit import *
from   Core.Homeostat import *
import unittest, string, random
from copy import copy

class HomeoConnectionTest(unittest.TestCase):


    def setUp(self):
        """
        Set up a unit connected to itself
        """
        self.unit = HomeoUnit()
        self.unit.setRandomValues()
        self.unit.selfUpdate()              #allows the unit to have some values in its slots"
        self.connection = HomeoConnection()
        self.connection.incomingUnit = self.unit

    def tearDown(self):
        pass


    def testAddConnection(self):
        "Test the unit we setup is properly connected to itself"
        self.assertTrue(self.connection.incomingUnit == self.unit)

    def testDefaults(self):
        "Test default values for a connection "
        self.assertTrue(self.connection.weight >  0 and
                        self.connection.weight < 1)
        self.assertTrue(self.connection.noise > 0 and
                        self.connection.noise < 0.1)
        self.assertTrue(self.connection.switch is not None)
        
    def testSameAs(self):
        "Test if two connections are the same"

        self.unit = HomeoUnit()
        self.unit.setRandomValues()
        unit2 = HomeoUnit()
        unit2.setRandomValues()

        self.connection.randomizeConnectionValues()
        self.connection.incomingUnit = self.unit

        connection2 = copy(self.connection)
        self.assertTrue(self.connection.sameAs(connection2))

        self.connection.incomingUnit = unit2
        self.assertFalse(self.connection.sameAs(connection2))
        
    def testState(self):
        "Test default state of the connection units" 
        self.assertTrue(self.connection.state == 'uniselector') 

        "switching from manual to uniselector and back"
        self.connection.switchToUniselector
        self.assertTrue(self.connection.state == 'uniselector')

        self.connection.switchToManual()
        self.assertTrue(self.connection.state == 'manual')
            
    def testValueOfState(self):
        "Test connections are always in either 'uniselector' or 'manual' state"

        self.assertTrue(self.connection.state == 'manual' or self.connection.state =='uniselector')
            
        self.connection.state = 'manual'
        self.assertTrue(self.connection.state == 'manual' or
                        self.connection.state == 'uniselector')

        self.connection.state = 'uniselector'
        self.assertTrue(self.connection.state == 'manual' or
                        self.connection.state == 'uniselector')

        for testTry in xrange(10):
            randomString = ''.join(random.choice(string.ascii_lowercase) for x in range(10))
            self.assertRaises(Exception, self.connection.state, randomString) 
                
    def testWeight(self):
        """"Test basic algorithm of a connection.
        Output is equal to the originating unit's output * weight * switch - noise 
        We don't test for the influence of noise, as it is a normally distributed value around
        connection.noise and therefore difficult to test reliably. We trust the noise tests carried
        out in HomeNoiseTests 
        
        """
        errorTolerance = pow(10,-7)
        inputUnit = self.connection.incomingUnit
        tests = 100
        
        for i in xrange(tests):
            self.connection.noise = 0                  # eliminate noise"
            outputWeighed = self.connection.output()
            self.assertTrue(abs(outputWeighed - 
                                ((inputUnit.currentOutput * self.connection.weight * self.connection.switch) - self.connection.noise)) 
                                < errorTolerance)
            inputUnit.selfUpdate()
            
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()