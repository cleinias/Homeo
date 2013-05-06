'''
Provides a minimal interface to control a Homeostat simulation.
It can start and stop a simulation from a GUI, as well as save and graph the simulation's data. 
Created on May 5, 2013
@author: stefano
'''

from PyQt4.QtCore import *
from PyQt4.QtGui import * 
from Core.Homeostat import *
from Helpers.QtSeparator import Separator
from Simulator.HomeoQtSimulation import *
from Helpers.QObjectProxyEmitter import emitter
from Helpers.SimulationThread import SimulationThread
import matplotlib.pyplot as plt
import pyqtgraph as pg

class HomeoMinimalGui(QDialog):    
    '''
    A minimal GUI for a HomeoSimulation. 
    It just provide access to starting and stopping the simulation and to saving and graphing data.
    It does not provide interactive real-time access to the homeostat 
    
    The simulation itself is run in a separate thread held in simulThread. 

    Instance Variables:
        simulation                 <aHomeoQtSimulation>  The simulation being controlled
        simulThread                <aSimulationThread>    The QT thread holding the simulation run
    '''
    def __init__(self, parent = None):
        '''
        Build all the widgets and layouts and set them up with proper connections
        Initialize the iVars to hold on to the simulation being run 
        '''

        super(HomeoMinimalGui,self).__init__(parent)
        
        self._simulation = HomeoQtSimulation()
        self._simulation.initializeAshbySimulation()
        
        self._simulThread = SimulationThread()
        self._simulation.moveToThread(self._simulThread)
        self._simulThread.started.connect(self._simulation.go)


#===============================================================================
# Simulation control pane
#===============================================================================
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
        self.discardDataButton = QPushButton("Discard data")
        self.discardDataButton.setCheckable(True)
        
        'Spinboxes and lineEdits'
        self.maxRunSpinBox = QSpinBox()
        self.currentTimeSpinBox = QSpinBox()
        self.slowingFactorSpinBox = QDoubleSpinBox()
        
        self.maxRunSpinBox.setRange(0,10000000)
        
        self.currentTimeSpinBox.setRange(0,10000000)
        self.currentTimeSpinBox.setReadOnly(True)
        
        self.slowingFactorSpinBox.setRange(0.001,1000)
        
        "Separators"
        self.runningSectionSep1 = Separator()
        self.runningSectionSep2 = Separator()
        
        
        "Layout"
        simulationPaneLayout = QGridLayout()
        
        'Top row (0)'
        simulationPaneLayout.addWidget(self.startButton, 0,0,1,3)
        
        'Row 1'
        simulationPaneLayout.addWidget(self.runningSectionSep1, 1,1)
        
        'Row 2'
        simulationPaneLayout.addWidget(self.pauseButton, 2,0)
        simulationPaneLayout.addWidget(self.resumeButton, 2,1)
        simulationPaneLayout.addWidget(self.stepButton, 2,2)
        
        'Row 3'
        simulationPaneLayout.addWidget(self.maxRunsLabel, 3,0)
        simulationPaneLayout.addWidget(self.maxRunSpinBox, 3,1)
        
        'Row 4'
        simulationPaneLayout.addWidget(self.currentTimeLabel,4,0)
        simulationPaneLayout.addWidget(self.currentTimeSpinBox,4,1)
        
        'Row 5'
        simulationPaneLayout.addWidget(self.slowingFactorLabel, 5,0)
        simulationPaneLayout.addWidget(self.slowingFactorSpinBox, 5,1)

        'Row 6'
        simulationPaneLayout.addWidget(self.runningSectionSep2,6,1)
        
        'Row 7'
        simulationPaneLayout.addWidget(self.resetValuesButton,7,0)
        simulationPaneLayout.addWidget(self.discardDataButton,7,1)
        simulationPaneLayout.addWidget(self.debugModeButton,7,2)
                
        'Row 8'
        simulationPaneLayout.addWidget(self.resetTimeButton,8,0)
        simulationPaneLayout.addWidget(self.showUniselActionButton, 8,2)
        
        "Initial values"
        self.maxRunSpinBox.setValue(self._simulation.maxRuns)
        self.currentTimeSpinBox.setValue(self._simulation.homeostat.time)
        self.slowingFactorSpinBox.setValue(self._simulation.homeostat.slowingFactor)

        "Connections"
        self.startButton.clicked.connect(self.go)
        self.pauseButton.clicked.connect(self.pause)
        self.resumeButton.clicked.connect(self.resume)
        self.stepButton.clicked.connect(self.step)
        self.maxRunSpinBox.valueChanged.connect(self._simulation.setMaxRuns)
        self.resetValuesButton.clicked.connect(self._simulation.homeostat.randomizeValuesforAllUnits)
        self.resetTimeButton.clicked.connect(self.timeReset)
        self.slowingFactorSpinBox.valueChanged.connect(self._simulation.setSimulDelay)
        self.debugModeButton.clicked.connect(self._simulation.toggleDebugMode)
        self.showUniselActionButton.clicked.connect(self.toggleShowUniselAction)
        self.discardDataButton.clicked.connect(self.toggleDiscardData)

        QObject.connect(emitter(self._simulation.homeostat), SIGNAL("homeostatTimeChanged"), self.currentTimeSpinBox.setValue)
        
