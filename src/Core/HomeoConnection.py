#===============================================================================
#     This file is part of Homeo, a homeostat simulator.
#     Copyright Stefano Franchi 2012-2014
# 
#     Homeo is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     Homeo is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with Homeo.  If not, see <http://www.gnu.org/licenses/>.
#===============================================================================





from Helpers.HomeoNoise import *
import numpy as np
from Helpers.QObjectProxyEmitter import emitter
import sys
from Helpers.ExceptionAndDebugClasses import hDebug

class ConnectionError(Exception):
    '''
    Base class for exceptions in the HomeoConnection module
    '''
    pass

class HomeoConnection(object):
    '''
    HomeoConnection represents a connection between two HomeoUnits.
    It  holds the incoming unit (the unit the signal is coming from), 
    the outgoing unit (the unit the signal goes to---typically the unit that is holding the connection),  
    the weight of the connection, and the polarity of the connection.

    Instance Variables:
    incomingUnit        <aHomeoUnit>      the HomeoUnit the signal is coming from
    outgoingUnit        <aHomeoUnit>      the HomeoUnit the signal is going to (typically the unit holding on to this HomeoConnection)
    switch               <anInteger>      polarity of the connection ( +1 or -1)
    weight               <aFloat>         weight of the connection : between 0 and 1
    noise                <aFloat>         possible noise on the connection (between 0--no noise - to 1, so noisy to break the connection)
    state                <aString>        determines whether the connection is governed by weight and switch or by the uniselector. 
                                          The value can only be 'manual' or 'uniselector'
    status               <aBoolean>        whether the connection is active or not. 
    '''
    
    
    def __init__(self):
        '''
        A new connection is always initialized to some random values. 
        '''
        self.randomizeConnectionValues()
        
    def randomizeConnectionValues(self):
        '''Initialize the connection to some random value for noise and weight, 
           and set the default state to "uniselector"'''

        self.noise = np.random.uniform(0,0.1)
        self.state = 'uniselector'
        self.newWeight(np.random.uniform(-1,1))
        #self.newWeight(0)
        self.status = True


    "class methods"
    @classmethod    
    def newWithIncomingUnitWeightSwitchNoiseStateActive(cls,incomingUnit, aWeight, aSwitch, aNoise, aState, aBoolean):
        '''
        Return a new connection with values initialized as specified
        '''
        conn = HomeoConnection()
        conn.incomingUnit = incomingUnit
        conn.newWeight(aWeight * aSwitch)
        conn.noise = aNoise
        conn.state = aState
        conn.status = aBoolean
        
        return conn 
    
    @classmethod    
    def newWithIncomingUnitOutgoingUnitWeightSwitchNoiseStateActive(cls,aUnit,anotherUnit,aWeight,aSwitch,aNoise,aState,aBoolean):
        '''
        Return a new connection with values initialized as specified.
        '''
        
        conn = HomeoConnection()
        conn.incomingUnit = aUnit
        conn.outgoingUnit = anotherUnit
        conn.newWeight(aWeight * aSwitch)
        conn.noise = aNoise
        conn.state = aState
        conn.status = aBoolean
        
        return conn 

    @classmethod    
    def newFromUnitToUnit(self,aHomeoUnit,anotherUnit):
        '''Creates a new connection with  the incoming and outgoing units'''
        
        conn = HomeoConnection()
        conn.outgoingUnit =  aHomeoUnit
        conn.incomingUnit =  anotherUnit
        return conn
    
    @classmethod
    def connWeightFromGAWeight(self, aWeightParam):
        ''''updates weight and switch by scaling aWeightParam (0,1) to the
        interval (-1,1)'''
        return -1 + (aWeightParam * 2)


    def getIncomingUnit(self):
        return self._incomingUnit
    
    def setIncomingUnit(self, aHomeoUnit):
        "Set incoming unit"
        self._incomingUnit = aHomeoUnit
    
    incomingUnit = property(fget = lambda self: self.getIncomingUnit(),
                          fset = lambda self, value: self.setIncomingUnit(value))   
    def getOutgoingUnit(self):
        return self._outgoingUnit
    
    def setOutgoingUnit(self, aHomeoUnit):
        "Set outgoing unit"
        self._outgoingUnit = aHomeoUnit
    
    outgoingUnit = property(fget = lambda self: self.getOutgoingUnit(),
                          fset = lambda self, value: self.setOutgoingUnit(value))   

    def getSwitch(self):
        return self._switch
    
    def setSwitch(self, aSwitch):
        '''Raise an exception: switch is only set through the newWeight or toggleSwitch methods'''
        raise ConnectionError("A HomeoConnection's switch can only be set through the newWeight method")
    
    switch = property(fget = lambda self: self.getSwitch(),
                          fset = lambda self, value: self.setSwitch(value))
    
    def toggleSwitch(self, aNumber):
        "Change the polarity of the connection to aNumber"
