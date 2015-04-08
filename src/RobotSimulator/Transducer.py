'''
Created on Sep 3, 2013
@author: stefano

The Transducer module contains the classes necessary to operate 
a robot's actuators (motors, etc). The basic class is fairly abstract 
and may be subclassed to operate concrete robotic simulation environments
(player/Stage, Webots, V-REP, etc.) 
'''
from socket import error as SocketError
from Helpers.General_Helper_Functions import SubclassResponsibility
from Helpers.ExceptionAndDebugClasses import hDebug
import random
import vrep
from string import uppercase
from sys import stderr

class TransducerException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Transducer(object):
    '''
    Transducer is an abstract class. It subclasses control a robot's input /output interfaces. 
    It has just three instance variables:

    robot          <aRef>       a ref to the robot whose actuator it operates
    transdFunction <aString>    the name of the robot's function to operate the actuator
    parameters     <aList>      a list of  parameters to be passed to the function

    The basic methods (all defined in subclasses) are 
    
    act  ---  which activates the actuator by running robot.transdFunction(parameters)
    sense --- which read the sensor by running robot.transdFunction(parameters) and returning a value
    range --- which returns a 2 value list containing the minimum and maximum values of the transducer 
    
    '''


    def __init__(self):
        '''
        Basic setup
        '''
    #=========================================several========================
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
    #=========================================several=============================
    
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
        "Initialize instance to Webots values and sets the right or left wheel accordingly"
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
           FIXME Webots actually has no access to the light sensor maximum value (its minimum value is 0).
           Raise an exception for now'''
        raise TransducerException("Webots does not give access to a sensor's max value")
    

class VREP_DiffMotor(Transducer):
    """ Connects a unit to a the motor of a Khepera-like differential drive
        robot in the V-REP simulator"""
    
    def __init__(self, wheel, clientID):
        "Wheel could either 'right or 'left' and nothing else"

        if wheel not in ["right","left"]:
            raise TransducerException("Wheel must either be right or left")
        self._wheel = wheel
        self.robot = clientID
        self._transdFunction = vrep.simxSetJointTargetVelocity
        self._opMode = 'simx_opmode_oneshot_wait'
        try:
            eCode, self._transducID = vrep.simxGetObjectHandle(self.robot, (self._wheel+"Wheel"), getattr(vrep,self._opMode))
            vrep.simxSynchronousTrigger(self.robot)
        except Exception as e:
            print "Cannot connect to VREP!"
            print "Error: ",e  
        
        if eCode != 0:
            raise TransducerException("Cannot connect to VREP motor: " + self._wheel+"Wheel")
        self._range = self.getRange()
            
    def getRange(self):
        "get motor range"
        eCode, value = vrep.simxGetFloatSignal(self.robot, "HOMEO_SIGNAL_"+self._wheel+"Wheel"+"_MAX_SPEED",getattr(vrep,self._opMode))
        vrep.simxSynchronousTrigger(self.robot)
        if eCode != 0:
            raise TransducerException("Cannot get maxSpeed of VREP motor: " + self._wheel+"Wheel")
        return value
    
    def act(self):
        '''activates the wheel motor by calling the actuator function (transdFunction) with 
           VREP client (stored in self.robot) and the needed parameters (stored in funcParameters)'''
#         parametersString =  str(self.robot) + ", " + str(self._transducID) + ", " + str(self.funcParameters) + ", " + 'vrep.'+self._opMode
        eCode = self.transdFunction(self.robot, self._transducID, self.funcParameters, getattr(vrep, self._opMode))
        vrep.simxSynchronousTrigger(self.robot)
        if eCode != 0:
            stderr.write("Motor command to VREP motor:%sWheel failed " % self._wheel)
#             raise TransducerException("Motor command to VREP motor:%sWheel failed " % self._wheel)
    
    def read(self):
        "Motors cannot sense"
        raise TransducerException("VREP Motor %sWheel cannot sense" %self._wheel)
    
    def range(self):
        "Motor's max speed is obtained at initialization and cached for efficiency"
        '''Function returns a list containing the min and max speed of the motor.
           notice that the posits min speed as always = to minus maxspeed'''

        return (-self._range, self._range)

class VREP_LightSensor(Transducer):
    """ Connects a unit to a HomeoLight sensor of  a Khepera-like robot
        in the V-REP simulator"""
        
    def __init__(self, eye, clientID):
        "Current HOMEO Khepera models only have a 'right' and a 'left' eye and nothing else"

        if eye not in ["right","left"]:
            raise TransducerException("Eye must either be right or left")
        self._eye = eye
        self.robot = clientID
        self._transdFunction = vrep.simxGetFloatSignal
        self._opMode = 'simx_opmode_oneshot_wait'
        self._VREPSignalName = "HOMEO_SIGNAL_"+self._eye+"Eye"+"_LIGHT_READING"
        self._range = self.getRange()
        
    def getRange(self):
        "get sensor range"
        eCode, value = vrep.simxGetFloatSignal(self.robot, "HOMEO_SIGNAL_"+self._eye+"Eye"+"_MAX_LIGHT",getattr(vrep,self._opMode))
        vrep.simxSynchronousTrigger(self.robot)
        if eCode != 0:
            raise TransducerException("Cannot get maxLight of VREP sensor: " + self._eye+"Eye")
        return value

    def read(self):
#         sensingParameters = self.robot + ", " + self._VREPSignalName +  ", " + 'vrep.'+self._opMode
        eCode, value = self._transdFunction(self.robot, self._VREPSignalName , getattr(vrep, self._opMode))
        vrep.simxSynchronousTrigger(self.robot)
        if eCode != 0:
#             raise Exception("Cannot read value for sensor " + self._eye+"Eye")
            stderr.write("Cannot read value for sensor " + self._eye+"Eye")
            return 0
#         print "Sensor %s read value %.3f" %((self._eye+"Eye"),value)
        return value
        
    def range(self):
        "Sensor's range is obtained at initialization and cached for efficiency"
        '''Function returns a tuple with min and max range. We posits minRange = 0'''
        return (0,self._range)
    
    def act(self):
        "Eyes cannot act"
        raise TransducerException("VREP sensor %sEye cannot act" %self._eye)

class TransducerTCP(object):
    '''
    TransducerTCP is an abstract class. Its subclasses control a robot's input /output interfaces
    through a TCP connection to a server running on the robot. 
    It has just four instance variables:

    robotSocket    <aString>    the socket connected to the robot server
    transdFunction <aString>    the string corresponding to the transducer command. Acceptable strings are defined by the server protocol 
                                and detailed in class WebotsTCPClient
    funcParameters <aString>    a string containing a list of  parameters to be passed to the command
    transducRange  <aList>      the min and max range of the transducer. Cached here for efficiency reasons

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
    
    def setRobotSocket(self, aValue):
        self._robotSocket = aValue
    def getRobotSocket(self):
        return self._robotSocket
    robotSocket = property(fget = lambda self: self.getRobotSocket(),
                    fset = lambda self, value: self.setRobotSocket(value))  
    
    def setTransdFunction(self, aValue):
        self._transdFunction = aValue
    def getTransdFunction(self):
        return self._transdFunction
    transdFunction = property(fget = lambda self: self.getTransdFunction(),
                    fset = lambda self, value: self.setTransdFunction(value))
    
    def setFuncParameters(self, aValue):
        self._funcParameters = str(aValue)
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