#===============================================================================
# Homeostat control pane and saving/plotting data       
#===============================================================================

        "Widgets"
        self.homeostatLabel = QLabel("Current homeostat")
        self.homeostatLineEdit = QLineEdit()
        self.noOfUnitsLabel = QLabel("Number of units")
        self.noOfUnitsLineEdit = QLineEdit()
        self.homeostatActionsLabel = QLabel("Homeostat actions")
        self.dataActionsLabel = QLabel("Data Actions")
        self.newHomeostatButton = QPushButton("New")
        self.loadHomeostatButton = QPushButton("Load")
        self.saveHomeostatButton = QPushButton("Save")
        self.saveDataButton = QPushButton("Save all data")
        self.saveGraphDataButton = QPushButton("Save plot data")
        self.graphButton = QPushButton("Graph")

        "layout"
        homeostatPaneLayout = QGridLayout()
        
        'Top Row (0)'       
        homeostatPaneLayout.addWidget(self.homeostatLabel, 0,0,1,2)
        
        'Row 1'
        homeostatPaneLayout.addWidget(self.homeostatLineEdit, 1,0,1,2)
        
        'Row 2'
        homeostatPaneLayout.addWidget(self.noOfUnitsLabel,2,0)
        homeostatPaneLayout.addWidget(self.noOfUnitsLineEdit,2,1)
        
        'Row 3'
        homeostatPaneLayout.addWidget(Separator(), 3,0,1,2)
        
        'Row 4'
        homeostatPaneLayout.addWidget(self.homeostatActionsLabel, 4,0)
        homeostatPaneLayout.addWidget(self.dataActionsLabel,4,1)
        
        'Row 5'
        homeostatPaneLayout.addWidget(self.newHomeostatButton,5,0)
        homeostatPaneLayout.addWidget(self.saveDataButton, 5,1)
        
        'Row 6'
        homeostatPaneLayout.addWidget(self.loadHomeostatButton, 6,0)
        homeostatPaneLayout.addWidget(self.saveGraphDataButton, 6,1)

        'Row 7'
        homeostatPaneLayout.addWidget(self.saveHomeostatButton,7,0)
        homeostatPaneLayout.addWidget(self.graphButton,7,1)
        
        self.vertSeparator = QFrame()
        self.vertSeparator.setFrameShape(QFrame.VLine)
        self.vertSeparator.setFrameShadow(QFrame.Sunken)
        homeostatPaneLayout.addWidget(self.vertSeparator, 0,3,7,1)
        
        "Initial Values"
        self.homeostatLineEdit.setText(self._simulation.homeostatFilename)
        self.noOfUnitsLineEdit.setText(str(len(self._simulation.homeostat.homeoUnits)))
        self.noOfUnitsLineEdit.setReadOnly(True)
                                       
        "Connections"
        self.homeostatLineEdit.returnPressed.connect(self._simulation.setHomeostatFilename)
        QObject.connect(self._simulation, SIGNAL("homeostatFilenameChanged"), self.homeostatLineEdit.setText)

        self.newHomeostatButton.clicked.connect(self.newHomeostat)
        self.loadHomeostatButton.clicked.connect(self.loadHomeostat)
        self.saveHomeostatButton.clicked.connect(self.saveHomeostat)
        self.saveDataButton.clicked.connect(self.saveAllData)
        self.saveGraphDataButton.clicked.connect(self.savePlotData)
        self.graphButton.clicked.connect(self.graphData)
                
