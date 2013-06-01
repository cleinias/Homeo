'''
Created on Mar 19, 2013

@author: stefano
'''
from Core.Homeostat import *
from Core.HomeoDataCollector  import *
from Core.HomeoUnitNewtonian  import *
from datetime import datetime
import os, pickle
from PyQt4.QtCore import  *
from PyQt4.QtGui import QApplication 
from collections import deque
#from Core.HomeoUnit import setRandomValues

class HomeoQtSimulation(QObject):
    '''
    HomeoQSimulation is the class that manages a complete run of a Homeostat
    run in the Qt framework. 
    
    It takes care of the administrative tasks: 
    - setting up the initial conditions, 
    - starting and stopping the simulation. 
    It also knows how to read initial conditions from a file (for repeated experiments). 
    The real work of simulating the Homeostat is done by the Homeostat 
    class---an instance of which is held by the simulation---and its components.

    Instance Variables:
        homeostat                   <aHomeostat>       The Homeostat being run in the simulation
        maxRuns                     <anInteger>        The maximum number of simulation steps 
        dataFilename                <aString>          The filename used to save the simulation data
        dataAreSaved                <aBoolean>         Whether the simnulation run data have been saved
        homeostatFilename           <aString>          The filename used to save the homeostat
        homeostatIsSaved            <aBoolean>         Whether the homeostat being simulated has been saved        
        simulDelay                  <anInteger>        Delay, in milliseconds, between two simulation steps
        liveData                    <aDictionary>      aDictionary holding the critDev and uniselector activation data for all the units 
        unitsSelfWeights             <aDictionary>      aDictionary holding the weights for the units' self-connections
        liveDataOn                  <aBoolean>         enables live charting
        liveDataWindow              <aDictionary>      a Dictionary holding double-ended queues holding only the last maxDataPoints number of datapoints
        maxDataPoints               <anInteger>        the maximum dataPoints to hold for live charting
        panningCharts               <aBoolean>         whether charts should show the complete history or only the last MaxDataPoints
        currentExperiment           <aMethod>          holds a reference to the initialization procedure for the current experimental setup
    '''

#===============================================================================
# Class methods
#===============================================================================

    @classmethod    
    def readFrom(self,filename):
        '''This is a class method that create a new HomeoSimulation instance from a filename,
        by loading a pickled homeostat'''
        newHomeostat = Homeostat.readFrom(filename)
        newHomeoSimulation = HomeoQtSimulation()
        newHomeoSimulation.homeostat = newHomeostat
        newHomeoSimulation.homeostatIsSaved = True 
        return newHomeoSimulation



#===============================================================================
# Accessing and initialization
#===============================================================================

    def getDataFilename(self):
        return self._dataFilename
    
    def setDataFilename(self, aString):
        self._dataFilename = aString

    dataFilename = property(fget = lambda self: self.getDataFilename(),
                        fset = lambda self, aString: self.setDataFilename(aString))

    def getHomeostatFilename(self):
        return self._homeostatFilename
    
    def setHomeostatFilename(self, aString):
        self._homeostatFilename = aString
        self.emit(SIGNAL("homeostatFilenameChanged"), self._homeostatFilename)

    homeostatFilename = property(fget = lambda self: self.getHomeostatFilename(),
                        fset = lambda self, aString: self.setHomeostatFilename(aString))

    def getHomeostat(self):
        return self._homeostat
    
    def setHomeostat(self,aHomeostat):
        self._homeostat = aHomeostat
    
    homeostat = property(fget = lambda self: self.getHomeostat(),
                         fset = lambda self, aHomeostat: self.setHomeostat(aHomeostat))
    
    def getMaxRuns(self):
        return self._maxRuns
    
    def setMaxRuns(self,anInteger):
        self._maxRuns =  anInteger

    maxRuns = property(fget = lambda self: self.getMaxRuns(),
                       fset = lambda self, number: self.setMaxRuns(number)) 

    def getHomeostatIsSaved(self):
        return self._homeostatIsSaved
    
    def setHomeostatIsSaved(self,anInteger):
        self._homeostatIsSaved =  anInteger
        #Emit signal here"

    homeostatIsSaved = property(fget = lambda self: self.getHomeostatIsSaved(),
                       fset = lambda self, number: self.setHomeostatIsSaved(number)) 

    def getDataAreSaved(self):
        return self._dataAreSaved
    
    def setDataAreSaved(self,anInteger):
        self._dataAreSaved =  anInteger

    dataAreSaved = property(fget = lambda self: self.getDataAreSaved(),
                       fset = lambda self, number: self.setDataAreSaved(number)) 
    
    def getSimulDelay(self):
        return self._simulDelay
    
    def setSimulDelay(self,aValue):
        self._simulDelay = aValue
        
    simulDelay = property(fget=lambda self: self.getSimulDelay(),
                          fset = lambda self, value: self.setSimulDelay())
    
    def units(self):
        return self.homeostat.homeoUnits
    
    def __init__(self):
        '''
        Initialize the instance with a new homeostat and a default number of runs."
        '''
