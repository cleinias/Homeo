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
from Helpers.QtSeparator import Separator
'''
Created on Apr 23, 2013

@author: stefano
'''

from PyQt4.QtCore import *
from PyQt4.QtGui import * 
from Core.Homeostat import *
from Simulator.HomeoQtSimulation import *
from Helpers.QObjectProxyEmitter import emitter
from Helpers.SimulationThread import SimulationThread

class HomeoTestGui(QDialog):    
    '''
    A minimal GUI for a HomeoSimulation. 
    It just provide access to starting and stopping the simulation and to saving and graphing data.
    It does not provide interactive real-time access to the homeostat 
    
    The simulation itself is run in a separate thread held in simulThread. 

    Instance Variables:
        simulation                  <aHomeoQtSimulation>  The simulation being controlled
        simulThread                <aSimulationThread>    The QT thread holding the simulation run
    '''
    def __init__(self, parent = None):
        '''
        Build all the widgets and layouts and set them up with proper connections
        Initialize the iVars to hold on to the simulation being run 
        '''

        super(HomeoTestGui,self).__init__(parent)
        
        self._simulation = HomeoQtSimulation()
        self._simulation.initializeAshbySimulation()
        
        self._simulThread = SimulationThread()
        self._simulation.moveToThread(self._simulThread)
        self._simulThread.started.connect(self._simulation.go)

        "Widgets"
        'Labels'
        self.maxRunsLabel = QLabel("Max Runs")
        self.currentTimeLabel = QLabel("Current time")
        self.slowingFactorLabel = QLabel("Slowing Factor (millisec.)")
        'Buttons'
        self.startButton = QPushButton("Start")
        self.pauseButton = QPushButton("Stop")
        self.stepButton = QPushButton("Step")
        self.resumeButton = QPushButton("Resume")
        self.resetValuesButton = QPushButton("Reset unit values")
        self.resetTimeButton = QPushButton("Reset time")
        self.debugModeButton = QPushButton("Debug Mode")
        self.debugModeButton.setCheckable(True)   #Turn push button into a Toggle Button
        self.showUniselActionButton = QPushButton("Show Unisel. Action")
        self.showUniselActionButton.setCheckable(True)
        
        'Spinboxes and lineEdits'
        self.maxRunSpinBox = QSpinBox()
        self.currentTimeSpinBox = QSpinBox()
        self.slowingFactorSpinBox = QSpinBox()
        
        self.maxRunSpinBox.setRange(0,100000)
        self.maxRunSpinBox.setValue(self._simulation.maxRuns)
        
        self.currentTimeSpinBox.setRange(0,100000)
        self.currentTimeSpinBox.setValue(self._simulation.homeostat.time)
        self.currentTimeSpinBox.setReadOnly(True)
        
        self.slowingFactorSpinBox.setRange(0.1,1000)
        self.slowingFactorSpinBox.setValue(self._simulation.homeostat.slowingFactor)
        
        "Separators"
        self.runningSectionSep1 = Separator()
        self.runningSectionSep2 = Separator()
        
        
        "Layout"
        layout = QGridLayout()
        
        'Top row (0)'
        layout.addWidget(self.startButton, 0,0,1,3)
        
        'Row 1'
        layout.addWidget(self.runningSectionSep1, 1,1)
        
        'Row 2'
        layout.addWidget(self.pauseButton, 2,0)
        layout.addWidget(self.resumeButton, 2,1)
        layout.addWidget(self.stepButton, 2,2)
        
        'Row 3'
        layout.addWidget(self.maxRunsLabel, 3,0)
        layout.addWidget(self.maxRunSpinBox, 3,1)
        
        'Row 4'
        layout.addWidget(self.currentTimeLabel,4,0)
        layout.addWidget(self.currentTimeSpinBox,4,1)
        
        'Row 5'
        layout.addWidget(self.slowingFactorLabel, 5,0)
        layout.addWidget(self.slowingFactorSpinBox, 5,1)

        'Row 6'
        layout.addWidget(self.runningSectionSep2,6,1)
        
        'Row 7'
        layout.addWidget(self.resetValuesButton,7,0)
        layout.addWidget(self.debugModeButton,7,2)
                
        'Row 8'
        layout.addWidget(self.resetTimeButton,8,0)
        layout.addWidget(self.showUniselActionButton, 8,2)
        
        self.setLayout(layout)
        
        
        "Connections"
        self.startButton.clicked.connect(self.go)
        self.pauseButton.clicked.connect(self.pause)
        self.resumeButton.clicked.connect(self.resume)
        self.stepButton.clicked.connect(self.step)
        self.maxRunSpinBox.valueChanged.connect(self._simulation.setMaxRuns)
        self.resetValuesButton.clicked.connect(self._simulation.homeostat.randomizeValuesforAllUnits)
        self.resetTimeButton.clicked.connect(self._simulation.timeReset)
        self.slowingFactorSpinBox.valueChanged.connect(self._simulation.setSimulDelay)
        self.debugModeButton.clicked.connect(self._simulation.toggleDebugMode)
        self.showUniselActionButton.clicked.connect(self.toggleShowUniselAction)

        QObject.connect(emitter(self._simulation.homeostat), SIGNAL("homeostatTimeChanged"), self.currentTimeSpinBox.setValue)
        
        self.setWindowTitle("Homeo Simulation")
        
        
    def go(self):
        'Start simulation. Disable Go Resume, and Step buttons'
        'need to use it as a toggle to start/stop machine with an iVar checking if the QThread is running '
        self.pauseButton.setEnabled(True)
        self.startButton.setEnabled(False)
        self.stepButton.setEnabled(False)
        self.resumeButton.setEnabled(False)
        self._simulThread.start()
        
    def pause(self):
        'Pause simulation. Disable stop button, re-enable resume and step buttons'
        self.pauseButton.setEnabled(False)
        self.resumeButton.setEnabled(True)
        self.stepButton.setEnabled(True)
        self._simulation.pause()

    def resume(self):
        'Resume simulation. Disable resume and step buttons, re-enable stop button'
        self.pauseButton.setEnabled(True)
        self.resumeButton.setEnabled(False)
        self.stepButton.setEnabled(False)
        self._simulation.resume()
        
    def step(self):
        'Step simulation'
        self._simulation.step()               
        
    def toggleShowUniselAction(self):
        self._simulation.toggleShowUniselectorAction()
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    simul = HomeoTestGui()
    simul.show()
    app.exec_()
        