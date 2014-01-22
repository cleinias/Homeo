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
     '''Assume that the current directory is under a "src" directory
        and that a data folder called 'SimulationsData will exist
        at the same level as "src"
        Save file with filename equal to resulting path + an identifier '''

     curDateTime = time.strftime('%h-%d-%Y-%H-%M-%S')    
     trajFilename = 'trajectoryData-'+curDateTime+'.txt'
     
     addedPath = 'SimulationsData'
     datafilePath = os.path.join(os.getcwd().split('src/')[0],addedPath)
     fullPathTrajFilename = os.path.join(datafilePath, trajFilename)
     print "The computed filename name with path is: ", fullPathTrajFilename
     posFile = open(fullPathTrajFilename,"a")
     print "opened data file %s at location %s" % (posFile.name, datafilePath)

     "Get the translation node of the robot by its definition"
     myKhepera = self.getFromDef("KHEPERA")
     transField = myKhepera.getField("translation")
     " Get vehicle's initial position"
     initialPos = transField.getSFVec3f()
     "Get position of the light sources"
     '''Write data file header with General info, followed
        by position of light sources and initial position of vehicle'''
     posFile.write("# Position data for Homeo simulation run\n#\n#\n")
     posFile.write("# Light sources positioned at:\n")
     "Loop through  all light sources of name (DEF) of the form LIGHTx and write their positions to file"
     "The radius of the light sources is provisionally set to 2.5"
     lightRadius = 2.5
     for i in xrange(10):
         try:
             light = self.getFromDef("LIGHT" + str(i+1))
             lightPosField = light.getField("location")
             lightPos = lightPosField.getSFVec3f()
             posFile.write('%f\7%f\t %f \n' % (lightPos[0],
                                             lightPos[2],
                                             lightRadius))
             posFile.flush()
             print "Point light number %u is at %f \t %f\n" % (i+1,
                                                          lightPos[0],
                                                          lightPos[2])
         except: 
             print "There are exactly %u point lights in this simulation" % (i)
             posFile.write("\n\n")
             posFile.flush()
             break
     posFile.write("# Vehicle's initial position at:\n")
     posFile.write('%f\t %f\n\n\n' % (initialPos[0],
                                    initialPos[2]))
     posFile.write("# Vehicle's coordinates (x and z in Webots term, as y is the vertical axis)\n")
     posFile.flush()
   
     while True:
        "Perform a simulation step"
        "and leave the loop when the simulation is over"
        if self.step(64) == -1:
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
#        print float(trans[1])
        posFile.write('%f\t%f\n' % (trans[0],
                                    trans[2]))
        posFile.flush()

        self.step(32)

controller = supervisorTrajectory()
controller.run()
