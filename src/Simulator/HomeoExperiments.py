# Copyright (C) 2013-2026 Stefano Franchi
#
# This file is part of Homeo, a simulation of Ashby's homeostat and of
# homeostat-controlled robots.
#
# Homeo is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# Homeo is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with Homeo.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from Core.Homeostat import *
from Core.HomeoUnitNewtonian import *
from Core.HomeoConnection import * 
from RobotSimulator.HomeoUnitNewtonianTransduc import *
from RobotSimulator.Transducer import  *
from Helpers.ExceptionAndDebugClasses import hDebug
from Helpers.GenomeDecoder import genomePrettyPrinter, genomeDecoder
from Helpers.General_Helper_Functions import dated_data_dir
from KheperaSimulator.KheperaSimulator import KheperaSimulation
import os

'''
Module HomeoExperiments provides initializations data for various experiments to be conducted with the homeo package.
The module's methods return a properly configured homeostat to be used in the simulations.
The functions setting up robotics experiments build their vehicle on a robotic simulator
backend (Simulator/SimulatorBackend.py).
'''

def initialize10UnitHomeostat(params=None):
    "Returns a homeostat with 10 units. Used for testing UI"
    hom = Homeostat()
    for i in range(10):
        unit = HomeoUnitNewtonian()
        unit.setRandomValues()
        hom.addFullyConnectedUnit(unit)
    return hom
    
def initializeAshbySimulation(**params):
    '''Returns a Homeostat with
       four fully connected units with random values to the simulator
       (as per Ashby basic design)'''
    hom = Homeostat()
    for i in range(4):
        unit = HomeoUnitNewtonian()
        unit.setRandomValues()
        hom.addFullyConnectedUnit(unit)

    'Return the properly configured homeostat'
    return hom

def initializeAshbyNoNoiseSimulation(**params):
    '''Returns a Homeostat with
       four fully connected units with random values to the simulator
       (as per Ashby basic design)
       Set all noises values to 0 for testing purposes'''
    hom = Homeostat()
    for i in range(4):
        unit = HomeoUnitNewtonian()
        unit.setRandomValues()
        hom.addFullyConnectedUnit(unit)
    for unit in hom.homeoUnits:
        unit.noise = 0
        for conn in unit.inputConnections:
            conn.noise = 0

    'Return the properly configured homeostat'
    return hom



def initialize_1minus_2xExperiment(params=None):
    '''
    Initialize a standard Homeostat to have 2 2-units 1-, 2x standard settings for 1- 2x experiment (Agent-Environment)
    with fixed parameters to improve repeated runs
    '''
    hom = Homeostat()
    # Its units' names are fixed: release the names of a homeostat built
    # before, as the other setups do, or a second call (the GUI's New) raises
    # 'The name H1_Agent exists already'
    HomeoUnit.clearNames()
    
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
        for i in range(4):
            unit = HomeoUnitNewtonian()
            unit.setRandomValues()
            hom.addFullyConnectedUnit(unit)
        
    'disable all connections except self-connections'
    for unit in hom.homeoUnits:
        for i in range(1, len(hom.homeoUnits)):
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
    homeo1_unit2x.mass = env_mass
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
    homeo2_unit2x.mass = env_mass
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
            connection.newWeight(env_incoming_connection_weight * env_incoming_connection_polarity)
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
    HomeoUnit.clearNames()          # fixed names: see initialize_1minus_2xExperiment
    
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
        for i in range(4):
            unit = HomeoUnitNewtonian()
            unit.setRandomValues()
            hom.addFullyConnectedUnit(unit)

    'disable all connections except self-connections'
    for unit in hom.homeoUnits:
        for i in range(1, len(hom.homeoUnits)):
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
    homeo1_unit3x.mass = env_mass
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

def initializeBraiten2_2(raw=False,params=None, backendSimulator = None, dataDir = None):
    '''
    Initialize a Homeostat to replicate a Braitenberg type-2 vehicle with
    4 real units: two for either Motor and two for the sensors, plus 2  HomeoInput Units
    to interface to the outside world, on the robot of backendSimulator (a
    SimulatorBackend instance, e.g. SimulatorBackendHOMEO).

    raw=True asks for inverted readings (high for a weak stimulus); the
    backends have only the standard polarity, so it raises a ValueError.

    Every active link between units is under the uniselector, the sensor ->
    eye links included: as in every adaptive vehicle (and Ashby's homeostat),
    only the self-connections are manual.
'''
    if backendSimulator is None:
        raise ValueError("initializeBraiten2_2 needs a backendSimulator")
    if raw:
        # The backends' sensors have no raw (inverted) reading
        raise ValueError("initializeBraiten2_2: raw=True is not supported with a "
                         "backendSimulator; its sensors have only the standard polarity")
    worlds = {'HOMEO': 'kheperaBraitenberg2_HOMEO_World',
              'WEBOTS': 'kheperaBraitenberg2_HOMEO_World'}     # its Webots twin
    try:
        world = worlds[backendSimulator.name]
    except KeyError:
        raise Exception("I cannot use backend simulator %s yet" % backendSimulator.name)
    """The backend's transducers: a dictionary with rightWheelTransd,
    leftWheelTransd, rightEyeTransd, leftEyeTransd"""
    transducers = basicBraiten2Tranducers(backendSimulator, world)

    "2. set up homeostat"
    hom = Homeostat()

    '''Clear the class-based set containing the names of all units
        FIXME: this is a hack that will not work in case of repeated calls to the
        same experimental setup within the same experiment.
        Need to give names with incremental integer values'''
    HomeoUnit.clearNames()
    
       
    '3.1 Setup robotic communication parameters in actuator and sensor'
    'motors'
    rightWheel = transducers["rightWheelTransd"]
    leftWheel = transducers["leftWheelTransd"]
    
    'sensors'
    leftEyeSensorTransd = transducers["leftEyeTransd"]
    rightEyeSensorTransd = transducers["rightEyeTransd"]
    

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
    
    "4. Set up Homeostat"   

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
        for i in range(1, len(hom.homeoUnits)):
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
    rightEye.inputConnections[0].status = True

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

    'Return the properly configured homeostat'
    hDebug('unit', "Homeostat initialized")
    return hom

def initializeBraiten2_2Pos(params=None, backendSimulator = None, dataDir = None):
    '''Utility function to choose a  Braitenberg type-2 vehicle with
    4 real units and 2 positive connections between actual stimulus and sensory
    input (the higher the world's value, the higher the stimulus'''
    return initializeBraiten2_2(False, backendSimulator = backendSimulator, dataDir = dataDir)

