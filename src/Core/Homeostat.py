'''
Created on Mar 13, 2013

@author: stefano
'''
from Core.HomeoDataCollector import  *
from Core.HomeoJIT import warmup_jit
from Helpers.General_Helper_Functions import withAllSubclasses
import time, sys, pickle
from Helpers.QObjectProxyEmitter import emitter
from RobotSimulator.WebotsTCPClient import *
from Helpers.ExceptionAndDebugClasses import hDebug


class HomeostatError(Exception):
    pass

class Homeostat(object):
    '''
    Homeostat manages a complete homeostat by taking care of the communication between the units and between the Units and the Uniselector.
    It stores a collection of units, and some state variables representing the general state of the Homeostat at any point in time. 
    "Starting" (an instance of) this class is equivalent to turning the switch on the electro-mechanical machine built by Ashby. 
    Notice that this is typically done by the application class HomeoSimulation, which offers facilities for adding units, 
    adding connections, selecting parameters pertaining to the homeostat (weights, etcetera) and pertaining to the simulation 
    (number of iterations, print out and/or display of data, etcetera). Homeostat collaborates with DataCollector 
    (an instance of which it holds) to record its states for any instant of time it goes through. However, it does not contain any facility
     for visualizing the data themselves.  If operated manually, an instance of Homeostat requires manually setting up the various 
    parameters and does not offer any output.
    
    Instance Variables:
        homeoUnits           <aCollection>    the collection of homeoUnits making up the homeostat
        microTime            <aNumber>        the temporal scale regulating the communication among units (typically identical to the unit time)
        slowingFactor        <aNumber>        the current slowingFactor index (i.e., t)
        dataCollector        <aDataCollector> the object recording the states of the homeostat
        collectsData         <aBoolean>       whether or not the homeostat collects data about its run
        slowingFactor:       <milliseconds>   it slows down the simulation by inserting a slowingFactor wait after each cycle.
        isRunning            <aBoolean>       whether the homeostat is running
        usesSocket           <aBoolean>       whether the homeostat uses Socket and therefore cannot be pickled
        host                 <aString>        a string with the IP address of the host running the simulation, or 'localhost' 
        port                 <anInteger>      port number accepting robotic commands
        client               <a WebTCPClient> the cllient holding the network connection, including the socket
    '''

#===============================================================================
# Class methods
#===============================================================================

    @classmethod    
    def readFrom(self,filename):
        '''This is a class method that create a new Homeostat instance from filename'''
        fileIn = open(filename, 'rb')
        unpickler = pickle.Unpickler(fileIn, encoding='latin-1')
        try:
            newHomeostat = unpickler.load()
        except Exception as e:
            raise HomeostatError("The file is not a pickled Homeostat: %s" % e)
        fileIn.close()
        if newHomeostat.isReadyToGo():
            return newHomeostat
        else:
            raise HomeostatError("The loaded is not a valid homeostat")

#===============================================================================
# Initialization methods, getters and setters
#===============================================================================

    def __init__(self, ip = None, port = None):
        '''Set slowingFactor to 0, and microTime to 0 as well, reflecting the default 
           conditions of a Homeostat. Sets also some physical equivalence parameters'''

