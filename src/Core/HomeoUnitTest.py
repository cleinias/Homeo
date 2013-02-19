   
from   HomeoUnit import *
import HomeoConnection
import unittest

class HomeoUnitTest(unittest.TestCase):
    """Unit testing for the HomeoUnit class and subclasses, including adding and removing connections to other HomeoUnits."""
    
    def setUp(self):
        """Set up a Homeounit for all tests in the suite"""
        self.unit = HomeoUnit()
        
    def tearDown(self):
        pass
    
        
    def test_AddConnection(self):
        """Connect to another unit and test the connection values."""
        newUnit = HomeoUnit()
        weight = 0.5
        polarity = 1
        self.unit.addConnection(newUnit, weight, polarity)
        self.assertTrue(self.unit.inputConnections is not None)
        self.assertTrue(self.unit.inputConnections.last.incomingUnit == newUnit)
        self.assertTrue(self.unit.inputConnections.last.weight == weight)
        self.assertTrue(self.unit.inputConnections.last.switch == polarity)
        self.assertTrue(self.unit.inputConnections.last.state == 'manual')

    def testClassDefaults(self):
        "test that  the class has its appropriate dictionary of Defaults and that the values are not empty"
        defParam = HomeoUnit.defaultParameters  #HomeoUnit class variables with all the defaults values"


        self.assertTrue(defParam.haskey('viscosity'))
        self.assertTrue(defParam.haskey('maxDeviation'))
        self.assertTrue(defParam.haskey('outputRange'))
        self.assertTrue(defParam.haskey('noise'))
        self.assertTrue(defParam.haskey('potentiometer'))
        self.assertTrue(defParam.haskey('time'))
        self.assertTrue(defParam.haskey('uniselectorTimeInterval'))
        self.assertTrue(defParam.haskey('uniselectorTime'))
        self.assertTrue(defParam.haskey('needleCompMethod'))
        self.assertTrue(defParam.haskey('outputRange'))

        self.assertTrue(defParam['viscosity'] is not None)
        self.assertTrue(defParam['maxDeviation'] is not None)
        self.assertTrue(defParam['noise'] is not None)
        self.assertTrue(defParam['potentiometer'] is not None)
        self.assertTrue(defParam['time'] is not None)
        self.assertTrue(defParam['uniselectorTimeInterval'] is not None)
        self.assertTrue(defParam['uniselectorTime'] is not None)
        self.assertTrue(defParam['needleCompMethod']  is not None)
        self.assertTrue(defParam['outputRange'] is not None)

        outputRange = defParam['outputRange']

        self.assertTrue(outputRange.haskey('high'))
        self.assertTrue(outputRange['high'] is not None)

        self.assertTrue(outputRange.haskey('low'))
        self.assertTrue(outputRange['low'] is not None)

 

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()  