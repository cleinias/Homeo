'''
Created on Sep 4, 2013

@author: stefano
'''

from Core.Homeostat import *
from Core.HomeoUnitNewtonian import *
from Core.HomeoConnection import * 
from RobotSimulator.HomeoUnitNewtonianTransduc import *
from RobotSimulator.WebotsTCPClient import *
from subprocess import check_output
from subprocess import call as subCall
from RobotSimulator.Transducer import  *
from os import system
from time import sleep 
from docutils.nodes import problematic
from Helpers.ExceptionAndDebugClasses import hDebug



'''
Module HomeoExperiments provides initializations data for various experiments to be conducted with the homeo package.
The module's methods return a properly configured homeostat to be used in the simulations.
The functions setting up robotics experiments also launch Webots and set up communication
parameters between Webots and Homeo. 
'''

def initialize10UnitHomeostat(params=None):
    "Returns a homeostat with 10 units. Used for testing UI"
    hom = Homeostat()
    for i in xrange(10):
        unit = HomeoUnitNewtonian()
        unit.setRandomValues()
        hom.addFullyConnectedUnit(unit)
    return hom
    
def initializeAshbySimulation(params=None):
    '''Returns a Homeostat with
       four fully connected units with random values to the simulator 
       (as per Ashby basic design)'''
    hom = Homeostat()
    for i in xrange(4):
        unit = HomeoUnitNewtonian()
        unit.setRandomValues()
        hom.addFullyConnectedUnit(unit)

    'Return the properly configured homeostat'
    return hom

def initializeAshbyNoNoiseSimulation(params=None):
    '''Returns a Homeostat with
       four fully connected units with random values to the simulator 
       (as per Ashby basic design)
       Set all noises values to 0 for testing purposes'''
    hom = Homeostat()
    for i in xrange(4):
        unit = HomeoUnitNewtonian()
        unit.setRandomValues()
        hom.addFullyConnectedUnit(unit)
    for unit in hom.homeoUnits:
        unit.noise = 0
        for conn in unit.inputConnections:
            conn.noise = 0

    'Return the properly configured homeostat'
    return hom



def initialize_Ashby_2nd_Experiment(params=None):
    """
       Return a standard homeostat with 3 active units connected in a circle, as per 
       Ashby's experiment in Design for a brain, pp. 106-107.
       In detail: connections are 1-->2-->3-->1
       connection 1--> 2 is uniselector controlled
       connection 2--> 3 is hand-controlled
       connection 3--> 1 is always negative
       
       We start with:
       1 (possibly representing Motor/Agent) with negative, fixed, self-connection
       2 (possibly representing Environment) with no self-connection
       3 (possibly representing Sensor/Agent) with negative, fixed self-connection           
       """
    hom = Homeostat()
    'Standard parameters'
    agent_visc = 0.9 * HomeoUnit.DefaultParameters['maxViscosity']
    env_visc = 0.9 * HomeoUnit.DefaultParameters['maxViscosity']
    agent_mass = 100
    env_mass = 100
    agent_self_noise = 0.05
    env_self_noise = 0.05
    agent_density = 1
    env_density = 1
    agent_uniselector_timing= 100
    
    agent_self_connection_active = 'active'
    agent_self_connection_uniselector = 'manual'
    agent_self_connection_switch = -1
    agent_self_connection_potentiomenter = 0.5
    agent_self_connection_noise = 0.05
            
    agent_incoming_conn_weight = 0.5
    agent_incoming_conn_noise = 0.05
    agent_incoming_connection_polarity = 1
    agent_incoming_connection_uniselector = 'uniselector' 
    
    env_incoming_connection_weight = 0.5
    env_incoming_connection_noise = 0.05
    env_incoming_connection_polarity = 1
    env_incoming_connection_uniselector = 'manual'
    
    'Setup a standard Homeostat if none exists. Then change the parameters'
     
    if len(hom.homeoUnits) == 0 :                 # check if the homeostat is set up already"
        for i in xrange(4):
            unit = HomeoUnitNewtonian()
            unit.setRandomValues()
            hom.addFullyConnectedUnit(unit)

    'disable all connections except self-connections'
    for unit in hom.homeoUnits:
        for i in xrange(1, len(hom.homeoUnits)):
            unit.inputConnections[i].status = False
            
    homeo1_unit1_minus = hom.homeoUnits[0]
    homeo1_unit2_minus = hom.homeoUnits[1]
    homeo1_unit3x = hom.homeoUnits[2]
    homeo1_inactive_unit = hom.homeoUnits[3]

    'First Agent or sensor'
    homeo1_unit1_minus.name = 'Agent_Motor'
    homeo1_unit1_minus.mass = agent_mass
    homeo1_unit1_minus.viscosity = agent_visc
    homeo1_unit1_minus.density = agent_density
    homeo1_unit1_minus.noise  = agent_self_noise
    homeo1_unit1_minus.uniselectorTimeInterval = agent_uniselector_timing
    
    'self-connection'
    homeo1_unit1_minus.potentiometer = agent_self_connection_potentiomenter
    homeo1_unit1_minus.switch = agent_self_connection_switch
    homeo1_unit1_minus.inputConnections[0].noise = agent_self_connection_noise
    homeo1_unit1_minus.inputConnections[0].state = agent_self_connection_uniselector
       
    'Second Agent or sensor'
    homeo1_unit2_minus.name = 'Agent_Sensor'
    homeo1_unit2_minus.mass = agent_mass
    homeo1_unit2_minus.viscosity = agent_visc
    homeo1_unit2_minus.density = agent_density
    homeo1_unit2_minus.noise  = agent_self_noise
    homeo1_unit2_minus.uniselectorTimeInterval = agent_uniselector_timing
    'disactivate uniselector'
    homeo1_unit2_minus.uniselectorActive = False
    
    'self-connection'
    homeo1_unit2_minus.potentiometer = agent_self_connection_potentiomenter
    homeo1_unit2_minus.switch = agent_self_connection_switch
    homeo1_unit2_minus.inputConnections[0].noise = agent_self_connection_noise
    homeo1_unit2_minus.inputConnections[0].state = agent_self_connection_uniselector

    'Environment '
    homeo1_unit3x.name = 'Env'
    homeo1_unit3x.mass - env_mass
    homeo1_unit3x.viscosity = env_visc
    homeo1_unit3x.density = env_density
    homeo1_unit3x.noise = env_self_noise
    'self-connection disabled'
    homeo1_unit3x.disactivateSelfConn()
    'disactivate uniselector'
    homeo1_unit3x.uniselectorActive = False
    
    'fourth unit is inactive'
    homeo1_inactive_unit.name= 'UNUSED'
    homeo1_inactive_unit.disactivate()

    "set up homeostat's connections"
    "homeo1_unit_1_minus receives input only from sensor, i.e. homeo1_unit_2_minus"
    "connection is always negative polarity"
    for connection in homeo1_unit1_minus.inputConnections:
        if not (connection.incomingUnit.name == 'UNUSED' or 
                connection.incomingUnit == connection.outgoingUnit or 
                connection.incomingUnit.name == 'Env'):
            incomingWeight = -0.5
            connection.newWeight(incomingWeight)
            connection.noise = agent_incoming_conn_noise
            connection.state = agent_incoming_connection_uniselector
            connection.status = True
    
    "homeo1_unit_2_minus receives input only from env"
    for connection in homeo1_unit2_minus.inputConnections:
        if not (connection.incomingUnit.name == 'UNUSED' or 
                connection.incomingUnit == connection.outgoingUnit or
                connection.incomingUnit.name == 'Agent_Motor'):
            connection.newWeight(agent_incoming_conn_weight * agent_incoming_connection_polarity)
            connection.noise = agent_incoming_conn_noise
            connection.state = agent_incoming_connection_uniselector
            connection.status = True
    
    "Homeo1_unit_3x receive input only from motor, i.e. homeo1_unit_1_minus"
    for connection in homeo1_unit3x.inputConnections:
        if not (connection.incomingUnit.name == 'UNUSED'  or 
                connection.incomingUnit == connection.outgoingUnit or
                connection.incomingUnit.name == 'Agent_Sensor'):
            connection.newWeight(env_incoming_connection_weight * env_incoming_connection_polarity)
            connection.noise = env_incoming_connection_noise
            connection.state = env_incoming_connection_uniselector
            connection.status = True
    
    'Return the properly configured homeostat'
    return hom
            
def initialize_1minus_2xExperiment(params=None):
    '''
    Initialize a standard Homeostat to have 2 2-units 1-, 2x standard settings for 1- 2x experiment (Agent-Environment)
    with fixed parameters to improve repeated runs
    '''
    hom = Homeostat()
    
    'Standard parameters'
    agent_visc = 0.9 * HomeoUnit.DefaultParameters['maxViscosity']
    env_visc = 0.9 * HomeoUnit.DefaultParameters['maxViscosity']
    agent_mass = 100
    env_mass = 100
    agent_self_noise = 0.05
    env_self_noise = 0.05
    agent_density = 1
    env_density = 1
    agent_uniselector_timing= 100
    
    agent_self_connection_active = 'active'
    agent_self_connection_uniselector = 'manual'
    agent_self_connection_switch = -1
    agent_self_connection_potentiomenter = 0.1
    agent_self_connection_noise = 0.05
            
    agent_incoming_conn_weight = 0.5
    agent_incoming_conn_noise = 0.05
    agent_incoming_connection_polarity = 1
    agent_incoming_connection_uniselector = 'uniselector' 
    
    env_incoming_connection_weight = 0.5
    env_incoming_connection_noise = 0.05
    env_incoming_connection_polarity = 1
    env_incoming_connection_uniselector = 'manual' 


    'Setup a standard Homeostat if none exists. Then change the parameters'
     
    if len(hom.homeoUnits) == 0 :                 # check if the homeostat is set up already"
        for i in xrange(4):
            unit = HomeoUnitNewtonian()
            unit.setRandomValues()
            hom.addFullyConnectedUnit(unit)
        
    'disable all connections except self-connections'
    for unit in hom.homeoUnits:
        for i in xrange(1, len(hom.homeoUnits)):
            unit.inputConnections[i].status = False
    
    homeo1_unit1_minus = hom.homeoUnits[0]
    homeo1_unit2x = hom.homeoUnits[1]
    homeo2_unit1_minus = hom.homeoUnits[2]
    homeo2_unit2x = hom.homeoUnits[3]
    
    'Agent for Homeostat 1'
    homeo1_unit1_minus.name = 'H1_Agent'
    homeo1_unit1_minus.mass = agent_mass
    homeo1_unit1_minus.viscosity = agent_visc
    homeo1_unit1_minus.density = agent_density
    homeo1_unit1_minus.noise  = agent_self_noise
    homeo1_unit1_minus.uniselectorTimeInterval = agent_uniselector_timing
    
    'self-connection'
    homeo1_unit1_minus.potentiometer = agent_self_connection_potentiomenter
    homeo1_unit1_minus.switch = agent_self_connection_switch
    homeo1_unit1_minus.inputConnections[0].noise = agent_self_connection_noise
    homeo1_unit1_minus.inputConnections[0].state = agent_self_connection_uniselector
    
    
    'Environment for Homeostat 1'
    homeo1_unit2x.name = 'H1_Env'
    homeo1_unit2x.mass - env_mass
    homeo1_unit2x.viscosity = env_visc
    homeo1_unit2x.density = env_density
    homeo1_unit2x.noise = env_self_noise
    'self-connection disabled'
    homeo1_unit2x.disactivateSelfConn()


    'set up first homeostat'
    for connection in homeo1_unit1_minus.inputConnections:
        if connection.incomingUnit.name == 'H1_Env':
            connection.newWeight(agent_incoming_conn_weight * agent_incoming_connection_polarity)
            connection.noise = agent_incoming_conn_noise
            connection.state = agent_incoming_connection_uniselector
            connection.status = True
    
    
    
    for connection in homeo1_unit2x.inputConnections:
        if connection.incomingUnit.name == 'H1_Agent':
            connection.newWeight(env_incoming_connection_weight * env_incoming_connection_polarity)
            connection.noise = env_incoming_connection_noise
            connection.state = env_incoming_connection_uniselector
            connection.status = True
    
   
    'Second Homeostat'
    
    'Agent for Homeostat 2'
    homeo2_unit1_minus.name = 'H2_Agent'
    homeo2_unit1_minus.mass = agent_mass
    homeo2_unit1_minus.viscosity = agent_visc
    homeo2_unit1_minus.density = agent_density
    homeo2_unit1_minus.noise  = agent_self_noise
    homeo2_unit1_minus.uniselectorTimeInterval = agent_uniselector_timing
    
    'self-connection'
    homeo2_unit1_minus.potentiometer = agent_self_connection_potentiomenter
    homeo2_unit1_minus.switch = agent_self_connection_switch
    homeo2_unit1_minus.inputConnections[0].noise = agent_self_connection_noise
    homeo2_unit1_minus.inputConnections[0].state = agent_self_connection_uniselector

    
    
    'Environment for Homeostat 2'
    homeo2_unit2x.name = 'H2_Env'
    homeo2_unit2x.mass - env_mass
    homeo2_unit2x.viscosity = env_visc
    homeo2_unit2x.density = env_density
    homeo2_unit2x.noise = env_self_noise
    'self-connection disabled'
    homeo2_unit2x.disactivateSelfConn()
    

    'set up second homeostat'
    for connection in homeo2_unit1_minus.inputConnections:
        if connection.incomingUnit.name == 'H2_Env':
            connection.newWeight(agent_incoming_conn_weight * agent_incoming_connection_polarity)
            connection.noise = agent_incoming_conn_noise
            connection.state = agent_incoming_connection_uniselector
            connection.status = True        
    
    for connection in homeo2_unit2x.inputConnections:
        if connection.incomingUnit.name == 'H2_Agent':
            connection.newWeight(env_incoming_connection_weight * agent_incoming_connection_polarity)
            connection.noise = env_incoming_connection_noise
            connection.state = env_incoming_connection_uniselector
            connection.status = True      
    
    'Return the properly configured homeostat'
    return hom        
            
            