#        super(Homeostat,self).__init__()
        self._slowingFactor = 0
        self._time = 0                                  # a newly created homeostat starts at 0
        self._microTime = 0
        self._homeoUnits = []
        self._dataCollector = HomeoDataCollector()
        self._collectsData = True                       # default is to collect data. Can be turned off via accessor.
        self._slowingFactor = 10                        # Default slowing time is 10 milliseconds 
        self._isRunning = False                         # a new homeostat is not running
        self._headless = False                          # when True, skip signal emissions for GUI
        self._usesSocket = False
        if ip != None:
            self._ip = ip
        if port != None:
            self. _port = port

    def getTime(self):
        return self._time
    def setTime(self,aValue):
        self._time = aValue
        if not getattr(self, '_headless', False):
            emitter(self).homeostatTimeChanged.emit(self._time)
    time = property(fget = lambda self: self.getTime(),
                    fset = lambda self, value: self.setTime(value))

    def getMicroTime(self):
        return self._microtime
    def setMicroTime(self,aValue):
        self._microtime = aValue
    microtime = property(fget = lambda self: self.getMicroTime(),
                         fset = lambda self, value: self.setMicroTime(value))
    
    def getHomeoUnits(self):
        return self._homeoUnits
    def setHomeoUnits(self,aValue):
        self._homeoUnits = aValue
    homeoUnits = property(fget = lambda self: self.getHomeoUnits(),
                          fset = lambda self, value: self.setHomeoUnits(value))


    def getDataCollector(self):
        return self._dataCollector
    def setDataCollector(self,aValue):
        self._dataCollector = aValue
    dataCollector = property(fget = lambda self: self.getDataCollector(),
                             fset = lambda self, value: self.setDataCollector(value))
    
    def getCollectsData(self):
        return self._collectsData

    def setCollectsData(self,aValue):
        self._collectsData = aValue
    collectsData = property(fget = lambda self: self.getCollectsData(),
                            fset = lambda self, value: self.setCollectsData(value))

    def getSlowingFactor(self):
        return self._slowingFactor
    def setSlowingFactor(self,aValue):
        self._slowingFactor = aValue
    slowingFactor = property(fget = lambda self: self.getSlowingFactor(),
                             fset = lambda self, value: self.setSlowingFactor(value))

    def getIsRunning(self):
        return self._isRunning
    def setIsRunning(self,aValue):
        self._isRunning = aValue
    isRunning = property(fget = lambda self: self.getIsRunning(),
                         fset = lambda self, value: self.setIsRunning(value))


#===============================================================================
# Testing methods
#===============================================================================

    def hasUnit(self,aHomeoUnit):
        "Check whether the Homeostat includes aHomeoUnit"

        return aHomeoUnit in self.homeoUnits 

    def homeoUnitsArePresent(self):
        '''Checks that the minimum number of units are present. 
           This is set to one, but the method is here so it can be 
           overridden in subclasses and/or changed in the future'''

        return len(self.homeoUnits) > 0

    def homeoUnitsAreReady(self):
        "Check that all units are ready"

        return False not in ([unit.isReadyToGo() for unit in self.homeoUnits])
 
    def isConnectedFromTo(self,aHomeoUnit,anotherUnit): 


        if (aHomeoUnit in self.homeoUnits) and anotherUnit in self.homeoUnits:
            return anotherUnit.isConnectedTo(aHomeoUnit)

    def isReadyToGo(self):
        '''Check that the homeostat has all the needed elements to start the simulation:
           - at least 1 homeoUnit
           - the homeoUnits are not missing any essential parameter
           - (Other conditions that are not fully clear yet to be added later)'''

        return self.homeoUnitsArePresent() and self.homeoUnitsAreReady

    def sameAs(self,aHomeostat):
        '''Check whether two homeostats are equivalent, defined as:
        
           1. Both belong to Homeostat class or its subclasses
           2. They have the same number of units
           3. The units are pair-wise equivalent
           
           Notice that this method will:
           
           - NOT consider equivalent homeostats with same units in different order
           - WILL consider equivalent homeostats with pair-wise equivalent units 
             BUT with DIFFERENT CONNECTIONS'''  

        areTheSame = True
        
        "receiver is a homeostat"

        if not aHomeostat.__class__ in withAllSubclasses(Homeostat):
            return False

        "Same number of units"

        if not len(self.homeoUnits) == len(aHomeostat.homeoUnits):
            return False 

        "equivalent units"

        for firstUnit, secondUnit in zip(self.homeoUnits, aHomeostat.homeoUnits):
            areTheSame = (areTheSame and (firstUnit.sameAs(secondUnit)))

        return areTheSame

