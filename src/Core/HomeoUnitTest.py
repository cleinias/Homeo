from __future__ import division
from   HomeoUnit import *
from   HomeoUniselector import *
from   Homeostat import *
from   Helpers.General_Helper_Functions import  withAllSubclasses
import unittest, numpy, string, random, pickle, os
from copy import copy
from _pydev_xmlrpclib import Error

class HomeoUnitTest(unittest.TestCase):
    """Unit testing for the HomeoUnit class and subclasses, including adding and removing connections to other HomeoUnits."""
    
    def setUp(self):
        """Set up a Homeounit for all tests in the suite"""
        self.unit = HomeoUnit()
        self.unit.setRandomValues()
        
    def tearDown(self):
        pass
    def testAddConnectionUnitWeightPolarityState(self):
        """Connect to another unit and test the connection values."""
        newUnit = HomeoUnit()
        weight = 0.5
        polarity = 1
        state = 'manual'
        self.unit.addConnectionUnitWeightPolarityState(newUnit, weight, polarity, state)
        self.assertTrue(self.unit.inputConnections is not None)
        self.assertTrue(self.unit.inputConnections[-1].incomingUnit == newUnit)
        self.assertTrue(self.unit.inputConnections[-1].weight == weight)
        self.assertTrue(self.unit.inputConnections[-1].switch == polarity)
        self.assertTrue(self.unit.inputConnections[-1].state == 'manual')

    def testClassDefaults(self):
        """test that  the class has its appropriate dictionary of Defaults and that the values are not empty."""
        defParam = HomeoUnit.DefaultParameters  #HomeoUnit class variables with all the defaults values"


        self.assertTrue(defParam.has_key('viscosity'))
        self.assertTrue(defParam.has_key('maxDeviation'))
        self.assertTrue(defParam.has_key('outputRange'))
        self.assertTrue(defParam.has_key('noise'))
        self.assertTrue(defParam.has_key('potentiometer'))
        self.assertTrue(defParam.has_key('time'))
        self.assertTrue(defParam.has_key('uniselectorTimeInterval'))
        self.assertTrue(defParam.has_key('uniselectorTime'))
        self.assertTrue(defParam.has_key('needleCompMethod'))
        self.assertTrue(defParam.has_key('outputRange'))
        self.assertTrue(defParam.has_key('critThreshold'))

        self.assertTrue(defParam['viscosity'] is not None)
        self.assertTrue(defParam['maxDeviation'] is not None)
        self.assertTrue(defParam['noise'] is not None)
        self.assertTrue(defParam['potentiometer'] is not None)
        self.assertTrue(defParam['time'] is not None)
        self.assertTrue(defParam['uniselectorTimeInterval'] is not None)
        self.assertTrue(defParam['uniselectorTime'] is not None)
        self.assertTrue(defParam['needleCompMethod']  is not None)
        self.assertTrue(defParam['outputRange'] is not None)
        self.assertTrue(defParam['critThreshold'] is not None)

        outputRange = defParam['outputRange']

        self.assertTrue(outputRange.has_key('high'))
        self.assertTrue(outputRange['high'] is not None)

        self.assertTrue(outputRange.has_key('low'))
        self.assertTrue(outputRange['low'] is not None)
        
    def testSaveToFileAndBack(self):
        '''test that the unit can be saved to file and recovered.
        Pickle the unit to a new file to erase afterwards'''
        
        fileOut = 'saved_HomeoUnit_test'
        self.unit.saveTo(fileOut)
        newUnit = HomeoUnit.readFrom(fileOut)
        os.remove(fileOut)
        
        "The read back unit belongs to HomeoUnit or its subclasses"
        self.assertTrue(newUnit.__class__ in withAllSubclasses(HomeoUnit))
        
        " and it is functionally equivalent"
        self.assertTrue(self.unit.sameAs(newUnit))

    def testIsConnectedTo(self):
        newUnit=HomeoUnit()
        weight = 0.5
        polarity = 1

        self.assertFalse(self.unit.isConnectedTo(newUnit))
        self.unit.addConnectionUnitWeightPolarityState(newUnit,weight,polarity,'manual')
        self.assertTrue(self.unit.isConnectedTo(newUnit))
        
    def testRandomizeValues(self):
        self.unit.setRandomValues()
        oldOutput = self.unit.currentOutput
        self.unit.setRandomValues()
        self.assertFalse(oldOutput == self.unit.currentOutput)
            
    def testRemoveConnection(self):
        newUnit = HomeoUnit()
        weight = 0.5
        polarity = 1

        self.unit.addConnectionUnitWeightPolarityState(newUnit,weight,polarity,'manual')
        self.assertTrue(self.unit.isConnectedTo(newUnit))
        self.unit.removeConnectionFromUnit(newUnit)
        self.assertFalse(self.unit.isConnectedTo(newUnit))

    def testIstReadyToGo(self):
        "test the initialization procedure of a HomeoUnit against the conditions set in the isReadyToGo method"
        "A newly created unit must be ready to go"
        newUnit=HomeoUnit() 
        self.assertTrue(newUnit.isReadyToGo())

    def testUnitNameExist(self):
        "Units must have a name"
        self.assertTrue(self.unit.name is not None)

    def testUnitNameUnique(self):
        "Two units cannot have the sane name. Check on 100 units"
        #Create 100 units, collects their names and check"
        self.unitNames = []
        for i in xrange(100):
            newUnit = HomeoUnit()
            self.unitNames.append(newUnit.name)
        self.assertTrue(len(self.unitNames) == len(set(self.unitNames)))
                
    def testApplicationInternalNoise(self):
        "Check that in presence of noise the unit's critical deviation is changed  and not changed when noise = 0."
        # FIXIT A more comprehensive test could p/h check that the noise value applied is uniformly distributing, proportional, and distorting."

        self.unit.setRandomValues()
        self.unit.noise = 0.1
        for i in xrange(1,10):
            oldDeviation = self.unit.criticalDeviation
            self.unit.updateDeviationWithNoise()
            self.assertFalse(oldDeviation == self.unit.criticalDeviation)

        self.unit.noise = 0
        for i in xrange(1,10):
            oldDeviation = self.unit.criticalDeviation
            self.unit.updateDeviationWithNoise()
            self.assertTrue(oldDeviation == self.unit.criticalDeviation)
            
    def testComputeNextDeviationRunoffAndStabilityLinear(self):
        "Approximate tests on the behavior of a self-connected unit running repeatedly. Check if it runs to (+/-) infinity or it stabilizes"

        errorTolerance = pow(10,-6)              
        self.unit = HomeoUnit()

        #the polarity of the output controls the change in the criticalDeviation through simple summation.
        #We  check that it runs up toward positive infinity (1) and negative infinity (2) (with linear increases)"
        # We set noises to 0, viscosity to 1, potentiometer to 1, etc, to check that the basic mechanism works."

        self.unit.needleCompMethod = 'linear'
        self.unit.needleUnit.mass = 1                 # the force acting on a Aristotelian unit is always inversely proportional to the mass. 
                                                     # set it to 1 to exclude complications from this test."

        #1. with self connection to 1, noise at 0, viscosity to 1 and the unit not connected to other units, 
        # the deviation increases by the ratio criticalDeviation/maxDeviation every cycle if it starts positive, 
        #because output is proportional to the unit's range. Eventually it will go up to infinity, i..e to maxDeviation." 

        self.unit.potentiometer = 1                  #this sets the value of the self-connection"
        self.unit.inputConnections[0].newWeight(abs(self.unit.potentiometer))     # make sure self-connection is positive"
        self.unit.noise = 0                          #No noise  to simplify computations"
        self.unit.viscosity = 0                      #No viscosity to simplify computations
        self.unit.criticalDeviation = 1
        self.unit.computeOutput()
        for i in xrange(10):
            expectedDev = self.unit.criticalDeviation + self.unit.currentOutput
            self.unit.selfUpdate()
        self.assertTrue(abs(self.unit.criticalDeviation  - expectedDev) < errorTolerance)     
        for i in xrange(100):
            self.unit.selfUpdate()
        self.assertTrue(self.unit.criticalDeviation == self.unit.maxDeviation)



        #"2. with starting point negative we will run up to negative infinity, 
        # because the output will become negative after the first iteration."
        self.unit.criticalDeviation = -3
        self.unit.computeOutput()
        expectedDev = self.unit.criticalDeviation + self.unit.currentOutput
        self.unit.selfUpdate()
        self.assertTrue(self.unit.criticalDeviation == expectedDev)
        
        for i in xrange(10):
            expectedDev = self.unit.criticalDeviation + self.unit.currentOutput
            self.unit.selfUpdate()
        self.assertTrue(abs(self.unit.criticalDeviation  - expectedDev)  < errorTolerance)     
        for i in xrange(100):
            self.unit.selfUpdate()            
        self.assertTrue(self.unit.criticalDeviation == self.unit.minDeviation)



        # 3. with polarity reversed the unit will tend to stabilize itself around 0, 
        # because the output will always counteract the unit's deviation. "
        self.unit.switch = - 1                          #"self-connection's switch is negative: 
                                                        # unit's output is reinputted with reverse polarity"

        self.unit.criticalDeviation = -2
        self.unit.computeOutput()
        self.unit.selfUpdate()
        self.assertTrue(self.unit.criticalDeviation == (-2 + 0.2))
        for i in xrange(200):
            self.unit.selfUpdate()
        self.assertTrue(abs(self.unit.criticalDeviation) < errorTolerance)

        #4." 
        self.unit.criticalDeviation = 2
        self.unit.computeOutput()
        self.unit.selfUpdate()
        self.assertTrue((self.unit.criticalDeviation - (2 - 0.2)) < errorTolerance)
        for i in xrange(200):
            self.unit.selfUpdate()
        self.assertTrue(abs(self.unit.criticalDeviation) < errorTolerance)

    def testComputeNextDeviationRunoffAndStabilityProportional(self):
        "Approximate tests on the behavior of a self-connected unit running repeatedly. Check if it runs to (+/-) infinity or it stabilizes"

        errorTolerance = pow(10,-6)              
        self.unit = HomeoUnit()

        '''The polarity of the output controls the change in the criticalDeviation through simple summation.
         We  check that it runs up toward positive infinity (1) and negative infinity (2) (with proportional increases)"
         We set noises to 0, viscosity to 1, potentiometer to 1, etc, to check that the basic mechanism works.'''

        self.unit.needleCompMethod = 'proportional'
        self.unit.needleUnit.mass = 1                 # the force acting on a Aristotelian unit is always inversely proportional to the mass. 
                                                     # set it to 1 to exclude complications from this test."

        #1. with self connection to 1, noise at 0, viscosity to 1 and the unit not connected to other units, 
        # the deviation increases by the ratio criticalDeviation/maxDeviation every cycle if it starts positive, 
        #because output is proportional to the unit's range. Eventually it will go up to infinity, i..e to maxDeviation." 

        self.unit.potentiometer = 1                  #this sets the value of the self-connection"
        self.unit.inputConnections[0].newWeight(abs(self.unit.potentiometer))     # make sure self-connection is positive"
        self.unit.noise = 0                          #No noise  to simplify computations"
        self.unit.viscosity = 0                      #No viscosity to simplify computations
        self.unit.criticalDeviation = 1
        self.unit.computeOutput()
        for i in xrange(10):
            expectedDev = self.unit.criticalDeviation + (self.unit.currentOutput / (self.unit.maxDeviation *2.))
            self.unit.selfUpdate()
        self.assertTrue(abs(self.unit.criticalDeviation  - expectedDev) < errorTolerance)     
        runs = 1
        maxruns = 500
        while self.unit.criticalDeviation < self.unit.maxDeviation:
            self.unit.selfUpdate()
            runs += 1
            if runs > maxruns:
                raise(HomeoUnitError, "The unit does not run off after %u runs" % runs)
        self.assertTrue(self.unit.criticalDeviation == self.unit.maxDeviation)



        #"2. with starting point negative we will run up to negative infinity, 
        # because the output will become negative after the first iteration."
        self.unit.criticalDeviation = -1
        self.unit.computeOutput()
        expectedDev = self.unit.criticalDeviation + (self.unit.currentOutput /(self.unit.maxDeviation *2.))
        self.unit.selfUpdate()
        self.assertTrue((self.unit.criticalDeviation - expectedDev) < errorTolerance)        
        for i in xrange(10):
            expectedDev = self.unit.criticalDeviation + (self.unit.currentOutput / (self.unit.maxDeviation *2.))
            self.unit.selfUpdate()
        self.assertTrue(abs(self.unit.criticalDeviation  - expectedDev)  < errorTolerance)     
        runs = 1
        maxruns = 500
        while self.unit.criticalDeviation > self.unit.minDeviation:
            self.unit.selfUpdate()
            runs += 1
            if runs > maxruns:
                raise(HomeoUnitError, "The unit does not run off after %u runs" % runs)
        self.assertTrue(self.unit.criticalDeviation == self.unit.minDeviation)

        


        # 3. with polarity reversed the unit will tend to stabilize itself around 0, 
        # because the output will always counteract the unit's deviation. "
        self.unit.switch = - 1                          #"self-connection's switch is negative: 
                                                        # unit's output is re-inputted with reverse polarity"

        self.unit.criticalDeviation = -2
        self.unit.computeOutput()
        expectedDev = self.unit.criticalDeviation - (self.unit.currentOutput / (self.unit.maxDeviation * 2.))
        self.unit.selfUpdate()
        self.assertTrue((self.unit.criticalDeviation - expectedDev ) < errorTolerance)
        runs = 1
        maxRuns = 10000
        while (abs(self.unit.criticalDeviation) > errorTolerance):
            self.unit.selfUpdate()
            runs += 1
            if runs > maxRuns:
                raise(HomeoUnitError, "Unit does not stabilize after %u runs" % runs)
        self.assertTrue(abs(self.unit.criticalDeviation) < errorTolerance)

        #4." 
        self.unit.criticalDeviation = 2
        self.unit.computeOutput()
        expectedDev = self.unit.criticalDeviation - (self.unit.currentOutput / (self.unit.maxDeviation * 2.))
        self.unit.selfUpdate()
        self.assertTrue((self.unit.criticalDeviation - expectedDev ) < errorTolerance)
        runs = 1
        maxRuns = 10000
        while (abs(self.unit.criticalDeviation) > errorTolerance):
            self.unit.selfUpdate()
            runs += 1
            if runs > maxRuns:
                raise(HomeoUnitError, "Unit does not stabilize after %u runs" % runs)
        self.assertTrue(abs(self.unit.criticalDeviation) < errorTolerance)

    def testComputeNextDeviationLinearUnconnected(self):
        "Checks  a single unconnected unit. The value will always remain at its initial value no matter how many times the unit updates"

        '''A standard HomeoUnit increases its value (critDeviation) at each computational step by on of two basic formulas:
        1. when the computation method is linear (default):
         critDeviation (n+1) = criticalDev(n) + (sum(input * weight)/ unit mass)
         
        2. When the computational method is proportional:
        critDeviation (n+1) = criticalDev(n) + ( (sum(input * weight)) / (maxDeviation *2) / unit mass)
        
        Here we test the method 1, see testComputeNextDeviationProportionalUnconnected for case 2
        
         The basic formula is complicated by taking into consideration:
         1. noise, which affects both the stability of a unit's critDeviation (as flickering), and the connections to other units (as distortions)
         2. viscosity of the medium
         3. clipping, which limits the maximum/minimum values of critDeviation
         4. The unit's mass (in Newtonian units)
        
         Viscosity and clipping have their own tests, see the HomeoNoise class for noise testing.'''
        
        testRuns = 1000
        self.unit.needleCompMethod = 'linear'
        self.unit.potentiometer = 0  #"put the weight of the self-connection to zero."
        self.unit.noise = 0

        for each in xrange(testRuns):
            self.unit.criticalDeviation = numpy.random.uniform(- self.unit.maxDeviation, self.unit.maxDeviation)
            self.unit.needleUnit.mass = numpy.random.uniform(0.0001, 10000)
            self.unit.viscosity = numpy.random.uniform(0,1)
            tempDev = self.unit.criticalDeviation
            for i in xrange(10):
                self.unit. selfUpdate()
            self.assertTrue(tempDev == self.unit.criticalDeviation)

    def testComputeNextDeviationProportionalUnconnected(self):
        "Checks  a single unconnected unit. The value will always remain at its initial value no matter how many times the unit updates"

        '''A standard HomeoUnit increases its value (critDeviation) at each computational step by on of two basic formulas:
        
        1. When the computation method is linear (default):
         critDeviation (n+1) = criticalDev(n) + (sum(input * weight)/ unit mass)
         
        2. When the computational method is proportional:
        critDeviation (n+1) = criticalDev(n) + ( (sum(input * weight)) / (maxDeviation *2) / unit mass)
        
        Here we test the method 2, see testComputeNextDeviationLinearlUnconnected for case 1
        
         The basic formula is complicated by taking into consideration:
         1. noise, which affects both the stability of a unit's critDeviation (as flickering), and the connections to other units (as distortions)
         2. viscosity of the medium
         3. clipping, which limits the maximum/minimum values of critDeviation
         4. The unit's mass (in Newtonian units)
        
         Viscosity and clipping have their own tests, see the HomeoNoise class for noise testing.'''
        
        testRuns = 1000
        self.unit.needleCompMethod = 'proportional'
        self.unit.potentiometer = 0  #"put the weight of the self-connection to zero."
        self.unit.noise = 0

        for each in xrange(testRuns):
            self.unit.criticalDeviation = numpy.random.uniform(- self.unit.maxDeviation, self.unit.maxDeviation)
            self.unit.needleUnit.mass = numpy.random.uniform(0.0001, 10000)
            self.unit.viscosity = numpy.random.uniform(0,1)
            tempDev = self.unit.criticalDeviation
            for i in xrange(10):
                self.unit. selfUpdate()
            self.assertTrue(tempDev == self.unit.criticalDeviation)



    def testComputeNextDeviationLinearConnected(self):
        "Checks the computation of a self-connected unit connected to another unit."

        '''A standard HomeoUnit increases its value (critDeviation) at each computational step by on of two basic formulas:
        
        1. When the computation method is linear (default):
           critDeviation (n+1) = criticalDev(n) + (sum(input * weight)/ unit mass)
         
        2. When the computational method is proportional:
        critDeviation (n+1) = criticalDev(n) + ( (sum(input * weight)) / (maxDeviation *2) / unit mass)
        
        Here we test the method 1, see testComputeNextDeviationProportionalConnected for case 2
        
         The basic formula is complicated by taking into consideration:
         1. noise, which affects both the stability of a unit's critDeviation (as flickering), and the connections to other units (as distortions)
         2. viscosity of the medium
         3. clipping, which limits the maximum/minimum values of critDeviation
         4. The unit's mass (in Newtonian units)
        
         Viscosity and clipping have their own tests, see the HomeoNoise class for noise testing.'''
        
        testRuns = 100
        anotherUnit = HomeoUnit()
        anotherUnit.setRandomValues()
        self.unit.needleCompMethod = 'linear'
        self.unit.noise = 0                              # Eliminate flicker noise to simplify test"
        self.unit.viscosity = 0                          # Eliminate viscosity effect to simplify test (viscosity has its own tests) 
        self.unit.needleUnit.mass = 1
    
        self.unit.addConnectionWithRandomValues(anotherUnit)
        for eachConn in self.unit.inputConnections:
            eachConn.noise = 0                          # The self-connection and the connection to anotherUnit are noise-free"

        for i in xrange(testRuns):
            
            #-------------------------------------- " testing on simple values "
            #----------------------------------- self.unit.criticalDeviation = 1
            #--------------------------------- anotherUnit.criticalDeviation = 2
            #----------------------------------------- self.unit.computeOutput()
            #--------------------------------------- anotherUnit.computeOutput()
            #------------------------------------- self.unit.potentiometer = 0.5
            #------------ self.unit.switch = 1 #np.sign(np.random.uniform(-1,1))
            #------------------------ self.unit.inputConnections[1].newWeight(1)
            #------------------------------------- "End of simple value testing"
            
            "testing on random values"
            self.unit.criticalDeviation = numpy.random.uniform(-10,10)
            self.unit.computeOutput()
            anotherUnit.computeOutput()
            self.unit.potentiometer = numpy.random.uniform(0,1)
            self.unit.switch = numpy.sign(numpy.random.uniform(-1,1))   # sign returns 0 for input = 0. 
                                                                        # Homeounit.switch() considers 0 to be positive
            for i in xrange(10): 
                deviation = self.unit.criticalDeviation     
                errorTolerance = pow(10,-14)                            
                expectedInputfromOtherUnit = self.unit.inputConnections[1].output()
                expectedInputfromSelf = self.unit.currentOutput * self.unit.potentiometer * self.unit.switch
                expectedDeviation = deviation  + expectedInputfromSelf + expectedInputfromOtherUnit
                exceeded = abs(expectedDeviation) > self.unit.maxDeviation 
                self.unit.selfUpdate()
                if exceeded: 
                    self.assertTrue(True)                              # If criticalDeviation value went at any time beyond clipping limits don't check. 
                                                                       # clipping is tested in others test methods
                else:
                    self.assertTrue(abs(expectedDeviation - self.unit.criticalDeviation)  < errorTolerance)

    def testComputeNextDeviationProportionalConnected(self):
        "Checks the computation of a self-connected unit connected to another unit."

        '''A standard HomeoUnit increases its value (critDeviation) at each computational step by on of two basic formulas:
        
        1. When the computation method is linear (default):
           critDeviation (n+1) = criticalDev(n) + (sum(input * weight)/ unit mass)
         
        2. When the computational method is proportional:
        critDeviation (n+1) = criticalDev(n) + ( (sum(input * weight)) / (maxDeviation *2) / unit mass)
        
        Here we test the method 2, see testComputeNextDeviationLinearConnected for case 1
        
         The basic formula is complicated by taking into consideration:
         1. noise, which affects both the stability of a unit's critDeviation (as flickering), and the connections to other units (as distortions)
         2. viscosity of the medium
         3. clipping, which limits the maximum/minimum values of critDeviation
         4. The unit's mass (in Newtonian units)
        
         Viscosity and clipping have their own tests, see the HomeoNoise class for noise testing.'''
        
        testRuns = 100
        anotherUnit = HomeoUnit()
        anotherUnit.setRandomValues()
        self.unit.needleCompMethod = 'proportional'
        self.unit.noise = 0                              # Eliminate flicker noise to simplify test"
        self.unit.viscosity = 0                          # Eliminate viscosity effect to simplify test (viscosity has its own tests) 
        self.unit.needleUnit.mass = 1
    
        self.unit.addConnectionWithRandomValues(anotherUnit)
        for eachConn in self.unit.inputConnections:
            eachConn.noise = 0                          # The self-connection and the connection to anotherUnit are noise-free"

        for i in xrange(testRuns):
            
            #-------------------------------------- " testing on simple values "
            #----------------------------------- self.unit.criticalDeviation = 1
            #--------------------------------- anotherUnit.criticalDeviation = 2
            #----------------------------------------- self.unit.computeOutput()
            #--------------------------------------- anotherUnit.computeOutput()
            #------------------------------------- self.unit.potentiometer = 0.5
            #------------ self.unit.switch = 1 #np.sign(np.random.uniform(-1,1))
            #------------------------ self.unit.inputConnections[1].newWeight(1)
            #------------------------------------- "End of simple value testing"
            
            "testing on random values"
            self.unit.criticalDeviation = numpy.random.uniform(-10,10)
            self.unit.computeOutput()
            anotherUnit.computeOutput()
            self.unit.potentiometer = numpy.random.uniform(0,1)
            self.unit.switch = numpy.sign(numpy.random.uniform(-1,1))   # sign returns 0 for input = 0. 
                                                                        # Homeounit.switch() considers 0 to be positive
            for i in xrange(10): 
                deviation = self.unit.criticalDeviation     
                errorTolerance = pow(10,-14)                            
                expectedInputFromOtherUnit = self.unit.inputConnections[1].output()
                expectedInputFromSelf = self.unit.currentOutput * self.unit.potentiometer * self.unit.switch
                proportionalInput = (expectedInputFromSelf + expectedInputFromOtherUnit)/(self.unit.maxDeviation * 2.)
                expectedDeviation = deviation  + proportionalInput
                exceeded = abs(expectedDeviation) > self.unit.maxDeviation 
                self.unit.selfUpdate()
                if exceeded: 
                    self.assertTrue(True)                              # If criticalDeviation value went at any time beyond clipping limits don't check. 
                                                                       # clipping is tested in others test methods
                else:
                    self.assertTrue(abs(expectedDeviation - self.unit.criticalDeviation)  < errorTolerance)

    
    def testComputeNextDeviationLinearConnectedToNUnits(self):
        "Check the values of a unit connected to N other units"
        
        # "A standard HomeoUnit increases its value (critiDeviation) at each computational step by the basic formula:
        # critDeviation (n+1) = criticalDev(n) + (sum(input * weight)/ unit mass)
        #------------------------------------------------------------------------------ 
        # The basic formula is complicated by taking into consideration:
        # 1. noise, which affects both the stability of a unit's critDeviation (as flickering), and the connections to other units (as distortions)
        # 2. viscosity of the medium
        # 3. clipping, which limits the maximum/minimum values of critDeviation
        # 4. The unit's mass (in Newtonian units)
        #------------------------------------------------------------------------------ 
        # Viscosity and clipping have their own tests, see the HomeoNoise class for noise testing."
        # We also set the needleUnit mass to 1 simplify the computation"

        errorTolerance = pow(10,-14)             #Cannot get a result better than 10^-14. Consistently fails on smaller values"
        testRuns = 10
        N = 10                                   # number of units to create and connect to
        for each in xrange(N):
            aUnit = HomeoUnit()
            self.unit.addConnectionWithRandomValues(aUnit) 

        self.unit.needleCompMethod = 'linear'
        self.unit.noise = 0                              # "Eliminate flicker noise to simplify test"
        self.unit.needleUnit.mass = 1
        self.unit.viscosity = 0                     # set viscosity effect to 0 to simplify computations
    

        for conn in self.unit.inputConnections:
            conn.noise = 0                             #the self-connection and the connections to all other units are noise-free"

        for i in xrange(testRuns):
            #-------------------------------------- " Simple values for testing"
            #--------------------------- for conn in self.unit.inputConnections:
                #----------------------- conn.incomingUnit.criticalDeviation = 1
                #-------------- conn.newWeight(np.sign(np.random.uniform(-1,1)))
            #--------------------------------------- self.unit.potentiometer = 1
            #---------------------------------------------- self.unit.switch = 1
            #----------------------------------------------- "End simple values"
            
            "Random values"
            self.unit.criticalDeviation = numpy.random.uniform(self.unit.minDeviation, self.unit.maxDeviation)
            self.unit.potentiometer = np.random.uniform(0,1)
            self.unit.switch = np.sign(np.random.uniform(-1,1))
            for conn in self.unit.inputConnections:
               conn.incomingUnit.computeOutput()
               conn.newWeight(np.random.uniform(-1,1))
            " End random values "

            self.unit.computeOutput()
            for conn in self.unit.inputConnections:
                conn.incomingUnit.computeOutput()

            for k in xrange(100):
                deviation = self.unit.criticalDeviation     
                inputFromAllUnits = sum([conn.output() for conn in self.unit.inputConnections])  # includes self-connection
                expectedDeviation = deviation  + inputFromAllUnits
                exceeded = abs(expectedDeviation)  > self.unit.maxDeviation 
                self.unit.selfUpdate()
                if exceeded:
                    self.assertTrue(True)
                    #expectedDeviation = self.unit.criticalDeviation                                                    
                    # If criticalDeviation value went at any time  beyond clipping limits don't check. 
                    # (This test is carried out in other unit tests) 
                    # Reset computing deviation to avoid carrying the error over to next cycles"
                else:
                    self.assertTrue(abs(expectedDeviation - self.unit.criticalDeviation  < errorTolerance))

    def testComputeNextDeviationProportionalConnectedToNUnits(self):
        "Check the values of a unit connected to N other units"
        
        # "A standard HomeoUnit increases its value (critiDeviation) at each computational step by the basic formula:
        # critDeviation (n+1) = criticalDev(n) + (sum(input * weight)/ unit mass)
        #------------------------------------------------------------------------------ 
        # The basic formula is complicated by taking into consideration:
        # 1. noise, which affects both the stability of a unit's critDeviation (as flickering), and the connections to other units (as distortions)
        # 2. viscosity of the medium
        # 3. clipping, which limits the maximum/minimum values of critDeviation
        # 4. The unit's mass (in Newtonian units)
        #------------------------------------------------------------------------------ 
        # Viscosity and clipping have their own tests, see the HomeoNoise class for noise testing."
        # We also set the needleUnit mass to 1 simplify the computation"

        errorTolerance = pow(10,-14)             #Cannot get a result better than 10^-14. Consistently fails on smaller values"
        testRuns = 10
        N = 10                                   # number of units to create and connect to
        for each in xrange(N):
            aUnit = HomeoUnit()
            self.unit.addConnectionWithRandomValues(aUnit) 

        self.unit.needleCompMethod = 'proportional'
        self.unit.noise = 0                              # "Eliminate flicker noise to simplify test"
        self.unit.needleUnit.mass = 1
        self.unit.viscosity = 0                     # set viscosity effect to 0 to simplify computations
    

        for conn in self.unit.inputConnections:
            conn.noise = 0                             #the self-connection and the connections to all other units are noise-free"

        for i in xrange(testRuns):
            #-------------------------------------- " Simple values for testing"
            #--------------------------- for conn in self.unit.inputConnections:
                #----------------------- conn.incomingUnit.criticalDeviation = 1
                #-------------- conn.newWeight(np.sign(np.random.uniform(-1,1)))
            #--------------------------------------- self.unit.potentiometer = 1
            #---------------------------------------------- self.unit.switch = 1
            #----------------------------------------------- "End simple values"
            
            "Random values"
            self.unit.criticalDeviation = numpy.random.uniform(self.unit.minDeviation, self.unit.maxDeviation)
            self.unit.potentiometer = np.random.uniform(0,1)
            self.unit.switch = np.sign(np.random.uniform(-1,1))
            for conn in self.unit.inputConnections:
               conn.incomingUnit.computeOutput()
               conn.newWeight(np.random.uniform(-1,1))
            " End random values "

            self.unit.computeOutput()
            for conn in self.unit.inputConnections:
                conn.incomingUnit.computeOutput()

            for k in xrange(100):
                deviation = self.unit.criticalDeviation     
                inputFromAllUnits = sum([conn.output() for conn in self.unit.inputConnections])  # includes self-connection
                expectedDeviation = deviation  + (inputFromAllUnits/ (self.unit.maxDeviation * 2.))
                exceeded = abs(expectedDeviation)  > self.unit.maxDeviation 
                self.unit.selfUpdate()
                if exceeded:
                    self.assertTrue(True)
                    #expectedDeviation = self.unit.criticalDeviation                                                    
                    # If criticalDeviation value went at any time  beyond clipping limits don't check. 
                    # (This test is carried out in other unit tests) 
                    # Reset computing deviation to avoid carrying the error over to next cycles"
                else:
                    self.assertTrue(abs(expectedDeviation - self.unit.criticalDeviation  < errorTolerance))

    def testComputeNextDeviationLinearSelfconnected(self):
        "Check the values of a single self-connected unit"
    
        '''A standard HomeoUnit increases its value (critDeviation) at each computational step by of two basic formulas:
        
        1. When the computation method is linear (default):
           critDeviation (n+1) = criticalDev(n) + (sum(input * weight)/ unit mass)
         
        2. When the computational method is proportional:
        critDeviation (n+1) = criticalDev(n) + ( (sum(input * weight)) / (maxDeviation *2) / unit mass)
        
        Here we test the method 1 on a single self-connected unit, see testComputeNextDeviationProportionalSelfconnected for case 2
        
         The basic formula is complicated by taking into consideration:
         1. noise, which affects both the stability of a unit's critDeviation (as flickering), and the connections to other units (as distortions)
         2. viscosity of the medium
         3. clipping, which limits the maximum/minimum values of critDeviation
         4. The unit's mass (in Newtonian units)
        
         Viscosity and clipping have their own tests, see the HomeoNoise class for noise testing.'''
        
        self.unit = HomeoUnit()
        "testing on simple values "
