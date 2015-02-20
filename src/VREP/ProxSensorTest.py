"Testing V-Rep proximity sensors"

import vrep
import os, sys

# from vrepConst import simx_opmode_oneshot, simx_opmode_oneshot_wait
from time import sleep



class VREPTests(object):
    
    def __init__(self, noSteps = 5000, noRuns=5):
        "Parameters"
        self.simulation_port = 19997
        self.robot_host = '127.0.0.1'
        self.noRuns = noRuns
        self.noSteps = noSteps
        self.targetPose = [7,7] 
        self.initPose = [4,4,0.0191]
        self.initOrient = [-90,0,-90]
        self.betwCmdDelays = 0
        self.maxSpeed = 5


    def connectAll(self):
        self.VREPConnect()
        self.getHandles()

    def VREPConnect(self):
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
            

    def moveKJuniorReadProxSensors(self):
        "slowly move forward and print normal vector readings"
 
        rightInput = vrep.simxReadProximitySensor(self.simulID, self.KJrightEye, vrep.simx_opmode_streaming)
        leftInput = vrep.simxReadProximitySensor(self.simulID, self.KJleftEye, vrep.simx_opmode_streaming)
        vrep.simxSynchronousTrigger(self.simulID)
        print "Proximity sensor readings error codes: ", rightInput[0],leftInput[0]
        for step in xrange(self.noSteps):
            rightSpeed = 10
            leftSpeed = rightSpeed
            eCode = vrep.simxSetJointTargetVelocity(self.simulID, self.KJrightMotor, rightSpeed, vrep.simx_opmode_oneshot_wait)
            eCode = vrep.simxSetJointTargetVelocity(self.simulID, self.KJleftMotor, leftSpeed, vrep.simx_opmode_oneshot_wait)
            vrep.simxSynchronousTrigger(self.simulID)
            rightInput = vrep.simxReadProximitySensor(self.simulID, self.KJrightEye, vrep.simx_opmode_buffer)
            vrep.simxSynchronousTrigger(self.simulID)
            leftInput = vrep.simxReadProximitySensor(self.simulID, self.KJleftEye, vrep.simx_opmode_buffer)
            vrep.simxSynchronousTrigger(self.simulID)
            print "Left-->err:%s - Detct'd: %s\t%s\t\t\tRight--> err:%s - Detct'd: %s\t%s" % (leftInput[0],
                                                                                              leftInput[3],
                                                                                              leftInput[4],
                                                                                              rightInput[0],
                                                                                              rightInput[3],
                                                                                              rightInput[4])

            sleep(.2)
                                
    
    def cleanUp(self):
        print "About to stop simulation connected to self.simulID: ", self.simulID
        vrep.simxStopSimulation(self.simulID, vrep.simx_opmode_oneshot)
        vrep.simxSynchronousTrigger(self.simulID)                    
        vrep.simxFinish(self.simulID)
        vrep.simxFinish(-1)
        print "Disconnected from V-REP"

    def getHandles(self):
        "Get handles for KJunior, motors, and sensors"
        ecodeE, self.KJuniorHandle = vrep.simxGetObjectHandle(self.simulID, "KJunior", vrep.simx_opmode_oneshot_wait)
        vrep.simxSynchronousTrigger(self.simulID)
                            
        eCodeR, self.KJrightMotor  = vrep.simxGetObjectHandle(self.simulID, "KJunior_motorRight", vrep.simx_opmode_oneshot_wait)
        vrep.simxSynchronousTrigger(self.simulID)                 
           
        eCodeL, self.KJleftMotor   = vrep.simxGetObjectHandle(self.simulID, "KJunior_motorLeft", vrep.simx_opmode_oneshot_wait)
        vrep.simxSynchronousTrigger(self.simulID)      
                      
        eCodeR, self.KJrightEye  = vrep.simxGetObjectHandle(self.simulID, "KJunior_proxSensor4", vrep.simx_opmode_oneshot_wait)
        vrep.simxSynchronousTrigger(self.simulID)     
                       
        eCodeL, self.KJleftEye   = vrep.simxGetObjectHandle(self.simulID, "KJunior_proxSensor2", vrep.simx_opmode_oneshot_wait)
        vrep.simxSynchronousTrigger(self.simulID)    
                                 
        eCode,self.targetID =  vrep.simxGetObjectHandle(self.simulID,"Sphere", vrep.simx_opmode_oneshot_wait)
        vrep.simxSynchronousTrigger(self.simulID)                    
         

        if (self.KJrightMotor == 0 or self.KJleftMotor == 0 or self.KJrightEye == 0 or self.KJleftEye == 0):
            self.cleanUp()
            sys.exit("Exiting:  Could not connect to motors or sensors")
        else:
            print "Connected to Right Motor: %d, leftMotor: %d, Right eye: %d, Left eye: %d, with target ID:%d" % (self.KJrightMotor, 
                                                                                                                   self.KJleftMotor,
                                                                                                                   self.KJrightEye,
                                                                                                                   self.KJleftEye,
                                                                                                                   self.targetID)
    
if __name__ == "__main__":
    test = VREPTests(noSteps=30)
    test.connectAll()
    test.moveKJuniorReadProxSensors()
    test.cleanUp()