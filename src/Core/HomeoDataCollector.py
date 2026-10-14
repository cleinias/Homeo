'''
Created on Mar 13, 2013

@author: stefano
'''
import pickle, sys, datetime
from Core.HomeoDataUnit import  *
import numpy as np


class HomeoDataCollector(object):
    '''DataCollector collects the data for the Homeostat simulation. It can output them 
       on different media (file, screen, etc) and formats, write them to file or read 
       them from file. DataCollector DOES NOT collect the data about the homeostat 
       itself---i.e. the engine that has produced the data. 
       The homeostat class knows how to save itself and, conversely, how to read 
       its data and parameters from a  saved instance.

        Instance Variables:
            states    <aDictionary>        a collection recording a description of the states of 
                                           all units, indexed by time t. It is a Dictionary indexed 
                                           by time t, with each elements containing a collection of 
                                           HomeoDataUnits indexed by unit's name. 
                                           It cannot be an Array because the index cannot be 
                                           restrained to positive numbers (1--n). 
                                           Indeed, the simulation usually starts at 0, 
                                           but it could reasonably start in the past.
    '''

#===============================================================================
# Initialization and setters and getters 
#===============================================================================

    def __init__(self):
        '''
        Initialize the states dictionay
        '''
        self._states = {}
    
    def getStates(self):
        return self._states
    
    def setStates(self, aValue):
        self._states = aValue
        
    states = property(fget = lambda self: self.getStates(),
                      fset = lambda self, value: self.setStates(value))

#===============================================================================
# Class methods
#===============================================================================
    @classmethod
    def readFrom(self, aFilename):
        '''Create a new DataCollector instance from a file containing 
           a saved instance object'''

        fileIn = open(aFilename, 'rb')
        unpickler = pickle.Unpickler(fileIn)
        newDataCollector = unpickler.load()
        fileIn.close()
        return newDataCollector
        
#===============================================================================
# Saving methods
#===============================================================================

    def saveOn(self, aFilename):
        '''Save itself on a new pickle file opened on aFilename. 
           It will erase the old content of aFilename'''


        fileOut = open(aFilename, 'wb')
        pickler = pickle.Pickler(fileOut)
        pickler.dump(self)
        fileOut.close()

         
    def saveCompleteDataOnFile(self,aFilename):
        '''Save all data on a file in text format.
        Will erase aFilename if it exists already'''
        
        dataToSave = self.printCompleteDataOnAString('')
        fileOut = open(aFilename, 'w')
        fileOut.write(dataToSave)
        fileOut.close()
                   

    def saveEssentialDataOnFile(self,aFilename):
        '''Save essential data on a file in text format.
        Will erase aFilename if it exists already'''
        
#        dataToSave = self.printEssentialDataOnAString('')
        dataToSave = self.printPlottingDataForROnAString('')
        fileOut = open(aFilename, 'w')
        fileOut.write(dataToSave)
        fileOut.close()



#===============================================================================
# Accessing methods
#===============================================================================

    def atTimeIndexAddDataUnitForAUnit(self, timeIndex, aHomeoUnit):
        '''Add a dataunit for aHomeoUnit representing the latter state at time timeIndex'''

        if self.states is None: self.states = {}
        if timeIndex not in self.states.keys():
            self.states[timeIndex] = {} 
        self.states[timeIndex][aHomeoUnit.name] = HomeoDataUnit.newUnitFor(aHomeoUnit)


#===============================================================================
# Printing methods
#===============================================================================

    def printCompleteDataOnAString(self, aString):
        '''Append to aString a complete representation of its data'''
        
        for state in self.states:
            if self.states[state] is not None:
                for value in self.states[state]:
                    aString += "time:    %u    " % state
                    aString += self.states[state][value].printDataOn('')
        return aString


    def printEssentialDataOnAString(self, aString):
        '''Append to aString a brief representation of its data, with column headers'''
