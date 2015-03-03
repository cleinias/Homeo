'''
Created on Mar 2, 2015

@author: stefano
General Helpers functions needed by differnet modules when using V-REP robotic simulator as a backend 

'''

import vrep 
from  subprocess import check_output
from os.path import split
from Helpers.General_Helper_Functions import asByteArray, distance

def connectToVREP(host, port, VREP_World=None, clientId = None):
    "Connect to VREP and load the correct world if needed"
    "FIXME: SHOULD LAUNCH VREP IF NOT RUNNING"
    VREP_exec = 'vrep'
  
    '1. check that V-Rep is running and see whether we are already connected to it. Otherwise connect'
    if VREP_exec not in check_output(["ps","-f", "--no-headers",  "ww", "-C", "vrep"]):
        raise Exception(("V-REP is not running! Please start V-REP with scene: %s" % VREP_World))
    else:
        "Check if we are connected with the passed clientId already"
        if clientId is not None:
            print "ClientId = " ,clientId
            connId = vrep.simxGetConnectionId(clientId)
            print "My connId is " , connId
            if connId == -1:                                 # we are not: set client Id to none and re-connect
                print "Disconnecting all existing connections to V-REP"
                vrep.simxFinish(-1)
                clientId = None            
        while clientId is None:
            clientId = vrep.simxStart(host, port,True,True, 5000,5)
            if not clientId == -1:
                eCode = vrep.simxSynchronous(clientId, True)
                if eCode != 0:
                    raise Exception("Failed to connect to VREP simulation. Bailing out")
#     print " we are connected with clientId ", clientId
    "2. Check the correct world is running"
    if VREP_World is not None: 
        VREP_Scene = split(VREP_World)[1]
        if VREP_Scene not in check_output(["ps","-f", "--no-headers",  "ww", "-C", "vrep"]):
            eCode = vrep.simxLoadScene(clientId, VREP_World, 0, vrep.simx_opmode_oneshot_wait)
            if eCode != 0:
                raise Exception(("Could not load into V-REP the world",  VREP_World))     

    
    '3 Start simulation'
    eCode = vrep.simxStartSimulation(clientId, vrep.simx_opmode_oneshot_wait)
    if eCode != 0:
        raise Exception("VREP simulation cannot get started")
    else:
        print "V-REP simulation is running with clientId: ", clientId
        return clientId 

def sendSignalVREP(clientId, signalName, signalValue):
    if type(signalValue) == str:
        eCode = vrep.simxSetStringSignal(clientId, signalName, asByteArray(signalValue), vrep.simx_opmode_oneshot_wait)
    elif type(signalValue) == int:
        eCode = vrep.simxSetIntegerSignal(clientId, signalName, signalValue, vrep.simx_opmode_oneshot_wait)
    elif type(signalValue) == float:
        eCode = vrep.simxSetFloatSignal(clientId, signalName, signalValue, vrep.simx_opmode_oneshot_wait)
    else:
        raise Exception("Trying to send a signal of unknown data type. Only strings, floats and and ints are accepted")
    if eCode != 0:
        raise Exception("Could not send string signal", signalValue)
    vrep.simxSynchronousTrigger(clientId)
#     print "Set signal %s of type %s to: " % (signalName, type( signalValue)), signalValue
    
def startSimulationVREP(clientId):
    eCode = vrep.simxStartSimulation(clientId, vrep.simx_opmode_oneshot_wait)
    if eCode !=0:
        raise Exception("Could not start VREP simulation")
    
def getDistanceBetwObjectsVREP(clientId, objectNameA, objectNameB):
    """Get the distance between two named objects in V-REP.
       Raise exception if either does not exist"""
       
    eCode, handleA = vrep.simxGetObjectHandle(clientId, objectNameA, vrep.simx_opmode_oneshot_wait)
    if eCode != 0:
        raise Exception("Could not get handle of object", objectNameA)
    eCode, poseA =  vrep.simxGetObjectPosition(clientId, handleA, -1, vrep.simx_opmode_oneshot_wait)
    eCode, handleB = vrep.simxGetObjectHandle(clientId, objectNameB, vrep.simx_opmode_oneshot_wait)
    if eCode != 0:
        raise Exception("Could not get handle of object", objectNameB)
    eCode, poseB =  vrep.simxGetObjectPosition(clientId, handleB, -1, vrep.simx_opmode_oneshot_wait)
    return distance(poseA,poseB)

def quitServerVREP(clientId):
    "Try to quite the connection to the VREP server"
    vrep.simxStopSimulation(clientId, vrep.simx_opmode_oneshot_wait)
    vrep.simxFinish(clientId)
    vrep.simxFinish(-1)
        