#=======================================================================
# FIXME Currently setting the initialization method of the 
#       experimental set up in __init__. Should rather have a default value
#       and then be chosen from the GUI application  
#=======================================================================
#        self.currentExperiment = 'initialize_1minus_2xExperiment'
        self.currentExperiment = 'initialize_1minus_2_minus_3xExperiment'        
        super(HomeoQtSimulation,self).__init__()
        self._homeostat = Homeostat()
        self._maxRuns = 10
        self._dataFilename = self.createDefaultDataFilename()
        self._homeostatFilename = self.createDefaultHomeostatFilename()
        self._dataAreSaved = True       # There are no data to save yet
        self._homeostatIsSaved = False  # A new simulation has a new random Homeostat, unless is loaded form file
        self._simulDelay = 10           # in milliseconds
        self._isRunning = False
        self.liveData = {}
        self.unitsSelfWeights = {}
        self.liveDataOn = False
        self._homeostat.collectsData = False
        self.maxDataPoints = 50
        self.liveDataWindow = {}
        self.panningCharts = True       # default is to use panning charts. Can be changed in the Gui
                
    def initializeLiveData(self):
        "set up the liveData dictionary for live graphing"
        for unit in  self._homeostat.homeoUnits:
            self.liveData[unit] = []                         # add empty list to hold critDev data for unit
            self.liveData[unit.uniselector] = []             # add empty list to hold uniselector activation data for unit
            self.liveDataWindow[unit] = deque(maxlen=self.maxDataPoints)              # add empty queue to hold critDev data for unit
            self.liveDataWindow[unit.uniselector] = deque(maxlen=self.maxDataPoints)        # add empty queue to hold uniselector activation data for unit
            self.unitsSelfWeights[unit] = []

    def initializeExperSetup(self):
        '''Initialize the homeostat to the current experimental set up using the 
           method stored in self.currentExperiment'''
        initializeMethod = getattr(self, self.currentExperiment)
        initializeMethod()
    
#===============================================================================
# Running methods
#===============================================================================

    def go(self):
        '''Start the homeostat and runs it for the number of runs specified in maxRuns. 
           This method must be run in a thread, or it will block further access 
           to the interpreter. 
           The homeostat can be paused by sending #pause to the simulation'''
           
        self._dataAreSaved = False
        self._homeostatIsSaved = False
        self._isRunning = True
        
        while self._homeostat.time  < self._maxRuns  and self._isRunning == True:
#            print "I am running cycle number: %u" % self._homeostat.time
            self._homeostat.runOnce()
#            if self.liveDataOn:
            self.updateLiveData()
            time.sleep(self._simulDelay / 1000)
            QApplication.processEvents() 

    def pause(self):
        "Pause the simulation" 

        self._isRunning = False
        
    def resume(self):
        "Resume the simulation"
        
        self._isRunning = True
        self.go()
    
    def step(self):
        "Advance the simulation one step"
        if self._homeostat.time  < self._maxRuns:
#            print "I am running cycle number: %u" % self._homeostat.time
            self._homeostat.runOnce()
            self.updateLiveData()
