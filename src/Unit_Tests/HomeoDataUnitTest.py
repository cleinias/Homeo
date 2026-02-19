'''
Created on Mar 13, 2013

@author: stefano
'''
from   Core.HomeoUnit import *
from   Core.HomeoUniselector import *
from   Core.HomeoDataUnit import *
from   Core.Homeostat import *
from   Helpers.General_Helper_Functions import *

import unittest, numpy, string, random
from copy import deepcopy



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
        Test if two data units are the same according to the protocol
        specified in HomeoDataUnit>>sameValuesAs

        """
        
        anotherDataUnit = copy(self.dataUnit)
        aDeepcopyDataUnit = deepcopy(self.dataUnit)
        
        self.assertTrue(self.dataUnit.sameValuesAs(anotherDataUnit))
        self.assertTrue(self.dataUnit.sameValuesAs(aDeepcopyDataUnit))

        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()