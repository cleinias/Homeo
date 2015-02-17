

"Testing the reproducibility of random runs in V-Rep"

import vrep

import math
import numpy as np
import matplotlib.pyplot as plt
import os, sys
import subprocess
from vrepConst import simx_opmode_oneshot, simx_opmode_oneshot_wait
from time import sleep


class VREPTests(object):
    
    def __init__(self, noSteps = 5000, noRuns=5):
        "Parameters"
        
        #VREP_scene_file ="/home/stefano/Documents/Projects/Homeostat/Simulator/Python-port/Homeo/src/V-REP/Khepera-Like-scene-SF.ttt" 
        self.simulation_port = 19997
        self.robot_port = 20000
        self.robot_host = '127.0.0.1'
        self.VREP_HOME = '/home/stefano/builds/from-upstream-sources/V-REP_PRO_EDU_V3_2_0_64_Linux/'
        self.noRuns = noRuns
        self.noSteps = noSteps
        self.targetPose = [7,7] 
        self.initPose = [4,4,0.0191]
        self.initOrient = [-90,0,-90]
        self.betwCmdDelays = 0
        self.maxSpeed = 5


    def connectAll(self):
        self.startVrepAndConn()
        self.getHandles()

    def testDetermePuckMomvt(self):
        self.moveEPuckRandomly()
        
    def testKJLightSensors(self):
        self.moveKJuniorReadLights()
        
    def moveEPuckRandomly(self):
        for run in xrange(self.noRuns): #     print "About to start simulation for run number: ", run+1
            eCode = vrep.simxStartSimulation(self.simulID, vrep.simx_opmode_oneshot_wait)
            vrep.simxSynchronousTrigger(self.simulID)
            print "Simulation started, code", eCode #     stopRobot(self.simulID,[rightMotor,leftMotor])
            np.random.seed(64)
            #     resetRobotInitPose(initPose, self.simulID, ePuckHandle)
            for step in xrange(self.noSteps):
                rightSpeed = np.random.uniform(self.maxSpeed * 2) # - self.maxSpeed
                leftSpeed = np.random.uniform(self.maxSpeed * 2) # -maxSpeed
                eCode = vrep.simxSetJointTargetVelocity(self.simulID, self.rightMotor, rightSpeed, vrep.simx_opmode_oneshot)
                eCode = vrep.simxSetJointTargetVelocity(self.simulID, self.leftMotor, leftSpeed, vrep.simx_opmode_oneshot)
                vrep.simxSynchronousTrigger(self.simulID)
                for i in xrange(self.betwCmdDelays):
                    vrep.simxSynchronousTrigger(self.simulID) #         print "%d\t Speeds are L:%.3f\tR:%.3f" %(step, rightSpeed,leftSpeed)
            
            "Stop the robot"
            self.stopRobot(self.simulID, [self.rightMotor, self.leftMotor]) #     vrep.simxSynchronousTrigger(self.simulID)
                #     sleep(.5)
            robotPose = vrep.simxGetObjectPosition(self.simulID, self.ePuckHandle, -1, vrep.simx_opmode_oneshot_wait)[1][:2]
            vrep.simxSynchronousTrigger(self.simulID)
            print "%d: Robot is at: %.3f, %.3f Distance from target is:  %.4f" % (run, robotPose[0], robotPose[1], self.computeDistance(self.targetPose, robotPose)) #     print " About to stop simulation"
            eCode = vrep.simxStopSimulation(self.simulID, vrep.simx_opmode_oneshot_wait)
            vrep.simxSynchronousTrigger(self.simulID)
            sleep(2) #     print "Simulation stopped"
        print "Done"
        
    def moveKJuniorReadLights(self):
#         vrep.simxHandleVisionSensor???? (no remote API for this?)
        "rotate in place and print light readings"
        eCode, res, rightEyeRead = vrep.simxGetVisionSensorImage(self.simulID, self.KJrightEye, 0, vrep.simx_opmode_streaming)
        ecode, res, leftEyeRead = vrep.simxGetVisionSensorImage(self.simulID, self.KJleftEye, 0, vrep.simx_opmode_streaming)
        vrep.simxSynchronousTrigger(self.simulID)

        for step in xrange(100):
            rightSpeed = 25
            leftSpeed = rightSpeed
            eCode = vrep.simxSetJointTargetVelocity(self.simulID, self.KJrightMotor, rightSpeed, vrep.simx_opmode_oneshot_wait)
            eCode = vrep.simxSetJointTargetVelocity(self.simulID, self.KJleftMotor, leftSpeed, vrep.simx_opmode_oneshot_wait)
            vrep.simxSynchronousTrigger(self.simulID)
#             eCodeR, res, rightEyeRead = vrep.simxGetVisionSensorImage(self.simulID, self.KJrightEye, 0, vrep.simx_opmode_buffer)
#             eCodeL, res, leftEyeRead = vrep.simxGetVisionSensorImage(self.simulID, self.KJleftEye, 0, vrep.simx_opmode_buffer)
#             vrep.simxSynchronousTrigger(self.simulID)
#             print "Right eCode:\t", eCodeR,
#             print "Left eCode:\t", eCodeL
#             leftImg = np.array(leftEyeRead, np.uint8)
#             rightImg.resize(res[0],res[1],3)
#             print "Right:\t%d\tLeft:\t%d"% (sum(rightEyeRead), sum(leftEyeRead))
#         print rightImg.shape
#         plt.imshow(rightImg)#, origin="lower")