class WebotsDiffMotorTCP(TransducerTCP): 
    '''
     WebotsDiffMotorTCP is the interface to the wheels of a Webots'
     Differential Wheel robot controlled by a server. 
     Its "_wheel" variable specifies which wheel (right or left)
     it controls. It defines the transdFunction name and redefines
     setFuncParameters to modify only one of the values (corresponding to the right or left motor) 
     '''   
    
    def __init__(self, wheel):
        " initialize instance to Webots values and sets the right or left wheel accordingly"
        if wheel not in ["right","left"]:
            raise TransducerException("Wheel must either be 'right' or 'left'")
        else:
            self._wheel = wheel
            if self._wheel == 'right':
                self._transdFunction = 'R'
            else:
                self._transdFunction = 'L'

        
        self._functParameters = "0"        #parameter specifying the wheel's speed in radiant per second
                    
    def act(self):
        '''activates the wheel motor by calling the actuator function with the passed parameters'''
        command = self.transdFunction + ',' + self.funcParameters
        #print "Executing command: %s for transducer %s" % (command, type(self).__name__)
        try:
            #print "Motor transducer %s is connected to socket %s" % (type(self).__name__, type(self._robotSocket).__name__)
            hDebug('network',("sending motor command: " + command))
            print
            self._robotSocket.send(command)
            "Discard reply from receive buffer"
            discard = self._robotSocket.recv(1024)
            #===================================================================
            # if len(discard) == 0:
            #     print "CONNECTION INTERRUPTED! I received 0 bytes back"
            # else:
            #     print "I received %u bytes back, the message was: %s" % (len(discard), discard)
            #===================================================================
        except SocketError as e:
            print "FAILED! cannot connect to socket with command %s for actuator %s:  %s" % ( command, type(self).__name__, e)
                
    def range(self):
        '''return a list containing the min and max speed of the motor.
           notice that the min speed is always = to minus maxspeed in webots
           and the both wheels have identical maxspeed'''
        
        try:
            return self._transducRange
        except AttributeError:
            try:
                self.robotSocket.send('M')
                commandReturn = self._robotSocket.recv(1024).rstrip('\r\n').split(',')
                #print commandReturn
                self._transducRange = [-float(commandReturn[1]), float(commandReturn[1])]
                return self._transducRange
            except SocketError as e:
                print "FAILED! cannot connect to socket %s for actuator %s:  %s" % (type(self.robotSocket).__name__, type(self).__name__, e)

