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

class HomeoGASimulation(QWidget):
    '''
    Class managing a Genetic Algorithm simulation, with GUI interface
    '''
    
    def __init__(self, maxRun=1000, parent=None):
        '''
        Create a HomeoQTSimulation object to hold the actual simulation and initialize it. 
        Notice that the GA experiment must be set from within the HomeoQTSimulation class (FIXME).
        Instance variable maxRun holds the number of steps the single simulations should be run
        
        '''
        super(HomeoGASimulation,self).__init__(parent)
        self._simulation = HomeoQtSimulation(experiment="initializeBraiten2_2_Full_GA")             # instance variable holding the real simulation
        self._simulation.initializeExperSetup(self.createRandomHomeostatGenome())
        self._maxRun = maxRun
        

        "prepare to run the simulation itself in a thread"
        self._simulThread = SimulationThread()
        self._simulation.moveToThread(self._simulThread)
        self._simulThread.started.connect(self._simulation.go)
        
        "construct the interface"
        self.setWindowTitle('Homeo GA simulation')
        self.setMinimumWidth(400)

        self.buildGui()
        self.connectSlots()
        
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

    def runOneShotSimulation(self, genome, steps = 1000):
        'Run a complete simulation of a robot instantiated to given genome'
        
        '1. Initialize robot to given genome'
        
        '2. Reset simulation environment'
         
        '3. Run simulation'
        
        '4. Return fitness value'
        pass

    def resetRobot(self):
        'Reset the robotic simulation to initial conditions'
        pass
    
    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    simul = HomeoGASimulation()
    simul.show()
    app.exec_()