#         for run in xrange(self.noRuns):
#             np.random.seed(64)
#                 
#             for step in xrange(self.noSteps):
#                 rightSpeed = np.random.uniform(self.maxSpeed * 2) # - self.maxSpeed
#                 leftSpeed = np.random.uniform(self.maxSpeed * 2) # -maxSpeed
#                 eCode = vrep.simxSetJointTargetVelocity(self.simulID, self.KJrightMotor, rightSpeed, vrep.simx_opmode_oneshot_wait)
#                 eCode = vrep.simxSetJointTargetVelocity(self.simulID, self.KJleftMotor, leftSpeed, vrep.simx_opmode_oneshot_wait)
#                 vrep.simxSynchronousTrigger(self.simulID)
#                 eCode, res, rightEyeRead = vrep.simxGetVisionSensorImage(self.simulID, self.KJrightEye, 1, vrep.simx_opmode_buffer)
#                 ecode, res, leftEyeRead = vrep.simxGetVisionSensorImage(self.simulID, self.KJleftEye, 1, vrep.simx_opmode_buffer)
#                 vrep.simxSynchronousTrigger(self.simulID)
#                 print "Right eye reads: \t", rightEyeRead
#                 print "Left eye reads: \t", leftEyeRead


    "Clean up"
    def cleanUp(self):
        print "About to stop simulation connected to self.simulID: ", self.simulID
        vrep.simxStopSimulation(self.simulID, vrep.simx_opmode_oneshot)
        vrep.simxSynchronousTrigger(self.simulID)                    
    #     vrep.simxFinish(robotID)
        vrep.simxFinish(self.simulID)
        vrep.simxFinish(-1)
        print "Disconnected from V-REP"

    def computeDistance(self,a, b):
        return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

    def stopRobot(self,simulHandle, motorHandles):
        for motor in motorHandles:
            eCode = vrep.simxSetJointTargetVelocity(simulHandle, motor, 0, vrep.simx_opmode_oneshot)
            vrep.simxSynchronousTrigger(self.simulID)                    

    def startVrepAndConn(self):
        "Launch V-REP"
        #os.chdir(VREP_HOME)
        #subprocess.call([os.path.join(VREP_HOME,'vrep.sh'), VREP_scene_file], shell = True, cwd = VREP_HOME)
        "Close existing connections"
        vrep.simxFinish(-1)

        "Connect to Simulation"
        self.simulID = vrep.simxStart(self.robot_host,self.simulation_port,True,True, 5000,5)
        eCode = vrep.simxSynchronous(self.simulID, True)
        if eCode != 0:
            print "Could not get V-REP to synchronize operation with me"
    
        if not self.simulID == -1:
            eCode = vrep.simxStartSimulation(self.simulID, vrep.simx_opmode_oneshot)
            vrep.simxSynchronousTrigger(self.simulID)                    
            print "my SimulID is  ", self.simulID 
        else:
            sys.exit("Failed to connect to VREP simulation. Bailing out")

    def getHandles(self):
        "Get handles for epuck and motors"
#         ecodeE, self.ePuckHandle = vrep.simxGetObjectHandle(self.simulID, "ePuck", vrep.simx_opmode_oneshot_wait)
#         vrep.simxSynchronousTrigger(self.simulID)                    
#         ecodeE, self.kheperaHandle = vrep.simxGetObjectHandle(self.simulID, "K3_robot", vrep.simx_opmode_oneshot_wait)
#         vrep.simxSynchronousTrigger(self.simulID)                    
        ecodeE, self.KJuniorHandle = vrep.simxGetObjectHandle(self.simulID, "KJunior", vrep.simx_opmode_oneshot_wait)
        vrep.simxSynchronousTrigger(self.simulID)                    
#         eCodeR, self.rightMotor  = vrep.simxGetObjectHandle(self.simulID, "ePuck_rightJoint", vrep.simx_opmode_oneshot_wait)
#         vrep.simxSynchronousTrigger(self.simulID)                    
#         eCodeL, self.leftMotor   = vrep.simxGetObjectHandle(self.simulID, "ePuck_leftJoint", vrep.simx_opmode_oneshot_wait)
#         vrep.simxSynchronousTrigger(self.simulID)
        eCodeR, self.KJrightMotor  = vrep.simxGetObjectHandle(self.simulID, "KJunior_motorRight", vrep.simx_opmode_oneshot_wait)
        vrep.simxSynchronousTrigger(self.simulID)                    
        eCodeL, self.KJleftMotor   = vrep.simxGetObjectHandle(self.simulID, "KJunior_motorLeft", vrep.simx_opmode_oneshot_wait)
        vrep.simxSynchronousTrigger(self.simulID)                    
        eCodeR, self.KJrightEye  = vrep.simxGetObjectHandle(self.simulID, "KJ_RightEye1", vrep.simx_opmode_oneshot_wait)
        vrep.simxSynchronousTrigger(self.simulID)                    
        eCodeL, self.KJleftEye   = vrep.simxGetObjectHandle(self.simulID, "KJ_LeftEye1", vrep.simx_opmode_oneshot_wait)
        vrep.simxSynchronousTrigger(self.simulID)                    
                   

        if (self.KJrightMotor == 0 or self.KJleftMotor == 0 or self.KJrightEye == 0 or self.KJleftEye == 0):
            cleanUp()
            sys.exit("Exiting:  Could not connect to motors or sensors")
        else:
            print " I am connected to Right Motor: %d, leftMotor: %d, Right eye: %d, Left eye: %d" % (self.KJrightMotor, 
                                                                                                      self.KJleftMotor,
                                                                                                      self.KJrightEye,
                                                                                                      self.KJleftEye)
    


if __name__ == "__main__":
    test = VREPTests(noSteps=50)
    test.connectAll()
#     test.testDetermePuckMomvt()
    test.testKJLightSensors()
    test.cleanUp()