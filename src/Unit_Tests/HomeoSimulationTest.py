'''
Created on Mar 19, 2013

@author: stefano
'''
from   Core.HomeoUnit import *
from   Core.HomeoUniselectorUniformRandom import *
from   Core.Homeostat import *
from   Simulator.HomeoSimulation import *
import unittest, numpy, os, sys
from time import sleep
from  threading import Thread

class HomeoSimulationTest(unittest.TestCase):
    """
    Tests for the Homeostat simulation class
    """

    def setUp(self):
        self.simulation = HomeoSimulation()

    def testAddUnit(self):
        """
        Add a few units and check that the Homeostat is holding on to them
        """

        self.simulation = HomeoSimulation()
        unitsAdded = 5
        self.simulation.addUnit(HomeoUnit())
        self.assertTrue(len(self.simulation.homeostat.homeoUnits) == 1)
        for unit in xrange(unitsAdded):
            self.simulation.addUnit(HomeoUnit())
        self.assertTrue(len(self.simulation.homeostat.homeoUnits) == (1 + unitsAdded))

    def testAddFullyConnectedUnit(self):
        """
        Test that an added fully connected unit is actually fully connected 
        """
        self.simulation = HomeoSimulation()

        unitsAdded = 5
        self.simulation.addFullyConnectedUnit(HomeoUnit())
        self.assertTrue(len(self.simulation.homeostat.homeoUnits) == 1)
        self.assertTrue(len(self.simulation.homeostat.homeoUnits[0].inputConnections) == 1)
        for unit in xrange(unitsAdded):
            self.simulation.addFullyConnectedUnit(HomeoUnit())
        for unit in self.simulation.homeostat.homeoUnits: 
            self.assertTrue(len(unit.inputConnections) == (1+ unitsAdded))

    def testRemoveUnit(self):
        """
        Test removing a few units and check that the Homeostat is holding the correct number of units
        """
        self.simulation = HomeoSimulation()
        homeoUnit = HomeoUnit() 
        unitsAdded = 3
        self.simulation.addUnit(homeoUnit)
        self.assertTrue(len(self.simulation.homeostat.homeoUnits)  == 1)
        for i in xrange(unitsAdded):
            self.simulation.addUnit(HomeoUnit())
        self.assertTrue(len(self.simulation.homeostat.homeoUnits) == (1 + unitsAdded))

        self.simulation.homeostat.removeUnit(homeoUnit)
        self.assertTrue(len(self.simulation.homeostat.homeoUnits) == unitsAdded)
        
        for unit in self.simulation.homeostat.homeoUnits[:]:                    # iterating over a copy of the list
            self.simulation.homeostat.removeUnit(unit)
        self.assertTrue(len(self.simulation.homeostat.homeoUnits) == 0)
    
    def testAddConnection(self):
        """
        Test adding a connection between two units in the simulation
        """
        self.simulation = HomeoSimulation()
        
        unit1 = HomeoUnit()
        unit2 = HomeoUnit()

        "create a  2-unit homeostat"
        self.simulation.homeostat.addUnit(unit1)    
        self.simulation.homeostat.addUnit(unit2)    
        for index in xrange(2):
            "all units are self-connected and self-connected only"
            self.assertTrue(len(self.simulation.homeostat.homeoUnits[index].inputConnections) == 1)   

        "add a connection from the second unit to first one"
        self.simulation.homeostat.addConnectionWithRandomValuesFromUnit1toUnit2(unit2, unit1)
        
        "check that the first unit has now two connections"
        self.assertTrue(len(self.simulation.homeostat.homeoUnits[0].inputConnections) == 2)     
        self.assertTrue(len(unit1.inputConnections) == 2)

    def testRemoveConnection(self):
        """
        Test removing a connection between two units in the simulation
        """
        self.simulation = HomeoSimulation()

        unit1 = HomeoUnit()
        unit2 = HomeoUnit()

        "create a  2-unit homeostat"
        self.simulation.homeostat.addUnit(unit1)    
        self.simulation.homeostat.addUnit(unit2)    
        for index in xrange(2):
            "all units are self-connected and self-connected only"
            self.assertTrue(len(self.simulation.homeostat.homeoUnits[index].inputConnections) == 1)   

        "add a connection from the second unit to first one"
        self.simulation.homeostat.addConnectionWithRandomValuesFromUnit1toUnit2(unit2, unit1)

        "check that the first unit has now two connections"
        self.assertTrue(len(self.simulation.homeostat.homeoUnits[0].inputConnections) == 2)     
        self.assertTrue(len(unit1.inputConnections) == 2)

        "remove the connection from the second unit to the first one"
        self.simulation.homeostat.removeConnectionFromUnit1ToUnit2(unit2, unit1)

        "check  number of connections for unit1 is back to 1 (self-connection)"
        self.assertTrue(len(self.simulation.homeostat.homeoUnits[0].inputConnections) == 1)     
        self.assertTrue(len(unit1.inputConnections)== 1)

    def testStart(self):
        """
        Test that the simulation runs for the stated number of cycles
        """
        
        "Create a 4-unit full connected homeostat"
        self.simulation = HomeoSimulation()

        for unit in xrange(4):
            self.simulation.homeostat.addFullyConnectedUnit(HomeoUnit())
            
        simulationCycles = 30
        self.simulation.maxRuns = simulationCycles

        "runs for the default number of cycles"
        self.simulation.start()  

        self.assertTrue(simulationCycles == self.simulation.homeostat.time)

    def testStop(self):
        """
        Start a simulation and stop it: test that it has not run its maximum nyumber of cycles
        """
        
        "Create a 4-unit full connected homeostat"
        self.simulation = HomeoSimulation()

        for unit in xrange(4):
            self.simulation.homeostat.addFullyConnectedUnit(HomeoUnit())
            
        simulationCycles = 1000
        self.simulation.maxRuns = simulationCycles

        thr = Thread(target=self.simulation.start, name = 'simulationInAThread')
        thr.start()
        "wait one second"
        sleep(1)
        
        self.simulation.stop()
        self.assertFalse(simulationCycles == self.simulation.homeostat.time)
        
        def testDataFileIsPresent():
            """
            A simulation must always have a data file
            """

            self.assertTrue(self.simulation.datafile() is not None)
 
        def testDataFile():
            """
            Test that either the data file exists and it is writable or it does not exist yet
            """
            
            "Note that os.access wants a path, not just a filename"
            self.assertTrue(os.access(self.simulation.datafile(),os.W_OK) or
                            self.simulation.datafile is None)           
            
        def testReadConditionsFromFile(self):
            """
            FIXME: This  checks whether a simulation can be restarted from file
            """
            self.assertTrue(False)
            
            
        def testSaveToFile(self):
            """
            FIXME: This test checks if the simulation can be saved to file
            """
            self.assertTrue(False)
            
            
    def tearDown(self):
        pass




if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()