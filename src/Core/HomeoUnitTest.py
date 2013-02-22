   
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
        state = 'manual'
        self.unit.addConnection(newUnit, weight, polarity, state)
        self.assertTrue(self.unit.inputConnections is not None)
        self.assertTrue(self.unit.inputConnections.last.incomingUnit == newUnit)
        self.assertTrue(self.unit.inputConnections.last.weight == weight)
        self.assertTrue(self.unit.inputConnections.last.switch == polarity)
        self.assertTrue(self.unit.inputConnections.last.state == 'manual')

    def testClassDefaults(self):
        """test that  the class has its appropriate dictionary of Defaults and that the values are not empty."""
        defParam = HomeoUnit.DefaultParameters  #HomeoUnit class variables with all the defaults values"


        self.assertTrue(defParam.has_key('viscosity'))
        self.assertTrue(defParam.has_key('maxDeviation'))
        self.assertTrue(defParam.has_key('outputRange'))
        self.assertTrue(defParam.has_key('noise'))
        self.assertTrue(defParam.has_key('potentiometer'))
        self.assertTrue(defParam.has_key('time'))
        self.assertTrue(defParam.has_key('uniselectorTimeInterval'))
        self.assertTrue(defParam.has_key('uniselectorTime'))
        self.assertTrue(defParam.has_key('needleCompMethod'))
        self.assertTrue(defParam.has_key('outputRange'))

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

        self.assertTrue(outputRange.has_key('high'))
        self.assertTrue(outputRange['high'] is not None)

        self.assertTrue(outputRange.has_key('low'))
        self.assertTrue(outputRange['low'] is not None)
        
    def  testSaveToFileAndBack(self):
        "test that the unit can be saved to file and recovered"
        self.unit.saveTo('pippo.unit')
        newUnit = HomeoUnit.readFrom('pippo.unit')
        self.assertTrue(isinstance(newUnit, HomeoUnit))
        self.assertTrue(self.unit.sameAs(newUnit))

    def testIsConnectedTo(self):
        newUnit=HomeoUnit()
        weight = 0.5
        polarity = 1

        self.assertFalse(self.unit.isConnectedTo(newUnit))
        self.unit.addConnection(newUnit,weight,polarity,'manual')
        self.assertTrue(self.unit.isConnectedTo(newUnit))
        
    def testRandomizeValues(self):
        self.unit.setRandomValues()
        oldOutput = self.unit.currentOutput
        self.unit.setRandomValues()
        self.assertFalse(oldOutput == self.unit.currentOutput)
            
    def testRemoveConnection(self):
        newUnit = HomeoUnit()
        weight = 0.5
        polarity = 1

        self.unit.addConnection(newUnit,weight,polarity,'manual')
        self.assertTrue(self.unit.isConnectedTo(newUnit))
        self.unit.removeConnectionFromUnit(newUnit)
        self.assertFalse(self.unit.isConnectedTo(newUnit))

    def testIstReadyToGo(self):
        "test the initialization procedure of a HomeoUnit against the conditions set in the isReadyToGo method"
        "A newly created unit must be ready to go"
        newUnit=HomeoUnit() 
        self.assertTrue(newUnit.isReadyToGo())

    def testUnitNameExist(self):
        "Units must have a name"
        self.assertTrue(self.unit.name is not None)

    def testUnitNameUnique(self):
        "Two units cannot have the sane name"
        secondUnit=HomeoUnit()
        self.assertFalse(self.unit.name==secondUnit.name)



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()  