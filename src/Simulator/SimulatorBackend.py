'''
SimulatorBackend is a small utility package that provides a common interface 
to the various robotic simulation backends that the Homeo package can use.
Currently, V-REP, Webots, and the internal HOMEO simulator are supported.
Each backend subclasses the SimulatorBackend class and implements the necessary
methods.

The Homeo simulation classes can thus abstract from backends' specific functions
and operate uniformly.
 
Created on Apr 13, 2015

@author: stefano
'''

from abc import ABCMeta,abstractmethod,abstractproperty
from Helpers.ExceptionAndDebugClasses import hDebug, TCPConnectionError
from socket import error as SocketError
try:
    import vrep
except ImportError:
    vrep = None
from time import sleep
import os
from RobotSimulator import WebotsTCPClient
from  subprocess import check_output
from os import system
from os.path import split
from Helpers.General_Helper_Functions import asByteArray, distance
from RobotSimulator.Transducer import VREP_DiffMotor,VREP_LightSensor, HOMEO_DiffMotor,HOMEO_LightSensor, WebotsDiffMotorTCP,WebotsLightSensorTCP
from KheperaSimulator.KheperaSimulator import KheperaSimulation

class SimulatorBackendAbstract(object):
    '''
    Abstract class that defines the interface for the robotic simulation packages
    used by the HOMEO package
    '''
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def __init__(self):
        pass
    
#     def getKheperaHost(self):
#         "return the robotic supervisor host"
#         return self._host
#     
#     def setKheperaHost(self,value):
#         "set the robotic supervisor host"
#         
#     kheperaHost = abstractproperty(getKheperaHost, setKheperaHost)
       
    @abstractproperty
    def name(self):
        return self.name
              
    @abstractmethod
    def reset(self, lock):
        """Restore simulation to initial conditions.
           Simulations are run in a separate threads. 
           Always pass a lock to prevent access to the world 
           while it is being reset """
        pass

    @abstractmethod    
    def setRobotModel(self, modelName):
        "Set the name of the robot used in the robotic simulations"
        pass

    @abstractmethod
    def resetPhysics(self):
        "Reset the physics parameters and forces in the simulator"
        pass

    @abstractmethod    
    def quit(self):
        "Quit the simulation"
        pass

    @abstractmethod    
    def close(self):
        "Close the current simulation run"
        pass

    @abstractmethod        
    def connect(self):
        "For the TCP/IP based robotic simulators, establish the connection"
        pass

    @abstractmethod
    def start(self, lock):
        """Start the simulator backend"
           Simulations are run in a separate threads. 
           Always pass a lock to prevent access to the world 
           while it is being reset"""
        pass

    @abstractmethod    
    def setDataDir(self):
        "Set the directory where simulation's data will be saved (trajectories, etc.) "
        pass

    @abstractmethod
    def finalDisFromTarget(self,target):
        "Return distance of robot from target at simulation's end"
        pass
      
    @abstractmethod
    def getWheel(self,wheel):
        "Return a reference to a robot's wheel, which can be used to control its speed"
        pass
    
    @abstractmethod
    def getSensor(self,sensorName):
        "Return a reference to a robot's sensor, which can be used to read its value"
        pass