#===============================================================================
# Global layout        
#===============================================================================

        layout = QHBoxLayout()
        layout.addLayout(homeostatPaneLayout)
        layout.addLayout(simulationPaneLayout)
        self.setLayout(layout)



        
        self.setWindowTitle("Homeo Simulation")
        
#===============================================================================
# Slots (local to the GUI)       
#===============================================================================

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
    
    def timeReset(self):
        "Reset Simulation time to 0, enable resume and step button, disable stop button"
        self._simulation.timeReset()
        self.pauseButton.setEnabled(False)
        self.stepButton.setEnabled(True)
        self.resumeButton.setEnabled(True)
                 
    def toggleShowUniselAction(self):
        self._simulation.toggleShowUniselectorAction()
        
    def toggleDiscardData(self):
        self._simulation.toggleDiscardData()
        
        
    def loadHomeostat(self):
        filename = QFileDialog.getOpenFileNameAndFilter(parent=self, 
                                                        caption=QString("Choose a Homeostat file to open"), 
                                                        filter = QString("Homeostats (*.pickled);;All files (*.*)"))[0]   #QFileDialog.GetOpen returns a tuple
        if len(filename) > 0:
            try:
                self._simulation.loadNewHomeostat(filename)
                QObject.connect(emitter(self._simulation.homeostat), SIGNAL("homeostatTimeChanged"), self.currentTimeSpinBox.setValue)
                self._simulation.timeReset()
                self.stepButton.setEnabled(True)
                self.resumeButton.setEnabled(True)
                self.pauseButton.setEnabled(False)
            except HomeostatError as e:
                messageBox = QMessageBox()
                messageBox.setText(e.__str__())
                messageBox.exec_()

    
    def saveHomeostat(self):
        filename = QFileDialog.getSaveFileName(parent = self, 
                                                       caption = 'Choose the file to save the Homeostat to', 
                                                       directory = self._simulation.homeostatFilename)    #QFileDialog.GetSave returns a QString
        print filename
        if len(filename) > 0:                            # Change the filename to the newly selected one
            self._simulation.homeostatFilename = filename
            #if #Check that files exists here"
            self._simulation.save()
            self._simulation.homeostatIsSaved = True
        else:                                               # Use the current filename
            self._simulation.save()
            self._simulation.homeostatIsSaved = True

    def newHomeostat(self):
        self._simulation.fullReset()
        self.homeostatLineEdit.setText(self._simulation.homeostatFilename)
        self.noOfUnitsLineEdit.setText(str(len(self._simulation.homeostat.homeoUnits)))
        self.pauseButton.setEnabled(False)
        self.stepButton.setEnabled(True)
        self.resumeButton.setEnabled(True)
    
    def saveAllData(self):       
        filename = QFileDialog.getSaveFileName(parent = self, 
                                                       caption = "Save simulation's complete data", 
                                                       directory = self._simulation.dataFilename)    #QFileDialog.GetSave returns a QString
        print filename
        if len(filename) > 0:                            # Change the filename to the newly selected one
            self._simulation.dataFilename = filename
        self._simulation.saveCompleteRunOnFile(filename)
        self._simulation.dataAreSaved = True
                
    def savePlotData(self):
        filename = QFileDialog.getSaveFileName(parent = self, 
                                                       caption = "Save simulation's essential data", 
                                                       directory = (self._simulation.dataFilename + "-essential.txt"))    #QFileDialog.GetSave returns a QString
        print filename
        if len(filename) <= 0:                            # Change the filename to the newly selected one
            filename = (self._simulation.dataFilename + "-essential.txt") 
        self._simulation.saveEssentialDataOnFile(filename)


    def graphData(self):
        dataArray = self._simulation.homeostat.dataCollector.criticalDevAsNPArrayForAllUnits() 
        plt.plot(dataArray)
        plt.ylabel('Critical Deviation')
        plt.xlabel('Time')
        plt.show()
#        pg.plot(dataArray)
#        pg.show()
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    simul = HomeoMinimalGui()
    simul.show()
    app.exec_()
               
            