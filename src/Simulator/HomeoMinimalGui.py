'''
Provides a minimal interface to control a Homeostat simulation.
It can start and stop a simulation from a GUI, as well as save and graph the simulation's data. 
Created on Apr 23, 2013
@author: stefano
'''

from PyQt4.QtCore import *
from PyQt4.QtGui import * 
from Core.Homeostat import *
from Simulator.HomeoSimulation import *
from threading import Thread


class HomeoMinimalGui(QDialog):
    
    '''
    A minimal GUI for a HomeoSimulation. 
    It just provide access to starting and stopping the simulation and to saving and graphing data.
    It does not provide interactive real-time access to the homeostat 
    
    The simulation itself is run in a separate thread held in simulProcess. 

    Instance Variables:
        simulation                  <aHomeosimulation>  The simulation being controlled
        simulProcess                <aProcess>          the thread holding the simulation run
    '''
    def __init__(self, parent = None):
        '''
        Build all the widgets and layouts and set them up with proper connections
        Initialize the iVars to hold on to the simulation being run 
        '''
        self._simulation = HomeoSimulation()
        "initialize the simulation here, see ST code"
        
        self._simulProcess = Thread(target = self._simulation.start)
        self._startButton = QPushButton("Start")
        self._stopButton = QPushButton("Stop")
        super(HomeoMinimalGui,self).__init__(parent)
        layout = QVBoxLayout()
        layout.add(self.startButton)
        layout.add(self.stopButton)
        self.connect(self._startButton, SIGNAL("clicked()"), self._simulProcess.start())
        self.connect(self._stopButton, SIGNAL("clicked()"), self._simulation.stop())
        self.setWindowTitle("Homeo Simulation")
        
        
if __name__ == 'main':
    app = QApplication()
    simul = HomeoMinimalGui()
    simul.show()
    app.exec_()
        
            