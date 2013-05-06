'''
Created on May 3, 2013

@author: stefano
'''

from   Core.HomeoUnit import *
from   Core.HomeoUniselectorUniformRandom import *
from   Core.Homeostat import *
from   Simulator.HomeoQtSimulation import *
import unittest, numpy, os, sys
from time import sleep
from  Helpers.SimulationThread import SimulationThread

class HomeoQtSimulationTest(unittest.TestCase):
    """
    Tests for the Homeostat QtSimulation class
    """

    def setUp(self):
        self.simulation = HomeoQtSimulation()
        self.thr = SimulationThread()

    def testAddUnit(self):
        """
        Add a few units and check that the Homeostat is holding on to them
        """

        self.simulation = HomeoQtSimulation()
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
        self.simulation = HomeoQtSimulation()

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
        self.simulation = HomeoQtSimulation()
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
        self.simulation = HomeoQtSimulation()
        
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
        self.simulation = HomeoQtSimulation()
        self.thr = SimulationThread()

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
        self.simulation = HomeoQtSimulation()
        self.thr = SimulationThread()

        for unit in xrange(4):
            self.simulation.homeostat.addFullyConnectedUnit(HomeoUnit())
            
        simulationCycles = 30
        self.simulation.maxRuns = simulationCycles

        "runs for the default number of cycles"
        self.simulation.moveToThread(self.thr)
        self.thr.started.connect(self.simulation.go)
        self.thr.start()

        self.assertTrue(simulationCycles == self.simulation.homeostat.time)

    def testPause(self):
        """
        Start a simulation in a thread and pause it: 
        test that it has not run its maximum number of cycles
        """
        
        "Create a 4-unit full connected homeostat"
        self.simulation = HomeoQtSimulation()

        for unit in xrange(4):
            self.simulation.homeostat.addFullyConnectedUnit(HomeoUnit())
            
        simulationCycles = 100
        self.simulation.maxRuns = simulationCycles

        
        self.simulation.moveToThread(self.thr)
        self.thr.start()
        
        "wait half a second"
        sleep(0.5)
        
        self.simulation.pause()
        self.assertFalse(simulationCycles == self.simulation.homeostat.time)
        
    def testDataFileIsPresent(self):
        """
        A simulation must always have a data file
        """

        self.assertTrue(self.simulation.dataFilename is not None)
 
    def testDataFile(self):
        """
        Test that either the data file exists and it is writable or the data file does not exist  yet
        """
        
        "Note that os.access wants a path, not just a filename"
        self.assertTrue(os.access(self.simulation.dataFilename,os.W_OK) or
                        not os.access(self.simulation.dataFilename, os.F_OK))           
        
    def testReadConditionsFromFile(self):
        """
        Test  if  a simulation can be loaded from a pickled homeostat file.
        Create a simulation, run it and save it to file first.
        """

        "Create a fully connected 2-unit homeostat and randomize its values"
        self.simulation = HomeoQtSimulation()
        unit1 = HomeoUnit()
        unit2 = HomeoUnit()
        self.simulation.homeostat.addFullyConnectedUnit(unit1)    
        self.simulation.homeostat.addFullyConnectedUnit(unit2)    
        self.simulation.homeostat.randomizeValuesforAllUnits()
        
        "run the simulation for a few cycles"       
        self.simulation.maxRuns = 100
        self.simulation.go()
        
        "if a file exist on disk erase it."
        if os.access(self.simulation.homeostatFilename, os.F_OK):
            os.remove(self.simulation.homeostatFilename)
        
        "save the simulation"
        self.simulation.save()

        "create a new Simulation from the saved file"
        newSimul = HomeoQtSimulation.readFrom(self.simulation.homeostatFilename)
        
        "test the simulation is ready to go"
        self.assertTrue(newSimul.isReadyToGo())
        
        "clean up after yourself"
        os.remove(self.simulation.homeostatFilename)
        
        
    def testSaveToFile(self):
        """
        Test if the simulation can be saved to a pickled file
        """

        "Create a fully connected 2-unit homeostat and randomize its values"
        self.simulation = HomeoQtSimulation()
        unit1 = HomeoUnit()
        unit2 = HomeoUnit()
        self.simulation.homeostat.addFullyConnectedUnit(unit1)    
        self.simulation.homeostat.addFullyConnectedUnit(unit2)    
        self.simulation.homeostat.randomizeValuesforAllUnits()
        
        "run the simulation for a few cycles"       
        self.simulation.maxRuns = 100
        self.simulation.go()
        
        "if a file exist on disk erase it."
        if os.access(self.simulation.homeostatFilename, os.F_OK):
            os.remove(self.simulation.homeostatFilename)
        
        "save the simulation"
        self.simulation.save()
        
        "check the pickled file exists on disk"
        self.assertTrue(os.access(self.simulation.homeostatFilename, os.F_OK))
        
        "clean up after yourself"
        os.remove(self.simulation.homeostatFilename)
        
            
    def tearDown(self):
        pass




if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()