'''
Created on Mar 15, 2013

@author: stefano
'''
from   Core.HomeoUnit import HomeoUnit
from   Helpers.HomeoNoise import HomeoNoise

import scipy.stats as stats
import unittest,numpy

class HomeoNoiseTest(unittest.TestCase):
    """
    Testing the application of noise to HomeUnits and HomeConnections
    """

    def setUp(self):
        "Set up the test with a Homeostat unit and a noise object"

        self.unit = HomeoUnit()
        self.unit.setRandomValues()
        self.noise = HomeoNoise()
        
        modes = ['Distorting', 'Degrading']
        distributions = ['Constant', 'Uniform', 'Normal']
        ratios =  ['Linear', 'Proportional']
        self.noiseAlgs = []
        for mode in modes:
            for distribution in distributions:
                for ratio in ratios:
                    self.noiseAlgs.append('getNoise' + mode + distribution + ratio)

    def testAllAlgorithmsWithZeroNoise(self):
        '''Check that the basic method of HomeoNoise---getNoise()---can still 
           produce values when a unit's noise = 0'''
                        
        self.unit.noise = 0
        self.unit.criticalDeviation = 0.5
        self.noise = HomeoNoise()
        self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)

        for noiseAlg in self.noiseAlgs:
            try:
                producedNoise =  getattr(self.noise, noiseAlg)()   # raises an exception if something goes wrong
            except:
                self.assertTrue(False, ('Exception raised while running method: ' + noiseAlg))
            
    def testAllAlgorithmsWithZeroCurrent(self):
        '''Check that the basic method of HomeoNoise---getNoise()---can still 
           produce values when a unit's current = 0'''

        self.unit.noise = 0.5
        self.unit.criticalDeviation = 0
        self.noise = HomeoNoise()
        self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        
        for noiseAlg in self.noiseAlgs:
            try:
                producedNoise =  getattr(self.noise, noiseAlg)()   # raises an exception if something goes wrong
            except:
                self.assertTrue(False, ('Exception raised while running method: ' + noiseAlg))
        
    def testAllAlgorithmsWithZeroNoiseAndZeroCurrent(self):
        '''Check that the basic method of HomeoNoise---getNoise()---can still 
           produce values when *both* a unit's current and a unit's noise = 0'''

        self.unit.noise = 0
        self.unit.criticalDeviation = 0
        self.noise = HomeoNoise()
        self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)

        for noiseAlg in self.noiseAlgs:
            try:
                producedNoise =  getattr(self.noise, noiseAlg)()   # raises an exception if something goes wrong
            except:
                self.assertTrue(False, ('Exception raised while running method: ' + noiseAlg))
   
    def testDegradingConstantLinearNoise(self):
        """
        Degrading constant linear noise must
        - always have the same value (constant)
        - have a value equal to the unit's noise (linear)
        - always have opposite sign to the signal (unit's critical deviation) (degrading),
          unless the unit's critical deviation = 0, in which case the sign is -1
        """

        values = []
        self.unit.setRandomValues()
        self.unit.selfUpdate()
        tests = 100
        self.noise = HomeoNoise()
        self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)

        self.noise.constant() 
        self.noise.degrading() 
        self.noise.linear()

        for i in range(tests):
            values.append(self.noise.getNoise())
        values.sort()
        
        "As noise is constant, check sorted noises: first and last are both equal to unit's noise"
        self.assertTrue(len(values) == tests)
        self.assertTrue(numpy.sign(values[0]) == (numpy.sign(self.unit.criticalDeviation * -1)))    # Noise is degrading the signal: opposite sign
        self.assertTrue(abs(values[0]) == self.unit.noise)
        self.assertTrue(abs(values[tests-1]) == self.unit.noise)
        
        '''Check behavior for zero values
           When noise = 0, return zero
           When current = 0, return -noise
           When both are zero, return 0'''
        
        self.unit.noise = 0
        self.unit._criticalDeviation = 0.5
        self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        producedNoise = self.noise.getNoise()
        self.assertTrue(producedNoise == 0)
        
        self.unit.noise = 0.5
        self.unit._criticalDeviation = 0
        self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        producedNoise = self.noise.getNoise()
        self.assertTrue(producedNoise == -0.5)
        
        self.unit.noise = 0
        self.unit._criticalDeviation = 0
        self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        producedNoise = self.noise.getNoise()
        self.assertTrue(producedNoise == 0)



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
        self.noise = HomeoNoise()
        self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)

        self.noise.constant() 
        self.noise.degrading() 
        self.noise.proportional()

        for i in range(tests):
            values.append(self.noise.getNoise())
        values.sort()


        self.assertTrue(len(values) == tests)
        self.assertTrue(numpy.sign(values[0]) == (numpy.sign(self.unit.criticalDeviation * -1)))    # Noise is degrading the signal: opposite sign
        self.assertTrue(abs(values[0]) == (self.unit.noise * abs(self.unit.criticalDeviation)))
        self.assertTrue(abs(values[tests-1]) == (self.unit.noise * abs(self.unit.criticalDeviation)))

        
        '''Check behavior for zero values
           When noise = 0, return zero
           When current = 0, return -noise
           When both are zero, return 0'''
         
        self.unit.noise = 0
        self.unit._criticalDeviation = 0.5
        self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        producedNoise = self.noise.getNoise()
        self.assertTrue(producedNoise == 0)
        
        self.unit.noise = 0.5
        self.unit._criticalDeviation = 0
        self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        producedNoise = self.noise.getNoise()
        self.assertTrue(producedNoise == -0.5)
        
        self.unit.noise = 0
        self.unit._criticalDeviation = 0
        self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        producedNoise = self.noise.getNoise()
        self.assertTrue(producedNoise == 0)

    def testDegradingNormalLinearNoise(self):
        """
        Degrading normal linear noise must:
        - be centered around a unit's noise (linear)
        - be normally distributed around a unit's noise (normal)
        - always have opposite sign to the signal (unit's critical deviation) (degrading)
        """    
        tests = 1000
        signs = [] 
        values = []
        tolerance = 0.05
        self.unit.setRandomValues()

        self.noise = HomeoNoise()
        self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
 
        self.noise.normal() 
        self.noise.degrading() 
        self.noise.linear()

        for index in range(tests):
            noiseValue = self.noise.getNoise()
            values.append(noiseValue)
            signs.append(numpy.sign(noiseValue))
        self.assertTrue(len(values) == tests)

        values.sort()
        signs.sort()
        
        "Check if noise's sign is always opposite to current's sign"
        for noiseValue in values:
            self.assertTrue(numpy.sign(noiseValue) == (numpy.sign(self.unit.criticalDeviation) * -1) or 
                noiseValue == 0)
  
        "Check linearity by checking the absolute value of mean"
        absMean = abs(numpy.mean(values))
        self.assertTrue(absMean >= (self.unit.noise * (1 - tolerance)) and
                        absMean <= (self.unit.noise * (1 + tolerance)))

        "check the distribution is confidently normal (p > 0.05)"
        k2,p =  stats.normaltest(values)  #D'Agostino-Pearson omnibus test
        self.assertTrue(p > 0.05)

        