def initialize_1minus_2_minus_3xExperiment(params=None):
    """Initialize a homeostat to replicate a 3-unit
       homeostat roughly similar to DiPaolo's ocular inversion
       experiment:
       2 self-connected units representing the 'eyes' or 'sensors'
       1 unconnected unit representing the environment 
    """
    hom = Homeostat()
    
    'Standard parameters'
    agent_visc = 0.9 * HomeoUnit.DefaultParameters['maxViscosity']
    env_visc = 0.9 * HomeoUnit.DefaultParameters['maxViscosity']
    agent_mass = 100
    env_mass = 100
    agent_self_noise = 0.05
    env_self_noise = 0.05
    agent_density = 1
    env_density = 1
    agent_uniselector_timing= 100
    
    agent_self_connection_active = 'active'
    agent_self_connection_uniselector = 'manual'
    agent_self_connection_switch = -1
    agent_self_connection_potentiomenter = 0.1
    agent_self_connection_noise = 0.05
            
    agent_incoming_conn_weight = 0.5
    agent_incoming_conn_noise = 0.05
    agent_incoming_connection_polarity = 1
    agent_incoming_connection_uniselector = 'uniselector' 
    
    env_incoming_connection_weight = 0.5
    env_incoming_connection_noise = 0.05
    env_incoming_connection_polarity = 1
    env_incoming_connection_uniselector = 'manual'
    
    'Setup a standard Homeostat if none exists. Then change the parameters'
     
    if len(hom.homeoUnits) == 0 :                 # check if the homeostat is set up already"
        for i in xrange(4):
            unit = HomeoUnitNewtonian()
            unit.setRandomValues()
            hom.addFullyConnectedUnit(unit)

    'disable all connections except self-connections'
    for unit in hom.homeoUnits:
        for i in xrange(1, len(hom.homeoUnits)):
            unit.inputConnections[i].status = False
    
    homeo1_unit1_minus = hom.homeoUnits[0]
    homeo1_unit2_minus = hom.homeoUnits[1]
    homeo1_unit3x = hom.homeoUnits[2]
    homeo1_inactive_unit = hom.homeoUnits[3]
    
    'First Agent or sensor'
    homeo1_unit1_minus.name = '1_Agent'
    homeo1_unit1_minus.mass = agent_mass
    homeo1_unit1_minus.viscosity = agent_visc
    homeo1_unit1_minus.density = agent_density
    homeo1_unit1_minus.noise  = agent_self_noise
    homeo1_unit1_minus.uniselectorTimeInterval = agent_uniselector_timing
    
    'self-connection'
    homeo1_unit1_minus.potentiometer = agent_self_connection_potentiomenter
    homeo1_unit1_minus.switch = agent_self_connection_switch
    homeo1_unit1_minus.inputConnections[0].noise = agent_self_connection_noise
    homeo1_unit1_minus.inputConnections[0].state = agent_self_connection_uniselector
    
    'Second Agent or sensor'
    homeo1_unit2_minus.name = '2_Agent'
    homeo1_unit2_minus.mass = agent_mass
    homeo1_unit2_minus.viscosity = agent_visc
    homeo1_unit2_minus.density = agent_density
    homeo1_unit2_minus.noise  = agent_self_noise
    homeo1_unit2_minus.uniselectorTimeInterval = agent_uniselector_timing
    
    'self-connection'
    homeo1_unit2_minus.potentiometer = agent_self_connection_potentiomenter
    homeo1_unit2_minus.switch = agent_self_connection_switch
    homeo1_unit2_minus.inputConnections[0].noise = agent_self_connection_noise
    homeo1_unit2_minus.inputConnections[0].state = agent_self_connection_uniselector
    
    
    'Environment '
    homeo1_unit3x.name = 'Env'
    homeo1_unit3x.mass - env_mass
    homeo1_unit3x.viscosity = env_visc
    homeo1_unit3x.density = env_density
    homeo1_unit3x.noise = env_self_noise
    'self-connection disabled'
    homeo1_unit3x.disactivateSelfConn()

    'fourth unit is inactive'
    homeo1_inactive_unit.name= 'UNUSED'
    homeo1_inactive_unit.disactivate()

    'set up homeostat'
    for connection in homeo1_unit1_minus.inputConnections:
        if not (connection.incomingUnit.name == 'UNUSED' or connection.incomingUnit == connection.outgoingUnit):
            connection.newWeight(agent_incoming_conn_weight * agent_incoming_connection_polarity)
            connection.noise = agent_incoming_conn_noise
            connection.state = agent_incoming_connection_uniselector
            connection.status = True
    
    for connection in homeo1_unit2_minus.inputConnections:
        if not (connection.incomingUnit.name == 'UNUSED'  or connection.incomingUnit == connection.outgoingUnit):
            connection.newWeight(agent_incoming_conn_weight * agent_incoming_connection_polarity)
            connection.noise = agent_incoming_conn_noise
            connection.state = agent_incoming_connection_uniselector
            connection.status = True
    
    
    for connection in homeo1_unit3x.inputConnections:
        if not (connection.incomingUnit.name == 'UNUSED'  or connection.incomingUnit == connection.outgoingUnit):
            connection.newWeight(env_incoming_connection_weight * env_incoming_connection_polarity)
            connection.noise = env_incoming_connection_noise
            connection.state = env_incoming_connection_uniselector
            connection.status = True

    'Return the properly configured homeostat'
    return hom        

def initializeBraiten1_1Arist(raw=True,params=None):
    '''
    Initialize a Homeostat to replicate a Braitenberg type-1 vehicle with
    1 real Aristotelian  unit for the motor, plus one HomeoUnitInput to connect to the outside world.
    Set up Webots accordingly and pass Webots parameters (port #) to the units

    The initialization variable 'raw' controls the type of sensory tranducer. 
    If it is set to 'False" the raw sensory input from webot is reversed: high sensory values correspond 
    to high actual stimuli, and viceversa.
    If the 'raw' variable is set to True (default), the sensory transducer reads webots raw values, 
    which are minimum for maximum stimulus and maximal for minimun stimulus                      
    ''' 
    if raw == None:
        raw = True
            

    
    "1. setup webots"
    "PUT THE CORRECT WEBOTS WORLD HERE WITH COMPLETE PATH"  
    webotsWorld = '/home/stefano/Documents/Projects/Homeostat/Simulator/Python-port/Homeo/src/Webots/Homeo-experiments/worlds/khepera-braitenberg-1-1-HOMEO.wbt'   
    '''Webots parameters for tcp/ip communication
       (Defined in webots world specified above) '''
    kheperaPort = 10020
    supervisorPort = 10021
    
    startWebots(webotsWorld)
    
    "2. set up connection and create client and socket, etc."
    client = WebotsTCPClient()
    client._clientPort = kheperaPort
    socket = client.getClientSocket()
    
       
    '3.1 Setup robotic communication parameters in actuator and sensor'
    'motor'
    wheel = WebotsDiffMotorTCP('right')
    wheel.robotSocket = socket
    wheel.funcParameters = 10
    
    'sensor'
    if raw == False:
        sensorTransd = WebotsLightSensorTCP(0)
    else:
        sensorTransd = WebotsLightSensorRawTCP(0)
    sensorTransd._clientPort = kheperaPort
    sensorTransd.robotSocket = socket
    
    '3.2 initialize motor and sensor units with properly setup motor and sensor '
    motor = HomeoUnitAristotelianActuator(actuator = wheel)
    sensor = HomeoUnitInput(sensor=sensorTransd)
    
    "4. Set up Homeostat"   
    hom = Homeostat()
    
    'Setup standard homeo parameters'
    motor_visc = 0.9 * HomeoUnit.DefaultParameters['maxViscosity']
    sensor_visc = 0.9 * HomeoUnit.DefaultParameters['maxViscosity']
    
    motor_mass = 100
    sensor_mass = 100
    
    motor_self_noise = 0.05
    sensor_self_noise = 0.05
    
    motor_density = 1
    sensor_density = 1
    
    motor_uniselector_timing= 100
    
    motor_self_connection_active = False  # Set to either True or False to (dis-)active uniselector 
    motor_self_connection_uniselector = 'manual'
    motor_self_connection_switch = -1
    motor_self_connection_potentiomenter = 0.1
    motor_self_connection_noise = 0.05
            
    motor_incoming_conn_weight = 0.5
    motor_incoming_conn_noise = 0.05
    motor_incoming_connection_polarity = 1
    motor_incoming_connection_uniselector = 'uniselector' 
    
    sensor_incoming_connection_weight = 0.5
    sensor_incoming_connection_noise = 0.05
    sensor_incoming_connection_polarity = 1
    sensor_incoming_connection_uniselector = 'manual'
    
    'Setup a 1 unit Homeostat with an additional input unit. Then change the parameters'
    if len(hom.homeoUnits) == 0 :                 # check if the homeostat is set up already"
            hom.addFullyConnectedUnit(motor)
            hom.addFullyConnectedUnit(sensor)

     
    'Disable all connections except self-connections'
    for unit in hom.homeoUnits:
        for i in xrange(1, len(hom.homeoUnits)):
            unit.inputConnections[i].status = False

    'Agent unit or motor'
    motor.name = 'Motor'
    motor.mass = motor_mass
    motor.viscosity = motor_visc
    motor.density = motor_density
    motor.noise = motor_self_noise
    motor.uniselectorActive = motor_self_connection_active
    motor.uniselectorTimeInterval = motor_uniselector_timing
    
    'self-connection'
    'disactivate self-connection'
    motor.inputConnections[0].status = False
    motor.potentiometer = motor_self_connection_potentiomenter
    motor.switch = motor_self_connection_switch
    motor.inputConnections[0].noise = motor_self_connection_noise
    motor.inputConnections[0].state = motor_self_connection_uniselector

    'Sensor unit'
    sensor.name = 'Sensor'
    sensor.mass = sensor_mass
    sensor.viscosity = sensor_visc
    sensor.density = sensor_density
    sensor.noise = sensor_self_noise

    'disactivate uniselector'
    sensor.uniselectorActive = False
    
    'disactivate self-connection'
    sensor.inputConnections[0].status = False

    "Set up homeostat's connection."
    'Motor is connected to (receives input from) sensor'
    for connection in motor.inputConnections:
        if connection.incomingUnit.name == 'Sensor':
            connection.newWeight(motor_incoming_conn_weight)
            connection.noise = motor_incoming_conn_noise
            connection.state = motor_incoming_connection_uniselector
            connection.status = True
    
    'Sensor is not connected to (does not receive input from) any other unit'
    for connection in sensor.inputConnections:
        connection.status = False
        
    hom._usesSocket = True
    'Return the properly configured homeostat'
    return hom

