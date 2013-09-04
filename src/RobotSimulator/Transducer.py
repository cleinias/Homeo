'''
Created on Sep 3, 2013
@author: stefano

The Transducer module contains the classes necessary to operate 
a robot's actuators (motors, etc). The basic class is fairly abstract 
and may be subclassed to operate concrete robotic simulation environments
(player/Stage, Webots, etc) 
'''

class Transducer(object):
    '''
    Transducer controls an actuator of a robot. 
    It has just three instance variables:

    robot          <aRef>        a ref to the robot whose actuator it operates
    actFunction    <aString>    the name of the robot's function to operate the actuator
    parameters     <aList>      a list of  parameters to be passed to the function

    The basic metod is runOnce, which activates the actuator by running 
    robot.function(parameters)
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

    def setActFunction(self, aValue):
        self._actFunction = aValue
    def getActFunction(self):
        return self._actFunction
    actFunction = property(fget = lambda self: self.getActFunction(),
                    fset = lambda self, value: self.setActFunction(value))
    
    def setFuncParameters(self, aValue):
        self._funcParameters = aValue
    def getFuncParameters(self):
        return self._funcParameters
    funcParameters = property(fget = lambda self: self.getFuncParameters(),
                    fset = lambda self, value: self.setFuncParameters(value))  
  

    #======================================================================
    #  Running methods
    #======================================================================
    
    def runOnce(self, parameters):
        '''activates the actuators with the passed parameters'''
        self._robot.__getattribute__(self.actFunction)(self.funcParameters)
        
class webotsDiffRightMotor(Transducer): 
    '''
     webotsDiffRightMotor is the interface to the right Wheel of a Webots
     Differential Wheel robot. It defines the actFunction name and redefines
     setFuncParameters to modify only the second value (corresponding to the right motor) 
     '''   
    
    def __init__(self):
        " intialize instance to Webots values"
        self._actFunction = "setSpeed"
        
        self._functParameters = (0,0)
        
    def setFunctParameters(self,aNumber):
        self._functParameters = (self._robot.getLeftSpeed(), aNumber)       
 
class webotsDiffLeftMotor(Transducer): 
    '''
     webotsDiffLeftMotor is the interface to the Left Wheel of a Webots
     Differential Wheel robot. It defines the actFunction name and redefines
     setFuncParameters to modify only the first value (corresponding to the right motor) 
     '''   
    
    def __init__(self):
        " intialize instance to Webots values"
        self._actFunction = "setSpeed"
        
        self._functParameters = (0,0)
        
    def setFunctParameters(self,aNumber):
        self._functParameters = (aNumber, self._robot.getRightSpeed())       

    