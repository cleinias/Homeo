'''
Created on Sep 3, 2013

@author: stefano
'''
from Core.HomeoUnitNewtonian import HomeoUnitNewtonian
from Core.HomeoUnit import HomeoUnit
from Core.HomeoUnitAristotelian import HomeoUnitAristotelian
from numpy import sign
from Helpers.General_Helper_Functions import scaleTo
from math import exp

class HomeoUnitNewtonianActuator(HomeoUnitNewtonian):
    '''
    HomeoUnitNewtonianActuator is a HomeoUnitNewtonian unit with 
    an added actuator. When it self updates, it also transmits
    its own critical deviation value to the actuator.
    The critical deviation value is scaled to the actuator range
    Notice that proper setup of the actuator is responsibility 
    of the calling class/instance.  
    
    Instance variable:
    actuator <anActuator> an instance of an actuator subclass of Transducer 
    '''


    def __init__(self, actuator = None):
        '''
        Initialize according to superclass
        '''
        super(HomeoUnitNewtonianActuator, self).__init__()
        
        'Initialize actuator, if passed'
        if actuator is not None:
            self._actuator = actuator
            self.rightSpeed = 0
            self.leftSpeed = 0
            self.maxDelta = 0
        
        '''Initialize default parameters for sigmoid function used to convert
           unit's deviation to motor commands'''
        self._maxSpeedFraction = 0.2  # The maximum speed of a motor as a fraction of the actuator speed
        self._switchingRate = .1       # The speed at which the function switches from positive to negative, or the slope of the curve     
        self._maxSpeed = self._actuator.range()[1]* self._maxSpeedFraction
    
    def setActuator(self, anActuator):
        self._actuator = anActuator
    def getActuator(self):
        return self._actuator
    actuator = property(fget = lambda self: self.getActuator(),
                          fset = lambda self, aValue: self.setActuator(aValue))
    
    def selfUpdate(self):
        '''First run the self-update function of superclass, 
            then convert unit-value to actuator value,
            then operate actuator on the unit value scaled 
            to the actuator range'''
        super(HomeoUnitNewtonianActuator, self).selfUpdate()
        #=======================================================================
        # '''For testing'''
        # if self.actuator._wheel == 'right':
        #     self.rightSpeed = scaleTo([-self.maxDeviation,self.maxDeviation],self.actuator.range(),self.criticalDeviation)
        # else:
        #     self.leftSpeed = scaleTo([-self.maxDeviation,self.maxDeviation],self.actuator.range(),self.criticalDeviation)
        # delta = self.leftSpeed - self.rightSpeed 
        # if abs(delta) > self.maxDelta:
        #     self.maxDelta = abs(delta)
        # print "The unit value is %f and its scaled value is %f. The delta b/w wheels is %f and maxDelta is %f" % (self.criticalDeviation,
        #                                                            scaleTo([-self.maxDeviation,self.maxDeviation],self.actuator.range(),self.criticalDeviation),
        #                                                            delta,
        #                                                            self.maxDelta)
        # 'end testing'
        #=======================================================================

#        setSpeed = scaleTo([-self.maxDeviation,self.maxDeviation],self.actuator.range(),self.criticalDeviation)        
#        setSpeed = self.criticalDeviation
        ''' Use logistic function to normalize speed to [-1,1]'''        
        setSpeed = float(-self._maxSpeed) + ((2 * self._maxSpeed)/ (1+exp(- self._switchingRate * self.criticalDeviation)))
        print "Speed of %s wheel is %f " % (self.actuator._wheel, setSpeed)
        self.actuator.funcParameters = setSpeed
        self.actuator.act()
    
