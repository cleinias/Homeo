# Copyright (C) 2013-2026 Stefano Franchi
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

'''
The Transducer module contains the classes necessary to operate 
a robot's actuators (motors, etc). The basic class is fairly abstract 
and may be subclassed to operate concrete robotic simulation environments
(here, the HOMEO_ subclasses, for Homeo's own simulators)
'''
from Helpers.General_Helper_Functions import SubclassResponsibility
from Helpers.ExceptionAndDebugClasses import hDebug
from sys import stderr
from KheperaSimulator.KheperaSimulator import KheperaRobot

class TransducerException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Transducer(object):
    '''
    Transducer is an abstract class. It subclasses control a robot's input /output interfaces. 
    It has just three instance variables:

    robot          <aRef>       a ref to the robot whose actuator it operates
    transdFunction <aString>    the name of the robot's function to operate the actuator
    parameters     <aList>      a list of  parameters to be passed to the function

    The basic methods (all defined in subclasses) are 
    
    act  ---  which activates the actuator by running robot.transdFunction(parameters)
    sense --- which reads the sensor by running robot.transdFunction(parameters) and returning a value
    range --- which returns a 2 value list containing the minimum and maximum values of the transducer 
    
    '''


    def __init__(self):
        '''
        Basic setup
        '''
    #=================================================================
    # Class properties
    #=================================================================
    
    def setRobot(self, aValue):
        self._robot = aValue
    def getRobot(self):
        return self._robot
    robot = property(fget = lambda self: self.getRobot(),
                    fset = lambda self, value: self.setRobot(value))  

    def setTransdFunction(self, aValue):
        self._transdFunction = aValue
    def getTransdFunction(self):
        return self._transdFunction
    transdFunction = property(fget = lambda self: self.getTransdFunction(),
                    fset = lambda self, value: self.setTransdFunction(value))
    
    def setFuncParameters(self, aValue):
        self._funcParameters = aValue
    def getFuncParameters(self):
        return self._funcParameters
    funcParameters = property(fget = lambda self: self.getFuncParameters(),
                    fset = lambda self, value: self.setFuncParameters(value))  
  

    #======================================================================
    #  Running methods
    #======================================================================
    
    def act(self, parameters):
        '''act method is implemented only by Transducer's subclasses'''
        raise SubclassResponsibility()
    
    def read(self):
        '''read method is implemented only by Transducer's subclasses'''
        raise SubclassResponsibility()
        
    def range(self):
        '''range method is implemented only by Transducer's subclasses'''
        raise SubclassResponsibility()


        
    


class HOMEO_DiffMotor(Transducer):
    """Interface to a motor of a differential wheel robot simulated by HOMEO internal robotic simulator
       Instance variables:
       - wheel     aString: the right or left wheel 
       - robot     aString: the string identifying the robot in the HOMEO simulation
       - simul     aRef: reference to the simulation (needed to advance it in single step after each command is actuating command"""
    
    def __init__(self, wheel, robotRef, simul):
        "Wheel could either 'right or 'left' and nothing else"

        if wheel == 'right':
            self._transdFunction = 'setRightSpeed'
        elif wheel == 'left':
            self._transdFunction = 'setLeftSpeed'
        else:
            raise TransducerException("Wheel must either be right or left")

        self._wheel = wheel
        self.robot = robotRef
        self.simul = simul
        self._range = self.getRange()


    def getRange(self):
        "Get motor range from robot"

        try:
            range = self.simul.allBodies[self.robot].getMaxSpeed()[self._wheel]
            return range
        except:
            raise TransducerException("Cannot get maxSpeed of HOMEO motor: " + self._wheel+"Wheel")
    
    def act(self):
        '''Activates the wheel motor by calling the actuator function (transdFunction) with 
           HOMEO client (stored in self.robot) and the needed parameters (stored in funcParameters).
           The motor only sets its wheel's speed: the world advances once per
           tick, after every unit has updated (KheperaSimulation.tickAdvance).'''
        
        try:         
            getattr(self.simul.allBodies[self.robot], self._transdFunction)(self.funcParameters)
        except:
            stderr.write("Motor command to HOMEO motor:%sWheel failed " % self._wheel)
            raise #TransducerException("Motor command to HOMEO motor:%sWheel failed " % self._wheel)
        
    def read(self):
        "Motors cannot sense"
        raise TransducerException("HOMEO Motor %sWheel cannot sense" %self._wheel)
 
    def range(self):
        "Motor's max speed is obtained at initialization and cached for efficiency"
        '''Function returns a list containing the min and max speed of the motor.
           notice that this posits minSpeed as always = to minus maxSpeed'''

        return (-self._range, self._range)


