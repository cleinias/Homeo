'''
Created on Sep 3, 2013

@author: stefano
'''
from Core.HomeoUnitNewtonian import HomeoUnitNewtonian
from numpy import sign

class HomeoUnitNewtonianActuator(HomeoUnitNewtonian):
    '''
    HomeoUnitNewtonianActuator is a HomeoUnitNewtonian unit with 
    an added actuator. When it self updates, it also transmits
    its own critical deviation value to the actuator.
    The critical deviation value is scaled to the actuator range
    Notice that proper setup of the actuator is responsibility 
    of the calling class/instance
    
    Instance variable:
    actuator <anActuator> an instance of an actuator subclass of Transducer 
    '''


    def __init__(self):
        '''
        Initialize according to superclass
        '''
        super(HomeoUnitNewtonianActuator, self).__init__()
    
    def setActuator(self, anActuator):
        self._actuator = anActuator
    def getActuator(self):
        return self._actuator
    actuator = property(fget = lambda self: self.getActuator(),
                          fset = lambda self, aValue: self.setActuator(aValue))
    
    def selfUpdate(self):
        '''First run the self-update function of superclass, 
            then convert unit-value to actuator value,
            then operate actuator'''
        super(HomeoUnitNewtonianActuator, self).selfUpdate()
        self.actuator.act(self.scaleCritDevToActValue())
    
    def scaleCritDevToActValue(self):
        '''
        Convert the unit's critical deviation value to an equivalent number expressing
        the same ratio in the actuator's range            
        '''
        return  sign(self.criticalDeviation * 
                     (abs(self.criticalDeviation) / self.maxDeviation) *
                     self.actuator.range[1])
