'''
Created on Sep 3, 2013
@author: stefano

The Transducer module contains the classes necessary to operate 
a robot's actuators (motors, etc). The basic class is fairly abstract 
and may be subclassed to operate concrete robotic simulation environments
(player/Stage, Webots, etc) 
'''

from Helpers.General_Helper_Functions import SubclassResponsibility

class TransducerException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Transducer(object):
    '''
    Transducer is an abstract class. It subclasses control a robot's input /output interfaces. 
    It has just three instance variables:

    robot          <aRef>        a ref to the robot whose actuator it operates
    transdFunction    <aString>    the name of the robot's function to operate the actuator
    parameters     <aList>      a list of  parameters to be passed to the function

    The basic methods (all defined in subclasses) are 
    
    act  ---  which activates the actuator by running robot.function(parameters)
    sense --- which read the sensor by running robot.function(parameters) and returning a value
    range --- which returns a 2 value list containing the minimum and maximum values of the transducer 
    
    '''


    def __init__(self):
        '''
        Basic setup
        '''
    #=================================================================
    # Class properties
    #=================================================================
    
    def setRobot(self, aValue):
        self._robot = aValue
    def getRobot(self):
        return self._robot
    robot = property(fget = lambda self: self.getRobot(),
                    fset = lambda self, value: self.setRobot(value))  

    def setTransdFunction(self, aValue):
        self._transdFunction = aValue
    def getTransdFunction(self):
        return self._transdFunction
    transdFunction = property(fget = lambda self: self.getTransdFunction(),
                    fset = lambda self, value: self.setTransdFunction(value))
    
    def setFuncParameters(self, aValue):
        self._funcParameters = aValue
    def getFuncParameters(self):
        return self._funcParameters
    funcParameters = property(fget = lambda self: self.getFuncParameters(),
                    fset = lambda self, value: self.setFuncParameters(value))  
  

    #======================================================================
    #  Running methods
    #======================================================================
    
    def act(self, parameters):
        '''act method is implemented only by Transducer's subclasses'''
        raise SubclassResponsibility()
    
    def read(self):
        '''read method is implemented only by Transducer's subclasses'''
        raise SubclassResponsibility()
        
    def range(self):
        '''range method is implemented only by Transducer's subclasses'''
        raise SubclassResponsibility()


class WebotsDiffMotor(Transducer): 
    '''
     webotsDiffMotor is the interface to the wheels of a Webots'
     Differential Wheel robot. Its "_wheel" variable specifies which wheel (right or left)
     it controls. It defines the transdFunction name and redefines
     setFuncParameters to modify only one of the values (corresponding to the right or left motor) 
     '''   
    
    def __init__(self, wheel):
        " initialize instance to Webots values and sets the right or left wheel accordingly"
        self._transdFunction = "setSpeed"
        if wheel not in ["right","left"]:
            raise TransducerException("Wheel must either be right or left")
        else:
            self._wheel = wheel
        
        self._functParameters = (0,0)
        
    def setFunctParameters(self,aNumber):
        if self._wheel == "right":
            self._functParameters = (self._robot.getLeftSpeed(), aNumber)
        else:
            self._functParameters = (aNumber, self._robot.getRightSpeed())
            
    def act(self):
        '''activates the wheel motor by calling the actuator function with the passed parameters'''
        self._robot.__getattribute__(self.transdFunction)(self.funcParameters)
        
    def range(self):
        '''return a list containing the min and max speed of the motor'''
        if self._wheel == "right":
            return [0, self._robot.getMaxSpeed[1]]
        else:
            return [0,self._robot.getMaxSpeed[0]]
        
class WebotsLightSensor(Transducer):
    '''Interface to a Webots' robot light sensor'''
    
    def __init__(self, sensor):
        '''Initialize the sensor with the Webots function name and the sensor's name'''
        self._transdFunction = "getValue"
        self._funcParameters = sensor
        
    def read(self):
        '''returns the light value''' 
        self._robot.__getattribute__(self.transdFunction)(self.funcParameters)
       
    def range(self):
        '''Returns the range of the light sensor.
           FIXME Webots actually has now access to the light sensor maximum value (its min is 0).
           Raise an exception for now'''
        raise TransducerException("Webots does not give access to a sensor's max value")
        
    