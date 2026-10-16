'''
SimulatorBackend is a small utility package that provides a common interface 
to the various robotic simulation backends that the Homeo package can use.
Currently the internal HOMEO simulator (Box2D) is supported; the V-REP
backend and the old Webots TCP bridge were deleted on 14 Oct 2026.
Each backend subclasses the SimulatorBackend class and implements the necessary
methods.

The Homeo simulation classes can thus abstract from backends' specific functions
and operate uniformly.
 
Created on Apr 13, 2015

@author: stefano
'''

from abc import ABCMeta, abstractmethod
from Helpers.ExceptionAndDebugClasses import hDebug
from Helpers.General_Helper_Functions import distance

# Optional backend dependencies: guarded so that the module loads without Box2D
try:
    from RobotSimulator.Transducer import (HOMEO_DiffMotor, HOMEO_LightSensor,
                                           HOMEO_QualitySensor)
except ImportError:
    HOMEO_DiffMotor = HOMEO_LightSensor = HOMEO_QualitySensor = None

try:
    from KheperaSimulator.KheperaSimulator import KheperaSimulation
except ImportError:
    KheperaSimulation = None


class SimulatorBackendAbstract(object, metaclass=ABCMeta):
    '''
    Abstract class that defines the interface for the robotic simulation packages
    used by the HOMEO package
    '''

    @abstractmethod
    def __init__(self):
        pass

    @property
    @abstractmethod
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

    def __init__(self, lock = None, robotName='', dataDir = None, robotModel = 'epuck2'):
        '''robotModel: 'epuck2' (default) or 'kjunior'; see KheperaRobot.'''
        self._robotName = robotName
        self.lock = lock
        if KheperaSimulation is None:
            raise ImportError("KheperaSimulator requires Box2D. Install with: pip install box2d-py")
        self.kheperaSimulation = KheperaSimulation(robotModel=robotModel)
        if dataDir is not None:
            self.kheperaSimulation.setDataDir(dataDir)
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
        if self.lock is not None:
            self.lock.acquire()
        try:
            self.kheperaSimulation.resetWorld()
        finally:
            if self.lock is not None:
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

        if self.lock is not None:
            with self.lock:
                self.kheperaSimulation.setupWorld(world)
        else:
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

        return HOMEO_LightSensor(eye, self._robotName, self.kheperaSimulation)

    def getQualitySensor(self, sensorName, quality):
        """Return a quality-filtered sensor transducer.
           sensorName: fixture name (e.g. 'leftTempEye')
           quality: 'light', 'temperature', 'oxygen', 'organic'"""

        return HOMEO_QualitySensor(sensorName, quality, self._robotName,
                                   self.kheperaSimulation)


class SimulatorBackendWEBOTS(SimulatorBackendHOMEO):
    '''Webots, run by Homeo as its robot's extern controller (see
    WebotsSimulator.WebotsSimulation).  Its kheperaSimulation is a
    WebotsSimulation, with KheperaSimulation's interface, so the HOMEO
    backend's transducers and the experiment setups work unchanged.

    The robot is the e-puck2; the worlds are the Webots twins of
    KheperaSimulation's (WebotsSimulator.WebotsSimulation.WORLDS).  One
    process runs one Webots, shared by every backend made in it: a later
    start() resets the world.

    rendering: show Webots' window and render (figures), or not (batch).'''

    def __init__(self, lock = None, robotName='Khepera', dataDir = None, rendering = False,
                 robotModel = 'epuck2'):
        if robotModel != 'epuck2':
            raise ValueError("the Webots robot is the e-puck2 (robot 'epuck2')")
        from WebotsSimulator.WebotsSimulation import WebotsSimulation
        self._robotName = robotName
        self.lock = lock
        self.kheperaSimulation = WebotsSimulation.shared(rendering=rendering)
        if dataDir is not None:
            self.kheperaSimulation.setDataDir(dataDir)
        self.host = None
        self.port = None

    @property
    def name(self):
        return "WEBOTS"

    def finalDisFromTarget(self):
        return self.kheperaSimulation.finalDisFromTarget()

    def quit(self):
        "Keep the process's Webots for the next backend; WebotsSimulation.quit stops it"
        pass