#===============================================================================
#        '''Check behavior for zero values
#           When noise = 0, return zero
#           When current = 0, return normal value centered on -noise
#           When both are zero, return 0'''
#         
#        self.unit.noise = 0
#        self.unit._criticalDeviation = 0.5
#        self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
#        producedNoise = self.noise.getNoise()
#        self.assertTrue(producedNoise == 0)
# 
#        self.unit.noise = 0.5
#        self.unit._criticalDeviation = 0
#        self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
#        producedNoise = self.noise.getNoise()
#        self.assertTrue(producedNoise == -0.5)
# 
#        self.unit.noise = 0
#        self.unit._criticalDeviation = 0
#        self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
#        producedNoise = self.noise.getNoise()
#        self.assertTrue(producedNoise == 0)
#===============================================================================

    def testDegradingNormalProportionalNoise(self):
        """
        Noise Degrading Normal Proportional must be:
        - normally distributed around a unit's noise (normal)
        - always have opposite sign to the signal (unit's critical deviation) (degrading)
        - have a value proportional to the unit's value  (proportional)
        """
    
        tests = 1000
        signs = [] 
        values = []
        tolerance = 0.05
        self.unit.setRandomValues()

        self.noise = HomeoNoise()
        self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
 
        self.noise.normal() 
        self.noise.degrading() 
        self.noise.proportional()

        for index in range(tests):
            noiseValue = self.noise.getNoise()
            values.append(noiseValue)
            signs.append(numpy.sign(noiseValue))
        self.assertTrue(len(values) == tests)

        values.sort()
        signs.sort()

        "Check if noise's sign is always opposite to current's sign"
        for noiseValue in values:
            self.assertTrue((numpy.sign(noiseValue) == (numpy.sign(self.unit.criticalDeviation) * -1)) or (noiseValue == 0))


        "Check proportionality through the absolute value of the mean---should be the absolute value of a unit's noise * unit's criticalDev (+/- tolerance) "
        absMean = abs(numpy.mean(values))
        self.assertTrue(absMean >= ((abs(self.unit.noise * self.unit.criticalDeviation)) * (1 - tolerance)) and
                        absMean <= ((abs(self.unit.noise * self.unit.criticalDeviation)) * (1 + tolerance)))

        "check the distribution is confidently normal (p > 0.05)"
        k2,p =  stats.normaltest(values)  #D'Agostino-Pearson omnibus test
        self.assertTrue(p > 0.05)
        #=======================================================================
        #          TODO (Fix expected behavior first)
        #'''Check behavior for zero values
        #   When noise = 0, return zero
        #   When current = 0, return -noise
        #   When both are zero, return 0'''
        # 
        # self.unit.noise = 0
        # self.unit._criticalDeviation = 0.5
        # self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        # producedNoise = self.noise.getNoise()
        # self.assertTrue(producedNoise == 0)
        # 
        # self.unit.noise = 0.5
        # self.unit._criticalDeviation = 0
        # self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        # producedNoise = self.noise.getNoise()
        # self.assertTrue(producedNoise == -0.5)
        # 
        # self.unit.noise = 0
        # self.unit._criticalDeviation = 0
        # self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        # producedNoise = self.noise.getNoise()
        # self.assertTrue(producedNoise == 0)
        #=======================================================================

    def testDegradingUniformLinearNoise(self):
        """
        Degrading uniform linear noise must be  
        - be centered around a unit's noise (linear)
        - be uniformly distributed around a unit's noise (uniform)
        - always have opposite sign to the signal (unit's critical deviation) (degrading)
        """
        tests = 1000
        signs = [] 
        values = []
        tolerance = 0.05
        self.unit.setRandomValues()
        lowThreshold =  2 * (self.unit.noise) * tolerance
        highThreshold = 2 * (self.unit.noise) * (1 - tolerance)

