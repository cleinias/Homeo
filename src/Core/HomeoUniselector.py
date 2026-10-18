# Copyright (C) 2006-2026 Stefano Franchi
#
# This file is part of Homeo, a simulation of Ashby's homeostat and of
# homeostat-controlled robots.
#
# Homeo is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# Homeo is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with Homeo.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from Helpers.General_Helper_Functions  import SubclassResponsibility, withAllSubclasses
from Helpers.QObjectProxyEmitter import emitter
import numpy


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
  
        '''sets the defaults for the uniselector weights. 
        Can be (and usually is) overridden by subclasses'''
        
        self._lowerBound = 0
        self._upperBound = 1
        self._beeps = False
        emitter(self).uniselSoundChanged.emit(self._beeps)
             
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

    def setBeeps(self, aBoolean):
        '''Whether the uniselector beeps when it fires.  Emits
           uniselSoundChanged, the signal the GUI's checkbox listens to.'''
        self._beeps = bool(aBoolean)
        emitter(self).uniselSoundChanged.emit(self._beeps)

    def toggleBeeping(self):
        self.setBeeps(not self._beeps)

    beeps = property(fget= lambda self: self.getBeeps(),
                     fset = lambda self, aBoolean: self.setBeeps(aBoolean))
        
    def advance(self):
        '''control how to advance to the next position of the uniselector. 
        Each subclass implements different mechanisms'''
        
        raise SubclassResponsibility()
    
    def allValuesChanged(self):
        "Signals back to GUI that all its relevant values have changed"
        pass