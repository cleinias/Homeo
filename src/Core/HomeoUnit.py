from __future__ import division
from Core.HomeoNeedleUnit import *
from Core.HomeoUniselectorAshby import *
from Core.HomeoUniselector import *
from Core.HomeoConnection import *
from Helpers.General_Helper_Functions import withAllSubclasses
import numpy as np
import sys, pickle
from copy import copy
import StringIO


class HomeoUnitError(Exception):
    pass

class HomeoUnit(object):
    '''
    Created on Feb 19, 2013

    @author: stefano

    Homeo Unit is the fundamental element of a Homeostat.
    
    HomeoUnit represents a basic unit of Ashby's Homeostat (see Ashby's Design for a Brain, 1960, chp. 8). 
    HomeoUnit does know about its connections to other units (including itself). 

    HomeoUnit holds the  values describing the state of the unit at time t, as specified by Ashby.
    The design of this simulation of the Homeostat  was influenced by the C simulation described 
    by Alice Eldridge in "Ashby's Homeostat in Simulation," unpublished, 2002, 
    available at: http://www.informatics.sussex.ac.uk/users/alicee/NEWSITE/ecila_files/content/papers/ACEhom.pdf 

     Instance Variables:
     criticalDeviation        <Float>    Deviation of the needle from equilibrium (0 state). In Ashby's original electromechanical model, 
                                          this value is a function of the input current applied to the magnet that operates
                                          the needle AND the possible manual operation on the needle itself
     currentOutput            <Float>    The current  the unit outputs at time t. This value is proportional to criticalDeviation and typically between 0 and 1.
     inputConnections         <List>     A collection of HomeoConnections storing the units the presents unit is connected to and the associated weights. 
                                         It includes a connection to itself. 
     maxDeviation             <Float>    Maximum deviation from equilibrium
     nextDeviation            <Float>    The needle's deviation the unit will assume at at t+1. This is a function of criticalDeviation, 
                                         of viscosity (as a dampener), and potentiometer. It is limited at both ends by maxDeviation
                                         (i.e. maxDeviation negated < nextDeviation < maxDeviation)
     outputRange              <Dict>     The range of the output current, keyed as low and high. Default is -1 to 1.
     viscosity                <Float>    The viscosity of the medium in which the metallic needle of the original Ashbian unit is free to move. 
                                         It acts as a dampening agent on the change of output. Min is 0 (no effect), max is 1 (no movement)
     density                  <Float>    The density  of the medium in which the metallic needle of the original Ashbian unit is free to move. 
                                         Used to compute the drag at high velocities, if needed
     noise                    <Float>    As per Ashby's implementation, it represents the noise in the transmission medium 
                                         of the unit's connection to itself. In our implementation it is always identical 
                                         to the noise of a unit's first connection 
     potentiometer             <Float>   As per Ashby's implementation, it represents the weight of the unit's connection to itself. 
                                         In our implementation it is always identical to the weight of a unit's 
                                         first connection,---Check Design for a Brain, chp.8  for details
                                         Notice that the polarity of the self-connection (the switch, in Ashby terminology, which we follow)
                                         is **not** held in an instance variable. In our implementation it is always identical 
                                         to the polarity of a unit's first connection, that is: self.inputConnections[0].switch,
     time                      <Integer>  The internal tick counter
     uniselectorTime            <Integer> The internal tick counter for activation of the uniselector
     uniselectorTimeInterval    <Integer> The number of ticks that specifies how often to check that the output is in range and eventually activate uniselector
     uniselector       <HomeoUniselector> The uniselector that can modify the weights of input values coming from other units
     uniselectorActive          <Boolean>  Whether the uniselector mechanism is active or not
     needleCompMethod          <String>    Whether the unit's needle's displacement depends of the sum of its input, 
                                          or on the ratio between the sum of the inputs and the maxDeviation. 
                                          Possible values are 'linear' and 'proportional', default is 'linear'.
    inputTorque                <Float>    It represents the input force derived from the weighed sum of the inputs (as computed by computeTorque)
    active                     <String>   Whether the unit is active or not (on or off)
    status                     <String>   Active, Non Active, or other possible status
    debugMode                  <Boolean>  It control whether the running methods print out debugging information
    showUniselectorAction      <Boolean>  It controls whether the running methods print out when the uniselector kicks into action
    currentVelocity            <Float>    The current velocity of the needle moving in the trough
    needleUnit         <HomeoNeedleUnit>  Holds an instance of HomeoNeedleUnit, the class containing the parameters 
                                          of the needle used by the unit (mass, area, etc.)
    _physicalParameters        <Dict>      A dictionary containing equivalence factors between the simulation units and real physical parameters


    A HomeoUnit knows how to:

    - compute its next output on the basis of the input (received through connections stored in inputConnections) and its internal parameters
    - add a connection with a given unit as the incoming unit
    - periodically check that its outputValue has not become critical (outside the acceptable range) 
    - ask the uniselector to reset the weight of its inputConnections
    - print a description of itself with the values of all its parameters
     '''

    #===========================================================================
    # '''CLASS CONSTANTS'''
    #===========================================================================

    "The unit's output range is by default -1  to 1 to express the proportion of the needle's deviation" 
    unitRange = {'high':1,'low':-1}               

    "DefaultParameters is a class variable holding the  default values of all the various parameters of future created units."
    DefaultParameters  = dict(viscosity = 0,
                              maxDeviation=10,
                              outputRange = unitRange,
                              noise = 0,
                              potentiometer= 1,
                              time = 0,
                              switch = -1,                      # This value is used to control the polarity of a unit's self-connection
                              inputValue=0,
                              uniselectorTime= 0,               # How often the uniselector checks the thresholds, in number of ticks
                              uniselectorTimeInterval = 10,
                              needleCompMethod= 'linear',       # switches between linear and proportional computation of displacement
                              uniselectorActivated = False,
                              density = 1,                      # density of water
                              maxViscosity = (10^6),
                              critThreshold = 0.9)              # the ration of max deviation  beyond which a unit's essential variable's value  is considered critical 
    
    allNames = set()        # set of units' unique names
        
    #===========================================================================
    #  END OF CLASS CONSTANTS 
    #===========================================================================
    #===========================================================================
    # CLASS METHODS 
    #===========================================================================
    
    @classmethod    
    def readFrom(self,filename):
        '''This is a class method that create a new HomeoUnit instance from filename'''
        fileIn = open(filename, 'r')
        unpickler = pickle.Unpickler(fileIn)
        newHomeoUnit = unpickler.load()
        fileIn.close()
        return newHomeoUnit
    #===========================================================================
    #  INITIALIZATIONS AND GETTERS, SETTERS, PROPERTIES
    #===========================================================================
    def __init__(self):
        '''
        Initialize the HomeoUnit with the default parameters found in the Class variable 
        DefaultParameters. Assign a random but unique name and sets the output to 
        some value around 0, i.e. at equilibrium.
        These values are supposed to be overridden in normal practice, because the values are set by the simulation 
        (an instance of HomeoSimulation or by the graphic interface)
        '''
        self._viscosity = HomeoUnit.DefaultParameters['viscosity']
        self._maxDeviation = HomeoUnit.DefaultParameters['maxDeviation']     #set the critical deviation at time 0 to 0."
        self._outputRange = HomeoUnit.DefaultParameters['outputRange']
        self._noise = HomeoUnit.DefaultParameters['noise']
        self._potentiometer = HomeoUnit.DefaultParameters['potentiometer']
        self._time = HomeoUnit.DefaultParameters['time']
        self._uniselectorTime = HomeoUnit.DefaultParameters['uniselectorTime']
        self._uniselectorTimeInterval = HomeoUnit.DefaultParameters['uniselectorTimeInterval']
        self._needleCompMethod = HomeoUnit.DefaultParameters['needleCompMethod']
        self._uniselectorActivated = HomeoUnit.DefaultParameters['uniselectorActivated']
        self._critThreshold = HomeoUnit.DefaultParameters['critThreshold']

        '''A new unit is turned off, hence its velocity is 0, and 
          its criticalDeviation and nextDeviation are 0, and
          its inputTorque (from other units) is 0, and
          its currentOutput is 0'''
        self._currentVelocity = 0 
        self._criticalDeviation = 0
        self._nextDeviation = 0
        self._inputTorque = 0
        self._currentOutput = 0 
        
        self.needleUnit = HomeoNeedleUnit()


        "sets the correspondence between the simulation units and real physical units"
        self.__physicalParameters=dict(timeEquivalence = 1,           # 1 simulation tick corresponds to 1 second of physical time"
                                      lengthEquivalence = 0.01,       # 1 unit of displacement corresponds to 1 cm (expressed in meters)"
                                      massEquivalence = 0.001)        # 1 unit of mass equals one gram, or 0.001 kg"
    
        "creates the connection collection and connects the unit to itself in manual mode with a negative feedback"
        self._inputConnections = []
        self.setDefaultSelfConnection()

        "sets default uniselector settings."
        self.setDefaultUniselectorSettings()
        
        "give the unit  a default name"
        self._name = None
        self.setDefaultName()
        
        "generates a random output to set the unit close to equilibrium"
        self.setDefaultOutputAndDeviation()
        
        "turn the unit on"
        self._status= 'Active'
        self._debugMode = False
        self._showUniselectorAction = False
        
        
    "properties with setter and getter methods for external access"
    
    def getCriticalDeviation(self):
        return self._criticalDeviation
    
    def setCriticalDeviation(self,aValue):       