class WebotsDiffMotorTCPWithWrite(WebotsDiffMotorTCP):
    ''' Add the capability to write to file the value of the output command
        issued to the Webots differential wheel robot.
        Only overwrites the act method
    '''
    
    def __init__(self, wheel, filename = None):
        super(WebotsDiffMotorTCPWithWrite, self).__init__(wheel)
        if not filename is None:
            try:
                self._fileoutFile = open(filename,'w')
            except IOError:
                print "Could not open file in DUMMY transducer"
    
    def act(self):
        '''activate the wheel motor by calling the actuator function with the passed parameters
           and write the value of the motor command to file'''
        command = self.transdFunction + ',' + self.funcParameters
        #print "Executing command: %s for transducer %s" % (command, type(self).__name__)
        try:
            #print "Motor transducer %s is connected to socket %s" % (type(self).__name__, type(self._robotSocket).__name__)
            hDebug('network',("sending motor command: " + command))
            print
            self._robotSocket.send(command)
            "Discard reply from receive buffer"
            discard = self._robotSocket.recv(1024)
            self._fileoutFile.write(command.split(',')[1]+"\n")
            self._fileoutFile.flush()
            #===================================================================
            # if len(discard) == 0:
            #     print "CONNECTION INTERRUPTED! I received 0 bytes back"
            # else:
            #     print "I received %u bytes back, the message was: %s" % (len(discard), discard)
            #===================================================================
        except SocketError as e:
            print "FAILED! cannot connect to socket with command %s for actuator %s:  %s" % ( command, type(self).__name__, e)
                
        
