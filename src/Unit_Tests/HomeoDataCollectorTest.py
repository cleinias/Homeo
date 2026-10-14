'''
Created on Mar 13, 2013

@author: stefano
'''
from   Core.HomeoUnit import *
from   Core.HomeoUniselector import *
from   Core.HomeoDataCollector import *
from   Core.Homeostat import *
from   Helpers.General_Helper_Functions import *

import unittest,  pickle, os
import numpy as np



class HomeoDataCollectorTest(unittest.TestCase):


    def setUp(self):
        self.dataCollector = HomeoDataCollector()

        "setup a standard Ashby 4 units homeostat to be used in various tests"

        self.homeostat = Homeostat()
        for unit in range(4):
            unit = HomeoUnit()
            unit.setRandomValues()
            self.homeostat.addFullyConnectedUnit(unit)
            self.homeostat.slowingFactor = 1


    def testAddStateForUnit(self):
        " DataCollector adds a DataUnit for a  HomeoUnit for time t"

        unit1 = HomeoUnit()
        unit2 = HomeoUnit()
        unit3 = HomeoUnit()

        unit1.time = 0
        unit2.time = 0
        unit3.time = 0
        self.dataCollector.atTimeIndexAddDataUnitForAUnit(0, unit1)
        self.dataCollector.atTimeIndexAddDataUnitForAUnit(0,unit2)
        self.dataCollector.atTimeIndexAddDataUnitForAUnit(0,unit3)

        unit1.time = 1
        unit2.time = 1
        unit3.time = 1
        self.dataCollector.atTimeIndexAddDataUnitForAUnit(1,unit1)
        self.dataCollector.atTimeIndexAddDataUnitForAUnit(1,unit2)
        self.dataCollector.atTimeIndexAddDataUnitForAUnit(1,unit3)

        unit1.time = 2
        unit2.time = 2
        unit2.time = 2
        self.dataCollector.atTimeIndexAddDataUnitForAUnit(2, unit1)
        self.dataCollector.atTimeIndexAddDataUnitForAUnit(2, unit2)
        self.dataCollector.atTimeIndexAddDataUnitForAUnit(2, unit3)

        unit1.time = -1
        unit2.time = -1
        unit3.time = -1
        self.dataCollector.atTimeIndexAddDataUnitForAUnit(-1, unit1)
        self.dataCollector.atTimeIndexAddDataUnitForAUnit(-1, unit2)
        self.dataCollector.atTimeIndexAddDataUnitForAUnit(-1, unit3)

        "Checks that the dictionary contains DataUnits for all the units"
        for dataDic in self.dataCollector.states: 
            if dataDic is not None: 
                self.assertTrue(unit1.name in self.dataCollector.states[dataDic])
                self.assertTrue(unit2.name in self.dataCollector.states[dataDic])
                self.assertTrue(unit3.name in self.dataCollector.states[dataDic])
                self.assertTrue(self.dataCollector.states[dataDic][unit1.name].name == unit1.name)                

    def testPickleOut(self):
        """
        saves the complete run to  a pickle file for later rereading and analysis
        """

        "produce some data"
        unit1 = HomeoUnit()
        unit2 = HomeoUnit()
        unit3 = HomeoUnit()
        self.dataCollector.atTimeIndexAddDataUnitForAUnit(1, unit1)
        self.dataCollector.atTimeIndexAddDataUnitForAUnit(1, unit2)
        self.dataCollector.atTimeIndexAddDataUnitForAUnit(1, unit3)

        unit1.time = 2
        unit2.time = 2
        unit3.time = 2
        self.dataCollector.atTimeIndexAddDataUnitForAUnit(2, unit1)
        self.dataCollector.atTimeIndexAddDataUnitForAUnit(2, unit2)
        self.dataCollector.atTimeIndexAddDataUnitForAUnit(3, unit3)

        filename = 'pickled_dataCollector_test'
        self.dataCollector.saveOn(filename)
        newDataCollector = HomeoDataCollector.readFrom(filename)
        os.remove(filename)
        
        
        " Check that the two dataCollectors have the same number of states (= time indices)"
        self.assertTrue(len(self.dataCollector.states) == len(newDataCollector.states))
 
        '''checks that  the saved dataCollector has, for each time tick, 
           a dictionary indexed by the same unit names as the original dataCollector'''
        for firstDic, secDic in zip(self.dataCollector.states.values(), newDataCollector.states.values()):
            self.assertTrue(len(firstDic) == len(secDic))
            for origName, savedName in zip(sorted(firstDic.keys()), sorted(secDic.keys())):
                self.assertTrue(origName == savedName)

    def testExtractCriticalDevAsCollectionForUnit(self):
        """
        Test that the critical deviation data extracted by the DataCollector is identical to the original
        """

        "initializing and setting up the homeostat run  and the data collections"
        testResultCollection = []
        originalData = []
        extractedData = []
        self.homeostat.runFor(1000)

        "extracting data and comparing to the original" 
        for unit in self.homeostat.homeoUnits: 
            extractedData = self.homeostat.dataCollector.criticalDevAsCollectionForUnit(unit)
            originalData = [self.homeostat.dataCollector.states[tick][unit.name].criticalDeviation for tick in self.homeostat.dataCollector.states]
            self.assertTrue(len(extractedData) == len(originalData))
            for orig, extracted in zip(originalData,extractedData) :
                testResultCollection.append(orig != extracted)    #collecting all instances in which the data differ"
            self.assertFalse(True in testResultCollection)
   
    def testExtractCriticalDevAsCollectionForAllUnit(self):
        """
        Test that the critical deviation data extracted by the DataCollector is identical to the original
        """

        "initializing and setting up the homeostat run  and the data collections"
        testResultCollection = []
        originalData = []
        extractedData = []
        self.homeostat.runFor(1000)

        "extracting data and comparing to the original" 
        for unit in self.homeostat.homeoUnits: 
            extractedData = self.homeostat.dataCollector.criticalDevAsCollectionForUnit(unit)
            originalData = [self.homeostat.dataCollector.states[tick][unit.name].criticalDeviation for tick in self.homeostat.dataCollector.states]
            self.assertTrue(len(extractedData) == len(originalData))
            for orig, extracted in zip(originalData,extractedData) :
                testResultCollection.append(orig != extracted)    #collecting all instances in which the data differ"
            self.assertFalse(True in testResultCollection)

    def testSaveCompleteDataOnFile(self):
        """
        Test that complete data are  saved on  file: 
        
        The integrity of saving data for single units is already tested in HomeoDataUnit
        Here we test that: 
        - we have the correct number of time indices for the homeostat run
        - the correct number of unit's data points for each time index 
        """
 
        "produce some data"
 
        "initializing and setting up the homeostat run the ouput file and the data collections" 
        
        unitNames = []
        for unit in self.homeostat.homeoUnits:
            unitNames.append(unit.name)

        dataReadBack = []
        homeostatRuns = 100

        datafile = 'testing-datafile.txt'
        self.homeostat.runFor(homeostatRuns)
        self.homeostat.dataCollector.saveCompleteDataOnFile(datafile)
        datafile = open('testing-datafile.txt', 'r+')             # open file for reading and writing
 
        dataReadBack = datafile.readlines()
        datafile.close()
        os.remove('testing-datafile.txt')
        
        '''test that the data file has exactly as many lines as 
           the homeostat runs * the number of units in the homeostat
           and that it has exactly as many time indices as the homeostat runs''' 
        timeIndices = []
        for line in dataReadBack:
            timeIndices.append(line.split()[1])
        self.assertTrue(len(timeIndices) == homeostatRuns * len(self.homeostat.homeoUnits))
        self.assertTrue(len(set(timeIndices)) == homeostatRuns)
 
        dataUnitsReadBack = {}
        for line in dataReadBack:
            for unitName in unitNames:
                if ('name: ' + unitName) in line:                        # only count the first occurrence of unit, avoiding mentions in connections
                    if unitName not in dataUnitsReadBack:
                        dataUnitsReadBack[unitName] = 1
                    else:
                        dataUnitsReadBack[unitName] += 1
         
        self.assertTrue(len(dataUnitsReadBack) == len(unitNames))        # we have recorded data for the right number of units              
        for unit, count in dataUnitsReadBack.items():
            self.assertTrue(unit in unitNames)                           # we have data for all the units
            self.assertTrue(count == homeostatRuns)                      # each unit has as many lines as homeostat runs
            
    def tearDown(self):
        pass

