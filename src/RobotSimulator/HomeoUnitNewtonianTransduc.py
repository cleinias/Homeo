'''
Created on Sep 3, 2013

@author: stefano
'''
from Core.HomeoUnitNewtonian import HomeoUnitNewtonian
from Core.HomeoUnit import HomeoUnit,  HomeoUnitError
from Core.HomeoUnitAristotelian import HomeoUnitAristotelian
from numpy import sign
from numpy  import exp as np_exp
from Helpers.General_Helper_Functions import scaleTo
from math import exp
from Helpers.ExceptionAndDebugClasses import hDebug

    
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


    def __init__(self, transducer = None, filename = None,maxSpeed = None):
        '''
        Initialize according to superclass
        '''
        super(HomeoUnitNewtonianActuator, self).__init__()
        self._maxSpeed = maxSpeed
        'Initialize actuator, if passed'
        if transducer is not None:
            self._transducer = transducer
            #self.rightSpeed = 0
            #self.leftSpeed = 0
            self.maxDelta = 0
            try:
                self._maxSpeed = self._transducer.range()[1]* self._maxSpeedFraction
            except: 
                hDebug('unit network', "Transducer still unconnected to network or socket stale")
        
            
        '''Initialize default parameters for sigmoid function used to convert
           unit's deviation to motor commands'''
        self._maxSpeedFraction = 0.2   # The maximum speed of a motor as a fraction of the actuator speed
        self._switchingRate = .1      # The speed at which the function switches from positive to negative, or the slope of the logistic curve     
        
        'Open file for writing updated values, if needed'
        if filename is not None:
            self._fileOut = open(filename,'w')
            self._fileOut.write('currentDev,currentVel, torque,drag,acc,Mass,displ,newDev,noise,\n')
    
    def setTransducer(self, aTransducer):
        self._transducer = aTransducer
        
    def getTransducer(self):
        return self._transducer
    transducer = property(fget = lambda self: self.getTransducer(),
                          fset = lambda self, aValue: self.setActuator(aValue))
    
    def selfUpdate(self):
        '''First run the self-update function of superclass, 
            then convert unit-value to actuator value,
            then operate actuator on the unit value scaled 
            to the actuator range'''
        
        super(HomeoUnitNewtonianActuator, self).selfUpdate()
        
        #=======================================================================
        # 'write value to file, if needed'
        # if self._fileOut is not None:
        #     self._fileOut.write(str(self.criticalDeviation))
        #     self._fileOut.flush()
        #=======================================================================
            
        #=======================================================================
        # '''For testing'''
        # if self.actuator._wheel == 'right':
        #     self.rightSpeed = scaleTo([-self.maxDeviation,self.maxDeviation],self.transducer.range(),self.criticalDeviation)
        # else:
        #     self.leftSpeed = scaleTo([-self.maxDeviation,self.maxDeviation],self.transducer.range(),self.criticalDeviation)
        # delta = self.leftSpeed - self.rightSpeed 
        # if abs(delta) > self.maxDelta:
        #     self.maxDelta = abs(delta)
        # hDebug('unit', ("The unit value is %f and its scaled value is %f. The delta b/w wheels is %f and maxDelta is %f" % (self.criticalDeviation,
        #                                                            scaleTo([-self.maxDeviation,self.maxDeviation],self.transducer.range(),self.criticalDeviation),
        #                                                            delta,
        #                                                            self.maxDelta))
        # 'end testing'
        #=======================================================================

#        setSpeed = scaleTo([-self.maxDeviation,self.maxDeviation],self.transducer.range(),self.criticalDeviation)        
#        setSpeed = self.criticalDeviation
        ''' Use logistic function to normalize speed to [-1,1]'''        
        if self._maxSpeed is None:
            try:
                self._maxSpeed = self._transducer.range()[1]* self._maxSpeedFraction
            except:
                raise HomeoUnitError("Cannot get max speed from Transducer")
        hDebug('unit', ("critDev for unit: %s is %.3f" % (self.name, self.criticalDeviation)))                  
        setSpeed = float(-self._maxSpeed) + ((2 * self._maxSpeed)/ (1+np_exp(- self._switchingRate * self.criticalDeviation)))
        setSpeed = round(setSpeed,3)
        hDebug('unit', ("Speed set by %s is %f with critDev: %.3f " % (self.name, setSpeed, self.criticalDeviation)))
        self.transducer.funcParameters = setSpeed
        self.transducer.act()
    
class HomeoUnitAristotelianActuator(HomeoUnitAristotelian):
    '''
    HomeoUnitAristotelianActuator is a HomeoUnitAristotelian unit with 
    an added actuator. When it self updates, it also transmits
    its own critical deviation value to the actuator.
    The critical deviation value is scaled to the actuator range
    Notice that proper setup of the actuator is responsibility 
    of the calling class/instance.  
    
    Instance variable:
    transducer <aTransducer> an instance of an actuator subclass of Transducer 
    '''


    def __init__(self, transducer = None):
        '''
        Initialize according to superclass
        '''
        super(HomeoUnitAristotelianActuator, self).__init__()
        
        'Initialize actuator, if passed'
        if transducer is not None:
            self.transducer = transducer

    
    def setTransducer(self, aTransducer):
        self._transducer = aTransducer
    def getTransducer(self):
        return self._transducer
    actuator = property(fget = lambda self: self.getTransducer(),
                          fset = lambda self, aValue: self.setTransducer(aValue))
    
    def selfUpdate(self):
        '''First run the self-update function of superclass, 
            then convert unit-value to actuator value,
            then operate transducer on the unit value scaled 
            to the transducer range'''
        super(HomeoUnitAristotelianActuator, self).selfUpdate()
        self.transducer.funcParameters = scaleTo([-self.maxDeviation,self.maxDeviation],self.transducer.range(),self.criticalDeviation)
        self.transducer.act()
        
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
    transducer <aTransducer> an instance of a sensory subclass of Transducer
    alway_pos <Boolean>  whether the scaled transducer value is always positive or centered around zero  
    '''

    def __init__(self, transducer = None, always_pos=True):
        '''
        Initialize according to superclass
        '''
        super(HomeoUnitInput, self).__init__()
        'Initialize transducer and always_pos, if passed'
        if transducer is not None:
            self._transducer = transducer
        if always_pos == False:
             self.always_pos = False
        else: self.always_pos = True   
    
    def setTransducer(self, aTransducer):
        self._Transducer = aTransducer
    def getTransducer(self):
        return self._transducer
    transducer = property(fget = lambda self: self.getTransducer(),
                          fset = lambda self, aValue: self.setTransducer(aValue))
    
    def selfUpdate(self):
        '''
        Read the value from the external transducer (self.sensor) and scale it to the unit's deviation. 
        NOTICE that the sensor's value is always positive WHILE the scaled unit's deviation value 
        MAY BE positive if the ivar always_pos is set to true (default) OR  centered at 0 (zero), 
        (hence either positive or negative) if the ivar always_pos is set to False'''
        
        print " in selfUpdate of HomeoUnitInput. my transducer is of type", type(self.transducer)
        if self.always_pos == True:
            self.criticalDeviation = scaleTo(self.transducer.range(), [0, self.maxDeviation], self.transducer.read())
        else:
            self.criticalDeviation = scaleTo(self.transducer.range(), [-self.maxDeviation, self.maxDeviation], self.transducer.read())
        print "    about to compute output"
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

