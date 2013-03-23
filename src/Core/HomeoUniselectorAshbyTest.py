'''
Created on Mar 18, 2013

@author: stefano
'''
from   HomeoUnit import *
from   HomeoUniselectorAshby import *
from   Homeostat import *
import unittest, numpy


class HomeoUniselectorAshbyTest(unittest.TestCase):
    '''
    Unit tests for the revised HomeoUniselectorAshby class. See class comments for a detailed description
    '''

    def setUp(self):
        self.uniselector = HomeoUniselectorAshby()

    def testDefaultSteps(self):
        '''
        Test Asby's original implementation's value: it must be 12, 
        because Ashby had 25 steps overall, and we assume
        12 positive values, 0, and 12 negative values
        '''
        self.assertTrue(self.uniselector.steps == 12)

    def testStep(self):
        '''
        There must always be am integer positive number of steps in the uniselector
        '''
        self.assertTrue(self.uniselector.steps > 0)

        for index in xrange(100):
            self.uniselector.steps = numpy.random.uniform(-100,100)
            self.assertTrue(self.uniselector.steps >  0)
            self.assertTrue(isinstance(self.uniselector.steps, (int, long)))

    def testIntervalBounds(self):
        '''
        A Uniselector's intervals are always 0 and 1, 
        no matter which computation method is used
        '''

        self.uniselector.equallySpaced()
        for index in xrange(100):
            self.uniselector.lowerBound = numpy.random.uniform(-10,10)
            self.assertTrue(self.uniselector.lowerBound == 0)
            self.uniselector.upperBound = numpy.random.uniform(-10,10)
            self.assertTrue(self.uniselector.upperBound == 1)

        self.uniselector.independentlyRandomized()
        for index in xrange(100):
            self.uniselector.lowerBound = numpy.random.uniform(-10,10)
            self.assertTrue(self.uniselector.lowerBound == 0)
            self.uniselector.upperBound = numpy.random.uniform(-10,10)
            self.assertTrue(self.uniselector.upperBound == 1)

        self.uniselector.randomized()        
        for index in xrange(100):
            self.uniselector.lowerBound = numpy.random.uniform(-10,10)
            self.assertTrue(self.uniselector.lowerBound == 0)
            self.uniselector.upperBound = numpy.random.uniform(-10,10)
            self.assertTrue(self.uniselector.upperBound == 1)


    def testProduceSound(self):
        '''
        Uniselector produces a sound when toggleBeeping is toggled.
        Not really an automated unit test --- needs someone to hear it
        Will change to a more refined test when sound component (Osc/SuperCollider) is added
        '''
        for index in xrange(2):
            self.uniselector.produceNewValue()
            self.uniselector.advance()

        self.uniselector.toggleBeeping()
        for index in xrange(2):
            self.uniselector.produceNewValue()
            self.uniselector.advance

    def testEquallySpacedValuesMatrix(self):
        '''
        checks that the Uniselector produces a number of different sets of values
        equal to uniselector steps (which would  be  sets of 25 different values, 
        as in Ashby's original implementation, with the default value of steps)
        '''
        self.uniselector.equallySpaced()
        expectedNumberOfValues = (self.uniselector.steps * 2 ) + 1 
        valuesProduced =  []

        for i in xrange(1000):
            values =  []
            for unit in xrange(self.uniselector.unitsControlled):
                values.append(self.uniselector.produceNewValue()) 
            valuesProduced.append(values)
            self.uniselector.advance()

        "Test that we have only 25 different values"
        allValues = [] 
        for values in valuesProduced:
            allValues.extend(values)
    
        uniqueSortedValues = sorted(list(set(allValues)))
        self.assertTrue(len(uniqueSortedValues) == expectedNumberOfValues)

        "Check that the values are equally spaced"
        deltas = []
        for value in xrange(len(uniqueSortedValues) , 1, -1):
            deltas.append(round(uniqueSortedValues[value-1] - uniqueSortedValues[value - 2], 7) )
        setDeltas = set(deltas)
        self.assertTrue(len(set(deltas)) == 1)
        
        '''We cannot run a test such as:
        
        self.assertTrue(len(set(values)) == len(values)
        
        because values for different units cannot (necessarily) be all 
        different:  there are only 25 possible random values 
        (see comments to produceRandomizedSequence for more comments''' 
        
        for values in valuesProduced: 
            self.assertTrue(len(values) == self.uniselector.unitsControlled )

    def testIndependentlyRandomizedValuesMatrix(self):
        '''
        checks that  the Uniselector produces a number of different sets of values
        equal to uniselector steps (which would  be  25 different sets of values, 
        as in Ashby's original implementation, with the default value of steps)
        
        FIXME: Does not actually test the computation method
        '''
        self.uniselector.independentlyRandomized()
        expectedNumberOfValues = (self.uniselector.steps() * 2 ) + 1 
        valuesProduced= []

        for i in xrange(1000):
            values =  []
            for unit in self.uniselector.unitsControlled():
                values.append(self.uniselector.produceNewValue()) 
            valuesProduced.append(values)
            self.uniselector.advance()

        self.assertTrue(len(set(valuesProduced)) == expectedNumberOfValues)
        
        '''We cannot run a test such as:
        
        self.assertTrue(len(set(values)) == len(values)
        
        because values for different units cannot (necessarily) be all 
        different:  there are only 25 possible random values 
        (see comments to produceRandomizedSequence for more comments''' 
        
        for values in valuesProduced: 
            self.assertTrue(len(values) == self.uniselector.unitsControlled())
        
    def testRandomizedValuesMatrix(self):
        '''
        Check that the Uniselector produces a number of different sets of values
        equal to uniselector steps (which would  be  25 different sets of values, 
        as in Ashby's original implementation, with the default value of steps)
        
        FIXME: Does not actually test the computation method 
        '''
        
        self.uniselector.randomized()
        expectedNumberOfValues = (self.uniselector.steps() * 2 ) + 1 
        valuesProduced= []

        for i in xrange(1000):
            values =  []
            for unit in self.uniselector.unitsControlled():
                values.append(self.uniselector.produceNewValue()) 
            valuesProduced.append(values)
            self.uniselector.advance()
       
        "Test that we have only 25 different values"
        allValues = [] 
        for values in valuesProduced:
            allValues.extend(values)
    
        self.assertTrue(len(set(allValues)) == expectedNumberOfValues)
        
        '''We cannot run a test such as:
        
        self.assertTrue(len(set(values)) == len(values)
        
        because values for different units cannot (necessarily) be all 
        different:  there are only 25 possible random values 
        (see comments to produceRandomizedSequence for more comments''' 
        
        "Check that the we are producing values for all units controlled"
        for values in valuesProduced: 
            self.assertTrue(len(values) == self.uniselector.unitsControlled())

    def testValuesWithinBounds(self):
        '''
        Checks that the Uniselector produces values 
        that are always between the upper and lower bounds
        '''
        outOfBounds  = 1000
        tests = 1000
        valuesProduced = []
        for test in xrange(tests):
            values = []
            for unit in self.uniselector.unitsControlled(): 
                values.append(self.uniselector.produceNewValue())
            valuesProduced.append(values)
            self.uniselector.advance()

        for valueSet in valuesProduced: 
            for value in valueSet:
                if not (value >= self.uniselector.lowerBound() and value <= self.uniselector.upperBound()):
                    outOfBounds = 1
        
        self.assertTrue(outOfBounds == 1)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()