#===============================================================================
# Genetic Algorithms experiments
#===============================================================================
def initializeBraiten2_2_Full_GA(homeoGenome, noHomeoParameters=4, backendSimulator = None, dataDir = None, noNoise = False, noUnisel = False):
    '''
    Initialization of a Braitenberg-like homeostat for use in GA simulations.
    
    Initialize a Homeostat to replicate a Braitenberg type-2 vehicle with
    4 real units: two for either Motor and two for the sensors, plus 2 HomeoInput Units
    to interface to the outside world.
    
    The homeoGenome parameter contains values in the (0,1) range for the 4 evolved
    units (motors and eyes) and their connections. The 2 sensor-only HomeoUnitInput
    units have no genes — their parameters are fixed.

    genomeSize = noEvolvedUnits * noHomeoParameters + noEvolvedUnits * noTotalUnits
               = 4 * 4 + 4 * 6 = 40

    The array is structured as follows:
    1. Indices 0 to noEvolvedUnits * noHomeoParameters - 1 (= 0 to 15)
       contain the essential parameters of the 4 evolved units.

    2. Indices noEvolvedUnits * noHomeoParameters to end (= 16 to 39)
       contain the connection weights for the 4 evolved units
       (6 connections each, one per unit in the fully-connected homeostat).

    The order of the evolved units in the genome is:
    1. Left Motor
    2. Right Motor
    3. Left Sensor (eye)
    4. Right Sensor (eye)   

    The genome sets every link's starting weight; every link but the
    self-connections is then under the uniselector, the sensor -> eye links
    included, as in every adaptive vehicle.
    
    Initialize the homeostat to be **fully connected** (real units only)
    
    The backendSimulator variable determines how to initialize the transducer units, depending 
    on the robotic simulator backend. 
                      
''' 
    """Get the simulator-specific transducer units
       The basicBraiten2 functions return a dictionary with 4 transducers: 
       rightWheelTransd, leftWheelTransd, rightEyeTransd, leftEyeTransd"""
    world = _backendWorld(backendSimulator, 'kheperaBraitenberg2_HOMEO_World')

    transducers = basicBraiten2Tranducers(backendSimulator, world) 

        
    if transducers is None:
        raise Exception("Could not build transducers for simulator backend ", backendSimulator.name)
    
    "2. set up homeostat"
    hom = Homeostat()

    '''Clear the class-based set containing the names of all units
        FIXME: this is a hack that will not work in case of repeated calls to the
        same experimental setup within the same experiment.
        Need to give names with incremental integer values'''
    HomeoUnit.clearNames()
    
       
    '3.1 Setup robotic communication parameters in actuator and sensor'
    'motors'
    rightWheel = transducers["rightWheelTransd"]
    leftWheel = transducers["leftWheelTransd"]
    
    'sensors'
    leftEyeSensorTransd = transducers["leftEyeTransd"]
    rightEyeSensorTransd = transducers["rightEyeTransd"]
    
    '3.2 initialize motors and sensors units with properly setup motors and sensors'        
    leftMotor = HomeoUnitNewtonianActuator(transducer = leftWheel)
    rightMotor = HomeoUnitNewtonianActuator(transducer = rightWheel)
    leftEye = HomeoUnitNewtonian()
    rightEye = HomeoUnitNewtonian()
    leftEyeSensorOnly = HomeoUnitInput(transducer=leftEyeSensorTransd)
    rightEyeSensorOnly = HomeoUnitInput(transducer=rightEyeSensorTransd)
    
    '3.3 initialize units essential parameters according to slices of input list'
    # Sliced by noHomeoParameters, as the connection genes' offset is below:
    # initialize_GA raises unless it is the units' number of parameters
    n = noHomeoParameters
    leftMotor.initialize_GA(homeoGenome[0:n])
    rightMotor.initialize_GA(homeoGenome[n:2 * n])
    leftEye.initialize_GA(homeoGenome[2 * n:3 * n])
    rightEye.initialize_GA(homeoGenome[3 * n:4 * n])
                               
        
    '3.4. Setup *non-essential* homeo parameters'
    
    'Set noise to 0 if so desired)'
    if noNoise == True:
        motor_self_noise = 0
        sensor_self_noise = 0
    else:
        motor_self_noise = 0.05
        sensor_self_noise = 0.05
        
    motor_self_connection_active = 'active'
    motor_self_connection_uniselector = 'manual'
    motor_self_connection_switch = -1
    motor_self_connection_noise = 0.05
    motor_incoming_connection_uniselector = 'uniselector' 
    
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
    #     for i in range(1, len(hom.homeoUnits)):
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
    rightEye.inputConnections[0].status = True

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

    if noNoise == True:
        incoming_conn_noise = 0.0
    else:
        incoming_conn_noise = 0.05           # General constraint

    offset = initializeBraiten2_2_Full_GA.noEvolvedUnits * noHomeoParameters
    for connection in leftMotor.inputConnections:
        connection.newWeightGA(homeoGenome[offset])
        connection.noise = incoming_conn_noise
        connection.state = motor_incoming_connection_uniselector
        connection.status = True
        offset += 1

    "Right motor's connections"
    for connection in rightMotor.inputConnections:
        connection.newWeightGA(homeoGenome[offset])
        connection.noise = incoming_conn_noise
        connection.state = motor_incoming_connection_uniselector
        connection.status = True
        offset += 1
    
    "Left eye's connections"
    for connection in leftEye.inputConnections:
        connection.newWeightGA(homeoGenome[offset])
        connection.noise = incoming_conn_noise
        connection.state = motor_incoming_connection_uniselector
        connection.status = True    
        offset += 1

    "Right eye's connections"
    for connection in rightEye.inputConnections:
        connection.newWeightGA(homeoGenome[offset])
        connection.noise = incoming_conn_noise
        connection.state = motor_incoming_connection_uniselector
        connection.status = True    
        offset += 1

    '''Self-connections stay manual: the genome sets them, the uniselector
       leaves them alone, as in the weight-free setups.'''
    for unit in (leftMotor, rightMotor, leftEye, rightEye):
        unit.inputConnections[0].state = motor_self_connection_uniselector
            
    'Sensors are not connected (do not receive input from) any other unit'
    for connection in leftEyeSensorOnly.inputConnections:
        connection.status = False
    for connection in rightEyeSensorOnly.inputConnections:
        connection.status = False

    if noUnisel == True:
        for unit in hom.homeoUnits:
            unit.uniselectorActive = False


    'Return the properly configured homeostat'
    hDebug('unit', "Homeostat initialized")
    return hom

initializeBraiten2_2_Full_GA.noEvolvedUnits = 4
initializeBraiten2_2_Full_GA.fitnessSign = 1


# The GA phototaxis setups' TARGET: a light of intensity +100, the world's
# default and the phototaxis CLIs' (whose --dark gives -100).  Each setup
# takes lightIntensity (-100: a darkness source), and GA logbooks record it
# (see loggedLightIntensity).
GA_LIGHT_INTENSITY = 100


def setTargetIntensity(backendSimulator, intensity):
    "Set the intensity of the TARGET of backendSimulator's world"
    if backendSimulator is not None:
        target = backendSimulator.kheperaSimulation.allBodies['TARGET']
        target.userData['intensity'] = intensity
        target.userData['lightIntensity'] = intensity


def loggedLightIntensity(experimentName, logbookMeta):
    """The TARGET intensity a GA run evaluated its genomes with, as its
       logbook records it; ValueError if the logbook records none."""
    meta = logbookMeta or {}
    if meta.get('lightIntensity') is None:
        raise ValueError('the logbook of %s records no light intensity' % experimentName)
    return meta['lightIntensity']


def initializeBraiten2_2_Full_GA_phototaxis(homeoGenome, noHomeoParameters=4,
        backendSimulator=None, dataDir=None, noNoise=False, noUnisel=False,
        lightIntensity=GA_LIGHT_INTENSITY):
    '''Phototaxis GA experiment: the robot seeks the light source, the
    TARGET, of intensity lightIntensity (+100, see GA_LIGHT_INTENSITY).
    Fitness = distance (minimised).'''
    hom = initializeBraiten2_2_Full_GA(
        homeoGenome=homeoGenome, noHomeoParameters=noHomeoParameters,
        backendSimulator=backendSimulator, dataDir=dataDir,
        noNoise=noNoise, noUnisel=noUnisel)
    setTargetIntensity(backendSimulator, lightIntensity)
    return hom

initializeBraiten2_2_Full_GA_phototaxis.noEvolvedUnits = 4
initializeBraiten2_2_Full_GA_phototaxis.fitnessSign = 1  # minimise distance


def initializeBraiten2_2_Full_GA_scototaxis(homeoGenome, noHomeoParameters=4,
        backendSimulator=None, dataDir=None, noNoise=False, noUnisel=False):
    '''Scototaxis GA experiment (positive light intensity, default).
    The robot avoids the light source. Fitness = -distance (minimised).'''
    hom = initializeBraiten2_2_Full_GA(
        homeoGenome=homeoGenome, noHomeoParameters=noHomeoParameters,
        backendSimulator=backendSimulator, dataDir=dataDir,
        noNoise=noNoise, noUnisel=noUnisel)
    # Light intensity is already positive (100) by default
    return hom

initializeBraiten2_2_Full_GA_scototaxis.noEvolvedUnits = 4
initializeBraiten2_2_Full_GA_scototaxis.fitnessSign = -1  # negate: minimising = maximising distance