class SimulatorBackendHOMEO(SimulatorBackendAbstract):
    "Interface to the internal HOMEO Khepera-like robotic simulator" 

    def __init__(self, lock = None, robotName='', dataDir = None):
        self._robotName = robotName
        self.lock = lock
        self.kheperaSimulation = KheperaSimulation()    
        self.host = None
        self.port = None

    @property
    def name(self):
        return "HOMEO"
            
    def setRobotModel(self, modelName):            
        """Tell the internal simulator to save the current trajectory (by sending the 
           appropriate signal, set the new name of the robot's model, 
           and start recording trajectory to a new, appropriately named file.  
         """
        self.kheperaSimulation.saveTrajectory()
        self.kheperaSimulation.setRobotModelName(self._robotName, modelName)
        self.kheperaSimulation.newTrajectoryFile()
                 
    def reset(self):
        """The internal simulator's resetWorld resets a simulation
           to initial conditions.
           Use the instance's lock to prevent access to the world before it is properly set up"""
        try:
            self.lock.acquire()
            self.kheperaSimulation.resetWorld()
        finally:
            self.lock.release()
        
    def resetPhysics(self):
        "Do nothing: no comparable function is needed in HOMEO"
        pass
                   
    def finalDisFromTarget(self):
        """Compute the distance from target by asking the internal
           simulator to return the distance between an object called
           'TARGET' and the KHEPERA robot (whose name is stored in an iVar)"""
       
        obj1Name = self._robotName
        obj2Name = 'TARGET'
        try:
            return self.kheperaSimulation.getDistance(obj1Name, obj2Name)
        except:
            raise Exception("Cannot get distance between %s and %s" % (obj1Name, obj2Name))
        
    def close(self):
        "Do nothing: we do not need to disconnect from the internal simulation environment"
        pass 
        
    def connect(self):
        "Do nothing: we do not need to connect to the internal simulation environment"
        pass
                
    def setDataDir(self,dataDir):
        "Set the directory for data recording"
        
        self.kheperaSimulation.setDataDir(dataDir)
        
    def start(self, world):
        """Internal simulator is started by creating the experimental setup.
           Use the instance's lock to prevent access to the world before it is properly set up"""
        
        with self.lock:
            self.kheperaSimulation.setupWorld(world)
    
    def quit(self):
        """Trash the existing simulation instance """     
        self.kheperaSimulation = None

    def getWheel(self,wheel):
        """Return a transducer to a HOMEO's khepera-like robot's wheel.
           Wheel is a string: 'left' or 'right'"""
        
        return HOMEO_DiffMotor(wheel, self._robotName ,self.kheperaSimulation)

    def getSensor(self,eye):
        """Return a transducer to a HOMEO's khepera-like robot's 'eye'.
           Eye is a string: 'left' or 'right'"""
        
        return HOMEO_LightSensor(eye, self.kheperaSimulation.allBodies[self._robotName])
    


       