#        "FIXME for debugging"
#        self.unit.noise = 1
#        "End debugging"
        self.noise = HomeoNoise()
        self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
 
        self.noise.uniform() 
        self.noise.degrading() 
        self.noise.linear()

        for index in range(tests):
            noiseValue = self.noise.getNoise()
            values.append(noiseValue)
            signs.append(numpy.sign(noiseValue))
        self.assertTrue(len(values) == tests)

        values.sort()
        signs.sort()

        "Degrading: Check if noise's sign is always opposite to current's sign"
        for noiseValue in values:
            self.assertTrue((numpy.sign(noiseValue) == (numpy.sign(self.unit.criticalDeviation) * -1)) or (noiseValue == 0))

        "Linearity: checks if min and max values of noise values are within boundaries of distribution, i.e. 0 and 2*unit noise (with a tolerance)"
        if values[0]  > 0:
            minAbsNoise = abs(values[0])
            maxAbsNoise = abs(values[tests-1])
        else:
            minAbsNoise = abs(values[tests-1])
            maxAbsNoise = abs(values[0])
    
        self.assertTrue(minAbsNoise >= 0  and
                        maxAbsNoise <= (2 * self.unit.noise))

        "uniform: use 2-sample Kolmogorov-Smirnov test against a uniform distribution with a p-value > 0.05"
        if values[0] < 0:
            uniformRandomSample = numpy.random.uniform(-2 * self.unit.noise,0,10000)
        else:
            uniformRandomSample = numpy.random.uniform(0, 2 * self.unit.noise,10000)
        D,p = stats.ks_2samp(values,uniformRandomSample)
        self.assertTrue(p > 0.05)

        #=======================================================================
        #          TODO (Fix expected behavior first)
        #'''Check behavior for zero values
        #   When noise = 0, return zero
        #   When current = 0, return -noise
        #   When both are zero, return 0'''
        # 
        # self.unit.noise = 0
        # self.unit._criticalDeviation = 0.5
        # self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        # producedNoise = self.noise.getNoise()
        # self.assertTrue(producedNoise == 0)
        # 
        # self.unit.noise = 0.5
        # self.unit._criticalDeviation = 0
        # self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        # producedNoise = self.noise.getNoise()
        # self.assertTrue(producedNoise == -0.5)
        # 
        # self.unit.noise = 0
        # self.unit._criticalDeviation = 0
        # self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        # producedNoise = self.noise.getNoise()
        # self.assertTrue(producedNoise == 0)
        #=======================================================================
        
    def testDegradingUniformProportionalNoise(self):
        """
        Degrading uniform proportional noise must: 
        - always have opposite sign to the signal (unit's critical deviation) (degrading)
        - be uniformly distributed around a unit's noise (uniform)
        - have a value proportional to the unit's value  (proportional)
        """
        tests = 1000
        signs = [] 
        values = []
        tolerance = 0.05
        self.unit.setRandomValues()
        lowThreshold =  2 * (self.unit.noise * abs(self.unit.criticalDeviation)) * tolerance
        highThreshold = 2 * (self.unit.noise* abs(self.unit.criticalDeviation)) * (1 - tolerance)