def initializeBraiten2_2_Full_GA_phototaxis_continuous(homeoGenome, noHomeoParameters=4,
        backendSimulator=None, dataDir=None, noNoise=False, noUnisel=False,
        lightIntensity=GA_LIGHT_INTENSITY):
    '''Phototaxis GA experiment with continuous (Ornstein-Uhlenbeck) uniselectors.

    Same as phototaxis (the robot seeks the light source, of intensity
    lightIntensity; fitness = distance minimised) but replaces the discrete Ashby stepping switch
    with a continuous stochastic weight drift on all evolved units.

    The genome structure is identical to the standard phototaxis experiment
    (40 genes: 4x4 unit params + 4x6 connection weights).  The uniselector_timing
    gene (gene index 2 within each unit's 4-gene block) still sets
    uniselectorTimeInterval on the unit, but it is ignored by the continuous
    uniselector — the timescale separation is handled by tau_a instead.

    Continuous uniselector parameters use defaults from
    HomeoUniselectorContinuous.DefaultParameters.
    '''
    from Core.HomeoUniselectorContinuous import HomeoUniselectorContinuous

    hom = initializeBraiten2_2_Full_GA(
        homeoGenome=homeoGenome, noHomeoParameters=noHomeoParameters,
        backendSimulator=backendSimulator, dataDir=dataDir,
        noNoise=noNoise, noUnisel=noUnisel)

    setTargetIntensity(backendSimulator, lightIntensity)

    # Replace discrete uniselectors with continuous ones on evolved units
    if not noUnisel:
        for unit in hom.homeoUnits:
            if unit.uniselectorActive:
                unit.uniselector = HomeoUniselectorContinuous()

    return hom

initializeBraiten2_2_Full_GA_phototaxis_continuous.noEvolvedUnits = 4
initializeBraiten2_2_Full_GA_phototaxis_continuous.fitnessSign = 1  # minimise distance


# The genome layout of the weight-free setups, 'weightfree_v2': 4 genes per
# evolved unit, [mass, viscosity, tau_a, maxDeviation]; mass and viscosity
# log-uniform (HomeoUnit.massFromGeneLog, viscosityFromGeneLog), dt_fast 1.
# (GenomeDecoder also reads logbooks recorded with other layouts.)
WEIGHTFREE_GENES_PER_UNIT = {'weightfree_v2': 4}


def _decodeWeightfreeUnits(units, homeoGenome, layout):
    "Set the evolved units' mass, viscosity and maxDeviation from the genome"
    perUnit = WEIGHTFREE_GENES_PER_UNIT[layout]
    for i, unit in enumerate(units):
        genes = homeoGenome[i * perUnit:(i + 1) * perUnit]
        unit.mass = HomeoUnit.massFromGeneLog(genes[0])
        unit.viscosity = HomeoUnit.viscosityFromGeneLog(genes[1])
        # gene 2 = tau_a (applied after the uniselector swap)
        unit.maxDeviation = HomeoUnit.maxDeviationFromWeight(genes[3])


def _setup_continuous_weightfree_homeostat(homeoGenome, backendSimulator,
                                           dataDir=None, noNoise=False, noUnisel=False,
                                           topology='random',
                                           layout='weightfree_v2', eyes=True,
                                           lightIntensity=GA_LIGHT_INTENSITY):
    '''Shared helper for the weight-free continuous-uniselector GA experiments on a
    Braitenberg type-2 vehicle: with eyes (6 units: 2 motors, 2 eyes, 2
    sensor inputs; the _Full_GA_continuous_weightfree setups) or without
    (eyes=False: the 2+2 direct vehicle, the sensors feeding the motors; the
    _direct_GA_ setups).  The evolved units are the motors and, with eyes,
    the eyes.

    Genome: the genes of each evolved unit, in the layout given (see
    WEIGHTFREE_GENES_PER_UNIT): 'weightfree_v2', 4 genes per unit (16 with
    eyes, 8 without), [mass, viscosity, tau_a, maxDeviation].

    Connection weights are NOT in the genome — they are initialised to small
    random values and evolved online by the continuous uniselector.  Without eyes the
    motors' self-connections are always negative (guaranteed stability per
    2-unit homeostat analysis); with eyes they are drawn from [-0.1, 0.1).

    Parameters
    ----------
    homeoGenome : array-like
        values in [0, 1), genes as above.
    backendSimulator : simulator backend
        The robotic simulator backend (SimulatorBackendHOMEO).
    dataDir : str, optional
        Data output directory.
    noNoise : bool
        If True, set all noise to 0.
    noUnisel : bool
        If True, the evolved units' uniselectors are inactive: the weights
        stay at their initial values.
    topology : str
        'random' — all connections on the evolved units are active.
        'fixed'  — only Braitenberg cross-wired connections are active:
                    with eyes Left Eye -> Right Motor, Right Eye -> Left Motor,
                    Left Sensor -> Left Eye, Right Sensor -> Right Eye;
                    without, Left Sensor -> Right Motor, Right Sensor -> Left Motor.
    eyes : bool
        Whether the vehicle has the two eye units between sensors and motors.
    '''
    from Core.HomeoUniselectorContinuous import HomeoUniselectorContinuous

    world = _backendWorld(backendSimulator, 'kheperaBraitenberg2_HOMEO_World')

    transducers = basicBraiten2Tranducers(backendSimulator, world)
    if transducers is None:
        raise Exception("Could not build transducers for simulator backend ", backendSimulator.name)

    "1. Create homeostat and units"
    hom = Homeostat()
    HomeoUnit.clearNames()

    rightWheel = transducers["rightWheelTransd"]
    leftWheel = transducers["leftWheelTransd"]
    leftEyeSensorTransd = transducers["leftEyeTransd"]
    rightEyeSensorTransd = transducers["rightEyeTransd"]

    leftMotor = HomeoUnitNewtonianActuator(transducer=leftWheel)
    rightMotor = HomeoUnitNewtonianActuator(transducer=rightWheel)
    if eyes:
        leftEye = HomeoUnitNewtonian()
        rightEye = HomeoUnitNewtonian()
    leftEyeSensorOnly = HomeoUnitInput(transducer=leftEyeSensorTransd)
    rightEyeSensorOnly = HomeoUnitInput(transducer=rightEyeSensorTransd)

    "2. Decode genome"
    genes_per_unit = WEIGHTFREE_GENES_PER_UNIT[layout]
    evolved_units = [leftMotor, rightMotor] + ([leftEye, rightEye] if eyes else [])
    _decodeWeightfreeUnits(evolved_units, homeoGenome, layout)

    "3. Build fully-connected homeostat"
    hom.addFullyConnectedUnit(leftMotor)
    hom.addFullyConnectedUnit(rightMotor)
    if eyes:
        hom.addFullyConnectedUnit(leftEye)
        hom.addFullyConnectedUnit(rightEye)
    hom.addFullyConnectedUnit(leftEyeSensorOnly)
    hom.addFullyConnectedUnit(rightEyeSensorOnly)

    "4. Name units and set noise"
    if noNoise:
        unit_noise = 0
        conn_noise = 0.0
    else:
        unit_noise = 0.05
        conn_noise = 0.05

    leftMotor.name = 'Left Motor'
    leftMotor.noise = unit_noise
    leftMotor._maxSpeedFraction = 0.8
    leftMotor._switchingRate = 0.5
    leftMotor._maxSpeed = None              # force recalculation from new fraction
    rightMotor.name = 'Right Motor'
    rightMotor.noise = unit_noise
    rightMotor._maxSpeedFraction = 0.8
    rightMotor._switchingRate = 0.5
    rightMotor._maxSpeed = None
    if eyes:
        leftEye.name = 'Left Eye'
        leftEye.noise = unit_noise
        rightEye.name = 'Right Eye'
        rightEye.noise = unit_noise
    leftEyeSensorOnly.name = 'Left Sensor'
    leftEyeSensorOnly.noise = unit_noise
    rightEyeSensorOnly.name = 'Right Sensor'
    rightEyeSensorOnly.noise = unit_noise

    "5. Disable sensor-only units (pure input transducers)"
    leftEyeSensorOnly.uniselectorActive = False
    rightEyeSensorOnly.uniselectorActive = False
    for conn in leftEyeSensorOnly.inputConnections:
        conn.status = False
    for conn in rightEyeSensorOnly.inputConnections:
        conn.status = False

    "6. Configure connections on evolved units according to topology"
    for unit in evolved_units:
        "Self-connection: active, manual (protected from uniselector);"
        "without eyes negative"
        unit.inputConnections[0].newWeight(np.random.uniform(-0.1, 0.1) if eyes
                                           else -np.random.uniform(0.01, 0.1))
        unit.inputConnections[0].noise = conn_noise
        unit.inputConnections[0].state = 'manual'
        unit.inputConnections[0].status = True

    if topology == 'fixed':
        "Braitenberg cross-wiring: disable all non-self connections first"
        for unit in evolved_units:
            for conn in unit.inputConnections[1:]:
                conn.status = False

        "Then activate only the cross-wired paths"
        cross_wiring = {
            'Left Motor': 'Right Eye',
            'Right Motor': 'Left Eye',
            'Left Eye': 'Left Sensor',
            'Right Eye': 'Right Sensor',
        } if eyes else {
            'Left Motor': 'Right Sensor',
            'Right Motor': 'Left Sensor',
        }
        for unit in evolved_units:
            source_name = cross_wiring[unit.name]
            for conn in unit.inputConnections:
                if conn.incomingUnit.name == source_name:
                    conn.newWeight(np.random.uniform(-0.1, 0.1))
                    conn.noise = conn_noise
                    conn.state = 'uniselector'
                    conn.status = True
    else:
        "Random topology: all connections between evolved units are active"
        for unit in evolved_units:
            for conn in unit.inputConnections[1:]:
                conn.newWeight(np.random.uniform(-0.1, 0.1))
                conn.noise = conn_noise
                conn.state = 'uniselector'
                conn.status = True

    "7. Swap uniselectors to continuous ones and set tau_a from genome"
    for i, unit in enumerate(evolved_units):
        # noUnisel: the continuous uniselector stays installed (it records tau_a) but
        # never runs, so the weights keep their initial values
        unit.uniselectorActive = not noUnisel
        unis = HomeoUniselectorContinuous()
        unis.tau_a = HomeoUnit.tauAFromWeight(homeoGenome[i * genes_per_unit + 2])
        unit.uniselector = unis

    "8. The light the robot seeks (see GA_LIGHT_INTENSITY)"
    setTargetIntensity(backendSimulator, lightIntensity)


    hDebug('unit', "Homeostat initialized (%s, weight-free continuous, topology=%s)"
           % ('with eyes' if eyes else 'direct 2+2', topology))
    return hom


