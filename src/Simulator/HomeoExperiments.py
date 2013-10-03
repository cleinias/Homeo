'''
Created on Sep 4, 2013

@author: stefano
'''

from Core.Homeostat import *
from Core.HomeoUnitNewtonian import *
from Core.HomeoConnection import  * 


'''
Module HomeoExperiments provides initializations data for various experiments to be conducted with the homeo package.
The module's methods return a properly configured homeostat to be used in the simulations.
'''


def initializeAshbySimulation():
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

def initialize_Ashby_2nd_Experiment():
    """
       Return a standard homeostat with 3 active units connected in a cricle, as per 
       Ashby's experiment in Design for a brain, pp. 106-107.
       In detail: connections are 1-->2-->3-->1
       connection 1-->2 is uniselector controlled
       connection 2-->3 is hand-controlled
       connection 3--> is always negative
       
       We start with:
       1 (possibly representing Motor/Agent) with negative, fixed, self-connection
       2 (possibly representing Environment) with no self-connection
       3 (possibly representing Sensor/Agent) with negative, fixed self-connection           
       """
    hom = Homeostat()
    'Standard parameters'
    agent_visc = 0.9
    env_visc = 0.9
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
            unit.inputConnections[i].status = 0
            
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

    "set up homeostat's connection"
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
            
def initialize_1minus_2xExperiment():
    '''
    Initialize a standard Homeostat to have 2 2-units 1-, 2x standard settings for 1- 2x experiment (Agent-Environment)
    with fixed parameters to improve repeated runs
    '''
    hom = Homeostat()
    
    'Standard parameters'
    agent_visc = 0.9
    env_visc = 0.9
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
            unit.inputConnections[i].status = 0
    
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
            
            
def initialize_1minus_2_minus_3xExperiment():
    """Initialize a homeostat to replicate a 3-unit
       homeostat roughly similar to DiPaolo's ocular inversion
       experiment:
       2 self-connected units representing the 'eyes' or 'sensors'
       1 unconnected nit representing the environment 
    """
    hom = Homeostat()
    
    'Standard parameters'
    agent_visc = 0.9
    env_visc = 0.9
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
            unit.inputConnections[i].status = 0
    
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


def initializeBraiten1_1():
    '''
    Initialize a Homeostat to replicate a Braitenberg type-1 vehicle with
    1 real unit for both  motor and sensor, plus one HomeoInput unit to connect to the outside world
    ''' 
    hom = Homeostat()
    
    
def initializeBraiten1_2():
    '''
    Initialize a Homeostat to replicate a Braitenberg type-1 vehicle with
    2 real units: one for the Motor and one for the sensor, plus one HomeoInput unit
    to interface to the outside world
    ''' 
    hom = Homeostat()
 
def initializeBraiten2_1():
    '''
    Initialize a Homeostat to replicate a Braitenberg type-2 vehicle with
    3 real units: two for either Motor and one for the sensor, plus one HomeoInput unit
    to interface to the outside world
    ''' 
    hom = Homeostat()

def initializeBraiten2_2():
    '''
    Initialize a Homeostat to replicate a Braitenberg type-2 vehicle with
    4 real units: two for either Motor and two for the sensors, plus one HomeoInput Unit
    to interface to the outside world
    ''' 
    hom = Homeostat()
