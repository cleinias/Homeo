from Core.HomeoNeedleUnit import *
from Core.HomeoUniselectorAshby import *
from Core.HomeoUniselector import *
from Core.HomeoConnection import *
from Helpers.General_Helper_Functions import withAllSubclasses
import numpy as np
import sys, pickle
from copy import copy


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
    The design of this simulation of the Homeostat  has been influenced by the C simulation described 
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
     outputRange              <Dict>     The range of the output current, keyed as low and high. Default is 0 to 1.
     viscosity                <Float>    The viscosity of the medium in which the metallic needle of the original Ashbian unit is free to move. 
                                         It acts as a dampening agent on the change of output
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
    physicalParameters        <Dict>      A dictionary containing equivalence factors between the simulation units and real physical parameters


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
    DefaultParameters  = dict(viscosity = 1,
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

        "A new unit is turned off, hence its velocity is 0 and its criticalDeviation is 0"
        self._currentVelocity = 0 
        self._criticalDeviation = 0 
        
        self._needleUnit = HomeoNeedleUnit()


        "sets the correspondence between the simulation units and real physical units"
        self.__physicalParameters=dict(timeEquivalence =1,            # 1 simulation tick corresponds to 1 second of physical time"
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
        "Do nothing"        
        self._criticalDeviation = self._criticalDeviation
    
    criticalDeviation = property(fget = lambda self: self.getCriticalDeviation(),
                                 fset = lambda self, value: self.setCriticalDeviation(value))
    
    def setViscosity(self, aValue):
        self._viscosity = aValue
    def getViscosity(self):
        return self._viscosity
    
    viscosity = property(fget = lambda self: self.getViscosity(),
                         fset = lambda self, value: self.setViscosity(value))
      
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
    
        if aValue <= 1:
            if aValue >=0:
                self._noise = aValue
            else:
                self._noise = 0
        else:
            self._noise = 1
                    
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
    
    def setOutputRange(self, aDict):
        self._outputRange = aDict
    def getOutputRange(self):
        return self._outputRange
    outputRange = property(fget = lambda self: self.getOutputRange(),
                           fset = lambda self, value: self.setOutputRange(value))  

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
        set._currentOutput = aValue
    
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
           defaults to a negative feedback connection (i.e. -1)
          Notice that  changing the value of the unit's switch 
          affects the unit's connection to itself 
          (which is always at location 0  in the inputConnections collection)'''

        accValues = (-1,1)
        if aNumber in accValues:
            self._inputConnections[0].switch = aNumber
        else: 
            self._inputConnections[0].switch = -1
    
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
    
    #===========================================================================
    #  End of setter and getter methods"
    #===========================================================================

    def unitActive(self, aBoolean):
        self._status= True

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
    def isConnectedTo(self,aHomeoUnit):
        '''Test whether there is a connection coming from aHomeoUnit'''
            
        connUnits = [x.incomingUnit for x in self._inputConnections]
        return (aHomeoUnit in connUnits)

    def isActive(self):
        self._status = 'Active'

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
        self.criticalDeviation = np.random.uniform(self.outputRange['low'], self.outputRange['high']) 
   
    def activate(self):
        self.active = True

    def disactivate(self):
        self.active = False

    def maxConnectedUnits(self, anInteger):
        "Changes the parameter to the Uniselector for the maximum number of connected units"
        
        self._uniselector.unitsControlled(anInteger)

    def toggleDebugMode(self):
        "Controls whether the running methods print out debug information"

        if self.debugMode is True: 
            self._debugMode = False
        else: 
            self.debugMode = True

    def toggleShowUniselectorAction(self):
        "Control whether the running methods print out information when the uniselector kicks into action"

        if self._showUniselectorAction is True:
            self.showUniselectorAction= False
        else:
            self._showUniselectorAction = True
            
    def isNeedleWithinLimits(self, aValue):
        '''Check whether the proposed value exceeds the unit's range (both + and -)'''

        return (aValue >= (- self.maxDeviation) and aValue <= self.maxDeviation)

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
            
        if self.isNeedleWithinLimits(aValue):
            return aValue
        else:
            return (self.maxDeviation * np.sign(aValue))

    def newRandomNeedlePosition(self):
        '''Compute a random value for the needle position within the accepted range'''

        return np.random.uniform(self.minDeviation, self.maxDeviation)
         

    def __del__(self):
        ''''Remove a HomeoUnit's name from the set of used names.
            Subclasses' instances must call this method explicitly 
            to remove  their names'''
        if self._name is not None:
            HomeoUnit.allNames.remove(self._name)
        
        
        
        
        