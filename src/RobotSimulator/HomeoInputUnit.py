'''
Created on Aug 29, 2013

@author: stefano
'''

from  Core.HomeoUnit import *

class HomeoInputUnit(HomeoUnit):
    '''
    Class HomeoInputUnit is an interface to an external input device. Instead of computing its value from the other units, it
    reads it from a (simulated) robot's sensor. 
    It does so by reimplementing the selfUpdate method to call a readFunction of a robot on a particular sensor instance.
    
    Instance variables:
    
    robot: a reference to the robot whose sensor it needs to read
    readFunction: the  python method used to read data from the sensor
    sensorName: the name of the sensor to be passed to the read function
    sensorParams; other parameters to be passed to the sensor reading functions 
     
    '''


    def __init__(self,aSensor):
        '''
        Initalize the HomeoInputUnit instance with a sensor
        '''
        self._sensor = aSensor

    def getSensor(self):
        return self._sensor
    
    def setSensor(self, aSensor):
        self._sensor = aSensor
    
    sensor = property(fget = lambda self: self.getSensor(),
                      fset = lambda self, aValue: self.setSensor(aValue))
        
     
    def selfUpdate(self):
        '''
        Read the value from the input sensor, scale it to the current deviation range
        and update criticalDeviation'''
        
        self._criticalDeviation = self.scaleSensorValueToCritDev()
        
        
    def scaleSensorValueToCritDev(self):
        '''
        Scale the sensor reading to the unit's critical deviation value range            
        '''
        return  (self.sensor.read() / (self.sensor.range[1]- self.sensor.range[0])) * self.maxDeviation