class _HOMEO_RobotByName(object):
    """The robot a sensor reads: looked up by name in its simulation at each
    read, as HOMEO_DiffMotor does, so that a sensor made before a world reset
    (which builds a new robot) reads the new robot.  Given a robot object
    instead (no simul), the sensor reads that robot."""

    def getRobot(self):
        if getattr(self, 'simul', None) is not None:
            return self.simul.allBodies[self._robot]
        return self._robot


class HOMEO_LightSensor(_HOMEO_RobotByName, Transducer):
    """ Connects a unit to a HomeoLight sensor of  a Khepera-like robot
        in the internal HOMEO simulator.  robotRef: the robot's name in simul,
        or (without simul) the robot itself."""
        
    def __init__(self, eye, robotRef, simul=None):
        "Current HOMEO Khepera models only have a 'right' and a 'left' eye and nothing else"

        if eye not in ["right","left"]:
            raise TransducerException("Eye must either be right or left")
        self._eye = eye + "Eye"
        self.simul = simul
        self.robot = robotRef
        self._transdFunction = 'getSensorRead'
        self._range = self.getRange()
        
    def getRange(self):
        "get the max of the sensor's response: the eye reports a response normalised to [0, 1]"
        try:
            value = self.robot.getMaxSensorValue(self._eye)
        except:
            raise TransducerException("Cannot get maxValue of HOMEO sensor: " + self._eye)
        return value

    def read(self):
        """Return the eye's response, in [0, 1], to the sum of all the
           irradiances at the sensor's surface produced by the detectable
           lights in the world (KheperaRobot.eyeResponse); in [-1, 0] for a
           darkness source (negative intensity)."""
#         value = 0
        try:
            value =  self.robot.getSensorRead(self._eye)
        except:
            raise Exception("Cannot read value for HOMEO sensor " + self._eye)
#             stderr.write("Cannot read value for HOMEO sensor " + self._eye)
#             return 0
        return value
        
    def range(self):
        "Sensor's range is obtained at initialization and cached for efficiency"
        '''Function returns a tuple with min and max range. We posits minRange = 0'''
        return (0,self._range)
    
    def act(self):
        "Eyes cannot act"
        raise TransducerException("HOMEO sensor %s cannot act" %self._eye)


class HOMEO_QualitySensor(_HOMEO_RobotByName, Transducer):
    """Sensor transducer that reads from sources of a specific quality only.

    Unlike HOMEO_LightSensor which reads from all detectable lights,
    this sensor filters by quality (e.g. 'light', 'temperature',
    'oxygen', 'organic') using KheperaRobot.getSensorReadByQuality().
    """

    def __init__(self, sensorName, quality, robotRef, simul=None):
        # sensorName: fixture name (e.g. 'rightTempEye')
        # quality: 'light', 'temperature', 'oxygen', 'organic'
        # robotRef: the robot's name in simul, or (without simul) the robot
        self._eye = sensorName
        self._quality = quality
        self.simul = simul
        self.robot = robotRef
        self._transdFunction = 'getSensorReadByQuality'
        self._range = self.robot.getMaxSensorValue(self._eye)

    def read(self):
        return self.robot.getSensorReadByQuality(self._eye, self._quality)

    def range(self):
        return (0, self._range)

    def act(self):
        raise TransducerException("Quality sensor %s cannot act" % self._eye)


        
       