#        "FIXME for debugging"
#        self.unit.noise = 1
#        "End debugging"
        
        self.noise = HomeoNoise()
        self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
 
        self.noise.uniform() 
        self.noise.degrading() 
        self.noise.proportional()

        for index in range(tests):
            noiseValue = self.noise.getNoise()
            values.append(noiseValue)
            signs.append(numpy.sign(noiseValue))
        self.assertTrue(len(values) == tests)

        values.sort()
        signs.sort()

        "Degrading: Check if noise's sign is always opposite to current's sign"
        for noiseValue in values:
            self.assertTrue((numpy.sign(noiseValue) == (numpy.sign(self.unit.criticalDeviation) * -1)) or (noiseValue == 0))

        ''' Proportional: check if min and max values of noise values are 
            within boundaries of distribution, i.e:
            0 and 2*(unit noise/unit current abs) '''
        if values[0]  > 0:
            minAbsNoise = abs(values[0])
            maxAbsNoise = abs(values[tests-1])
        else:
            minAbsNoise = abs(values[tests-1])
            maxAbsNoise = abs(values[0])
    
        self.assertTrue(minAbsNoise >= 0  and
                        maxAbsNoise <= (2 * self.unit.noise / abs(self.unit.criticalDeviation)))

        "uniform: use 2-sample Kolmogorov-Smirnov test against a uniform distribution with a p-value > 0.05"
        if values[0] < 0:
            uniformRandomSample = numpy.random.uniform(-2 * self.unit.noise * abs(self.unit.criticalDeviation),0,10000)
        else:
            uniformRandomSample = numpy.random.uniform(0, 2 * self.unit.noise * abs(self.unit.criticalDeviation),10000)
        D,p = stats.ks_2samp(values,uniformRandomSample)
        self.assertTrue(p > 0.05)

        #=======================================================================
        #          TODO (Fix expected behavior first)
        #'''Check behavior for zero values
        #   When noise = 0, return zero
        #   When current = 0, return -noise
        #   When both are zero, return 0'''
        # 
        # self.unit.noise = 0
        # self.unit._criticalDeviation = 0.5
        # self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        # producedNoise = self.noise.getNoise()
        # self.assertTrue(producedNoise == 0)
        # 
        # self.unit.noise = 0.5
        # self.unit._criticalDeviation = 0
        # self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        # producedNoise = self.noise.getNoise()
        # self.assertTrue(producedNoise == -0.5)
        # 
        # self.unit.noise = 0
        # self.unit._criticalDeviation = 0
        # self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        # producedNoise = self.noise.getNoise()
        # self.assertTrue(producedNoise == 0)
        #=======================================================================

    def testDistortingConstantLinearNoise(self):
        """
        Distorting constant linear noise must
        - always have the same value (constant)
        - have a value equal to the unit's noise (linear)
        - be distributed  *around* a unit's noise (approximately) (distorting)
        """
        tests = 1000
        signs = [] 
        values = []
        self.unit.setRandomValues()

        self.noise = HomeoNoise()
        self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
 
        self.noise.constant() 
        self.noise.distorting() 
        self.noise.linear()

        for index in range(tests):
            noiseValue = self.noise.getNoise()
            values.append(noiseValue)
            signs.append(numpy.sign(noiseValue))
        self.assertTrue(len(values) == tests)

        values.sort()
        signs.sort()

        '''distorting: test whether the sign of the noise value is about 50% of the times positive and 50% negative.
           Use binomial test with standard significance value of 0.05. This test will fail about 5% of the times...'''
        positives =  len(list(filter(lambda sign: sign == 1, signs)))
        self.assertTrue(stats.binomtest(positives, tests, 0.5).pvalue > 0.05)

        "constant and linear: the noise produced is always equal to a unit's noise"
        self.assertTrue(abs(values[0])  == self.unit.noise)
        self.assertTrue(abs(values[tests-1]) == self.unit.noise)

        #=======================================================================
        #          TODO (Fix expected behavior first)
        #'''Check behavior for zero values
        #   When noise = 0, return zero
        #   When current = 0, return -noise
        #   When both are zero, return 0'''
        # 
        # self.unit.noise = 0
        # self.unit._criticalDeviation = 0.5
        # self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        # producedNoise = self.noise.getNoise()
        # self.assertTrue(producedNoise == 0)
        # 
        # self.unit.noise = 0.5
        # self.unit._criticalDeviation = 0
        # self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        # producedNoise = self.noise.getNoise()
        # self.assertTrue(producedNoise == -0.5)
        # 
        # self.unit.noise = 0
        # self.unit._criticalDeviation = 0
        # self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        # producedNoise = self.noise.getNoise()
        # self.assertTrue(producedNoise == 0)
        #=======================================================================

    def testDistortingConstantProportionalNoise(self):
        """
        Distorting constant proportional noise must
        - always have the same value (constant)
        - have a value proportional to the unit's value (proportional)
        - be distributed  *around* a unit's noise (approximately) (distorting)
        """
        tests = 1000
        signs = [] 
        values = []
        self.unit.setRandomValues()

        self.noise = HomeoNoise()
        self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
 
        self.noise.constant() 
        self.noise.distorting() 
        self.noise.proportional()

        for index in range(tests):
            noiseValue = self.noise.getNoise()
            values.append(noiseValue)
            signs.append(numpy.sign(noiseValue))
        self.assertTrue(len(values) == tests)

        values.sort()
        signs.sort()
    
        '''distorting: test whether the sign of the noise value is about 50% of the times positive and 50% negative.
           Use binomial test with standard significance value of 0.05. This test will fail about 5% of the times...'''
        positives =  len(list(filter(lambda sign: sign == 1, signs)))
        self.assertTrue(stats.binomtest(positives, tests, 0.5).pvalue > 0.05)

        "constant and proportional: the absolute value of noise is always equal to the absolute value of unit's noise * unit's value"
        self.assertTrue(abs(values[0])  == abs(self.unit.noise * self.unit.criticalDeviation))
        self.assertTrue(abs(values[tests-1]) == abs(self.unit.noise * self.unit.criticalDeviation))

        #=======================================================================
        #          TODO (Fix expected behavior first)
        #'''Check behavior for zero values
        #   When noise = 0, return zero
        #   When current = 0, return -noise
        #   When both are zero, return 0'''
        # 
        # self.unit.noise = 0
        # self.unit._criticalDeviation = 0.5
        # self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        # producedNoise = self.noise.getNoise()
        # self.assertTrue(producedNoise == 0)
        # 
        # self.unit.noise = 0.5
        # self.unit._criticalDeviation = 0
        # self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        # producedNoise = self.noise.getNoise()
        # self.assertTrue(producedNoise == -0.5)
        # 
        # self.unit.noise = 0
        # self.unit._criticalDeviation = 0
        # self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        # producedNoise = self.noise.getNoise()
        # self.assertTrue(producedNoise == 0)
        #=======================================================================

    def testDistortingNormalLinearNoise(self):
        """
        Distorting normal linear noise must
        - normally distributed around a unit's noise (normal)
        - have a value related to the unit's noise (linear)
        - be distributed  *around* a unit's noise (approximately) (distorting)
        """
        tests = 1000
        values = []
        tolerance = 0.05
        self.unit.setRandomValues()

        self.noise = HomeoNoise()
        self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
 
        self.noise.normal() 
        self.noise.distorting() 
        self.noise.linear()

        for index in range(tests):
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
        self.assertTrue((minAbsNoise >= - self.unit.noise)  and
                        (maxAbsNoise <= self.unit.noise))

        "Normal: check the distribution is confidently normal (p > 0.05)"
        k2,p =  stats.normaltest(values)  #D'Agostino-Pearson omnibus test
        self.assertTrue(p > 0.05)

        #=======================================================================
        #          TODO (Fix expected behavior first)
        #'''Check behavior for zero values
        #   When noise = 0, return zero
        #   When current = 0, return -noise
        #   When both are zero, return 0'''
        # 
        # self.unit.noise = 0
        # self.unit._criticalDeviation = 0.5
        # self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        # producedNoise = self.noise.getNoise()
        # self.assertTrue(producedNoise == 0)
        # 
        # self.unit.noise = 0.5
        # self.unit._criticalDeviation = 0
        # self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        # producedNoise = self.noise.getNoise()
        # self.assertTrue(producedNoise == -0.5)
        # 
        # self.unit.noise = 0
        # self.unit._criticalDeviation = 0
        # self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        # producedNoise = self.noise.getNoise()
        # self.assertTrue(producedNoise == 0)
        #=======================================================================

    def testDistortingNormalProportionalNoise(self):
        """
        Distorting normal proportional noise must
        - normally distributed around a unit's noise (normal)
        - have a value proportional to the unit's value  (proportional)
        - be distributed  *around* a unit's noise (approximately) (distorting)
        """
        tests = 1000
        values = []
        tolerance = 0.05
        self.unit.setRandomValues()
