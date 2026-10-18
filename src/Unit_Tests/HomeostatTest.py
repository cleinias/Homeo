'''
@author: stefano
'''
from   Core.HomeoUnit import *
from   Core.HomeoUniselector import *
from   Core.Homeostat import *
from   Helpers.General_Helper_Functions import *

import unittest, pickle, os, time, tempfile
from copy import copy, deepcopy

class HomeostatTest(unittest.TestCase):


    def setUp(self):
        "the pickles go to a temporary directory, not into the checkout"
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
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
        filename = os.path.join(self.tmpdir.name, 'pickled_homeostat_test')
        
        "pickle out the empty homeostat and read it back"
        fileOut = open(filename, 'wb')
        pickler = pickle.Pickler(fileOut)
        pickler.dump(self.homeostat)
        fileOut.close()
        fileIn = open(filename, 'rb')
        unpickler = pickle.Unpickler(fileIn)
        newHomeostat = unpickler.load()
        fileIn.close()
        os.remove(filename)
        self.assertTrue(self.homeostat.sameAs(newHomeostat))

        "Do the same relying upon the class's own methods"
        
        self.homeostat.saveTo(filename)
        anotherHomeostat = Homeostat.readFrom(filename)
        self.assertTrue(self.homeostat.sameAs(anotherHomeostat))
        

    def testLoadedUnitsKeepTheirNames(self):
        '''A loaded homeostat's units register their names: a unit
           made afterwards gets a new name, also once the units they were
           saved from are gone.'''
        filename = os.path.join(self.tmpdir.name, 'names')
        names = [unit.name for unit in self.homeostat.homeoUnits]
        self.homeostat.saveTo(filename)
        self.homeostat = None                   # the saved units die
        HomeoUnit.clearNames()                  # as in a fresh process
        loaded = Homeostat.readFrom(filename)
        self.assertEqual([unit.name for unit in loaded.homeoUnits], names)
        self.assertTrue(set(names) <= HomeoUnit.allNames)
        self.assertNotIn(HomeoUnit().name, names)
        "loaded while the first loaded homeostat is alive, which then dies"
        again = Homeostat.readFrom(filename)
        loaded = None
        import gc
        gc.collect()
        self.assertTrue(set(names) <= HomeoUnit.allNames)
        self.assertNotIn(HomeoUnit().name, names)

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

        self.assertIs(self.homeostat.isReadyToGo(), True)

    def testHomeostatWithAnUnreadyUnitIsNotReady(self):
        '''A unit missing an essential parameter makes the homeostat not
           ready, and runFor does not run it.'''
        units = [HomeoUnit() for i in range(2)]
        for unit in units:
            self.homeostat.addFullyConnectedUnit(unit)
        self.homeostat.slowingFactor = 0
        units[1]._viscosity = None
        self.assertFalse(units[1].isReadyToGo())
        self.assertIs(self.homeostat.isReadyToGo(), False)
        self.homeostat.runFor(5)
        self.assertEqual(self.homeostat.time, 0)

    def testHomeostatSaveInitialConditions(self):
        """
        Test that saving to file a full Ashby (4-unit Homeostat as setup in the setUp method)
        and reading it back produces an homeostat identical to the original as specified
        in the protocol Homeostat>>sameAs
        """        
        filename = os.path.join(self.tmpdir.name, 'pickled_homeostat_test')
        fileOut = open(filename, 'wb')
        pickler = pickle.Pickler(fileOut)

        pickler.dump(self.homeostat)
        fileOut.close()
        fileIn = open(filename, 'rb')
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
        for timeIndex, units in self.homeostat.dataCollector.states.items():
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
        delay = 100  #in milliseconds
        
        self.homeostat.slowingFactor = delay
        
        for i in range(5):
            timeAtStart = time.time() # in seconds
            self.homeostat.runOnce()  
            timeAtEnd =  time.time()  # in seconds
            self.assertTrue((timeAtEnd - timeAtStart) >= (delay/1000))

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
        A homeostat runs for the ticks asked, recording every unit at each tick
        """
        self.homeostat.slowingFactor = 0
        self.homeostat.runFor(20)
        self.assertEqual(self.homeostat.time, 20)
        states = self.homeostat.dataCollector.states
        self.assertEqual(sorted(states), list(range(20)))
        self.assertTrue(all(len(units) == len(self.homeostat.homeoUnits) == 4 for units in states.values()))
        self.assertTrue(all(unit.time == 19 for unit in self.homeostat.homeoUnits))

    def testRunContinuesFromItsTime(self):
        """
        runFor(t) runs until the homeostat's time reaches t, the way the batch
        scripts call it (runFor(target_tick)).  A second runFor carries on
        from where the first stopped: time goes on from 20, the new ticks are
        recorded under their own indices, and the units' times follow; a
        target already reached runs nothing.
        """
        self.homeostat.slowingFactor = 0
        self.homeostat.runFor(20)
        before = {tick: dict(units) for tick, units in self.homeostat.dataCollector.states.items()}
        self.homeostat.runFor(35)
        self.assertEqual(self.homeostat.time, 35)
        states = self.homeostat.dataCollector.states
        self.assertEqual(sorted(states), list(range(35)))
        for tick, units in before.items():
            self.assertEqual(states[tick], units)
        self.assertTrue(all(len(states[tick]) == 4 for tick in range(20, 35)))
        self.assertTrue(all(unit.time == 34 for unit in self.homeostat.homeoUnits))
        self.homeostat.runFor(30)
        self.assertEqual(self.homeostat.time, 35)
        self.assertEqual(len(states), 35)

    def tearDown(self):
        pass


if __name__ == "__main__":
    unittest.main()