#            time.sleep(self._simulDelay / 1000)
            QApplication.processEvents() 

    
    def updateLiveData(self):
        for unit in self._homeostat.homeoUnits:
            self.liveData[unit].append(unit.criticalDeviation)
            self.liveData[unit.uniselector].append(unit.uniselectorActivated)
            self.liveDataWindow[unit].append(unit.criticalDeviation)
            self.liveDataWindow[unit.uniselector].append(unit.uniselectorActivated)
            self.unitsSelfWeights[unit].append(unit.inputConnections[0].weight)
            
#            if unit.uniselectorActivated <> 0:
#                sys.stderr.write("Uniselector activated for unit %s at time %u and value %u\n" % (unit.name, self._homeostat.time, unit.uniselectorActivated))
            if self.liveDataOn:
                self.emit(SIGNAL("liveDataCritDevChanged"), unit)
#                self.emit(SIGNAL("liveDataUniselChanged"), unit.uniselector)
            "for testing, replaces a self halt"
#        if (self._homeostat.time % 100 ) == 0:
#            print "time is a multiple of 100"
        

#===============================================================================
# Adding methods 
#===============================================================================

    def addFullyConnectedUnit(self, aHomeoUnit):
        '''Add a fully connected unit to the simulation's homeostat'''

        self.homeostat.addFullyConnectedUnit(aHomeoUnit)


    def addUnit(self, aHomeoUnit):
        '''Add a  unit to the simulation's homeostat'''

        self._homeostat. addUnit(aHomeoUnit)

#===============================================================================
# Saving and loading methods
#===============================================================================

    def createDefaultDataFilename(self):
        '''Create a default string corresponding to the dataFilename. 
           Check that no file with the same name exists in current directory'''
        
        dateString = ''
        now_ = datetime.now()
        dateString += str(now_.month) + '-' + str(now_.day) + '-' + str(now_.year)
        name = 'HomeoSimulationData'
    
        number = 1
        completeName = name + '-' + dateString + '-' + '1'
    
        while os.path.exists(completeName):
            number += 1
            completeName = name + '-' + dateString  + '-' + str(number)+'.txt'
    
        return completeName

    def createDefaultHomeostatFilename(self):
        '''Create a default string corresponding to the dataFilename. 
           Check that no file with the same name exists in current directory'''
        
        dateString = ''
        now_ = datetime.now()
        dateString += str(now_.month) + '-' + str(now_.day) + '-' + str(now_.year)
        name = 'Homeostat'
    
        number = 1
        completeName = name + '-' + dateString + '-' + '1'+'.pickled'
    
        while os.path.exists(completeName):
            number += 1
            completeName = name + '-' + dateString  + '-' + str(number)+'.pickled'
    
        return completeName

    def saveCompleteRunOnFile(self,aFilename):
        "Asks the datacollector of the homeostat to save all data on dataFilename"

        self.homeostat.dataCollector.saveCompleteDataOnFile(aFilename)
        self._dataAreSaved = True

    def saveEssentialDataOnFile(self,aFilename, withWeights):
