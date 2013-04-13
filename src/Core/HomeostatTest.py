'''
Created on Mar 11, 2013

@author: stefano
'''
from   HomeoUnit import *
from   HomeoUniselector import *
from   Homeostat import *
from   Helpers.General_Helper_Functions import *

import unittest, pickle, os, time
from copy import copy, deepcopy
from threading import Thread

class HomeostatTest(unittest.TestCase):


    def setUp(self):
        self.homeostat = Homeostat()
        "set up a 4 units fully connected Homeostat"
        unit1 = HomeoUnit()
        unit2 = HomeoUnit()
        unit3 = HomeoUnit()
        unit4 = HomeoUnit()
        self.homeostat.addFullyConnectedUnit(unit1)
        self.homeostat.addFullyConnectedUnit(unit2)
        self.homeostat.addFullyConnectedUnit(unit3)
        self.homeostat.addFullyConnectedUnit(unit4)
        
        '''temporary testing:
           set collectsData to False to avoid generating errors
           from unfinished dataCollector class'''
#        self.homeostat.collectsData = False


    def testStartAndStop(self):
        '''As the start method runs an infinite loop, it must be run
           in a separate thread. That will allow setting the ivar isRunning to False
           thereby stopping the homeostat'''
        

        self.assertTrue(self.homeostat.isReadyToGo)

        thr = Thread(target=self.homeostat.start, name = 'homeostatInAThread')
        thr.start()
     
        self.assertTrue(self.homeostat.isRunning == True)
        time.sleep(1)
        self.homeostat.stop()
        self.assertTrue(self.homeostat.isRunning == False)
        
    def testAddFullyConnectedUnits(self):
        """
        
        """
        unit1 = HomeoUnit()
        unit2 = HomeoUnit()
        unit3 = HomeoUnit()
        coll1 = [unit1, unit2, unit3]
        coll2 = copy(coll1)
        self.homeostat.addFullyConnectedUnit(unit1)
        self.homeostat.addFullyConnectedUnit(unit2)
        self.homeostat.addFullyConnectedUnit(unit3)
        self.assertTrue(self.homeostat.hasUnit(unit1))
        self.assertTrue(self.homeostat.hasUnit(unit2))
        self.assertTrue(self.homeostat.hasUnit(unit3))
        for fromUnit in coll1:
            for toUnit in coll2:  
                    self.assertTrue(self.homeostat.isConnectedFromTo(fromUnit,toUnit))

    def testAddUnit(self):
        """
        Test adding new and existing units
        """
        unit1 = HomeoUnit()
        "test adding a new unit"
        self.homeostat.addUnit(unit1)
        self.assertTrue(self.homeostat.hasUnit(unit1))

        "test adding an already existing unit"
        existingUnits = len(self.homeostat.homeoUnits)
        self.homeostat.addUnit(unit1)
        self.assertTrue(len(self.homeostat.homeoUnits)  == existingUnits)
                    
    def testSaveHomeostatAndReadBackHomeostat(self):
        """
        Test saving out an empty serialized homeostat, reading it back in and checking
        it is the same as the original according to protocol specified in
        Homeostat>>sameAs 
        """
        filename = 'pickled_homeostat_test'
        
        "pickle out the empty homeostat and read it back"
        fileOut = open(filename, 'w')
        pickler = pickle.Pickler(fileOut)
        pickler.dump(self.homeostat)
        fileOut.close()
        fileIn = open(filename, 'r')
        unpickler = pickle.Unpickler(fileIn)
        newHomeostat = unpickler.load()
        fileOut.close()
        os.remove(filename)
        self.assertTrue(self.homeostat.sameAs(newHomeostat))
        
        "Do the same relying upon the class's own methods"
        
        self.homeostat.saveTo(filename)
        anotherHomeostat = Homeostat.readFrom(filename)
        self.assertTrue(self.homeostat.sameAs(anotherHomeostat))
        

    def testHomeostatReadyToGo(self):
        """
        Test that a homeostat is ready to go as soon as fully connected units are added
        """
        unit1 = HomeoUnit()
        unit2 = HomeoUnit()
        unit3 = HomeoUnit()
        unit4 = HomeoUnit()
        self.homeostat.addFullyConnectedUnit(unit1)
        self.homeostat.addFullyConnectedUnit(unit2)
        self.homeostat.addFullyConnectedUnit(unit3)
        self.homeostat.addFullyConnectedUnit(unit4)
    
        self.assertTrue(self.homeostat.isReadyToGo())
        
    def testHomeostatSaveInitialConditions(self):
        """
        Test that saving to file a full Ashby (4-unit Homeostat as setup in the setUp method)
        and reading it back produces an homeostat identical to the original as specified
        in the protocol Homeostat>>sameAs
        """        
        filename = 'pickled_homeostat_test'
        fileOut = open(filename, 'w')
        pickler = pickle.Pickler(fileOut)
        
        pickler.dump(self.homeostat) 
        fileOut.close()
        fileIn = open(filename, 'r')
        unpickler = pickle.Unpickler(fileIn)
        newHomeostat = unpickler.load()
        fileIn.close()
        os.remove(filename)
        self.assertTrue(self.homeostat.sameAs(newHomeostat))
 
        "Do the same with the class's saving methods"
        self.homeostat.saveTo(filename)
        anotherHomeostat = Homeostat.readFrom(filename)
        self.assertTrue(self.homeostat.sameAs(anotherHomeostat))
        
 
    def testIsConnectedAUnitToAnotherUnit(self):
        """
        Test adding and removing connection for a homeostat's units
        """
        unit1 = HomeoUnit()
        unit2 = HomeoUnit()

        self.homeostat.addUnit(unit1)
        self.homeostat.addUnit(unit2)

        self.homeostat.addConnectionWithRandomValuesFromUnit1toUnit2(unit1, unit2)

        self.assertTrue(self.homeostat.isConnectedFromTo(unit1,unit2))

        self.homeostat.removeConnectionFromUnit1ToUnit2(unit1, unit2)

        self.assertFalse(self.homeostat.isConnectedFromTo(unit1,unit2))
       
    def testRemoveConnection(self):
        """
        Test removing connections
        """
        unit1 = HomeoUnit()
        unit2 = HomeoUnit()
        unit3 = HomeoUnit()
        self.homeostat.addFullyConnectedUnit(unit1)
        self.homeostat.addFullyConnectedUnit(unit2)
        self.homeostat.addFullyConnectedUnit(unit3)

        self.homeostat.removeConnectionFromUnit1ToUnit2(unit1,unit2)
        self.homeostat.removeConnectionFromUnit1ToUnit2(unit2,unit3)

        self.assertTrue(self.homeostat.isConnectedFromTo(unit2,unit1))
        self.assertFalse(self.homeostat.isConnectedFromTo(unit1, unit2))
        self.assertFalse(self.homeostat.isConnectedFromTo(unit2, unit3))
        
    def testRemoveUnit(self):
        
        unit1 = HomeoUnit()

        "test remove an existing unit"

        self.homeostat.addUnit(unit1)
        self.homeostat.removeUnit(unit1)
        self.assertFalse(self.homeostat.hasUnit(unit1))

        "test removing a non existing unit"
        "this is ugly, but python's unittest does not have the shouldnt method"

        try:
            self.homeostat.removeUnit(unit1)
        except:
            self.fail("Homeostat should not raise Errors/Exception when removing non existing units ")
            
    def testRunForTicks(self):
        """
        Test that running for t ticks produces t data units for all units in the homeostat
        """
        initialTime = self.homeostat.time
        unit1 = HomeoUnit()
        unit2 = HomeoUnit()
        unit3 = HomeoUnit()
        unit4 = HomeoUnit()
        self.homeostat.addFullyConnectedUnit(unit1)
        self.homeostat.addFullyConnectedUnit(unit2)
        self.homeostat.addFullyConnectedUnit(unit3)
        self.homeostat.addFullyConnectedUnit(unit4)

        ticks = 100
        
        self.homeostat.runFor(ticks)
        self.assertTrue(self.homeostat.time == initialTime + ticks)
        "checks that it has a number of data points equal to ticks, and for all the units."

        self.assertTrue(len(self.homeostat.dataCollector.states) == ticks)
        for timeIndex, units in self.homeostat.dataCollector.states.iteritems():
            for unit in self.homeostat.homeoUnits:
                self.assertTrue(unit.name in units)

    def testRunningwithDelays(self):
        """
        Test that inserting a delays actually delays the homeostat
        """
        unit1 = HomeoUnit()
        unit2 = HomeoUnit()
        unit3 = HomeoUnit()
        unit4 = HomeoUnit()
        self.homeostat.addFullyConnectedUnit(unit1)
        self.homeostat.addFullyConnectedUnit(unit2)
        self.homeostat.addFullyConnectedUnit(unit3)
        self.homeostat.addFullyConnectedUnit(unit4)
        delay = 100
        
        self.homeostat.slowingFactor = delay
        
        for i in xrange(5):
            timeAtStart = time.time() 
            self.homeostat.runOnce()
            timeAtEnd =  time.time()
            self.assertTrue((timeAtEnd - timeAtStart) >= delay)

    def testSameAs(self):
        """
        Test that a copy of a homeostat is the equivalent to the original according 
        to the protocol in Homeostat>>sameAs
        """
        anotherHomeostat = deepcopy(self.homeostat)

        self.assertTrue(self.homeostat.sameAs(anotherHomeostat))
        
    def testSetupRandomValueFor(self):
        """
        Test  randomizing units' values through homeostat's methods 
        """

        unit1 = HomeoUnit()
        unit2 = HomeoUnit()
        unit3 = HomeoUnit()
        self.homeostat.addFullyConnectedUnit(unit1)
        self.homeostat.addFullyConnectedUnit(unit2)
        self.homeostat.addFullyConnectedUnit(unit3)

        oldOutput = unit1.currentOutput
        self.homeostat.randomizeValuesForAHomeoUnit(unit1)
        self.assertFalse(oldOutput == unit1.currentOutput)

    def testRun(self):
        """
        Test that homeostat runs without raising exceptions/errors
        and that it can be stopped once it starts. It needs to be run in a thread,
        otherwise we would never get control back
        """
        unit1 = HomeoUnit()
        unit2 = HomeoUnit()
        unit3 = HomeoUnit()
        unit4 = HomeoUnit()
        self.homeostat.addFullyConnectedUnit(unit1)
        self.homeostat.addFullyConnectedUnit(unit2)
        self.homeostat.addFullyConnectedUnit(unit3)
        self.homeostat.addFullyConnectedUnit(unit4)

        thr = Thread(target = self.homeostat.start)
        thr.start()
        time.sleep(1)
        self.homeostat.stop()
        
    def tearDown(self):
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()