#        self.newWeight(self.weight * -1)
#        QObject.emit(emitter(self), SIGNAL('switchChanged'), self._switch)
        acceptedValues = (-1,1)
        oldWeight = self.weight
        oldSwitch = self.switch     
        try:
            if int(aNumber) in acceptedValues:
                newWeight = abs(oldWeight) * int(aNumber)
                self.newWeight(newWeight)
                self._switch = int(aNumber)
#                sys.stderr.write("Unit %s's new weight is %f: with switch equal to %f. The value passed from the GUI was %f . \nThe old weight was %f and the old switch was %f, and the old unit's switch was %f\n" 
#                                 % (self.name, self.inputConnections[0].weight, self.switch, int(aNumber), oldWeight, oldSwitch, oldUnitSwitch))
            else: 
                raise  ConnectionError
        except ValueError:
            sys.stderr.write("Tried to assign a non-numeric value to the switch of the connection from %s to %s The value was: %s\n" % (self.outgoingUnit.name, self.incomingUnit.name, aNumber))
        finally:
            emitter(self).switchChanged.emit(self._switch)
            emitter(self).switchChangedLineEdit.emit(str(int(self._switch)))
            emitter(self.incomingUnit).switchChangedLineEdit.emit(str(int(self._switch))) 
#            sys.stderr.write('%s emitted signals switchChanged with value %f the object emitting the signal was %s\n' % (self._name, self._switch, emitter(self.inputConnections[0])))
   

    def getWeight(self):
        return self._weight
    
    def setWeight(self, aWeight):
        '''Raise an exception:  weight can only be set with  
        newWeight: a value, which takes care of absolute value and polarity (switch)'''
        raise ConnectionError("A HomeoConnection's weight can only be set  through the newWeight method")
    
    weight = property(fget = lambda self: self.getWeight(),
                          fset = lambda self, value: self.setWeight(value))   

    def getNoise(self):
        return self._noise
    
    def setNoise(self, aNoise):
        '''
        Must be between 0 and 1 included
        '''
        if  0 <=  aNoise <= 1:
            self._noise = aNoise
        else:
            raise ConnectionError("Noise must be between 0 and 1")
        emitter(self).noiseChanged.emit(self._noise)

    
    noise = property(fget = lambda self: self.getNoise(),
                          fset = lambda self, value: self.setNoise(value))   
    def getState(self):
        return self._state
    
    def setState(self, aString):
        '''raise an exception if the input value is neither "manual" or "uniselector"'''
        if aString in ['manual','uniselector']:                 
            self._state = aString
        else:
            raise ConnectionError("The state value %s is not allowed. Only allowed values are manual and uniselector" % aString)
    
    state = property(fget = lambda self: self.getState(),
                          fset = lambda self, value: self.setState(value))   

    def getStatus(self):
        return self._status
    
    def setStatus(self, aBoolean):
        if aBoolean in (True,False):
            self._status = aBoolean
        else:
            raise ConnectionError('The status of a connection can only be a Boolean')
    
    status = property(fget = lambda self: self.getStatus(),
                          fset = lambda self, value: self.setStatus(value))   
    
    def toggleStatus(self):
        self.status = not self.status

    active = property(fget = lambda self: self.getStatus(),
                          fset = lambda self, value: self.setStatus(value))   
    
 
    def newWeight(self, aWeight):
        "updates weight and switch on the basis -1 <=  aWeight <= 1"
        
        if aWeight == 0:
            self._switch = 1
            self._weight = 0
        else:
            if -1 <= aWeight <= 1:
                self._weight= abs(aWeight)
                self._switch = np.sign(aWeight)
            else:
                raise ConnectionError("A HomeoConnection weight must be between -1 and 1")
        emitter(self).weightChanged.emit(self._weight)
        emitter(self).switchChanged.emit(self._switch)

        "Signaling back to the incoming unit's potentiometer and switch in case of a self-connection"
        try:
            if self.incomingUnit == self.outgoingUnit:
                emitter(self.incomingUnit).potentiometerChangedLineEdit.emit(str(round(self._weight, 4)))
                emitter(self.incomingUnit).switchChangedLineEdit.emit(str(int(self._switch)))
        except AttributeError:
            pass
            #sys.stderr.write("Initializing connection, no incoming unit assigned yet\n")
            
    def newWeightGA(self, aWeightParam):
        ''''updates weight and switch by scaling aWeightParam (0,1) to the
        interval (-1,1)'''
        self.newWeight(HomeoConnection.connWeightFromGAWeight(aWeightParam))
        #print "GAparam: %.3f, weight: %.3f., switch: %d for conn from %s to %s" % (aWeightParam, self.weight, self.switch, self.incomingUnit.name, self.outgoingUnit.name)


    def setAbsoluteWeight(self, aPositiveValue):
        'Utility function that changes the weight of a connection without changing its sign (i.e. the switch)'
        if aPositiveValue == 0:
            self._switch = 1
            self._weight = 0
        else:
            if 0 < aPositiveValue <= 1:
                self._weight= aPositiveValue