def initializeBraiten2_2_Full_GA_continuous_weightfree_v2(homeoGenome, noHomeoParameters=4,
        backendSimulator=None, dataDir=None, noNoise=False, noUnisel=False,
        lightIntensity=GA_LIGHT_INTENSITY):
    '''Weight-free phototaxis GA experiment with continuous uniselectors
    on the vehicle with eyes; all connections between evolved units active.

    Genome: 16 genes = 4 units x 4 params [mass, viscosity, tau_a, maxDeviation],
    layout 'weightfree_v2': mass and viscosity log-uniform in [0.25, 250] and
    [0.05, 50] (HomeoUnit.massFromGeneLog, viscosityFromGeneLog); dt_fast 1.
    '''
    return _setup_continuous_weightfree_homeostat(
        homeoGenome, backendSimulator, dataDir=dataDir,
        noNoise=noNoise, noUnisel=noUnisel, topology='random', layout='weightfree_v2',
        lightIntensity=lightIntensity)

initializeBraiten2_2_Full_GA_continuous_weightfree_v2.noEvolvedUnits = 4
initializeBraiten2_2_Full_GA_continuous_weightfree_v2.fitnessSign = 1
initializeBraiten2_2_Full_GA_continuous_weightfree_v2.genomeSize = 16
initializeBraiten2_2_Full_GA_continuous_weightfree_v2.genomeLayout = 'weightfree_v2'


def initializeBraiten2_2_Full_GA_continuous_weightfree_fixed_v2(homeoGenome, noHomeoParameters=4,
        backendSimulator=None, dataDir=None, noNoise=False, noUnisel=False,
        lightIntensity=GA_LIGHT_INTENSITY):
    '''Weight-free phototaxis GA experiment with continuous uniselectors
    on the vehicle with eyes; fixed Braitenberg cross-wiring.

    Genome: 16 genes = 4 units x 4 params [mass, viscosity, tau_a, maxDeviation],
    layout 'weightfree_v2': mass and viscosity log-uniform in [0.25, 250] and
    [0.05, 50] (HomeoUnit.massFromGeneLog, viscosityFromGeneLog); dt_fast 1.
    '''
    return _setup_continuous_weightfree_homeostat(
        homeoGenome, backendSimulator, dataDir=dataDir,
        noNoise=noNoise, noUnisel=noUnisel, topology='fixed', layout='weightfree_v2',
        lightIntensity=lightIntensity)

initializeBraiten2_2_Full_GA_continuous_weightfree_fixed_v2.noEvolvedUnits = 4
initializeBraiten2_2_Full_GA_continuous_weightfree_fixed_v2.fitnessSign = 1
initializeBraiten2_2_Full_GA_continuous_weightfree_fixed_v2.genomeSize = 16
initializeBraiten2_2_Full_GA_continuous_weightfree_fixed_v2.genomeLayout = 'weightfree_v2'


# ===============================================================
#  Simplified 2+2 vehicle (no eye intermediaries) — GA init funcs
#
#  2 HomeoUnitInput (sensors) + 2 HomeoUnitNewtonianActuator (motors).
#  Sensors connect directly to contra-lateral motors (Braitenberg
#  cross-wiring).  Motor self-connections are always negative.
# ===============================================================

def _setup_continuous_weightfree_homeostat_direct(homeoGenome, backendSimulator,
                                                  dataDir=None, noNoise=False, noUnisel=False,
                                                  topology='fixed',
                                                  layout='weightfree_v2',
                                                  lightIntensity=GA_LIGHT_INTENSITY):
    '''The weight-free continuous-uniselector helper for the simplified 2+2 vehicle
    (no eye intermediaries): _setup_continuous_weightfree_homeostat with
    eyes=False.'''
    return _setup_continuous_weightfree_homeostat(homeoGenome, backendSimulator,
                                                  dataDir=dataDir, noNoise=noNoise,
                                                  noUnisel=noUnisel, topology=topology,
                                                  layout=layout, eyes=False,
                                                  lightIntensity=lightIntensity)


def initializeBraiten2_direct_GA_continuous_weightfree_v2(homeoGenome, noHomeoParameters=4,
        backendSimulator=None, dataDir=None, noNoise=False, noUnisel=False,
        lightIntensity=GA_LIGHT_INTENSITY):
    '''Weight-free 2+2 direct phototaxis GA experiment with continuous
    uniselectors; all connections on the motors active.

    Genome: 8 genes = 2 units x 4 params [mass, viscosity, tau_a, maxDeviation],
    layout 'weightfree_v2': mass and viscosity log-uniform in [0.25, 250] and
    [0.05, 50] (HomeoUnit.massFromGeneLog, viscosityFromGeneLog); dt_fast 1.
    '''
    return _setup_continuous_weightfree_homeostat_direct(
        homeoGenome, backendSimulator, dataDir=dataDir,
        noNoise=noNoise, noUnisel=noUnisel, topology='random', layout='weightfree_v2',
        lightIntensity=lightIntensity)

initializeBraiten2_direct_GA_continuous_weightfree_v2.noEvolvedUnits = 2
initializeBraiten2_direct_GA_continuous_weightfree_v2.noUnits = 4
initializeBraiten2_direct_GA_continuous_weightfree_v2.fitnessSign = 1
initializeBraiten2_direct_GA_continuous_weightfree_v2.genomeSize = 8
initializeBraiten2_direct_GA_continuous_weightfree_v2.genomeLayout = 'weightfree_v2'