#        self._criticalDeviation = self._criticalDeviation
        self._criticalDeviation = aValue
    
    criticalDeviation = property(fget = lambda self: self.getCriticalDeviation(),
                                 fset = lambda self, value: self.setCriticalDeviation(value))
    
    def getNextDeviation(self):
        return self._nextDeviation
    
    def setNextDeviation(self,aValue):       
        self._nextDeviation = aValue
    
    nextDeviation = property(fget = lambda self: self.getNextDeviation(),
                                 fset = lambda self, value: self.setNextDeviation(value))

    def setViscosity(self, aValue):
        ''''Viscosity must be between 0 (zero effect)
        and 1 (all force canceled out)'''
        
        if aValue < 0 or aValue > 1:
            raise(HomeoUnitError, "The value of viscosity must always be between 0 and 1 (included)")
        else: self._viscosity = aValue
        
    def getViscosity(self):
        return self._viscosity
    
    viscosity = property(fget = lambda self: self.getViscosity(),
                         fset = lambda self, value: self.setViscosity(value))
      
    def setNeedleUnit(self, aValue):
        self._needleUnit = aValue
        
    def getNeedleUnit(self):
        return self._needleUnit
    
    needleUnit = property(fget = lambda self: self.getNeedleUnit(),
                         fset = lambda self, value: self.setNeedleUnit(value))

    def setPotentiometer(self, aValue):
        '''Changing the value of the potentiometer affects 
           the unit's connection to itself (which is always at position 0
           in the inputConnections list)'''
        self._potentiometer = aValue
        self._inputConnections[0].newWeight(aValue)

    def getPotentiometer(self):
        return self._potentiometer
    potentiometer = property(fget = lambda self: self.getPotentiometer(),
                             fset = lambda self, value: self.setPotentiometer(value))  
    
    def setNoise(self, aValue):
        '''Set the value of the unit's internal noise. 
            As noise must always be between 0 and 1,
            clip it otherwise'''
    
        self._noise = np.clip(aValue, 0,1)
                    
    def getNoise(self):
        return self._noise
    noise = property(fget = lambda self: self.getNoise(),
                     fset = lambda self, value: self.setNoise(value))  
    
    def setTime(self, aValue):
        self._time = aValue
    def getTime(self):
        return self._time
    time = property(fget = lambda self: self.getTime(),
                    fset = lambda self, value: self.setTime(value))  
    
    def setUniselectorTime(self, aValue):
        self._uniselectorTime = aValue
    def getUniselectorTime(self):
        return self._uniselectorTime
    uniselectorTime = property(fget = lambda self: self.getUniselectorTime(),
                               fset = lambda self, value: self.setUniselectorTime(value))  
    
    def setNeedleCompMethod(self, aString):
        self._needleCompMethod = aString
    def getNeedleCompMethod(self):
        return self._needleCompMethod
    needleCompMethod = property(fget = lambda self: self.getNeedleCompMethod(),
                                fset = lambda self, value: self.setNeedleCompMethod(value))  
        
    def setMaxDeviation(self,aNumber):
        '''Max deviation is always positive, 
           because the unit's deviation is centered around 0. 
           Ignore negative numbers'''
    
        if aNumber > 0:
            self._maxDeviation = aNumber
        else:
            raise(HomeoUnitError, "The value of MaxDeviation must always be positive")
            
    def getMaxDeviation(self):
        return self._maxDeviation
    maxDeviation = property(fget = lambda self: self.getMaxDeviation(),
                            fset = lambda self, value: self.setMaxDeviation(value))  
    
    def setOutputRange(self, minOut,maxOut):
        aDict = {'low':minOut, 'high':maxOut}
        self._outputRange = aDict
    def getOutputRange(self):
        return self._outputRange
    outputRange = property(fget = lambda self: self.getOutputRange(),
                           fset = lambda self, minOut, maxOut: self.setOutputRange(minOut,maxOut))  

    def setUniselectorActive(self,aBoolean):
        self._uniselectorActivated = aBoolean
    def getUniselectorActive(self):
        return self._uniselectorActivated
    uniselectorActive = property(fget = lambda self: self.getUniselectorActive(),
                                 fset = lambda self, value: self.setUniselectorActive(value))  
    
    def setUniselectorTimeInterval(self,aValue):
        self._uniselectorTimeInterval = aValue
    def getUniselectorTimeInterval(self):
        return self._uniselectorTimeInterval
    uniselectorTimeInterval = property(fget = lambda self: self.getUniselectorTimeInterval(),
                                       fset = lambda self, value: self.setUniselectorTimeInterval(value))  

    def setActive(self, aBoolean):
        if aBoolean == True or aBoolean == False:
            self.active = aBoolean
        else:
            raise HomeoUnitError("The value of instance variable active can only be a Boolean") 
        
    def getActive(self):
        return self.active
    
    active = property(fget = lambda self: self.getActive(),
                      fset = lambda self, aBoolean: self.setActive(aBoolean))
                                
    def getCurrentOutput(self):
        return self._currentOutput
        
    def setCurrentOutput(self, aValue):
        self._currentOutput = aValue
            
        "For testing"
        if self._debugMode == True:
            sys.stderr.write(str(self._currentOutput))
            sys.stderr.write('\n')

    currentOutput = property(fget = lambda self: self.getCurrentOutput(),
                             fset = lambda self, aBoolean: self.setCurrentOutput(aBoolean))
  
    def getHighRange(self):
        return self.outputRange['high']

    def setHighRange(self,aValue):
        self.outputRange['high'] =  aValue

    highRange = property(fget = lambda self: self.getHighRange(),
                         fset = lambda self, aValue: self.setHighRange(aValue))
    
    def getLowRange(self):
        return self.outputRange['low']

    def setLowRange(self,aValue):
        self.outputRange['low'] =  aValue

    lowRange = property(fget = lambda self: self.getLowRange(),
                         fset = lambda self, aValue: self.setLowRange(aValue))

    def getInputConnections(self):
        return self._inputConnections
    
    def setInputConnections(self, aList):
        self._inputConnections = aList
        
    inputConnections = property(fget = lambda self: self.getInputConnections(),
                                fset = lambda self, aList: self.setInputConnections(self, aList))

    def getInputTorque(self):
        return self._inputTorque

    def setInputTorque(self,aValue):
        self._inputTorque = aValue

    inputTorque = property(fget = lambda self: self.getInputTorque(),
                           fset = lambda self,aValue: self.setInputTorque(aValue))

    def getCurrentVelocity(self):
        return self._currentVelocity

    def setCurrentVelocity(self, aValue):
        self._currentVelocity = aValue
    
    currentVelocity = property(fget = lambda self: self.getCurrentVelocity(),
                              fset = lambda self, aValue: self.setCurrentVelocity(aValue)) 

    def setSwitch(self,aNumber):
        '''Set the polarity of the unit's self-connection. 
           aNumber must be either -1 or +1, otherwise method 
           raises an exception.
           
           The switch can only be set by changing the sign of weight
           of the the unit's connection to itself (which is always 
           at location 0 in the inputConnections collection)'''

        acceptValues = (-1,1)
        oldWeight = self.inputConnections[0].weight
        newWeight = abs(oldWeight) * aNumber

        if aNumber in acceptValues:
            self.inputConnections[0].newWeight(newWeight)
        else: 
            raise  HomeConnection
    
    def getSwitch(self):
        return self.inputConnections[0].switch
    
    switch = property(fget = lambda self: self.getSwitch(),
                      fset = lambda self, aValue: self.setSwitch(aValue))
    
    def getMinDeviation(self):
        '''Deviation is always centered around 0. 
           Min deviation is less than 0 and equal to maxDeviation negated'''

        return - self.maxDeviation

    def setMinDeviation(self,aNumber):
        '''Deviation is always centered around 0. 
           Min deviation must be less than 0 and equal to maxDeviation negated. 
           If we change the minimum we must change the maximum as well'''
        
        if aNumber < 0:
            self.maxDeviation = - aNumber
    
    minDeviation = property(fget = lambda self: self.getMinDeviation(),
                            fset= lambda self, aValue: self.setMinDeviation(aValue))

    def getDensity(self):
        return self._density

    def setDensity(self,aValue):
        self._density = aValue

    density = property(fget = lambda self: self.getDensity(),
                           fset = lambda self,aValue: self.setDensity(aValue))
    
    def getStatus(self):
        return self._status

    def setStatus(self,aValue):
        self._status = aValue

    status = property(fget = lambda self: self.getStatus(),
                           fset = lambda self,aValue: self.setStatus(aValue))
    
    def getUniselector(self):
        return self._uniselector
    
    def setUniselector(self,aUniselectorInstance):
        '''Set the uniselector and check that it is a valid one'''
        
        if HomeoUniselector.includesType(aUniselectorInstance.__class__.__name__): 
            self._uniselector = aUniselectorInstance
            self.uniselectorTime = 0
    
    uniselector = property(fget = lambda self: self.getUniselector(),
                           fset = lambda self, aString: self.setUniselector(aString))
    
    def getCritThreshold(self):
        return self._critThreshold
    
    def setCritThreshold(self,aValue):
        "Must be > 0 and  < 1. Raise error otherwise"
        if aValue > 0 and aValue < 1:
            self._critThreshold = aValue
        else:
            raise(HomeoUnitError, "The value of the critical threshold must be between 0 and 1 excluded")
    
    critThreshold = property(fget = lambda self: self.getCritThreshold(),
                            fset = lambda self, aValue: self.setCritThreshold(aValue))
    
    def getName(self):
        return self._name
    
    def setName(self, aString):
        "aString must be a new name not present in HomeoUnit.allNames"
        if aString not in HomeoUnit.allNames:
            self._name = aString
            HomeoUnit.allNames.add(aString)
        else:
            raise(HomeoUnitError, "The name %s exists already" % aString)
    
    name = property(fget = lambda self: self.getName(),
                    fset = lambda self, aString: self.setName(aString))  
 
    def activateUnit(self):
        self._status = 'Active'

    
    #===========================================================================
    #  End of setter and getter methods"
    #===========================================================================

    def setDefaultSelfConnection(self):
        '''
        Connect the unit to itself in manual mode with the default feedback and no noise
        '''
        self.addConnectionUnitWeightPolarityNoiseState(self,self.potentiometer,HomeoUnit.DefaultParameters['switch'],0,'manual')
   
    def setNewName(self):
        pass

    def setDefaultOutputAndConnections(self):
        pass

    def setDefaultUniselectorSettings(self):
        "set default uniselector settings"

        self.uniselector = HomeoUniselectorAshby()
        self.uniselectorActive = True
    
    def setDefaultName(self):
        '''Assign a default unique name to the unit with the help of an auxiliary method'''
        
        self.name = self.produceNewName()
        
    def setDefaultOutputAndDeviation(self):

        randOutput = np.random.uniform(0,0.5)       #generates a random output to set the unit close to equilibrium"
        currentOutput = randOutput

        "set the critical deviation at time 0 to 0."
        self.criticalDeviation = 0

    def randomizeAllConnectionValues(self):
        '''Reset the weight, switch, and noise of all connections to random values 
           (see HomeoConnection for details).
           Do not touch the self connection of the unit to itself.  
           Do not change the uniselector operation'''

        for conn in self._inputConnections:  
                if not conn.incomingUnit == self:
                    conn.randomizeConnectionValues()
        
    #===========================================================================
    # TESTING METHODS
    #===========================================================================
    def isActive(self):
        if self._status == 'Active':
            return True
        else:
            return False
    
    def isConnectedTo(self,aHomeoUnit):
        '''Test whether there is a connection coming from aHomeoUnit'''
            
        connUnits = [x.incomingUnit for x in self._inputConnections]
        return (aHomeoUnit in connUnits)


    def sameAs(self,aHomeoUnit):
        '''Test whether two units are the same, by checking (and delegating the actual checks):
               1. name and other first-level parameters (potentiometer, switch, etcetera
               2. the number of connections
               3. the parameters of each  connection
               4. the names of the connected units'''

        return self.sameFirstLevelParamsAs(aHomeoUnit)  and \
               self.sameConnectionsAs(aHomeoUnit)
               
    def sameFirstLevelParamsAs(self,aHomeoUnit):
        '''Checks whether the first level parameters of two units 
            (i.e. not the connections) are the same.
            Does not include dynamic parameters (output, currentOutput, 
            nextDeviation, criticalDeviation, time, uniselectorTime, inputTorque).
            Do not check uniselector transition tables, only kind of device'''

        return (self.name ==  aHomeoUnit.name and
                self.viscosity == aHomeoUnit.viscosity and 
                self.maxDeviation == aHomeoUnit.maxDeviation and 
                self.outputRange['high'] == aHomeoUnit.outputRange['high'] and 
                self.outputRange['low'] == aHomeoUnit.outputRange['low'] and 
                self.noise == aHomeoUnit.noise and 
                self.potentiometer == aHomeoUnit.potentiometer and 
                self.switch == aHomeoUnit.switch and 
                self.uniselector.sameKindAs(aHomeoUnit.uniselector) and 
                self.uniselectorTimeInterval == aHomeoUnit.uniselectorTimeInterval and 
                self.uniselectorActive == aHomeoUnit.uniselectorActive and 
                self.needleCompMethod == aHomeoUnit.needleCompMethod and 
                self.status == aHomeoUnit.status)
        
    def sameConnectionsAs(self, aHomeoUnit): 
        "Check that two units have the same connections"

        connSame = True
        if not len(self.inputConnections) == len(aHomeoUnit.inputConnections): 
            return False
        else:
            for conn1, conn2 in zip(self.inputConnections, aHomeoUnit.inputConnections):
                if not conn1.sameAs(conn2):
                        connSame = False
        
        return connSame
        

    def isReadyToGo(self):
        '''Make sure that unit has all the parameters it needs to operate properly.
    
           criticalDeviation    is notNil and
           maxDeviation    is notNil
           outputRange        is notNil
           viscosity            is notNil
           noise            is notNil
           potentiometer     is notNil     
           if  uniselectorActive is true then
               uniselector                 is notNil
               uniselectorTime               is notNil
               uniselectorTimeInterval      is notNil'''

        if self.uniselectorActive:
            uniselectorConditions = (self.uniselector is not None and 
                                     self.uniselectorTime is not None and 
                                     self.uniselectorTimeInterval is not None)
        else:
            uniselectorConditions = True
        
        return (self.criticalDeviation is not None and 
                self.maxDeviation is not None and 
                self.outputRange is not None and 
                self.viscosity is not None and 
                self.noise is not None and 
                self.potentiometer is not None and 
                uniselectorConditions)
   
    def essentialVariableIsCritical(self):
        '''Checks if the next output is critical, 
            i.e. too close to the limit of the  acceptable range, stored in maxDeviation.
            The critical threshold is stored in critThreshold and defaults to 0.9
            in DefaultParameters['critThreshold']'''

        return self.nextDeviation >= self.critThreshold and self.nextDeviation <= self.critThreshold

