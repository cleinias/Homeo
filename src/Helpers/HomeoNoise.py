'''
Created on Mar 15, 2013

@author: stefano
'''
from Helpers.General_Helper_Functions import  *
import numpy as np


class HomeoNoise(object):
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
    __metaclass__ = Singleton

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

        "add the random number generator"

#        randomGen := Random new.Constructor
        
    def getNoise(self):
        '''Select the correct noise algorithm according to the values 
       of mode, distribution and ratio and returns the noise value.
       Return a noise value computed accordingly'''

        noiseAlg = 'getNoise' + self._mode + self._distribution + self._ratio
        return self.getattr(self, noiseAlg)()

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
