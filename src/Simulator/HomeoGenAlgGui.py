'''
Created on Dec 16, 2014

@author: stefano

Module with classes and functions needed to run a GA simulation of Homeo experiments
'''
from Simulator.HomeoQtSimulation import HomeoQtSimulation
from Helpers.SimulationThread import SimulationThread
from PyQt4.QtCore import *
from PyQt4.QtGui import * 
import sys
import numpy as np
from Simulator.HomeoExperiments import initializeBraiten2_2_Full_GA
import RobotSimulator.WebotsTCPClient
from RobotSimulator.WebotsTCPClient import WebotsTCPClient
from socket import error as SocketError
import os
from math import sqrt
from time import sleep, time, strftime
from tabulate import tabulate

class GA_ConnectionError(Exception):
    def __init__(self, value):
            self.value = value
    def __str__(self):
         return repr(self.value)

class HomeoGASimulation(QWidget):
    '''
    Class managing a Genetic Algorithm simulation, with GUI interface
    '''
    
    def __init__(self, maxRun=1000, parent=None, supervisor_host = '127.0.0.1', supervisor_port = 10021):
        '''
        Create a HomeoQTSimulation object to hold the actual simulation and initialize it. 
        Notice that the GA experiment must be set from within the HomeoQTSimulation class (FIXME).
        Instance variable maxRun holds the number of steps the single simulations should be run
        _supervisor is the socket used to control the Webots supervisor 
                    that allows resetting the Webots simulation
        '''
        super(HomeoGASimulation,self).__init__(parent)
        self._simulation = HomeoQtSimulation(experiment="initializeBraiten2_2_Full_GA")             # instance variable holding the real simulation
        #self._simulation.initializeExperSetup(self.createRandomHomeostatGenome())
        self._maxRun = maxRun
        self._supervisor = WebotsTCPClient(port=supervisor_port)
        

        "prepare to run the simulation itself in a thread"
        self._simulThread = SimulationThread()
        self._simulation.moveToThread(self._simulThread)
        self._simulThread.started.connect(self._simulation.go)
        
        
        "construct the interface"
        self.setWindowTitle('Homeo GA simulation')
        self.setMinimumWidth(400)
 
        self.buildGui()
        self.connectSlots()
        #self._supervisor.clientConnect()
        curDateTime = strftime("%Y%m%d%H%M%S")  
        statsFilename = 'Ga_Statistics-'+curDateTime+'.txt'
        addedPath = 'SimulationsData'
        datafilePath = os.path.join(os.getcwd().split('src/')[0],addedPath)
        fullPathstatsFilename = os.path.join(datafilePath, statsFilename)
        statsFile = open(fullPathstatsFilename,'w')
        self.results = [] 
        popSize = 150
        population = []
        for i in xrange(popSize):
            population.append(self.createRandomHomeostatGenome())  
        timeGen = time()               
        for i in xrange(popSize):
            timeInd = time()
            runResults = []
            runResults.append(str(i+1))
            runResults.append(round(self.evaluateGenomeFitness(steps = 50000, genome = population[i]),4))
            runResults.append(str(round((time() - timeInd),2)))
            for gene in population[i]:
                runResults.append(gene)
            for i in runResults:
                statsFile.write(str(i)+'\t')
            self.results.append(runResults)
            statsFile.write('\n')
            statsFile.flush()
            os.fsync(statsFile)
        self.simulationEnvironQuit()
        statsFile.close()
        headers = ['Run', 'Final distance','Time in secs']
        for i in xrange(len(population[0])):
            headers.append('Gene'+str(i+1))
        print tabulate(self.results, headers, tablefmt='orgtbl')
        print "Total time for generation was: %s" % str(round((time() - timeGen),2))
        
        
            
        #=======================================================================
        # "debugging code"
        # print "Simulation starting....."
        # result = self.finalDisFromTarget(simTarget)
        # print "Final distance from target was: %f" % result
        # print "......simulation over."
        # 
        # "end debugging code"
        #=======================================================================
        
    def buildGui(self):
        '''
        Build the general GUI for the GA simulation
        '''
        
        #mainGui = QDialog()
        'layouts'
        self.controlLayout = QGridLayout()
        self.overallLayout = QVBoxLayout()
        self.textLayout = QVBoxLayout()

        
        'widgets'
        self.initializePopButton = QPushButton("Initialize Population")
        self.noIndividualsSpinBox = QSpinBox()
        self.noIndividualsLabel = QLabel("No of individuals")
        self.startPushButton = QPushButton("Start")
        self.stopPushButton = QPushButton("Stop")
        self.quitPushButton = QPushButton("Quit")
        self.currentFitnessLineEdit = QLineEdit()
        self.currentFitnessLabel = QLabel("Current Fitness")
        self.outputPane = QTextEdit()
        
        self.controlLayout.addWidget(self.initializePopButton,0,0)
        self.controlLayout.addWidget(self.noIndividualsLabel,0,2)
        self.controlLayout.addWidget(self.noIndividualsSpinBox, 0,3)
        self.controlLayout.addWidget(self.currentFitnessLabel, 1,2)
        self.controlLayout.addWidget(self.currentFitnessLineEdit, 1,3)
        self.controlLayout.addWidget(self.startPushButton, 2,0)
        self.controlLayout.addWidget(self.stopPushButton,2,2)
        self.controlLayout.addWidget(self.quitPushButton,2,3)
        
        'text pane'
        self.textLayout.addWidget(self.outputPane)
        
        self.overallLayout.addLayout(self.controlLayout)
        self.overallLayout.addLayout(self.textLayout)
        self.setLayout(self.overallLayout)
        #return mainGui

    def connectSlots(self):
        pass

    def createRandomHomeostatGenome(self,noUnits=6, essentParams=4):
        '''Create a list containing the essential parameters for every
           units in a fully  connected Homeostat and the weights of
           all the connections.
           All values are in the [0,1] range. It is the responsibility of
           the Homeostat- and connections-instantiating method to scale these 
           values to the Units' appropriate ranges.
           
           Basic essential parameters are 5: mass, viscosity,
           uniselectorTiming, and maxDeviation.
           
           (The potentiometer is also an essential parameter, but it is specified as one of the unit's
            connections)
        '''          
        return np.random.uniform(size=(noUnits * (essentParams + noUnits)))

    def simulationEnvironReset(self):
        """Reset webots simulation.
         Do not return from function until the simulation has really exited 
         and the previous tcp/ip socket is no longer valid.
        """
        try:
            self._supervisor._clientSocket.send("R")
            response = self._supervisor._clientSocket.recv(100) 
            #print "Reset Webots simulation: received back %s from server" %response
            try:
                while True:
                    self._supervisor._clientSocket.send(".")
                    sleep(0.05)
            except SocketError:
                pass
        except SocketError:
            raise GA_ConnectionError("statsFileCould not reset Webots simulation")
        
    def simulationEnvironResetPhysics(self):
        "Reset Webots simulation physics"
        try:
            self._supervisor._clientSocket.send("P")
            response = self._supervisor._clientSocket.recv(100) 
            print "Reset Webots simulation physics: received back %s from server" %response
        except SocketError:
            raise GA_ConnectionError("Could not reset Webots simulation's physics")
            
    
    def simulationEnvironQuit(self):
        "Quit Webots application"
        try:
            self._supervisor._clientSocket.send("Q")
            response = self._supervisor._clientSocket.recv(100) 
            print "Quit Webots: received back %s from server" %response
        except SocketError:
            raise GA_ConnectionError("Could not quit Webots")
        
    def evaluateGenomeFitness(self,genome=None, steps = 1000, target=None):
        """Run a simulation for a given number of steps on the given genome.
           Return final distance from target"""
            
        if genome==None:
            genome=self.createRandomHomeostatGenome()
        self._simulation.initializeExperSetup(genome)
        self._supervisor.clientConnect()
        self.simulationEnvironReset()
        self._supervisor.close()
        self._supervisor.clientConnect()
        self._simulation.homeostat.connectUnitsToNetwork()
        self._simulation.maxRuns = steps
        "Initialize live data recording and display "
        self._simulation.initializeLiveData()

        self._simulThread.start()
        timeNow = time()
        #=======================================================================
        # print "Simulation started at time: %f" % timeNow  
        # # print "Steps....",
        # for i in xrange(steps):
        #     print "Step: ", str(i+1)
        #     self._simulation.step()
        #=======================================================================
        self._simulation.go()
        print "Elapsed time in seconds was %s" % str(round((time() - timeNow),3))
        finalDis =self.finalDisFromTarget()
        print "Final distance from target was: ", finalDis
        return finalDis
        
    def finalDisFromTarget(self):
        '''Compute the distance from target by asking the supervisor to
        evaluate the distance between a node with 'DEF' = 'TARGET'
        and the KHEPERA robot'''
        
        self._supervisor._clientSocket.send("D")
        response = float(self._supervisor._clientSocket.recv(100)) 
        return response
        
    def finalDisFromTargetFromFile(self, target):
        """ Compute the distance between robot and target at
        the end of the simulation.
        
        Target must be passed to function as a list of 2 floats (x-coord, y-coord)
        
        Read the robot's final position from the trajectory data file
        
        Assume that the current directory is under a "src" directory
        and that a data folder called 'SimulationsData will exist
        at the same level as "src"
        Assume also that the trajectory data filename will start with 
        the string filenamePattern and will include date and time info in the filename
        so they properly sort in time order
        Get the most recent file fulfilling the criteria
        """ 
        