class HomeoUnitAristotelianActuator(HomeoUnitAristotelian):
    '''
    HomeoUnitAristotelianActuator is a HomeoUnitAristotelian unit with 
    an added actuator. When it self updates, it also transmits
    its own critical deviation value to the actuator.
    The critical deviation value is scaled to the actuator range
    Notice that proper setup of the actuator is responsibility 
    of the calling class/instance.  
    
    Instance variable:
    actuator <anActuator> an instance of an actuator subclass of Transducer 
    '''


    def __init__(self, actuator = None):
        '''
        Initialize according to superclass
        '''
        super(HomeoUnitAristotelianActuator, self).__init__()
        
        'Initialize actuator, if passed'
        if actuator is not None:
            self._actuator = actuator

    
    def setActuator(self, anActuator):
        self._actuator = anActuator
    def getActuator(self):
        return self._actuator
    actuator = property(fget = lambda self: self.getActuator(),
                          fset = lambda self, aValue: self.setActuator(aValue))
    
    def selfUpdate(self):
        '''First run the self-update function of superclass, 
            then convert unit-value to actuator value,
            then operate actuator on the unit value scaled 
            to the actuator range'''
        super(HomeoUnitAristotelianActuator, self).selfUpdate()
        self.actuator.funcParameters = scaleTo([-self.maxDeviation,self.maxDeviation],self.actuator.range(),self.criticalDeviation)
        self.actuator.act()
        
class HomeoUnitInput(HomeoUnit):
    '''
    HomeoUnitInput is a HomeoUnit which
    reads its value from a sensory transducer. When it self updates, 
    it reads the value from the sensor and scales it to its own deviation 
    range.
    HomeoUnitInput is thus not a "proper" HomeoUnit but rather a "dummy" unit that merely
    reads input values from the environment and transmit them to the connected unit(s).
    It has no defended value, uniselector action, etc. 
    
    Notice that proper setup of the transducer is responsibility 
    of the calling class/instance
    
    Instance variable:
    sensor <aTransducer> an instance of a sensory subclass of Transducer
    alway_pos <Boolean>  whether the scaled transducer value is always positive or centered around zero  
    '''

    def __init__(self, sensor = None, always_pos=True):
        '''
        Initialize according to superclass
        '''
        super(HomeoUnitInput, self).__init__()
        'Initialize sensor and always_pos, if passed'
        if sensor is not None:
            self._sensor = sensor
        if always_pos == False:
             self.always_pos = False
        else: self.always_pos = True   
    
    def setSensor(self, aTransducer):
        self._sensor = aTransducer
    def getSensor(self):
        return self._sensor
    sensor = property(fget = lambda self: self.getSensor(),
                          fset = lambda self, aValue: self.setSensor(aValue))
    
    def selfUpdate(self):
        '''
        Read the value from the external transducer (self.sensor) and scale it to the unit's deviation. 
        NOTICE that the sensor's value is always positive WHILE the scaled unit's deviation value 
        MAY BE positive is the ivar always_pos is set to true (default) OR  centered at 0 (zero), 
        (hence either positive or negative) if the ivar always_pos is set to False'''
        
        if self.always_pos == True:
            self.criticalDeviation = scaleTo(self.sensor.range(), [0, self.maxDeviation], self.sensor.read())
        else:
            self.criticalDeviation = scaleTo(self.sensor.range(), [-self.maxDeviation, self.maxDeviation], self.sensor.read())
        self.computeOutput()
        if self.debugMode:
            print "%s has crit dev of: %f and output of: %f" % (self.name, self.criticalDeviation, self.currentOutput)

        #=======================================================================
        # "for debugging"
        # if self.always_pos == True:
        #     print_scaled_value = scaleTo(self.sensor.range(), [0, self.maxDeviation], self.sensor.read())
        # else:
        #     print_scaled_value = scaleTo(self.sensor.range(), [-self.maxDeviation, self.maxDeviation], self.sensor.read())
        # print "Sensor range min: %f  max: %f raw value read: %f scaled Value: %f self critDev: %f)" %(self.sensor.range()[0],
        #                                                                                              self.sensor.range()[1],
        #                                                                                              self.sensor.read(),
        #                                                                                              print_scaled_value,
        #                                                                                              self.criticalDeviation )    
        # 
        #=======================================================================