#===============================================================================
#        '''Ask the datacollector of the homeostat 
#           to save only the essential data on dataFilename'''
# 
# #        self.homeostat.dataCollector.saveEssentialDataOnFile(aFilename)
#===============================================================================
        """FIXME: Following code uses the class's own liveData instead of relying on the dataCollector.
        It should eventually be moved into the dataCollector class.
        
        Save the data about unit's critical deviation and uniselector activation on file.
        If withWeights = True, saves also values of units' self-connection weights 
        """


        "Print a header with general information at the top of the file"
        headerText = ''
        headerText += ('# Simulation data produced by HOMEO---the homeostat simulation program\n')
        headerText +=  ('# Data printed on: ')
        headerText += (str(datetime.now()))
        headerText += ("\n")
        headerText += ('# There were exactly %u units in this simulation' % len(self.homeostat.homeoUnits))
        headerText += ("\n")
        "Create an array with the time indexes and update header text and format string" 
        npDataArray = np.arange(len(self.liveData[self.homeostat.homeoUnits[0]]))
        listOfFormatStrings = ['%u']                    # First column: unsigned integers for the time indexes
        formatForUnitsAndUnisel = '%10.8f'              # Float values for all successive columns
        for unit in self.homeostat.homeoUnits:
            npDataArray = np.vstack((npDataArray,self.liveData[unit]))
            listOfFormatStrings.append(formatForUnitsAndUnisel)
            npDataArray = np.vstack((npDataArray,self.liveData[unit.uniselector]))
            listOfFormatStrings.append(formatForUnitsAndUnisel)
            if withWeights == True:
                npDataArray = np.vstack((npDataArray, self.unitsSelfWeights[unit]))
                headerText += (unit.name + ','+unit.name + '_unisel'+','+unit.name +'_weight')
                listOfFormatStrings.append(formatForUnitsAndUnisel)
            else:
                headerText += (unit.name + ','+unit.name + '_unisel'+',')
        npDataArray = np.transpose(npDataArray)
        np.savetxt(str(aFilename), npDataArray, fmt = listOfFormatStrings, delimiter = ',', comments = '',header = headerText)
  
        
    def essentialSimulationData(self):
        "Ask the DataCollector to teturn a string with the essential data about the simulaiton"
        return self.homeostat.dataCollector.printPlottingDataForROnAString('')

    def saveEssentialDataOnFileWithSeparator(self, aCharacter):
        '''Ask the datacollector of the homeostat 
           to save only the essential data on dataFilename,
           using aCharacter as a column separator'''

        fileContent = self.homeostat.dataCollector.saveEssentialsOnAStringWithSeparator('', aCharacter)
        fileOut  = open(self.dataFilename, 'w')
        fileOut.write(fileContent)
        fileOut.close()
        
        
    def save(self):
        '''Save the homeostat the simulation manages to a pickled file
           It will erase the old content of aFilename.'''

        self.homeostat.saveTo(self.homeostatFilename)
        self._homeostatIsSaved = True


    def isReadyToGo(self):
        '''Check that the homeostat is ready to go and that 
           the maxRuns and dataFilename are present'''

        return (self._homeostat.isReadyToGo() and
                self.maxRuns is not None and
                self._dataFilename is not None and
                self._homeostatFilename is not None)
    
    def loadNewHomeostat(self, aFilename):
        "loads a new homeostat from aFilename"
        try:
            newHomeostat = Homeostat.readFrom(aFilename)
        except HomeostatError:
            sys.stderr.write(("Could not load a new homeostat from filename: %s" % aFilename))
            raise
        self.homeostat = newHomeostat
        self.homeostatFilename = aFilename
        self.homeostatIsSaved = True
        self.dataAreSaved = True

#===============================================================================
# Changing simulation values methods
#===============================================================================

    def timeReset(self):
        """
        Restart the  simulation: 
        resets simulation time to zero     
        clear the simulation data
        set dataAreSaved to true
        """
        self._homeostat.timeReset()
        self._homeostat.flushData()
        self._dataAreSaved = True
        
    def fullReset(self):
        """
        Start a new simulation:
        - fully reset the homeostat
        - reinitialize to the current simulation experiment
        - clear the simulation data
        - set dataAreSaved to true
        - pick a new name
        """
        self._homeostat.fullReset()
        self._homeostatFilename = self.createDefaultHomeostatFilename()
        self.initializeExperSetup()
        self._homeostat.flushData()
        self._dataAreSaved = True
        self.initializeLiveData()
        self.allUnitValuesChanged()
    
    def allUnitValuesChanged(self):
        '''forces each unit to send out update signals for all their relevant parameters, 
        so the GUI can update itself'''
        for unit in self.homeostat.homeoUnits:
            unit.allValuesChanged()
    
    def toggleLivedataOn(self):
        self.liveDataOn = not self.liveDataOn
        
    def toggleLivedataWindow(self):
        self.panningCharts = not self.panningCharts

