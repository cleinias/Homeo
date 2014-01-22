'''
# File:          LightMover.py
# Date:          12/18/2013
# Description:   A controller for a supervisor 
#                to move a light around
# Author:        Stefano Franchi
# Modifications: 
Created on Jan 10, 2014

@author: stefano
'''

from controller import Supervisor
from random import random

class LightMover(Supervisor):
    def run(self):
     "Main loop"
     simulationStep = 32
     simMinute = 60000  # in milliseconds. 1 minute = 60000
     timeInterval = int(0.1 * simMinute)
     print timeInterval
     
     "Get position of the first light source"
     light = self.getFromDef("LIGHT1")
     lightPosField = light.getField("location")
     initialLightPos = lightPosField.getSFVec3f()
     lightPos = initialLightPos
     print "First point light at %f \t %f\n" % (lightPos[0],
                                                lightPos[2])
     while True:
        "Perform a simulation step"
        "and leave the loop when the simulation is over"
        self.step(timeInterval)  #wait for the time interval to elapse
        newX = (lightPos[0]+(random()*0.1))%10
        newY = (lightPos[2]+(random()*0.1))%10
        lightPosField.setSFVec3f([newX,lightPos[1], newY])  #move light
        print "Light source is currently at %f\t %f" % (lightPos[0],
                                                        lightPos[2])

        lightPos =  lightPosField.getSFVec3f()
        if self.step(simulationStep) == -1:
           print "Light source is currently at %f\t %f" % (lightPos[0],
                                                           lightPos[2])
           print " Moving source back to original position"
           lightPosField.setSFVec3f([initialLightPos[0],initialLightPos[1], initialLightPos[2]])  #move light

           
           break

controller = LightMover()
controller.run()
