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
        Initialize according to superclass and then call a local initialization function
        that may also be called outside of the constructor call'''
        super(HomeoUniselectorAshby,self).__init__()
        self.setDefaults()

    def setDefaults(self):
        '''
        Initializes the interval and the steps to default values. 
        Notice that the lowerBound and upperBound are always 0 and 1, as per Ashby's implementation, 
        because they represent the fraction of the input to reach the unit. 
        They are set in the superclass's init method.
        (see Design for a Brain sec 8/2, p. 102 (1960 ed.))
        '''
        self._index = 0
        self._steps = 12
        self._unitsControlled = 10
        self._unitIndex = 0
        self._ashbyKind = 'RandomizedValues'
        self.produceSequence()
        self._beeps = False
        emitter(self).uniselSoundChanged.emit(self._beeps)

        
    def setLowerBound(self,aValue):
        '''Do nothing. The lowerBound is always 0'''
        pass
    
    def setUpperBound(self,aValue):
        '''Do nothing. The UpperBound is always 1'''
        pass
    
    def setSteps(self, aValue):
        '''
        steps is always a positive integer > 0'''
        if int(abs(aValue)) == 0:
            self._steps = 1
        else:
            self._steps = int(abs(aValue))
        
    def getSteps(self):
        return self._steps
    
    steps = property(fget = lambda self: self.getSteps(),
                          fset = lambda self, value: self.setSteps(value))
    
    def setAshbyKind(self,aString):
        '''
        Do nothing. The value of AshbyKind is managed by 
        other methods'''
        pass
        

    
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
                          fset = lambda self, value: self.setUnitsControlled(value))
    
    def matrix(self):
        return self._matrix
    
    def equallySpaced(self):
        '''set initialization procedure to equally spaced values
           and reinitializes the transition matrix if necessary 
           (See method produceEquallySpacedValues for details)'''

        if self._ashbyKind != 'EquallySpacedValues':
            self._ashbyKind = 'EquallySpacedValues'
            self.produceSequence()
    

    def independentlyRandomized(self):
        '''Set initialization procedure to independently randomized  values
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
        for i in range(self._unitsControlled - 1):
            tempSeqq = np.linspace(-1,1,(self._steps * 2) + 1)
            np.random.shuffle(tempSeqq) 
            tempSeq = np.column_stack((tempSeq,tempSeqq))
        return tempSeq

    def produceIndependentlyRandomizedValues(self):
        ''' Produce a m x n Matrix, where m = number of  uniformly distributed random values  (default = 25),
        n = maximum number of units controlled by the Uniselector. 
        Notice that in this implementation, all connections have ***different***  random values.
        This DOES NOT seem to capture the original homeostat, 
        where random values were implemented in hardware and could not be changed. 
        Initializing the uniselector with produceRandomized Sequence, 
        on the other hand, produces a matrix in which all rows (connections) 
        share the same  random values'''

        return np.random.uniform(- self._upperBound, self._upperBound, ((self._steps * 2) + 1 ,self._unitsControlled))

    def produceRandomizedValues(self):
        '''
        Produce a m x n Matrix, where m = number of  uniformly distributed random values  
        (default = 25), n = maximum number of units controlled by the Uniselector. 
        Notice that in this implementation, all connections share the same space 
        of 25 random values, although they go through them in a different order. 
        This seems to capture (one of the interpretations) of the original homeostat, 
        where random values were implemented in hardware and could not be changed. 
        Initializing the uniselector with produceIndependentRandomized Sequence, 
        on the other hand, produces a matrix in which all rows have (a highly likelihood of being)
        completely different values'''

        tempSeq = np.random.uniform(- self._upperBound, self._upperBound,(self._steps * 2) +1)
        tempSeqq = tempSeq.copy()
        for i in range(self._unitsControlled):
            tempSeqqq = tempSeqq.copy()
            np.random.shuffle(tempSeqqq) 
            tempSeq = np.column_stack((tempSeq,tempSeqqq))
        return tempSeq
    
    def produceSequence(self):
        ''' Produces the matrix containing the values for the uniselector switch
            according to the kind of Ashby uniselector specified in ashbyKind
            
            New matrix production methods can be added by:
            1 - Adding a method that produces a n*m matrix of transition values,
                where m is = self._unitsControlled
            2 - Naming the method 'produce' + methodName
            3 - Adding a method that allows setting self._ashbyKind  to methodName  
            
            '''
        
        self._matrix = getattr(self,'produce'+ self.ashbyKind)()
        
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
    
    def sameAs(self,aUniselector):
        '''True if it is of the  same ashby kind
            as aUniselector and transition matrices are the same.
            
            It will almost never return true for uniselector, for
            transition matrices' values are  shuffled'''
        
        return (self.sameKindAs(aUniselector) and
                np.array_equal(self.matrix(), aUniselector.matrix()))
            
    
    def sameKindAs(self,aUniselector):
        ''' It is the same class as aUniselector'''
        
        return (type(self) == type(aUniselector) and
                self.ashbyKind == aUniselector.ashbyKind)
        