#===============================================================================
# Running methods
#===============================================================================

    def fullReset(self):
        '''Reset the values of the units and their connections to default values  for basic parameters
           and to random values for deviation, weights, etc. 
           Reset time to 0.'''

        self.timeReset()
        self.restoreDefaultValuesForAllUnits()
        self.randomizeValuesforAllUnits()

    def runFor(self,ticks):
        '''Start the simulation by setting the units 'in motion' and run it 
           for a certain number of ticks. 
           This involves cycling through the units and asking them to update themselves, 
           then collecting data for each unit.
           First check that there are enough data to start'''

        sleepTime = self.slowingFactor

        if self.isReadyToGo():
            if self.time is None:
                self.time = 0
            "FOR TESTING"
            outputString = ("INITIAL DATA AT TIME: %u and tick: %u \n" % (self.time,  ticks))
            for unit in self.homeoUnits:
                outputString += ('Unit %s with output %.3f and critical deviation %.3f \n' %
                                 (unit.name,
                                 unit.currentOutput,
                                 unit.criticalDeviation))
            "END TESTING"

            if getattr(self, '_headless', False):
                warmup_jit()
                for unit in self.homeoUnits:
                    if unit.isActive():
                        unit._sync_jit_arrays()

            while self.time < ticks:
                for unit in self.homeoUnits:
                    if self.collectsData:
                        self.dataCollector.atTimeIndexAddDataUnitForAUnit(self.time, unit)
                    unit.time =  self.time
                    # sys.stderr.write("the status of %s in the function is %s and in the ivar is %s \n" % (unit.name, unit.isActive(), unit._status))
#                     print "unit: %s of type %s about to update with value: %.3f" % (unit.name, type(unit), unit.criticalDeviation)
                    if unit.isActive():
                        unit.selfUpdate()
                self.time +=  1
                if not getattr(self, '_headless', False):
                    emitter(self).homeostatTimeChanged.emit(self.time)
                if sleepTime > 0:
                    time.sleep(sleepTime / 1000)           # sleep accepts seconds, slowingFactor is in milliseconds
        else:
            sys.stderr.write('Warning: Homeostat is not ready to start')
            
        "FOR TESTING"
        outputString = 'FINAL DATA AT TIME: %u and tick %u \n' % (self.time, ticks)
        for unit in self.homeoUnits:
            outputString += ('Unit %s with output %.3f and deviation %.3f \n' %
                             (unit.name,
                             unit.currentOutput,
                             unit.criticalDeviation))
        "END TESTING"

    def runOnce(self):
        "Advance the simulation by one tick"
        
        upTo = self.time + 1
        self.runFor(upTo)
        
    def start(self):
        '''Start the simulation by setting the units "in motion." 
           This involves cycling though the units and asking them to update themselves, 
           then collecting data for each unit
           First check that it there are enough data to start
           Notice that once started the Homeostat goes on forever. 
           The only way to stop it is to send it the message stop.'''
        
        sleepTime = self.slowingFactor
        
        if self.isReadyToGo():
            if self.time is None:
                self.time = 0
            self.isRunning = True
            while self.isRunning:
                for unit in self.homeoUnits:
                    unit.time = time
                    unit.selfUpdate()
                    if self.collectsData:
                        self.dataCollector.atTimeIndexAddDataUnitForAUnit(self.time, unit)
                    self.time += 1
                    if sleepTime > 0:
                        time.sleep(sleepTime / 1000)           # sleep accepts seconds, slowingFactor is in milliseconds
        else:
            sys.stderr.write('Warning: Homeostat is not ready to start')

    def stop(self):
        '''Stop the homeostat's running by changing the value of the isRunning ivar to false. 
           This procedure is equivalent to, and indeed wants to simulate, 
           turning the switch off on the physical equivalent of the homeostat'''

        self.isRunning = False

    def timeReset(self):
        '''Reset time to 0. Does not change the external values of the units 
           or their connections, but do change their internal computational values: 
           input, nextDeviation, etcetera'''

        self.time = 0
        for unit in self.homeoUnits:
            unit.clearFutureValues()

#===============================================================================
# Adding methods
#===============================================================================

    def addConnectionWithRandomValuesFromUnit1toUnit2(self, unit1, unit2):
        '''Check that the units exist, and adds a connection 
           with random values by asking the receiving unit to do the job'''

        if unit1 in self.homeoUnits and unit2 in self.homeoUnits:
            unit2.addConnectionWithRandomValues(unit1)

    def addFullyConnectedUnit(self, aHomeoUnit):
        '''Add aHomeoUnit to the homeostat and creates connections between 
           the new units and all other HomeoUnits already present. 
           This latter task is delegated to the units themselves. 
           Notice that the connection are uni-directional, and we need 
           to add connections twice: from the new unit to the existing ones 
           and from the exiting one to the new unit.'''

        for unit in self.homeoUnits: 
            unit.addConnectionWithRandomValues(aHomeoUnit)
            aHomeoUnit.addConnectionWithRandomValues(unit)
            unit.maxConnectedUnits = len(self.homeoUnits) + 1           # let the old units know that there may be a new connected unit."        
        aHomeoUnit.maxConnectedUnits(len(self.homeoUnits))             # let the new unit know how many other units there may be."
        self.addUnit(aHomeoUnit)

    def addUnit(self, aHomeoUnit):
        '''Add a new unit to the homeostat'''

        if self.homeoUnits is None:
            self.homeoUnits = []
        if aHomeoUnit not in self.homeoUnits:
            self.homeoUnits.append(aHomeoUnit)

