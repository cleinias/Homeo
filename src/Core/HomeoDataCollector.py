'''
Created on Mar 13, 2013

@author: stefano
'''
import pickle, sys, datetime
from Core.HomeoDataUnit import  *
import numpy as np


class HomeoDataCollector(object):
    '''DataCollector collects the data for the Homestat simulation. It can output them 
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

        fileIn = open(aFilename, 'r')
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


        fileOut = open(aFilename, 'w')
        pickler = pickle.Pickler(fileOut)
        pickler.dump(self) 
        fileOut.close()

    def saveDeviationOnForUnit(self, aString, aUnit):
        '''Append the output of the simulation to a string (typically associated 
           to a file by the calling app) as a series of lines, one per time tick, 
           each comprising the critical deviation  value for aUnit'''

        for timeItem in self.states:
            for dataUnit in timeItem:
                if dataUnit == aUnit:
                    aString += "%.5f\n" % dataUnit.output
        return aString
         
    def saveCompleteDataOnFile(self,aFilename):
        '''Save all data on a file in text format.
        Will erase aFilename if it exists already'''
        
        dataToSave = self.printCompleteDataOnAString('')
        fileOut = open(aFilename, 'w')
        fileOut.write(dataToSave)
        fileOut.close()
                   
    def saveEssentialsOnAStringWithSeparator(self, aString, aCharacter):
        '''Save the output of the simulation on aString (typically associated 
           to a file by the calling app) as a series of lines, one per time tick, 
           each comprising a row of output values separated by aCharacter.'''

        for timeItem in self.states:
            for dataUnit in timeItem:
                    aString += "%.5f" % dataUnit.output
                    aString += aCharacter + "\n"
        return aString

    def saveEssentialDataOnFile(self,aFilename):
        '''Save essential data on a file in text format.
        Will erase aFilename if it exists already'''
        
        dataToSave = self.printEssentialDataOnAString('')
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

    def printCompleteDataForUnitOn(self, aHomeoUnit, aString):
        '''Append to aString a brief representation of aHomeoUnit data'''
        
        timeIndex = 0
        for state in self.states:
            if state is not None:
                for key,value in state.iteritems():
                    if key == aHomeoUnit.name:
                        aString += "time: %u    " % timeIndex
                        aString += value.printDataOn('')
            timeIndex += 1

    def printCompleteDataOnAString(self, aString):
        '''Append to aString a complete representation of its data'''
        
        for state in self.states:
            if self.states[state] is not None:
                for value in self.states[state]:
                    aString += "time:    %u    " % state
                    aString += self.states[state][value].printDataOn('')
        return aString

    def printCriticalDevForUnitOnAString(self, aHomeoUnit, aString):
        '''Append to aString the values for Critical Deviation of aHomeoUnit'''
        
        for state in self.states:
            if state is not None:
                for key,value in state.iteritems():
                    if key == aHomeoUnit.name:
                        aString += value.printCriticalDeviationOn('')

    def printEssentialDataForUnitOnAString(self, aHomeoUnit, aString):
        '''Append to aString a brief representation of aHomeoUnit data'''
        
        timeIndex = 0
        for state in self.states:
            if state is not None:
                for key, value in state.iteritems():
                    if key == aHomeoUnit.name:
                        aString += 'time: %u    ' % timeIndex
                        aString += value.name
                        aString += value.printEssentialVariableOn('')
                timeIndex += 1

    def printEssentialDataOnAString(self, aString):
        '''Append to aString a brief representation of its data'''
        timeIndex = 0
        for state in self.states:
            if self.states[state] is not None:
                for key,value in self.states[state].iteritems():
                    aString += " time:    %u    " % timeIndex
                    aString += value.name
                    aString += ":    "
                    aString += value.printEssentialVariableOn('')
            timeIndex += 1
        return aString

    def printPlottingDataForGgobiOnAString(self, aString):
        '''Append to aString a multi-column representation of its data, 
           suitable for plotting. aCharacter is the character separatng the column.
            The format includes:
            - first a couple of lines of commented data detailing the particular simulation the data describe,
            then a commented line with the data headers
            then a sequence of lines with each  column containing the critical deviation value for a unit 
            
            We convert datapoints  to a fixed number of decimal '''

        "FIXIT This use of decimals is not correct in Python" 
        decimals = 8    #The number of fixed decimals we keep. 
                            # Data points are double and may have up to 15 digits, 
                            # sometimes expressed in exponential notation"

        aCharacter = ','

        unitNames = []
        if len(self.states) ==0:
            sys.stderr.write("DataCollector: There are no data to save")
            return
        for dataUnit in self.states[0]:
            unitNames.append(dataUnit.name)
                
        criticDevData = self.criticalDevAsCollectionOfArraysForAllUnits()


        "Print  the column headers"
        aString += 'Time,'
        for name in unitNames:
            aString += str(name)
            aString += aCharacter
            aString +=  name
            aString += '-unisel'
            aString += aCharacter
            aString += "\n"

        "print the data"
        for timeSlice, index in enumerate(criticDevData):
            aString += "%u" % index
            aString += aCharacter
            for dataPoint in timeSlice:
                aString +=  "%.8f" % dataPoint
                aString += aCharacter 
            aString += "\n"
        
        return aString

    def printPlottingDataForROnAString(self, aString):
        '''Append to aString a multi-column representation of its data, suitable for plotting. 
           aCharacter is the character separatng the column.
           
           The format includes:
           - first a couple of lines of commented data detailing 
             the particular simulation the data describe,
           - then a commented line with the data headers
           - then a sequence of lines with each  column containing the 
             critical deviation value for a unit '''


        aCharacter = ','
        
        unitNames = []
        if len(self.states) == 0:
            sys.stderr.write("DataCollector: There are no data to save")
        for dataUnit in self.states[0]:
            unitNames.append(dataUnit.name)
        
        criticDevData = self.criticalDevAsCollectionOfArraysForAllUnits()

        "Print a header with general information at the top of the file"
        aString +=  '# Simulation data produced by HOMEO---the homeostat simulation program\n'
        aString +=  '# Data printed on: '
        aString +=  datetime.datetime.now()
        aString +=  "\n"
        aString +=  '# There were exactly %u units in this simulation' % len(unitNames) 
        aString += "\n\n\n"

        "Print  the column headers, preceded by the 'Time' Header"
        aString += 'Time'
        aString += aCharacter
        for name in unitNames:
            aString += name
            aString += aCharacter
            aString += name
            aString += '-unisel'
            aString += aCharacter 
        aString += "\n"

        "print the data"
        for timeSlice, index in enumerate(criticDevData):
            aString += index
            aString += aCharacter
            for dataPoint in timeSlice:
                aString +=  "%.8f" % dataPoint
                aString +=  aCharacter
            aString += "\n"

        return aString

    def printPlottingDataOnAString(self, aString):
        '''Append to aString a multi-column representation of its data, suitable for plotting. 
            The format includes:
            - first a couple of lines of commented data detailing the particular simulation the data describe,
            - then a commented line with the data headers
            - then a sequence of lines with each  column containing the critical deviation value for a unit'''

        unitNames = []
        if len(self.states) == 0:
            sys.stderr.write("DataCollector: There are no data to save")
        for dataUnit in self.states[0]:
            unitNames.append(dataUnit.name)
        criticDevData = self.criticalDevAsCollectionOfArraysForAllUnits()

        "Print a header with general information at the top of the file"
        aString += '# Simulation data produced by HOMEO---the homeostat simulation program'
        aString += "\n"
        aString += '# Data printed on: '
        aString += datetime.datetime.now()
        aString += "\n"
        aString +=  '# There were exactly %u ' % len(unitNames)
        aString += 'units in this simulation'
        aString += "\n\n\n"
        aString +=  '# \n'
        for name in unitNames:
            aString += name
            aString += "\t\t\t"
            aString += name
            aString += '-unisel'
            aString += "\t\t\t"
        aString +=  "\n"

        "print the data"
        for timeSlice in criticDevData:
            for dataPoint in timeSlice:
                aString += "%8.f" % dataPoint
                aString += "\t\t\t"
            aString += "\n"
        
        return aString

    def printPlottingDataOnAStringWithSeparator(self, aString, aCharacter):
        '''Append to aString a multi-column  representation of its data, suitable for plotting. 
           aCharacter is the character separatng the column.
           The format includes:
           - first a couple of lines of commented data detailing the particular simulation the data describe,
           - then a commented line with the data headers
           - then a sequence of lines with each  column containing the critical deviation value for a unit '''

        unitNames = []
        if len(self.states)  == 0:
            sys.stderr.write("DataCollector: There are no data to save")
        for dataUnit in self.states[0]:
            unitNames.append(dataUnit.name)
        criticDevData = self.criticalDevAsCollectionOfArraysForAllUnits()

        "Print a header with general information at the top of the file"
        aString += '# Simulation data produced by HOMEO---the homeostat simulation program'
        aString += '\n'
        aString += '# Data printed on: '
        aString += datetime.datetime.now()
        aString += '\n'
        aString += '# There were exactly %u units in this simulation' % len(unitNames)
        aString += "\n\n\n"
        aString += '# \n'
        for name in unitNames:
            aString += name
            aString += aCharacter
            aString += name
            aString += '-unisel'
            aString += aCharacter
        aString += "\n"

        "print the data"
        for timeSlice in criticDevData:
            for dataPoint in timeSlice:
                aString += "%.8f" % dataPoint
                aString +=  aCharacter
            aString += "\n"
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
                for key, value in self.states[state].iteritems():
                    if key == aHomeoUnit.name:
                        aCollection.append(value.criticalDeviation)
        return aCollection

    def criticalDevAsCollectionOfArraysForAllUnits(self):
        '''Extract the Critical Deviation and Uniselector activation data for all units 
           and returns them as a list of lists 
           Each list has all the homeoDataunits for a point in time'''

        aCollection = []
        for stateAtTick, data in self.states.iteritems():
            if data is not None:
                dataPoint = []
                for HomeoUnitName, homeoDataUnit in data.iteritems():
                    dataPoint.append(homeoDataUnit.criticalDeviation)
                    dataPoint.append(homeoDataUnit.uniselectorActive)
            aCollection.append(dataPoint)

        return aCollection

    def uniselectorActivatedAsCollectionOfArraysForAllUnits(self):
        '''Extract the data about the activation of the uniselector for all units 
           and returns them as a list of lists. 
           Each list  has all the values for a point in time'''

        aCollection = []
        for state in self.states:
            if state is not None:
                dataPoint = []
                for value in state:
                    dataPoint.append(value.uniselectorActivated)
            aCollection.append(dataPoint)

        return aCollection

    def criticalDevAsNPArrayForAllUnits(self):
        '''Convert the representation of critical deviation homeoDataunits for all units 
           from a list of list into a multi-dim NP-Array'''

        npArr = np.array(self.criticalDevAsCollectionOfArraysForAllUnits())
        return npArr
    
    def criticalDevAsNPArrayForUnit(self,aHomeoUnit):
        '''Convert the representaiton of critical deviation homeoDataunits for aHomeoUJnit 
           from a list of list into a mono-dim NP-Array'''
        
        npArr = np.array(self.criticalDevAsCollectionForUnit(aHomeoUnit))
        return npArr