#################################################################
# First test controlling a khepera robot in a simple Webots world
# simulating a Bretinteberg environment with a type 2 vehicle
#
# Stefano Franchi 2013
#################################################################

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
 
    while (self.step(32) != -1):
      # Read the sensors, like:
      rightLightValue = self.rightEye.getValue()
      leftLightValue = self.leftEye.getValue()

      # Process sensor data here
      print "%u Right eye: %d Left eye: %d \r" % (counter,
                                               rightLightValue,
                                               leftLightValue)
      # Enter here functions to send actuator commands, like:
      self.setSpeed(-1,1)
      counter = counter + 1

    # Enter here exit cleanup code

robot = Vehicle2()
robot.run()