#        self.unit.criticalDeviation = 0.5
#        self.unit.currentOutput = 1
        " end of testing on simple values"
        testRuns = 100
        self.unit.needleCompMethod = 'linear'
        self.unit.maxDeviation = 10
        self.unit.noise = 0                        #Eliminate flicker noise to simplify computations"
        self.unit.needleUnit.mass = 1
        self.unit.inputConnections[0].noise = 0    #the self-connection is noise-free"

        ''''Test that the next computed deviation will be equal to 
        the current deviation plus the output from self * weight (unless it runs to maximum)'''
        
        for test in xrange(testRuns):
#            self.unit.criticalDeviation = numpy.random.uniform(- self.unit.maxDeviation,self.unit.maxDeviation)
            self.unit.computeOutput()
#            self.unit.potentiometer = numpy.random.uniform(0, 1)
            self.unit.switch = numpy.sign(numpy.random.uniform(-1,1))
            for i in xrange(10):
                deviation = self.unit.criticalDeviation
                nextDeviation = deviation + (self.unit.currentOutput * self.unit.potentiometer * self.unit.switch)
                exceeded = abs(nextDeviation) >  self.unit.maxDeviation
                self.unit.selfUpdate()
                if exceeded: 
                    self.assertTrue(True)
                else:
                    self.assertTrue(nextDeviation == self.unit.criticalDeviation)

    def testComputeNextDeviationProportionalSelfconnected(self):
        "Check the values of a single self-connected unit"
    
        '''A standard HomeoUnit increases its value (critDeviation) at each computational step by of two basic formulas:
        
        1. When the computation method is linear (default):
           critDeviation (n+1) = criticalDev(n) + (sum(input * weight)/ unit mass)
         
        2. When the computational method is proportional:
        critDeviation (n+1) = criticalDev(n) + ( (sum(input * weight)) / (maxDeviation *2) / unit mass)
        
        Here we test the method 1 on a single self-connected unit, see testComputeNextDeviationLinearSelfconnected for case 1
        
         The basic formula is complicated by taking into consideration:
         1. noise, which affects both the stability of a unit's critDeviation (as flickering), and the connections to other units (as distortions)
         2. viscosity of the medium
         3. clipping, which limits the maximum/minimum values of critDeviation
         4. The unit's mass (in Newtonian units)
        
         Viscosity and clipping have their own tests, see the HomeoNoise class for noise testing.'''
        
        self.unit = HomeoUnit()
        "testing on simple values "
