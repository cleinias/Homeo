# Copyright (C) 2015-2026 Stefano Franchi
#
# This file is part of Homeo, a simulation of Ashby's homeostat and of
# homeostat-controlled robots.
#
# Homeo is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# Homeo is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with Homeo.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# File:          RobotTrajectoryWriter.py
# Description:   Writes a robot's trajectory to a .traj file.  The Box2D simulator
#                (KheperaSimulation) and the Webots backend (WebotsSimulation) each
#                use an instance, and pass it the robot's position at each step.
# Author:        Stefano Franchi
# Modifications: 

import time
import os
from math import degrees, sqrt
from os.path import exists
from Helpers.General_Helper_Functions import run_tag, dated_data_dir, unique_stem


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
       run writes ~12M rows (~600 MB); 20 of them fill some 12 GB.
       Decimating is lossless for every use Homeo makes of the files: the grapher thins to
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
        # Simulator steps per homeostat tick, for the header (2: the
        # KheperaSimulation default)
        self.stepsPerTick = 2
        # The eyes as configured, {name: (threshold, saturation, response)},
        # and where they sit along the robot's radii; set by KheperaSimulation
        # before the header is written, None if unknown
        self.eyes = None
        self.eyeRadiusRatio = None
        self.robotModel = None
        self.posFile = open(self.buildTrajFilename(modelName), 'w') if self._enabled else None
        self._openHeader(initialPos)

    def _openHeader(self, initialPos):
        '''Hold the header back until the first step (writeHeaderNow), so that
           it records the world as the experiment left it -- light intensity
           changed for --dark, robot moved to a random start -- not the
           defaults the world was built with.  initialPos is the fallback for
           a file closed before any step.'''
        self._headerWritten = False
        self._fallbackPos = (initialPos[0], initialPos[2])
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
                self._finishFile()
                if self.posFile is not None:
                    self.posFile.close()
                self._state = self.State.DONOTHING
#                print "I am in state DONOTHING"
            elif self._state == self.State.NEWFILE:
#                print "I am in state NEWFILE"
                self._finishFile()
                try:
                    if self.posFile is not None:
                        self.posFile.close()
                except IOError:
                    print("Trajectory file already close")
                self._rowCount = 0
                if lights is not None:
                    self.lights = lights        # rows and header list the same sources
                self.posFile = (open(self.buildTrajFilename(modelName = modelName), 'w')
                                if self._enabled else None)
                self._openHeader(position)
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
        self.writeHeaderNow(robotBody)

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

    def _finishFile(self):
        '''Complete the file before closing it: the header (if no step was
           recorded), the last skipped row, and a last comment line with the
           number of steps recorded, "# Steps recorded<TAB>S".  A decimated
           file's rows give the run's length only to within a sampling
           interval; this line gives it exactly (a file whose run was
           killed before closing has none).'''
        self.writeHeaderNow()
        self._flushPendingRow()
        if self.posFile is not None and not self.posFile.closed:
            self.posFile.write("# Steps recorded\t%d\n" % self._rowCount)

    def _flushPendingRow(self):
        "Write the last skipped row, if any, so the file ends at the true final pose."

        if self._pendingRow is not None and self.posFile is not None:
            self.posFile.write(self._pendingRow)
            self._pendingRow = None


    def writeHeaderNow(self, robotBody=None):
        '''Write the file's header, once: the light sources as they are now
           (position, intensity -- negative for a darkness source -- and
           whether on) and the robot's pose now (robotBody's, else the
           position the writer was opened with).  KheperaSimulation calls it
           before its first step, so the pose is the start pose.'''
        if self._headerWritten or self.posFile is None:
            return
        self._headerWritten = True
        if robotBody is not None:
            pos = (robotBody.position[0], robotBody.position[1])
            heading = '\t%.1f' % (degrees(robotBody.angle) % 360)
        else:
            pos, heading = self._fallbackPos, ''
        self.writeTrajFileHeader((pos[0], 0, pos[1]), self.lights, heading)

    def writeTrajFileHeader(self, initialPos, lights, heading=''):
        '''Write data file header with General info, followed
           by position of light sources and initial position of vehicle'''

        if self.posFile is None:
            return

        self.posFile.write("# Position data for Homeo simulation run\n#\n#\n")
        '''One row per simulator step, stepsPerTick steps per homeostat tick;
           with decimation, one row per interval steps.  A comment line, so
           readers that do not know it skip it.'''
        self.posFile.write("# Sampled every %d simulator steps, %d steps per homeostat tick\n"
                           % (self._interval, self.stepsPerTick))
        self.posFile.write("# Light sources positioned at:\n")
        for light in lights:
            intensity = light.userData.get('intensity', light.userData['lightIntensity'])
            self.posFile.write(light.userData['name'] + '\t%f\t%f\t%f\t%s\n' % (
                light.userData['lightPos'][0], light.userData['lightPos'][2], intensity,
                light.userData['lightIsOn']))
        self.writeEyes()
        self.posFile.write("# Vehicle's initial position at:\n")
        self.posFile.write('%f\t %f%s\n\n' % (initialPos[0], initialPos[2], heading))
        '''One light_x, light_y, distance triplet per source, in the order of
           the rows' columns: the first source's unprefixed, the others'
           prefixed with their names.'''
        columns = ['robot_x', 'robot_y', 'heading', 'light_x', 'light_y', 'distance']
        for light in lights[1:]:
            name = light.userData['name']
            columns += [name + '_x', name + '_y', name + '_distance']
        self.posFile.write("# " + "\t".join(columns) + "\n")
        self.posFile.flush()

        
    def writeEyes(self):
        '''The eyes' sensitivity, one comment line each, so that a chart can
        tell how far they see: an eye stops seeing a source of intensity I at
        sqrt(I / threshold) (on its axis).  With them, the Homeo code that
        wrote the file and the robot.'''
        from Helpers.General_Helper_Functions import homeo_version
        self.posFile.write("# Homeo\t%s\n" % homeo_version())
        if self.robotModel is not None:
            self.posFile.write("# Robot model\t%s\n" % self.robotModel)
        if self.eyeRadiusRatio is not None:
            self.posFile.write("# Eye radius ratio\t%g\n" % self.eyeRadiusRatio)
        for name, (threshold, saturation, response) in (self.eyes or {}).items():
            self.posFile.write("# Eye\t%s\tthreshold\t%f\tsaturation\t%f\tresponse\t%s\n"
                               % (name, threshold, saturation, response))

    def buildTrajFilename(self, modelName=None):
        '''Reads dataDir from internal ivar and builds a
           filename equal to resulting path + an identifier '''

        if modelName == None:
            modelName = ''
        dataDir = self.dataDir
        curDateTime = time.strftime("%Y-%m-%d-%H-%M-%S")
        if self.experimentName:
            stem = self.experimentName + '-' + curDateTime + run_tag()
        else:
            stem = 'trajData-ID-' + modelName + '-' + curDateTime + run_tag()
        # Not an existing file's name: a world set up again within the same
        # second would otherwise reopen, and empty, the last one's file
        return os.path.join(dataDir, unique_stem(dataDir, stem, ('.traj',)) + '.traj')
    
    def setDataDir(self, dataDir):
        """Set the directory to save the trajectory files to; None means
           today's data directory (dated_data_dir())."""
        if dataDir is None:
            dataDir = dated_data_dir()
        if exists(dataDir):
            self.dataDir = dataDir
        else:
            raise IOError                    