#------------------------------------------------------------------------------ 

   #============================================================================
   # CONNECTION METHODS
   #============================================================================
   
    def addConnectionUnitWeightPolarityState(self,aHomeoUnit,aWeight,aSwitch,aString):
        '''
        Add a new connection to the unit and set the connection parameters.
        Notice that you always connect the unit starting from the destination, 
        HomeoUnits don't know anything at all about where their output goes.
        If the parameters are not within the expected values, 
        the accessor methods of HomeoConnection will raise exceptions
        '''
        aNewConnection = HomeoConnection()

        aNewConnection.incomingUnit = aHomeoUnit
        aNewConnection.outgoingUnit = self
        aNewConnection.newWeight(aWeight * aSwitch) #must be between -1 and +1
        aNewConnection.state = aString          # must be 'manual' or 'uniselector'"
                
        self.inputConnections.append(aNewConnection)

    def addConnectionUnitWeightPolarityNoiseState(self,aHomeoUnit,aWeight,aSwitch,aNoise,aString):
        '''
        Add a new connection to the unit and set the connection parameters.
        Notice that you always connect the unit starting from the destination, 
        HomeoUnits don't know anything at all about where their output goes.
        If the parameters are not within the expected values, 
        the accessor methods of HomeoConnection will raise exceptions
        '''
        aNewConnection = HomeoConnection()

        aNewConnection.incomingUnit = aHomeoUnit
        aNewConnection.outgoingUnit = self
        aNewConnection.newWeight(aWeight * aSwitch) # must be between -1 and +1
        aNewConnection.noise = aNoise               # must be between 0 and 1"
        aNewConnection.state = aString              # must be 'manual' or 'uniselector'"
                
        self.inputConnections.append(aNewConnection)

    def removeConnectionFromUnit(self, aHomeoUnit): 
        '''Remove the connection(s) to self and originating from aHomeoUnit'''
        
        for conn in self._inputConnections:
            if conn.incomingUnit == aHomeoUnit:
                self.inputConnections.remove(conn)

    def addConnectionWithRandomValues(self,aHomeoUnit):
        '''
        Add a new connection to the unit. Uses the random values (weight, noise, and polarity) 
        selected by the initialization method of HomeoConnection.
        Notice that you always connect the unit starting from the destination, i.e. from the input side, and never from the output side.
        HomeoUnits don't know anything at all about where their output goes.
        If the parameters are not within the expected values, the accessor methods of HomeoConnection will raise exceptions
        '''

        aNewConnection = HomeoConnection()        # The initialize method of HomeoConnection sets random weights"
        aNewConnection.incomingUnit =  aHomeoUnit
        aNewConnection.outgoingUnit =  self
        self._inputConnections.append(aNewConnection)
    

    def saveTo(self,filename):
        "Pickle yourself to filename"

        fileOut = open(filename, 'w')
        pickler = pickle.Pickler(fileOut)
        pickler.dump(self) 
        fileOut.close()

    
    def setRandomValues(self):
        "sets up the unit with random values"

        self.viscosity = np.random.uniform(0.8,1)
        self.noise = np.random.uniform(0, 0.1)
        self.potentiometer = np.random.uniform(0, 1)

        switchSign = np.sign(np.random.uniform(-1, 1)) #sets the polarity of the self-connection, avoid  0"
        if switchSign == 0:
            switchSign = 1
        self._switch = switchSign 

        "generates a random output  over the whole range"
        self._currentOutput =  np.random.uniform(0, 1)    
        "set the critical deviation to a random value over the whole range"                                                         
        self._criticalDeviation = np.random.uniform(self.outputRange['low'], self.outputRange['high']) 
   
    def activate(self):
        self.active = True

    def disactivate(self):
        self.active = False

    def maxConnectedUnits(self, anInteger):
        "Changes the parameter to the Uniselector for the maximum number of connected units"
        
        self._uniselector.unitsControlled = anInteger

    def toggleDebugMode(self):
        "Controls whether the running methods print out debug information"

        if self._debugMode is True: 
            self._debugMode = False
        else: 
            self._debugMode = True

    def toggleShowUniselectorAction(self):
        "Control whether the running methods print out information when the uniselector kicks into action"

        if self.showUniselectorAction is True:
            self.showUniselectorAction = False
        else:
            self.showUniselectorAction = True
            
    def isNeedleWithinLimits(self, aValue):
        '''Check whether the proposed value exceeds the unit's range (both + and -)'''

        return np.clip(aValue, self.minDeviation, self.maxDeviation) == aValue

    def uniselectorChangeType(self,uniselectorType):
        "Switch the uniselector type of the unit"
        
        if HomeoUniselector.includesType(uniselectorType): 
            self.uniselector = eval(uniselectorType)()
            self.uniselectorTime = 0
        else:
            raise HomeoUnitError("%s is not a valid HomeoUniselector class" % uniselectorType)
        
    def produceNewName(self):
        '''Produce a name made up of  'Unit-'  plus a unique integer.
           Check the name does not exist yet'''
        
        i = 1
        while ('Unit-' + str(i)) in HomeoUnit.allNames:
            i += 1
        else:
            return ('Unit-' + str(i))
            

    #===========================================================================
    # "Running methods that update a HomeoUnit's value"
    #===========================================================================
    
    def clearFutureValues(self):
        '''Set to 0 the internal values used for computing future states'''

        self.nextDeviation = 0
        self.inputTorque = 0
        self.currentOutput =  0

    def clipDeviation(self, aValue): 
        '''Clip the unit's criticalDeviation value if it exceeds its maximum or minimum. 
            Keep the sign of aValue'''
            
        return np.clip(aValue,self.minDeviation,self.maxDeviation)
        

    def newRandomNeedlePosition(self):
        '''Compute a random value for the needle position within the accepted range'''

        return np.random.uniform(self.minDeviation, self.maxDeviation)
    
    def selfUpdate(self):
        '''This is the master loop for the HomeoUnit. It goes through the following sequence:
        1. compute new needle's deviation (nextDeviation (includes reading inputs))
        2. update the current output on the basis of the deviation.
        3. check whether it's time to check the essential value and if so does it and  update the counter (uniselectorTime) [this might change the weight of the connections]
        4. Move the needle to new position and compute new output'''

        "1. compute where the needle should move to"
        "Testing"
        if self._debugMode:
            sys.stderr.write('Current Deviat. at time: %s for unit %s is %f' 
                             % self.name, str(self.time), str(self.criticalDeviation)) 
            sys.stderr.write('\n')
        
        self.computeNextDeviation()

        "2. update times"
        self.updateTime()
        self.updateUniselectorTime()

        '''3. check whether it's time to check the uniselector/detection mechanism and if so do it. 
           Register that the uniselector is active in an instance variable'''
        if (self.uniselectorTime >= self.uniselectorTimeInterval and
            self.uniselectorActive):
            if self.essentialVariableIsCritical():
                self.operateUniselector
                self.uniselectorActive = 1
            else:
                self.uniselectorActive = 0          

        '''4. updates the needle's position (critical deviation) with clipping, 
            if necessary, and updates the output'''
        self.criticalDeviation = self.clipDeviation(self.nextDeviation)
        self.computeOutput()
        self.nextDeviation = 0
    
    def computeNextDeviation(self):
        '''Computes the output current at time t+1 on the basis of the current input 
        and the various parameters of the unit.
        This basic function mimicks Asbhy's original device by the following procedure:

        1. Try to move the needle to a new position (on the basis of  the input values
           computed by computeTorque) 
           (the details of this operation are in method HomeoUnit >> newNeedlePosition: aValue and in HomeoUnit>>computeTorque
        2. clip value if it is outside maxRange
        3. put new value in criticalDeviation

        One alternative  possibility would have been  to use a minimal function like
        the one used by A Eldridge in her simulation (see Eldridge 2000, p.20): 
        nextOutput := (input(j) * weight(j) * ) + noise  (with j ranging over  all units connected to the current unit)

        This approach simplifies considerably the simulation, but has the disadvantage
        of  reducing the role of the unit to nil. In fact, (in Eldridge's simulation) 
        all the work is done by the system, which reads, for every tick of time, the
        outputs from the various connected units, computes new outputs, and updates 
        the units. In other words, this approach reduces the homeostat's units 
        to simple data structures (which is literally what they are in her C program),
        deprived of any possibility of 'action', i.e. of any behavior. 
        Our approach here will be different, by allowing a partial separation 
        between homeostat, units, and connections. It follows that the computation 
        of the unit's next value is internal to unit itself, even if it considers 
        values (obtained from inputConnections) that may have been deposited from the
        outside. 
        This approach allows the possibility that different units may have 
        different behaviors, etc. and it also allows for the possibility of 
        having the units being operated upon by means other than the inputs coming
        from other homeoUnits. For instance, input coming directly from the environment,
        like the direct manipulation of the needles. It also forces the simulation 
        to provide a closer resemblance of Ashby's original electro-mechanical device. 
        Furthermore, Eldridge's simple approach can be easily recovered by reducing the
        computation of the unit's next output to the sum of values stored 
        in inputConnections, and by setting the range of the needles' deviation 
        (maxDeviation) to 1. 
        In short: Eldridge's model as reimplemented here would have the following method: 
        self.computeNextOuput 
        self.nextOutput = sum([conn.output() for conn in inputsCollection])

        Our method is close to hers and basically reduces to this behavior when 
        all the parameters specific to the unit are uninfluent. That is, when: 
        noise = 0, viscosity = 0, and  there is no direct outside influence. 
        Nonetheless, encapsulating the computation inside the unit allows for a  
        more flexible system that can be easily extended to encompass more 
        sophisticated behavior.'''
    
        '''1. first update the current value of critical deviation with 
        the unit's internal noise'''
        self.updateDeviationWithNoise()
        "2. then update the deviation"
        self.computeTorque()
        self.nextDeviation  = self.newNeedlePosition(self.inputTorque)

    def computeOutput(self):
        '''Scale the current criticalDeviation to the output range.
           Clip the output to within the allowed output range.'''

        "1. Scaling"
        outRange = float((self.outputRange['high'] - self.outputRange['low']))
        lowDev = self.minDeviation
        devRange = float(self.maxDeviation - lowDev)
        out = ((self.criticalDeviation - lowDev) *
               (outRange / devRange ) + self.outputRange['low'])
                        
        "2.Clipping"
        self.currentOutput = np.clip(out, self.outputRange['low'],self.outputRange['high'])

    def computeTorque(self):
        '''In order to closely simulate Asbhy's implementation, 
        computeTorque would have to compute the torque affecting the needle
        by solving a set of differential equations whose coefficients 
        represents the weighted values of the input connections. This is the 
        approach followed by Capehart (1967) in his simulaton of the Homeostat 
        in Fortran. See the comment to the method newNeedlePosition for a discussion.
        
        Here we simply compute the sum of the weighted input values extracted from 
        the inputsCollection on all the connections that are active'''

        activeConnections = [conn for conn in self.inputConnections if (conn.isActive() and 
                                                                        conn.incomingUnit.isActive())]

        self.inputTorque = sum([conn.output() for conn in activeConnections])

        "Testing"
        if self._debugMode:
            sys.stderr.write('Current torque at time: %s for unit %s is %f' %
                             str(self.time), self.name, self.inputTorque)
            sys.stderr.write('\n')

    def newLinearNeedlePosition(self,aTorqueValue):
        '''See method newNeedlePosition for an extended comment on how 
        to compute the displacement of the needle. Briefly, here we just sum 
        aTorqueValue to the current deviation.
        
        Internal noise is computed in method updateDeviationWithNoise, while noise
        on the connections is computed by HomeoConnections when they return values'''

        totalForce = aTorqueValue    
        '''NOTE: the HomeoUnit method that computes aTorqueValue (passed to this method)
        does not  compute the net force acting on the needle 
        by adding the (negative) force produced by the drag and/ or frictional forces). 
        
        Only subclasses of HomeoUnit do that. Here we simply consider the viscosity 
        of the medium as a fractional multiplier of the torque.
        Viscosity is max at 1 (All force canceled out) and minimum at 0 (no effect)   
        It is a proxy for the more sophisticated computation of drag carried out
        in subclasses'''
        
        "Applying the viscosity "
        totalForce = totalForce * (1 - self._viscosity)
        
        newVelocity = totalForce / self.needleUnit.mass    
        '''In an Aristotelian model, the change in displacement (= the velocity) 
        is equal to the force affecting the unit divided by the mass: F = mv or v = F/m
        '''
        
        
        "Testing"
        if self._debugMode:
            sys.stderr.write('new position at time: %s for unit %s will be %f ' %
                             str(self.time + 1),
                             self.name,
                             self.criticalDeviation + newVelocity)
            sys.stderr.write('\n')
    
        return self.criticalDeviation + newVelocity    
        '''In an Aristotelian model, new displacement is old displacement totalForce
        plus velocity: x = x0 + vt, with t obviously = 1 in our case'''

    def newNeedlePosition(self,aTorqueValue):
        '''Compute the new needle position on the basis of aTorqueValue, 
        which represents the torque applied to the unit's needle. 
        This method is marquedly different from Ashby's implementation, 
        even if it somehow captures its intent. A longer discussion is appended  below.'''

        if self.needleCompMethod == 'linear':
            return self.newLinearNeedlePosition(aTorqueValue)
        else:
            if self.needleCompMethod == 'proportional':
                return self.newProportionalNeedlePosition(aTorqueValue)
            else:
                return self.newRandomNeedlePosition()       #defaults to a random computation method if the method is not specified"

        """In Asbhy's original implementation, each incoming connection corresponded to a coil 
        around the unit's magnet. The sum of the input currents flowing through the coils produced  
        a torque on the magnet, which, in turn, moved the needle in the trough.
        In order to closely simulate Asbhy's implementation, newNeedlePosition would have 
        to compute the torque affecting the needle by solving a set of differential equations 
        whose coefficients represent the weighted values of the input connections. This is 
        the approach followed by Capehart (1967) in his simulaton of the Homeostat in Fortran.
        
        However, it seems pointless to use differential equations to model a physical mechanism 
        which was originally devised to model a physiological system. After all, as Capehart 
        himself acknowledges, the Homeostat is a kind of analogue computer set up to compute 
        the fundamental features of the system it models.. We might as well use a different 
        kind of computer, assuming we are able to capture the essential features as accurately. 
        In this respect, we follow Ashby's suggestion that 'the torque on the magnet 
        [ i.e. the needle] is approximately proportional to the algebraic sum of the currents 
        in A, B, and C' (Ashby 1960:102, sec 8/2), where the coils A, B, C, (and D, i.e. 
        the unit itself) carry a current equal to the weighted input. Thus, this method 
        produces a value that is proportional to the inputValue.
        
        However,  it might be argued (for instance by a dynamic system theorist) that 
        a thoroughly digital simulation of the Homeostat like this one loses what is 
        most essential to it: the continuity of real-valued variables operating in 
        real time. Anyone accepting this objection may partially meet it by:
        
        1. subclassing HomeoUnit, 
        2. adding a method that produces differential equation describing the Torque
        3. and replacing the two methods computeTorque and newNeedlePosition: aTorqueValue 
        with numeric computations of the solutions of the diff equations.
        
        See Ashby, Design for a Brain, chps. 19-22 for a mathematical treatment of the 
        Homeostat and Capehart 1967 for suggestions on a possible implementation 
        (which requires a Runge-Kutta diff solution routine or equivalent and 
        Hutwitz convergence test on the coefficient matrix)
        
        Our method(s) assumes:
        
        1. that the torque is simply the sum of the input connections, hence a value 
        included in +/-  (inputConnections size) (since the max value of any unit's output 
        and hence  of any input, is 1 and the minimum  -1)
        
        2. the torque represents the force that displaces the needle from its current position. 
        The value of this displacement is obviously directly proportional to the force. 
        However, the constant of proportionality is important: if the displacement is 
        simply equal to the torque, which, in turn, is equal to the sum of inputs, 
        then the ***potential displacement*** grows linearly with the connected units. 
        If, instead, the displacement is equal to the ratio between the maximum torque 
        and the maximum deviation, then the ***potential displacement*** is independent 
        from the number of connected units and will depend more directly on the values of 
        the incoming units rather than their number. It is obvious that the behaviototalForcer of a 
        collection of units, i.e. a homeostat, will be different in either case. Ashby's 
        probably followed the former model, as evidenced by his (widely reported) comments 
        about the direct relation between instability and number of units (see alsototalForce 
        Capehart 1967 for comments to the same effect). 
        It must be admitted, however, that a careful manipulation of the weights of the 
        connection may reduce the difference between the two methods: one would have to 
        uniformly reduce the weights whenever a new connection is added to transform the 
        first ('Ashby's') approach into the second.
        
        In order to allow experimentation with either approach, we include both methods: 
        HomeoUnit().newLinearNeedlePosition and HomeoUnit().newProportionalNeedlePosition
        The choice between the two is determined by the value of the instance variable 
        needleCompMethod. Default (stored in the class variable) is linear.
        
        The viscosity is between 0 and 1, with 0 being the maximum (needle unable to move) 
        and 1 being the minimum (no effect on movement)"""


    def newProportionalNeedlePosition(self, aTorque):
        '''See method newNeedlePosition for an extended comment on how 
        to compute the displacement of the needle'''

        totalForce = aTorque  / (self.maxDeviation  * 2.)
        totalForce = totalForce * (1- self.viscosity)
        newVelocity = totalForce / self.needleUnit.mass   
        return self.criticalDeviation + newVelocity
    
    def operateUniselector(self):
        '''Activate the uniselector to randomly change the weights of the input connections        
         (excluding the self connection) and reset the tick count of uniselector activation to 0'''



        "We save the values about the units that have changed weights, old weights and new weight for debugging"
        weightChanges = []
        for conn in self.inputConnections:
            if not conn.incomingUnit == self:
                if conn.state ==  'uniselector' and conn.active():
                    change = []
                    change.append(self.incomingUnit.name)
                    change.append(conn.weight)
                    changedWeight = self.uniselector.produceNewValue()
                    change.append(changedWeight)
                    weightChanges.append(change)
                    conn.newWeight(changedWeight)
        self.uniselectorTime = 0
        self.uniselector.advance()



        "For debugging"
        if self.showUniselectorAction():
            for connChange in weightChanges:
                sys.stderr.write('At time: %i, %s activated uniselector for unit %s switching weight from: %f to: %f' %
                                 (self.time) + 1,
                                 self.name,
                                 connChange[0],
                                 connChange[1],
                                 connChange[2])
                sys.stderr.write('\n')

    def physicalVelocity(self):
        '''Convert the velocity of the unit into a value expressed in 
           physical units (m/s) according to the physical equivalence parameters'''

        return self.currentVelocity * (self._physicalParameters['lengthEquivalence'] / self._physicalParameters['timeEquivalence'])

    def updateDeviationWithNoise(self):
        '''Apply the unit's internal noise to the critical deviation and update accordingly.  
           Computation of noise uses the utility HomeoNoise class'''
        
        newNoise = HomeoNoise()
        newNoise.withCurrentAndNoise(self.criticalDeviation, self.noise)
        newNoise.distorting()    # since the noise is a distortion randomly select either a positive or negative value for noise"
        newNoise.normal()        # compute a value for noise by choosing a normally distributed random value centered around 0."
        newNoise.proportional()  # consider noise as the ration of the current affected by noise"   
        self._criticalDeviation = self._criticalDeviation + newNoise.getNoise()    # apply the noise to the critical deviation value"


    def updateTime(self):
        '''Do nothing. In the current model, time is updated by the homeostat, 
           the homeounit are basically computing machine with no knowledge of time'''

        pass

    def updateUniselectorTime(self):
        '''Updates the tick counter fore the uniselector'''
        
        self.uniselectorTime = self.uniselectorTime + 1

 #==============================================================================
 # Printing
 #==============================================================================
 
    def printDescription(self):
        '''Return a string containing a text representation of 
           all of the the unit's instance variables'''

        aStream = StringIO.StringIO()
        aStream.write('aHomeoUnit with values: \n')
        for ivar in sorted(vars(self).keys()):
            aStream.write(ivar)
            aStream.write(' --> ')
            aStream.write(vars(self)[ivar])
            aStream.write('\t')
            aStream.write
        aStream.write('\n')
        content = aStream.getvalue()     
        aStream.close()
        return content

    def printOn(self, aStream):
        "Returns a brief description of the unit"

        aStream.write(self.__class__.__name__)
        aStream.write(': ')
        aStream.write(self.name)
        return aStream
        
    def __del__(self):
        ''''Remove a HomeoUnit's name from the set of used names.
            Subclasses' instances must call this method explicitly 
            to remove  their names'''
        if self._name is not None:
            HomeoUnit.allNames.remove(self._name)
        
        
        
        
        