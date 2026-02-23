'''
Created on Mar 15, 2013

@author: stefano
'''
from Helpers.General_Helper_Functions import Singleton
import numpy as np
import random
import sys

class HomeoNoise(object, metaclass=Singleton):
    '''
    HomeoNoise is a utility class that provides different algorithms to deal with 
    the computation of how noise affects the transmission of current between units 
    and the flicker noise that may affect the units' internal values. 

    Instance variables:

    current       <aNumber>    The value of the current affected by the noise
    noise         <aNumber>    The value of the noise affecting the transmission of the current. This value is typically between 0 (no noise) and 1 (channel so noisy to block communication)
    mode          <aString>    Mode of the noise. Possible values: 'distorting' 'degrading', indicates how the noise affects the currentWhether the noise is a        
    distribution  <aString>    Probability distribution of the actual noise with respect to the noise value. Possible values: 'constant', 'uniform', 'normal'
    ratio         <aString>    Ratio of the noise to the affected current. Possible values: 'linear' 'proportional'

    It is a singleton class. 
    The only class creation method is newWithCurrent: andNoise: which simply updates the values of 
    the instance variables if the unique instance exists already.

    The noise-computing algorithm is selected by changing the values of 
    the three iVars mode, distribution, and ratio, and then calling the method getNoise. 
    This method constructs a selector string from the values of the ivar and calls the corresponding method. 

    '''
    def __init__(self):
        '''
        Initialize the instance to a current of 1 and noise of 0, representing a full current and no noise. 
        These values are typically overridden by class creation methods.
        '''

        self._current = 1
        self._noise = 0
        
        "default values for noise parameters"
        self._mode = 'Distorting'
        self._distribution = 'Normal'
        self._ratio = 'Proportional'

    def getCurrent(self):
        return self._current
    
    def setCurrent(self, aValue):
        "Do nothing. Noise is set through other methods"
        pass
    
    current = property(fget = lambda self: self.getCurrent(),
                          fset = lambda self, value: self.setCurrent(value))   
    
    def noiseGetter(self):
        '''Using noiseGetter for a get method, because getNoise is used to produce noise value'''
        return self._noise
    
    def noiseSetter(self, aValue):
        "Do nothing. Noise is set through other methods"
        pass

    noise = property(fget = lambda self: self.noiseGetter(),
                          fset = lambda self, value: self.noiseSetter(value))   
    
    def getRatio(self):
        return self._ratio
    
    def setRatio(self, aValue):
        "Do nothing. Ratio is always set via other methods"
        pass

    ratio = property(fget = lambda self: self.getRatio(),
                          fset = lambda self, value: self.setRatio(value))   
    
    def getMode(self):
        return self._mode
    
    def setMode(self, aValue):
        "Do nothing. Mode is always set via other methods"
        pass

    mode = property(fget = lambda self: self.getMode(),
                          fset = lambda self, value: self.setMode(value))   
    
    def getDistribution(self):
        return self._distribution
    
    def setDistribution(self, aValue):
        "Do nothing. Distribution is always set via other methods"
        pass

    distribution = property(fget = lambda self: self.getDistribution(),
                          fset = lambda self, value: self.setDistribution(value))   
    
    
    def withCurrentAndNoise(self, aNumber, anotherNumber):
        "Set current and noise on the only instance of the class"
        self._current = aNumber
        self._noise = anotherNumber

        
    def getNoise(self):
        '''Return 0 if noise is 0. Otherwise:
        Select the correct noise algorithm according to the values 
        of mode, distribution and ratio and returns the noise value.
        Return a noise value computed accordingly'''

        if self._noise == 0:
            return 0
        else:
            noiseAlg = 'getNoise' + self._mode + self._distribution + self._ratio
            producedNoise =  getattr(self, noiseAlg)()
            return producedNoise

    "Methods setting noise's mode"
    def degrading(self):
        self._mode = 'Degrading'

    def distorting(self):
        self._mode = 'Distorting'

    "Methods setting noise's ratio"
    def proportional(self):
        self._ratio = 'Proportional'

    def linear(self):
        self._ratio = 'Linear'
        
    "Methods setting noise's distribution"
    def normal(self):
        self._distribution = 'Normal'
        
    def uniform(self):
        self._distribution = 'Uniform'
        
    def constant(self): 
        self._distribution = 'Constant'

