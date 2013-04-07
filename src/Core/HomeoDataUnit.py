'''
Created on Mar 13, 2013

@author: stefano
'''

class HomeoDataUnit(object):
    '''
    HomeoDataUnit holds the 'photograph' of a HomeoUnit unit at a certain 
    time instant t. It contains a representation of all the variables affecting 
    the unit's functioning. It knows how to read these values from a unit and 
    how to print itself (in various ways) on a stream. Consistently with Ashby's, 
    the time itself is not recorded, because we are assuming that the unit is 
    in time always, and the data unit represents a particular splice of the unit's behavior.
    
    Instance Variables:
        connectedTo             <aDictionary>    indexed by unit's name: it contains weight, switch, 
                                                 and state for every unit connected to.
        criticalDeviation       <aNumber>        the critical value of the unit at t
        maxDeviation            <anObject>       the  maximum deviation of the unit
        name                    <aString>        name of the unit
        output                  <aNumber>        output value at t
        uniselectorState        <aString>        state of the unit's uniselector
        uniselectorActive       <aNumber>        indicates whether the uniselector is active at time t 
                                                 (thus potentially changing connections' weight for time t+1) 
    '''

#===============================================================================
# Class methods
#===============================================================================

    @classmethod
    def newUnitFor(cls, aHomeoUnit):
        '''Create a new instance, reads the state from aHomeoUnit and returns it.
           This is just a convenience, but it is the most common use of HomeoDataUnit'''

        dataUnit = HomeoDataUnit()

        return dataUnit.readStateFrom(aHomeoUnit)


#===============================================================================
# Initialization and getter and setter methods 
#===============================================================================

    def getUniselectorActive(self):
        return self._connectedTo
    
    def setUniselectorActive(self, anObject):
        self._connectedTo = anObject
    
    connectedTo = property(fget = lambda self: self.getUniselectorActive(),
                         fset = lambda self, value: self.setUniselectorActive(value))
    
    def getCriticalDeviation(self):
        return self._criticalDeviation
    
    def setCriticalDeviation(self, anObject):
        self._criticalDeviation = anObject
    
    criticalDeviation = property(fget = lambda self: self.getCriticalDeviation(),
                         fset = lambda self, value: self.setCriticalDeviation(value))
    def getMaxDeviation(self):
        return self._maxDeviation
    
    def setMaxDeviation(self, anObject):
        self._maxDeviation = anObject
    
    maxDeviation = property(fget = lambda self: self.getMaxDeviation(),
                         fset = lambda self, value: self.setMaxDeviation(value))

    def getName(self):
        return self._name
    
    def setName(self, anObject):
        self._name = anObject
    
    name = property(fget = lambda self: self.getName(),
                         fset = lambda self, value: self.setName(value))
    
    def getOutput(self):
        return self._output
    
    def setOutput(self, anObject):
        self._output = anObject
    
    output = property(fget = lambda self: self.getOutput(),
                         fset = lambda self, value: self.setOutput(value))

    def getUniselectorState(self):
        return self._uniselectorState
    
    def setUniselectorState(self, anObject):
        self._uniselectorState = anObject
    
    uniselectorState = property(fget = lambda self: self.getUniselectorState(),
                         fset = lambda self, value: self.setUniselectorState(value))
    
    def __init__(self):
        '''
        Initialization simply sets all ivars to None, as a DataUnit will always be created 
        with a class method passing a HomeoUnit and filling all its variables
        '''
        self._connectedTo = {}
        self._criticalDeviation = None
        self._maxDeviation = None
        self._name = None
        self._output = None
        self._uniselectorState = None
        self._uniselectorActive = None
        
    def readStateFrom(self, aHomeoUnit):
        '''
        Read the values for a DataUnit variable from aHomeoUnit
        '''

        self.name = aHomeoUnit.name
        self.output = aHomeoUnit.currentOutput
        self.uniselectorState = aHomeoUnit.uniselectorActive
        self.maxDeviation =  aHomeoUnit.maxDeviation
        self.criticalDeviation = aHomeoUnit.criticalDeviation
        self.uniselectorActive = aHomeoUnit.uniselectorActive
        for conn in aHomeoUnit.inputConnections:
            self.connectedTo[conn.incomingUnit.name] = [conn.weight, conn.switch, conn.state, conn.noise]

#===============================================================================
# Testing methods 
#===============================================================================

        def sameValuesAs(self, aDataUnit):
            '''Answer true if the values in the two data units are the same. 
               Do  not check the values of the connections'''

            return (self.name == aDataUnit.name and
                    self.output == aDataUnit.output and
                    self.maxDeviation == aDataUnit.maxDeviation and
                    self.uniselectorState == aDataUnit.uniselectorState)

#===============================================================================
# Printing methods
#===============================================================================

    def printCriticalDeviationOn(self,aString):
        '''Appends the DataUnit's criticalDeviation values to aString. 
           Useful for graphing and compact representations.'''
    
        aString =+ "%.5f" % self.criticalDeviation
        return aString

    def printDataOn(self,aString):
        '''Append to aString a complete representation of its data'''

        aString += "name ; %s output: %.5f uniselector: %s" % (self.name, self.output, self.uniselectorState)
        for connName, connValue in self.connectedTo.iteritems():
            aString += " Connct to: %s weight: %.5f switch: %u noise: %.5f \n" % (connName.name,
                                                                                  connValue[0],
                                                                                  connValue[1],
                                                                                  connValue[2],
                                                                                  connValue[2],)

    def printEssentialVariableOn(self, aString):
        '''Append only the DataUnit's output values to aString.
           Useful for graphing and compact representations.'''

        aString += "%.5f\n" % self.output
    
    def printUniselectorActivatedOn(self, aString):
        '''Prints only the data about the DataUnit's uniselector's activation'''
        
        aString += "%s\n" % self.uniselectorActive

        