'''
Created on Dec 16, 2014

@author: stefano

Module with classes and functions needed to run a GA simulation of Homeo experiments
'''
from Simulator.HomeoQtSimulation import HomeoQtSimulation
from Helpers.SimulationThread import SimulationThread
from PyQt4.QtCore import *
from PyQt4.QtGui import * 

import numpy as np

class HomeoGASimulation(object):
    '''
    Class managing a Genetic Algorithm simulation, with GUI interface
    '''

    def __init__(self, maxRun=1000):
        '''
        Create a HomeoQTSimulation object to hold the actual simulation and initialize it. 
        Notice that the GA experiment must be set from within the HomeoQTSimulation class (FIXME).
        Instance variable maxRun holds the number of steps the single simulations should be run
        
        '''
        self._simulation = HomeoQtSimulation()             # instance variable holding the real simulation
        self._simulation.initializeExperSetup(self.createRandomHomeostatGenome())
        self._maxRun = maxRun
        

        "prepare to run the simulation itself in a thread"
        self._simulThread = SimulationThread()
        self._simulation.moveToThread(self._simulThread)
        self._simulThread.started.connect(self._simulation.go)
        

    def createRandomHomeostatGenome(self,noUnits=4, essentParams=5):
        '''Create a list containing the essential parameters for every
           units in a fully  connected Homeostat and the weights of
           all the connections.
           All values are in the [0,1] range. It is the responsibility of
           the Homeostat- and connections-instantiating method to scale these 
           values to the Units' appropriate ranges.
           
           Basic essential parameters are 5: mass, viscosity, potentiometer,
           uniselectorTiming, and maxDeviation.
        '''          
        return np.random.uniform(size=(noUnits * (essentParams + noUnits)))
        
    def runOneShotSimulation(self):
        pass



if __name__ == '__main__':
    app = QApplication(sys.argv)
#    simul = HomeoSimulationControllerGui()
#    simul.show()
    app.exec_()
