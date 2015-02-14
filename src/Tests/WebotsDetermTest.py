'''
Created on Jan 24, 2015

@author: stefano

Script that tests Webots determinist runs.
Runs Webots repeatedly with a deterministic
series of random motor commands over TCP/IP

Assumes:
1. Webots world Determinist-Khepera-world.wbt (or different world passed on command line) 
   is present in 'worlds' subdir of script's dir 
2. Webots can be launched from command line
3. Khepera robot's controller listens on localhost:10020
4. Supervisor's controller listens on localhost:10021
5. A SimsData subdir exists at the same level as the script 
'''
import decimal
import sys
import numpy as np
import csv
import datetime
import socket
from os import system
from subprocess import check_output
from mpmath import mpf, nstr


#import RobotSimulator.WebotsTCPClient
from RobotSimulator.WebotsTCPClient import WebotsTCPClient
from socket import error as SocketError
import os
from math import sqrt
from time import sleep, time, strftime, localtime
from tabulate import tabulate
from xml.dom.minidom import _clone_node

ORIG_TRANSL = [4,0,4]      # y coord is always 0 in a 2d world
ORIG_ROTAT  = [0,1,0,0]    # Rotation expressed as a normalized vector for rot axis, plus a rot angle along that axis  
WEBOTS_MIN_TIME_STEP =  mpf(0.032)

class TestWebotsDeterminism(object):
    ''' Class testing a Webots determinist run'''
    
        
    def __init__(self,parent=None, stepsSize = 1000, 
                                   popSize=150,
                                   supervisor_host = 'localhost', 
                                   supervisor_port = 10021, 
                                   khepera_host = 'localhost',
                                   khepera_port = 10020,
                                   exp = "Determinist-Khepera-world-TESTING.wbt"):
        self.popSize = popSize
        self.stepsSize = stepsSize    
        self.exp = exp
        self.khepera_port = khepera_port
        self.khepera_host = khepera_host
        self.supervisor_port = supervisor_port
        self.supervisor_host  = supervisor_host
        self._kheperaSocket = None
        self._supervisorSocket = None
        self._dataDir = None

        "Directory to save simulations'data: SimsData subdir of parent dir"
        self._dataDir = os.path.join(os.getcwd(),'SimsData',('SimsData-'+strftime("%Y-%m-%d-%H-%M-%S", localtime(time()))))
        try:
            os.mkdir(self._dataDir)
        except OSError:
            print "Saving to existing directory", self._dataDir
        'save self._dataDir path to a file, so Webots trajectory supervisor can read it'
        'FIXME: Should really communicate it to webots simulation supervisor to pass it to trajectory supervisor '
        try:
            dataDirFile = open(os.path.join(os.getcwd(),'.SimDataDir.txt'),'w+')
            dataDirFile.write(self._dataDir)
            dataDirFile.close()
        except OSError:
            print "could not write to  dataDir file"
            raise Exception

        decimal.getcontext().prec = 4                       
    
    def getWebotsSocket(self, host, port, my_socket):
        '''Try a few times to create a connection if not connected already. 
           Return a socket'''
        
        connected = False
        connectAttempts = 1000
        sleepTime = 0.05
        if my_socket is not None:
            print 'Already connected! Use the socket stored in clientSocket'
        else:
            if connected == False:
                try:
                    for i in xrange(connectAttempts):
                        try:
                            my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            my_socket.connect((host, port))
                            print 'Success! Connected to server at %s on port %u' % (host, port)
                            connected = True
                            return my_socket
                        except socket.error:
                            print 'Cannot connect to server at %s on port %u' % (host, port)
                            print "Waiting %f seconds and then going for attempt number %d" % (sleepTime,i+2)
                            sleep(sleepTime)
                    if connected == False:
                        print "I could not connect to server at %s on port %u after %d attempts" % (host, port, connectAttempts)
                        my_socket = None
                        raise socket.error
                except socket.error:
                    print "I could NOT connect to server"
                
                      
    def close(self, my_socket):
        'Closes the connection and set socket to None'
        if my_socket is not None:
            try:
                my_socket.close()
                my_socket = None
                return my_socket
            except socket.error:
                print 'Cannot close socket!'

    def runDetermTest(self):
        """Run pop number of Webots run 
        
           Execute a complete GA run. Could be either over a population of clones
           or over a truly randomly generated  population.
           All parameters (popsize, gen, cxProb, etc.) as well as DEAP-specific tools,
           are stored in class's ivars.
           Save fitness data to logbook"""

          
        'Record time for naming logbook pickled object and computing time statistics'
        self.simulationEnvironStart(world=self.exp, mode='fast')
        try:
            self._supervisorSocket = self.getWebotsSocket(self.supervisor_host, self.supervisor_port, self._supervisorSocket)
            self._clientSocket = self.getWebotsSocket(self.khepera_host, self.khepera_port, self._kheperaSocket)
        except Exception, e:
            print " Could not connect to Webots robot or Webots supervisor", e
            return
        try:
            timeStep      =  mpf(32)                      # In milliseconds
            betwCmdsDelay =  mpf(50)                      # In time steps
            betwLoopsDelay = mpf(100)                     # In time steps
            for ind in xrange(self.popSize):
                np.random.seed(64)
                formattedTime = strftime("%Y-%m-%d-%H-%M-%S", localtime(time()))
                rightCmdFile = open(os.path.join(self._dataDir,("RightMotorCommands-"+formattedTime+'.csv')),'w')
                leftCmdFile = open(os.path.join(self._dataDir,("LeftMotorCommands-"+formattedTime+'.csv')),'w')
                'name the robot according to pattern 000-ind'
                robot_ID = "000-"+str(ind+1).zfill(3)
                self._supervisorSocket.send('M,'+robot_ID)
                print "indiv number: ", ind
                cmdExptdTime = int( (self.getSimulTime(self._clientSocket) /WEBOTS_MIN_TIME_STEP))                             
                for step in xrange(self.stepsSize):
                    cmdExptdTime += betwCmdsDelay
                    print "now cmd expect param: %d" % cmdExptdTime
                    rightCmd = str(round(np.random.uniform(low=0,high=10),3))
                    self._clientSocket.send('R,'+rightCmd + ','+str(cmdExptdTime) +','+str((2*step)+1))
                    discard = self._clientSocket.recv(100)
                    rightCmdFile.write(str(rightCmd+','+str(cmdExptdTime*timeStep) +','+str((2*step)+1)+'\n'))
                    leftCmd = str(round(np.random.uniform(low=0,high=10),3))