#        aString += 'time,'
        timeIndex = 0
        for state in self.states:
            if self.states[state] is not None:
                for key,value in self.states[state].items():
                    aString += " time:    %u    " % timeIndex
                    aString += value.name
                    aString += ":    "
                    aString += value.printEssentialVariableOn('')
            timeIndex += 1
        return aString


    def printPlottingDataForROnAString(self, aString):
        '''Append to aString a multi-column representation of its data, suitable for plotting. 
           aCharacter is the character separatng the column.
           
           The format includes:
           - first a couple of lines of commented data detailing 
             the particular simulation the data describe,
           - then a commented line with the data headers
           - then a sequence of lines with each  column containing the 
             critical deviation value for a unit and its uniselector activation (1 if any, o/w 0)'''


        aCharacter = ','
        
        unitNames = []
        if len(self.states) == 0:
            sys.stderr.write("DataCollector: There are no data to save")
        for index, dataUnit in self.states[0].items():
            unitNames.append(dataUnit.name)
        
        criticDevData = self.criticalDevAsCollectionOfArraysForAllUnits()

        "Print a header with general information at the top of the file"
        aString +=  '# Simulation data produced by HOMEO---the homeostat simulation program\n'
        aString +=  '# Data printed on: '
        aString +=  str(datetime.datetime.now())
        aString +=  "\n"
        aString +=  '# There were exactly %u units in this simulation' % len(unitNames) 
        aString += "\n"

        "Print  the column headers"
        for index, name in enumerate(unitNames):
            if index != 0:
                aString += aCharacter
            aString += name
            aString += aCharacter
            aString += name
            aString += '_un.'
        aString += "\n"

        "print the data"
        for timeSlice in criticDevData:
            CSVString = ",".join(map(str,timeSlice))
            aString += CSVString
            aString += '\n'

        return aString


    
#===============================================================================
# Converting methods
#===============================================================================

    def criticalDevAsCollectionForUnit(self, aHomeoUnit):
        '''Extract the Critical Deviaton values for aHomeoUnit 
           and return them as an Ordered Collection'''

        aCollection = []
        for state in self.states:
            if state is not None:
                for key, value in self.states[state].items():
                    if key == aHomeoUnit.name:
                        aCollection.append(value.criticalDeviation)
        return aCollection

    def criticalDevAsCollectionOfArraysForAllUnits(self):
        '''Extract the Critical Deviation and Uniselector activation data for all units
           and returns them as a list of lists, one per point in time:
           [unit 1 deviation, unit 1 uniselector active (0/1), unit 2 deviation, ...]
           (the R exporter's columns).  criticalDevAsNPArrayForAllUnits has
           the deviations alone.'''

        aCollection = []
        for stateAtTick, data in self.states.items():
            if data is not None:
                dataPoint = []
                for HomeoUnitName, homeoDataUnit in data.items():
                    dataPoint.append(homeoDataUnit.criticalDeviation)
                    if (homeoDataUnit.uniselectorActive == True):
                        dataPoint.append(1)
                    else:
                        dataPoint.append(0)
                aCollection.append(dataPoint)

        return aCollection


    def criticalDevAsNPArrayForAllUnits(self):
        '''The critical deviations of all units as a (ticks, units) NumPy
           array, one row per recorded tick and one column per unit, in the
           order the units were recorded (the homeostat's).  Until 14 Oct 2026
           it returned criticalDevAsCollectionOfArraysForAllUnits as an array,
           each deviation column followed by a 0/1 uniselector column, although
           CODE_OVERVIEW called it the deviation history (CD-14).'''

        return np.array([[dataUnit.criticalDeviation for dataUnit in data.values()]
                         for data in self.states.values() if data is not None])
    
    def criticalDevAsNPArrayForUnit(self,aHomeoUnit):
        '''Convert the representaiton of critical deviation homeoDataunits for aHomeoUJnit 
           from a list of list into a mono-dim NP-Array'''
        
        npArr = np.array(self.criticalDevAsCollectionForUnit(aHomeoUnit))
        return npArr