def initializeBraiten2_direct_GA_continuous_weightfree_fixed_v2(homeoGenome, noHomeoParameters=4,
        backendSimulator=None, dataDir=None, noNoise=False, noUnisel=False,
        lightIntensity=GA_LIGHT_INTENSITY):
    '''Weight-free 2+2 direct phototaxis GA experiment with continuous
    uniselectors; fixed Braitenberg cross-wiring.

    Genome: 8 genes = 2 units x 4 params [mass, viscosity, tau_a, maxDeviation],
    layout 'weightfree_v2': mass and viscosity log-uniform in [0.25, 250] and
    [0.05, 50] (HomeoUnit.massFromGeneLog, viscosityFromGeneLog); dt_fast 1.
    '''
    return _setup_continuous_weightfree_homeostat_direct(
        homeoGenome, backendSimulator, dataDir=dataDir,
        noNoise=noNoise, noUnisel=noUnisel, topology='fixed', layout='weightfree_v2',
        lightIntensity=lightIntensity)

initializeBraiten2_direct_GA_continuous_weightfree_fixed_v2.noEvolvedUnits = 2
initializeBraiten2_direct_GA_continuous_weightfree_fixed_v2.noUnits = 4
initializeBraiten2_direct_GA_continuous_weightfree_fixed_v2.fitnessSign = 1
initializeBraiten2_direct_GA_continuous_weightfree_fixed_v2.genomeSize = 8
initializeBraiten2_direct_GA_continuous_weightfree_fixed_v2.genomeLayout = 'weightfree_v2'


# ===============================================================
#  Hunger: a battery on the robot, sensed by the homeostat
#
#  A composable layer: add_battery_to_homeostat() gives any vehicle's
#  robot a battery (KheperaSimulator.Battery) and its homeostat a
#  Battery unit, an interoceptive sensor, wired to the motors -- directly,
#  or through a Hunger unit whose inputs its own uniselector adjusts.
# ===============================================================

# The radius of the worlds' sources (their bodies' radius): a battery whose
# saturation is not given absorbs at most the food at its source's edge.
FOOD_SOURCE_RADIUS = 0.06


def _foodSource(robot, target):
    "The source the robot feeds on: the TARGET if it is one of its food sources, else the first"
    sources = robot.foodSources()
    if not sources:
        raise ValueError('the world has no source of quality %r with a positive intensity'
                         % robot.foodQuality)
    return target if any(s is target for s in sources) else sources[0]


def add_battery_to_homeostat(hom, backendSimulator, food_quality='light', capacity=1.0,
                             discharge_rate=1e-5, recharge_factor=None, saturation=None,
                             critical_level=0.3, depletion='none', min_efficiency=0.1,
                             signal='hunger', to_motors=True, hunger_unit=False,
                             hunger_inputs='battery', stress_source=None, noNoise=False):
    '''Give the robot of backendSimulator's world a battery and hom a
    Battery unit that senses it.  Call once the world exists (after the
    vehicle's setup).  Returns the Battery unit.

    The battery (KheperaSimulator.Battery; its parameters are described
    there) feeds on the sources of quality food_quality.  Defaults:
      recharge_factor None: break-even at BREAK_EVEN_DISTANCE (1.0) from the
                      food source (the TARGET, if it is one), so the battery
                      gains charge closer than that and loses it farther;
      saturation None: the food at the food source's edge
                      (FOOD_SOURCE_RADIUS from its centre), the most a robot
                      on the source can absorb.
    The Battery unit (a HomeoUnitInput, no inputs, no uniselector) reads the
    battery's hunger (signal 'hunger', the default: capacity - level) or
    its level ('level').  With to_motors (the default) it feeds every motor
    (the units named '... Motor') through a small random weight, in
    [-0.1, 0.1) as the weight-free vehicles' sensor weights, under the
    motor's uniselector if it has an active one, fixed otherwise; its other
    outgoing connections are off.  to_motors=False: a battery that is only
    recorded.

    hunger_unit=True puts a Newtonian unit 'Hunger' between the Battery
    unit and the motors: the Battery feeds Hunger, Hunger feeds the motors
    (small random weights, as above), and the Battery no longer feeds the
    motors directly.  Hunger's inputs are under its own uniselector (the
    motors' kind: continuous if theirs is), with a negative self-connection
    as the motors have: from the Battery only (hunger_inputs 'battery') or
    from every unit but itself ('all').

    Every continuous uniselector of hom gets the battery's sensor, so that
    its stress can come from the battery; stress_source, if given, is set on
    every active one (HomeoUniselectorContinuous.STRESS_SOURCES: 'battery'
    makes the search grow with hunger).
    '''
    from KheperaSimulator.Battery import Battery, BREAK_EVEN_DISTANCE
    from Core.HomeoUniselectorContinuous import HomeoUniselectorContinuous

    if hunger_inputs not in ('battery', 'all'):
        raise ValueError("hunger_inputs must be 'battery' or 'all', got %r" % hunger_inputs)
    sim = backendSimulator.kheperaSimulation
    robot = sim.allBodies['Khepera']
    robot.foodQuality = food_quality
    source = _foodSource(robot, sim.allBodies.get('TARGET'))
    if recharge_factor is None:
        recharge_factor = Battery.breakEvenRechargeFactor(
            discharge_rate, robot.sourceValue(source, BREAK_EVEN_DISTANCE))
    if saturation is None:
        saturation = robot.sourceValue(source, FOOD_SOURCE_RADIUS)
    robot.battery = Battery(capacity=capacity, discharge_rate=discharge_rate,
                            recharge_factor=recharge_factor, saturation=saturation,
                            critical_level=critical_level, depletion=depletion,
                            min_efficiency=min_efficiency)

    unit_noise = 0 if noNoise else 0.05
    conn_noise = 0.0 if noNoise else 0.05
    motors = [u for u in hom.homeoUnits if u.name.endswith('Motor')]

    battery_unit = HomeoUnitInput(transducer=backendSimulator.getBatterySensor(signal))
    hom.addFullyConnectedUnit(battery_unit)
    battery_unit.name = 'Battery'
    battery_unit.noise = unit_noise
    battery_unit.uniselectorActive = False
    for conn in battery_unit.inputConnections:
        conn.status = False

    def feed(unit, source_unit):
        "Connect source_unit to unit with a small random weight"
        conn = [c for c in unit.inputConnections if c.incomingUnit is source_unit][0]
        conn.newWeight(np.random.uniform(-0.1, 0.1))
        conn.noise = conn_noise
        conn.state = 'uniselector' if unit.uniselectorActive else 'manual'
        conn.status = True

    def silence(source_unit, keep=()):
        "Turn off source_unit's connections to every unit not in keep"
        for unit in hom.homeoUnits:
            if unit is source_unit or any(unit is k for k in keep):
                continue
            for conn in unit.inputConnections:
                if conn.incomingUnit is source_unit:
                    conn.status = False

    def stress_from_battery():
        "Give every continuous uniselector the battery, and the stress source"
        for unit in hom.homeoUnits:
            if isinstance(unit.uniselector, HomeoUniselectorContinuous):
                unit.uniselector.batterySensor = backendSimulator.getBatterySensor('level')
                if stress_source is not None and unit.uniselectorActive:
                    unit.uniselector.stress_source = stress_source

    if not hunger_unit:
        silence(battery_unit, keep=motors if to_motors else ())
        if to_motors:
            for motor in motors:
                feed(motor, battery_unit)
        stress_from_battery()
        return battery_unit

    hunger = HomeoUnitNewtonian()
    hom.addFullyConnectedUnit(hunger)
    hunger.name = 'Hunger'
    hunger.noise = unit_noise
    hunger.uniselectorActive = True
    if any(isinstance(m.uniselector, HomeoUniselectorContinuous) for m in motors):
        hunger.uniselector = HomeoUniselectorContinuous()
    for conn in hunger.inputConnections:
        conn.status = False
    self_conn = hunger.inputConnections[0]
    self_conn.newWeight(-np.random.uniform(0.01, 0.1))
    self_conn.noise = conn_noise
    self_conn.state = 'manual'
    self_conn.status = True
    for unit in hom.homeoUnits:
        if unit is battery_unit or (hunger_inputs == 'all' and unit is not hunger):
            feed(hunger, unit)
    silence(battery_unit, keep=(hunger,))
    silence(hunger, keep=motors if to_motors else ())
    if to_motors:
        for motor in motors:
            feed(motor, hunger)
    stress_from_battery()
    return battery_unit


