# File:          supervisorTrajectory.py
# Date:          12/18/2013
# Description:   A simple controller for the supervisor 
#                to record a robot's trajectory to file
# Author:        Stefano Franchi
# Modifications: 

from controller import Supervisor, Receiver, Node, Field
import time 
import os  

class Enumerate(object):
    def __init__(self, names):
        for number, name in enumerate(names.split()):
            setattr(self, name, number)

class supervisorTrajectory(Supervisor):
    State = Enumerate('SAVE CLOSEFILE NEWFILE DONOTHING')
    state = State.SAVE
        
    def initialize(self):
        """state determines the controller's behavior. Possible values:
           SAVE: save data to file
           CLOSEFILE: close existing traj file
           NEWFILE: create new traj file  
           DONOTHING: do not do anything, just pass        
        The value of self._state is changed by reading the receiver field, which receives instructions from the supervisor"""
        
        self.timeStep = 32
        self._state = self.State.SAVE
        self.receiver = self.getReceiver("stateReceiver")
        myKhepera = self.getFromDef("KHEPERA")
        self.translField = myKhepera.getField("translation")
        self.modelField = myKhepera.getField("model")
        self.receiver.enable(32)
        self.posFile = open(self.buildTrajFilename(modelName = self.modelField.getSFString()), 'w')
        self.writeTrajFileHeader(self.posFile)
      

    def run(self):     
        while True:
            if self.receiver.getQueueLength() > 0:
                message = self.receiver.getData()
                self.receiver.nextPacket()
#                print "I got the message: %s from supervisor: " % message
                if message == "SAVE":
                    self._state = self.State.SAVE
                elif message == 'CLOSEFILE':
                    self._state = self.State.CLOSEFILE
                elif message == 'NEWFILE':
                    self._state = self.State.NEWFILE
                elif message == 'DONOTHING':
                    self._state = self.State.DONOTHING 
                   
            if self._state == self.State.SAVE:
#                print "I am in state SAVE"
                self.writePosition(self.posFile)
            elif self._state == self.State.CLOSEFILE:
#                print "I am in state CLOSE"
                self.posFile.close()
                self._state = self.State.DONOTHING
#                print "I am in state DONOTHING"
            elif self._state == self.State.NEWFILE:
#                print "I am in state NEWFILE"
                try:
                    self.posFile.close()
                except IOError:
                    print "Trajectory file already close"
                self.posFile = open(self.buildTrajFilename(modelName = self.modelField.getSFString()), 'w')
                self.writeTrajFileHeader(self.posFile)
                self._state = self.State.SAVE
#                print "I am in state SAVE"
            elif self._state == self.State.DONOTHING:
#                print "I am in state DONOTHING"
                pass
            if self.step(self.timeStep) == -1: 
                self.posFile.close()
                break
                     
    def writePosition(self,fileHandle):
        fileHandle.write('%f\t%f\n' % (self.translField.getSFVec3f()[0],
                                       self.translField.getSFVec3f()[2]))
        
    def writeTrajFileHeader(self,posFile):
        '''Write data file header with General info, followed
           by position of light sources and initial position of vehicle'''
             
        "Get vehicle's initial position"
        initialPos = self.translField.getSFVec3f()
                
        "Get position of the light sources"
        posFile.write("# Position data for Homeo simulation run\n#\n#\n")
        posFile.write("# Light sources positioned at:\n")
        
        """Loop through  all light sources of name (DEF) of the form LIGHTx (0<x<10) 
        or of form TARGET and write their positions to file"""
        lights = ["TARGET"] + ["LIGHT"+str(i+1) for i in xrange(10)]
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

    
    def openTrajFile(self):
        "Return handle to opened file for the trajectory data"        
        
        myKhepera = self.getFromDef("KHEPERA")
        "get the robot's model, corresponding to the homeostat being evaluated (if any)"
        khepModelField = myKhepera.getField("model")
        khepModel = khepModelField.getSFString()

        'build the filename and open the trajectory file'
        fullPathTrajFileName = self.buildTrajFilename(khepModel)
        posFile = open(fullPathTrajFileName, "a")
        return posFile
    
    def trajFileRename(self, trajFileHandle, oldFileName, modelField):
        "rename trajectory file to include robot's model, if needed"

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

    def buildTrajFilename(self, modelName=None):
        '''FIXME: reads dataDirectory from a file called .SimDataDir.txt
               stored in parent/parent (../..) directory 
               Should really get the dataDir from the simulation supervisor. 
           Save file with filename equal to resulting path + an identifier '''
        
        if modelName == None:
            modelName = ''
        try:
            dataDirName = os.path.dirname(os.path.dirname(os.getcwd()))
            dataDirSource = open(os.path.join(dataDirName, '.SimDataDir.txt'),'r')
            dataDir = dataDirSource.read()
            dataDirSource.close()
        except IOError:
            dataDir = os.getcwd()
        
        curDateTime = time.strftime("%Y-%m-%d-%H-%M-%S")                    
        trajFilename = 'trajData-'+curDateTime+"-ID-"+ modelName+'.traj'
        print "Saving data to: ", os.path.join(dataDir,trajFilename)                 
        return  os.path.join(dataDir, trajFilename)


        

controller = supervisorTrajectory()
controller.initialize()
controller.run()