#==========================================================================
# Various experiments initialization methods
# FIXME: Should be moved to their own class, and each method should return
#        a properly configured homeostat
#==========================================================================
        
    def initializeAshbySimulation(self):
        '''Adds four fully connected units with random values to the simulator 
           (as per Ashby basic design)'''
 
        for i in xrange(4):
            unit = HomeoUnitNewtonian()
            unit.setRandomValues()
            self._homeostat.addFullyConnectedUnit(unit)
    

    def initialize_1minus_2xExperiment(self):
        '''
        Initialize a standard Homeostat to have 2 2-units 1-, 2x standard settings for 1- 2x experiment (Agent-Environment)
        with fixed parameters to improve repeated runs
        '''
        
        'Standard parameters'
        agent_visc = 0.9
        env_visc = 0.9
        agent_mass = 100
        env_mass = 100
        agent_self_noise = 0.05
        env_self_noise = 0.05
        agent_density = 1
        env_density = 1
        agent_uniselector_timing= 100
        
        agent_self_connection_active = 'active'
        agent_self_connection_uniselector = 'manual'
        agent_self_connection_switch = -1
        agent_self_connection_potentiomenter = 0.1
        agent_self_connection_noise = 0.05
                
        agent_incoming_conn_weight = 0.5
        agent_incoming_conn_noise = 0.05
        agent_incoming_connection_polarity = 1
        agent_incoming_connection_uniselector = 'uniselector' 
        
        env_incoming_connection_weight = 0.5
        env_incoming_connection_noise = 0.05
        env_incoming_connection_polarity = 1
        env_incoming_connection_uniselector = 'manual' 


        'Setup a standard Homeostat if none exists. Then change the parameters'
         
        if len(self._homeostat.homeoUnits) == 0 :                 # check if the homeostat is set up already"
            for i in xrange(4):
                unit = HomeoUnitNewtonian()
                unit.setRandomValues()
                self._homeostat.addFullyConnectedUnit(unit)
        
        'change homeostat and dataFile names'
        self.homeostatFilename = '1-minus-2x-experiment'
        self._dataFilename = '1-minus-2x-experiment-Plot-Data'
        
        'disable all connections except self-connections'
        for unit in self.homeostat.homeoUnits:
            for i in xrange(1, len(self.homeostat.homeoUnits)):
                unit.inputConnections[i].status = 0
        
        homeo1_unit1_minus = self.homeostat.homeoUnits[0]
        homeo1_unit2x = self.homeostat.homeoUnits[1]
        homeo2_unit1_minus = self.homeostat.homeoUnits[2]
        homeo2_unit2x = self.homeostat.homeoUnits[3]
        
        'Agent for Homeostat 1'
        homeo1_unit1_minus.name = 'H1_Agent'
        homeo1_unit1_minus.mass = agent_mass
        homeo1_unit1_minus.viscosity = agent_visc
        homeo1_unit1_minus.density = agent_density
        homeo1_unit1_minus.noise  = agent_self_noise
        homeo1_unit1_minus.uniselectorTimeInterval = agent_uniselector_timing
        
        'self-connection'
        homeo1_unit1_minus.potentiometer = agent_self_connection_potentiomenter
        homeo1_unit1_minus.switch = agent_self_connection_switch
        homeo1_unit1_minus.inputConnections[0].noise = agent_self_connection_noise
        homeo1_unit1_minus.inputConnections[0].state = agent_self_connection_uniselector
        
        
        'Environment for Homeostat 1'
        homeo1_unit2x.name = 'H1_Env'
        homeo1_unit2x.mass - env_mass
        homeo1_unit2x.viscosity = env_visc
        homeo1_unit2x.density = env_density
        homeo1_unit2x.noise = env_self_noise
        'self-connection disabled'
        homeo1_unit2x.disactivateSelfConn()


        'set up first homeostat'
        for connection in homeo1_unit1_minus.inputConnections:
            if connection.incomingUnit.name == 'H1_Env':
                connection.newWeight(agent_incoming_conn_weight * agent_incoming_connection_polarity)
                connection.noise = agent_incoming_conn_noise
                connection.state = agent_incoming_connection_uniselector
                connection.status = True
        
        
        
        for connection in homeo1_unit2x.inputConnections:
            if connection.incomingUnit.name == 'H1_Agent':
                connection.newWeight(env_incoming_connection_weight * env_incoming_connection_polarity)
                connection.noise = env_incoming_connection_noise
                connection.state = env_incoming_connection_uniselector
                connection.status = True
        
       
        'Second Homeostat'
        
        'Agent for Homeostat 2'
        homeo2_unit1_minus.name = 'H2_Agent'
        homeo2_unit1_minus.mass = agent_mass
        homeo2_unit1_minus.viscosity = agent_visc
        homeo2_unit1_minus.density = agent_density
        homeo2_unit1_minus.noise  = agent_self_noise
        homeo2_unit1_minus.uniselectorTimeInterval = agent_uniselector_timing
        
        'self-connection'
        homeo2_unit1_minus.potentiometer = agent_self_connection_potentiomenter
        homeo2_unit1_minus.switch = agent_self_connection_switch
        homeo2_unit1_minus.inputConnections[0].noise = agent_self_connection_noise
        homeo2_unit1_minus.inputConnections[0].state = agent_self_connection_uniselector

        
        
        'Environment for Homeostat 2'
        homeo2_unit2x.name = 'H2_Env'
        homeo2_unit2x.mass - env_mass
        homeo2_unit2x.viscosity = env_visc
        homeo2_unit2x.density = env_density
        homeo2_unit2x.noise = env_self_noise
        'self-connection disabled'
        homeo2_unit2x.disactivateSelfConn()
        

        'set up second homeostat'
        for connection in homeo2_unit1_minus.inputConnections:
            if connection.incomingUnit.name == 'H2_Env':
                connection.newWeight(agent_incoming_conn_weight * agent_incoming_connection_polarity)
                connection.noise = agent_incoming_conn_noise
                connection.state = agent_incoming_connection_uniselector
                connection.status = True        
        
        for connection in homeo2_unit2x.inputConnections:
            if connection.incomingUnit.name == 'H2_Agent':
                connection.newWeight(env_incoming_connection_weight * agent_incoming_connection_polarity)
                connection.noise = env_incoming_connection_noise
                connection.state = env_incoming_connection_uniselector
                connection.status = True      
                
                
                
    def initialize_1minus_2_minus_3xExperiment(self):
        """Initialize a homeostat to replicate a 3-unit
           homeostat roughly similar to DiPaolo's ocular inversion
           experiment:
           2 self-connected units representing the 'eyes' or 'sensors'
           1 unconnected nit representing the environment 
        """
        'Standard parameters'
        agent_visc = 0.9
        env_visc = 0.9
        agent_mass = 100
        env_mass = 100
        agent_self_noise = 0.05
        env_self_noise = 0.05
        agent_density = 1
        env_density = 1
        agent_uniselector_timing= 100
        
        agent_self_connection_active = 'active'
        agent_self_connection_uniselector = 'manual'
        agent_self_connection_switch = -1
        agent_self_connection_potentiomenter = 0.1
        agent_self_connection_noise = 0.05
                
        agent_incoming_conn_weight = 0.5
        agent_incoming_conn_noise = 0.05
        agent_incoming_connection_polarity = 1
        agent_incoming_connection_uniselector = 'uniselector' 
        
        env_incoming_connection_weight = 0.5
        env_incoming_connection_noise = 0.05
        env_incoming_connection_polarity = 1
        env_incoming_connection_uniselector = 'manual'
        
        'Setup a standard Homeostat if none exists. Then change the parameters'
         
        if len(self._homeostat.homeoUnits) == 0 :                 # check if the homeostat is set up already"
            for i in xrange(4):
                unit = HomeoUnitNewtonian()
                unit.setRandomValues()
                self._homeostat.addFullyConnectedUnit(unit)

        'change homeostat and dataFile names'
        self.homeostatFilename = '1-minus-2-minus--3x-experiment'
        self._dataFilename = '1-minus-2-minus--3x--Plot-Data'
        
        'disable all connections except self-connections'
        for unit in self.homeostat.homeoUnits:
            for i in xrange(1, len(self.homeostat.homeoUnits)):
                unit.inputConnections[i].status = 0
        
        homeo1_unit1_minus = self.homeostat.homeoUnits[0]
        homeo1_unit2_minus = self.homeostat.homeoUnits[1]
        homeo1_unit3x = self.homeostat.homeoUnits[2]
        homeo1_inactive_unit = self.homeostat.homeoUnits[3]
        
        'First Agent or sensor'
        homeo1_unit1_minus.name = '1_Agent'
        homeo1_unit1_minus.mass = agent_mass
        homeo1_unit1_minus.viscosity = agent_visc
        homeo1_unit1_minus.density = agent_density
        homeo1_unit1_minus.noise  = agent_self_noise
        homeo1_unit1_minus.uniselectorTimeInterval = agent_uniselector_timing
        
        'self-connection'
        homeo1_unit1_minus.potentiometer = agent_self_connection_potentiomenter
        homeo1_unit1_minus.switch = agent_self_connection_switch
        homeo1_unit1_minus.inputConnections[0].noise = agent_self_connection_noise
        homeo1_unit1_minus.inputConnections[0].state = agent_self_connection_uniselector
        
        'Second Agent or sensor'
        homeo1_unit2_minus.name = '2_Agent'
        homeo1_unit2_minus.mass = agent_mass
        homeo1_unit2_minus.viscosity = agent_visc
        homeo1_unit2_minus.density = agent_density
        homeo1_unit2_minus.noise  = agent_self_noise
        homeo1_unit2_minus.uniselectorTimeInterval = agent_uniselector_timing
        
        'self-connection'
        homeo1_unit2_minus.potentiometer = agent_self_connection_potentiomenter
        homeo1_unit2_minus.switch = agent_self_connection_switch
        homeo1_unit2_minus.inputConnections[0].noise = agent_self_connection_noise
        homeo1_unit2_minus.inputConnections[0].state = agent_self_connection_uniselector
        
        
        'Environment '
        homeo1_unit3x.name = 'Env'
        homeo1_unit3x.mass - env_mass
        homeo1_unit3x.viscosity = env_visc
        homeo1_unit3x.density = env_density
        homeo1_unit3x.noise = env_self_noise
        'self-connection disabled'
        homeo1_unit3x.disactivateSelfConn()

        'fourth unit is inactive'
        homeo1_inactive_unit.name= 'UNUSED'
        homeo1_inactive_unit.disactivate()

        'set up homeostat'
        for connection in homeo1_unit1_minus.inputConnections:
            if not (connection.incomingUnit.name == 'UNUSED' or connection.incomingUnit == connection.outgoingUnit):
                connection.newWeight(agent_incoming_conn_weight * agent_incoming_connection_polarity)
                connection.noise = agent_incoming_conn_noise
                connection.state = agent_incoming_connection_uniselector
                connection.status = True
        
        for connection in homeo1_unit2_minus.inputConnections:
            if not (connection.incomingUnit.name == 'UNUSED'  or connection.incomingUnit == connection.outgoingUnit):
                connection.newWeight(agent_incoming_conn_weight * agent_incoming_connection_polarity)
                connection.noise = agent_incoming_conn_noise
                connection.state = agent_incoming_connection_uniselector
                connection.status = True
        
        
        for connection in homeo1_unit3x.inputConnections:
            if not (connection.incomingUnit.name == 'UNUSED'  or connection.incomingUnit == connection.outgoingUnit):
                connection.newWeight(env_incoming_connection_weight * env_incoming_connection_polarity)
                connection.noise = env_incoming_connection_noise
                connection.state = env_incoming_connection_uniselector
                connection.status = True

#===============================================================================
# Debugging methods
#===============================================================================

    def toggleDebugMode(self):
        'Toggle the debugMode switch of  all the units in the homeostat'
        for unit in self._homeostat.homeoUnits:
            unit.toggleDebugMode()
        
    def toggleShowUniselectorAction(self):
        'Toggle the ShowUniselectorAction switch of all the units in the homeostat'
        for unit in self._homeostat.homeoUnits:
            unit.toggleShowUniselectorAction()
    
    def toggleDiscardData(self):
        "toggle the collects data switch of the homeostat"
        self._homeostat.collectsData = not self.homeostat.collectsData
