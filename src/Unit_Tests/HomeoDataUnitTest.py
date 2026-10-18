'''
@author: stefano
'''
from   Core.HomeoUnit import *
from   Core.HomeoUniselector import *
from   Core.HomeoDataUnit import *
from   Core.Homeostat import *
from   Helpers.General_Helper_Functions import *

import unittest, numpy, string, random
from copy import copy, deepcopy



class HomeoDataUnitTest(unittest.TestCase):


    def setUp(self):
  
        self.dataUnit = HomeoDataUnit()
        self.unit = HomeoUnit()
   


    def tearDown(self):
        pass

    def testNewStateFor(self):
        """
        FIXIT I am not sure why I repeat the test already done in testReadDataFromUnit
        """
        newDataUnit = HomeoDataUnit.newUnitFor(self.unit)
        self.dataUnit = newDataUnit
        self.assertTrue(self.dataUnit.name == self.unit.name)
        self.assertTrue(self.dataUnit.maxDeviation  == self.unit.maxDeviation)
        for conn in self.unit.inputConnections: 
            connArray = []
            connArray = self.dataUnit.connectedTo[conn.incomingUnit.name]
            self.assertTrue(connArray[0] == conn.weight)
            self.assertTrue(connArray[1] == conn.switch)
            self.assertTrue(connArray[2] == conn.state)
            self.assertTrue(connArray[3] == conn.noise)
        self.assertTrue(self.dataUnit.output == self.unit.currentOutput)
        self.assertTrue(self.dataUnit.uniselectorState == self.unit.uniselectorActive)

    def testReadDataFromUnit(self):
        """
        Test all data read from a Homeounit 
        coincide with the HomeoUnit's own
        """
        self.dataUnit.readStateFrom(self.unit)
        self.assertTrue(self.dataUnit.name == self.unit.name)
        self.assertTrue(self.dataUnit.maxDeviation == self.unit.maxDeviation)
        for conn in self.unit.inputConnections: 
            connArray = []
            connArray = self.dataUnit.connectedTo[conn.incomingUnit.name]
            self.assertTrue(connArray[0] == conn.weight)
            self.assertTrue(connArray[1] == conn.switch)
            self.assertTrue(connArray[2] == conn.state)
            self.assertTrue(connArray[3] == conn.noise)
        self.assertTrue(self.dataUnit.output == self.unit.currentOutput)
        self.assertTrue(self.dataUnit.uniselectorState == self.unit.uniselectorActive)

    def testPrintDataOnString(self):
        """
        Test that the data the HomeoDataUnit prints out correctly represent its data"
        """

        "0. create a list of lists with pairs of labels/values from the printed data"
        
        unit2 = HomeoUnit()
        unit3 = HomeoUnit()
        self.unit.addConnectionWithRandomValues(unit2)
        self.unit.addConnectionWithRandomValues(unit3)
        self.unit.selfUpdate()
        self.dataUnit.readStateFrom(self.unit)
        dataString = self.dataUnit.printDataOn('')
        dataItems = dataString.split()
        dataItems = [s.replace(':', '') for s in dataItems]
        unitAsLists = []
        for i in range(0,len(dataItems) -1, 2):
            unitAsLists.append([dataItems[i] , dataItems[i+1]])
        
        '''Create a simil data unit  from the list of lists, knowing that:
        the first 5 items represent the homeodataunit primary values
        (name, critDev, output, uniselector, active), and any
        block of 4 pairs afterwards represent a connection and its values'''
        dic = {}
        dic['name'] = unitAsLists[0][1]
        dic['critDev'] = unitAsLists[1][1]
        dic['output'] = unitAsLists[2][1]
        dic['uniselector'] = unitAsLists[3][1]
        dic['active'] = unitAsLists[4][1]
        headerPairs = 5
        if len(unitAsLists) > headerPairs:
            dic['connections'] = {}
            for i in range(headerPairs, len(unitAsLists), 4):
                dic['connections'][unitAsLists[i][1]] = [unitAsLists[i+1][1], unitAsLists[i+2][1], unitAsLists[i+3][1]]
      
        "1. Check unit's primary data are the same as the original" 
        self.assertTrue(self.dataUnit.name == dic['name'])
        self.assertAlmostEqual(self.dataUnit.output, float(dic['output']), 5)
        self.assertTrue(str(self.dataUnit.uniselectorState) == dic['uniselector']) 
            
        "2. the connections and their values are the same"
        connectedTo = dic['connections']
        self.assertTrue(len(connectedTo) == len(self.dataUnit.connectedTo))
        for orig, readback in zip(sorted(self.dataUnit.connectedTo.keys()), sorted(connectedTo.keys())):
            self.assertTrue(orig == readback)    # names are the same
            self.assertAlmostEqual(float(connectedTo[readback][0]), self.dataUnit.connectedTo[orig][0],5) # weights are the same
            self.assertAlmostEqual(float(connectedTo[readback][1]), self.dataUnit.connectedTo[orig][1],5) # switches are the same
            self.assertAlmostEqual(float(connectedTo[readback][2]),  self.dataUnit.connectedTo[orig][3],5) # noises are the same 
        
    def testPrintEssentialVariableOnString(self):
        """
        Test that the ***essential*** data the HomeoDataUnit prints out correctly represent its data
        TODO
        Check HomeoDataUnit>>printEssentialVariablesOn: for ideas on how to carry out the test
        """
        self.unit
        unit2 = HomeoUnit()
        unit3 = HomeoUnit()
        self.unit.addConnectionWithRandomValues(unit2)
        self.unit.addConnectionWithRandomValues(unit3)
        for i in range(100):
            self.unit.selfUpdate()
        self.dataUnit.readStateFrom(self.unit)
        printedData = self.dataUnit.printEssentialVariableOn('')
        self.assertAlmostEqual(self.dataUnit.criticalDeviation, float(printedData),5)

    def testSameValuesAs(self):
        """
        Two data units read from the same unit state have the same values,
        and so do their copies; a difference in any recorded value -- the
        critical deviation included -- makes them different.  The data units
        compared hold recorded values, not empty ones.
        """
        numpy.random.seed(3)
        self.unit.setRandomValues()
        other = HomeoUnit()
        self.unit.addConnectionWithRandomValues(other)
        for i in range(50):
            self.unit.selfUpdate()
        self.dataUnit.readStateFrom(self.unit)
        self.assertIsNotNone(self.dataUnit.criticalDeviation)
        sameState = HomeoDataUnit()
        sameState.readStateFrom(self.unit)
        self.assertTrue(self.dataUnit.sameValuesAs(sameState))
        self.assertTrue(self.dataUnit.sameValuesAs(copy(self.dataUnit)))
        self.assertTrue(self.dataUnit.sameValuesAs(deepcopy(self.dataUnit)))

        changes = {'criticalDeviation': self.dataUnit.criticalDeviation + 0.1,
                   'output': self.dataUnit.output + 0.1,
                   'maxDeviation': self.dataUnit.maxDeviation + 1,
                   'name': self.dataUnit.name + 'x',
                   'uniselectorState': ('manual' if self.dataUnit.uniselectorState != 'manual'
                                        else 'uniselector'),
                   'uniselectorActive': not self.dataUnit.uniselectorActive}
        for attribute, value in changes.items():
            with self.subTest(attribute):
                changed = deepcopy(self.dataUnit)
                setattr(changed, attribute, value)
                self.assertFalse(self.dataUnit.sameValuesAs(changed))

    def testAFiringShowsWithTheWeightsItDrew(self):
        '''The row recorded at time t holds the state left by the update of
           tick t-1: a uniselector firing in that update shows in the same row
           as the weights it drew, and only there.'''
        hom = Homeostat()
        hom.slowingFactor = 0
        units = [HomeoUnit() for i in range(2)]
        for unit in units:
            unit.setRandomValues()
            hom.addFullyConnectedUnit(unit)
        unit = units[0]
        unit.critThreshold = 0.01           # critical at almost any deviation
        unit.uniselectorTimeInterval = 5
        firings = []
        for tick in range(40):
            count = unit.uniselectorActivationCount
            hom.runFor(tick + 1)
            if unit.uniselectorActivationCount > count:
                firings.append(tick)
        self.assertTrue(firings)
        states = hom.dataCollector.states
        other = units[1].name
        for tick in range(1, 40):
            row, before = states[tick][unit.name], states[tick - 1][unit.name]
            self.assertEqual(row.uniselectorActive, 1 if tick - 1 in firings else 0, tick)
            if tick - 1 in firings:
                self.assertNotEqual(row.connectedTo[other][0], before.connectedTo[other][0])
            else:
                self.assertEqual(row.connectedTo[other][0], before.connectedTo[other][0])



if __name__ == "__main__":
    unittest.main()