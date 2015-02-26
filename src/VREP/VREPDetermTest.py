'''
Created on Feb 22, 2015

@author: stefano

Script that tests V-REP deterministic runs.
Runs V-REP repeatedly with a deterministic
series of random motor commands over TCP/IP

Include also related tests (such as light readings, Braitenberg-like simulations)

Assumes:
1. V-REP world ("Scene") "$HOMEO/src/VREP/Khepera-J-Proximity-only.SF.ttt" is already running
2. V-REP listens on ports 19997 (for main control)
3. The V-REP robot to be controlled is called "Khepera"
4. Other V-REP assumptions about lights and other features of the V-REP world (see method comments and V-REP world description)  
5. A SimsData subdir exists at /home/stefano/Documents/Projects/Homeostat/Simulator/Python-port/Homeo/SimulationsData
'''


import vrep
from Helpers.SimulationThread import SimulationThread
import math
import numpy as np
# import matplotlib.pyplot as plt
import os, sys
import subprocess
import datetime
from numpy import dot, arccos, degrees
from math import pi
from numpy.linalg import norm
from time import sleep,time, strftime,localtime
from Helpers.General_Helper_Functions import scaleTo
from ctypes import c_ubyte

def distance(pointA3D, pointB3D):
    "Return Euclidean distance"    
    return math.sqrt((pointA3D[0]-pointB3D[0])**2 + (pointA3D[1]-pointB3D[1])**2 + (pointA3D[2]-pointB3D[2])**2)

def distanceFromOrig(point3D):
    "Return Euclidean distance"    
    return math.sqrt((0 - point3D[0])**2 + (0 - point3D[1])**2 + (0 - point3D[2])**2)

def clip(clipValue,minV,maxV):
    if clipValue < minV:
        return minV
    elif clipValue > maxV:
        return maxV
    return clipValue

def asByteArray(m_string):
    return (c_ubyte * len(m_string)).from_buffer_copy(m_string)

class VREPTests(object):
    
    def __init__(self, noSteps = 5000, noRuns=5, robotName = "Khepera"):
        "Parameters"
        
        #VREP_scene_file ="/home/stefano/Documents/Projects/Homeostat/Simulator/Python-port/Homeo/src/VREP/Khepera-J-Proximity-only.SF.ttt" 
        self.simulation_port = 19997
        self.trajectoryPort = 19998
        self.robot_host = '127.0.0.1'
        self.VREP_HOME = '/home/stefano/builds/from-upstream-sources/V-REP_PRO_EDU_V3_2_0_64_Linux/'
        self.robotName = robotName
        self.noRuns = noRuns
        self.noSteps = noSteps
        self.targetPose = [7,7] 
        self.initPose = [4,4,0.0191]
        self.initOrient = [-90,0,-90]
        self.betwCmdDelays = 0
        self.maxSpeed = 50
        self.trajStateSignalName = "HOMEO_SIGNAL_"+ self.robotName + "_TRAJECTORY_RECORDER"
        
        
    def startTrajRecorder(self):
        pass

    def connectAll(self):
        self.connect()
        self.getHandles()
#         self.startTrajRecorder()

    def testDetermMomvt(self):
        self.moveRandomly()
        
    def testLightSensors(self):
        self.moveAndReadLights()
    
    def moveReadLights(self):
        self.moveAndReadProxSensors()
                
    def moveRandomly(self):
        "Set trajectory data directory and communicate to V-REP"
        HOMEODIR = '/home/stefano/Documents/Projects/Homeostat/Simulator/Python-port/Homeo/'
        dataDir = 'SimsData-'+strftime("%Y-%m-%d-%H-%M-%S", localtime(time()))
        simsDataDir = os.path.join(HOMEODIR,"SimulationsData",dataDir)
        os.mkdir(simsDataDir)
        print "Saving to: ", simsDataDir
        e = vrep.simxSetStringSignal(self.simulID,"HOMEO_SIGNAL_SIM_DATA_DIR" ,asByteArray(simsDataDir), vrep.simx_opmode_oneshot_wait)
        vrep.simxSynchronousTrigger(self.simulID)
        print "Message sent, error code: ", e
        for run in xrange(self.noRuns):
            eCode = vrep.simxStartSimulation(self.simulID, vrep.simx_opmode_oneshot_wait)
            vrep.simxSynchronousTrigger(self.simulID)
            e = vrep.simxSetStringSignal(self.simulID,"HOMEO_SIGNAL_SIM_DATA_DIR" ,asByteArray(simsDataDir), vrep.simx_opmode_oneshot_wait)
            vrep.simxSynchronousTrigger(self.simulID)
            print "Simulation started: run number %d, error code: %d"% (run+1, eCode)
            "Wait until simulation is ready, otherwise we will miss a few movement commands"    
