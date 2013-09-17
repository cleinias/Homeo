'''
Created on Sep 17, 2013

@author: stefano
'''

from RobotSimulator.WebotsTCPClient import WebotsTCPClient
from RobotSimulator.Transducer import  *

testClient = WebotsTCPClient()
testClient._clientPort = 10020
testSocket = testClient.getClientSocket()
rightWheel = WebotsDiffMotorTCP('right')
rightWheel.robotSocket = testSocket
rightWheel.funcParameters = 10

leftWheel = WebotsDiffMotorTCP('left')
leftWheel.robotSocket = testSocket
leftWheel.funcParameters = 10

rightWheel.act()
leftWheel.act()

leftEye = WebotsLightSensorTCP(0)
rightEye = WebotsLightSensorTCP(1)
leftEye.robotSocket = testSocket
rightEye.robotSocket = testSocket

print "rightEye sees: ", rightEye.read()
print "leftEye sees: ", leftEye.read()


testClient.close()

if __name__ == "__main__":
    pass