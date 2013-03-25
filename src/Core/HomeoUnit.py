from  HomeoNeedleUnit import *
from  HomeoUniselector import *
from  HomeoConnection import *
import numpy as np

class HomeoUnit:
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
     switch                    <Integer>  As per Ashby's implementation, it represents the polarity of the connection of the unit to itself.  
                                          In our implementation it is always identical to the polarity of a unit's first connection,
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

    "The unit's output range is by default -1  to 1 to express the proportion of the needle's deviation" 
    unitRange = {'high':1,'low':-1}               

    "DefaultParameters is a class variable holding the  default values of all the various parameters of future created units."
    DefaultParameters  = dict(viscosity = 1,
                              maxDeviation=10,
                              outputRange = unitRange,
                              noise = 0,
                              potentiometer= 1,
                              time = 0,
                              inputValue=0,
                              uniselectorTime= 0,               # How often the uniselector checks the thresholds, in number of ticks
                              uniselectorTimeInterval = 10,
                              needleCompMethod= 'linear',       # switches between linear and proportional computation of displacement
                              uniselectorActivated = 0,
                              density = 1,                      # density of water
                              maxViscosity = (10^6))
    
    #TODO: Need to create a pool of unique names (a Set)
    
    
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
        self._needleCompMethod    = HomeoUnit.DefaultParameters['needleCompMethod']
        self._uniselectorActivated = HomeoUnit.DefaultParameters['uniselectorActivated']

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
        self.setUnitName()
        
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
        "Do nothing. Critical deviation cannot be set from the outside"
        pass
    criticalDeviation = property(fget = lambda self: self.getCriticalDeviation(),
                                 fset = lambda self, value: self.setCriticalDeviation(value))
    
    def setViscosity(self, aValue):
        self._viscosity = aValue
    def getViscosity(self):
        return self._viscosity
    viscosity = property(fget = lambda self: self.getViscosity(),
                         fset = lambda self, value: self.setViscosity(value))
      
    def setPotentiometer(self, aValue):
        self._potentiometer = aValue
    def getPotentiometer(self):
        return self._potentiometer
    potentiometer = property(fget = lambda self: self.getPotentiometer(),
                             fset = lambda self, value: self.setPotentiometer(value))  
    
    def setNoise(self, aValue):
        self._noise = aValue
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
        
    def setMaxDeviation(self,aValue):
        self._maxDeviation = aValue
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

    "end of setter and getter methods"

    def unitActive(self, aBoolean):
        self._status= True

    def setDefaultSelfConnection(self):
        pass
    def setNewName(self):
        pass
    def setDefaultOutputAndConnections(self):
        pass
    def setDefaultUniselectorSettings(self):
        pass
    def setUnitName(self):
        pass
    def setDefaultOutputAndDeviation(self):
        pass
    def isConnectedTo(self,aHomeoUnit):
        pass
    def addConnection(self, aHomeoUnit, weight,polarity,state):
        "polarity is 1 or -1; state is 'active' or 'uniselector'"
        pass
    def addConnectionWithNoise(self,aHomeoUnit,weight,polarity,noise,state):
        "polarity is 1 or -1; state is 'active' or 'uniselector'; noise is a number < 1"
        pass
    def isReadyToGo(self):
        pass
    def saveTo(self,filename):
        pass
    def setRandomValues(self):
        "sets up the unit with random values"

        self._viscosity = np.random.uniform(0.8,1)
        self._noise = np.random.uniform(0, 0.1)
        self._potentiometer = np.random.uniform(0, 1)

        switchSign = np.sign(np.random.uniform(-1, 1)) #sets the polarity of the self-connection, avoid  0"
        if switchSign == 0:
            switchSign = 1
        self._switch = switchSign 

        "generates a random output  over the whole range"
        self._currentOutput =  np.random.uniform(0, 1)    
        "set the critical deviation to a random value over the whole range"                                                         
        self._criticalDeviation = np.random.uniform(self._outputRange['low'], self._outputRange['high']) 

    def removeConnectionFromUnit(self,aHomeoUnit):
        pass
    
#This is a class method that create a new HomeoUnit instance from filename    
#       def readFrom(self,filename):
#           pass
 
        
    
