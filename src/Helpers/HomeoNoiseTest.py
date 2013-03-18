'''
Created on Mar 15, 2013

@author: stefano
'''
from   Core.HomeoUnit import HomeoUnit
from   HomeoUniselector import *
from   HomeoDataCollector import *
from   Homeostat import *
from   HomeoNoise import  *

import unittest,numpy
import scipy.stats as stats


class HomeoNoiseTest(unittest.TestCase):
    """
    Testing the application of noise to the HomeUnit and HomeConnections
    """

    def setUp(self):
        "Set up the test with a Homeostat unit and a noise object"

        self.unit = HomeoUnit()
        self.noise = HomeoNoise()

    def testDegradingConstantLinearNoise(self):
        """
        Degrading constant linear noise must
        - always have the same value (constant)
        - have a value equal to the unit's noise (linear)
        - always have opposite sign to the signal (unit's critical deviation) (degrading)
        """

        values = []
        self.unit.setRandomValues()
        tests = 100
        self.noise = HomeoNoise.newWithCurrentAndNoise(self.unit.criticalDeviation(), self.unit.noise())

        self.noise.constant() 
        self.noise.degrading() 
        self.noise.linear()

        for i in xrange(tests):
            values.append(self.noise.getNoise())
        values.sort()
        
        "As noise is constant, check sorted noises: first and last are both equal to unit's noise"
        self.assertTrue(len(values) == tests)
        self.assertTrue(numpy.sign(values[0]) == (numpy.sign(self.unit.criticalDeviation() * -1)))    # Noise is degrading the signal: opposite sign
        self.assertTrue(abs(values[0]) == self.unit.noise())
        self.assertTrue(abs(values[tests-1]) == (self.unit.noise()))


    def testDegradingConstantProportionalNoise(self):
        """
        Degrading constant proportional noise must
        - always have the same value (constant)
        - the value is equal to the unit's noise times its *value* (proportional)
        - always have opposite sign to the signal (unit's critical deviation) (degrading)
        """
       
        values = []
        self.unit.setRandomValues()
        tests = 100
        self.noise = HomeoNoise.newWithCurrentAndNoise(self.unit.criticalDeviation(), self.unit.noise())

        self.noise.constant() 
        self.noise.degrading() 
        self.noise.proportional()

        for i in xrange(tests):
            values.append(self.noise.getNoise())
        values.sort()


        self.assertTrue(len(values) == tests)
        self.assertTrue(numpy.sign(values[0]) == (numpy.sign(self.unit.criticalDeviation() * -1)))    # Noise is degrading the signal: opposite sign
        self.assertTrue(abs(values[0]) == (self.unit.noise() * abs(self.unit.criticalDeviation())))
        self.assertTrue(abs(values[tests-1]) == (self.unit.noise() * abs(self.unit.criticalDeviation())))

    def testDegradingNormalLinearNoise(self):
        """
        Degrading normal linear noise must:
        - be centered around a unit's noise (linear)
        - be normally distributed around a unit's noise (normal)
        - always have opposite sign to the signal (unit's critical deviation) (degrading)
        """    
        tests = 1000.
        signs = [] 
        values = []
        tolerance = 0.05
        self.unit.setRandomValues()

        self.noise = HomeoNoise.newWithCurrentAndNoise(self.unit.criticalDeviation(), self.unit.noise())
 
        self.noise.normal() 
        self.noise.degrading() 
        self.noise.linear()

        for index in xrange(tests):
            noiseValue = self.noise.getNoise()
            values.append(noiseValue)
            signs.append(numpy.sign(noiseValue))
        self.assertTrue(len(values) == tests)

        values.sort()
        signs.sort()
        
        "Check if noise's sign is always opposite to current's sign"
        for noiseValue in values:
            self.assertTrue(numpy.sign(noiseValue) == (numpy.sign(self.unit.criticalDeviation()) * -1) or 
                noiseValue == 0)
  
        "Check linearity by checking mean"
        mean = numpy.mean(values)
        self.assertTrue(mean >= (self.unit.noise() * (1 - tolerance) and
                                 mean <= self.unit.noise() * (1 + tolerance)))

        "check the distribution is confidently normal (p > 0.05)"
        k2,p =  stats.normaltest(values)  #D'Agostino-Pearson omnibus test
        self.assertTrue(p > 0.05)

    def testDegradingNormalProportionalNoise(self):
        """
        Noise Degrading Normal Proportional must be:
        - normally distributed around a unit's noise (normal)
        - always have opposite sign to the signal (unit's critical deviation) (degrading)
        - have a value proportional to the unit's value  (proportional)
        """
    
        tests = 1000.
        signs = [] 
        values = []
        tolerance = 0.05
        self.unit.setRandomValues()

        self.noise = HomeoNoise.newWithCurrentAndNoise(self.unit.criticalDeviation(), self.unit.noise())
 
        self.noise.normal() 
        self.noise.degrading() 
        self.noise.proportional()

        for index in xrange(tests):
            noiseValue = self.noise.getNoise()
            values.append(noiseValue)
            signs.append(numpy.sign(noiseValue))
        self.assertTrue(len(values) == tests)

        values.sort()
        signs.sort()

        "Check if noise's sign is always opposite to current's sign"
        for noiseValue in values:
            self.assertTrue((numpy.sign(noiseValue) == (numpy.sign(self.unit.criticalDeviation) * -1)) or (noiseValue == 0))


        "Check proportionality through the mean---should be unit's noise * unit's value (+/- tolerance) "
        mean = numpy.mean(values)
        self.assertTrue((mean >= (abs(self.unit.noise() * self.unit.criticalDeviation()) * (1 - tolerance))) and
                         (mean <= (abs(self.unit.noise() * self.unit.criticalDeviation()) * ( 1+ tolerance))))

        "check the distribution is confidently normal (p > 0.05)"
        k2,p =  stats.normaltest(values)  #D'Agostino-Pearson omnibus test
        self.assertTrue(p > 0.05)

    def testDegradingUniformLinearNoise(self):
        """
        Degrading uniform linear noise must be  
        - be centered around a unit's noise (linear)
        - be uniformly distributed around a unit's noise (uniform)
        - always have opposite sign to the signal (unit's critical deviation) (degrading)
        """
        tests = 1000.
        signs = [] 
        values = []
        tolerance = 0.05
        self.unit.setRandomValues()
        lowThreshold =  2 * (self.unit.noise()) * tolerance
        highThreshold = 2 * (self.unit.noise()) * (1 - tolerance)

        self.noise = HomeoNoise.newWithCurrentAndNoise(self.unit.criticalDeviation(), self.unit.noise())
 
        self.noise.uniform() 
        self.noise.degrading() 
        self.noise.linear()

        for index in xrange(tests):
            noiseValue = self.noise.getNoise()
            values.append(noiseValue)
            signs.append(numpy.sign(noiseValue))
        self.assertTrue(len(values) == tests)

        values.sort()
        signs.sort()

        "Degrading: Check if noise's sign is always opposite to current's sign"
        for noiseValue in values:
            self.assertTrue((numpy.sign(noiseValue) == (numpy.sign(self.unit.criticalDeviation) * -1)) or (noiseValue == 0))

        "Linearity: checks min and max values of noise values are within boundaries of distribution, i.e. 0 and 2*unit noise,   (with a tolerance)"
        if values[0]  > 0:
            minAbsNoise = abs(values[0])
            maxAbsNoise = abs(values[tests-1])
        else:
            minAbsNoise = abs(values[tests-1])
            maxAbsNoise = abs(values[0])
    
        self.assertTrue((minAbsNoise >= 0)  and
                         (minAbsNoise <= lowThreshold))
        self.assertTrue((maxAbsNoise <= (2 * self.unit.noise())) and
                        maxAbsNoise >= highThreshold) 

        "uniform: use Kolmogorov-Smirnov test with a p-value over 0.9"
        D,p = stats.kstest(values,'uniform')
        self.assertTrue(p > 0.9)
        
    def testDegradingUniformProportionalNoise(self):
        """
        Degrading uniform proportional noise must: 
        - always have opposite sign to the signal (unit's critical deviation) (degrading)
        - be uniformly distributed around a unit's noise (uniform)
        - have a value proportional to the unit's value  (proportional)
        """
        tests = 1000.
        signs = [] 
        values = []
        tolerance = 0.05
        self.unit.setRandomValues()
        lowThreshold =  2 * (self.unit.noise() * abs(self.unit.criticalDeviation())) * tolerance
        highThreshold = 2 * (self.unit.noise()* abs(self.unit.criticalDeviation())) * (1 - tolerance)

        self.noise = HomeoNoise.newWithCurrentAndNoise(self.unit.criticalDeviation(), self.unit.noise())
 
        self.noise.uniform() 
        self.noise.degrading() 
        self.noise.proportional()

        for index in xrange(tests):
            noiseValue = self.noise.getNoise()
            values.append(noiseValue)
            signs.append(numpy.sign(noiseValue))
        self.assertTrue(len(values) == tests)

        values.sort()
        signs.sort()

        "Degrading: Check if noise's sign is always opposite to current's sign"
        for noiseValue in values:
            self.assertTrue((numpy.sign(noiseValue) == (numpy.sign(self.unit.criticalDeviation) * -1)) or (noiseValue == 0))

        "Linear: checks min and max values of noise values are within boundaries of distribution, i.e. 0 and 2*unit noise,   (with a tolerance)"
        if values[0]  > 0:
            minAbsNoise = abs(values[0])
            maxAbsNoise = abs(values[tests-1])
        else:
            minAbsNoise = abs(values[tests-1])
            maxAbsNoise = abs(values[0])
    
        self.assertTrue((minAbsNoise >= 0)  and
                         (minAbsNoise <= lowThreshold))
        self.assertTrue((maxAbsNoise <= (2 * self.unit.noise())) and
                        maxAbsNoise >= highThreshold) 

        ''' Proportional: check if min and max values of noise values are 
            within boundaries of distribution, i.e:
            0 and 2*(unit noise/unit noise current abs) (with a tolerance)'''
        if values[0]  > 0:
            minAbsNoise = abs(values[0])
            maxAbsNoise = abs(values[tests-1])
        else:
            minAbsNoise = abs(values[tests-1])
            maxAbsNoise = abs(values[0])
    
        self.assertTrue((minAbsNoise >= 0)  and
                         (minAbsNoise <= lowThreshold))
        self.assertTrue((maxAbsNoise <= (2 * self.unit.noise())) and
                        maxAbsNoise >= highThreshold) 

        "uniform: use Kolmogorov-Smirnov test with a p-value over 0.9"
        D,p = stats.kstest(values,'uniform')
        self.assertTrue(p > 0.9)

    def testDistortingConstantLinearNoise(self):
        """
        Distorting constant linear noise must
        - always have the same value (constant)
        - have a value equal to the unit's noise (linear)
        - be distributed  *around* a unit's noise (approximately) (distorting)
        """
        tests = 1000.
        signs = [] 
        values = []
        tolerance = 0.05
        self.unit.setRandomValues()

        self.noise = HomeoNoise.newWithCurrentAndNoise(self.unit.criticalDeviation(), self.unit.noise())
 
        self.noise.constant() 
        self.noise.distorting() 
        self.noise.linear()

        for index in xrange(tests):
            noiseValue = self.noise.getNoise()
            values.append(noiseValue)
            signs.append(numpy.sign(noiseValue))
        self.assertTrue(len(values) == tests)

        values.sort()
        signs.sort()

        "distorting: test whether the sign of the noise value is about 50% of the times positive and 50% negative. Chooses 'tolerance' as  threshold"
        positives =  filter(lambda sign: sign == 1, signs)
        self.assertTrue((positives / (len(signs) / 2) >= (1 - tolerance)) and
                        ((positives / len(signs / 2)) <= (1 + tolerance)))

        "constant and linear: the noise produced is always equal to a unit's noise"
        self.assertTrue(abs(values[0])  == self.unit.noise())
        self.assertTrue(abs(values[tests-1]) == self.unit.noise())

    def testDistortingConstantProportionalNoise(self):
        """
        Distorting constant proportional noise must
        - always have the same value (constant)
        - have a value proportional to the unit's value  (proportional)
        - be distributed  *around* a unit's noise (approximately) (distorting)
        """
        tests = 1000.
        signs = [] 
        values = []
        tolerance = 0.05
        self.unit.setRandomValues()

        self.noise = HomeoNoise.newWithCurrentAndNoise(self.unit.criticalDeviation(), self.unit.noise())
 
        self.noise.constant() 
        self.noise.distorting() 
        self.noise.proportional()

        for index in xrange(tests):
            noiseValue = self.noise.getNoise()
            values.append(noiseValue)
            signs.append(numpy.sign(noiseValue))
        self.assertTrue(len(values) == tests)

        values.sort()
        signs.sort()
    
        "distorting: test whether the sign of the noise value is about 50% of the times positive and 50% negative. Choose 'tolerance' as  threshold"
        positives =  filter(lambda sign: sign == 1, signs)
        self.assertTrue((positives / (len(signs) / 2) >= (1 - tolerance)) and
                        ((positives / len(signs / 2)) <= (1 + tolerance)))

        "constant and proportional: the absolute value of noise is  always equal to unit's noise times unit's value"
        self.assertTrue(abs(values[0])  == self.unit.noise() * self.unit.criticalDeviation())
        self.assertTrue(abs(values[tests-1]) == self.unit.noise() * self.unit.criticalDeviation())

    def testDistortingNormalLinearNoise(self):
        """
        Distorting normal linear noise must
        - normally distributed around a unit's noise (normal)
        - have a value related to the unit's noise (linear)
        - be distributed  *around* a unit's noise (approximately) (distorting)
        """
        tests = 1000.
        values = []
        tolerance = 0.05
        self.unit.setRandomValues()

        self.noise = HomeoNoise.newWithCurrentAndNoise(self.unit.criticalDeviation(), self.unit.noise())
 
        self.noise.normal() 
        self.noise.distorting() 
        self.noise.linear()

        for index in xrange(tests):
            noiseValue = self.noise.getNoise()
            values.append(noiseValue)
        self.assertTrue(len(values) == tests)

        values.sort()


        minAbsNoise = abs(values[0]) 
        maxAbsNoise = abs(values[tests-1])
        mean = numpy.mean(values)

        "Distorting: mean is around 0 (plus or minus tolerance)"
        self.assertTrue((mean >= (0 -  tolerance)) and
                        ((mean <= (0 + tolerance))))


        "Linear:  all values within {-noise, +noise} interval"
        self.assertTrue((minAbsNoise >= - self.unit.noise())  and
                        (maxAbsNoise <= self.unit.noise()))

        "Normal: check the distribution is confidently normal (p > 0.05)"
        k2,p =  stats.normaltest(values)  #D'Agostino-Pearson omnibus test
        self.assertTrue(p > 0.05)

    def testDistortingNormalProportionalNoise(self):
        """
        Distorting normal proportional noise must
        - normally distributed around a unit's noise (normal)
        - have a value proportional to the unit's value  (proportional)
        - be distributed  *around* a unit's noise (approximately) (distorting)
        """
        tests = 1000.
        values = []
        tolerance = 0.05
        self.unit.setRandomValues()

        self.noise = HomeoNoise.newWithCurrentAndNoise(self.unit.criticalDeviation(), self.unit.noise())
 
        self.noise.normal() 
        self.noise.distorting() 
        self.noise.proportional()

        for index in xrange(tests):
            noiseValue = self.noise.getNoise()
            values.append(noiseValue)
        self.assertTrue(len(values) == tests)

        values.sort()

        minNoise = values[0]
        maxNoise = values [tests-1]
        mean = numpy.mean(values)

        "Distorting: mean is around 0 (plus or minus tolerance)"
        self.assertTrue((mean >= (0 -  tolerance)) and
                        ((mean <= (0 + tolerance))))

        "Proportional: all values within {(current * -noise), (current * noise} interval"
        self.assertTrue(minNoise >= ( - (self.unit.noise()) * abs(self.unit.criticalDeviation()))  and
                        (maxNoise <= (self.unit. noise() * abs(self.unit.criticalDeviation()))))

        "Normal: check the distribution is confidently normal (p > 0.05)"
        k2,p =  stats.normaltest(values)  #D'Agostino-Pearson omnibus test
        self.assertTrue(p > 0.05)

    def testDistortingUniformProportionalNoise(self):
        """
        Distorting uniform proportional noise must
        - uniformly  distributed around a unit's noise *times* unit's value (uniform)
        - have a value proportional to the unit's value  (proportional)
        - be distributed  *around* a unit's noise *times* a unit's value (approximately) (distorting)
        """
        tests = 1000.
        values = []
        tolerance = 0.05
        self.unit.setRandomValues()

        self.noise = HomeoNoise.newWithCurrentAndNoise(self.unit.criticalDeviation(), self.unit.noise())
 
        self.noise.uniform() 
        self.noise.distorting() 
        self.noise.proportional()

        for index in xrange(tests):
            noiseValue = self.noise.getNoise()
            values.append(noiseValue)
        self.assertTrue(len(values) == tests)

        values.sort()

        minNoise = values[0]
        maxNoise = values [tests-1]
        mean = numpy.mean(values)

        "Distorting: mean is around 0 (plus or minus tolerance)"
        self.assertTrue((mean >= (0 -  tolerance)) and
                        ((mean <= (0 + tolerance))))

        "Proportional: all values within {(current * -noise), (current * noise} interval"
        self.assertTrue(minNoise >= ( - (self.unit.noise()) * abs(self.unit.criticalDeviation()))  and
                        (maxNoise <= (self.unit. noise() * abs(self.unit.criticalDeviation()))))

        "Uniform: use Kolmogorov-Smirnov test with a p-value over 0.9"
        D,p = stats.kstest(values,'uniform')
        self.assertTrue(p > 0.9)
            
    def testDistortingUniformLinearNoise(self):
        """
        Distorting uniform linear noise must
        - have a value related to the unit's noise (linear)
        - be uniformly distributed around a unit's noise (uniform)
        - be distributed around a unit's noise (distorting) 
        """
        tests = 1000.
        values = []
        tolerance = 0.05
        self.unit.setRandomValues()

        self.noise = HomeoNoise.newWithCurrentAndNoise(self.unit.criticalDeviation(), self.unit.noise())
 
        self.noise.uniform() 
        self.noise.distorting() 
        self.noise.linear()

        for index in xrange(tests):
            noiseValue = self.noise.getNoise()
            values.append(noiseValue)
        self.assertTrue(len(values) == tests)

        values.sort()

        minNoise = values[0]
        maxNoise = values [tests-1]
        mean = numpy.mean(values)

        "Distorting: mean is around 0 (plus or minus tolerance)"
        self.assertTrue((mean >= (0 -  tolerance)) and
                        ((mean <= (0 + tolerance))))

        "Linear: all values within {-noise,  noise} interval"
        self.assertTrue(minNoise >= ( - self.unit.noise())  and
                        maxNoise <= self.unit. noise())

        "Uniform: use Kolmogorov-Smirnov test with a p-value over 0.9"
        D,p = stats.kstest(values,'uniform')
        self.assertTrue(p > 0.9)

    def tearDown(self):
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()