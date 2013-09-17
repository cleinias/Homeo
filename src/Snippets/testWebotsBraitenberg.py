'''
Created on Sep 17, 2013
Test connection to Webots with a simlation of a Braitenberg type 2 vehicle
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


leftSensor = WebotsLightSensorTCP(1)
rightSensor = WebotsLightSensorTCP(0)
leftSensor.robotSocket = testSocket
rightSensor.robotSocket = testSocket


for i in xrange(100):
    """Convert light values into a sensed value going from 
       10 (max value) to 0.01 (min value)
    """
    r =  rightSensor.read()
    if r  == 0:
        right_eye = 1
    else:
        right_eye = r
    
    l = leftSensor.read()
    if l == 0:
        left_eye = 1
    else:
        left_eye = l
    
    """ Scale perceived lights to 0 - 100 and set them to speed of opposite wheel"""
    rightSpeed = left_eye / 100
    leftSpeed = right_eye / 100
    rightWheel.funcParameters = rightSpeed
    leftWheel.funcParameters = leftSpeed
    rightWheel.act()
    leftWheel.act()    
    print "right_eye: %d, left_eye: %d, rightSpeed: %d, leftSpeed: %d" % (right_eye,
                                                                          rightSpeed,
                                                                          left_eye,
                                                                          leftSpeed)

testClient.close()