def initializeBraiten1_1Pos(params=None):
    '''Utility function to choose a  Braitenberg type-1 vehicle with
    1 real units and a positive connection between actual stimulus and sensory 
    input (the higher the world's value, the higher the stimulus'''
    return initializeBraiten1_1(False)

def initializeBraiten1_1Neg(params=None):
    '''Utility function to choose a  Braitenberg type-1 vehicle with
    1 real unit and a negative connection between actual stimulus and sensory 
    input (the higher the world's value, the lower the stimulus'''

    return initializeBraiten1_1(True)

def initializeBraiten1_1(raw=False,params=None):
    '''
    Initialize a Homeostat to replicate a Braitenberg type-1 vehicle with
    1 real unit for both  motor and sensor, plus one HomeoUnitInput to connect to the outside world.
    Set up Webots accordingly and pass Webots parameters (port #) to the units

    The initialization variable 'raw' controls the type of sensory tranducer. 
    If it is set to 'False" (default) the raw sensory input from webot is reversed: high sensory values correspond 
    to high actual stimuli, and viceversa.
    If the 'raw' variable is set to True, the sensory transducer reads webots raw values, 
    which are minimum for maximum stimulus and maximal for minimun stimulus                      
    ''' 
    if raw == None:
        raw = False
            

    
    "1. setup webots"
    "PUT THE CORRECT WEBOTS WORLD HERE WITH COMPLETE PATH"  
    webotsWorld = '/home/stefano/Documents/Projects/Homeostat/Simulator/Python-port/Homeo/src/Webots/Homeo-experiments/worlds/khepera-braitenberg-1-1-HOMEO.wbt'   
    '''Webots parameters for tcp/ip communication
       (Defined in webots world specified above) '''
    kheperaPort = 10020
    supervisorPort = 10021
    
    startWebots(webotsWorld)
    
    "2. set up connection and create client and socket, etc."
    client = WebotsTCPClient()
    client._clientPort = kheperaPort
    socket = client.getClientSocket()
    
       
    '3.1 Setup robotic communication parameters in actuator and sensor'
    'motor'
    wheel = WebotsDiffMotorTCP('right')
    wheel.robotSocket = socket
    wheel.funcParameters = 10
    
    'sensor'
    if raw == False:
        sensorTransd = WebotsLightSensorTCP(0)
    else:
        sensorTransd = WebotsLightSensorRawTCP(0)
    sensorTransd._clientPort = kheperaPort
    sensorTransd.robotSocket = socket
    
    '3.2 initialize motor and sensor units with properly setup motor and sensor '
    motor = HomeoUnitNewtonianActuator(transducer = wheel)
    sensor = HomeoUnitInput(transducer = sensorTransd)
    
    "4. Set up Homeostat"   
    hom = Homeostat()
    
    'Setup standard homeo parameters'
    motor_visc = 0.9 * HomeoUnit.DefaultParameters['maxViscosity']
    sensor_visc = 0.9 * HomeoUnit.DefaultParameters['maxViscosity']
    
    motor_mass = 100
    sensor_mass = 100
    
    motor_self_noise = 0.05
    sensor_self_noise = 0.05
    
    motor_density = 1
    sensor_density = 1
    
    motor_uniselector_timing= 100
    
    motor_self_connection_active = False  # Set to either True or False to (dis-)active uniselector 
    motor_self_connection_uniselector = 'manual'
    motor_self_connection_switch = -1
    motor_self_connection_potentiomenter = 0.1
    motor_self_connection_noise = 0.05
            
    motor_incoming_conn_weight = 0.5
    motor_incoming_conn_noise = 0.05
    motor_incoming_connection_polarity = 1
    motor_incoming_connection_uniselector = 'uniselector' 
    
    sensor_incoming_connection_weight = 0.5
    sensor_incoming_connection_noise = 0.05
    sensor_incoming_connection_polarity = 1
    sensor_incoming_connection_uniselector = 'manual'
    
    'Setup a 1 unit Homeostat with an additional input unit. Then change the parameters'
    if len(hom.homeoUnits) == 0 :                 # check if the homeostat is set up already"
            hom.addFullyConnectedUnit(motor)
            hom.addFullyConnectedUnit(sensor)

     
    'Disable all connections except self-connections'
    for unit in hom.homeoUnits:
        for i in xrange(1, len(hom.homeoUnits)):
            unit.inputConnections[i].status = False

    'Agent unit or motor'
    motor.name = 'Motor'
    motor.mass = motor_mass
    motor.viscosity = motor_visc
    motor.density = motor_density
    motor.noise = motor_self_noise
    motor.uniselectorActive = motor_self_connection_active
    motor.uniselectorTimeInterval = motor_uniselector_timing
    
    'self-connection'
    'disactivate self-connection'
    motor.inputConnections[0].status = False
    motor.potentiometer = motor_self_connection_potentiomenter
    motor.switch = motor_self_connection_switch
    motor.inputConnections[0].noise = motor_self_connection_noise
    motor.inputConnections[0].state = motor_self_connection_uniselector

    'Sensor unit'
    sensor.name = 'Sensor'
    sensor.mass = sensor_mass
    sensor.viscosity = sensor_visc
    sensor.density = sensor_density
    sensor.noise = sensor_self_noise

    'disactivate uniselector'
    sensor.uniselectorActive = False
    
    'disactivate self-connection'
    sensor.inputConnections[0].status = False

    "Set up homeostat's connection."
    'Motor is connected to (receives input from) sensor'
    for connection in motor.inputConnections:
        if connection.incomingUnit.name == 'Sensor':
            connection.newWeight(motor_incoming_conn_weight)
            connection.noise = motor_incoming_conn_noise
            connection.state = motor_incoming_connection_uniselector
            connection.status = True
    
    'Sensor is not connected to (does not receive input from) any other unit'
    for connection in sensor.inputConnections:
        connection.status = False
    
    hom._usesSocket = True

    'Return the properly configured homeostat'
    return hom

def initializeBraiten1_2Pos(params=None):
    '''Utility function to choose a  Braitenberg type-1 vehicle with
    2 real units and a positive connection between actual stimulus and sensory 
    input (the higher the world's value, the higher the stimulus'''
    return initializeBraiten1_2(False)

def initializeBraiten1_2Neg(params=None):
    '''Utility function to choose a  Braitenberg type-1 vehicle with
    2 real units and a negative connection between actual stimulus and sensory 
    input (the higher the world's value, the lower the stimulus'''

    return initializeBraiten1_2(True)
     
def initializeBraiten1_2(raw=False,params=None):
    '''
    Initialize a Homeostat to replicate a Braitenberg type-1 vehicle with
    2 real units: one for the Motor and one for the sensor, plus one HomeoUnitInput
    to interface to the outside world         
    
    The initialization variable 'raw' controls the type of sensory tranducer. 
    If it is set to 'False" (default) the raw sensory input from webot is reversed: high sensory values correspond 
    to high actual stimuli, and viceversa.
    If the 'raw' variable is set to True, the sensory transducer reads webots raw values, 
    which are minimum for maximum stimulus and maximal for minimun stimulus                      
                      
    ''' 
    if raw == None:
            raw = False
            
             
    "1. setup webots"
    "PUT THE CORRECT WEBOTS WORLD HERE WITH COMPLETE PATH"  
    webotsWorld = '/home/stefano/Documents/Projects/Homeostat/Simulator/Python-port/Homeo/src/Webots/Homeo-experiments/worlds/khepera-braitenberg-1-1-HOMEO.wbt'   

    '''Webots parameters for tcp/ip communication
       (Defined in webots world specified above
    '''
    kheperaPort = 10020
    supervisorPort = 10021
    
    startWebots(webotsWorld)
    
    "2. set up connection and create client and socket, etc."
    client = WebotsTCPClient()
    client._clientPort = kheperaPort
    socket = client.getClientSocket()
    
       
    '3.1 Setup robotic communication parameters in actuator and sensor'
    'motor'
    wheel = WebotsDiffMotorTCP('right')
    wheel.robotSocket = socket
    wheel.funcParameters = 10
    
    'sensor'
    if raw == False:
        sensorTransd = WebotsLightSensorTCP(0)
    else:
        sensorTransd = WebotsLightSensorRawTCP(0)
        
    sensorTransd._clientPort = kheperaPort
    sensorTransd.robotSocket = socket
    
    '3.2 initialize motor and sensor units with properly setup motor and sensor '
    motor = HomeoUnitNewtonianActuator(transducer = wheel)
    sensor = HomeoUnitNewtonian()
    sensorOnly = HomeoUnitInput(transducer=sensorTransd)
        
    '3. Setup standard homeo parameters'
    motor_visc = 0.9 * HomeoUnit.DefaultParameters['maxViscosity']
    sensor_visc = 0.9 * HomeoUnit.DefaultParameters['maxViscosity']
    
    motor_mass = 100
    sensor_mass = 100
    
    motor_self_noise = 0.05
    sensor_self_noise = 0.05
    
    motor_density = 1
    sensor_density = 1
    
    motor_uniselector_timing= 100
    
    motor_self_connection_active = 'active'
    motor_self_connection_uniselector = 'manual'
    motor_self_connection_switch = -1
    motor_self_connection_potentiomenter = 0.1
    motor_self_connection_noise = 0.05
            
    motor_incoming_conn_weight = 0.5
    motor_incoming_conn_noise = 0.05
    motor_incoming_connection_polarity = 1
    motor_incoming_connection_uniselector = 'uniselector' 
    
    sensor_incoming_connection_weight = 0.5
    sensor_incoming_connection_noise = 0.05
    sensor_incoming_connection_polarity = 1
    sensor_incoming_connection_uniselector = 'manual'
    
    "4. Set up Homeostat"   
    hom = Homeostat()

    'Setup a 2 unit Homeostat with an additional input unit. Then change the parameters'
    if len(hom.homeoUnits) == 0 :                 # check if the homeostat is set up already"
            hom.addFullyConnectedUnit(motor)
            hom.addFullyConnectedUnit(sensor)
            hom.addFullyConnectedUnit(sensorOnly)

     
    'Disable all connections except self-connections'
    for unit in hom.homeoUnits:
        for i in xrange(1, len(hom.homeoUnits)):
            unit.inputConnections[i].status = False

    '4.1 Agent unit or motor parameters setting'
    motor.name = 'Motor'
    motor.mass = motor_mass
    motor.viscosity = motor_visc
    motor.density = motor_density
    motor.noise = motor_self_noise
    motor.uniselectorTimeInterval = motor_uniselector_timing
    
    'self-connection'
    motor.potentiometer = motor_self_connection_potentiomenter
    motor.switch = motor_self_connection_switch
    motor.inputConnections[0].noise = motor_self_connection_noise
    motor.inputConnections[0].state = motor_self_connection_uniselector

    '4.2 Sensor unit parameters setting'
    sensor.name = 'Sensor'
    sensor.mass = sensor_mass
    sensor.viscosity = sensor_visc
    sensor.density = sensor_density
    sensor.noise = sensor_self_noise

    'Activate uniselector'
    sensor.uniselectorActive = True
    
    'Activate self-connection'
    sensor.inputConnections[0].status = True

    '4.3 SensorOnly unit parameters setting'
    sensorOnly.name = 'SensorOnly'
    sensorOnly.mass = sensor_mass
    sensorOnly.viscosity = sensor_visc
    sensorOnly.density = sensor_density
    sensorOnly.noise = sensor_self_noise

    'disactivate uniselector'
    sensorOnly.uniselectorActive = False
    
    'disactivate self-connection'
    sensorOnly.inputConnections[0].status = False


    "Set up homeostat's connections"
    'Motor is connected to (receives input from) sensor'
    for connection in motor.inputConnections:
        if connection.incomingUnit.name == 'Sensor':
            connection.newWeight(motor_incoming_conn_weight)
            connection.noise = motor_incoming_conn_noise
            connection.state = motor_incoming_connection_uniselector
            connection.status = True
    
    'Sensor is  connected to (receives input from) sensorOnly'
    for connection in sensor.inputConnections:
        if connection.incomingUnit.name == 'SensorOnly':
            connection.newWeight(motor_incoming_conn_weight)
            connection.noise = motor_incoming_conn_noise
            connection.state = motor_incoming_connection_uniselector
            connection.status = True    
            
    'SensorOnly is not connected to (does not receive input from) any other unit'
    for connection in sensorOnly.inputConnections:
        connection.status = False

    hom._usesSocket = True

    'Return the properly configured homeostat'
    return hom


