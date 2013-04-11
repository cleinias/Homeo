'''
Created on Mar 13, 2013

@author: stefano
'''
from   HomeoUnit import *
from   HomeoUniselector import *
from   HomeoDataCollector import *
from   Homeostat import *
from   Helpers.General_Helper_Functions import *

import unittest,  pickle, os



class HomeoDataCollectorTest(unittest.TestCase):


    def setUp(self):
        self.dataCollector = HomeoDataCollector()

        "setup a standard Ashby 4 units homeostat to be used in various tests"

        self.homeostat = Homeostat()
        for unit in xrange(4):
            unit = HomeoUnit()
            unit.setRandomValues()
            self.homeostat.addFullyConnectedUnit(unit)
            self.homeostat.slowingFactor = 0


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
                if ('name: ' + unitName) in line:                                    # only count the first occurrence of unit, avoiding mentions in connections
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

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()