class WebotsLightSensorTCP(TransducerTCP):
    '''Interface to a Webots' robot light sensor. 
       Converts the raw value read from the sensor to its complement, 
       since webots uses a light sensor's maximum value for the 
       minimum stimulus and 0 for the maximum possible stimulus'''
    
    def __init__(self, aNumber, filename = None, debug=False):
        '''Initialize the sensor with the Webots function name and the number of the sensor.
           Notice that it is the caller class responsibility to make sure that there is actually 
           such a sensor in the robot and that the robot tcp server controller returns an appropriate string'''
        self._transdFunction = "O"
        self._funcParameters = aNumber
        if not filename is None:
            try:
                self._fileOut = open(filename,'w')
            except IOError:
                print "Could not open file in DUMMY transducer"
        self._debug = debug 
        
        
    def read(self):
        '''Return the light value by reading the nth element of 
           the list of values returned by the read command.
           Convert the value to its complement to Max Value, because Webots
           use Max for the minimum stimulus and 0 for the max stimulus'''
        #print "Unit %s sending command: %s" %(type(self).__name__,self._transdFunction)
        #try:
        i = 0
        while i<20:
            hDebug('network',("inside try clause of read function: sending command" + self._transdFunction))
            self._robotSocket.send(self._transdFunction)
            #print "   after send command has been sent in read function"
            receivedData = self._robotSocket.recv(1024)
            #print "      Received: %s on try no.: %u" % (receivedData, i)
            #===================================================================
            # if i > 0:
            #     print "      HAD TO RESEND A READ COMMAND: ", i
            #===================================================================
            i  += 1
            if receivedData[0] == 'o':
                break
    #except:
        #print "Comm error with robot light transducer"
        
        #light_values = self._robotSocket.recv(1024).rstrip('\r\n').split(',')[1:]
        light_values = receivedData.rstrip('\r\n').split(',')[1:]
        if self._debug == True:
            self._fileOut.write(str( self.range()[1] - float(light_values[self._funcParameters]))+"\n")
            self._fileOut.flush()

        return self.range()[1] - float(light_values[self._funcParameters])
        #except SocketError as e:
            #print "FAILED! cannot connect to socket with actuator %s: %s" % (type(self).__name__, e)
       
    def range(self):
        '''Returns the range of the light sensor.
           FIXME Webots actually has no access to the light sensor maximum value (its minimum value is 0).
           return 1000'''
#        raise TransducerException("Webots does not give access to a sensor's max value")
        return [0,1000]   
        
class WebotsLightSensorRawTCP(WebotsLightSensorTCP):
    '''Interface to a Webots' robot light sensor. 
       DOES NOT convert the raw value read from the sensor to its complement, 
       and respects Webots's conventions: 0 is the maximum value
       and Max is the minimum.
       The class overrides only the read function of its superclass'''
    
    def __init__(self, aNumber, filename = None):
        '''Initialize according to superclass'''
        super(WebotsLightSensorRawTCP, self).__init__(aNumber)
        if not filename is None:
            try:
                self._fileOut = open(filename,'w')
            except IOError:
                print "Could not open file in DUMMY transducer" 


        
    def read(self):
        '''returns the light value by reading the nth element of 
           the list of values returned by the read command.
           '''
        self._robotSocket.send(self._transdFunction)
        light_values = self._robotSocket.recv(1024).rstrip('\r\n').split(',')[1:]  
        return float(light_values[self._funcParameters])
       
class WebotsLightSensorDUMMY(WebotsLightSensorTCP):
    '''DUMMY Interface to a Webots' robot light sensor,
       for testing purposes.
       Return a random, repeatable sequence of random numbers,
       based on the random seed stored in the instance variable SensorSeed.
       Record all input values to file for later analysis.
        
       The class overrides only the read function of its superclass'''
    
    
    def __init__(self, aNumber, aSeed, filename=None):
        '''Initialize according to superclass.
           Store the seed for random gen initialization and future reseeds'''
        super(WebotsLightSensorDUMMY, self).__init__(aNumber)
        self._randomGen = random.Random()
        self._seed = aSeed
        self._randomGen.seed(self._seed)
        if not filename is None:
            try:
                self._fileOut = open(filename,'w')
            except IOError:
                print "Could not open file in DUMMY transducer" 
        
    def read(self):
        '''return a fake, random light value in the allowed range.
           '''
        readInput =  self._randomGen.random() * self.range()[1]
        self._fileOut.write(str(readInput)+"\n")
        self._fileOut.flush()
        return readInput
        
    def reSeed(self):
        self._randomGen.seed(self._seed)  
       
   