def initializeBraiten1_3(params=None):
    '''
    Initialize a Homeostat to replicate a Braitenberg type-1 vehicle with
    3 real units: one for the Motor,  one for the sensor, and one hidden unit, 
    plus one HomeoUnitInput to interface to the outside world         
                          
    ''' 
     
    "1. setup webots"
    "PUT THE CORRECT WEBOTS WORLD HERE WITH COMPLETE PATH"  
    webotsWorld = '/home/stefano/Documents/Projects/Homeostat/Simulator/Python-port/Homeo/src/Webots/Homeo-experiments/worlds/khepera-braitenberg-1-1-HOMEO.wbt'   

    '''Webots parameters for tcp/ip communication
       (Defined in webots world specified above
    '''
    kheperaPort = 10020
    supervisorPort = 10021
    
    startWebots(webotsWorld)
    
    "2. set up connection and create client and socket, etc."
    client = WebotsTCPClient()
    client._clientPort = kheperaPort
    socket = client.getClientSocket()
    
       
    '3.1 Setup robotic communication parameters in actuator and sensor'
    'motor'
    wheel = WebotsDiffMotorTCP('right')
    wheel.robotSocket = socket
    wheel.funcParameters = 10
    
    'sensor'
    sensorTransd = WebotsLightSensorTCP(0)
    sensorTransd._clientPort = kheperaPort
    sensorTransd.robotSocket = socket
    
    '3.2 initialize motor and sensor units with properly setup motor and sensor '
    motor = HomeoUnitNewtonianActuator(transducer = wheel)
    sensor = HomeoUnitNewtonian()
    hidden = HomeoUnitNewtonian()
    sensorOnly = HomeoUnitInput(transducer=sensorTransd)
        
    '3. Setup standard homeo parameters'
    motor_visc = 0.9 * HomeoUnit.DefaultParameters['maxViscosity']
    sensor_visc = 0.9 * HomeoUnit.DefaultParameters['maxViscosity']
    
    motor_mass = 100
    sensor_mass = 100
    
    motor_self_noise = 0.05
    sensor_self_noise = 0.05
    
    motor_density = 1
    sensor_density = 1
    
    motor_uniselector_timing= 100
    
    motor_self_connection_active = 'active'
    motor_self_connection_uniselector = 'manual'
    motor_self_connection_switch = -1
    motor_self_connection_potentiomenter = 0.1
    motor_self_connection_noise = 0.05
            
    motor_incoming_conn_weight = 0.5
    motor_incoming_conn_noise = 0.05
    motor_incoming_connection_polarity = 1
    motor_incoming_connection_uniselector = 'uniselector' 
    
    sensor_incoming_connection_weight = 0.5
    sensor_incoming_connection_noise = 0.05
    sensor_incoming_connection_polarity = 1
    sensor_incoming_connection_uniselector = 'manual'
    
    "4. Set up Homeostat"   
    hom = Homeostat()

    'Setup a 3 unit Homeostat with an additional input unit. Then change the parameters'
    if len(hom.homeoUnits) == 0 :                 # check if the homeostat is set up already"
            hom.addFullyConnectedUnit(motor)
            hom.addFullyConnectedUnit(sensor)
            hom.addFullyConnectedUnit(hidden)
            hom.addFullyConnectedUnit(sensorOnly)

     
    'Disable all connections except self-connections'
    for unit in hom.homeoUnits:
        for i in xrange(1, len(hom.homeoUnits)):
            unit.inputConnections[i].status = False

    '4.1 Agent unit or motor parameters setting'
    motor.name = 'Motor'
    motor.mass = motor_mass
    motor.viscosity = motor_visc
    motor.density = motor_density
    motor.noise = motor_self_noise
    motor.uniselectorTimeInterval = motor_uniselector_timing
    
    'self-connection'
    motor.potentiometer = motor_self_connection_potentiomenter
    motor.switch = motor_self_connection_switch
    motor.inputConnections[0].noise = motor_self_connection_noise
    motor.inputConnections[0].state = motor_self_connection_uniselector

    '4.2 Sensor unit parameters setting'
    sensor.name = 'Sensor'
    sensor.mass = sensor_mass
    sensor.viscosity = sensor_visc
    sensor.density = sensor_density
    sensor.noise = sensor_self_noise

    'Activate uniselector'
    sensor.uniselectorActive = True
    
    'Activate self-connection'
    sensor.inputConnections[0].status = True

    '4.3 SensorOnly unit parameters setting'
    sensorOnly.name = 'SensorOnly'
    sensorOnly.mass = sensor_mass
    sensorOnly.viscosity = sensor_visc
    sensorOnly.density = sensor_density
    sensorOnly.noise = sensor_self_noise

    'disactivate uniselector'
    sensorOnly.uniselectorActive = False
    
    'disactivate self-connection'
    sensorOnly.inputConnections[0].status = False
    
    '4.4 hidden unit paramter setting'
    hidden.name = 'Hidden'
    hidden.mass = sensor.mass
    hidden.viscosity = sensor.viscosity
    hidden.density = sensor.density
    hidden.noise = sensor.noise


    "Set up homeostat's connections"
    'Motor is connected to (receives input from) sensor'
    for connection in motor.inputConnections:
        if connection.incomingUnit.name == 'Sensor':
            connection.newWeight(motor_incoming_conn_weight)
            connection.noise = motor_incoming_conn_noise
            connection.state = motor_incoming_connection_uniselector
            connection.status = True
    
    'Sensor is  connected to (receives input from) sensorOnly'
    for connection in sensor.inputConnections:
        if connection.incomingUnit.name == 'SensorOnly':
            connection.newWeight(motor_incoming_conn_weight)
            connection.noise = motor_incoming_conn_noise
            connection.state = motor_incoming_connection_uniselector
            connection.status = True    
            
    'SensorOnly is not connected (does not receive input from) any other unit'
    for connection in sensorOnly.inputConnections:
        connection.status = False

    hom._usesSocket = True

    'Return the properly configured homeostat'
    return hom

 
def initializeBraiten2_1(params=None):
    '''
    Initialize a Homeostat to replicate a Braitenberg type-2 vehicle with
    3 real units: two for either Motor and one for the sensor, plus one HomeoUnitInput
    to interface to the outside world
    ''' 
    hom = Homeostat()

def initializeBraiten2_2(raw=False,params=None):
    '''
    Initialize a Homeostat to replicate a Braitenberg type-2 vehicle with
    4 real units: two for either Motor and two for the sensors, plus 2  HomeoInput Units
    to interface to the outside world
    
    The initialization variable 'raw' controls the type of sensory tranducer. 
    If it is set to 'False" (default) the raw sensory input from webot is reversed: high sensory values correspond 
    to high actual stimuli, and viceversa.
    This setting is equivalent to a classic Braitenberg vehicle: a high (e.g.)
    light intensity in the world will translate into a high sensor reading.
     
    If the 'raw' variable is set to True, the sensory transducer reads webots raw values, 
    which are minimum for maximum stimulus and maximal for minimun stimulus.
    This is the **reverse** of the classical Braitenberg case: a high intensity in the world
    will translate into a low sensor value.  
                      
''' 
    if raw == None:
        raw = False
             
    "1. setup webots"
    "PUT THE CORRECT WEBOTS WORLD HERE WITH COMPLETE PATH"  
    webotsWorld = '/home/stefano/Documents/Projects/Homeostat/Simulator/Python-port/Homeo/src/Webots/Homeo-experiments/worlds/khepera-braitenberg-2-HOMEO.wbt'
       

    '''Webots parameters for tcp/ip communication
       (Defined in webots world specified above)
    '''
    kheperaPort = 10020
    #kheperaPort = 50000   # Test server at port 50000 that just echoes commands back
    supervisorPort = 10021
    
    startWebots(webotsWorld)
    
    "2. set up connection and create client and socket, etc."
    client = WebotsTCPClient()
    client._clientPort = kheperaPort
    socket = client.getClientSocket()
    print "Connection to external robotic enviroment initialized"
       
    '3.1 Setup robotic communication parameters in actuator and sensor'
    'motors'
    rightWheel = WebotsDiffMotorTCP('right')
    leftWheel = WebotsDiffMotorTCP('left')
    rightWheel.robotSocket = socket
    rightWheel.funcParameters = 10
    leftWheel.robotSocket = socket
    leftWheel.funcParameters = 10

    
    'sensors'
    if raw == False:
        leftEyeSensorTransd  = WebotsLightSensorTCP(0)
        rightEyeSensorTransd = WebotsLightSensorTCP(1)
    else:
        leftEyeSensorTransd  = WebotsLightSensorRawTCP(0)
        rightEyeSensorTransd = WebotsLightSensorRawTCP(1)

        
    leftEyeSensorTransd._clientPort = kheperaPort
    leftEyeSensorTransd.robotSocket = socket
    rightEyeSensorTransd._clientPort = kheperaPort
    rightEyeSensorTransd.robotSocket = socket
    
    '3.2 initialize motors and sensors units with properly setup motors and sensors'    
    rightMotor = HomeoUnitNewtonianActuator(transducer = rightWheel)
    leftMotor = HomeoUnitNewtonianActuator(transducer = leftWheel)
    
    leftEye = HomeoUnitNewtonian()
    rightEye = HomeoUnitNewtonian()
    leftEyeSensorOnly = HomeoUnitInput(transducer=leftEyeSensorTransd)
    rightEyeSensorOnly = HomeoUnitInput(transducer=rightEyeSensorTransd)
    
        
    '3. Setup standard homeo parameters'
    motor_visc = 0.9 * HomeoUnit.DefaultParameters['maxViscosity']
    sensor_visc = 0.9 * HomeoUnit.DefaultParameters['maxViscosity']
    
    motor_mass = 100
    sensor_mass = 100
    
    motor_self_noise = 0.05
    sensor_self_noise = 0.05
    
    motor_density = 1
    sensor_density = 1
    
    motor_uniselector_timing= 100
    
    motor_self_connection_active = 'active'
    motor_self_connection_uniselector = 'manual'
    motor_self_connection_switch = -1
    motor_self_connection_potentiomenter = 0.1
    motor_self_connection_noise = 0.05
            
    motor_incoming_conn_weight = 0.5
    motor_incoming_conn_noise = 0.05
    motor_incoming_connection_polarity = 1
    motor_incoming_connection_uniselector = 'uniselector' 
    
    sensor_incoming_connection_weight = 0.5
    sensor_incoming_connection_noise = 0.05
    sensor_incoming_connection_polarity = 1
    sensor_incoming_connection_uniselector = 'manual'
    
    "4. Set up Homeostat"   
    hom = Homeostat()

    'Setup a 4 unit Homeostat with 2 additional input units. Then change the parameters'
    if len(hom.homeoUnits) == 0 :                 # check if the homeostat is set up already"
            hom.addFullyConnectedUnit(rightMotor)
            hom.addFullyConnectedUnit(leftMotor)
            hom.addFullyConnectedUnit(leftEye)
            hom.addFullyConnectedUnit(rightEye)
            hom.addFullyConnectedUnit(leftEyeSensorOnly)
            hom.addFullyConnectedUnit(rightEyeSensorOnly)


     
    'Disable all connections except self-connections'
    for unit in hom.homeoUnits:
        for i in xrange(1, len(hom.homeoUnits)):
            unit.inputConnections[i].status = False

    '4.1 Agent units or motors parameters setting'
    leftMotor.name = 'Left Motor'
    leftMotor.mass = motor_mass
    leftMotor.viscosity = motor_visc
    leftMotor.density = motor_density
    leftMotor.noise = motor_self_noise
    leftMotor.uniselectorTimeInterval = motor_uniselector_timing

    rightMotor.name = 'Right Motor'
    rightMotor.mass = motor_mass
    rightMotor.viscosity = motor_visc
    rightMotor.density = motor_density
    rightMotor.noise = motor_self_noise
    rightMotor.uniselectorTimeInterval = motor_uniselector_timing
    
    'self-connection'
    leftMotor.potentiometer = motor_self_connection_potentiomenter
    leftMotor.switch = motor_self_connection_switch
    leftMotor.inputConnections[0].noise = motor_self_connection_noise
    leftMotor.inputConnections[0].state = motor_self_connection_uniselector

    rightMotor.potentiometer = motor_self_connection_potentiomenter
    rightMotor.switch = motor_self_connection_switch
    rightMotor.inputConnections[0].noise = motor_self_connection_noise
    rightMotor.inputConnections[0].state = motor_self_connection_uniselector

    '4.2 Sensor units parameters setting'
    leftEye.name = 'Left Eye'
    leftEye.mass = sensor_mass
    leftEye.viscosity = sensor_visc
    leftEye.density = sensor_density
    leftEye.noise = sensor_self_noise

    rightEye.name = 'Right Eye'
    rightEye.mass = sensor_mass
    rightEye.viscosity = sensor_visc
    rightEye.density = sensor_density
    rightEye.noise = sensor_self_noise

    'Activate uniselector'
    leftEye.uniselectorActive = True
    rightEye.uniselectorActive = True
    
    'Activate self-connection'
    leftEye.inputConnections[0].status = True
    rightEye.uniselectorActive = True

    '4.3 SensorOnly units parameters setting'
    leftEyeSensorOnly.name = 'Left Sensor'
    leftEyeSensorOnly.mass = sensor_mass
    leftEyeSensorOnly.viscosity = sensor_visc
    leftEyeSensorOnly.density = sensor_density
    leftEyeSensorOnly.noise = sensor_self_noise

    rightEyeSensorOnly.name = 'Right Sensor'
    rightEyeSensorOnly.mass = sensor_mass
    rightEyeSensorOnly.viscosity = sensor_visc
    rightEyeSensorOnly.density = sensor_density
    rightEyeSensorOnly.noise = sensor_self_noise

    'disactivate uniselector'
    leftEyeSensorOnly.uniselectorActive = False
    rightEyeSensorOnly.uniselectorActive = False
    
    'disactivate self-connection'
    leftEyeSensorOnly.inputConnections[0].status = False
    rightEyeSensorOnly.inputConnections[0].status = False


    '''Set up homeostat's initial connections,
       according to a Braitenberg's cross-connection scheme'''
    'Right motor is connected to (receives input from) left eye sensor'
    for connection in rightMotor.inputConnections:
        if connection.incomingUnit.name == 'Left Eye':
            connection.newWeight(motor_incoming_conn_weight)
            connection.noise = motor_incoming_conn_noise
            connection.state = motor_incoming_connection_uniselector
            connection.status = True
            
    'Left motor is connected to (receives input from) right eye sensor'
    for connection in leftMotor.inputConnections:
        if connection.incomingUnit.name == 'Right Eye':
            connection.newWeight(motor_incoming_conn_weight)
            connection.noise = motor_incoming_conn_noise
            connection.state = motor_incoming_connection_uniselector
            connection.status = True

    
    'The Right Eye is only connected to (receives input from) Right Sensor'
    for connection in rightEye.inputConnections:
        if connection.incomingUnit.name == 'Right Sensor':
            connection.newWeight(motor_incoming_conn_weight)
            connection.noise = motor_incoming_conn_noise
            connection.state = motor_incoming_connection_uniselector
            connection.status = True    
            
    'The Left Eye  is only connected to (receives input from) Left Sensor'
    for connection in leftEye.inputConnections:
        if connection.incomingUnit.name == 'Left Sensor':
            connection.newWeight(motor_incoming_conn_weight)
            connection.noise = motor_incoming_conn_noise
            connection.state = motor_incoming_connection_uniselector
            connection.status = True    

    'Sensors are not connected (does not receive input from) any other unit'
    for connection in leftEyeSensorOnly.inputConnections:
        connection.status = False
    for connection in rightEyeSensorOnly.inputConnections:
        connection.status = False

    hom._usesSocket = True

    'Return the properly configured homeostat'
    hDebug('unit', "Homeostat initialized")
    return hom