#===============================================================================
# Utility functions
#===============================================================================


def _backendWorld(backendSimulator, world):
    """The world a GA setup builds on backendSimulator: the HOMEO (Box2D) world,
    or its Webots twin.  A setup called without a backend raises a ValueError."""
    if backendSimulator is None:
        raise ValueError("this setup needs a backendSimulator (Simulator/SimulatorBackend.py)")
    if backendSimulator.name not in ('HOMEO', 'WEBOTS'):
        raise Exception("I cannot use backend simulator %s yet" % backendSimulator.name)
    return world


def basicBraiten2Tranducers(backendSimulator, world):
    """Asks the back end simulator to return 4 
       tranducers: two wheels and two sensors"""
       
    "1. start backend simulation with correct world"
    
    try:
        backendSimulator.start(world)
    except Exception as e:
        raise Exception("I cannot start the backend simulator %s. Aborting...\nCause: %s" % (backendSimulator.name, e)) from e
    
    "2. get transducers"    
    transducers = {"rightWheelTransd" : backendSimulator.getWheel('right'), 
                   "leftWheelTransd"  : backendSimulator.getWheel('left'), 
                   "rightEyeTransd"   : backendSimulator.getSensor('right'), 
                   "leftEyeTransd"    : backendSimulator.getSensor('left')} 
   
    return transducers


def braiten3cTransducers(backendSimulator, world):
    """Return 10 transducers for Braitenberg Vehicle 3c:
    2 wheel motors + 8 quality-filtered sensors (one pair per quality).

    The robot must already have 8 sensor fixtures: leftEye, rightEye,
    leftTempEye, rightTempEye, leftOxyEye, rightOxyEye, leftOrgEye, rightOrgEye.
    """

    "1. start backend simulation with correct world"
    try:
        backendSimulator.start(world)
    except Exception as e:
        raise Exception("I cannot start the backend simulator %s. Aborting...\nCause: %s"
                        % (backendSimulator.name, e)) from e

    "2. get transducers"
    transducers = {
        "rightWheelTransd": backendSimulator.getWheel('right'),
        "leftWheelTransd":  backendSimulator.getWheel('left'),
        # Light sensors use the existing leftEye/rightEye fixtures
        "leftLightTransd":  backendSimulator.getQualitySensor('leftEye', 'light'),
        "rightLightTransd": backendSimulator.getQualitySensor('rightEye', 'light'),
        # Temperature
        "leftTempTransd":   backendSimulator.getQualitySensor('leftTempEye', 'temperature'),
        "rightTempTransd":  backendSimulator.getQualitySensor('rightTempEye', 'temperature'),
        # Oxygen
        "leftOxyTransd":    backendSimulator.getQualitySensor('leftOxyEye', 'oxygen'),
        "rightOxyTransd":   backendSimulator.getQualitySensor('rightOxyEye', 'oxygen'),
        # Organic matter
        "leftOrgTransd":    backendSimulator.getQualitySensor('leftOrgEye', 'organic'),
        "rightOrgTransd":   backendSimulator.getQualitySensor('rightOrgEye', 'organic'),
    }

    return transducers


def _setup_braitenberg_3c_homeostat(homeoGenome, backendSimulator,
                                    dataDir=None, noNoise=False, noUnisel=False,
                                    topology='fixed',
                                    layout='weightfree_v2',
                                    lightIntensity=GA_LIGHT_INTENSITY):
    '''Setup a 10-unit homeostat for Braitenberg Vehicle 3c (multi-quality).

    2 motor units (evolved via genome) + 8 sensor input units (pure transducers).

    Genome: the 2 motors' genes in the layout given (see
    WEIGHTFREE_GENES_PER_UNIT): 'weightfree_v2', 8 genes = 2 x
    [mass, viscosity, tau_a, maxDeviation].

    Connection weights are NOT in the genome — they are initialised to small
    random values and evolved online by the continuous uniselector.

    Parameters
    ----------
    topology : str
        'fixed'  — Braitenberg's wiring (Vehicles p.12):
                    Light: crossed excitatory, Temp: uncrossed excitatory,
                    O2: crossed inhibitory, Organic: uncrossed inhibitory.
        'open'   — all 16 sensor->motor connections active.
    '''
    from Core.HomeoUniselectorContinuous import HomeoUniselectorContinuous

    world = _backendWorld(backendSimulator, 'kheperaBraitenberg3c_HOMEO_World')

    transducers = braiten3cTransducers(backendSimulator, world)
    if transducers is None:
        raise Exception("Could not build transducers for simulator backend ",
                        backendSimulator.name)

    "1. Create homeostat and units"
    hom = Homeostat()
    HomeoUnit.clearNames()

    # Motors
    leftMotor = HomeoUnitNewtonianActuator(transducer=transducers["leftWheelTransd"])
    rightMotor = HomeoUnitNewtonianActuator(transducer=transducers["rightWheelTransd"])

    # Sensor-only units (8 of them)
    leftLight  = HomeoUnitInput(transducer=transducers["leftLightTransd"])
    rightLight = HomeoUnitInput(transducer=transducers["rightLightTransd"])
    leftTemp   = HomeoUnitInput(transducer=transducers["leftTempTransd"])
    rightTemp  = HomeoUnitInput(transducer=transducers["rightTempTransd"])
    leftOxy    = HomeoUnitInput(transducer=transducers["leftOxyTransd"])
    rightOxy   = HomeoUnitInput(transducer=transducers["rightOxyTransd"])
    leftOrg    = HomeoUnitInput(transducer=transducers["leftOrgTransd"])
    rightOrg   = HomeoUnitInput(transducer=transducers["rightOrgTransd"])

    "2. Decode genome — only motor units are evolved"
    genes_per_unit = WEIGHTFREE_GENES_PER_UNIT[layout]
    evolved_units = [leftMotor, rightMotor]
    _decodeWeightfreeUnits(evolved_units, homeoGenome, layout)

    "3. Build fully-connected homeostat"
    all_units = [leftMotor, rightMotor,
                 leftLight, rightLight, leftTemp, rightTemp,
                 leftOxy, rightOxy, leftOrg, rightOrg]
    for unit in all_units:
        hom.addFullyConnectedUnit(unit)

    "4. Name units and set noise"
    if noNoise:
        unit_noise = 0
        conn_noise = 0.0
    else:
        unit_noise = 0.05
        conn_noise = 0.05

    leftMotor.name = 'Left Motor'
    leftMotor.noise = unit_noise
    leftMotor._maxSpeedFraction = 0.8
    leftMotor._switchingRate = 0.5
    leftMotor._maxSpeed = None
    rightMotor.name = 'Right Motor'
    rightMotor.noise = unit_noise
    rightMotor._maxSpeedFraction = 0.8
    rightMotor._switchingRate = 0.5
    rightMotor._maxSpeed = None

    sensor_names = {
        leftLight: 'Left Light', rightLight: 'Right Light',
        leftTemp: 'Left Temp',   rightTemp: 'Right Temp',
        leftOxy: 'Left Oxy',     rightOxy: 'Right Oxy',
        leftOrg: 'Left Org',     rightOrg: 'Right Org',
    }
    for unit, name in sensor_names.items():
        unit.name = name
        unit.noise = unit_noise

    "5. Disable sensor-only units (pure input transducers)"
    sensor_units = [leftLight, rightLight, leftTemp, rightTemp,
                    leftOxy, rightOxy, leftOrg, rightOrg]
    for su in sensor_units:
        su.uniselectorActive = False
        for conn in su.inputConnections:
            conn.status = False

    "6. Configure connections on motor units"
    for unit in evolved_units:
        "Self-connection: negative, manual (stability guarantee)"
        unit.inputConnections[0].newWeight(-np.random.uniform(0.01, 0.1))
        unit.inputConnections[0].noise = conn_noise
        unit.inputConnections[0].state = 'manual'
        unit.inputConnections[0].status = True

    # Disable motor-to-motor cross-connections
    for conn in leftMotor.inputConnections:
        if conn.incomingUnit is rightMotor:
            conn.status = False
    for conn in rightMotor.inputConnections:
        if conn.incomingUnit is leftMotor:
            conn.status = False

    if topology == 'fixed':
        "Braitenberg's Vehicle 3c wiring"
        # First disable all non-self connections on motors
        for unit in evolved_units:
            for conn in unit.inputConnections[1:]:
                conn.status = False

        # Braitenberg 3c wiring table (Vehicles p.12):
        #   quality     | wiring    | sign  | left motor source | right motor source
        #   Light       | crossed   | +     | Right Light       | Left Light
        #   Temperature | uncrossed | +     | Left Temp         | Right Temp
        #   Oxygen      | crossed   | -     | Right Oxy         | Left Oxy
        #   Organic     | uncrossed | -     | Left Org          | Right Org
        fixed_wiring = {
            leftMotor: [
                ('Right Light', +1),
                ('Left Temp',   +1),
                ('Right Oxy',   -1),
                ('Left Org',    -1),
            ],
            rightMotor: [
                ('Left Light',  +1),
                ('Right Temp',  +1),
                ('Left Oxy',    -1),
                ('Right Org',   -1),
            ],
        }
        for motor, wiring_list in fixed_wiring.items():
            for source_name, sign in wiring_list:
                for conn in motor.inputConnections:
                    if conn.incomingUnit.name == source_name:
                        init_weight = sign * np.random.uniform(0.01, 0.1)
                        conn.newWeight(init_weight)
                        conn.noise = conn_noise
                        conn.state = 'uniselector'
                        conn.status = True
    else:
        "Open topology: all 16 sensor->motor connections active"
        for unit in evolved_units:
            for conn in unit.inputConnections[1:]:
                if conn.incomingUnit in sensor_units:
                    conn.newWeight(np.random.uniform(-0.1, 0.1))
                    conn.noise = conn_noise
                    conn.state = 'uniselector'
                    conn.status = True

    "7. Swap uniselectors to continuous ones and set tau_a from genome"
    for i, unit in enumerate(evolved_units):
        # noUnisel: the continuous uniselector stays installed (it records tau_a) but
        # never runs, so the weights keep their initial values
        unit.uniselectorActive = not noUnisel
        unis = HomeoUniselectorContinuous()
        unis.tau_a = HomeoUnit.tauAFromWeight(homeoGenome[i * genes_per_unit + 2])
        unit.uniselector = unis

    "8. The light the robot seeks (see GA_LIGHT_INTENSITY); the other qualities' sources unchanged"
    setTargetIntensity(backendSimulator, lightIntensity)


    hDebug('unit', "Homeostat initialized (Braiten3c, topology=%s)" % topology)
    return hom


