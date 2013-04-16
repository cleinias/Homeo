'''
Created on Mar 11, 2013

@author: stefano

'''
from   Core.HomeoUniselector import *
from   Helpers.General_Helper_Functions import *

import unittest, string, random


class HomeoUniselectorTest(unittest.TestCase):


    def setUp(self):
        self.uniselector = HomeoUniselector()

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
            self.assertTrue(HomeoUniselector.includesType(currentClass))
        for bogusClass in bogusClasses:
            self.assertFalse(HomeoUniselector.includesType(bogusClass))

    def testIntervalBounds(self):
        """
        Test that HomeoUniselector has a positive interval
        """
        self.assertTrue((self.uniselector.upperBound - self.uniselector.lowerBound) >= 0)
                        
    def testHomeoUniselectorTriggered(self):
        """
        Cannot test that HomeoUniselector is activated when its input exceeds the normal bounds:
        it is a HomeoUnit's responsibility to do so. HomeoUniselector only returns values when called 
        """
        self.assertTrue(True)              
        
    def testHomeoUniselectorIsAbstractClass(self):
        '''
        The core method of HomeUniselector is advance, which is only defined in its subclasses
        '''
        self.assertRaises(SubclassResponsibility, self.uniselector.advance)
        
    def testBasicAshbyRandom(self):
        '''
        Test the basic Ashbian mechanism of returning a random value equal to 1/25
        of the interval between upperBound and lowerBound
        '''
        interval = self.uniselector.upperBound - self.uniselector.lowerBound
        for i in xrange(1000):
            value = self.uniselector.ashbyRandom()
            self.assertAlmostEqual(abs(value),interval/25,delta = 0.0001)
        
if __name__ == "__main__":
    unittest.main()