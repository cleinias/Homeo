'''
Created on Mar 13, 2013

@author: stefano
'''
from   HomeoUnit import *
from   HomeoUniselector import *
from   HomeoDataUnit import *
from   Homeostat import *
from   Helpers.General_Helper_Functions import *

import unittest, numpy, string, random



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
            connArray = self.dataUnit.connectedTo(conn.incomingUnit.name)
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
        self.dataUnit.readStateFrom(self.unit1)
        self.assertTrue(self.dataUnit.name() == self.unit.name())
        self.assertTrue(self.dataUnit.maxDeviation() == self.unit.maxDeviation())
        for conn in self.unit.inputConnections(): 
            connArray = []
            connArray = self.dataUnit.connectedTo(conn.incomingUnit.name())
            self.assertTrue(connArray[0] == conn.weight())
            self.assertTrue(connArray[1] == conn.switch())
            self.assertTrue(connArray[2] == conn.state())
            self.assertTrue(connArray[3] == conn.noise())
        self.assertTrue(self.dataUnit.output() == self.unit.currentOutput())
        self.assertTrue(self.dataUnit.uniselectorState() == self.unit.uniselectorActive())

    def testPrintDataOnStream(self):
        """
        Test that the data the HomeoDataUnit prints out correctly represent its data"
        TODO
        Check HomeoDataUnit>>printDataOn: for ideas on how to carry out the test 
        """
        self.dataUnit.readStateFrom(self.unit)
        #dataUnit printDataOn:    aStream.
        self.assertTrue(False)
        
    def testPrintEssentialVariableOn(self):
        """
        Test that the ***essential*** data the HomeoDataUnit prints out correctly represent its data
        TODO
        Check HomeoDataUnit>>printEssentialVariablesOn: for ideas on how to carry out the test
        """
        self.dataUnit.readStateFrom(self.unit)
        #self.dataUnit.printEssentialVariableOn:    aStream.

        self.assertTrue(False)


    def testSameValuesAs(self):
        """
        Test if two data units are the same according to the protocol
        specified in HomeoDataUnit>>same as
        TODO
        """
        self.assertTrue(False)
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()