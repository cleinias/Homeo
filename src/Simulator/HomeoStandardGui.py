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
from StringIO import StringIO
from Simulator.Four_units_Homeostat_Standard_UI import Ui_ClassicHomeostat
from math import floor
from itertools import cycle


class HomeoSimulationControllerGui(QDialog):    
    '''
    Part of a complete GUI for  a HomeoSimulation. 
    It provides access to starting and stopping the simulation and to saving and graphing data.
    Real-time interactive access to the homeostat is provided by class Classic_Homeostat,
    which this class instantiates and then modify.
    
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

        super(HomeoSimulationControllerGui,self).__init__(parent)
        
        self._simulation = HomeoQtSimulation()
        self._simulation.initializeAshbySimulation()
#        self._simulation.initializeAshbyFirstExperiment()
        self._simulation.initializeLiveData()
        
        'Construct the dialog in code, and initialize and connect its widgets'
        '''Create an empty dictionary indexed by HomeoUnits to hold references to 
           all the pyQtGraph plot widgets and plotDataItems, used to visualize the data.
           For each unit, the dictionary item has has 4-tuple of refs:   
           - ref to Unit PlotItem,
           - ref to Unit PlotDataItem
           - ref to Unit Uniselector Activated PlotItem,
           - ref to Unit Uniselector Activated PlotDataItem'''
        self.pgChartsAndItems= {}  # 
        self.setupSimulationDialog()
        

        "Create the main interface window for the 4 unit homeostat, initialize and connect its widget"
        self._homeostat_gui = Classic_Homeostat(parent=self)
        self.setupHomeostatGuiDialog()
        self._homeostat_gui.move(300,0)
        self._homeostat_gui.show()
#        sys.stderr.write(self.geometry())
#        sys.stderr.write(self._homeostat_gui.geometry())
        
        "prepare to run the simulation itself in a thread"
        self._simulThread = SimulationThread()
        self._simulation.moveToThread(self._simulThread)
        self._simulThread.started.connect(self._simulation.go)



    def setupSimulationDialog(self):
        """ 
        Construct the dialog containing all the button and parameters 
        necessary to run the simulation. 
        The dialog has two 'logical' panes: a simulation control pane
        on the right, and a homeostat control pane on the right
        """   
    
        #===================================================================
        # Simulation control pane
        #===================================================================
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
        self.discardDataButton.setChecked(not self._simulation.homeostat.collectsData)  
        
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
#        self.dataWindow = QLineEdit()

        "checkBoxes"
        self.liveDataOnCheckbox = QCheckBox("Charts on")
        self.liveDataWindowCheckBox = QCheckBox('Panning data')
        

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
        
        'Row 8'
        homeostatPaneLayout.addWidget(self.liveDataOnCheckbox, 8,0,1,1)
        homeostatPaneLayout.addWidget(self.liveDataWindowCheckBox, 8, 1,1,1)
#        homeostatPaneLayout.addWidget(self.dataWindow, 8,2,1,1)
        
        self.vertSeparator = QFrame()
        self.vertSeparator.setFrameShape(QFrame.VLine)
        self.vertSeparator.setFrameShadow(QFrame.Sunken)
        homeostatPaneLayout.addWidget(self.vertSeparator, 0,3,7,1)
        
        "Initial Values"
        self.homeostatLineEdit.setText(self._simulation.homeostatFilename)
        self.noOfUnitsLineEdit.setText(str(len(self._simulation.homeostat.homeoUnits)))
        self.noOfUnitsLineEdit.setReadOnly(True)
        self.liveDataWindowCheckBox.setChecked(self._simulation.panningCharts)
                                       
        "Connections"
        self.homeostatLineEdit.returnPressed.connect(self._simulation.setHomeostatFilename)
        QObject.connect(self._simulation, SIGNAL("homeostatFilenameChanged"), self.homeostatLineEdit.setText)

        self.newHomeostatButton.clicked.connect(self.newHomeostat)
        self.loadHomeostatButton.clicked.connect(self.loadHomeostat)
        self.saveHomeostatButton.clicked.connect(self.saveHomeostat)
        self.saveDataButton.clicked.connect(self.saveAllData)
        self.saveGraphDataButton.clicked.connect(self.savePlotData)
        self.graphButton.clicked.connect(self.graphData)
        self.liveDataOnCheckbox.stateChanged.connect(self._simulation.toggleLivedataOn)
        self.liveDataWindowCheckBox.stateChanged.connect(self.toggleLiveDataWindow)
        
        
        #=======================================================================
        # Output and Err panel
        #=======================================================================
        # Uncomment the following to add a stdout/stderr text widget
        # Need to work on class Outlog first
        #=======================================================================
        # self.outAndErr = QTextEdit()
        # sys.stdout = OutLog(self.outAndErr, sys.stdout)
        # sys.stderr = OutLog(self.outAndErr, sys.stderr, QColor(255,0,0) ) 
        # completeLayout = QVBoxLayout()
        # completeLayout.addLayout(layout)
        # completeLayout.addWidget(self.outAndErr)
        # self.setLayout(completeLayout)
        #=======================================================================
        #=======================================================================

        
                
        #===============================================================================
        # Homeostat control pane and Simulation control pane  layout        
        #===============================================================================
        
        layout = QHBoxLayout()
        layout.addLayout(homeostatPaneLayout)
        layout.addLayout(simulationPaneLayout)
        
        #====================================================================================================================
        # Adding  Plot widget(s) and plotDataItems with PyQtGraph - perhaps add 2 * units (crit dev + uniselector for each)
        #====================================================================================================================
        completeLayout = QVBoxLayout()
        completeLayout.addLayout(layout)

        completeLayout.addLayout(self.setupPgChartWidget())  
        self.setLayout(completeLayout)
        self.setWindowTitle("Homeo Simulation")

    def minusXifPlus(self, x, number):
        if number >= x:
            return number - x
        else: 
            return 0
                
    def setupPgChartWidget(self):
        '''
        Setup the widget(s) that will show a live chart of units' critical deviation
        '''
        
        plotsWindow = pg.GraphicsLayoutWidget()
        plotLayout=QVBoxLayout()
        if self._simulation.panningCharts ==True:
            self._plotData = getattr(self._simulation,'liveDataWindow')
        else:
            self._plotData = getattr(self._simulation,'liveData')
        colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,255)]
        for unit, color, dataPlotRow, uniselPlotRow in  zip(self._simulation.homeostat.homeoUnits, 
                                                           cycle(colors),
                                                            xrange(0,len(self._simulation.homeostat.homeoUnits)*2,2),
                                                            xrange(1,(len(self._simulation.homeostat.homeoUnits)*2),2)):
            colorFaded = [self.minusXifPlus(170,x)  for x in color]
            self.pgChartsAndItems[unit] = []
            plotItemCritDev = plotsWindow.addPlot(row=dataPlotRow, col=0, rowspan=1, colspan=4,  name=(unit.name))
            plotItemCritDev.addLine(y=0, pen ={'color' : '#E6E6AF'})  #pale muted yellow color in hex RGB value
            plotItemCritDev.setRange(rect=None, xRange=None, yRange=(unit.minDeviation, unit.maxDeviation),
                               padding=None, update=True, disableAutoRange=True)
            plotItemCritDev.hideAxis('bottom')
            plotDataItemCritDev = plotItemCritDev.plot(self._plotData[unit], pen = color)
            self.pgChartsAndItems[unit].append(plotItemCritDev)
            self.pgChartsAndItems[unit].append(plotDataItemCritDev)
#            plotItem.setTitle(unit.name)
#            plotItem.setAutoPan(x=1000)
            "adding uniselectors"
            plotItemUnisel = plotsWindow.addPlot(row = uniselPlotRow, col=0, rowspan=1, colspan=4, name=(unit.name + "-unisel"))
            plotItemUnisel.setRange(rect=None, xRange=None, yRange=(0, 1),
                               padding=None, update=True, disableAutoRange=True)
            plotItemUnisel.hideAxis('bottom')
            plotItemUnisel.hideAxis('left')
            plotDataItemUnisel = plotItemUnisel.plot(self._plotData[unit.uniselector], pen = colorFaded)
            self.pgChartsAndItems[unit].append(plotItemUnisel)
            self.pgChartsAndItems[unit].append(plotDataItemUnisel)
            
            "linking x axes"
            plotItemCritDev.getViewBox().setXLink(plotItemUnisel.getViewBox())
            
        plotLayout.addWidget(plotsWindow)
        self.connect(self._simulation, SIGNAL("liveDataCritDevChanged"), self.updateCritDevChart)
#        self.connect(self._simulation, SIGNAL("liveDataUniselChanged"), self.updateCritDevChart)
        return plotLayout
 
    def updateCritDevChart(self, unitRef):
        self.pgChartsAndItems[unitRef][1].setData(self._plotData[unitRef])
        self.pgChartsAndItems[unitRef][3].setData(self._plotData[unitRef.uniselector])
#             
#===============================================================================
#   Homeostat Gui setup        
#==============================================================================="""

    def setupHomeostatGuiDialog(self):
        
        "set up all the units' widgets"
        self.setupHomeostatGuiUnitsLineEdits()
        self.setupHomeostatGuiUnitsComboAndCheckBoxes()
        self.setupHomeostatGuiConnections()
#        self.setupHomeostatGuiUnitsQwtCritDevSliders()
        self.setupHomeostatGuiUnitsStandardCritDevSliders()   

    def setupHomeostatGuiUnitsLineEdits(self):
        "Set up the line edit widgets for the units (not for the connections)"
        
        '''1. Set up a dictionary with homeoUnits properties corresponding to (shortened) widget names, 
        desired visualized precision (if needed), and range (if needed)'''
        lineEditsNames = {'name':('Name', '', 'LineEdit'), 
                          'currentOutput':('Output', 5, 'LineEdit', ()), 
                          'inputTorque':('Input', 5, 'LineEdit', ()), 
                          'mass':('Mass', 0, 'LineEdit',(1,100000)), 
                          'potentiometer':('Potent', 4, 'LineEdit',(0,1)), 
                          'viscosity':('Viscosity', 4,'LineEdit', (0,1)),
                          'noise':('Noise', 4, 'LineEdit', (0,1)), 
                          'switch':('Switch', 0, 'LineEdit', ()), 
                          'uniselectorTimeInterval':('UniselTiming', 0, 'LineEdit', (0,1000)), 
                          'maxDeviation':('MaxCritDev', 0, 'LineEdit', ()), 
                          'minDeviation':('MinCritDev', 0, 'LineEdit', ()), 
                          'density':('Density', 0, 'LineEdit',()),
                          'criticalDeviation':('CritDev', 5, 'LineEdit', ())}
        
        '2. create and setup the widgets'
        for i in xrange(len(self._simulation.homeostat.homeoUnits)):
            for propertyName, lineEdit in iteritems(lineEditsNames):
                widget = getattr(self._homeostat_gui, 'unit' + str(i + 1) + lineEdit[0] + lineEdit[2])
                attribute = getattr(self._simulation.homeostat.homeoUnits[i], propertyName)
                slot = getattr(self._simulation.homeostat.homeoUnits[i], 'set' + propertyName[0].upper() + propertyName[1:])
                if isinstance(attribute, basestring):
                    widget.setText(attribute)
                else:
#                    floatValidator = QDoubleValidator()
#                    if lineEdit[3]:                     # Empty lists and tuple are false in Python (Yak!) 
#                        floatValidator.setRange(lineEdit[3][0], lineEdit[3][1])
#                    widget.setValidator(floatValidator)
                    widget.setText(str(round(attribute, lineEdit[1])))
                widget.textModified.connect(slot)                
                'Update signals'
                signalFromUnit =  propertyName + "ChangedLineEdit"
                QObject.connect(emitter(self._simulation.homeostat.homeoUnits[i]), SIGNAL(signalFromUnit), widget.setText)

    def setupHomeostatGuiUnitsComboAndCheckBoxes(self):
        '''
        Set up comboboxes and checkboxes for the units (not connections)'
        The values of all of these widget cannot be changed from the simulation as normally running. 
        However, they need to be updated when the simulation is reset. 
        Therefore, they need to listen to signals coming from it. 
        ''' 
        uniselectList = HomeoUniselector.__subclasses__()
        for i in xrange(len(self._simulation.homeostat.homeoUnits)):
            'comboBoxes'
            'uniselector type'
            widget = getattr(self._homeostat_gui, 'unit'+str(i+1)+'UniselectTypeComboBox')
            attribute = getattr(self._simulation.homeostat.homeoUnits[i], 'uniselector')
            for uniselectType in uniselectList:
                widget.addItem(uniselectType.__name__.split("HomeoUniselector").pop())
                widget.setEditable(False)
                widget.currentIndexChanged[str].connect(self._simulation.homeostat.homeoUnits[i].changeUniselectorType)          
            
            'unit is active'
            widget = getattr(self._homeostat_gui, 'unit'+str(i+1)+'ActiveComboBox')
            attribute = getattr(self._simulation.homeostat.homeoUnits[i], 'status')
            widget.addItems(('Active', 'Non Active'))
            widget.setEditable(False)
            widget.setCurrentIndex(("Active", "Non Active").index(self._simulation.homeostat.homeoUnits[i].status))            
            slot = getattr(self._simulation.homeostat.homeoUnits[i], 'setStatus')
            widget.currentIndexChanged[str].connect(slot)
            signalFromUnit = 'unitActiveIndexchanged'
            QObject.connect(emitter(self._simulation.homeostat.homeoUnits[i]), SIGNAL(signalFromUnit), widget.setCurrentIndex) 
            
            'uniselector active and uniselector sound checkboxes'
            widget = getattr(self._homeostat_gui, 'unit'+str(i+1)+'UniselOnCheckBox')
            attribute = getattr(self._simulation.homeostat.homeoUnits[i],'uniselectorActive')
            widget.setChecked(attribute)
            signalFromUnit = 'unitUniselOnChanged'
            widget.stateChanged.connect(self._simulation.homeostat.homeoUnits[i].toggleUniselectorActive)
            QObject.connect(emitter(self._simulation.homeostat.homeoUnits[i]), SIGNAL(signalFromUnit), widget.setChecked)             
            widget = getattr(self._homeostat_gui, 'unit'+str(i+1)+'UniselSoundCheckBox')
            attribute = getattr(self._simulation.homeostat.homeoUnits[i].uniselector,'beeps')
            widget.setChecked(attribute)
            signalFromUnit = 'uniselSoundChanged'
            widget.stateChanged.connect(self._simulation.homeostat.homeoUnits[i].uniselector.toggleBeeping)
            QObject.connect(emitter(self._simulation.homeostat.homeoUnits[i].uniselector), SIGNAL(signalFromUnit), widget.setChecked)             
             

    def setupHomeostatGuiUnitsQwtCritDevSliders(self):
        '''Set up the critical deviation slider. 
           As Qt slider only accept integer values, we are using PyQwt sliders, which accept floats.'''
                
        for i in xrange(len(self._simulation.homeostat.homeoUnits)):
            widget = getattr(self._homeostat_gui, 'unit'+str(i+1)+'CritDevSlider')
            slot = getattr(self._simulation.homeostat.homeoUnits[i], 'setCriticalDeviation') 
            widget.setRange(getattr(self._simulation.homeostat.homeoUnits[i], 'minDeviation'), getattr(self._simulation.homeostat.homeoUnits[i], 'maxDeviation'))
            widget.setValue(getattr(self._simulation.homeostat.homeoUnits[i], 'criticalDeviation'))
            widget.valueChanged.connect(slot)
            QObject.connect(emitter(self._simulation.homeostat.homeoUnits[i]), SIGNAL('criticalDeviationChanged'), widget.setValue)
            QObject.connect(emitter(self._simulation.homeostat.homeoUnits[i]), SIGNAL('deviationRangeChanged'), widget.setRange)

    def setupHomeostatGuiUnitsStandardCritDevSliders(self):
        '''Set up the critical deviation sliders. 
           As Qt sliders only accept integer values, we convert floats to integers using a precision parameter'''
         
        "the precision value to use for the float <--> integer conversion is stored in a class variable of HomeoUnit" 
        prec = HomeoUnit.precision                    
        for i in xrange(len(self._simulation.homeostat.homeoUnits)):
            widget = getattr(self._homeostat_gui, 'unit'+str(i+1)+'CritDevSlider')
            slot = getattr(self._simulation.homeostat.homeoUnits[i], 'setCriticalDeviationFromSlider')        # scaling to float in range done by the Unit 
            widget.setMinimum(int(floor(getattr(self._simulation.homeostat.homeoUnits[i], 'minDeviation') * prec)))
            widget.setMaximum(int(floor(getattr(self._simulation.homeostat.homeoUnits[i], 'maxDeviation') * prec)))
            widget.setValue(int(floor(getattr(self._simulation.homeostat.homeoUnits[i], 'criticalDeviation') *  prec)))

            widget.valueChanged.connect(slot)
           
            'The value passed back to the slider are scaled by the Unit'
            QObject.connect(emitter(self._simulation.homeostat.homeoUnits[i]), SIGNAL('criticalDeviationScaledChanged(int)'), widget.setValue) 
            QObject.connect(emitter(self._simulation.homeostat.homeoUnits[i]), SIGNAL('minDeviationScaledChanged'), widget.setMinimum)  
            QObject.connect(emitter(self._simulation.homeostat.homeoUnits[i]), SIGNAL('maxDeviationScaledChanged'), widget.setMaximum)  
            


    
    def setupHomeostatGuiConnections(self):
        " Set up, initialize, and connect the line edits for all the units' connections's lineEdits widgets"
        
        for incomingUnit in xrange(len(self._simulation.homeostat.homeoUnits)):
            for outgoingUnit in xrange(len(self._simulation.homeostat.homeoUnits)):
                'lineEdits'
                widget = getattr(self._homeostat_gui, 'unit' + str(incomingUnit + 1) + 'Unit' + str(outgoingUnit+1)+ 'ConnNameLineEdit')
                attribute = getattr(self._simulation.homeostat.homeoUnits[incomingUnit].inputConnections[outgoingUnit].incomingUnit, 'name')
                widget.setText(attribute)
                widget.setReadOnly(True)
                QObject.connect(emitter(self._simulation.homeostat.homeoUnits[incomingUnit].inputConnections[outgoingUnit].incomingUnit), 
                                SIGNAL("nameChanged"), widget.setText)
        
                'spinboxes'
                'setup a dictionary with spinboxes names, types, and setter methods'
                spinBoxes = {'weight':('Double', 'newWeight'), 
                             'switch':('','toggleSwitch'), 
                             'noise':('Double', 'setNoise')}
                for spinBox, type in iteritems(spinBoxes):
                    widget = getattr(self._homeostat_gui, 'unit' + str(incomingUnit + 1) + 
                                     'Unit' + str(outgoingUnit+1)+ (spinBox[0].upper()) + spinBox[1:] + type[0] + 'SpinBox')
                    attribute = getattr(self._simulation.homeostat.homeoUnits[incomingUnit].inputConnections[outgoingUnit], spinBox)
                    slot = getattr(self._simulation.homeostat.homeoUnits[incomingUnit].inputConnections[outgoingUnit], type[1])                    
                    signalFromUnit = spinBox + "Changed"
                    widget.setValue(attribute)
#                    widget.realSlot = slot
#                    widget.valueChanged.connect(slot)
                    widget.editingValueFinished.connect(slot)                  #uses a custom signal produced by SFSpinBox and SFDoubleSpinBox
                    QObject.connect(emitter(self._simulation.homeostat.homeoUnits[incomingUnit].inputConnections[outgoingUnit]), SIGNAL(signalFromUnit), widget.setValue)

                
                'comboboxes'
                'setup a dictionary with comboBoxes names, values, and setter methods indexed by attributes'
                comboBoxes = {'status':({'Active':True,'Non active':False},'Connected','toggleStatus'),
                              'state':({'manual':'manual', 'uniselector':'uniselector'},'Uniselector', 'toggleUniselectorState')}
                for attrName, attrData in iteritems(comboBoxes):
                    widget = getattr(self._homeostat_gui, 'unit' + str(incomingUnit + 1) + 
                                     'Unit' + str(outgoingUnit+1)+ attrData[1]+'ComboBox')
                    attribute = getattr(self._simulation.homeostat.homeoUnits[incomingUnit].inputConnections[outgoingUnit], attrName)
                    values = attrData[0].keys()
                    slot = getattr(self._simulation.homeostat.homeoUnits[incomingUnit].inputConnections[outgoingUnit], attrData[2])
                    index = attrData[0].values().index(getattr(self._simulation.homeostat.homeoUnits[incomingUnit].inputConnections[outgoingUnit],attrName))
                    widget.addItems(values)
                    widget.setEditable(False)
                    widget.setCurrentIndex(index)
                    widget.currentIndexChanged.connect(slot)

                    

                
        
        
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
                self.clearLiveCharts()
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
        self.clearLiveCharts()
    
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
        "Chart essential data (crit dev and uniselector ticks) with matplotlib"

        dataArray = np.genfromtxt(StringIO(self._simulation.essentialSimulationData()), delimiter = ',', skiprows = 3,  names = True)
        plt.figure()
        for col_name in dataArray.dtype.names:
            plt.plot(dataArray[col_name], label=col_name)
        plt.legend(loc=3, fontsize = 8)
        plt.ylabel('Critical Deviation')
        plt.xlabel('Time')
        plt.title(self._simulation.dataFilename)
        plt.grid(b=True, which='both', color='0.65',linestyle='-')
        plt.axis(ymin=self._simulation.homeostat.homeoUnits[0].minDeviation, ymax= self._simulation.homeostat.homeoUnits[0].maxDeviation)
        plt.show()

    def changeUniselectorTypeForUnit(self, aUnitNumber, aUniselectorType):
        pass
    
    def clearLiveCharts(self):
        for unitRef in self._simulation._homeostat.homeoUnits:
            self.pgChartsAndItems[unitRef][1].clear()
            self.pgChartsAndItems[unitRef][3].clear()
            
    def toggleLiveDataWindow(self):
        self._simulation.toggleLivedataWindow()
        if self._simulation.panningCharts ==True:
            self._plotData = getattr(self._simulation,'liveDataWindow')
        else:
            self._plotData = getattr(self._simulation,'liveData')
        

class Classic_Homeostat(QDialog, Ui_ClassicHomeostat):
    """Interface to a classic 4-unit Homeostat showing all the parameters of each units
    and allowing real-time interactive manipulation. The simulation itself is usually 
    controlled by an instance of HomeoSimulationControllerGui"""
    def __init__(self, parent = None):
        super(Classic_Homeostat, self).__init__(parent)
        self.setupUi(self)
#        self.setGeometry




class OutLog(object):
    "A class used to redirect stdout and stderr to a text widget"
    def __init__(self, aQTextEdit, out=None, color=None):
        """(edit, out=None, color=None) -> can write stdout, stderr to a
        QTextEdit.
        edit = QTextEdit
        out = alternate stream ( can be the original sys.stdout )
        color = alternate color (i.e. color stderr a different color)
        
        Example usage:
        import sys
        sys.stdout = OutLog(edit, sys.stdout)
        sys.stderr = OutLog(edit, sys.stderr, QtGui.QColor(255,0,0) )

        """
        self.textEdit = aQTextEdit
        self.out = None
        self.color = color

    def write(self, msg):
        if self.color:
            tc = self.textEdit.textColor()
            self.textEdit.setTextColor(self.color)

        
        self.textEdit.append(msg)

        if self.color:
            self.textEdit.setTextColor(tc)

        if self.out:
            self.out.write(msg)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    simul = HomeoSimulationControllerGui()
    simul.show()
    app.exec_()
               
            