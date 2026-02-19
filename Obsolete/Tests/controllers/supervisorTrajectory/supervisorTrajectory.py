# File:          supervisorTrajectory.py
# Date:          12/18/2013
# Description:   A simple controller for the supervisor 
#                to record a robot's trajectory to file
# Author:        Stefano Franchi
# Modifications: 

from controller import Supervisor, Receiver, Node, Field
import time 
import os  
from Helpers.RobotTrajectoryWriter import RobotTrajectoryWriter


class supervisorTrajectory(Supervisor):
        
    def initialize(self):
        """The value of self.writer._state is changed by reading the receiver field, 
        which receives instructions from the supervisor"""
        
        self.timeStep = 32
        self._state = self.State.SAVE
        self.receiver = self.getReceiver("stateReceiver")
        myKhepera = self.getFromDef("KHEPERA")
        self.translField = myKhepera.getField("translation")
        self.modelField = myKhepera.getField("model")
        self.receiver.enable(32)
        "Get robot's initial position and lights"
        
        "Write header"
        initialPos = self.translField.getSFVec3f()
        lightsInfo = self.getLightsInfo()
        self.writer = RobotTrajectoryWriter(self.modelField.getSFString(), initialPos, lightsInfo)
      

    def run(self):     
        while self.step(self.timeStep) != -1:
            "Check for state transition message"
            if self.receiver.getQueueLength() > 0:
                transMessage = self.receiver.getData()
                self.receiver.nextPacket()
#                 print "I got the message: %s from supervisor: " % transMessagemessage
            else:
                transitionMessage = None
            "get position and model name"
            position = self.translField.getSFVec3f()
            modelName = self.modelField.getSFString()
            self.writer.runOnce(position, transitionMessage, modelName)
        self.writer.runOnce(transitionMessage="CLOSEFILE")
                     
    def getLightsInfo(self):
        """Loop through  all light sources of name of the form LIGHTx (0<x<10) 
        or of form TARGET and write their positions and intensity into a dictionary"""
        lights = []
        lightsList = ["TARGET"] + ["LIGHT"+str(i+1) for i in xrange(10)]
        for l in lightsList:
            try:
                light = self.getFromDef(l)
                lightPosField = light.getField("location")
                lightPos = lightPosField.getSFVec3f()
                lightIsOnField = light.getField("on")
                lightIsOn=lightIsOnField.getSFBool()
                lightIntensity=(light.getField("intensity")).getSFFloat()
                lightInfo = {'name':l,
                             'lightPos':[lightPos[0],lightPos[2]],
                             'lightIntensity':lightIntensity,
                             'lightIsOn':lightIsOn}
                lights.append[lightInfo]
            except: 
                break
        return lights
    

controller = supervisorTrajectory()
controller.initialize()
controller.run()