#    "Noise algorithms"
#
#    def constDegradLinearNoise(self):
#        '''Returns a value representing a constant degrading noise affecting linearly  the current .
#         Assumes noise is a value between 0 and 1'''
#
#        currentSign = np.sign(self._current)
#        if currentSign == 0:
#            currentSign = 1        #make sure we don't lose the current when noise is 0"
#        return (abs(self._current) - self._noise) * currentSign
#    
#    def constDegradPropNoise(self):
#        '''Returns a value representing a constant degrading noise affecting the current proportionally. 
#            Assumes noise is a value between 0 and 1, i.e. the percentage of current lost to noise'''
#
#        currentSign = np.sign(self._current)
#        if currentSign == 0:
#            currentSign = 1        #make sure we don't lose the current when noise is 0"
#
#            return (abs(self._current) - (abs(self._current) * self._noise)) * currentSign
#
#    def constDistortLinearNoise(self):
#        '''Returns a value representing a constant distorting noise affecting the current linearly. 
#            Assumes the noise is a number between 0 and 1'''
#
#        noiseSign = np.sign(np.random.uniform(-1,1))
#        if noiseSign == 0:
#            noiseSign = 1
#
#        currentSign = np.sign(self._current)
#        if currentSign == 0:
#            currentSign = 1        #make sure we don't lose the current when noise is 0"
#        
#        return (abs(self._current) - (self._noise * noiseSign)) * currentSign
#
#    def DistortPropNoise(self):
#        '''Returns a value representing a constant distorting noise affecting the current proportionally. 
#            Assumes the noise is a number between 0 and 1, i. e. the percentage of current lost to noise'''
#
#        noiseSign = np.sign(np.random.uniform(-1,1))
#        if noiseSign == 0:
#            noiseSign = 1
#
#        currentSign = np.sign(self._current)
#        if currentSign == 0:
#            currentSign = 1        #make sure we don't lose the current when noise is 0"
#        
#        return (abs(self._current) - (self._noise * abs(self._current) *noiseSign)) * currentSign
    "Noise algorithms"

    def getNoiseDegradingConstantLinear(self):
        '''Return a degrading noise (with sign always opposite to affected current), 
            and constant value equal to the noise parameter.
            
            If current is 0, return noise itself, the assumption being 
            that  noise is some kind of extraneous activity that always takes
            place, regardless of whether there is some current on the 
            affected line'''
        
        if self._current == 0:
            return self._noise * -1
        else:
            return self._noise * -1 * np.sign(self._current)

    def getNoiseDegradingConstantProportional(self):
        '''Return a degrading noise (with sign always opposite to affected current), 
            and constant value equal to the ratio between the noise parameter and the affected current'''

        if self.noise == 0:
            return 0
        else:
            if self.current == 0:
                return - self.noise
            else:
                return (self._noise * abs(self._current)) * np.sign(self._current) * -1

    def getNoiseDegradingNormalLinear(self):
        '''Return a degrading noise (sign always opposite to current),
           normally distributed and proportional to the absolute magnitude of the noise parameter'''

        if self.noise == 0:
            return 0
        else:
            noiseSign = np.sign(self._current) * -1 
            noiseAbsValue = np.random.normal(self._noise, self._noise * 1 / 3.)

            "trim noise within the interval (0, 2 * noise)"
            return np.clip(noiseAbsValue, 0, 2* self.noise) * noiseSign

    def getNoiseDegradingNormalProportional(self):
        '''Return a degrading noise (with sign always opposite to affected current), 
            and normally distributed value in the interval [0, 2 * noise * abs(current)]
            If the affected current is = 0, still returns a value in the interval 
            (0 , 2 * noise)'''

        if self.noise == 0:
            return 0
        else:
            if self._current != 0:
                minNoise = - self._noise * abs(self._current)
                maxNoise = self._noise * abs(self._current)
            else:
                minNoise = - self._noise
                maxNoise = self._noise

        if self.noise == 0:
            return 0
        else:
            if self._current != 0:
                noiseSign = np.sign(self._current) * -1 
                minAbsNoise = 0
                maxAbsNoise = self._noise * abs(self._current) * 2
            else:
                noiseSign = -1
                minAbsNoise = 0
                maxAbsNoise = self._noise

            noiseAbsValue = np.random.normal(maxAbsNoise / 2, maxAbsNoise / 6.)
        
            "trim noise within the interval {0, 2 *noise *current abs}"
            return np.clip(noiseAbsValue, minAbsNoise, maxAbsNoise) * noiseSign

    def getNoiseDegradingUniformLinear(self):
        '''Return a degrading noise (sign always opposite to current) uniformly distributed
             and proportional to the absolute magnitude of the noise parameter'''

        currentSign = np.sign(self._current) * -1
        maxNoise = self._noise
        noiseAbsValue = np.random.uniform(0, (2 * maxNoise))

        return noiseAbsValue * currentSign
    
    def getNoiseDegradingUniformProportional(self):
        '''Return a degrading noise (with sign always opposite to affected current), 
            and uniformly distributed value in the interval [0, 2 * noise * current ]'''

        currentSign = np.sign(self._current)  * -1
        maxNoise = 2 * self._noise * abs(self._current)
        noiseAbsValue = np.random.uniform(0, maxNoise)
        return noiseAbsValue * currentSign

    def getNoiseDistortingConstantLinear(self):
        '''Return a distorting noise (centered around 0),  
            with absolute value equal to the noise parameter'''

        randomSign = np.sign(np.random.uniform(-1,1))
        return  self._noise * randomSign

    def getNoiseDistortingConstantProportional(self):
        '''Return a distorting noise (centered around 0),
            equal to the ratio between the absolute magnitude
            of the affected current and the noise parameter'''

        randomSign = np.sign(np.random.uniform(-1,1))
        return self.noise *abs(self._current) * randomSign

    def getNoiseDistortingNormalLinear(self):
        '''Returns a distorting noise (centered around 0),
             normally distributed and proportional to 
             the  absolute magnitude of the noise parameter'''
 
        if self.noise == 0:
            return 0
        else:
            noiseValue =  np.random.normal(0, self._noise / 3.)
        
        "trim noise within the interval { -noise, noise}"
        return max(-self._noise, min(self._noise, noiseValue))
            
    def getNoiseDistortingNormalProportional(self):
        '''Returns a distorting noise (centered around 0), normally distributed
         and proportional to the absolute magnitude of the affected current
         
         Standard deviation of the normal distribution is 1/3 of noise's value'''


        if self.noise == 0:
            return 0
        else:
            if self._current != 0:
                minNoise = - self._noise * abs(self._current)
                maxNoise = self._noise * abs(self._current)
            else:
                minNoise = - self._noise
                maxNoise = self._noise

        noiseValue = np.random.normal(0, maxNoise / 3.)
    
        "trim noise within the interval (0, 2 *noise)"
        return max(minNoise, min(maxNoise, noiseValue))
        

    def getNoiseDistortingUniformLinear(self):
        '''Return a distorting noise (centered around 0),
             uniformly distributed in the interval [-noise, noise]'''

        maxNoise = self._noise
        noiseAbsValue = np.random.uniform(- maxNoise, maxNoise)

        return noiseAbsValue

    def getNoiseDistortingUniformProportional(self):
        '''Return a distorting noise (centered around 0), 
            uniformly distributed in the interval [-noise * abs(current), noise * abs(current) ]'''

        maxNoise = self._noise * abs(self._current)
        noiseValue = np.random.uniform(- maxNoise, maxNoise)

        return noiseValue

    @staticmethod
    def connNoise(current, noise):
        '''Inlined distorting-normal-proportional noise for connections.
           Equivalent to getNoiseDistortingNormalProportional but avoids
           singleton re-init, string dispatch, and numpy scalar overhead.'''
        if noise == 0:
            return 0.0
        bound = noise * abs(current) if current != 0 else noise
        val = random.gauss(0, bound / 3.0)
        if val < -bound:
            return -bound
        if val > bound:
            return bound
        return val

    @staticmethod
    def unitNoise(noise):
        '''Inlined distorting-normal-linear noise for units.
           Equivalent to getNoiseDistortingNormalLinear but avoids
           singleton re-init, string dispatch, and numpy scalar overhead.'''
        if noise == 0:
            return 0.0
        val = random.gauss(0, noise / 3.0)
        if val < -noise:
            return -noise
        if val > noise:
            return noise
        return val