#        "FIX ME for debugging"
#        self.unit.criticalDeviation = 1
#        self.unit.noise = 1
#        "End debugging"
        self.noise = HomeoNoise()
        self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
 
        self.noise.normal() 
        self.noise.distorting() 
        self.noise.proportional()

        for index in range(tests):
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
        self.assertTrue(minNoise >= ( - (self.unit.noise) * abs(self.unit.criticalDeviation))  and
                        (maxNoise <= (self.unit.noise * abs(self.unit.criticalDeviation))))

        "Normal: check the distribution is confidently normal (p > 0.05)"
        k2,p =  stats.normaltest(values)  #D'Agostino-Pearson omnibus test
        self.assertTrue(p > 0.05)

        #=======================================================================
        #          TODO (Fix expected behavior first)
        #'''Check behavior for zero values
        #   When noise = 0, return zero
        #   When current = 0, return -noise
        #   When both are zero, return 0'''
        # 
        # self.unit.noise = 0
        # self.unit._criticalDeviation = 0.5
        # self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        # producedNoise = self.noise.getNoise()
        # self.assertTrue(producedNoise == 0)
        # 
        # self.unit.noise = 0.5
        # self.unit._criticalDeviation = 0
        # self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        # producedNoise = self.noise.getNoise()
        # self.assertTrue(producedNoise == -0.5)
        # 
        # self.unit.noise = 0
        # self.unit._criticalDeviation = 0
        # self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        # producedNoise = self.noise.getNoise()
        # self.assertTrue(producedNoise == 0)
        #=======================================================================

    def testDistortingUniformProportionalNoise(self):
        """
        Distorting uniform proportional noise must
        - uniformly  distributed around a unit's noise *times* unit's value (uniform)
        - have a value proportional to the unit's value  (proportional)
        - be distributed  *around* a unit's noise *times* a unit's value (approximately) (distorting)
        """
        tests = 1000
        values = []
        tolerance = 0.05
        self.unit.setRandomValues()
