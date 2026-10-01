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
from Helpers.General_Helper_Functions import run_tag


class EnumerateClass(object):
    "Manage enumerate type"
    def __init__(self, names):
        for number, name in enumerate(names.split()):
            setattr(self, name, number)


def configureTrajectoryDefaults(interval=1, enabled=True):
    '''Set the defaults every later RobotTrajectoryWriter is built with.

       Call this before the world is set up: each world-setting method in
       KheperaSimulator constructs its own writer, and routing two arguments
       through all of them (and through the visualizer and the GA workers)
       would touch a dozen call sites for a setting that is global to a run.

       interval: write one row every N recorded positions (1 = every one).
       enabled:  False suppresses the trajectory file entirely.'''

    RobotTrajectoryWriter.defaultInterval = max(1, int(interval))
    RobotTrajectoryWriter.defaultEnabled = bool(enabled)


class RobotTrajectoryWriter(object):
    State = EnumerateClass('SAVE CLOSEFILE NEWFILE DONOTHING')
    state = State.SAVE

    '''Run-wide defaults, set through configureTrajectoryDefaults().  A 6M-step
       run writes ~12M rows (~600 MB); 20 of them filled 11.5 GB on 2026-09-30.
       Decimating is lossless for every present use: the grapher thins to
       50,000 points anyway, and fitness comes from the DEAP logbook, never
       from these files.'''
    defaultInterval = 1
    defaultEnabled = True

    def __init__(self, modelName, initialPos, lights, dataDir = None, experimentName = None,
                 interval = None, enabled = None):
        """state determines the controller's behavior. Possible values:
           SAVE: save data to file
           CLOSEFILE: close existing traj file
           NEWFILE: create new traj file
           DONOTHING: do not do anything, just pass
        The value of self._state is changed by reading the receiver field, which receives instructions from the supervisor"""

        self.lights = lights
        self.experimentName = experimentName
        self.setDataDir(dataDir)
        self._state = self.State.SAVE
        self._interval = self.defaultInterval if interval is None else max(1, int(interval))
        self._enabled = self.defaultEnabled if enabled is None else bool(enabled)
        self._rowCount = 0
        self._pendingRow = None          # last skipped row, written on close
        self.posFile = open(self.buildTrajFilename(modelName), 'w') if self._enabled else None
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
                self._flushPendingRow()
                if self.posFile is not None:
                    self.posFile.close()
                self._state = self.State.DONOTHING
#                print "I am in state DONOTHING"
            elif self._state == self.State.NEWFILE:
#                print "I am in state NEWFILE"
                self._flushPendingRow()
                try:
                    if self.posFile is not None:
                        self.posFile.close()
                except IOError:
                    print("Trajectory file already close")
                self._rowCount = 0
                self.posFile = (open(self.buildTrajFilename(modelName = modelName), 'w')
                                if self._enabled else None)
                self.writeTrajFileHeader(position,lights)
                self._state = self.State.SAVE
#                print "I am in state SAVE"
            elif self._state == self.State.DONOTHING:
#                print "I am in state DONOTHING"
                pass
                     
    def writePosition(self, robotBody):
        '''Write robot state and light data to file, every self._interval-th call.

           A skipped row is held in _pendingRow rather than dropped, so that
           whenever the run ends the file's last line is the vehicle's true
           final pose -- which is what the final-distance analyses read.'''

        if self.posFile is None:
            return

        rx = robotBody.position[0]
        ry = robotBody.position[1]
        heading = degrees(robotBody.angle) % 360
        parts = ['%f\t%f\t%.1f' % (rx, ry, heading)]
        for light in self.lights:
            lx = light.position[0]
            ly = light.position[1]
            dist = sqrt((rx - lx)**2 + (ry - ly)**2)
            parts.append('%f\t%f\t%f' % (lx, ly, dist))
        row = '\t'.join(parts) + '\n'

        self._rowCount += 1
        if self._rowCount % self._interval != 0:
            self._pendingRow = row
            return
        self._pendingRow = None
        self.posFile.write(row)

    def _flushPendingRow(self):
        "Write the last skipped row, if any, so the file ends at the true final pose."

        if self._pendingRow is not None and self.posFile is not None:
            self.posFile.write(self._pendingRow)
            self._pendingRow = None


    def writeTrajFileHeader(self, initialPos, lights):
        '''Write data file header with General info, followed
           by position of light sources and initial position of vehicle'''

        if self.posFile is None:
            return

        "Get position of the light sources"
        self.posFile.write("# Position data for Homeo simulation run\n#\n#\n")
        if self._interval > 1:
            '''Record the decimation, or a reader cannot tell a short run from a
               sampled long one.  A comment line, so old readers skip it.'''
            self.posFile.write("# Sampled every %d ticks\n" % self._interval)
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
        trajFilename = 'trajData-ID-'+modelName+'-'+curDateTime+'.traj'
        print("Saving data to: ", os.path.join(dataDir,trajFilename))                 
        return  os.path.join(dataDir, trajFilename)
    
    def buildTrajFilename(self, modelName=None):
        '''Reads dataDir from internal ivar and builds a
           filename equal to resulting path + an identifier '''

        if modelName == None:
            modelName = ''
        dataDir = self.dataDir
        curDateTime = time.strftime("%Y-%m-%d-%H-%M-%S")
        if self.experimentName:
            trajFilename = self.experimentName + '-' + curDateTime + run_tag() + '.traj'
        else:
            trajFilename = 'trajData-ID-'+modelName+'-'+curDateTime+run_tag()+'.traj'
        return  os.path.join(dataDir, trajFilename)
    
    def setDataDir(self, dataDir):
        "Set the directory to save the trajectory files to"
        
        if exists(dataDir):
            self.dataDir = dataDir
        else:
            raise IOError                    
