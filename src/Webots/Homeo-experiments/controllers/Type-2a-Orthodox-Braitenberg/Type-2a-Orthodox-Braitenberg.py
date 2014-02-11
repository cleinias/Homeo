#################################################################
# First test controlling a khepera robot in a simple Webots world
# simulating a straightforward Braitenberg-like type-2a vehicle:
#
# 2 sensors and 2 motors, with NON crossed connections
#
# Stefano Franchi 2014
#################################################################
from __future__ import division
from controller import *
import sys

class Vehicle2 (DifferentialWheels):
  counter = 1
  def run(self):
    self.leftEye = self.getLightSensor('ls0')
    self.rightEye = self.getLightSensor('ls1')
    self.leftEye.enable(32)
    self.rightEye.enable(32)
    counter = 1
    maxSpeed = 100
    maxLight = 1200
    maxDelta = 0

    while (self.step(32) != -1):
      # Read the sensors:
      # Take the complement of sensors' values, since webots' sensors return a value close to zero
      # for maximum intensity and values close to maxLight for minimum intensity 
      rightLightValue = maxLight - self.rightEye.getValue()
      leftLightValue = maxLight - self.leftEye.getValue()
      # Cross sensor data to same side motor, as in a straightforward
      # Braitenberg type-2a vehicle. 
      # Also, scale sensor values to speed range :
      leftSpeed = leftLightValue * (maxSpeed/maxLight)
      rightSpeed = rightLightValue * (maxSpeed/maxLight)

      #=========================================================================
      #
      #     "Debugging info"
      #
      # speedDelta = abs(rightSpeed - leftSpeed)
      # if speedDelta > maxDelta:
      #     maxDelta = speedDelta
      # print "Right eye: %d Left eye: %d Right Speed %f Left Speed %f Speed delta is %f Max so far is %f\r" % (rightLightValue,
      #                                                                    leftLightValue,
      #                                                                    rightSpeed,
      #                                                                    leftSpeed,
      #                                                                    speedDelta,
      #                                                                    maxDelta)
      # counter = counter + 1
      #=========================================================================
      self.setSpeed(leftSpeed, rightSpeed)

robot = Vehicle2()
robot.run()