#                     simulTime = self.getSimulTime(self._clientSocket)
                    cmdExptdTime +=  betwCmdsDelay
#                     print "now simul at: %d and cmd expect param: %d"%(simulTime, cmdExptdTime) 
                    self._clientSocket.send('L,'+ leftCmd+ ','+str(cmdExptdTime)+','+str((2*step)+2))
                    discard = self._clientSocket.recv(100)
                    leftCmdFile.write(leftCmd+','+str(cmdExptdTime*timeStep) +','+str((2*step)+2)+'\n')
                    cmdExptdTime += betwLoopsDelay
#                 self._clientSocket.send("Z,,-1,")
                rightCmdFile.close()
                leftCmdFile.close()
                self.stopRobot()
                self.simulationEnvironResetPos(ORIG_TRANSL + ORIG_ROTAT)
                simulTime = self.getSimulTime(self._clientSocket)
                print "Simulation now at ==>  ", str(simulTime)
                self.simulationEnvironResetPhysics()
#            self.stopRobot()
            self._supervisorSocket.send('M,'+'Dummy_final')
            sleep(1)
            self.simulationEnvironQuit()
            print "Simulation completed."
            print "Data files are available in directory:"
            print self._dataDir    
        except Exception, e:
            print "TCP connection error. Cleaning up and quitting...", e
            print "Trying to quit webots"
            self.simulationEnvironQuit()
                
    def getTimeFormattedCompleteFilename(self,timeStarted, prefix, extension, path = None):
        """ Return a string containing a complete filename (including path)
            that starts with prefix, plus a formatted version of the timeNow string, plus
            the extension.
            Create a folder under the globally defined dataDir if no path is given.
            TimeStarted is in seconds from the epoch (as returned by time.time())
        """ 
        formattedTime = strftime("%Y-%m-%d-%H-%M-%S", localtime(timeStarted))
        filename = prefix+'-'+formattedTime+ '.' + extension
        if path == None:
            datafilePath = self._dataDir
        else: datafilePath = path
        return os.path.join(datafilePath, filename)
                               
    def simulationEnvironReset(self):
        """Reset webots simulation.
           Do not return from function until the simulation has really exited 
           and the previous tcp/ip socket is no longer valid. """
           
        try:
            self._supervisorSocket.send("R")
            response = self._supervisorSocket.recv(100)
            try:
                while True:
                    self._supervisorSocket.send(".")
                    sleep(0.05)
            except SocketError:
                pass
        except SocketError:
             print "Could not reset Webots simulation"
        finally: 
            self._supervisorSocket = None        
        
    def simulationEnvironResetPhysics(self):
        "Reset Webots simulation physics"
        
        try:
            self._supervisorSocket.send("P")
            #response = self._supervisorSocket.recv(100)
            print "Webots pysics reset" 
        except SocketError:
            print "Could not reset Webots simulation's physics"
            
    
    def simulationEnvironQuit(self):
        "Quit Webots application"
        
        try:
            self._supervisorSocket.send("Q")
        except SocketError as e:
            print "Sorry, I lost the connection to Webots and could not could not quit"
            print e.value()
        except AttributeError as e:
             print "I lost the socket communicating to Webots"
             print e.value()
            
    def simulationEnvironStart(self,world = None, mode = "fast"):
        """
        Start a webots instance with the given world and at the specified speed (mode).
        Mode can be one of realtime, run, or fast 
        """
        if not 'webots-bin' in check_output(['ps','ax']):
            callString =  "/home/stefano/bin/webots  --stderr --stdout  --mode="+ mode+ " " +os.path.join (os.getcwd(),'worlds',world) + " &"