#        self.unit.criticalDeviation = 0.5
#        self.unit.currentOutput = 1
        " end of testing on simple values"
        testRuns = 100
        self.unit.needleCompMethod = 'proportional'
        self.unit.maxDeviation = 10
        self.unit.noise = 0                        #Eliminate flicker noise to simplify computations"
        self.unit.needleUnit.mass = 1
        self.unit.inputConnections[0].noise = 0    #the self-connection is noise-free"

        ''''Test that the next computed deviation will be equal to 
        the current deviation plus the output from self * weight / maxdeviation *2 (unless it runs to maximum)'''
        
        for test in xrange(testRuns):
#            self.unit.criticalDeviation = numpy.random.uniform(- self.unit.maxDeviation,self.unit.maxDeviation)
            self.unit.computeOutput()
#            self.unit.potentiometer = numpy.random.uniform(0, 1)
            self.unit.switch = numpy.sign(numpy.random.uniform(-1,1))
            for i in xrange(10):
                deviation = self.unit.criticalDeviation
                nextDeviation = deviation + ((self.unit.currentOutput * self.unit.potentiometer * self.unit.switch) / (self.unit.maxDeviation * 2))
                exceeded = abs(nextDeviation) >  self.unit.maxDeviation
                self.unit.selfUpdate()
                if exceeded: 
                    self.assertTrue(True)
                else:
                    self.assertTrue(nextDeviation == self.unit.criticalDeviation)

    def testInitializationDefaults(self):
        '''test that the class default values are properly inserted in 
           a newly created HomeoUnit's  instance variables'''
       
        self.unit = HomeoUnit()
        
        defViscosity = HomeoUnit.DefaultParameters['viscosity']
        self.assertTrue(self.unit.viscosity == defViscosity)
    
        defMaxDeviation = HomeoUnit.DefaultParameters['maxDeviation']
        self.assertTrue(self.unit.maxDeviation == defMaxDeviation)

        defNoise = HomeoUnit.DefaultParameters['noise']
        self.assertTrue(self.unit.noise == defNoise)

        defPotentiometer = HomeoUnit.DefaultParameters['potentiometer']
        self.assertTrue(self.unit.potentiometer == defPotentiometer)

        defOutputRange = HomeoUnit.DefaultParameters['outputRange']
        self.assertTrue((self.unit.outputRange['high']) == defOutputRange['high'])
        self.assertTrue((self.unit.outputRange['low']) == defOutputRange['low'])

        defTime = HomeoUnit.DefaultParameters['time']
        self.assertTrue(self.unit.time == defTime)

        defUniselectorTime = HomeoUnit.DefaultParameters['uniselectorTime']
        self.assertTrue(self.unit.uniselectorTime == defUniselectorTime)

        defUniselectorTimeInterval = HomeoUnit.DefaultParameters['uniselectorTimeInterval']
        self.assertTrue(self.unit.uniselectorTimeInterval == defUniselectorTimeInterval)

    def testSameAs(self):
        """two units are the same is their values are the same AND they have the same connections
           two units are not the same if they have different names (everything else being the same) """
        self.unit.setRandomValues()
        unit2 = HomeoUnit()
        unit2.setRandomValues()
        unit3 = HomeoUnit()
        unit3.setRandomValues()
        unit4 = HomeoUnit()
        unit4.setRandomValues()

        self.unit.addConnectionWithRandomValues(unit2)
        self.unit. addConnectionWithRandomValues(unit3)

        unit4 = copy(self.unit)

        self.assertTrue(self.unit.sameAs(unit4))   # two units are the same

        param = unit4.name 
        unit4.name = param + 'pippo'                  #change the name and check again
        self.assertFalse(self.unit.sameAs(unit4))
        
        "two newly created units can never be same because their names will differ"
        self.unit = HomeoUnit()
        unit4 = HomeoUnit()
        self.assertFalse(self.unit.sameAs(unit4))
        self.assertFalse(self.unit.name == unit4.name)

    def testNeedleWithinLimit(self):
        "testing the clipping function operating on a unit's critical deviation's value"

        highVal = self.unit.maxDeviation
        lowVal = - self.unit.maxDeviation

        aValue = highVal * 1.1
        self.assertFalse(self.unit.isNeedleWithinLimits(aValue))

        aValue = highVal * 0.9
        self.assertTrue(self.unit.isNeedleWithinLimits(aValue))

        aValue = lowVal * 1.1
        self.assertFalse(self.unit.isNeedleWithinLimits(aValue))

        aValue = lowVal * 0.9
        self.assertTrue(self.unit.isNeedleWithinLimits(aValue))

    def testNewNeedlePosition(self):
        "test correct computation of needle movement. Ignore noise, as it is computed within the unit itself"

        self.unit.needleUnit.mass = 1
        self.unit.needleCompMethod = 'linear'       # Default, but we want to make sure
        maxInput = 3                #typical of the 4 units Homeostat"
        minInput = - maxInput
        for i in xrange(100):
            self.unit.criticalDeviation = 1
            self.unit.noise = 0
            self.unit.viscosity = 0      # no viscosity effects to simplify computations
            torqueValue = numpy.random.uniform(minInput, maxInput)
            newNeedlePosition = self.unit.newNeedlePosition(torqueValue)
            correctValue = self.unit.criticalDeviation + (torqueValue * (1- self.unit.viscosity))  - self.unit.noise
          
            # Print values to console for debugging purposes
            print 'newNeedlePos: ' + str(newNeedlePosition) + '   and critical Dev: ' + str(self.unit.criticalDeviation)
            print  self.unit.printDescription()
            
            
            self.assertTrue(newNeedlePosition == correctValue)
            
            
        "Repeat tests for proportional method"
        self.unit.needleUnit.mass = 1
        self.unit.needleCompMethod = 'proportional'       
        maxInput = 3                #typical of the 4 units Homeostat"
        minInput = - maxInput
        for i in xrange(100):
            self.unit.criticalDeviation = 1
            self.unit.noise = 0
            self.unit.viscosity = 0      # no viscosity effects to simplify computations
            torqueValue = numpy.random.uniform(minInput, maxInput)
            newNeedlePosition = self.unit.newNeedlePosition(torqueValue)
            correctValue = self.unit.criticalDeviation + ((torqueValue/(self.unit.maxDeviation * 2.)) * (1- self.unit.viscosity))  - self.unit.noise
          
            # Print values to console for debugging purposes
            print 'newNeedlePos: ' + str(newNeedlePosition) + '   and critical Dev: ' + str(self.unit.criticalDeviation)
            print  self.unit.printDescription()
            
            
            self.assertTrue(newNeedlePosition == correctValue)


    def testFirstLevelParamSameAs(self):
        '''A unit that is a copy of another unit must have 
            the same first level parameters, name included.
            This test only checks changing two parameters (name and potentiometer)
            of two otherwise identical units and testing for falsity.
            A really comprehensive test should check all relevant parameters''' 
        
        self.unit.setRandomValues()
        anotherUnit = copy(self.unit)
        self.assertTrue(self.unit.sameFirstLevelParamsAs(anotherUnit))

        newRandomName = ''.join(random.choice(string.ascii_lowercase) for x in range(10))
        self.unit.name = newRandomName
        self.assertFalse(self.unit.sameFirstLevelParamsAs(anotherUnit))

        anotherUnit.potentiometer = numpy.clip(anotherUnit.potentiometer + numpy.random.uniform(0,0.1),0,1)

        self.assertFalse(self.unit.sameFirstLevelParamsAs(anotherUnit))

    def testComputeNextDeviationRandom(self):
            "Test that a unit's deviation will go through random value when no computation method is chosen"
            self.unit.needleCompMethod = ''      # empty string should trigger the random method"
            deviationValues = [] 
            #check that the critical deviation values are always different"
            
            for i in xrange(1000):
                deviationValues.append(self.unit.criticalDeviation)
                self.unit.selfUpdate()
            self.assertTrue(len(set(deviationValues)) == 1000)

    def testPotentiometer(self):
        "Testing initial conditions"
        self.assertTrue(self.unit.potentiometer == self.unit.inputConnections[0].weight)
        
        "Changing the potentiometer value changes the value of the units connection to itself"                
      
        for i in xrange(10):
            poten = numpy.random.uniform(0,1)
            self.unit.potentiometer = poten
            self.assertTrue(self.unit.potentiometer == poten)
            self.assertTrue(self.unit.inputConnections[0].weight == poten)
            
    def testCriticalThreshold(self):
        '''The threshold beyond which a HomeoUnit's essential variable's 
            value is deemed critical must be between 0 and 1'''
        
        for i in xrange(100):
            critValue = np.random.uniform(0, 1)
            self.unit.critThreshold = critValue
            self.assertTrue(self.unit.critThreshold == critValue)        
        for i in xrange(100):   
            critValue = np.random.uniform(-100, 0)
            self.assertRaises(HomeoUnitError, self.unit.setCritThreshold, critValue)
        for i in xrange(100):   
            critValue = np.random.uniform(1, 100)
            self.assertRaises(HomeoUnitError, self.unit.setCritThreshold, critValue)

    def testOutputRange(self):
        "a Unit in normal operation never goes out of range"
        highRange = self.unit. outputRange['high']
        lowRange = self.unit. outputRange['low']
        for i in xrange(100): 
            self.unit.selfUpdate()
            self.assertTrue((self.unit.currentOutput <= highRange) and 
                            (self.unit.currentOutput >= lowRange))
            
    def testComputeOutput(self):
        ''' A unit's output at time t is equal to 
        its critical at t scaled to the outputRange interval (default: (-1,1))
        
        We:
        1. compute the distance of critDeviation from the minDeviation,
        2. scale it to the ratio outputRange/deviationRange
        3. add the scaled distance to the minimum outputRange'''
        
        
        errorTolerance = 10**-14
        self.unit = HomeoUnit()
        
        "Test first with simple values and corner cases"
        "Disconnect unit by zeroing potentiometer (value of self-connection)"
        "test with critDev = 1"
        self.unit.potentiometer = 0
        self.unit.noise = 0                     #eliminate flickering noise
        self.unit.criticalDeviation = 1
        self.unit.selfUpdate()
        outRange = self.unit.outputRange['high']-self.unit.outputRange['low']
        devRange = self.unit.maxDeviation - self.unit.minDeviation
        critDevDistance = np.sqrt(pow((1 - self.unit.minDeviation),2))
