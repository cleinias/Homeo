# File:          supervisorTrajectoryAbstract.py
# Date:          2/20/2015
# Description:   A file writer class for the controllers recording trajectories in the 
#                robotics simulation packages. 
#                It basically works as a finite state machine. Webots, V-REP, etc. will use an instance as
#                a component and add package specific mechanisms to (1) read the state transitions and
#                (2) read the robot's position
# Author:        Stefano Franchi
# Modifications: 

import time
import os
from math import degrees, sqrt
from os.path import exists


class EnumerateClass(object):
    "Manage enumerate type"
    def __init__(self, names):
        for number, name in enumerate(names.split()):
            setattr(self, name, number)


class RobotTrajectoryWriter(object):
    State = EnumerateClass('SAVE CLOSEFILE NEWFILE DONOTHING')
    state = State.SAVE
        
    def __init__(self, modelName, initialPos, lights, dataDir = None):
        """state determines the controller's behavior. Possible values:
           SAVE: save data to file
           CLOSEFILE: close existing traj file
           NEWFILE: create new traj file
           DONOTHING: do not do anything, just pass
        The value of self._state is changed by reading the receiver field, which receives instructions from the supervisor"""

        self.lights = lights
        self.setDataDir(dataDir)
        self._state = self.State.SAVE
        self.posFile = open(self.buildTrajFilename(modelName), 'w')
        self.writeTrajFileHeader(initialPos, lights)
                
    def runOnce(self,position=None, transitionMessage=None, modelName = None, lights = None):     
            "update state if necessary"
            if transitionMessage is not None:
                if transitionMessage == "SAVE":
                    self._state = self.State.SAVE
                elif transitionMessage == 'CLOSEFILE':
                    self._state = self.State.CLOSEFILE
                elif transitionMessage == 'NEWFILE':
                    self._state = self.State.NEWFILE
                elif transitionMessage == 'DONOTHING':
                    self._state = self.State.DONOTHING 

            "state actions and transitions"       
            if self._state == self.State.SAVE:
#                 print "I am in state SAVE"
                self.writePosition(position)
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
                    print("Trajectory file already close")
                self.posFile = open(self.buildTrajFilename(modelName = modelName), 'w')
                self.writeTrajFileHeader(position,lights)
                self._state = self.State.SAVE
#                print "I am in state SAVE"
            elif self._state == self.State.DONOTHING:
#                print "I am in state DONOTHING"
                pass
                     
    def writePosition(self, robotBody):
        "Write robot state and light data to file"
        rx = robotBody.position[0]
        ry = robotBody.position[1]
        heading = degrees(robotBody.angle) % 360
        parts = ['%f\t%f\t%.1f' % (rx, ry, heading)]
        for light in self.lights:
            lx = light.position[0]
            ly = light.position[1]
            dist = sqrt((rx - lx)**2 + (ry - ly)**2)
            parts.append('%f\t%f\t%f' % (lx, ly, dist))
        self.posFile.write('\t'.join(parts) + '\n')
        
    def writeTrajFileHeader(self, initialPos, lights):
        '''Write data file header with General info, followed
           by position of light sources and initial position of vehicle'''
                             
        "Get position of the light sources"
        self.posFile.write("# Position data for Homeo simulation run\n#\n#\n")
        self.posFile.write("# Light sources positioned at:\n")
        
        for light in lights:
                self.posFile.write(light.userData['name'] +'\t%f\t%f\t%f\t%s\n' % (light.userData['lightPos'][0],
                                                                  light.userData['lightPos'][2],
                                                                  light.userData['lightIntensity'],
                                                                  light.userData['lightIsOn']))
                self.posFile.flush()
        self.posFile.write("# Vehicle's initial position at:\n")
        self.posFile.write('%f\t %f\n\n' % (initialPos[0], initialPos[2]))
        self.posFile.write("# robot_x\trobot_y\theading\tlight_x\tlight_y\tdistance\n")
        self.posFile.flush()

        
    def trajFileRename(self, trajFileHandle, oldFileName, modelName):
        "rename trajectory file to include robot's model, if needed"

        newTrajFileHandle = trajFileHandle
        if modelName != "Unspecified":
            trajFileHandle.close()
            newFileName = self.buildTrajFilename(modelName)
            os.rename(oldFileName, newFileName)
            newTrajFileHandle = open(newFileName, 'a')
            #print "Traj data file renamed to: ", newFileName
        return newTrajFileHandle

    def buildTrajFilenamefromFile(self, modelName=None):
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
        print("Saving data to: ", os.path.join(dataDir,trajFilename))                 
        return  os.path.join(dataDir, trajFilename)
    
    def buildTrajFilename(self, modelName=None):
        '''Reads dataDir from internal ivar and builds a 
           filename equal to resulting path + an identifier '''
        
        if modelName == None:
            modelName = ''        
        dataDir = self.dataDir
        curDateTime = time.strftime("%Y-%m-%d-%H-%M-%S")                    
        trajFilename = 'trajData-'+curDateTime+"-ID-"+ modelName+'.traj'
#         print("Saving data to: ", os.path.join(dataDir,trajFilename))                 
        return  os.path.join(dataDir, trajFilename)
    
    def setDataDir(self, dataDir):
        "Set the directory to save the trajectory files to"
        
        if exists(dataDir):
            self.dataDir = dataDir
        else:
            raise IOError                    