#             sleep(2) 
            np.random.seed(64)
            #     resetRobotInitPose(initPose, self.simulID, ePuckHandle)
            eCode = vrep.simxSetStringSignal(self.simulID, self.trajStateSignalName, asByteArray("NEWFILE"), vrep.simx_opmode_oneshot_wait)
            vrep.simxSynchronousTrigger(self.simulID)
            if eCode == 0:
                print "Starting a new trajectory file"
            else:
                print "ERROR: Could not start a new trajectory file" 
            for step in xrange(self.noSteps):
                timeStart = time()
                rightSpeed = np.random.uniform(self.maxSpeed * 2) # - self.maxSpeed
                leftSpeed = np.random.uniform(self.maxSpeed * 2) # -maxSpeed
                eCode = vrep.simxSetJointTargetVelocity(self.simulID, self.rightMotor, rightSpeed, vrep.simx_opmode_oneshot_wait)
                vrep.simxSynchronousTrigger(self.simulID)
                eCode = vrep.simxSetJointTargetVelocity(self.simulID, self.leftMotor, leftSpeed, vrep.simx_opmode_oneshot_wait)
                vrep.simxSynchronousTrigger(self.simulID)
                for i in xrange(self.betwCmdDelays):
                    vrep.simxSynchronousTrigger(self.simulID)
                timeElapsed = time() - timeStart
            "Stop the robot"
            self.stopRobot(self.simulID, [self.rightMotor, self.leftMotor])
            eCode = vrep.simxSetStringSignal(self.simulID, self.trajStateSignalName, asByteArray("SAVE"), vrep.simx_opmode_oneshot_wait)
            vrep.simxSynchronousTrigger(self.simulID)
            if eCode == 0:
                print "Saving trajectory file"
            else:
                print "ERROR: Could not save a new trajectory file" 

            sleep(.5)
            robotPose = vrep.simxGetObjectPosition(self.simulID, self.robotHandle, -1, vrep.simx_opmode_oneshot_wait)[1][:2]
            vrep.simxSynchronousTrigger(self.simulID)
            print "%d: Robot is at: %.3f, %.3f Distance from target is:  %.4f. Run took exactly %.3f seconds" % (run, 
                                                                                                                 robotPose[0], 
                                                                                                                 robotPose[1], 
                                                                                                                 self.computeDistance(self.targetPose, robotPose),
                                                                                                                 timeElapsed) #
            eCode = vrep.simxStopSimulation(self.simulID, vrep.simx_opmode_oneshot_wait)
            vrep.simxSynchronousTrigger(self.simulID)
            sleep(1) 
#             eCode = vrep.simxStartSimulation(self.simulID, vrep.simx_opmode_oneshot_wait)
#             vrep.simxSynchronousTrigger(self.simulID)
        eCode = vrep.simxSetStringSignal(self.simulID, self.trajStateSignalName, asByteArray("CLOSEFILE"), vrep.simx_opmode_oneshot_wait)
        vrep.simxSynchronousTrigger(self.simulID)
        if eCode == 0:
            print "Starting a new trajectory file"
        else:
            print "ERROR: Could not close a new trajectory file" 
        print "Done"
        
    def moveAndReadLights(self):
        "rotate in place and print light readings"
        eCode, res, rightEyeRead = vrep.simxGetVisionSensorImage(self.simulID, self.rightEye, 0, vrep.simx_opmode_streaming)
        ecode, res, leftEyeRead = vrep.simxGetVisionSensorImage(self.simulID, self.leftEye, 0, vrep.simx_opmode_streaming)
        vrep.simxSynchronousTrigger(self.simulID)

        for step in xrange(self.noSteps):
            rightSpeed = 25
            leftSpeed = rightSpeed
            eCode = vrep.simxSetJointTargetVelocity(self.simulID, self.rightMotor, rightSpeed, vrep.simx_opmode_oneshot_wait)
            eCode = vrep.simxSetJointTargetVelocity(self.simulID, self.leftMotor, leftSpeed, vrep.simx_opmode_oneshot_wait)
            vrep.simxSynchronousTrigger(self.simulID)
            eCodeR, res, rightEyeRead = vrep.simxGetVisionSensorImage(self.simulID, self.rightEye, 0, vrep.simx_opmode_buffer)
            eCodeL, res, leftEyeRead  = vrep.simxGetVisionSensorImage(self.simulID, self.leftEye,  0, vrep.simx_opmode_buffer)
            vrep.simxSynchronousTrigger(self.simulID)
