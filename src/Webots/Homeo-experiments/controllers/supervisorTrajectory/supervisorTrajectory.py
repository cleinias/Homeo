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
    #===========================================================================
    # def __init__(self):
    #     self.checkModelName = True 
    #===========================================================================
        
    def run(self):        
         "Main loop"
         "Get the translation node of the robot by its definition"
         myKhepera = self.getFromDef("KHEPERA")
         transField = myKhepera.getField("translation")
    
         "get the robot's model, corresponding to the homeostat being evaluated (if any)"
         khepModelField =   myKhepera.getField("model")
         khepModel = khepModelField.getSFString()
         #print "Robot's model is: ", khepModel
    
         'build the filename and open the trajectory file'
         fullPathTrajFileName =self.buildTrajFilename(khepModel)

         posFile = open(fullPathTrajFileName,"a")
         # print "opened data file %s at location %s" % (posFile.name, datafilePath)
    
         
         
         " Get vehicle's initial position"
         initialPos = transField.getSFVec3f()
         "Get position of the light sources"
         '''Write data file header with General info, followed
            by position of light sources and initial position of vehicle'''
         posFile.write("# Position data for Homeo simulation run\n#\n#\n")
         posFile.write("# Light sources positioned at:\n")
         """Loop through  all light sources of name (DEF) of the form LIGHTx (0<x<10) 
         or of form TARGET and write their positions to file"""
         lights = []
         lights.append("TARGET")
         for i in xrange(10):
             lights.append("LIGHT"+str(i+1))
         for l in lights:
             try:
                 light = self.getFromDef(l)
                 lightPosField = light.getField("location")
                 lightPos = lightPosField.getSFVec3f()
                 lightIsOnField = light.getField("on")
                 lightIsOn=lightIsOnField.getSFBool()
                 lightIntensity=(light.getField("intensity")).getSFFloat()
                 posFile.write(l+'\t%f\t%f\t%f\t%s\n' % (lightPos[0],
                                                              lightPos[2],
                                                              lightIntensity,
                                                              lightIsOn))
                 posFile.flush()
             except: 
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
            if self.checkModelName:
                posFile = self.trajFileRename(posFile, fullPathTrajFileName,khepModelField)   
            self.step(32)
            
    def buildTrajFilename(self, modelName=None):        
         '''Assume that the current directory is under a "src" directory
         and that a data folder called 'SimulationsData will exist
         at the same level as "src"
         Save file with filename equal to resulting path + an identifier '''

         if modelName == None:
             modelName = ''
             
         curDateTime = time.strftime("%Y-%m-%d-%H-%M-%S")                    
         trajFilename = 'trajData-'+curDateTime+"-ID-"+ modelName+'.traj'
         #print trajFilename
             
         addedPath = 'SimulationsData'
         datafilePath = os.path.join(os.getcwd().split('src/')[0],addedPath)
         #print datafilePath 
         return  os.path.join(datafilePath, trajFilename)
     
    def trajFileRename(self, trajFileHandle, oldFileName,modelField):
         "rename traj file to include robot's model, if needed"

         khepModel = modelField.getSFString()
         newTrajFileHandle = trajFileHandle
         if khepModel != "Unspecified":
             trajFileHandle.close()
             newFileName = self.buildTrajFilename(khepModel)
             os.rename(oldFileName, newFileName)
             newTrajFileHandle = open(newFileName, 'a')
             #print "Traj data file renamed to: ", newFileName
             self.checkModelName = False
         return newTrajFileHandle


        

controller = supervisorTrajectory()
controller.checkModelName = True
controller.run()