class SimulatorBackendWEBOTS(SimulatorBackendAbstract):
    "Interface to the Webots robotic simulator backend"
    
    def __init__(self,supervisorHost, supervisorPort, kheperaHost, kheperaPort, robotName = ''):
        
        self.supervisorHost =  supervisorHost
        self.supervisorPort = supervisorPort
        self.kheperaHost = kheperaHost
        self._kheperaPort = kheperaPort
        self._supervisor = WebotsTCPClient(self.supervisorHost, self.supervisorPort)
        self._robotName = robotName
        
    @property
    def name(self):
        return "WEBOTS"
            
    def reset(self):
        """Reset webots simulation.
           Do not return from function until the simulation has really exited 
           and the previous tcp/ip socket is no longer valid. """
           
        try:
            self._supervisor._clientSocket.send("R")
            response = self._supervisor._clientSocket.recv(100) 
            hDebug('network',("Reset Webots simulation: received back "+ response + " from server"))
            try:
                while True:
                    self._supervisor._clientSocket.send(".")
                    sleep(0.05)
            except SocketError:
                pass
        except SocketError:
            raise TCPConnectionError("Could not reset Webots simulation")
    
    def setRobotModel(self,modelName):
        """Set the name  of the robot's model,
           which is then used to name the trajectory file"""
           
        try:
            self._supervisor._clientSocket.send("M,"+modelName)
            response = self._supervisor._clientSocket.recv(100) 
            hDebug('network',("Reset robot's model to: " + modelName + ". Received back: " + response))
        except SocketError:
            raise TCPConnectionError("Could not set model name of Webots robot")
        
    def quit(self):
        "Quit Webots application"
        
        try:
            self._supervisor._clientSocket.send("Q")
            response = self._supervisor._clientSocket.recv(100) 
            hDebug('network', "Quit Webots: received back " + response + " from server")
        except SocketError:
            hDebug('network',  "Sorry, I lost the connection to Webots and could not could not quit")
        except AttributeError:
            hDebug('network', "I encountered a major error: lost the socket communicating to Webots")        

    def resetPhysics(self):
        "Reset Webots simulation physics"
        try:
            self._supervisor._clientSocket.send("P")
            response = self._supervisor._clientSocket.recv(100) 
            hDebug('network', ("Reset Webots simulation physics: received back %s from server" % response))
        except SocketError:
            raise TCPConnectionError("Could not reset Webots simulation's physics")
            
    def connect(self):
        self._supervisor.clientConnect()
    
    def close(self):
        self._supervisor.close()
        
    def setDataDir(self,dataDir):
        'save dataDir path to a file, so Webots trajectory supervisor can read it'
        'FIXME: Should really communicate it to webots simulation supervisor to pass it to trajectory supervisor '
        dataDirFile = open(os.path.join(os.getenv("HOME"),'.HomeoSimDataDir.txt'),'w+')
        dataDirFile.write(dataDir)
        dataDirFile.close()

    def finalDisFromTarget(self):
        """Compute the distance from target by asking the supervisor to
        evaluate the distance between a node with 'DEF' = 'TARGET'
        and the KHEPERA robot"""
        
        self._supervisor._clientSocket.send("D")
        response = float(self._supervisor._clientSocket.recv(100)) 
        return response
    
    def isRunning(self):
        'Check if Webots is running'
        webots_running = False
        if 'webots-bin' in check_output(['ps','ax']):
                webots_running = True
        return webots_running

    def start(self,world = None, mode = "realtime"):
        """
        Start a Webots instance with the given world and at the specified speed (mode).
        Mode can be one of realtime, run, or fast 
        """
        if not self.isRunning():
            hDebug('network',("Is webots-running: " + str(self.isRunning())))
            callString = "/usr/local/webots/webots " +"--mode="+ mode+ " " +world + " &"
            hDebug('network',callString)
            system(callString)
            'Wait for webots to start listening to commands (in seconds)'
            sleep(2)

    def basicBraiten2WEBOTSTransducers(self, WEBOTS_World, raw = False):
        """Define and return transducers for Braitenberg type 2 simulations, 
           with transducers set up for the WEBOTS robotic simulator"""   
    
        """ If the 'raw' variable is set to True, the sensory transducer reads webots raw values, 
            which are minimum for maximum stimulus and maximal for minimun stimulus.
            This is the **reverse** of the classical Braitenberg case: a high intensity in the world
            will translate into a low sensor value."""  
    
        "1. setup webots"
        webotsMode = "fast"              #for GA experiments, run simulation as fast as possible 
    
        '''Webots parameters for tcp/ip communication
           (Defined in webots world specified above)
        '''        
        self.start(world=WEBOTS_World, mode=webotsMode)
        
        'Setup robotic communication parameters in actuator and sensor'
        
        'motors'
        rightWheel = WebotsDiffMotorTCP('right')
        leftWheel = WebotsDiffMotorTCP('left')
        rightWheel.funcParameters = 10 #wheel speed in rad/s
        leftWheel.funcParameters = 10  #wheel speed in rad/s
      
        'sensors'
        if raw == False:
            leftEyeSensorTransd  = WebotsLightSensorTCP(0)
            rightEyeSensorTransd = WebotsLightSensorTCP(1)
        else:
            leftEyeSensorTransd  = WebotsLightSensorRawTCP(0)
            rightEyeSensorTransd = WebotsLightSensorRawTCP(1)
    
        leftEyeSensorTransd._clientPort = port
        rightEyeSensorTransd._clientPort = port
        
        transducers = {"rightWheelTransd": rightWheel, 
                       "leftWheelTransd":leftWheel, 
                       "rightEyeTransd":rightEyeSensorTransd, 
                       "leftEyeTransd":leftEyeSensorTransd}
        
        return transducers


    
