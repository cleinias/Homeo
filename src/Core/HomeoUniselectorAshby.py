'''
Created on Mar 18, 2013

@author: stefano
'''
from Core.HomeoUniselector import  *
import numpy as np

class HomeoUniselectorAshby(HomeoUniselector):
    '''
    HomeoUniselectorAshby is a different implementation of Ashby's (sparsely described!) algorithm.
    It simulates a stepping switch (or Uniselector) that advances one step every time it is activated.
    At every step the uniselector produces weight values for the HomeoUnits connections. 
    The simulation is implemented  with a m x n matrix (the ivar matrix) where m 
    are the steps of the uniselector, and n are the number of connected units. 
    In Ashby's classical homeostat m= 25, n = 3.  The values in the matrix are produced according 
    to three different algorithms, each a different intepretation of Ashby's original idea. 
    The parameter deciding which production method to use is held in ashbyKind.

    Instance Variables:
    unitsControlled <anInteger>       The maximum number of units this uniselector controls. Default values is 10. It will be incremented in 10-units increment if needed
    unitIndex       <anInteger>        The index keeping track of which unit's connection we are currently producing a value (a weight) for.
    ashbyKind       <aString>          The string determining which initialization (and re-initialization) method to use.
    unitIndex
    interval
    steps        <anInteger>       The number of possible steps in the Uniselector (default is 12, as per Ashby's implementation)
    index        <anInteger>       The index keeping track of which row of weight we should output next
    matrix        <aMatrix>       A matrix of size (unitsControlled x steps) holding all the possible weights
    '''


    def __init__(self):
        '''
        Initializes the interval and the steps to default values. 
        The lowerBound and upperBound are always 0 and 1, as per Ashby's implementation, 
        because they represent the fraction of the input to reach the unit 
        (see Design for a Brain sec 8/2, p. 102 (1960 ed.)
        '''
   
        super(HomeoUniselectorAshby,self).__init__()
        self._lowerBound = 0
        self._upperBound = 1
        self._index = 0
        self._steps = 12
        self._unitsControlled = 10
        self._unitIndex = 0
        self._ashbyKind = 'RandomizedValues'
        self.produceSequence()
        
    def setLowerBound(self,aValue):
        '''Do nothing. The lowerBound is always 0'''
        pass
    
    def setUpperBound(self,aValue):
        '''Do nothing. The UpperBound is always 1'''
        pass
    
    def setSteps(self, aValue):
        '''
        steps is always a positive integer'''
        self._steps = int(abs(aValue))
        
    def getSteps(self):
        return self._steps
    
    steps = property(fget = lambda self: self.getSteps(),
                          fset = lambda self, value: self.setSteps(value))
    
    def setAshbyKind(self,aString):
        self._ashbyKind = aString
    
    def getAshbyKind(self):
        return self._ashbyKind
    
    ashbyKind = property(fget = lambda self: self.getAshbyKind(),
                          fset = lambda self, value: self.setAshbyKind(value))
    
    def getUnitsControlled(self):
        return self._unitsControlled
    
    def setUnitsControlled(self,aNumber):
        '''The uniselector is initialized to control 10 maximum connections 
           and it initializes its transition matrix (sequence) accordingly. 
           When the required number of max connections increases, it goes up 
           in 10 units step increments and produces a new transition matrix'''

        if aNumber > self._unitsControlled:
            self._unitIndex = self._unitsControlled + 10
        self.produceSequence()
        
    unitsControlled = property(fget = lambda self: self.getUnitsControlled(),
                          fset = lambda self, value: self.setUnitControlled(value))
    def equallySpaced(self):
        '''set initialization procedure to equally spaced values
           and reinitializes the transition matrix if necessary 
           (See method produceEquallySpacedValues for details)'''

        if self._ashbyKind != 'EquallySpacedValues':
            self._ashbyKind = 'EquallySpacedValues'
            self.produceSequence()
    

    def independentlyRandomized(self):
        '''Set initialization procedure to independentely randomized  values
            and reinitializes the transition matrix if necessary 
            (See method produceIndependentlyRandomizedValues for details)'''

        if self._ashbyKind != 'IndependentlyRandomizedValues':
            self._ashbyKind = 'IndependentlyRandomizedValues'
            self.produceSequence()
        
    def randomized(self):
        '''Set initialization procedure to  randomized  values 
           and reinitializes the transition matrix if necessary 
           (see method produceRandomizedValues for details)'''

        if self._ashbyKind != 'RandomizedValues':
            self._ashbyKind = 'RandomizedValues'
            self.produceSequence()

    
    def produceEquallySpacedValues(self):
        ''' Produce a m x n Matrix, where m = number of equally spaced values
         (default = 25), n = maximum number of units controlled by the Uniselector'''        
        
        tempSeq = np.linspace(-1,1,(self._steps * 2) + 1)
        for i in xrange(self._unitsControlled - 1):
            tempSeqq = np.linspace(-1,1,(self._steps * 2) + 1)
            np.random.shuffle(tempSeqq) 
            tempSeq = np.column_stack((tempSeq,tempSeqq))
        return tempSeq

    def produceIndependentRandomizedValues(self):
        ''' Produce a m x n Matrix, where m = number of  uniformly distributed random values  (default = 25),
        n = maximum number of units controlled by the Uniselector. 
        Notice that in this implementation, all connections have ***different***  random values.
        This DOES NOT seem to capture the original homeostat, 
        where random values were implemented in hardware and could not be changed. 
        Initializing the uniselector with produceRandomized Sequence, 
        on the other hand, produces a matrix in which all rows (connections) 
        share the same  random values'''

        return np.random.uniform(0,1, (self._steps,self._unitsControlled))

    def produceRandomizedValues(self):
        '''
        Produce a m x n Matrix, where m = number of  uniformly distributed random values  
        (default = 25), n = maximum number of units controlled by the Uniselector. 
        Notice that in this implementation, all connections share the same space o
        f 25 random values, although they go through them in a different sequence. 
        This seems to capture (one of the interpretations) of the original homeostat, 
        where random values were implemented in hardware and could not be changed. 
        Initializing the uniselector with produceIndependentRandomized Sequence, 
        on the other hand, produces a matrix in which all rows have (a highly likelihood of being)
        completely different values'''

        tempSeq = np.random.uniform(0,1,self._steps)
        tempSeqq = tempSeq.copy()
        for i in xrange(self._unitsControlled):
            tempSeqqq = tempSeqq.copy()
            np.random.shuffle(tempSeqqq) 
            tempSeq = np.column_stack((tempSeq,tempSeqqq))
        return tempSeq
    
    def produceSequence(self):
        ''' Produces the matrix containing the values for the uniselector switch
            according to the kind of Ashby uniselector specified in ashbyKind'''
        
        if self._ashbyKind == 'EquallySpacedValues':
            self._matrix = self.produceEquallySpacedValues()
        if self._ashbyKind == 'IndependentlyRandomizedValues':
                self._matrix = self.produceIndependentRandomizedValues()
        if self._ashbyKind ==  'RandomizedValues':
            self._matrix = self.produceRandomizedValues()

    def produceNewValue(self):
        '''Return the weight for the next connection and advances the unitIndex'''
        if not self._unitIndex  > self._unitsControlled:
            if self._beeps:
                # FIXME will need to put a beep here
                pass
            self._unitIndex = self._unitIndex + 1
            return self._matrix[self._index - 1, self._unitIndex -1]
        else:
            raise Exception('Too many units for the uniselector to control')

    def advance(self):
        '''Advance the uniselector to the next position'''
        if self._index == self._matrix.shape[0]:
            self._index = 0
        else:
            self._index = self._index + 1
            
        self._unitIndex = 0