#===============================================================================
# Removing methods 
#===============================================================================

    def removeConnectionFromUnit1ToUnit2(self, unit1,unit2):
        '''Remove a connections between two units by asking 
           the receiving unit (unit2) to remove the inputConnection 
           coming from unit1'''

        if unit1 in self.homeoUnits and  unit2 in self.homeoUnits:
            if self.isConnectedFromTo(unit1, unit2):
                unit2.removeConnectionFromUnit(unit1)

    def removeUnit(self,aHomeoUnit):
        '''Remove a unit from the homeostat. Must also remove 
           all the connections originating from the unit'''

        if aHomeoUnit in self.homeoUnits:
            self.homeoUnits.remove(aHomeoUnit)
            for unit in self.homeoUnits:
                unit.removeConnectionFromUnit(aHomeoUnit)
        else:
            sys.stderr.write('Warning: trying to remove the unit %s which is not currently part of the Homeostat' % aHomeoUnit.name)

#===============================================================================
# Units managing methods
#===============================================================================

    def randomizeValuesForAHomeoUnit(self,aHomeoUnit):
        '''Reset the values of a unit to random values'''

        if aHomeoUnit in self.homeoUnits:
            aHomeoUnit.setRandomValues()

    def randomizeValuesforAllUnits(self):
        '''Reset all units to random values'''

        for unit in self.homeoUnits:
            unit.setRandomValues()
            unit.randomizeAllConnectionValues()
            
    def restoreDefaultValuesForAllUnits(self):
        "Restore default values for a unit's basic parameters"
        for unit in self.homeoUnits:
            unit.initializeBasicParameters()
            unit.initializeUniselector()
            
    def unitWithName(self,aString):
        '''Return the Unit with name aString, if it exists,
        Return None Otherwise. Assumes units' names are unique '''
        
        unit = list(filter(lambda x: x.name==aString, self.homeoUnits))
        if len(unit) == 0:
            return None
        else:
            return unit[0]

#===============================================================================
# Saving methods 
#===============================================================================

    def saveTo(self,filename):
        '''Pickle yourself to filename.
           It will erase the old content of aFilename.'''

        fileOut = open(filename, 'wb')
        pickler = pickle.Pickler(fileOut)
        pickler.dump(self)
        fileOut.close()

    def flushData(self):
        "Clear all data from aDataCollector"

        self.initializeDataCollection()

    def initializeDataCollection(self):
        "Trash the dataCollector, effectively flushing all collected data"

        self.dataCollector = HomeoDataCollector()
        
#===============================================================================
# Network-related
#===============================================================================
    def connectUnitsToNetwork(self):
        "Connect all transducer-connected units to network"
        if self._usesSocket == False:
            hDebug('network', "Trying to reconnect a homeostat that uses no sockets to network...Ignoring")
            return
        else:
            try:
                self._client.close()
                self._client = WebotsTCPClient(ip = self._host, port = self._port)
            except:
                self._client = WebotsTCPClient(ip = self._host, port = self._port)
                                                     
            for unit in self.homeoUnits:
                try:
                    unit.transducer.robotSocket = self._client.getClientSocket()
                    #print "now assigning new socket to transducers for unit %s" % unit.name
                except:
                    hDebug('network', ("Did not connect: The unit %s of type %s has no transducer" % (unit.name,
                                                                                         type(unit).__name__)))

    
    def reconnectUnitsToNetworkViaSocket(self,socket):
        """Reconnect all transducer-connected units
           by passing a new socket
        """
        self._socket = socket
        self.connectUnitsToNetwork()
                    
#===============================================================================
# Private-saving methods
#===============================================================================

'''No private saving methods, perhaps add later depending on HomeoSimulation needs'''

#===============================================================================
# Printing methods
#===============================================================================

'''No special printing methods, perhaps add later depending on GUI needs'''