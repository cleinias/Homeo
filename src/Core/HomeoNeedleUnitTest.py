'''
Created on Mar 11, 2013

@author: stefano
'''
from  Core.HomeoNeedleUnit import *
import unittest


class HomeoNeedleUnitTest(unittest.TestCase):
    '''
    Unit tests for the HomeoNeedleUnit class, which simply holds
    the parameters needed to compute the movement of the needle
    in a HomeoUnit 
    '''


    def setUp(self):
        pass

    def testClassDefaults(self):
        """test that  the class has its appropriate dictionary of Defaults and that the values are not empty."""
        defParam = HomeoNeedleUnit.DefaultParameters  #HomeoUnit class variables with all the defaults values"


        self.assertTrue(defParam.has_key('mass'))
        self.assertTrue(defParam.has_key('surfaceArea'))
        self.assertTrue(defParam.has_key('dragCoefficient'))

        self.assertTrue(defParam['mass'] is not None)
        self.assertTrue(defParam['surfaceArea'] is not None)
        self.assertTrue(defParam['dragCoefficient'] is not None)
        
    
    def testNeedleUnitInstanceHasDefaultValues(self):
        '''
        Test that a HomeoNeedleUnit has values accessible with implicit getters and setters
        '''
        
        needleUnit = HomeoNeedleUnit()
        
        needleUnit.mass = 10
        needleUnit.dragCoefficient = 100
        needleUnit.surfaceArea = 10
        
        self.assertTrue(needleUnit.mass == 10)
        self.assertTrue(needleUnit.surfaceArea == 10)
        self.assertTrue(needleUnit.dragCoefficient == 100)
        
    def tearDown(self):
        pass




if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()