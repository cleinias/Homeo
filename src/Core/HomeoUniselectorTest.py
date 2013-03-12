'''
Created on Mar 11, 2013

@author: stefano

These tests are currently very scarce. Need to add better coverage
'''
from   HomeoUnit import *
from   HomeoConnection import *
from   HomeoUniselector import *
from   Homeostat import *
from   HomeoNeedleUnit import *
from   Helpers.General_Helper_Functions import *

import unittest, numpy, string, random


class HomeoUniselectorTest(unittest.TestCase):


    def setUp(self):
        uniselector = HomeoUniselector()

    def tearDown(self):
        pass

    def testHomeoUniselectorClassType(self):
        """
        Test that HomeoUniselector knows its types include only itself and its subclasses 
        """
        currentClasses = []
        bogusClasses = []
        currentClasses.extend([class_.__name__ for class_ in withAllSubclasses(HomeoUniselector)])
        for bogusClass in xrange(5):
            newRandomName = ''.join(random.choice(string.ascii_lowercase) for x in range(10))
            bogusClasses.extend(newRandomName)
        for currentClass in currentClasses:
            self.assertTrue(HomeoUniselector.includeType(currentClass))
        for bogusClass in bogusClasses:
            self.assertFalse(HomeoUniselector.includesType(bogusClass))

    def testIntervalBounds(self):
        """
        Test that HomeoUniselector has a positive interval
        """
        self.assertTrue(self.uniselector.upperBound() - self.uniselector.lowerBound()) >= 0
                        
    def testHomeoUniselectorTriggered(self):
        """
        Test that HomeoUniselector is activated when its input exceeds the normal bounds
        """
        self.assertTrue(False)              #DOIT
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()