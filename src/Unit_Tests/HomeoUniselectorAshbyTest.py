'''
Created on Mar 18, 2013

@author: stefano
'''
from   Core.HomeoUnit import *
from   Core.HomeoUniselectorAshby import *
from   Core.Homeostat import *
import scipy.stats as stats
import unittest, numpy
from copy import copy, deepcopy

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
        There must always be an integer positive number of steps in the uniselector
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
        Test that  the Uniselector produces a number of different sets of values
        
        The values produced should be all different and uniformly distributed 
        over the interval -1 , 1 (or -upperBound, upperBound, to be precise)
        '''
        self.uniselector.independentlyRandomized()
        expectedNumberOfValues = (self.uniselector.steps * 2 ) + 1 
        valuesProduced= []
        tests = 100
        
        for i in xrange(tests):
            values =  []
            for unit in xrange(self.uniselector.unitsControlled):
                values.append(self.uniselector.produceNewValue()) 
            valuesProduced.append(values)
            self.uniselector.advance()
        
        "Values are all different"
        allValues = numpy.array(valuesProduced).flatten()
                        
        ''''The transition matrix has  m = ((self.uniselector.steps * 2) + 1) rows and
        n = self._unitsControlled column. There must be m*n different values'''
        tempSet = set(allValues)
        self.assertTrue(len(set(allValues)) == ((self.uniselector.steps * 2) + 1) * self.uniselector.unitsControlled)
        
        '''And uniformly distributed over -upperBound,upperBound,
            We measure against a large sample drawn from a uniform distrib and set the p-value to 0.05'''
            
        uniformRandomSample = numpy.random.uniform(- self.uniselector.upperBound,self.uniselector.upperBound,10000)
        D,p = stats.ks_2samp(allValues,uniformRandomSample)
        self.assertTrue(p < 0.05)
        
        "Check that the we are producing values for all units controlled"
        for values in valuesProduced: 
            self.assertTrue(len(values) == self.uniselector.unitsControlled )
        
    def testRandomizedValuesMatrix(self):
        '''
        Test that the Uniselector produces a number of different sets of values
        equal to uniselector steps (which would  be  25 different sets of values, 
        as in Ashby's original implementation, with the default value of steps)
        
        There is only a fixed number of different values (default = 25)
        '''
        
        self.uniselector.randomized()
        expectedNumberOfValues = (self.uniselector.steps * 2 ) + 1 
        valuesProduced= []

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
        tempSet = set(allValues)
        self.assertTrue(len(set(allValues)) == expectedNumberOfValues)
        
        '''We cannot run a test such as:
        
        self.assertTrue(len(set(values)) == len(values)
        
        because values for different units cannot (necessarily) be all 
        different:  there are only 25 possible random values 
        (see comments to produceRandomizedSequence for more comments''' 
        
        "Check that the we are producing values for all units controlled"
        for values in valuesProduced: 
            self.assertTrue(len(values) == self.uniselector.unitsControlled)

    def testValuesWithinBounds(self):
        '''
        Checks that the Uniselector produces values 
        that are always between -upperBound (= -1)  and upperBound (= 1. 
        The upper and lower bounds of the UniselectorAshby cannot be changed"
        '''
        outOfBounds  = False
        tests = 1000
        valuesProduced = []
        for test in xrange(tests):
            values = []
            for unit in xrange(self.uniselector.unitsControlled): 
                values.append(self.uniselector.produceNewValue())
            valuesProduced.append(values)
            self.uniselector.advance()

        for valueSet in valuesProduced: 
            for value in valueSet:
                if not (value >= - self.uniselector.upperBound and value <= self.uniselector.upperBound):
                    outOfBounds = True
        
        self.assertFalse(outOfBounds)
        
    def testSameAs(self):
        '''
        True if they are of same class, have same ashbyKind, and have the same transition matrix
        '''
    
        "Copies should always be the same, no matter the matrix's computation method"
        self.uniselector.equallySpaced()
        anotherUniselector = copy(self.uniselector)
        
        self.assertTrue(self.uniselector.sameAs(anotherUniselector))
     
        self.uniselector.equallySpaced()
        anotherUniselector = copy(self.uniselector)
        self.assertTrue(self.uniselector.sameAs(anotherUniselector))
        
        self.uniselector.equallySpaced()
        anotherUniselector = copy(self.uniselector)
        self.assertTrue(self.uniselector.sameAs(anotherUniselector))

        '''Otherwise, two uniselectors will almost never be the same.
        Test that they will not be equal in  more than 5% of the cases'''
        anotherUniselector = HomeoUniselectorAshby()
        tests = 100
        equalityResults = 0
        deltaTests = int(tests * 0.05)
        for i in xrange(tests):
            anotherUniselector.equallySpaced()
            if self.uniselector.sameAs(anotherUniselector):
                equalityResults += 1
            anotherUniselector.independentlyRandomized()
            if self.uniselector.sameAs(anotherUniselector):
                equalityResults += 1
            anotherUniselector.randomized()
            if self.uniselector.sameAs(anotherUniselector):
                equalityResults += 1
        
        self.assertAlmostEquals(equalityResults, 0, delta = deltaTests)

        
    def testSameKindAs(self):
        '''
        True if they are of same class and have same ashbyKind
        '''
        
        anotherUniselector = HomeoUniselectorAshby()
        self.uniselector.independentlyRandomized()
        anotherUniselector.independentlyRandomized()
        
        self.assertTrue(self.uniselector.sameKindAs(anotherUniselector))
        
        anotherUniselector.equallySpaced()
        self.assertFalse(self.uniselector.sameKindAs(anotherUniselector))

        anotherUniselector.randomized() 
        self.assertFalse(self.uniselector.sameKindAs(anotherUniselector))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()