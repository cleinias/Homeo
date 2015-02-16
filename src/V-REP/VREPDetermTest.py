"Testing the reproducibility of random runs in V-Rep"

import vrep

import math
import numpy as np
import os, sys
import subprocess
from vrepConst import simx_opmode_oneshot, simx_opmode_oneshot_wait
from time import sleep


"Parameters"

#VREP_scene_file ="/home/stefano/Documents/Projects/Homeostat/Simulator/Python-port/Homeo/src/V-REP/Khepera-Like-scene-SF.ttt" 
simulation_port = 19997
robot_port = 20000
robot_host = '127.0.0.1'
VREP_HOME = '/home/stefano/builds/from-upstream-sources/V-REP_PRO_EDU_V3_2_0_64_Linux/'
noRuns = 5
noSteps = 5000
targetPose = [7,7] 
initPose = [4,4,0.0191]
initOrient = [-90,0,-90]
betwCmdDelays = 0
maxSpeed = 5


"Clean up"
def cleanUp():
    print "About to stop simulation connected to simulID: ", simulID
    vrep.simxStopSimulation(simulID, vrep.simx_opmode_oneshot)
    vrep.simxSynchronousTrigger(simulID)                    
#     vrep.simxFinish(robotID)
    vrep.simxFinish(simulID)
    vrep.simxFinish(-1)
    print "Disconnected from V-REP"

def computeDistance(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

def stopRobot(simulHandle, motorHandles):
    for motor in motorHandles:
        eCode = vrep.simxSetJointTargetVelocity(simulHandle, motor, 0, vrep.simx_opmode_oneshot)
        vrep.simxSynchronousTrigger(simulID)                    

"Launch V-REP"
#os.chdir(VREP_HOME)
#subprocess.call([os.path.join(VREP_HOME,'vrep.sh'), VREP_scene_file], shell = True, cwd = VREP_HOME)


"Close existing connections"
vrep.simxFinish(-1)

"Connect to Simulation"
simulID = vrep.simxStart(robot_host,simulation_port,True,True, 5000,5)

eCode = vrep.simxSynchronous(simulID, True)
if eCode != 0:
    print "Could not get V-REP to synchronize operation with me"

if not simulID == -1:
    eCode = vrep.simxStartSimulation(simulID, vrep.simx_opmode_oneshot)
    vrep.simxSynchronousTrigger(simulID)                    
    print "my SimulID is  ", simulID 
else:
    sys.exit("Failed to connect to VREP simulation. Bailing out")

"Get handles for epuck and motors"
ecodeE, ePuckHandle = vrep.simxGetObjectHandle(simulID, "ePuck", vrep.simx_opmode_oneshot_wait)
vrep.simxSynchronousTrigger(simulID)                    
# eCodeEC, ePuckCollHandle = vrep.simxGetObjectHandle(simulID, "ePuck1", vrep.simx_opmode_oneshot_wait)
eCodeR, rightMotor  = vrep.simxGetObjectHandle(simulID, "ePuck_rightJoint", vrep.simx_opmode_oneshot_wait)
vrep.simxSynchronousTrigger(simulID)                    
eCodeL, leftMotor   = vrep.simxGetObjectHandle(simulID, "ePuck_leftJoint", vrep.simx_opmode_oneshot_wait)
vrep.simxSynchronousTrigger(simulID)                    

if (ePuckHandle == 0 or rightMotor == 0 or leftMotor == 0):
    cleanUp()
    sys.exit("Exiting:  Could not connect to motors")
else:
    print " I am connected to Right Motor with ID %d and leftMotor with id %d" % (rightMotor, leftMotor)

for run in xrange(noRuns):
#     print "About to start simulation for run number: ", run+1
    eCode = vrep.simxStartSimulation(simulID, vrep.simx_opmode_oneshot_wait)
    vrep.simxSynchronousTrigger(simulID)
    print "Simulation started, code", eCode    
#     stopRobot(simulID,[rightMotor,leftMotor])
    np.random.seed(64)
#     resetRobotInitPose(initPose, simulID, ePuckHandle)
    for step in xrange(noSteps):
        rightSpeed = -maxSpeed + np.random.uniform(maxSpeed*2)
        leftSpeed = -maxSpeed + np.random.uniform(maxSpeed*2)
        eCode = vrep.simxSetJointTargetVelocity(simulID, rightMotor, rightSpeed, vrep.simx_opmode_oneshot)
        eCode = vrep.simxSetJointTargetVelocity(simulID, leftMotor, leftSpeed, vrep.simx_opmode_oneshot)
        vrep.simxSynchronousTrigger(simulID)
        for i in xrange(betwCmdDelays):
            vrep.simxSynchronousTrigger(simulID)
#         print "%d\t Speeds are L:%.3f\tR:%.3f" %(step, rightSpeed,leftSpeed)
    "Stop the robot"
    stopRobot(simulID,[rightMotor,leftMotor])
#     vrep.simxSynchronousTrigger(simulID)
#     sleep(.5)
    robotPose = vrep.simxGetObjectPosition(simulID,ePuckHandle, -1, vrep.simx_opmode_oneshot_wait)[1][:2]
    vrep.simxSynchronousTrigger(simulID)
    print "%d: Robot is at: %.3f, %.3f Distance from target is:  %.4f" %(run, robotPose[0],robotPose[1], computeDistance(targetPose,robotPose))
#     print " About to stop simulation"
    eCode = vrep.simxStopSimulation(simulID,vrep.simx_opmode_oneshot_wait)
    vrep.simxSynchronousTrigger(simulID)
    sleep(2)
#     print "Simulation stopped"

print "Done"
# sleep(1)
cleanUp()
