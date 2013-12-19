# File:          supervisor-trajectory.py
# Date:          12/18/2013
# Description:   A simple controller for the supervisor to record a robot's trajectory
# Author:        Stefnao Franchi
# Modifications: 

# You may need to import some classes of the controller module. Ex:
#  from controller import Robot, LED, DistanceSensor
#
# or to import the entire module. Ex:
#  from controller import *
from controller import Supervisor

# Here is the main class of your controller.
# This class defines how to initialize and how to run your controller.
# Note that this class derives Robot and so inherits all its functions
class supervisorTrajectory(Supervisor):
  
  # User defined function for initializing and running
  # the supervisor-trajectory class
  def run(self):
     "Main loop"
     "Get the translation node of the robot by its definition"
     myKhepera = self.getFromDef("KHEPERA")
     transField = myKhepera.getField("translation")
     while True:
        "Perform a simulation step of 32 milliseconds"
        "and leave the loop when the simulation is over"
        if self.step(32) == -1:
           break
        "Get the robot's translation field"
        pos = myKhepera.getPosition()  
        trans = transField.getSFVec3f()
        "Print the translation values for x, y, and z out to console"
        print "x:%f y:%f z:%f"% (trans[0], trans[1], trans[2])
        "Print the position"
        print "position:",  pos
        self.step(32);

# The main program starts from here

# This is the main program of your controller.
# It creates an instance of your Robot subclass, launches its
# function(s) and destroys it at the end of the execution.
# Note that only one instance of Robot should be created in
# a controller program.
controller = supervisorTrajectory()
controller.run()