#            QObject.emit(emitter(self), SIGNAL('weightChanged'), self._weight)
        "signal back to unit's potentiometer in case of self-connections"
        if self.incomingUnit == self.outgoingUnit:
            emitter(self.incomingUnit).potentiometerChangedLineEdit.emit(str(round(self._weight, 4)))
                
        
        
    
    def outgoingUnit(self):
        ''' the "outgoingUnit" is the unit the signal is going *to*. 
            It is typically the HomeoUnit holding on to the connection''' 
        
        return self._outgoingUnit
    
    def output(self):
        ''''Return the value of the connection times the weight, possibly switched,  and  include  the noise. 
            The noise  is computed with the help of the HomeoNoise utility class. 
            Several different algorithms are available, see the instance methods of HomeoNoise for details'''
        
        newNoise = HomeoNoise()
        newNoise.withCurrentAndNoise(self.incomingUnit.currentOutput, self._noise)

        newNoise.normal()          # select noise as normally (Gaussian) distributed around the value for the unit's connection noise"
        newNoise.distorting()      # select  noise as distorting the current"
        newNoise.proportional()    # consider the noise on the communication line as a ratio of the current being transmitted"
        
        connNoise = newNoise.getNoise()
        hDebug('conn', ("The noise on the connection is %f" % connNoise))
        return (self._incomingUnit.currentOutput * self.switch * self.weight) + connNoise
    
    def isActive(self):
        '''Return the status of the connection to active'''
        return self._status
    
    def switchToManual(self):
        "Change the state of the connection to manual"

        self.state = 'manual'

    def switchToUniselector(self):
        "Change the state of the connection to uniselector"

        self.state = 'uniselector'
    
    def toggleUniselectorState(self):
        "Toggle between 'manual' and 'uniselector'"
        if self.state == 'manual':
            self.state = 'uniselector'
        else:
            self.state = 'manual'
        
    def sameAs(self,aConnection): 
        '''Test if two connections are the same, which means:
        - same parameters, 
        - same incoming Unit  (first level parameters only)

        Notice that since incoming units have, in turn, input connections, 
        we cannot pursue the testing that deep because we may enter into a loop. 
        We only check the first level parameters'''

        sameAs = self.weight == aConnection.weight and \
                 self.switch == aConnection.switch and \
                 self.noise == aConnection.noise and \
                 self.state == aConnection.state and \
                 self.status == aConnection.status and \
                 self.incomingUnit.sameFirstLevelParamsAs(aConnection.incomingUnit)
        return sameAs