def initializeBraiten2_2Aristotelian(raw=True,params=None):
    '''
    Initialize a Homeostat to replicate a Braitenberg type-2 vehicle with
    4 ARISTOTELIAN real units: two for either Motor and two for the sensors, plus 2  HomeoInput Units
    to interface to the outside world
    
    The initialization variable 'raw' controls the type of sensory tranducer. 
    If it is set to 'False" (default) the raw sensory input from webot is reversed: high sensory values correspond 
    to high actual stimuli, and viceversa.
    This setting is equivalent to a classic Braitenberg vehicle: a high (e.g.)
    light intensity in the world will translate into a high sensor reading.
     
    If the 'raw' variable is set to True, the sensory transducer reads webots raw values, 
    which are minimum for maximum stimulus and maximal for minimun stimulus.
    This is the **reverse** of the classical Braitenberg case: a high intensity in the world
    will translate into a low sensor value.  
                      
''' 
    if raw == None:
        raw = False
             
    "1. setup webots"
    "PUT THE CORRECT WEBOTS WORLD HERE WITH COMPLETE PATH"  
    webotsWorld = '/home/stefano/Documents/Projects/Homeostat/Simulator/Python-port/Homeo/src/Webots/Homeo-experiments/worlds/khepera-braitenberg-2-HOMEO.wbt'
       

    '''Webots parameters for tcp/ip communication
       (Defined in webots world specified above)
    '''
    kheperaPort = 10020
    supervisorPort = 10021
    
    startWebots(webotsWorld)
    
    "2. set up connection and create client and socket, etc."
    client = WebotsTCPClient()
    client._clientPort = kheperaPort
    socket = client.getClientSocket()
    
       
    '3.1 Setup robotic communication parameters in actuator and sensor'
    'motors'
    rightWheel = WebotsDiffMotorTCP('right')
    leftWheel = WebotsDiffMotorTCP('left')
    rightWheel.robotSocket = socket
    rightWheel.funcParameters = 10
    leftWheel.robotSocket = socket
    leftWheel.funcParameters = 10

    
    'sensors'
    if raw == False:
        leftEyeSensorTransd  = WebotsLightSensorTCP(0)
        rightEyeSensorTransd = WebotsLightSensorTCP(1)
    else:
        leftEyeSensorTransd  = WebotsLightSensorRawTCP(0)
        rightEyeSensorTransd = WebotsLightSensorRawTCP(1)

        
    leftEyeSensorTransd._clientPort = kheperaPort
    leftEyeSensorTransd.robotSocket = socket
    rightEyeSensorTransd._clientPort = kheperaPort
    rightEyeSensorTransd.robotSocket = socket
    
    '3.2 initialize motors and sensors units with properly setup motors and sensors'    
    rightMotor = HomeoUnitAristotelianActuator(transducer = rightWheel)
    leftMotor = HomeoUnitAristotelianActuator(transducer = leftWheel)
    
    leftEye = HomeoUnitAristotelian()
    rightEye = HomeoUnitAristotelian()
    leftEyeSensorOnly = HomeoUnitInput(transducer=leftEyeSensorTransd)
    rightEyeSensorOnly = HomeoUnitInput(transducer=rightEyeSensorTransd)
    
        
    '3. Setup standard homeo parameters'
    motor_visc = 0.9 * HomeoUnit.DefaultParameters['maxViscosity']
    sensor_visc = 0.9 * HomeoUnit.DefaultParameters['maxViscosity']
    
    motor_mass = 100
    sensor_mass = 100
    
    motor_self_noise = 0.05
    sensor_self_noise = 0.05
    
    motor_density = 1
    sensor_density = 1
    
    motor_uniselector_timing= 100
    
    motor_self_connection_active = 'active'
    motor_self_connection_uniselector = 'manual'
    motor_self_connection_switch = -1
    motor_self_connection_potentiomenter = 0.1
    motor_self_connection_noise = 0.05
            
    motor_incoming_conn_weight = 0.5
    motor_incoming_conn_noise = 0.05
    motor_incoming_connection_polarity = 1
    motor_incoming_connection_uniselector = 'uniselector' 
    
    sensor_incoming_connection_weight = 0.5
    sensor_incoming_connection_noise = 0.05
    sensor_incoming_connection_polarity = 1
    sensor_incoming_connection_uniselector = 'manual'
    
    "4. Set up Homeostat"   
    hom = Homeostat()

    'Setup a 4 unit Homeostat with 2 additional input units. Then change the parameters'
    if len(hom.homeoUnits) == 0 :                 # check if the homeostat is set up already"
            hom.addFullyConnectedUnit(rightMotor)
            hom.addFullyConnectedUnit(leftMotor)
            hom.addFullyConnectedUnit(leftEye)
            hom.addFullyConnectedUnit(rightEye)
            hom.addFullyConnectedUnit(leftEyeSensorOnly)
            hom.addFullyConnectedUnit(rightEyeSensorOnly)


     
    'Disable all connections except self-connections'
    for unit in hom.homeoUnits:
        for i in xrange(1, len(hom.homeoUnits)):
            unit.inputConnections[i].status = False

    '4.1 Agent units or motors parameters setting'
    leftMotor.name = 'Left Motor'
    leftMotor.mass = motor_mass
    leftMotor.viscosity = motor_visc
    leftMotor.density = motor_density
    leftMotor.noise = motor_self_noise
    leftMotor.uniselectorTimeInterval = motor_uniselector_timing

    rightMotor.name = 'Right Motor'
    rightMotor.mass = motor_mass
    rightMotor.viscosity = motor_visc
    rightMotor.density = motor_density
    rightMotor.noise = motor_self_noise
    rightMotor.uniselectorTimeInterval = motor_uniselector_timing
    
    'self-connection'
    leftMotor.potentiometer = motor_self_connection_potentiomenter
    leftMotor.switch = motor_self_connection_switch
    leftMotor.inputConnections[0].noise = motor_self_connection_noise
    leftMotor.inputConnections[0].state = motor_self_connection_uniselector

    rightMotor.potentiometer = motor_self_connection_potentiomenter
    rightMotor.switch = motor_self_connection_switch
    rightMotor.inputConnections[0].noise = motor_self_connection_noise
    rightMotor.inputConnections[0].state = motor_self_connection_uniselector

    '4.2 Sensor units parameters setting'
    leftEye.name = 'Left Eye'
    leftEye.mass = sensor_mass
    leftEye.viscosity = sensor_visc
    leftEye.density = sensor_density
    leftEye.noise = sensor_self_noise

    rightEye.name = 'Right Eye'
    rightEye.mass = sensor_mass
    rightEye.viscosity = sensor_visc
    rightEye.density = sensor_density
    rightEye.noise = sensor_self_noise

    'Activate uniselector'
    leftEye.uniselectorActive = True
    rightEye.uniselectorActive = True
    
    'Activate self-connection'
    leftEye.inputConnections[0].status = True
    rightEye.uniselectorActive = True

    '4.3 SensorOnly units parameters setting'
    leftEyeSensorOnly.name = 'Left Sensor'
    leftEyeSensorOnly.mass = sensor_mass
    leftEyeSensorOnly.viscosity = sensor_visc
    leftEyeSensorOnly.density = sensor_density
    leftEyeSensorOnly.noise = sensor_self_noise

    rightEyeSensorOnly.name = 'Right Sensor'
    rightEyeSensorOnly.mass = sensor_mass
    rightEyeSensorOnly.viscosity = sensor_visc
    rightEyeSensorOnly.density = sensor_density
    rightEyeSensorOnly.noise = sensor_self_noise

    'disactivate uniselector'
    leftEyeSensorOnly.uniselectorActive = False
    rightEyeSensorOnly.uniselectorActive = False
    
    'disactivate self-connection'
    leftEyeSensorOnly.inputConnections[0].status = False
    rightEyeSensorOnly.inputConnections[0].status = False


    '''Set up homeostat's initial connections,
       according to a Braitenberg's cross-connection scheme'''
    'Right motor is connected to (receives input from) left eye sensor'
    for connection in rightMotor.inputConnections:
        if connection.incomingUnit.name == 'Left Eye':
            connection.newWeight(motor_incoming_conn_weight)
            connection.noise = motor_incoming_conn_noise
            connection.state = motor_incoming_connection_uniselector
            connection.status = True
            
    'Left motor is connected to (receives input from) right eye sensor'
    for connection in leftMotor.inputConnections:
        if connection.incomingUnit.name == 'Right Eye':
            connection.newWeight(motor_incoming_conn_weight)
            connection.noise = motor_incoming_conn_noise
            connection.state = motor_incoming_connection_uniselector
            connection.status = True

    
    'The Right Eye is only connected to (receives input from) Right Sensor'
    for connection in rightEye.inputConnections:
        if connection.incomingUnit.name == 'Right Sensor':
            connection.newWeight(motor_incoming_conn_weight)
            connection.noise = motor_incoming_conn_noise
            connection.state = motor_incoming_connection_uniselector
            connection.status = True    
            
    'The Left Eye  is only connected to (receives input from) Left Sensor'
    for connection in leftEye.inputConnections:
        if connection.incomingUnit.name == 'Left Sensor':
            connection.newWeight(motor_incoming_conn_weight)
            connection.noise = motor_incoming_conn_noise
            connection.state = motor_incoming_connection_uniselector
            connection.status = True    

    'Sensors are not connected (does not receive input from) any other unit'
    for connection in leftEyeSensorOnly.inputConnections:
        connection.status = False
    for connection in rightEyeSensorOnly.inputConnections:
        connection.status = False

    hom._usesSocket = True

    'Return the properly configured homeostat'
    return hom

