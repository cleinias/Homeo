'''
Created on Oct 3, 2013

Test connection to Webots with a simulation of a Braitenberg type 1 vehicle
It uses a standard khepera 2 robot with two sensors, but it averages 
the readings and it always give the same speed command to both motors
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
leftSensorMaxRange = leftSensor.range()[1]
rightSensorMaxRange = rightSensor.range()[1]
leftWheelMaxRange = rightWheelMaxRange = rightWheel.range()[1]
DAMPING = .1

for i in range(1000):
    """Convert light values into a sensed value going from motors' minSpeed to maxSpeed.
       Notice that minSpeed is always = -maxSpeed in Webots, and the two motors of a differential
       robots have identical minSpeed and MaxSpeed.
       Sensors, instead, always go from 0 to a maxRange    
    """
    r =  rightSensor.read()
    right_eye = (r * ((rightWheelMaxRange * 2)/rightSensorMaxRange))  - rightWheelMaxRange
    
    l = leftSensor.read()
    left_eye = (l * ((leftWheelMaxRange * 2 )/leftSensorMaxRange)) - leftWheelMaxRange
    
    
    """ Scale perceived lights by a damping factor set them to speed of opposite wheel"""
    rightSpeed = leftSpeed = ((left_eye + right_eye) /2)  * DAMPING

    
    rightWheel.funcParameters = rightSpeed
    leftWheel.funcParameters = leftSpeed
    rightWheel.act()
    leftWheel.act()    
    print("r_sensor: %d, right_eye: %d, l_sensor: %d, left_eye: %d, rightSpeed: %d, leftSpeed: %d" % (
                                                                          r,
                                                                          right_eye,
                                                                          l,
                                                                          left_eye,
                                                                          rightSpeed,
                                                                          leftSpeed))

testClient.close()