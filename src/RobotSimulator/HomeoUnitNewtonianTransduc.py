'''
Created on Sep 3, 2013

@author: stefano
'''
from Core.HomeoUnitNewtonian import HomeoUnitNewtonian
from Core.HomeoUnit import HomeoUnit
from numpy import sign
from Helpers.General_Helper_Functions import scaleTo

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
    '''

    def __init__(self, sensor = None):
        '''
        Initialize according to superclass
        '''
        super(HomeoUnitInput, self).__init__()
        'Initialize sensor, if passed'
        if sensor is not None:
            self._sensor = sensor
    
    def setSensor(self, aTransducer):
        self._sensor = aTransducer
    def getSensor(self):
        return self._sensor
    sensor = property(fget = lambda self: self.getSensor(),
                          fset = lambda self, aValue: self.setSensor(aValue))
    
    def selfUpdate(self):
        self.criticalDeviation = scaleTo(self.sensor.range(), [-self.maxDeviation, self.maxDeviation], self.sensor.read())
        self.computeOutput()
        if self.debugMode:
            print "%s has crit dev of: %f and output of: %f" % (self.name, self.criticalDeviation, self.currentOutput)

        #=======================================================================
        # "for debugging"
        # print "Raw value read: %d scaled Value: %d self critDev: %d)" %(self.sensor.read(),
        #                                                                 scaleTo(self.sensor.range(), [-self.maxDeviation, self.maxDeviation], self.sensor.read()),
        #                                                                 self.criticalDeviation )    
        #=======================================================================
    
    