def initializeBraiten2_2_Full(raw=False,params=None):
    '''
    Initialize a Homeostat to replicate a Braitenberg type-2 vehicle with
    4 real units: two for either Motor and two for the sensors, plus 2  HomeoInput Units
    to interface to the outside world
    
    Initialize the homeostat to be **fully connected**
    
    The initialization variable 'raw' controls the type of sensory tranducer. 
    If it is set to 'False" (default) the raw sensory input from webot is reversed: high sensory values correspond 
    to high actual stimuli, and viceversa.
    This setting is equivalent to a classic Braitenberg vehicle: a high (e.g.)
    light intensity in the world will translate into a high sensor reading.
     
    If the 'raw' variable is set to True, the sensory transducer reads webots raw values, 
    which are minimum for maximum stimulus and maximal for minimun stimulus.
    This is the **reverse** of the classical Braitenberg case: a high intensity in the world
    will translate into a low sensor value.  
                      
''' 
    if raw == None:
        raw = False
             
    "1. setup webots"
    "PUT THE CORRECT WEBOTS WORLD HERE WITH COMPLETE PATH"  
    webotsWorld = '/home/stefano/Documents/Projects/Homeostat/Simulator/Python-port/Homeo/src/Webots/Homeo-experiments/worlds/khepera-braitenberg-2-HOMEO.wbt'
       

    '''Webots parameters for tcp/ip communication
       (Defined in webots world specified above)
    '''
    kheperaPort = 10020
    supervisorPort = 10021
    
    startWebots(webotsWorld)
    
    "2. set up connection and create client and socket, etc."
    client = WebotsTCPClient()
    client._clientPort = kheperaPort
    socket = client.getClientSocket()
    
       
    '3.1 Setup robotic communication parameters in actuator and sensor'
    'motors'
    rightWheel = WebotsDiffMotorTCP('right')
    leftWheel = WebotsDiffMotorTCP('left')
    rightWheel.robotSocket = socket
    rightWheel.funcParameters = 100  #wheel speed in rad/s
    leftWheel.robotSocket = socket
    leftWheel.funcParameters = 100   ##wheel speed in rad/s

    
    'sensors'
    if raw == False:
        leftEyeSensorTransd  = WebotsLightSensorTCP(0)
        rightEyeSensorTransd = WebotsLightSensorTCP(1)
    else:
        leftEyeSensorTransd  = WebotsLightSensorRawTCP(0)
        rightEyeSensorTransd = WebotsLightSensorRawTCP(1)

        
    leftEyeSensorTransd._clientPort = kheperaPort
    leftEyeSensorTransd.robotSocket = socket
    rightEyeSensorTransd._clientPort = kheperaPort
    rightEyeSensorTransd.robotSocket = socket
    
    '3.2 initialize motors and sensors units with properly setup motors and sensors'    
    rightMotor = HomeoUnitNewtonianActuator(transducer = rightWheel)
    leftMotor = HomeoUnitNewtonianActuator(transducer = leftWheel)
    
    leftEye = HomeoUnitNewtonian()
    rightEye = HomeoUnitNewtonian()
    leftEyeSensorOnly = HomeoUnitInput(transducer=leftEyeSensorTransd)
    rightEyeSensorOnly = HomeoUnitInput(transducer=rightEyeSensorTransd)
    
        
    '3. Setup standard homeo parameters'
    motor_visc = 0.9 * HomeoUnit.DefaultParameters['maxViscosity']
    sensor_visc = 0.9 * HomeoUnit.DefaultParameters['maxViscosity']
    
    motor_mass = 100
    sensor_mass = 100
    
    motor_self_noise = 0.05
    sensor_self_noise = 0.05
    
    motor_density = 1
    sensor_density = 1
    
    motor_uniselector_timing= 100
    
    motor_self_connection_active = 'active'
    motor_self_connection_uniselector = 'manual'
    motor_self_connection_switch = -1
    motor_self_connection_potentiomenter = 0.1
    motor_self_connection_noise = 0.05
            
    motor_incoming_conn_weight = 0.5
    motor_incoming_conn_noise = 0.05
    motor_incoming_connection_polarity = 1
    motor_incoming_connection_uniselector = 'uniselector' 
    
    sensor_incoming_connection_weight = 0.5
    sensor_incoming_connection_noise = 0.05
    sensor_incoming_connection_polarity = 1
    sensor_incoming_connection_uniselector = 'manual'
    
    "4. Set up Homeostat"   
    hom = Homeostat()

    'Setup a 4 unit Homeostat with 2 additional input units. Then change the parameters'
    if len(hom.homeoUnits) == 0 :                 # check if the homeostat is set up already"
            hom.addFullyConnectedUnit(rightMotor)
            hom.addFullyConnectedUnit(leftMotor)
            hom.addFullyConnectedUnit(leftEye)
            hom.addFullyConnectedUnit(rightEye)
            hom.addFullyConnectedUnit(leftEyeSensorOnly)
            hom.addFullyConnectedUnit(rightEyeSensorOnly)


     
    #===========================================================================
    # 'Disable all connections except self-connections'
    # for unit in hom.homeoUnits:
    #     for i in xrange(1, len(hom.homeoUnits)):
    #         unit.inputConnections[i].status = False
    #===========================================================================

    '4.1 Agent units or motors parameters setting'
    leftMotor.name = 'Left Motor'
    leftMotor.mass = motor_mass
    leftMotor.viscosity = motor_visc
    leftMotor.density = motor_density
    leftMotor.noise = motor_self_noise
    leftMotor.uniselectorTimeInterval = motor_uniselector_timing

    rightMotor.name = 'Right Motor'
    rightMotor.mass = motor_mass
    rightMotor.viscosity = motor_visc
    rightMotor.density = motor_density
    rightMotor.noise = motor_self_noise
    rightMotor.uniselectorTimeInterval = motor_uniselector_timing
    
    'self-connection'
    leftMotor.potentiometer = motor_self_connection_potentiomenter
    leftMotor.switch = motor_self_connection_switch
    leftMotor.inputConnections[0].noise = motor_self_connection_noise
    leftMotor.inputConnections[0].state = motor_self_connection_uniselector

    rightMotor.potentiometer = motor_self_connection_potentiomenter
    rightMotor.switch = motor_self_connection_switch
    rightMotor.inputConnections[0].noise = motor_self_connection_noise
    rightMotor.inputConnections[0].state = motor_self_connection_uniselector

    '4.2 Sensor units parameters setting'
    leftEye.name = 'Left Eye'
    leftEye.mass = sensor_mass
    leftEye.viscosity = sensor_visc
    leftEye.density = sensor_density
    leftEye.noise = sensor_self_noise

    rightEye.name = 'Right Eye'
    rightEye.mass = sensor_mass
    rightEye.viscosity = sensor_visc
    rightEye.density = sensor_density
    rightEye.noise = sensor_self_noise

    'Activate uniselector'
    leftEye.uniselectorActive = True
    rightEye.uniselectorActive = True
    
    'Activate self-connection'
    leftEye.inputConnections[0].status = True
    rightEye.uniselectorActive = True

    '4.3 SensorOnly units parameters setting'
    leftEyeSensorOnly.name = 'Left Sensor'
    leftEyeSensorOnly.mass = sensor_mass
    leftEyeSensorOnly.viscosity = sensor_visc
    leftEyeSensorOnly.density = sensor_density
    leftEyeSensorOnly.noise = sensor_self_noise

    rightEyeSensorOnly.name = 'Right Sensor'
    rightEyeSensorOnly.mass = sensor_mass
    rightEyeSensorOnly.viscosity = sensor_visc
    rightEyeSensorOnly.density = sensor_density
    rightEyeSensorOnly.noise = sensor_self_noise

    'disactivate uniselector'
    leftEyeSensorOnly.uniselectorActive = False
    rightEyeSensorOnly.uniselectorActive = False
    
    'disactivate self-connection'
    leftEyeSensorOnly.inputConnections[0].status = False
    rightEyeSensorOnly.inputConnections[0].status = False


    '''Set up homeostat's initial connections,
       according to a Braitenberg's cross-connection scheme'''
    'Right motor is connected to (receives input from) left eye sensor'
    for connection in rightMotor.inputConnections:
        if connection.incomingUnit.name == 'Left Eye':
            connection.newWeight(motor_incoming_conn_weight)
            connection.noise = motor_incoming_conn_noise
            connection.state = motor_incoming_connection_uniselector
            connection.status = True
            
    'Left motor is connected to (receives input from) right eye sensor'
    for connection in leftMotor.inputConnections:
        if connection.incomingUnit.name == 'Right Eye':
            connection.newWeight(motor_incoming_conn_weight)
            connection.noise = motor_incoming_conn_noise
            connection.state = motor_incoming_connection_uniselector
            connection.status = True

    
    'The Right Eye is only connected to (receives input from) Right Sensor'
    for connection in rightEye.inputConnections:
        if connection.incomingUnit.name == 'Right Sensor':
            connection.newWeight(motor_incoming_conn_weight)
            connection.noise = motor_incoming_conn_noise
            connection.state = motor_incoming_connection_uniselector
            connection.status = True    
            
    'The Left Eye  is only connected to (receives input from) Left Sensor'
    for connection in leftEye.inputConnections:
        if connection.incomingUnit.name == 'Left Sensor':
            connection.newWeight(motor_incoming_conn_weight)
            connection.noise = motor_incoming_conn_noise
            connection.state = motor_incoming_connection_uniselector
            connection.status = True    

    'Sensors are not connected (does not receive input from) any other unit'
    for connection in leftEyeSensorOnly.inputConnections:
        connection.status = False
    for connection in rightEyeSensorOnly.inputConnections:
        connection.status = False

    hom._usesSocket = True

    'Return the properly configured homeostat'
    return hom

