# File:          supervisorTrajectory.py
# Date:          12/18/2013
# Description:   A simple controller for the supervisor 
#                to record a robot's trajectory to file
# Author:        Stefano Franchi
# Modifications: 

from controller import Supervisor
import time
import os

class supervisorTrajectory(Supervisor):
    def run(self):
     "Main loop"
     "Get the translation node of the robot by its definition"
     curDateTime = time.strftime('%h-%d-%Y-%H-%M-%S')
     posFile = open('trajectoryData'+curDateTime+'.txt', 'w')
     print "opened data file %s at location %s" % (posFile.name, os.getcwd())
     myKhepera = self.getFromDef("KHEPERA")
     transField = myKhepera.getField("translation")
     while True:
        "Perform a simulation step of 32 milliseconds"
        "and leave the loop when the simulation is over"
        if self.step(32) == -1:
           posFile.close()
           print "closed data file: %s" % posFile.name
           break
        "Get the robot's translation field"
        pos = myKhepera.getPosition()  
        trans = transField.getSFVec3f()
#        "Print the translation values for x, y, and z out to console"
#        print "x:%f y:%f z:%f"% (trans[0], trans[1], trans[2])
#        "Print the position"
#        print "position:",  pos
        print float(trans[1])
        posFile.write('%f,%f,%f\n' % (trans[0],
                                      trans[1],
                                      trans[2]))
        self.step(32)

controller = supervisorTrajectory()
controller.run()