class ExportersTest(unittest.TestCase):
    """Each exporter the collector keeps writes data that read back as the
    collected values (review finding CD-13).  The others -- the Ggobi,
    separator and per-unit exporters -- crashed on any data and had no
    callers: they were deleted on 14 Oct 2026."""

    def setUp(self):
        np.random.seed(2)
        self.homeostat = Homeostat()
        for _ in range(3):
            unit = HomeoUnit()
            unit.setRandomValues()
            self.homeostat.addFullyConnectedUnit(unit)
        self.homeostat.runFor(5)
        self.collector = self.homeostat.dataCollector
        self.names = [u.name for u in self.homeostat.homeoUnits]

    def deviation(self, tick, name):
        return self.collector.states[tick][name].criticalDeviation

    def testRExporter(self):
        lines = self.collector.printPlottingDataForROnAString('').splitlines()
        lines = [line for line in lines if not line.startswith('#')]
        header = lines[0].split(',')
        self.assertEqual(header, [h for n in self.names for h in (n, n + '_un.')])
        rows = [[float(v) for v in line.split(',')] for line in lines[1:]]
        self.assertEqual(len(rows), len(self.collector.states))
        for row, tick in zip(rows, sorted(self.collector.states)):
            self.assertEqual(row[0::2], [self.deviation(tick, n) for n in self.names])
            self.assertTrue(set(row[1::2]) <= {0.0, 1.0})

    def testCompleteAndEssentialExporters(self):
        complete = self.collector.printCompleteDataOnAString('').splitlines()
        essential = self.collector.printEssentialDataOnAString('').splitlines()
        expected = [(tick, n) for tick in sorted(self.collector.states) for n in self.names]
        self.assertEqual(len(complete), len(expected))
        self.assertEqual(len(essential), len(expected))
        for line, (tick, name) in zip(complete, expected):
            words = line.split()
            self.assertEqual(int(words[1]), tick)
            self.assertAlmostEqual(float(words[words.index('critDev:') + 1]),
                                   self.deviation(tick, name), places=5)
        for line, (tick, name) in zip(essential, expected):
            label, value = line.split(':    ')[1:3]
            self.assertTrue(label.endswith(name))
            self.assertAlmostEqual(float(value), self.deviation(tick, name), places=5)

    def testThePickleRoundTrips(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'collector.pickled')
            self.collector.saveOn(path)
            back = HomeoDataCollector.readFrom(path)
        self.assertEqual(sorted(back.states), sorted(self.collector.states))
        for tick in back.states:
            for name in self.names:
                self.assertTrue(back.states[tick][name].sameValuesAs(self.collector.states[tick][name]))

    def testTheDeviationHistoryArray(self):
        """criticalDevAsNPArrayForAllUnits is what CODE_OVERVIEW says: one
        column per unit, its deviations; until 14 Oct 2026 the deviations
        were interleaved with 0/1 uniselector columns (CD-14)."""
        data = self.collector.criticalDevAsNPArrayForAllUnits()
        self.assertEqual(data.shape, (len(self.collector.states), len(self.names)))
        for j, unit in enumerate(self.homeostat.homeoUnits):
            self.assertEqual(list(data[:, j]), self.collector.criticalDevAsCollectionForUnit(unit))

    def testCollectionNeedNotStartAtZero(self):
        """After flushData the first recorded tick is not 0: the exporters
        label rows with their ticks and the R exporter works; an empty
        collector exports nothing.  Until 14 Oct 2026 the R exporter raised
        KeyError and the essential one counted from 0 (CD-15)."""
        self.homeostat.flushData()
        self.homeostat.runFor(8)
        self.collector = self.homeostat.dataCollector
        ticks = sorted(self.collector.states)
        self.assertEqual(ticks[0], 5)
        rows = [line for line in self.collector.printPlottingDataForROnAString('').splitlines()
                if not line.startswith('#')][1:]
        self.assertEqual(len(rows), len(ticks))
        essential = self.collector.printEssentialDataOnAString('').splitlines()
        self.assertEqual([int(line.split()[1]) for line in essential[::len(self.names)]], ticks)
        import contextlib, io
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(HomeoDataCollector().printPlottingDataForROnAString(''), '')

    def testTheBrokenExportersAreGone(self):
        for name in ('saveDeviationOnForUnit', 'saveEssentialsOnAStringWithSeparator',
                     'printPlottingDataForGgobiOnAString', 'printPlottingDataOnAString',
                     'printPlottingDataOnAStringWithSeparator',
                     'uniselectorActivatedAsCollectionOfArraysForAllUnits'):
            self.assertFalse(hasattr(HomeoDataCollector, name), name)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()