def initializeBraiten2_7_Full(raw=False):
    '''
    Initialize a Homeostat to replicate a Braitenberg type-2 vehicle with
    7 real units: two for either Motor and two for the sensors, plus 3 internal units 
    and 2  HomeoInput Units to interface to the outside world
    
    Initialize the homeostat to be **fully connected**
    
    The initialization variable 'raw' controls the type of sensory tranducer. 
    If it is set to 'False" (default) the raw sensory input from webot is reversed: high sensory values correspond 
    to high actual stimuli, and viceversa.
    This setting is equivalent to a classic Braitenberg vehicle: a high (e.g.)
    light intensity in the world will translate into a high sensor reading.
     
    If the 'raw' variable is set to True, the sensory transducer reads webots raw values, 
    which are minimum for maximum stimulus and maximal for minimun stimulus.
    This is the **reverse** of the classical Braitenberg case: a high intensity in the world
    will translate into a low sensor value.  
                      
''' 
    if raw == None:
        raw = False
             
    "1. setup webots"
    "PUT THE CORRECT WEBOTS WORLD HERE WITH COMPLETE PATH"  
    webotsWorld = '/home/stefano/Documents/Projects/Homeostat/Simulator/Python-port/Homeo/src/Webots/Homeo-experiments/worlds/khepera-braitenberg-2-HOMEO.wbt'
       

    '''Webots parameters for tcp/ip communication
       (Defined in webots world specified above)
    '''
    kheperaPort = 10020
    supervisorPort = 10021
    
    startWebots(webotsWorld)
    
    "2. set up connection and create client and socket, etc."
    client = WebotsTCPClient()
    client._clientPort = kheperaPort
    socket = client.getClientSocket()
    
       
    '3.1 Setup robotic communication parameters in actuator and sensor'
    'motors'
    rightWheel = WebotsDiffMotorTCP('right')
    leftWheel = WebotsDiffMotorTCP('left')
    rightWheel.robotSocket = socket
    rightWheel.funcParameters = 10
    leftWheel.robotSocket = socket
    leftWheel.funcParameters = 10

    
    'sensors'
    if raw == False:
        leftEyeSensorTransd  = WebotsLightSensorTCP(0)
        rightEyeSensorTransd = WebotsLightSensorTCP(1)
    else:
        leftEyeSensorTransd  = WebotsLightSensorRawTCP(0)
        rightEyeSensorTransd = WebotsLightSensorRawTCP(1)

        
    leftEyeSensorTransd._clientPort = kheperaPort
    leftEyeSensorTransd.robotSocket = socket
    rightEyeSensorTransd._clientPort = kheperaPort
    rightEyeSensorTransd.robotSocket = socket
    
    '3.2 initialize motors and sensors units with properly setup motors and sensors'    
    rightMotor = HomeoUnitNewtonianActuator(transducer = rightWheel)
    leftMotor = HomeoUnitNewtonianActuator(transducer = leftWheel)
    
    leftEye = HomeoUnitNewtonian()
    rightEye = HomeoUnitNewtonian()
    leftEyeSensorOnly = HomeoUnitInput(transducer=leftEyeSensorTransd)
    rightEyeSensorOnly = HomeoUnitInput(transducer=rightEyeSensorTransd)
    
    ' Add internal units'
    interUnit_1 = HomeoUnitNewtonian()
    interUnit_2 = HomeoUnitNewtonian()
    interUnit_3 = HomeoUnitNewtonian()
        
    '3. Setup standard homeo parameters'
    motor_visc = 0.9 * HomeoUnit.DefaultParameters['maxViscosity']
    sensor_visc = 0.9 * HomeoUnit.DefaultParameters['maxViscosity']
    
    motor_mass = 100
    sensor_mass = 100
    
    motor_self_noise = 0.05
    sensor_self_noise = 0.05
    
    motor_density = 1
    sensor_density = 1
    
    motor_uniselector_timing= 100
    
    motor_self_connection_active = 'active'
    motor_self_connection_uniselector = 'manual'
    motor_self_connection_switch = -1
    motor_self_connection_potentiomenter = 0.1
    motor_self_connection_noise = 0.05
            
    motor_incoming_conn_weight = 0.5
    motor_incoming_conn_noise = 0.05
    motor_incoming_connection_polarity = 1
    motor_incoming_connection_uniselector = 'uniselector' 
    
    sensor_incoming_connection_weight = 0.5
    sensor_incoming_connection_noise = 0.05
    sensor_incoming_connection_polarity = 1
    sensor_incoming_connection_uniselector = 'manual'
    
    "4. Set up Homeostat"   
    hom = Homeostat()

    'Setup a 7 unit Homeostat with 2 additional input units. Then change the parameters'
    if len(hom.homeoUnits) == 0 :                 # check if the homeostat is set up already"
            hom.addFullyConnectedUnit(rightMotor)
            hom.addFullyConnectedUnit(leftMotor)
            hom.addFullyConnectedUnit(interUnit_1)
            hom.addFullyConnectedUnit(interUnit_2)
            hom.addFullyConnectedUnit(interUnit_3)
            hom.addFullyConnectedUnit(leftEye)
            hom.addFullyConnectedUnit(rightEye)
            hom.addFullyConnectedUnit(leftEyeSensorOnly)
            hom.addFullyConnectedUnit(rightEyeSensorOnly)


     
    #===========================================================================
    # 'Disable all connections except self-connections'
    # for unit in hom.homeoUnits:
    #     for i in xrange(1, len(hom.homeoUnits)):
    #         unit.inputConnections[i].status = False
    #===========================================================================

    '4.1 Agent units or motors parameters setting'
    leftMotor.name = 'Left Motor'
    leftMotor.mass = motor_mass
    leftMotor.viscosity = motor_visc
    leftMotor.density = motor_density
    leftMotor.noise = motor_self_noise
    leftMotor.uniselectorTimeInterval = motor_uniselector_timing

    rightMotor.name = 'Right Motor'
    rightMotor.mass = motor_mass
    rightMotor.viscosity = motor_visc
    rightMotor.density = motor_density
    rightMotor.noise = motor_self_noise
    rightMotor.uniselectorTimeInterval = motor_uniselector_timing
    
    'self-connection'
    leftMotor.potentiometer = motor_self_connection_potentiomenter
    leftMotor.switch = motor_self_connection_switch
    leftMotor.inputConnections[0].noise = motor_self_connection_noise
    leftMotor.inputConnections[0].state = motor_self_connection_uniselector

    rightMotor.potentiometer = motor_self_connection_potentiomenter
    rightMotor.switch = motor_self_connection_switch
    rightMotor.inputConnections[0].noise = motor_self_connection_noise
    rightMotor.inputConnections[0].state = motor_self_connection_uniselector

    '4.2 Sensor units parameters setting'
    leftEye.name = 'Left Eye'
    leftEye.mass = sensor_mass
    leftEye.viscosity = sensor_visc
    leftEye.density = sensor_density
    leftEye.noise = sensor_self_noise

    rightEye.name = 'Right Eye'
    rightEye.mass = sensor_mass
    rightEye.viscosity = sensor_visc
    rightEye.density = sensor_density
    rightEye.noise = sensor_self_noise

    'Activate uniselector'
    leftEye.uniselectorActive = True
    rightEye.uniselectorActive = True
    
    'Activate self-connection'
    leftEye.inputConnections[0].status = True
    rightEye.uniselectorActive = True

    '4.3 SensorOnly units parameters setting'
    leftEyeSensorOnly.name = 'Left Sensor'
    leftEyeSensorOnly.mass = sensor_mass
    leftEyeSensorOnly.viscosity = sensor_visc
    leftEyeSensorOnly.density = sensor_density
    leftEyeSensorOnly.noise = sensor_self_noise

    rightEyeSensorOnly.name = 'Right Sensor'
    rightEyeSensorOnly.mass = sensor_mass
    rightEyeSensorOnly.viscosity = sensor_visc
    rightEyeSensorOnly.density = sensor_density
    rightEyeSensorOnly.noise = sensor_self_noise

    'disactivate uniselector'
    leftEyeSensorOnly.uniselectorActive = False
    rightEyeSensorOnly.uniselectorActive = False
    
    'disactivate self-connection'
    leftEyeSensorOnly.inputConnections[0].status = False
    rightEyeSensorOnly.inputConnections[0].status = False


    '''Set up homeostat's initial connections,
       according to a Braitenberg's cross-connection scheme'''
    'Right motor is connected to (receives input from) left eye sensor'
    for connection in rightMotor.inputConnections:
        if connection.incomingUnit.name == 'Left Eye':
            connection.newWeight(motor_incoming_conn_weight)
            connection.noise = motor_incoming_conn_noise
            connection.state = motor_incoming_connection_uniselector
            connection.status = True
            
    'Left motor is connected to (receives input from) right eye sensor'
    for connection in leftMotor.inputConnections:
        if connection.incomingUnit.name == 'Right Eye':
            connection.newWeight(motor_incoming_conn_weight)
            connection.noise = motor_incoming_conn_noise
            connection.state = motor_incoming_connection_uniselector
            connection.status = True

    
    'The Right Eye is only connected to (receives input from) Right Sensor'
    for connection in rightEye.inputConnections:
        if connection.incomingUnit.name == 'Right Sensor':
            connection.newWeight(motor_incoming_conn_weight)
            connection.noise = motor_incoming_conn_noise
            connection.state = motor_incoming_connection_uniselector
            connection.status = True    
            
    'The Left Eye  is only connected to (receives input from) Left Sensor'
    for connection in leftEye.inputConnections:
        if connection.incomingUnit.name == 'Left Sensor':
            connection.newWeight(motor_incoming_conn_weight)
            connection.noise = motor_incoming_conn_noise
            connection.state = motor_incoming_connection_uniselector
            connection.status = True    

    'Sensors are not connected (does not receive input from) any other unit'
    for connection in leftEyeSensorOnly.inputConnections:
        connection.status = False
    for connection in rightEyeSensorOnly.inputConnections:
        connection.status = False

    hom._usesSocket = True

    'Return the properly configured homeostat'
    return hom



def initializeBraiten2_2_Full_Pos(params=None):    
    '''Utility function to choose a  FULLY Connected Braitenberg type-2 vehicle with
    4 real units and 2 positive connections between actual stimulus and sensory 
    input (the higher the world's value, the higher the stimulus'''
    
    return initializeBraiten2_2_Full(False)

def initializeBraiten2_2_Full_Neg(params=None):    
    '''Utility function to choose a  FULLY Connected Braitenberg type-2 vehicle with
    4 real units and 2 negative connections between actual stimulus and sensory 
    input (the higher the world's value, the higher the stimulus'''
    
    return initializeBraiten2_2_Full(True)

def initializeBraiten2_2Pos(params=None):
    '''Utility function to choose a  Braitenberg type-2 vehicle with
    4 real units and 2 positive connections between actual stimulus and sensory 
    input (the higher the world's value, the higher the stimulus'''
    return initializeBraiten2_2(False)

def initializeBraiten2_2Neg(params=None):
    '''Utility function to choose a  Braitenberg type-2 vehicle with
    4 real units and 2 negative connections between actual stimulus and sensory 
    input (the higher the world's value, the lower the stimulus'''

    return initializeBraiten2_2(True,params=None)