#             callString =  "/home/stefano/bin/webots    --mode="+ mode+ " " +os.path.join (os.getcwd(),'worlds',world) + " &"
            system(callString)
            'Wait for webots to start listening to commands (in seconds)'
            sleep(2)            

    def simulationEnvironResetPos(self,position):
        '''Reset the khepera robot to position,
           passed as a list of 7 numbers: x, y, z, for translation 
           and a normalized 3D vector plus a rotation angle.'''
        posList = ','.join(str(x) for x in position)
        try:
            self._supervisorSocket.send('S,'+ posList)
#             discard = self._clientSocket.recv(100)
        except SocketError:
            print "I could not reset robot's position"
            
    def stopRobot(self):
        'Stop the robot by setting its velocity to 0'
        try:
            self._clientSocket.send('S,,-1,')
            discard = self._clientSocket.recv(100)
        except SocketError:
            print 'I could not stop the robot'
        
    def finalDisFromTarget(self):
        """Compute the distance from target by asking the supervisor to
        evaluate the distance between a node with 'DEF' = 'TARGET'
        and the KHEPERA robot"""
        
        self._supervisor._clientSocket.send("D")
        response = float(self._supervisor._clientSocket.recv(100)) 
        return response
           
    def getSimulTime(self, webotsRobotSocket):
        "return the Webots simulation time, in simulation seconds"
        try:
            webotsRobotSocket.send("T,,-1,")
            W_time =  mpf(webotsRobotSocket.recv(100))
            print "Received time: %.5f from Webots" % W_time 
            return W_time
        except Exception, e:
            print "Could not connect to the robot client", e
            
    def checkCmdTime(self, webotRobotSocket, cmdTime):
        simulTime = self.getSimulTime(webotRobotSocket)
        if simulTime > (cmdTime * WEBOTS_MIN_TIME_STEP):
            print "Webots simulation ran ahead! Me: %.3f Webots: %.3f" %(cmdTime*WEBOTS_MIN_TIME_STEP, simulTime)
            return False
        else:
            return True

                         
if __name__ == '__main__':
    simul = TestWebotsDeterminism(popSize=50, stepsSize=2000)
    simul.runDetermTest()