#        "FIXME for debugging"
#        self.unit.noise = 1
#        self.unit.criticalDeviation = 1
#        " end debugging"

        self.noise = HomeoNoise()
        self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)

         
        self.noise.uniform() 
        self.noise.distorting() 
        self.noise.proportional()

        for index in range(tests):
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
        self.assertTrue(minNoise >= ( - (self.unit.noise) * abs(self.unit.criticalDeviation))  and
                        (maxNoise <= (self.unit.noise * abs(self.unit.criticalDeviation))))

        "uniform: use 2-sample Kolmogorov-Smirnov test against a uniform distribution with a p-value > 0.05"
        uniformRandomSample = numpy.random.uniform(- self.unit.noise * abs(self.unit.criticalDeviation), self.unit.noise * abs(self.unit.criticalDeviation),10000)
        D,p = stats.ks_2samp(values,uniformRandomSample)
        self.assertTrue(p > 0.05)

        #=======================================================================
        #          TODO (Fix expected behavior first)
        #'''Check behavior for zero values
        #   When noise = 0, return zero
        #   When current = 0, return -noise
        #   When both are zero, return 0'''
        # 
        # self.unit.noise = 0
        # self.unit._criticalDeviation = 0.5
        # self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        # producedNoise = self.noise.getNoise()
        # self.assertTrue(producedNoise == 0)
        # 
        # self.unit.noise = 0.5
        # self.unit._criticalDeviation = 0
        # self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        # producedNoise = self.noise.getNoise()
        # self.assertTrue(producedNoise == -0.5)
        # 
        # self.unit.noise = 0
        # self.unit._criticalDeviation = 0
        # self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        # producedNoise = self.noise.getNoise()
        # self.assertTrue(producedNoise == 0)
        #=======================================================================
           
    def testDistortingUniformLinearNoise(self):
        """
        Distorting uniform linear noise must
        - have a value related to the unit's noise (linear)
        - be uniformly distributed around a unit's noise (uniform)
        - be distributed around a unit's noise (distorting) 
        """
        tests = 1000
        values = []
        tolerance = 0.05
        self.unit.setRandomValues()

        self.noise = HomeoNoise()
        self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
 
        self.noise.uniform() 
        self.noise.distorting() 
        self.noise.linear()

        for index in range(tests):
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
        self.assertTrue(minNoise >= ( - self.unit.noise)  and
                        maxNoise <= self.unit.noise)

        "uniform: use 2-sample Kolmogorov-Smirnov test against a uniform distribution with a p-value > 0.05"
        uniformRandomSample = numpy.random.uniform(- self.unit.noise,self.unit.noise,10000)
        D,p = stats.ks_2samp(values,uniformRandomSample)
        self.assertTrue(p > 0.05)

        #=======================================================================
        #          TODO (Fix expected behavior first)
        #'''Check behavior for zero values
        #   When noise = 0, return zero
        #   When current = 0, return -noise
        #   When both are zero, return 0'''
        # 
        # self.unit.noise = 0
        # self.unit._criticalDeviation = 0.5
        # self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        # producedNoise = self.noise.getNoise()
        # self.assertTrue(producedNoise == 0)
        # 
        # self.unit.noise = 0.5
        # self.unit._criticalDeviation = 0
        # self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        # producedNoise = self.noise.getNoise()
        # self.assertTrue(producedNoise == -0.5)
        # 
        # self.unit.noise = 0
        # self.unit._criticalDeviation = 0
        # self.noise.withCurrentAndNoise(self.unit.criticalDeviation, self.unit.noise)
        # producedNoise = self.noise.getNoise()
        # self.assertTrue(producedNoise == 0)
        #=======================================================================

    def tearDown(self):
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()