#===============================================================================
# Genetic Algorithms experiments
#===============================================================================
def initializeBraiten2_2_Full_GA(homeoGenome, noHomeoParameters=4, raw=False):
    '''
    Initialization of a Braitenberg-like homeostat for use in GA simulations.
    
    Initialize a Homeostat to replicate a Braitenberg type-2 vehicle with
    4 real units: two for either Motor and two for the sensors, plus 2 HomeoInput Units
    to interface to the outside world.
    
    The homeoGenome parameter contains values in the (-1,1) range for all 6 units plus
    all their connections (for a total of 60 values in the default case), even though only 32 "genes" 
    are used: the essential parameters for the first 4 units (4 * 4) and the connection parameters 
    for the 4 real units (4*4)
    
    The single units' essential values (mass, viscosity, uniselector timing, maxDeviation, etc.) 
    and the weights of *all* the connections are passed to the method in the homeoGenome list.
    
    In general, the length of homeoGenome must be equal to 
    no_units*(no_essent_params + no_units) 
    
    In this experiments no_units = 6, hence the length of homeoGenome is
    6*(no_essent_params + 6)
    
    The array is structured as follows:
    1. 0 to no_units * no_essent_params     (= 0 to 6 * no_essent_params - 1)
       contain the essential parameters of units 1 to 6.
    
    2. (no_units * no_essent_params) - 1 to end of array
       contain the weights of the single units's connections (excepts self connections)
       in strict numerical order. 
       
    The order of the units in the homeoGenome list is 
    1. Left Motor
    2. Right Motor
    3. Left Sensor
    4. Right sensor
    5. Right HomeoInput Unit
    6. Left HomeoInput Unit   
    
    Initialize the homeostat to be **fully connected** (real units only)
    
    The initialization variable 'raw' controls the type of sensory tranducer. 
    If it is set to 'False" (default) the raw sensory input from webot is reversed: high sensory values correspond 
    to high actual stimuli, and viceversa.
    This setting is equivalent to a classic Braitenberg vehicle: a high (e.g.)
    light intensity in the world will translate into a high sensor reading.
     
    If the 'raw' variable is set to True, the sensory transducer reads webots raw values, 
    which are minimum for maximum stimulus and maximal for minimun stimulus.
    This is the **reverse** of the classical Braitenberg case: a high intensity in the world
    will translate into a low sensor value.  
                      
''' 
    if raw == None:
        raw = False
             
    "1. setup webots"
    "PUT THE CORRECT WEBOTS WORLD HERE WITH COMPLETE PATH"  
    webotsWorld = '/home/stefano/Documents/Projects/Homeostat/Simulator/Python-port/Homeo/src/Webots/Homeo-experiments/worlds/khepera-braitenberg-2-HOMEO.wbt'
    webotsMode = "fast"              #for GA experiments, run simulation as fast as possible 

    '''Webots parameters for tcp/ip communication
       (Defined in webots world specified above)
    '''
    
    #kheperaPort = 50000 # test server on port 50000 that just echoes commands back 
    host = 'localhost'
    kheperaPort = 10020
    supervisorPort = 10021
    
    startWebots(world=webotsWorld, mode=webotsMode)
    
    "2. set up homeostat, connect it and create client and socket, etc."
    hom = Homeostat()
    hom._host = host
    hom._port = kheperaPort

    '''Clear the class-based set containing the names of all units
        FIXME: this is a hack that will not work in case of repeated calls to the
        same experimental setup within the same experiment.
        Need to give names with incremental integer values'''
    HomeoUnit.clearNames()
    
       
    '3.1 Setup robotic communication parameters in actuator and sensor'
    'motors'
    rightWheel = WebotsDiffMotorTCP('right')
    leftWheel = WebotsDiffMotorTCP('left')
    #rightWheel.robotSocket = socket
    rightWheel.funcParameters = 10 #wheel speed in rad/s
    #leftWheel.robotSocket = socket
    leftWheel.funcParameters = 10  #wheel speed in rad/s

    
    'sensors'
    if raw == False:
        leftEyeSensorTransd  = WebotsLightSensorTCP(0)
        rightEyeSensorTransd = WebotsLightSensorTCP(1)
    else:
        leftEyeSensorTransd  = WebotsLightSensorRawTCP(0)
        rightEyeSensorTransd = WebotsLightSensorRawTCP(1)

        
    leftEyeSensorTransd._clientPort = kheperaPort
    #leftEyeSensorTransd.robotSocket = socket
    rightEyeSensorTransd._clientPort = kheperaPort
    #rightEyeSensorTransd.robotSocket = socket
    
    '3.2 initialize motors and sensors units with properly setup motors and sensors'        
    leftMotor = HomeoUnitNewtonianActuator(transducer = leftWheel)
    rightMotor = HomeoUnitNewtonianActuator(transducer = rightWheel)
    leftEye = HomeoUnitNewtonian()
    rightEye = HomeoUnitNewtonian()
    leftEyeSensorOnly = HomeoUnitInput(transducer=leftEyeSensorTransd)
    rightEyeSensorOnly = HomeoUnitInput(transducer=rightEyeSensorTransd)
    
    '3.3 initialize units essential parameters according to slices of input list'
    leftMotor.initialize_GA(homeoGenome[0:4])
    rightMotor.initialize_GA(homeoGenome[4:8])
    leftEye.initialize_GA(homeoGenome[8:12])
    rightEye.initialize_GA(homeoGenome[12:16])
                               
        
    '3.4. Setup *non-essential* homeo parameters'
    
    motor_self_noise = 0.05
    sensor_self_noise = 0.05
        
    motor_self_connection_active = 'active'
    motor_self_connection_uniselector = 'manual'
    motor_self_connection_switch = -1
    motor_self_connection_noise = 0.05
    motor_incoming_connection_uniselector = 'uniselector' 
    sensor_incoming_connection_uniselector = 'manual'
    
    "4. Set up Homeostat"   
    
    'Setup a 4 unit Homeostat with 2 additional input units. Then change the parameters'
    if len(hom.homeoUnits) == 0 :                 # check if the homeostat is set up already"
            hom.addFullyConnectedUnit(leftMotor)
            hom.addFullyConnectedUnit(rightMotor)
            hom.addFullyConnectedUnit(leftEye)
            hom.addFullyConnectedUnit(rightEye)
            hom.addFullyConnectedUnit(leftEyeSensorOnly)
            hom.addFullyConnectedUnit(rightEyeSensorOnly)
    else:
        raise(HomeostatError, "Homeostat is not empty")


     
    #===========================================================================
    # 'Disable all connections except self-connections'
    # for unit in hom.homeoUnits:
    #     for i in xrange(1, len(hom.homeoUnits)):
    #         unit.inputConnections[i].status = False
    #===========================================================================

    '4.1 Agent units or motors parameters setting'
    leftMotor.name = 'Left Motor'
    leftMotor.noise = motor_self_noise

    rightMotor.name = 'Right Motor'
    rightMotor.noise = motor_self_noise
    
    'self-connection'
    leftMotor.inputConnections[0].noise = motor_self_connection_noise
    leftMotor.inputConnections[0].state = motor_self_connection_uniselector

    rightMotor.inputConnections[0].noise = motor_self_connection_noise
    rightMotor.inputConnections[0].state = motor_self_connection_uniselector

    '4.2 Sensor units parameters setting'
    leftEye.name = 'Left Eye'
    leftEye.noise = sensor_self_noise

    rightEye.name = 'Right Eye'
    rightEye.noise = sensor_self_noise

    'Activate uniselector'
    leftEye.uniselectorActive = True
    rightEye.uniselectorActive = True
    
    'Activate self-connection'
    leftEye.inputConnections[0].status = True
    rightEye.uniselectorActive = True

    '4.3 SensorOnly units parameters setting'
    leftEyeSensorOnly.name = 'Left Sensor'
    leftEyeSensorOnly.noise = sensor_self_noise

    rightEyeSensorOnly.name = 'Right Sensor'
    rightEyeSensorOnly.noise = sensor_self_noise

    'disactivate uniselector'
    leftEyeSensorOnly.uniselectorActive = False
    rightEyeSensorOnly.uniselectorActive = False
    
    'disactivate self-connection'
    leftEyeSensorOnly.inputConnections[0].status = False
    rightEyeSensorOnly.inputConnections[0].status = False


    '''Set up homeostat's initial connections,
       according to input list.'''
    "Left motor's connections are contained in the input list at positions 24:29"
    incoming_conn_noise = 0.05           # General constraint
    
    offset = 24
    for connection in leftMotor.inputConnections:
        connection.newWeightGA(homeoGenome[offset])
        connection.noise = incoming_conn_noise
        connection.state = motor_incoming_connection_uniselector
        connection.status = True
        offset += 1

    "Right motor's connections are contained in the input list at positions 30:35"
    for connection in rightMotor.inputConnections:
        connection.newWeightGA(homeoGenome[offset])
        connection.noise = incoming_conn_noise
        connection.state = motor_incoming_connection_uniselector
        connection.status = True
        offset += 1
    
    "Left eye's connections are contained in the input list at positions 36:41"
    for connection in leftEye.inputConnections:
        connection.newWeightGA(homeoGenome[offset])
        connection.noise = incoming_conn_noise
        connection.state = motor_incoming_connection_uniselector
        connection.status = True    
        offset += 1

    "Right eye's connections are contained in the input list at positions 42:47"
    for connection in rightEye.inputConnections:
        connection.newWeightGA(homeoGenome[offset])
        connection.noise = incoming_conn_noise
        connection.state = motor_incoming_connection_uniselector
        connection.status = True    
        offset += 1
            
    'Sensors are not connected (do not receive input from) any other unit'
    for connection in leftEyeSensorOnly.inputConnections:
        connection.status = False
    for connection in rightEyeSensorOnly.inputConnections:
        connection.status = False
        
    #===========================================================================
    # Debugging code to isolate the tcp/ip problem
    # Removing the light sensors (input units)  
    #===========================================================================
    #hom.removeUnit(leftEyeSensorOnly)
    #hom.removeUnit(rightEyeSensorOnly)
        
    #===========================================================================
    # End of debugging code
    #===========================================================================
        
#===============================================================================
#     #===========================================================================
#     # Debugging 
#     #===========================================================================
#     from tabulate import tabulate
#     #===========================================================================
#     # for i in xrange(homeoGenome.size):
#     #     print "param %d  is:\t%f" % (i,homeoGenome[i])
#     #===========================================================================
#     " Checking HomeoUnits values"
#     homUnitsData = []
#     k = 0
#     for i in hom.homeoUnits:
#         singleUnitdata = []
#         singleUnitdata.append(k)
#         singleUnitdata.append(i.name)
#         singleUnitdata.append(homeoGenome[0+k])
#         singleUnitdata.append(i.mass)
#         singleUnitdata.append(homeoGenome[1+k])
#         singleUnitdata.append(i.viscosity)
#         singleUnitdata.append(homeoGenome[2+k])
#         singleUnitdata.append(i.uniselectorTimeInterval)
#         singleUnitdata.append(homeoGenome[3+k])
#         singleUnitdata.append(i.maxDeviation)
#         homUnitsData.append(singleUnitdata)        
#         k += 4
#     headers = ["k","Unit", "mass-param",  "mass", "Visc-param", "Visc.","Unisel-time-param", "Unisel-timing", "maxDev-param", "maxDev"]      
#     print tabulate(homUnitsData,headers,tablefmt='orgtbl')
#     print
#     print
#               
#     "Checking connections"                                                                                                                                                 
#     homConnectionsData = []
#     k = 0
#     offset = 24
#     for unit in hom.homeoUnits:
#         for conn in unit.inputConnections:
#             unitConnData = []
#             unitConnData.append(offset)
#             unitConnData.append(unit.name)
#             unitConnData.append(conn.incomingUnit.name)
#             unitConnData.append(homeoGenome[offset])
#             unitConnData.append(conn.weight)
#             unitConnData.append(abs((2*homeoGenome[offset])-1))
#             unitConnData.append(conn.weight-(abs((2*homeoGenome[offset])-1)))
#             unitConnData.append(conn.switch)            
#             unitConnData.append(np.sign(((2*homeoGenome[offset])-1)))
#             unitConnData.append(conn.switch - (np.sign(((2*homeoGenome[offset])-1))))
#             unitConnData.append(conn.status)
#             offset += 1
#             homConnectionsData.append(unitConnData)
# 
#     headers = ["Genome offset","To unit", "From unit", "weight param", "weight", "weight comp.", "weight delta", "switch", "switch comp.", "switch delta", "status"]
#     print tabulate(homConnectionsData, headers, tablefmt='orgtbl')                
#     #===========================================================================
#     # End debugging
#     #===========================================================================
#===============================================================================
    
    hom._usesSocket = True
    hom.connectUnitsToNetwork()

    'Return the properly configured homeostat'
    hDebug('unit', "Homeostat initialized")
    return hom

def initializeBraiten2_2_NoUnisel_Full_GA(genome, homeoParameters=4, raw=False):
    '''
    Initialize a homeostat according to initializeBraiten2_2_Full_GA, then turn 
    off all uniselectors.
    ***No Uniselectors active***
    
    See initializeBraiten2_2_Full_GA for details on initialization procedure.'''
    
    hom = initializeBraiten2_2_Full_GA(homeoGenome=genome, noHomeoParameters=homeoParameters, raw=False)
    for unit in hom.homeoUnits:
        unit.uniselectorActive = False
    return hom


#===============================================================================
# Utility functions
#===============================================================================

def isWebotsRunning():
    'Check if Webots is running'
    webots_running = False
    if 'webots-bin' in check_output(['ps','ax']):
            webots_running = True
    return webots_running
   
def startWebots(world = None, mode = "realtime"):
    """
    Start a webots instance with the given world and at the specified speed (mode).
    Mode can be one of realtime, run, or fast 
    """
    if not isWebotsRunning():
        hDebug('network',("Is webots-running: " + str(isWebotsRunning())))
        callString = "/usr/local/webots/webots " +"--mode="+ mode+ " " +world + " &"
        hDebug('network',callString)
        system(callString)
        'Wait for webots to start listening to commands (in seconds)'
        sleep(2)         
