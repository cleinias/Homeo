'''
Created on Mar 19, 2013

@author: stefano
'''
from Core.Homeostat import *
from Core.HomeoDataCollector  import *
from datetime import datetime
import os

class HomeoSimulation(object):
    '''
    HomeoSimulation is the class that manages a complete run of a Homeostat. 
    It takes care of the administrative tasks: 
    - setting up the initial conditions, 
    - starting and stopping the simulation. 
    It also knows how to read initial conditions from a file (for repeated experiments). 
    The real work of simulating the Homeostat is done by the Homeostat 
    class---an instance of which is held by the simulation---and its components.

    Instance Variables:
        homeostat          <aHomeostat>       The Homeostat being run in the simulation
        maxRuns            <anInteger>        The maximum number of simulation steps 
        dataFile           <aString>          The filename used to save the simulation data 
    '''


#===============================================================================
# Accessing and initialization
#===============================================================================

    def getDataFile(self):
        return self._datafile
    
    def setDatafile(self, aString):
        self._datafile = aString

    datafile = property(fget = lambda self: self.getDatafile(),
                        fset = lambda self, aString: self.setDatafile(aString))


    def getHomeostat(self):
        return self._homeostat
    
    def setHomeostat(self,aHomeostat):
        self._homeostat = aHomeostat
    
    homeostat = property(fget = lambda self: self.getHomeostat(),
                         fset = lambda self, aHomeostat: self.setHomeostat(aHomeostat))
    
    def getMaxRuns(self):
        return self._maxRuns
    
    def setMaxRuns(self,anInteger):
        self._maxRuns=  anInteger

    maxRuns = property(fget = lambda self: self.getMaxRuns(),
                       fset = lambda self, number: self.setMaxRuns(number)) 

    def units(self):
        return self.homeostat.homeoUnits
    
    def __init__(self):
        '''
        Initialize the instance with a new homeostat and a default number of runs."
        '''
        
        self._homeostat = Homeostat()
        self.maxRuns = 1000
        self._datafile = self.createDefaultDatafile()

#===============================================================================
# Running methods
#===============================================================================

    def runForever(self):
        '''Start the homeostat and runs it indefinitely. 
           This method must be run in a thread, or it will block further access 
           to the interpreter. 
           The homeostat can be stopped by sending #stop to the simulation'''
    
        self._homeostat.start()

    def start(self):
        '''Run the homeostat for the number of runs specified in maxRuns'''

        self._homeostat.runFor(self._maxRuns)

    def stop(self):
        "Stop the simulation" 

        self.homeostat.stop()

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
# Saving <methods>
#===============================================================================

    def createDefaultDatafile(self):
        '''Create a default strings corresponding to the datafile. 
           Check that no file with the same name exists in current directory'''
        
        dateString = ''
        now_ = datetime.now()
        dateString += str(now_.month) + '-' + str(now_.day) + '-' + str(now_.year)
        name = 'HomeoSimulationData'
    
        number = 1
        completeName = name + '-' + dateString + '-' + '1'
    
        while os.path.exists(completeName):
            number += 1
            completeName = name + '-' + dateString  + '-' + str(number)
    
        return completeName

    def saveCompleteRunOnFile(self):
        "Asks the datacollector of the homestat to save all data on datafile"

        fileContent = self.homeostat.dataCollector.printEssentialDataOnAString('')
        fileOut  = open(self.datafile, 'w')
        fileOut.write(fileContent)
        fileOut.close()

    def saveEssentialDataOnFile(self):
        '''Ask the datacollector of the homestat 
           to save only the essential data on datafile'''

        fileContent = self.homeostat.dataCollector.printEssentialDataOnAString('')
        fileOut  = open(self.datafile, 'w')
        fileOut.write(fileContent)
        fileOut.close()

    def saveEssentialDataOnFileWithSeparator(self, aCharacter):
        '''Ask the datacollector of the homestat 
           to save only the essential data on datafile,
           using aChracter as a column separator'''

        fileContent = self.homeostat.dataCollector.saveEssentialsOnAStringWithSeparator('', aCharacter)
        fileOut  = open(self.datafile, 'w')
        fileOut.write(fileContent)
        fileOut.close()

    def isReadyToGo(self):
        '''Check that the homeostat is ready to go and that 
           the maxRuns and datafile are present'''

        return (self._homeostat.isReadyToGo() and
                self.maxRuns is not None and
                self._datafile is not None)
        