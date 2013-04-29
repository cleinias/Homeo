'''
Provides a test interface to control a Homeostat simulation.
It can only start and stop a simulation from a GUI. 
Created on Apr 23, 2013
@author: stefano
'''

from PyQt4.QtCore import *
from PyQt4.QtGui import * 
from Core.Homeostat import *
from Simulator.HomeoSimulation import *
'''
Created on Apr 23, 2013

@author: stefano
'''

from PyQt4.QtCore import *
from PyQt4.QtGui import * 
from Core.Homeostat import *
from Simulator.HomeoSimulation import *
from threading import Thread
from Helpers.QObjectProxyEmitter import emitter


class HomeoTestGui(QDialog):    
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

        super(HomeoTestGui,self).__init__(parent)
        
        self._simulation = HomeoSimulation()
        self._simulation.initializeAshbySimulation()
        
        self._simulProcess = Thread(target = self._simulation.start)

        "Widgets"
        self.maxRunsLabel = QLabel("Max Runs")
        self.currentTimeLabel = QLabel("Current time")
        self.slowingFactorLabel = QLabel("Slowing Factor (millisec.)")
        
        self.startButton = QPushButton("Start")
        self.stopButton = QPushButton("Stop")
        self.stepButton = QPushButton("Step")
        self.resetValuesButton = QPushButton("Reset unit values")
        self.resetTimeButton = QPushButton("Reset time")
        self.debugModeButton = QPushButton("Debug Mode")
        self.showUniselActionButton = QPushButton("Show Uniselector Action")
        
        self.maxRunSpinBox = QSpinBox()
        self.currentTimeSpinBox = QSpinBox()
        self.slowingFactorSpinBox = QSpinBox()
        
        self.maxRunSpinBox.setRange(0,100000)
        self.maxRunSpinBox.setValue(self._simulation.maxRuns)
        
        self.currentTimeSpinBox.setRange(0,100000)
        self.currentTimeSpinBox.setValue(self._simulation.homeostat.time)
        
        self.slowingFactorSpinBox.setRange(0.1,1000)
        self.slowingFactorSpinBox.setValue(self._simulation.homeostat.slowingFactor)
        
        
        "Layout"
        layout = QGridLayout()
        layout.addWidget(self.maxRunsLabel,0,0)
        layout.addWidget(self.currentTimeLabel,1,0)
        layout.addWidget(self.slowingFactorLabel,2,0)
        
        layout.addWidget(self.startButton, 4,1)
        layout.addWidget(self.stopButton, 4, 0)
        layout.addWidget(self.stepButton, 4,2)
        layout.addWidget(self.resetValuesButton, 0,2)
        layout.addWidget(self.resetTimeButton,1,2 )
        layout.addWidget(self.debugModeButton,2,2 )
        layout.addWidget(self.showUniselActionButton,3,2)
        
        layout.addWidget(self.maxRunSpinBox,0,1)
        layout.addWidget(self.currentTimeSpinBox,1,1)
        layout.addWidget(self.slowingFactorSpinBox,2,1)
        
        self.setLayout(layout)
        
        
        "Connections"
        self.connect(self.stopButton, SIGNAL("clicked()"), self._simulation.stop)
        self.connect(self.startButton, SIGNAL("clicked()"), self._simulProcess.start)
        self.connect(emitter(self._simulation.homeostat), SIGNAL("homeostatTimeChanged(int)"), self.currentTimeSpinBox.setValue)
        
        
        
        self.setWindowTitle("Homeo Simulation")
        
        
     
        
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    simul = HomeoTestGui()
    simul.show()
    app.exec_()
        