class SimulatorBackendVREP(SimulatorBackendAbstract):
    "Interface to the V-REP robotic simulator backend"
    
    def __init__(self, host, kheperaPort, robotName = '', dataDir = None):
        self._host = host
        if kheperaPort == None:
            self._kheperaPort = 19997
        else:
            self._kheperaPort = kheperaPort
        self._robotName = robotName
        self._VREP_clientId = None
        self.VREPSimulation = None
        self.dataDir = dataDir
            
    @property
    def name(self):
        return "VREP"
    
    @property
    def port(self):
        return self._kheperaPort
    
    @property 
    def host(self):
        return self._host
    
    def reset(self):
        """In VREP we reset a simulation by stopping and restarting it"""
        eCode = vrep.simxStopSimulation(self._VREP_clientId, vrep.simx_opmode_oneshot_wait)  
        if eCode != 0:
            raise Exception("Could not stop VREP simulation")
        eCode = vrep.simxStartSimulation(self._VREP_clientId, vrep.simx_opmode_oneshot_wait)   
        if eCode != 0:
            raise Exception("Could not start VREP simulation")
        vrep.simxSynchronousTrigger(self._VREP_clientId)
    
    def setRobotModel(self, modelName):
        """Tell V-REP to save the current trajectory (by sending the 
           appropriate signal, set the new name of the robot's model, 
           and start recording trajectory to a new, appropriately named file.""" 
        self.sendSignalVREP("HOMEO_SIGNAL_"+self._robotName+"_TRAJECTORY_RECORDER","CLOSEFILE")
        self.sendSignalVREP("HOMEO_SIGNAL_"+self._robotName+"_MODELNAME", modelName)
        self.sendSignalVREP("HOMEO_SIGNAL_"+self._robotName+"_TRAJECTORY_RECORDER", "NEWFILE")
    
    def resetPhysics(self):
        "Do nothing: no comparable function in V-REP"
        pass
    
    def quit(self):
        "Quit connection to VREP tcp/ip server"
        self.quitServerVREP()

    def start(self,world = None):
        """
        Start a VREP instance with the given world
        """
        self.connectToVREP(world)
    
    def finalDisFromTarget(self):
        """Compute the distance from target by computing 
           the distance between a VREP object with name  = 'TARGET'
           and the KHEPERA robot (whose name is stored in an iVar)"""
        
        "Close trajectory file first"
        self.sendSignalVREP("HOMEO_SIGNAL_"+self._robotName+"_TRAJECTORY_RECORDER","CLOSEFILE")
        return self.getDistanceBetwObjects("TARGET",self._robotName)
    
    def close(self):
        "In VREP we close a simulation run by stopping it"
        eCode = vrep.simxStopSimulation(self._VREP_clientId, vrep.simx_opmode_oneshot_wait)
        if eCode != 0:
            raise Exception("Could not stop VREP simulation")
    
    def connect(self):
        """Try to connect to VREP and store the clientId in an ivar"""
        
        if self._VREP_clientId is not None:
            self.startSimulationVREP()
        else:
            self._VREP_clientId = self.connectToVREP(self.VREPSimulation)        
    
    def setDataDir(self,dataDir):
        "Set the directory for saving data (trajectories, etc."
        
        if self._VREP_clientId is None:
            """cannot send signal to V-REP unless I am connected.
             Store the dataDir value for later use"""
            self.dataDir = dataDir
        else:
            self.sendSignalVREP("HOMEO_SIGNAL_SIM_DATA_DIR", dataDir)

    def connectToVREP(self, VREP_World=None):
        "Connect to VREP and load the correct world if needed"
        "FIXME: SHOULD LAUNCH VREP IF NOT RUNNING"
        VREP_exec = 'vrep'
        if self.VREPSimulation == None:
            self.VREPSimulation = VREP_World
        
        '1. check that V-Rep is running and see whether we are already connected to it. Otherwise connect'
        if VREP_exec not in check_output(["ps","-f", "--no-headers",  "ww", "-C", "vrep"]):
            raise Exception(("V-REP is not running! Please start V-REP with scene: %s" % self.VREPSimulation))
        else:
            "Check if we are connected with the passed clientId already"
            if self._VREP_clientId is not None:
                print("ClientId = " ,self._VREP_clientId)
                connId = vrep.simxGetConnectionId(self._VREP_clientId)
                print("My connId is " , connId)
                if connId == -1:                                 # we are not: set client Id to none and re-connect
                    print("Disconnecting all existing connections to V-REP")
                    vrep.simxFinish(-1)
                    self._VREP_clientId = None            
            while self._VREP_clientId is None:
                self._VREP_clientId = vrep.simxStart(self._host, self._kheperaPort,True,True, 5000,5)
                if not self._VREP_clientId == -1:
                    eCode = vrep.simxSynchronous(self._VREP_clientId, True)
                    if eCode != 0:
                        raise Exception("Failed to connect to VREP simulation. Bailing out")
    #     print " we are connected with clientId ", self._VREP_clientId
        "2. Check the correct world is running"
        if self.VREPSimulation is not None: 
            VREP_Scene = split(self.VREPSimulation)[1]
            if VREP_Scene not in check_output(["ps","-f", "--no-headers",  "ww", "-C", "vrep"]):
                eCode = vrep.simxLoadScene(self._VREP_clientId, self.VREPSimulation, 0, vrep.simx_opmode_oneshot_wait)
                if eCode != 0:
                    raise Exception(("Could not load into V-REP the world",  self.VREPSimulation))     
    
    
        "3. Make sure VREP has bees set to the correct directory for saving data"
        self.setDataDir(self.dataDir)
                
        '4. Start simulation'
        eCode = vrep.simxStartSimulation(self._VREP_clientId, vrep.simx_opmode_oneshot_wait)
        if eCode != 0:
            raise Exception("VREP simulation cannot get started")
        else:
            print("V-REP simulation is running with clientId: ", self._VREP_clientId)
            return self._VREP_clientId 
    
    def sendSignalVREP(self,signalName, signalValue):
        if type(signalValue) == str:
            eCode = vrep.simxSetStringSignal(self._VREP_clientId, signalName, asByteArray(signalValue), vrep.simx_opmode_oneshot_wait)
        elif type(signalValue) == int:
            eCode = vrep.simxSetIntegerSignal(self._VREP_clientId, signalName, signalValue, vrep.simx_opmode_oneshot_wait)
        elif type(signalValue) == float:
            eCode = vrep.simxSetFloatSignal(self._VREP_clientId, signalName, signalValue, vrep.simx_opmode_oneshot_wait)
        else:
            raise Exception("Trying to send a signal of unknown data type. Only strings, floats and and ints are accepted")
        if eCode != 0:
            raise Exception("Could not send string signal", signalValue)
        vrep.simxSynchronousTrigger(self._VREP_clientId)
    #     print "Set signal %s of type %s to: " % (signalName, type( signalValue)), signalValue
        
    def startSimulationVREP(self):
        eCode = vrep.simxStartSimulation(self._VREP_clientId, vrep.simx_opmode_oneshot_wait)
        if eCode !=0:
            raise Exception("Could not start VREP simulation")
        
    def getDistanceBetwObjects(self, objectNameA, objectNameB):
        """Get the distance between two named objects in V-REP.
           Raise exception if either does not exist"""
           
        eCode, handleA = vrep.simxGetObjectHandle(self._VREP_clientId, objectNameA, vrep.simx_opmode_oneshot_wait)
        if eCode != 0:
            raise Exception("Could not get handle of object", objectNameA)
        eCode, poseA =  vrep.simxGetObjectPosition(self._VREP_clientId, handleA, -1, vrep.simx_opmode_oneshot_wait)
        eCode, handleB = vrep.simxGetObjectHandle(self._VREP_clientId, objectNameB, vrep.simx_opmode_oneshot_wait)
        if eCode != 0:
            raise Exception("Could not get handle of object", objectNameB)
        eCode, poseB =  vrep.simxGetObjectPosition(self._VREP_clientId, handleB, -1, vrep.simx_opmode_oneshot_wait)
        return distance(poseA,poseB)
    
    def quitServerVREP(self):
        "Try to quite the connection to the VREP server"
        vrep.simxStopSimulation(self._VREP_clientId, vrep.simx_opmode_oneshot_wait)
        vrep.simxFinish(self._VREP_clientId)
        vrep.simxFinish(-1)
        
    def getWheel(self,wheel):
        """Return a transducer to a VREP's khepera-like robot's wheel.
           Wheel is a string: 'left' or 'right'"""
        
        return VREP_DiffMotor(wheel, self._VREP_clientId)

    def getSensor(self,eye):
        """Return a transducer to a VREP's khepera-like robot's 'eye'.
           Eye is a string: 'left' or 'right'"""
        
        return VREP_LightSensor(eye, self._VREP_clientId)



   