def initializeBraiten3c_GA_continuous_weightfree_fixed_v2(homeoGenome, noHomeoParameters=4,
        backendSimulator=None, dataDir=None, noNoise=False, noUnisel=False,
        lightIntensity=GA_LIGHT_INTENSITY):
    '''Braitenberg Vehicle 3c with fixed Braitenberg wiring.

    Genome: 8 genes = 2 units x 4 params [mass, viscosity, tau_a, maxDeviation],
    layout 'weightfree_v2': mass and viscosity log-uniform in [0.25, 250] and
    [0.05, 50] (HomeoUnit.massFromGeneLog, viscosityFromGeneLog); dt_fast 1.
    '''
    return _setup_braitenberg_3c_homeostat(
        homeoGenome, backendSimulator, dataDir=dataDir,
        noNoise=noNoise, noUnisel=noUnisel, topology='fixed', layout='weightfree_v2',
        lightIntensity=lightIntensity)

initializeBraiten3c_GA_continuous_weightfree_fixed_v2.noEvolvedUnits = 2
initializeBraiten3c_GA_continuous_weightfree_fixed_v2.noUnits = 10
initializeBraiten3c_GA_continuous_weightfree_fixed_v2.fitnessSign = 1
initializeBraiten3c_GA_continuous_weightfree_fixed_v2.genomeSize = 8
initializeBraiten3c_GA_continuous_weightfree_fixed_v2.genomeLayout = 'weightfree_v2'


def initializeBraiten3c_GA_continuous_weightfree_open_v2(homeoGenome, noHomeoParameters=4,
        backendSimulator=None, dataDir=None, noNoise=False, noUnisel=False,
        lightIntensity=GA_LIGHT_INTENSITY):
    '''Braitenberg Vehicle 3c with open topology (all 16 sensor->motor connections).

    Genome: 8 genes = 2 units x 4 params [mass, viscosity, tau_a, maxDeviation],
    layout 'weightfree_v2': mass and viscosity log-uniform in [0.25, 250] and
    [0.05, 50] (HomeoUnit.massFromGeneLog, viscosityFromGeneLog); dt_fast 1.
    '''
    return _setup_braitenberg_3c_homeostat(
        homeoGenome, backendSimulator, dataDir=dataDir,
        noNoise=noNoise, noUnisel=noUnisel, topology='open', layout='weightfree_v2',
        lightIntensity=lightIntensity)

initializeBraiten3c_GA_continuous_weightfree_open_v2.noEvolvedUnits = 2
initializeBraiten3c_GA_continuous_weightfree_open_v2.noUnits = 10
initializeBraiten3c_GA_continuous_weightfree_open_v2.fitnessSign = 1
initializeBraiten3c_GA_continuous_weightfree_open_v2.genomeSize = 8
initializeBraiten3c_GA_continuous_weightfree_open_v2.genomeLayout = 'weightfree_v2'


# ===============================================================
#  Hunger GA setups: the weight-free vehicles with a battery
#
#  The battery dies at zero (depletion 'death') and the GA minimises the
#  setup's fitness measure (`fitness`, read by HomeoGenAlg.evaluate_genome):
#  'battery_mean', minus the battery's mean level over the evaluation (the
#  ticks after death count as empty).
# ===============================================================

def initializeHungerPhototaxis_GA_continuous_weightfree_fixed_v2(homeoGenome, noHomeoParameters=4,
        backendSimulator=None, dataDir=None, noNoise=False, noUnisel=False,
        lightIntensity=GA_LIGHT_INTENSITY):
    '''Hunger-driven phototaxis: the weight-free 2+2 direct vehicle with
    fixed Braitenberg cross-wiring (initializeBraiten2_direct_GA_continuous_weightfree_fixed_v2)
    and a battery that recharges from the light, sensed by a Battery unit
    feeding both motors (add_battery_to_homeostat, depletion 'death').
    Fitness: the battery's mean level.

    Genome: 8 genes = 2 units x 4 params [mass, viscosity, tau_a, maxDeviation],
    layout 'weightfree_v2' (see initializeBraiten2_direct_GA_continuous_weightfree_fixed_v2).
    '''
    hom = _setup_continuous_weightfree_homeostat_direct(
        homeoGenome, backendSimulator, dataDir=dataDir,
        noNoise=noNoise, noUnisel=noUnisel, topology='fixed', layout='weightfree_v2',
        lightIntensity=lightIntensity)
    add_battery_to_homeostat(hom, backendSimulator, food_quality='light', depletion='death',
                             noNoise=noNoise)
    return hom

initializeHungerPhototaxis_GA_continuous_weightfree_fixed_v2.noEvolvedUnits = 2
initializeHungerPhototaxis_GA_continuous_weightfree_fixed_v2.noUnits = 5
initializeHungerPhototaxis_GA_continuous_weightfree_fixed_v2.fitnessSign = 1
initializeHungerPhototaxis_GA_continuous_weightfree_fixed_v2.fitness = 'battery_mean'
initializeHungerPhototaxis_GA_continuous_weightfree_fixed_v2.genomeSize = 8
initializeHungerPhototaxis_GA_continuous_weightfree_fixed_v2.genomeLayout = 'weightfree_v2'