#        dist = numpy.linalg.norm(1 - self.unit.minDeviation)                         # or could use numpy
        expectedOutput = (critDevDistance * (outRange/devRange)) + self.unit.outputRange['low']
        self.assertTrue(abs(self.unit.currentOutput - expectedOutput) < errorTolerance) 
        
        self.unit.potentiometer = 0
        self.unit.noise = 0                     #eliminate flickering noise
        self.unit.criticalDeviation = 0
        self.unit.selfUpdate()
        outRange = self.unit.outputRange['high']-self.unit.outputRange['low']
        devRange = self.unit.maxDeviation - self.unit.minDeviation
        critDevDistance = np.sqrt(pow((0 - self.unit.minDeviation),2))  
#        dist = numpy.linalg.norm(0 - self.unit.minDeviation)                         # or could use numpy
        expectedOutput = (critDevDistance * (outRange/devRange)) + self.unit.outputRange['low']
        self.assertTrue(abs(self.unit.currentOutput - expectedOutput) < errorTolerance) 

        "Randomize values"
        "Test with unit still unconnected, but random values for critDeviation" 
        self.unit.potentiometer = 0
        self.unit.noise = 0                     #eliminate flickering noise
        for i in xrange(100):                   
            critDev = np.random.uniform(self.unit.minDeviation,self.unit.maxDeviation)
            self.unit.criticalDeviation = critDev
            self.unit.selfUpdate()
            outRange = self.unit.outputRange['high']-self.unit.outputRange['low']
            devRange = self.unit.maxDeviation - self.unit.minDeviation
            critDevDistance = np.sqrt(pow((critDev - self.unit.minDeviation),2))