#             print "Right eCode:\t", eCodeR,
#             print "Left eCode:\t", eCodeL
#             leftImg = np.array(leftEyeRead, np.uint8)
#             rightImg.resize(res[0],res[1],3)
            print "Right:\t%d, %d\tLeft:\t%d, %d"% (len(rightEyeRead),sum(rightEyeRead), len(leftEyeRead),sum(leftEyeRead))
#         print rightImg.shape
#         plt.imshow(rightImg)#, origin="lower")

#         for run in xrange(self.noRuns):
#             np.random.seed(64)
#                 
#             for step in xrange(self.noSteps):
#                 rightSpeed = np.random.uniform(self.maxSpeed * 2) # - self.maxSpeed
#                 leftSpeed = np.random.uniform(self.maxSpeed * 2) # -maxSpeed
#                 eCode = vrep.simxSetJointTargetVelocity(self.simulID, self.rightMotor, rightSpeed, vrep.simx_opmode_oneshot_wait)
#                 eCode = vrep.simxSetJointTargetVelocity(self.simulID, self.leftMotor, leftSpeed, vrep.simx_opmode_oneshot_wait)
#                 vrep.simxSynchronousTrigger(self.simulID)
#                 eCode, res, rightEyeRead = vrep.simxGetVisionSensorImage(self.simulID, self.rightEye, 1, vrep.simx_opmode_buffer)
#                 ecode, res, leftEyeRead = vrep.simxGetVisionSensorImage(self.simulID, self.leftEye, 1, vrep.simx_opmode_buffer)
#                 vrep.simxSynchronousTrigger(self.simulID)
#                 print "Right eye reads: \t", rightEyeRead
#                 print "Left eye reads: \t", leftEyeRead

    def moveAndReadProxSensors(self):
        "rotate in place and print sensor distance and normal vector readings"
 
        for step in xrange(self.noSteps):
            if step>self.noSteps / 2:
                rightSpeed = -1
                leftSpeed = -rightSpeed
            else:
                rightSpeed = 1
                leftSpeed = -rightSpeed
            eCode = vrep.simxSetJointTargetVelocity(self.simulID, self.rightMotor, rightSpeed, vrep.simx_opmode_oneshot_wait)
            eCode = vrep.simxSetJointTargetVelocity(self.simulID, self.leftMotor, leftSpeed, vrep.simx_opmode_oneshot_wait)
            vrep.simxSynchronousTrigger(self.simulID)
            rightInput = vrep.simxReadProximitySensor(self.simulID, self.rightEye, vrep.simx_opmode_oneshot_wait)
            vrep.simxSynchronousTrigger(self.simulID)
            leftInput = vrep.simxReadProximitySensor(self.simulID, self.leftEye, vrep.simx_opmode_oneshot_wait)
            vrep.simxSynchronousTrigger(self.simulID)
            print "Left-->err:%s - Detct'd: %s\t%s\t\tRight--> err:%s - Detct'd: %s\t\t\t%s" % (leftInput[0],
                                                                                        leftInput[3],
                                                                                        leftInput[2],
                                                                                        rightInput[0],
                                                                                        rightInput[3],
                                                                                        rightInput[2])

            sleep(.1)
        self.stopRobot(self.simulID,[self.rightMotor,self.leftMotor])
        vrep.simxSynchronousTrigger(self.simulID)


                
    def braiten1a(self):
        "slowly move forward and print normal vector readings"
        intens = 50
        ambientIntens = 0
        attVect = [0,0,1]
 
        print "Proximity sensor readings error codes: "
        for step in xrange(self.noSteps):
            rightInput = vrep.simxReadProximitySensor(self.simulID, self.rightEye, vrep.simx_opmode_oneshot_wait)
            vrep.simxSynchronousTrigger(self.simulID)
            leftInput = vrep.simxReadProximitySensor(self.simulID, self.leftEye, vrep.simx_opmode_oneshot_wait)
            vrep.simxSynchronousTrigger(self.simulID)
            centerInput = vrep.simxReadProximitySensor(self.simulID, self.KJcenterEye, vrep.simx_opmode_oneshot_wait)
            vrep.simxSynchronousTrigger(self.simulID)
            angle = degrees(self.angleBetVecs([0,0,1], centerInput[2]))
            lightReading = self.irradAtSensor(intens, ambientIntens, centerInput[2], attVect)
            print "Center-->err:%s - Detct'd: %s\tAngle:%.3f\tIrrad:%.3f\tNorm: %.3f\tVector:%s\t" % (centerInput[0],
                                                                                                      centerInput[3],
                                                                                                      angle,
                                                                                                      lightReading,
                                                                                                      norm(centerInput[2]),
                                                                                                      centerInput[2])
            eCode = vrep.simxSetJointTargetVelocity(self.simulID, self.rightMotor, lightReading, vrep.simx_opmode_oneshot_wait)
            eCode = vrep.simxSetJointTargetVelocity(self.simulID, self.leftMotor,  lightReading, vrep.simx_opmode_oneshot_wait)
            vrep.simxSynchronousTrigger(self.simulID)


            sleep(0)

    def braiten1b(self):
        "slowly move forward and print normal vector readings"
        intens = 100
        ambientIntensRatio = 0.2
        attVect = [0,0,pi *4]

        for step in xrange(self.noSteps):
            rightInput = vrep.simxReadProximitySensor(self.simulID, self.rightEye, vrep.simx_opmode_oneshot_wait)
            vrep.simxSynchronousTrigger(self.simulID)
            leftInput = vrep.simxReadProximitySensor(self.simulID, self.leftEye, vrep.simx_opmode_oneshot_wait)
            vrep.simxSynchronousTrigger(self.simulID)
            centerInput = vrep.simxReadProximitySensor(self.simulID, self.KJcenterEye, vrep.simx_opmode_oneshot_wait)
            vrep.simxSynchronousTrigger(self.simulID)
            angle = degrees(self.angleBetVecs([0,0,1], centerInput[2]))
            lightReading = self.irradAtSensor(intens, ambientIntensRatio, centerInput[2], attVect)
            print "Center-->err:%s - Detct'd: %s\tAngle:%.3f\tIrrad:%.3f\tNorm: %.3f\tVector:%s\t" % (centerInput[0],
                                                                                                      centerInput[3],
                                                                                                      angle,
                                                                                                      lightReading,
                                                                                                      norm(centerInput[2]),
                                                                                                      centerInput[2])
            eCode = vrep.simxSetJointTargetVelocity(self.simulID, self.rightMotor, 1/lightReading, vrep.simx_opmode_oneshot_wait)
            eCode = vrep.simxSetJointTargetVelocity(self.simulID, self.leftMotor,  1/lightReading, vrep.simx_opmode_oneshot_wait)
            vrep.simxSynchronousTrigger(self.simulID)
            sleep(0)
            
            
    def braiten2a(self, targetID):
        "Seek light source"
        intens = 50
        ambientIntensRatio = .2
        attVect = [0,0,1]
        for step in xrange(self.noSteps):
            rightInput = vrep.simxReadProximitySensor(self.simulID, self.rightEye, vrep.simx_opmode_oneshot_wait)
            vrep.simxSynchronousTrigger(self.simulID)
            leftInput = vrep.simxReadProximitySensor(self.simulID, self.leftEye, vrep.simx_opmode_oneshot_wait)
            vrep.simxSynchronousTrigger(self.simulID)
            rightAngle = degrees(self.angleBetVecs([0,0,1], rightInput[2]))
            leftAngle = degrees(self.angleBetVecs([0,0,1], rightInput[2]))

            if leftInput[3] == targetID:
                leftLightReading = self.irradAtSensor(intens, ambientIntensRatio, leftInput[2], attVect)
            else:
                leftLightReading = 0
            if rightInput[3] == targetID:
                rightLightReading = self.irradAtSensor(intens, ambientIntensRatio, rightInput[2], attVect)
            else:
                rightLightReading = 0