def initializeHunger3c_GA_continuous_weightfree_fixed_v2(homeoGenome, noHomeoParameters=4,
        backendSimulator=None, dataDir=None, noNoise=False, noUnisel=False,
        lightIntensity=GA_LIGHT_INTENSITY):
    '''Hunger in the Vehicle 3c world: the weight-free Vehicle 3c with
    fixed Braitenberg wiring (initializeBraiten3c_GA_continuous_weightfree_fixed_v2)
    and a battery that recharges from organic matter, sensed by a Battery
    unit feeding both motors (add_battery_to_homeostat, depletion 'death').
    Fitness: the battery's mean level.

    Genome: 8 genes = 2 units x 4 params [mass, viscosity, tau_a, maxDeviation],
    layout 'weightfree_v2'.
    '''
    hom = _setup_braitenberg_3c_homeostat(
        homeoGenome, backendSimulator, dataDir=dataDir,
        noNoise=noNoise, noUnisel=noUnisel, topology='fixed', layout='weightfree_v2',
        lightIntensity=lightIntensity)
    add_battery_to_homeostat(hom, backendSimulator, food_quality='organic', depletion='death',
                             noNoise=noNoise)
    return hom

initializeHunger3c_GA_continuous_weightfree_fixed_v2.noEvolvedUnits = 2
initializeHunger3c_GA_continuous_weightfree_fixed_v2.noUnits = 11
initializeHunger3c_GA_continuous_weightfree_fixed_v2.fitnessSign = 1
initializeHunger3c_GA_continuous_weightfree_fixed_v2.fitness = 'battery_mean'
initializeHunger3c_GA_continuous_weightfree_fixed_v2.genomeSize = 8
initializeHunger3c_GA_continuous_weightfree_fixed_v2.genomeLayout = 'weightfree_v2'


# The GA phototaxis setups, which take lightIntensity (see GA_LIGHT_INTENSITY)
for _f in (initializeBraiten2_2_Full_GA_phototaxis, initializeBraiten2_2_Full_GA_phototaxis_continuous,
           initializeBraiten2_2_Full_GA_continuous_weightfree_v2,
           initializeBraiten2_2_Full_GA_continuous_weightfree_fixed_v2,
           initializeBraiten2_direct_GA_continuous_weightfree_v2,
           initializeBraiten2_direct_GA_continuous_weightfree_fixed_v2,
           initializeBraiten3c_GA_continuous_weightfree_fixed_v2,
           initializeBraiten3c_GA_continuous_weightfree_open_v2,
           initializeHungerPhototaxis_GA_continuous_weightfree_fixed_v2,
           initializeHunger3c_GA_continuous_weightfree_fixed_v2,
           ):
    _f.lightIntensity = GA_LIGHT_INTENSITY


# ===============================================================
#  Ashby's 7 Original Experiments — GUI-friendly setup functions
#
#  Each returns a configured Homeostat ready to run, built by the
#  headless setup in AshbyOriginalExperiments.py, so the GUI and headless
#  experiments are one setup.  Per-tick callbacks (trainer, fibre, bars)
#  are NOT installed here; the GUI subclass installs them.
# ===============================================================

# The GUI's Ashby experiments build their homeostats with the headless
# setups (AshbyOriginalExperiments.setup_expN), seeded with params['seed']
# (drawn if absent) and the seed kept as hom.seed: a GUI run's homeostat is
# the headless run's with the same seed (the unused slots draw nothing, see
# _add_unused_slots).

def initializeAshbyExp1BasicUltrastability(**params):
    '''Exp 1: Basic Ultrastability (DftB 8/4, Fig. 8/4/1).

    Two units: 1->2 hand-controlled (reversed by the user), 2->1 on unit 1's
    uniselector.  Same setup as the headless
    AshbyOriginalExperiments.setup_exp1_basic_ultrastability, with units 3
    and 4 inactive.
    '''
    from Simulator.AshbyOriginalExperiments import setup_exp1_basic_ultrastability
    hom, seed, meta = setup_exp1_basic_ultrastability(seed=params.get('seed'), unused_slots=True)
    hom.seed = seed          # shown by the GUI and pickled with the homeostat
    return hom


def initializeAshbyExp2SelfReorganization(**params):
    '''Exp 2: Self-Reorganization in 3-Unit Circle (DftB 8/5).

    3 units in a ring, 1->2->3->1: 3->1 fixed negative, 1->2 on unit 2's
    uniselector, 2->3 hand-controlled (reversed by the user).  Same setup as
    the headless AshbyOriginalExperiments.setup_exp2_self_reorganization,
    with unit 4 inactive.
    '''
    from Simulator.AshbyOriginalExperiments import setup_exp2_self_reorganization
    hom, seed, meta = setup_exp2_self_reorganization(seed=params.get('seed'))
    hom.seed = seed          # shown by the GUI and pickled with the homeostat
    return hom


def initializeAshbyExp3Training(**params):
    '''Exp 3: Training by Punishment (DftB 8/9).

    3 units in a ring; the operator's tests and the trainer (installed by
    the GUI) act on units 1 and 3.  Same setup as the headless
    AshbyOriginalExperiments.setup_exp3_training, with unit 4 inactive.
    '''
    from Simulator.AshbyOriginalExperiments import setup_exp3_training
    hom, seed, meta = setup_exp3_training(seed=params.get('seed'), unused_slots=True)
    hom.seed = seed          # shown by the GUI and pickled with the homeostat
    return hom


def initializeAshbyExp4AlternatingEnvironments(**params):
    '''Exp 4: Alternating Environments (DftB 8/10).

    Two units: 1->2 is the commutator H (toggled by the user), 2->1 is on
    unit 1's uniselector.  Same setup as the headless
    AshbyOriginalExperiments.setup_exp4_alternating_environments, with
    units 3 and 4 inactive.
    '''
    from Simulator.AshbyOriginalExperiments import setup_exp4_alternating_environments
    hom, seed, meta = setup_exp4_alternating_environments(seed=params.get('seed'), unused_slots=True)
    hom.seed = seed          # shown by the GUI and pickled with the homeostat
    return hom


def initializeAshbyExp5Constraint(**params):
    '''Exp 5: Constraint / Glass Fibre (DftB 8/11).

    3 fully connected units; the user joins units 1 and 2 with the fibre
    (J) and later removes it (R); the fibre callback is installed by the GUI.
    Same setup as the headless AshbyOriginalExperiments.setup_exp5_constraint,
    with unit 4 inactive.
    '''
    from Simulator.AshbyOriginalExperiments import setup_exp5_constraint
    hom, seed, meta = setup_exp5_constraint(seed=params.get('seed'), unused_slots=True)
    hom.seed = seed          # shown by the GUI and pickled with the homeostat
    return hom


def initializeAshbyExp6Habituation(**params):
    '''Exp 6: Habituation (DftB 14/6, Fig. 14/6/1).

    Two units joined 1->2 only, 1->2 on unit 2's uniselector; the user
    delivers repeated stimuli to unit 1.  Same setup as the headless
    AshbyOriginalExperiments.setup_exp6_habituation, with units 3 and 4
    inactive.
    '''
    from Simulator.AshbyOriginalExperiments import setup_exp6_habituation
    hom, seed, meta = setup_exp6_habituation(seed=params.get('seed'), unused_slots=True)
    hom.seed = seed          # shown by the GUI and pickled with the homeostat
    return hom


def initializeAshbyExp7Multistable(**params):
    '''Exp 7: Multistable System (DftB 16/8).

    3 units, 2 <-> 1 <-> 3; 1->2 and 1->3 by hand, 2->1 and 3->1 on unit 1's
    uniselector; bars stop 2 and 3 above the centre (callback installed by
    the GUI).  Same setup as the headless
    AshbyOriginalExperiments.setup_exp7_multistable, with unit 4 inactive.
    '''
    from Simulator.AshbyOriginalExperiments import setup_exp7_multistable
    hom, seed, meta = setup_exp7_multistable(seed=params.get('seed'), unused_slots=True)
    hom.seed = seed          # shown by the GUI and pickled with the homeostat
    return hom