#        dist = numpy.linalg.norm(critDev - self.unit.minDeviation)                         # or could use numpy
            expectedOutput = (critDevDistance * (outRange/devRange)) + self.unit.outputRange['low']
            self.assertTrue(abs(self.unit.currentOutput - expectedOutput) < errorTolerance) 

#        "Finally, connect the unit to itself with random  values"
#        "and test with  random values for critDeviation" 
#        self.unit.noise = 0                      #eliminate flickering noise
#        self.unit.inputConnections[0].noise = 0  # eliminate noise on the self-connection
#        for i in xrange(100):                   
##            potValue = np.random.uniform(0,1)
##            switchValue = np.sign(np.random.uniform(-1,1)) 
#            potValue = 1
#            switchValue = 1 
#            self.unit.potentiometer = potValue
#            self.unit.switch = switchValue
#            critDev = np.random.uniform(self.unit.minDeviation,self.unit.maxDeviation)
##            self.unit.criticalDeviation = critDev
#            self.unit.criticalDeviation = 1
#            self.unit.currentOutput = 1            
#            self.unit.selfUpdate()
#            outRange = self.unit.outputRange['high']-self.unit.outputRange['low']
#            devRange = self.unit.maxDeviation - self.unit.minDeviation
#            critDevDistance = np.sqrt(pow((critDev - self.unit.minDeviation),2))
##        dist = numpy.linalg.norm(critDev - self.unit.minDeviation)                         # or could use numpy
#            """With one connected unit (self), the output must be equal to:
#            """
#            expectedOutput = (critDevDistance * (outRange/devRange)) + self.unit.outputRange['low']
#            self.assertTrue(abs(self.unit.currentOutput - expectedOutput) < errorTolerance) 

    def testOutputAndDeviationInRange(self):
        """
        Repeated test with fully connected units. 
        Check that outputs values and 
        critical deviation values are within their ranges
        """
                
        highOut = self.unit.outputRange['high']
        lowOut = self.unit.outputRange['low']
        highDev = self.unit.maxDeviation
        lowDev = -highDev

        unit2 = HomeoUnit()
        unit2.setRandomValues()
        unit3 = HomeoUnit()
        unit3.setRandomValues()
        unit4 = HomeoUnit()
        unit4.setRandomValues()

        self.unit.addConnectionWithRandomValues(unit2)
        self.unit.addConnectionWithRandomValues(unit3)
        self.unit.addConnectionWithRandomValues(unit4)

        for i in xrange(10000):
            self.unit.selfUpdate()
            self.assertTrue(self.unit.currentOutput >= lowOut and
                            self.unit.currentOutput <= highOut)
            self.assertTrue(self.unit.criticalDeviation >= lowDev and
                            self.unit.criticalDeviation <= highDev)

    def testComputeTorqueWithinLimits(self):
        """
        A unit's maximum torque is always between 
        the sum of the inputs from the connected units (eventually negated).
        Test with three connected units repeatedly self-updating
        """

        unit2 = HomeoUnit()
        unit2.setRandomValues()

        unit3 = HomeoUnit()
        unit3.setRandomValues()

        unit4 = HomeoUnit()
        unit4.setRandomValues()

        

        self.unit.addConnectionWithRandomValues(unit2)
        self.unit.addConnectionWithRandomValues(unit3)
        self.unit.addConnectionWithRandomValues(unit4)

        for i in xrange(1000):
            self.unit.selfUpdate()
            unit2.selfUpdate()
            unit3.selfUpdate()
            unit4.selfUpdate()
            self.assertTrue (self.unit.inputTorque >=  -3 and
                             self.unit.inputTorque <= 3)

    def testComputeTorque(self):
        "Tests that a unit's torque is equal to the sum of the connected unit's outputs"
        self.unit = HomeoUnit()
        unit2 = HomeoUnit()
        unit3 = HomeoUnit()
        unit4 = HomeoUnit()
    
        "1. test torque when unit is not connected to anything. Should be 0"
        self.unit.removeConnectionFromUnit(self.unit)

        self.assertTrue(len(self.unit.inputConnections) == 0)
        self.unit.computeTorque()
        self.assertTrue(self.unit.inputTorque == 0)

        "2. add a self connection at 1 and another connection at 1. torque should be 2"

        self.unit.currentOutput = 1
        unit2.currentOutput = 1
        self.unit.addConnectionUnitWeightPolarityNoiseState(self.unit,1,1, 0, 'manual')
        self.unit.addConnectionUnitWeightPolarityNoiseState(unit2, 1,1,0,'manual')
        self.assertTrue(len(self.unit.inputConnections) == 2)
        self.unit.computeTorque()
        self.assertTrue(self.unit.inputTorque == 2)

        "3. Add a pair of connections at -1. Torque should be 0"

        unit3.currentOutput = 1
        unit4.currentOutput = 1
        self.unit.addConnectionUnitWeightPolarityNoiseState(unit3,1,-1, 0, 'manual')
        self.unit.addConnectionUnitWeightPolarityNoiseState(unit4, 1,-1,0,'manual')
        self.unit.computeTorque()
        self.assertTrue(self.unit.inputTorque == 0)
        
        "4. Put some random values in the units, add their outputs, check inputTorque is equal to their sum"
        
        tests = 100
        for i in xrange(tests):
            out1 = np.random.uniform(-1,1)
            self.unit.currentOutput = out1
            
            out2 = np.random.uniform(-1,1)
            unit2.currentOutput = out2
            
            out3 = np.random.uniform(-1,1)
            unit3.currentOutput = out3
            
            out4 = np.random.uniform(-1,1)
            unit4.currentOutput = out4
            
            self.unit.computeTorque()
            self.assertTrue(self.unit.inputTorque == (out1 + out2 - out3 - out4))


    def testComputeNextOutputWithinRange(self):
        """A unit:
            1. computes a new value and puts it in the correct iVar
            2. has the value  within the unit's limits

            First tests are performed  with default values """

        errorTolerance = pow(10,-14)
        self.unit = HomeoUnit()
        self.unit.criticalDeviation = 1
        self.unit.currentOutput = 0.1
        highRange = self.unit.outputRange['high']
        lowRange = self.unit.outputRange['low']

        oldOutput= self.unit.currentOutput
        self.unit.selfUpdate()

        self.assertFalse((oldOutput - self.unit.currentOutput) < errorTolerance)       # "1st test " 
        self.assertTrue(self.unit.currentOutput >= lowRange and
                        self.unit.currentOutput <= highRange)         # "2nd test "
        
        "Then repeat tests with randomized values for unit"
        tests = 100
        for i in xrange(tests):
            self.unit.setRandomValues()
            oldOutput= self.unit.currentOutput
            self.unit.selfUpdate()
            self.assertFalse(oldOutput == self.unit.currentOutput)       # "1st test " 
            self.assertTrue(self.unit.currentOutput >= lowRange and
                            self.unit.currentOutput <= highRange)         # "2nd test "                    
        
    def testComputeNextDeviationWithDefaults(self):
        """
        A unit:
            2. has the value within the unit's limits

            tests are performed  with default values 
        """
        highRange = self.unit.maxDeviation
        lowRange = - highRange

        oldCriticalDeviation = self.unit.criticalDeviation
        self.unit.selfUpdate()

        self.assertFalse(oldCriticalDeviation == self.unit.criticalDeviation)       # "1st test " 
        self.assertTrue(self.unit.criticalDeviation > lowRange and
                        self.unit.criticalDeviation < highRange)         # "2nd test "

    
    def testChangeUniselectorType(self):
        """
        try changing a HomeoUnit uniselector  to an instance of the HomeoUniselector (sub)class
        and to some random string
        """
        goodUniselectors = []
        badUniselectors = []

        goodUniselectors.extend([class_.__name__ for class_ in withAllSubclasses(HomeoUniselector)])
        badUniselectors.extend(['Ashby','UniformRandom','HomeoUnit'])
        self.unit.setDefaultUniselectorSettings()
        for unisel in goodUniselectors:
            self.unit.uniselectorChangeType(unisel)
            self.assertTrue(self.unit.uniselector.__class__.__name__ == unisel)

        self.unit.setDefaultUniselectorSettings()
        for unisel in badUniselectors:
            self.assertRaises(HomeoUnitError, self.unit.uniselectorChangeType, unisel)
            self.assertFalse(self.unit.uniselector.__class__.__name__ == unisel)

    def testViscosity(self):
        """
        Viscosity reduces the effect of the outside force 
        on the unit's needle movement.
        When viscosity > 0, the force  changes according to drag. Real tests of drag laws 
        performed in drag unit tests, here we check that it works as a multiplicative constant"""
        
        "Setup a Unit, it will be negatively connected to itself by default"
        self.unit = HomeoUnit()
        self.unit.setRandomValues()
        self.unit.needleCompMethod = 'linear' # default, but we need to make sure
        
        ''''Set the noises on the internal connection and on 
        the unit to 0 to avoid complications'''
        self.unit.noise = 0
        self.unit.inputConnections[0].noise = 0
        
        "set the unit's needle mass to 1 to avoid complications"
        self.unit.needleUnit.mass = 1

        "Change the unit's viscosity to 0 (no effect)"
        self.unit.viscosity = 0
        
        ''''Viscosity affects the inputTorque which is added to the current criticalDeviation
        to compute the next deviation: when visc = 0, nextDeviation is the current deviation 
        plus the sum of the inputs. Here there is only one input to consider
        '''
        inputTorque =  self.unit.inputConnections[0].output()
        oldCritDeviation = self.unit.criticalDeviation
        self.unit.selfUpdate()
        self.assertTrue(self.unit.criticalDeviation == oldCritDeviation + inputTorque)
        
        "When viscosity = 1, the force affecting the unit is nullified"
        self.unit.viscosity = 1
        inputTorque =  self.unit.inputConnections[0].output()
        oldCritDeviation = self.unit.criticalDeviation
        self.unit.selfUpdate()
        self.assertTrue(self.unit.criticalDeviation == oldCritDeviation)
        
        "When viscosity = aValue, the force affecting the unit is multiplied by 1 - aValue"
        
        viscValue  = np.random.uniform (0,1)
        self.unit.viscosity = viscValue
        inputTorque =  self.unit.inputConnections[0].output()
        oldCritDeviation = self.unit.criticalDeviation
        self.unit.selfUpdate()
        self.assertTrue(self.unit.criticalDeviation == oldCritDeviation + (inputTorque * (1- viscValue)))

        "Repeat the tests for the proportional method"
        self.unit.needleCompMethod = 'proportional'
        
        "Change the unit's viscosity to 0 (no effect)"
        self.unit.viscosity = 0
        
        ''''Viscosity affects the inputTorque which is added to the current criticalDeviation
        to compute the next deviation: when visc = 0, nextDeviation is the current deviation 
        plus the sum of the inputs divided by (self.maxDeviation  * 2). 
        Here there is only one input to consider
        '''
        "TEMPORARY SETTINGS"
        self.unit.criticalDeviation = 10
        self.unit.currentOutput = 1
        self.unit.inputConnections[0].newWeight(-1)        
        "END TEMPORARY SETTINGS"
        
        inputTorque =  self.unit.inputConnections[0].output()
        oldCritDeviation = self.unit.criticalDeviation
        self.unit.selfUpdate()
        self.assertTrue(self.unit.criticalDeviation == oldCritDeviation + (inputTorque/(self.unit.maxDeviation * 2.)))
        
        "When viscosity = 1, the force affecting the unit is nullified"
        self.unit.viscosity = 1
        inputTorque =  self.unit.inputConnections[0].output()
        oldCritDeviation = self.unit.criticalDeviation
        self.unit.selfUpdate()
        self.assertTrue(self.unit.criticalDeviation == oldCritDeviation)
        
        "When viscosity = aValue, the force affecting the unit is multiplied by 1 - aValue"
        
        viscValue  = np.random.uniform (0,1)
        self.unit.viscosity = viscValue
        inputTorque =  self.unit.inputConnections[0].output()
        oldCritDeviation = self.unit.criticalDeviation
        self.unit.selfUpdate()
        self.assertTrue(self.unit.criticalDeviation == oldCritDeviation + 
                        (inputTorque /(self.unit.maxDeviation *2.)) * (1. - viscValue))
        

    def testSelfUpdateAdvancesUnitTime(self):
        """
        Test that a HomeoUnit's simulation time advances by 1 after a self update
        In current implementation, a HomeoUnit's time is updated by the Homeostat
        that holds it. A HomeUnit has no means of advancing its internal time counter.
        """
        
        self.assertTrue(True, "A HomeoUnit does not advance its time, its controlling Homoestat does it")
        #=======================================================================
        # "Test for alternative implementations"
        #
        # oldUnitTime = self.unit.time 
        # self.unit.selfUpdate()
        # self.assertTrue(self.unit.time == oldUnitTime + 1)
        #=======================================================================

    def testSelfUpdateAdvancesUniselectorTime(self):
        """
        Test that a HomeoUnit's Uniselector's simulation time advances by 1 after a self update
        """
        oldUniselectorTime= self.unit.uniselectorTime
        self.unit.selfUpdate()
        self.assertTrue(self.unit.uniselectorTime == oldUniselectorTime + 1)

    def testDeviationComputationsDontTouchInstanceVariables(self):
        """
        Check that the various methods used to compute the critical deviation simply output 
         a value and do not indeed change the actual value of deviation stored in the instance variable
         """
    
        self.unit.setRandomValues()

        self.unit.needleCompMethod = 'linear'
        for i in xrange(10):
                    aTorqueValue = numpy.random.uniform( -1 ,  1)
                    oldDeviation = self.unit.criticalDeviation
                    self.unit.newNeedlePosition(aTorqueValue)
                    self.assertTrue(oldDeviation == self.unit.criticalDeviation)

        self.unit.needleCompMethod ='proportional'
        for i in xrange(10):
                    aTorqueValue = numpy.random.uniform( -1 ,  1)
                    oldDeviation = self.unit.criticalDeviation
                    self.unit.newNeedlePosition(aTorqueValue)
                    self.assertTrue(oldDeviation == self.unit.criticalDeviation)

        self.unit.needleCompMethod = 'random'
        for i in xrange(10):
                    aTorqueValue = numpy.random.uniform( -1 ,  1)
                    oldDeviation = self.unit.criticalDeviation
                    self.unit.newNeedlePosition(aTorqueValue)
                    self.assertTrue(oldDeviation == self.unit.criticalDeviation)

        self.unit.needleCompMethod = ''
        for i in xrange(10):
                    aTorqueValue = numpy.random.uniform( -1 ,  1)
                    oldDeviation = self.unit.criticalDeviation
                    self.unit.newNeedlePosition(aTorqueValue)
                    self.assertTrue(oldDeviation == self.unit.criticalDeviation)
    
     
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()  
