'''
Created on Mar 11, 2013

@author: stefano
'''
from Core.HomeoUniselector import *
from Helpers.General_Helper_Functions import *

class HomeoUniselectorUniformRandom(HomeoUniselector):
    '''
    HomeoUniselectorUniformRandom is a Uniselector that does NOT follow Ashby's model. 
    It provides a random value uniformly distributed in the interval [lowerbound, upperBound], 
    which is symmetric around 0, i.e. lowerbound = upperBound negated.
    The default values for the interval are [-1, +1], but other values can be chosen. 
    However, the accessors of lowerBound and upperBound enforce the constraint 
    by refusing positive (resp. negative) values for lowerBound (resp. upperBound) 
    and changing upperBound (resp. lowerBound) to the negated value of lowerBound (resp. upperBound)
    '''
    
    def advance(self):
        '''
        Do nothing because this uniselector has no concept of an index
        it produces a new uniformly distributed  random value every time it is called
        '''
        pass

    def setLowerBound(self,aNumber):
        '''The lowerBound of the interval the uniselector value is chosen from. As the interval must be symmetric around 0,
        we always set the lowerBound to a negative number and set the upperBound accordingly'''

        if aNumber <= 0:
            self._lowerBound = aNumber
            self._upperBound = - self._lowerBound
        else:
             self._lowerBound = -aNumber
             self._upperBound = aNumber

    def setUpperBound(self,aNumber):
        '''The upperBound of the interval the uniselector value is chosen from. As the interval must be symmetric around 0,
        we always set the upperBound to a positive  number and set the lowerBound accordingly'''

        if aNumber <= 0:
            self._lowerBound = aNumber
            self._upperBound = - self._lowerBound
        else:
             self._lowerBound = -aNumber
             self._upperBound = aNumber
             
    def produceNewValue(self):
        "produce a new random value uniformly distributed in the interval [lowerBoud, upperBound]"
#        if self._beeps:
#            pass
            #ring bell
        return numpy.random.uniform(self._lowerBound, self._upperBound)


    def __init__(self):
        '''
        Initializes according to superclass 
        '''
        super(HomeoUniselectorUniformRandom, self).__init__()
        self._lowerBound = -1
        self._upperBound = 1
        self._beeps - False
