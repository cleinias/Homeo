'''
Created on Feb 19, 2013

@author: stefano
'''

from Helpers.General_Helper_Functions  import SubclassResponsibility, withAllSubclasses
from Helpers.QObjectProxyEmitter import emitter
import numpy
from PyQt4.QtCore import QObject, SIGNAL


class HomeoUniselectorError(Exception):
    pass

class HomeoUniselector(object):
    '''
    Uniselector is the abstract class for different kinds of mechanisms producing random values 
    for the connection between two units. UniselectorAshby replicate as much as possible 
    the original stepping mechanism described by Ashby. UniselectorRandom provides a simpler mechanism 
    that simply produces a random value in the admitted interval. 
    Other mechanism can be added by subclassing Uniselector and 
    providing an alternative method produceNewValue.
    
    Instance Variables:

    lowerBound          the lower bound of the weight, default is 0
    upperBound          the upperbound of the weight, default is 1
    beeps               aBoolean that control whether the uniselector beeps when activated.
    '''
    
    @classmethod
    def includesType(self,aString):
        '''
        Answer true if aString represents the HomeoUniselector class or one of its subclasses
        '''

        uniselectorClasses = []
        uniselectorClasses.extend([class_.__name__ for class_ in withAllSubclasses(HomeoUniselector)])
        return aString in uniselectorClasses 

    
    def __init__(self):
        "Initialize the HomeoUniselector instance"
        self.setDefaults()
        
    def setDefaults(self):        
        '''sets the defaults for the uniselector weights. 
        Can be (and usually is) overridden by subclasses'''
        
        self._lowerBound = 0
        self._upperBound = 1
        self._beeps = False
        QObject.emit(emitter(self), SIGNAL('uniselSoundChanged'), self._beeps)
             
    def getLowerBound(self):
        return self._lowerBound
    
    def setLowerBound(self, aValue):
        self._lowerBound = aValue

    lowerBound = property(fget = lambda self: self.getLowerBound(),
                          fset = lambda self, value: self.setLowerBound(value))

    def getUpperBound(self):
        return self._upperBound
    
    def setUpperBound(self, aValue):
        self._upperBound = aValue

    upperBound = property(fget = lambda self: self.getUpperBound(),
                          fset = lambda self, value: self.setUpperBound(value))  
    
    def getBeeps(self):
        return self._beeps
    
    def toggleBeeping(self):
        self._beeps = not self._beeps 
        QObject.emit(emitter(self), SIGNAL('unitUniselSoundChanged'), self._beeps)
    
    beeps = property(fget= lambda self: self.getBeeps(),
                     fset = lambda self: self.toggleBeeping)
    
    def ashbyRandom(self):
        '''
        Produce 1 of a possible 25 different values for the weight 
        by selecting at random a 25th of the interval defined by lowerBound and upperBound
        
        This is a very simplistic implementation of Ashby's algorithm that is improved
        in the proper HomeoUniselector subclass 
        '''
        intervalSegment = (self._upperBound - self._lowerBound) / 25
        randValue = numpy.random.uniform(1,25)
        sign = round(numpy.random.uniform(-1,1))
        
        return randValue * intervalSegment * sign
        
    def advance(self):
        '''control how to advance to the next position of the uniselector. 
        Each subclass implements different mechanisms'''
        
        raise SubclassResponsibility()
    