#===============================================================================
#         FIXME: The method read the robot's final distance from the last of the most 
#         recent trajectory log. It would be more robust to ask the C++ supervisor 
#         controlling the simulation to return the robot's final position.
# 
#         FIXME 2: The target is currently specified in the Homeo GA general interface. 
#         It would be more robust to indicate the target within Webots itself, and then 
#         ask the C++ supervisor to return the distance. 
#=============================================================================== 

        addedPath = 'SimulationsData'
        datafilePath = os.path.join(os.getcwd().split('src/')[0],addedPath)
        fileNamepattern = 'trajectoryData'
        try:
            trajDataFilename = max([ f for f in os.listdir(datafilePath) if f.startswith(fileNamepattern) ])
        except ValueError:
            print "The file I tried to open was:", os.path.join(datafilePath, max([ f for f in os.listdir(datafilePath) if f.startswith(fileNamepattern)]))
            messageBox =  QMessageBox.warning(self, 'No data file', 'There are no trajectory data to visualize', QMessageBox.Cancel)
            messageBox.show()
        fullPathTrajFilename = os.path.join(datafilePath, trajDataFilename)
        robotFinalPos =os.popen("tail --lines=1 " + fullPathTrajFilename).read()
        robotX = float(robotFinalPos.split('\t')[0])
        robotY = float(robotFinalPos.split('\t')[1])
        #=======================================================================
        # print "Robot's final position is at x: %f\t y:%d" % (robotX,robotY)
        # print "Target is at x: %f\t y: %f" % (target[0],target[1])
        # print "Distance to target is: ", sqrt((target[0]-robotX)**2 + (target[1]-robotY)**2)
        #=======================================================================
        return sqrt((target[0]-robotX)**2 + (target[1]-robotY)**2)
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    simul = HomeoGASimulation()
    #simul.show()
    #app.exec_()