#             print "Left sees: %s\tAngle:%.3f\tIrrad:%.2f\tSpeed:%.2f\tNorm: %.3f\tVector:%s\tRight sees: %s\tAngle:%.3f\tIrrad:%.3fSpeed:%.2f\t\tNorm: %.3f\tVector:%s\t" % (leftInput[3],
#                                                                                              leftAngle,
#                                                                                              leftLightReading,
#                                                                                              clip(leftLightReading, 0, self.maxSpeed),
#                                                                                              norm(leftInput[2]),
#                                                                                              leftInput[2],
#                                                                                              rightInput[3],
#                                                                                              rightAngle,
#                                                                                              rightLightReading,
#                                                                                              clip(rightLightReading, 0, self.maxSpeed),
#                                                                                              norm(rightInput[2]),
#                                                                                              rightInput[2])
              
            eCode = vrep.simxSetJointTargetVelocity(self.simulID, self.rightMotor, clip(leftLightReading,0,self.maxSpeed), vrep.simx_opmode_oneshot_wait)
            eCode = vrep.simxSetJointTargetVelocity(self.simulID, self.leftMotor,  clip(rightLightReading,0, self.maxSpeed), vrep.simx_opmode_oneshot_wait)
            vrep.simxSynchronousTrigger(self.simulID)
            sleep(0)
            
        
    
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

    def connect(self):
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
        ecodeE, self.robotHandle = vrep.simxGetObjectHandle(self.simulID, "Khepera", vrep.simx_opmode_oneshot_wait)
        vrep.simxSynchronousTrigger(self.simulID)                    
        eCodeR, self.rightMotor  = vrep.simxGetObjectHandle(self.simulID, "Khepera_motorRight", vrep.simx_opmode_oneshot_wait)
        vrep.simxSynchronousTrigger(self.simulID)                    
        eCodeL, self.leftMotor   = vrep.simxGetObjectHandle(self.simulID, "Khepera_motorLeft", vrep.simx_opmode_oneshot_wait)
        vrep.simxSynchronousTrigger(self.simulID)                    
        eCodeR, self.rightEye  = vrep.simxGetObjectHandle(self.simulID, "Khepera_proxSensor4", vrep.simx_opmode_oneshot_wait)
        vrep.simxSynchronousTrigger(self.simulID)                    
        eCodeL, self.leftEye   = vrep.simxGetObjectHandle(self.simulID, "Khepera_proxSensor2", vrep.simx_opmode_oneshot_wait)
        vrep.simxSynchronousTrigger(self.simulID)                    
          
        eCodeL, self.KJcenterEye   = vrep.simxGetObjectHandle(self.simulID, "Khepera_proxSensor3", vrep.simx_opmode_oneshot_wait)
        vrep.simxSynchronousTrigger(self.simulID)    
         
        eCode,self.targetID =  vrep.simxGetObjectHandle(self.simulID,"TARGET", vrep.simx_opmode_oneshot_wait)
        vrep.simxSynchronousTrigger(self.simulID)
        
                    


        if (self.rightMotor == 0 or self.leftMotor == 0 or self.rightEye == 0 or self.leftEye == 0):
            self.cleanUp()
            sys.exit("Exiting:  Could not connect to motors or sensors")
        else:
            print " I am connected to Right Motor: %d, leftMotor: %d, Right eye: %d, Left eye: %d, and my target has ID:%d" % (self.rightMotor, 
                                                                                                      self.leftMotor,
                                                                                                      self.rightEye,
                                                                                                      self.leftEye,
                                                                                                      self.targetID)
    
    def angleBetVecs(self,vecA,vecB):
        vecA_norm = vecA/norm(vecA)
        vecB_norm = vecB/norm(vecB)
        return arccos(dot(vecA_norm,vecB_norm))
    
    def irradAtSensor(self,intens,ambIntensRatio,vecToLight, attenVect):
        """Compute the irradiance at the light sensor surface
           Intens is the directional component of the light intensity, 
           ambIntensRatio is ambient component (not subject to attenuation) of the light's intensity. Must be in [0,1] 
           vecToLight is the 3D vector to the light source in the sensor's frame of reference
           attenVect is a 3 element vector with the direct, linear, and quadratic attenuation coefficients  """
        cosAngle = (dot([0,0,1],vecToLight)/norm(vecToLight))
        directIntens = (intens * (1-ambIntensRatio)) * cosAngle
        distance = norm(vecToLight)
        attenuation = 1/(attenVect[0]+(attenVect[1]*distance)+(attenVect[2]*distance**2))
        return (directIntens + (intens*ambIntensRatio)) * attenuation


if __name__ == "__main__":
    test = VREPTests(noSteps=10, noRuns=1)
    test.connectAll()
    test.testDetermMomvt()
#     test.testLightSensors()
#     test.moveReadLights()
#     test.braiten2a(test.targetID)
    test.cleanUp()
