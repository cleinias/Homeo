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
from PyQt5.QtWidgets import QApplication

app = QApplication.instance() or QApplication(sys.argv)

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
        for unit in range(unitsAdded):
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
        for unit in range(unitsAdded):
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
        for i in range(unitsAdded):
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
        for index in range(2):
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
        for index in range(2):
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

        for unit in range(4):
            self.simulation.homeostat.addFullyConnectedUnit(HomeoUnit())
            
        simulationCycles = 30
        self.simulation.maxRuns = simulationCycles

        "runs for the default number of cycles"
        self.simulation.go()

        self.assertTrue(simulationCycles == self.simulation.homeostat.time)

    def testPause(self):
        """
        A simulation running in its thread, started as the GUI starts it,
        stops advancing when paused, part way through its runs, and resume
        carries on from where it stopped.  (Review findings SR-11, TS-11: the
        test never connected the thread to go(), so the simulation never ran
        and the test could not fail.)
        """
        self.simulation = HomeoQtSimulation()
        for unit in range(4):
            self.simulation.homeostat.addFullyConnectedUnit(HomeoUnit())
        simulationCycles = 100000
        self.simulation.maxRuns = simulationCycles
        self.simulation.simulDelay = 1

        self.simulation.moveToThread(self.thr)
        self.thr.started.connect(self.simulation.go)
        self.thr.start()
        try:
            sleep(0.5)
            self.simulation.pause()
            sleep(0.2)                              # let the loop see the flag
            pausedAt = self.simulation.homeostat.time
            sleep(0.3)
            self.assertEqual(self.simulation.homeostat.time, pausedAt)
            self.assertGreater(pausedAt, 0)
            self.assertLess(pausedAt, simulationCycles)
        finally:
            self.simulation.pause()
            self.thr.quit()
            self.assertTrue(self.thr.wait(5000))

        self.simulation.maxRuns = pausedAt + 7
        self.simulation.resume()                    # runs here, to maxRuns
        self.assertEqual(self.simulation.homeostat.time, pausedAt + 7)

    def testDataFileIsPresent(self):
        """
        A simulation must always have a data file
        """

        self.assertTrue(self.simulation.dataFilename is not None)

    def testDefaultDataFilenames(self):
        """Every default data filename is an extension-less stem, and skips the
        names whose files exist: the complete data under the stem, the plot data
        under <stem>-essential.txt (review finding SR-16)."""
        import tempfile
        from datetime import datetime as realDatetime
        from unittest import mock
        import Simulator.HomeoQtSimulation as module
        fixed = mock.Mock(wraps=realDatetime)
        fixed.now.return_value = realDatetime(2026, 10, 14, 12, 0, 0)
        stem = 'HomeoSimulationData-20261014120000-'
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(module, 'datetime', fixed):
            here = os.getcwd()
            os.chdir(tmp)
            self.addCleanup(os.chdir, here)
            names = [self.simulation.createDefaultDataFilename()]
            for written in ('', '-essential.txt', '.txt'):
                open(names[-1] + written, 'w').close()
                names.append(self.simulation.createDefaultDataFilename())
        self.assertEqual(names, [stem + str(n) for n in (1, 2, 3, 4)])

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

    def testUniselectorTypeChangedMidRun(self):
        """
        Changing a unit's uniselector type after live data started (the GUI's
        uniselector combo box during a run) keeps its uniselector series
        """
        self.simulation.initializeExperSetup()
        self.simulation.initializeLiveData()
        self.simulation.maxRuns = 10
        for _ in range(3):
            self.simulation.step()
        unit = self.simulation.homeostat.homeoUnits[0]
        unit.changeUniselectorType('Continuous')
        for _ in range(3):
            self.simulation.step()
        series = self.simulation.liveData[self.simulation.uniselectorKey(unit)]
        self.assertEqual(len(series), 6)
        self.assertEqual(len(series), len(self.simulation.liveData[unit]))
        self.simulation.saveEssentialDataOnFile(os.devnull, True)

    def testPlotDataReadsBackByName(self):
        """
        The saved plot data have one name per column, time first, so a reader
        that maps names to columns reads every column right (SR-07)
        """
        import tempfile
        import numpy as np
        self.simulation.initializeExperSetup()
        self.simulation.maxRuns = 4
        for _ in range(4):
            self.simulation.step()
        units = self.simulation.homeostat.homeoUnits
        with tempfile.TemporaryDirectory() as tmp:
            for withWeights in (False, True):
                path = os.path.join(tmp, 'plot.csv')
                self.simulation.saveEssentialDataOnFile(path, withWeights)
                data = np.genfromtxt(path, delimiter=',', names=True, deletechars='',
                                     skip_header=3)      # the three comment lines
                names = ['time'] + [n for u in units for n in
                                    ([u.name, u.name + '_unisel', u.name + '_weight'] if withWeights
                                     else [u.name, u.name + '_unisel'])]
                self.assertEqual(list(data.dtype.names), names)
                self.assertEqual(list(data['time']), [1, 2, 3, 4])   # the time after each tick
                for u in units:
                    self.assertTrue(np.allclose(data[u.name], self.simulation.liveData[u]))

    def testTimeResetRestartsTheLiveData(self):
        """
        After a time reset the live data, and so the saved plot data, start
        again with the time, in the same containers (the GUI's charts hold
        them); a new homeostat's live data have only its units (SR-15)
        """
        self.simulation.initializeExperSetup()
        self.simulation.maxRuns = 20
        for _ in range(20):
            self.simulation.step()
        liveData = self.simulation.liveData
        self.simulation.timeReset()
        self.simulation.maxRuns = 5
        for _ in range(5):
            self.simulation.step()
        unit = self.simulation.homeostat.homeoUnits[0]
        self.assertIs(self.simulation.liveData, liveData)
        self.assertEqual(len(liveData[unit]), 5)
        self.assertEqual(self.simulation.liveTicks, [1, 2, 3, 4, 5])
        old = set(self.simulation.homeostat.homeoUnits)
        self.simulation.fullReset()
        self.assertFalse(old & set(k for k in liveData if not isinstance(k, str)))

    def testStepBeforeStart(self):
        """
        Step works before Start: the first step sets up the live data, as go()
        does (it raised KeyError, e.g. in HomeoMinimalGui, where Step is on
        from the start)
        """
        self.simulation.initializeExperSetup()
        self.simulation.maxRuns = 10
        self.simulation.step()
        unit = self.simulation.homeostat.homeoUnits[0]
        self.assertEqual(len(self.simulation.liveData[unit]), 1)

    def testPauseAndResume(self):
        """
        Pause, here from a tick callback, ends go() after the tick under way;
        resume() carries on from there to maxRuns, with one live-data sample
        and one callback and observer call per tick (SR-12)
        """
        sim = self.simulation
        sim.initializeExperSetup()
        sim.simulDelay = 0
        sim.maxRuns = 20
        seen, observed = [], []

        def pauseAt7(hom, t):
            seen.append(t)
            if t == 7:
                sim.pause()
        sim.tick_callbacks.append(pauseAt7)
        sim.tick_observers.append(lambda hom, t: observed.append(t))
        sim.go()
        self.assertEqual(sim.homeostat.time, 8)
        self.assertFalse(sim._isRunning)
        sim.resume()
        self.assertEqual(sim.homeostat.time, 20)
        self.assertEqual(seen, list(range(20)))
        self.assertEqual(observed, list(range(1, 21)))
        self.assertEqual(sim.liveTicks, list(range(1, 21)))
        unit = sim.homeostat.homeoUnits[0]
        self.assertEqual(len(sim.liveData[unit]), 20)

    def testStepStopsAtMaxRuns(self):
        sim = self.simulation
        sim.initializeExperSetup()
        sim.maxRuns = 3
        for _ in range(5):
            sim.step()
        self.assertEqual(sim.homeostat.time, 3)
        self.assertEqual(sim.liveTicks, [1, 2, 3])

    def testSaveAndLoadAHomeostat(self):
        """
        save() pickles the homeostat to its file; loadNewHomeostat reads it
        back into another simulation, live data restarted for the loaded
        units; a file that is not a homeostat raises HomeostatError (SR-12)
        """
        import tempfile
        sim = self.simulation
        sim.initializeExperSetup()
        sim.homeostat.randomizeValuesforAllUnits()
        sim.maxRuns = 5
        for _ in range(5):
            sim.step()
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'saved.pickled')
            sim.homeostatFilename = path
            sim.save()
            self.assertTrue(sim.homeostatIsSaved)
            other = HomeoQtSimulation()
            other.loadNewHomeostat(path)
            loaded = other.homeostat
            self.assertIsNot(loaded, sim.homeostat)
            self.assertEqual(other.homeostatFilename, path)
            self.assertTrue(other.homeostatIsSaved)
            self.assertTrue(other.dataAreSaved)
            self.assertEqual(loaded.time, 5)
            for a, b in zip(sim.homeostat.homeoUnits, loaded.homeoUnits):
                self.assertEqual(a.name, b.name)
                self.assertEqual(a.criticalDeviation, b.criticalDeviation)
                self.assertEqual([c.weight * c.switch for c in a.inputConnections],
                                 [c.weight * c.switch for c in b.inputConnections])
            self.assertEqual(set(k[0] if isinstance(k, tuple) else k for k in other.liveData),
                             set(loaded.homeoUnits))
            self.assertEqual(other.liveTicks, [])
            bad = os.path.join(tmp, 'not-a-homeostat.pickled')
            with open(bad, 'wb') as f:
                f.write(b'nothing to see')
            with self.assertRaises(HomeostatError):
                other.loadNewHomeostat(bad)
            self.assertIs(other.homeostat, loaded)

    def tearDown(self):
        pass




if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()