from   HomeoUnit import *
from   HomeoUniselector import *
from   Homeostat import *
from   Helpers.General_Helper_Functions import *

import unittest, numpy, string, random


class HomeoUnitTest(unittest.TestCase):
    """Unit testing for the HomeoUnit class and subclasses, including adding and removing connections to other HomeoUnits."""
    
    def setUp(self):
        """Set up a Homeounit for all tests in the suite"""
        self.unit = HomeoUnit()
        
    def tearDown(self):
        pass
       
    def testAddConnection(self):
        """Connect to another unit and test the connection values."""
        newUnit = HomeoUnit()
        weight = 0.5
        polarity = 1
        state = 'manual'
        self.unit.addConnection(newUnit, weight, polarity, state)
        self.assertTrue(self.unit.inputConnections is not None)
        self.assertTrue(self.unit.inputConnections.last.incomingUnit == newUnit)
        self.assertTrue(self.unit.inputConnections.last.weight == weight)
        self.assertTrue(self.unit.inputConnections.last.switch == polarity)
        self.assertTrue(self.unit.inputConnections.last.state == 'manual')

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

        self.assertTrue(defParam['viscosity'] is not None)
        self.assertTrue(defParam['maxDeviation'] is not None)
        self.assertTrue(defParam['noise'] is not None)
        self.assertTrue(defParam['potentiometer'] is not None)
        self.assertTrue(defParam['time'] is not None)
        self.assertTrue(defParam['uniselectorTimeInterval'] is not None)
        self.assertTrue(defParam['uniselectorTime'] is not None)
        self.assertTrue(defParam['needleCompMethod']  is not None)
        self.assertTrue(defParam['outputRange'] is not None)

        outputRange = defParam['outputRange']

        self.assertTrue(outputRange.has_key('high'))
        self.assertTrue(outputRange['high'] is not None)

        self.assertTrue(outputRange.has_key('low'))
        self.assertTrue(outputRange['low'] is not None)
        
    def testSaveToFileAndBack(self):
        "test that the unit can be saved to file and recovered"
        self.unit.saveTo('pippo.unit')
        newUnit = HomeoUnit.readFrom('pippo.unit')
        self.assertTrue(isinstance(newUnit, HomeoUnit))
        self.assertTrue(self.unit.sameAs(newUnit))

    def testIsConnectedTo(self):
        newUnit=HomeoUnit()
        weight = 0.5
        polarity = 1

        self.assertFalse(self.unit.isConnectedTo(newUnit))
        self.unit.addConnection(newUnit,weight,polarity,'manual')
        self.assertTrue(self.unit.isConnectedTo(newUnit))
        
    def testRandomizeValues(self):
        self.unit.setRandomValues()
        oldOutput = self.unit.currentOutput()
        self.unit.setRandomValues()
        self.assertFalse(oldOutput == self.unit.currentOutput)
            
    def testRemoveConnection(self):
        newUnit = HomeoUnit()
        weight = 0.5
        polarity = 1

        self.unit.addConnection(newUnit,weight,polarity,'manual')
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
        self.unitsNames = ()
        for i in xrange(100):
            newUnit = HomeoUnit()
            self.unitNames.append(newUnit.name())
        self.assertTrue(len(self.unitNames) == len(set(self.unitNames)))
                
    def testApplicationInternalNoise(self):
        "Check that in presence of noise the unit's critical deviation is changed  and not changed when noise = 0."
        # FIXIT A more comprehensive test could p/h check that the noise value applied is uniformly distributing, proportional, and distorting."

        self.unit.setRandomValues()
        self.unit.noise(0.1)
        for i in xrange(1,10):
            oldDeviation = self.unit.criticalDeviation
            self.unit.updateDeviationWithNoise()
            self.assertFalse(oldDeviation == self.unit.criticalDeviation)

        self.unit.noise(0)
        for i in xrange(1,10):
            oldDeviation = self.unit.criticalDeviation
            self.unit.updateDeviationWithNoise()
            self.assertTrue(oldDeviation = self.unit.criticalDeviation)
            
    def testComputeNextDeviationRunoffAndStabilityLinear(self):
        "Approximate tests on the behavior of a self-connected  unit running repeatedly. Check if it runs to (+/-) infinity or it stabilizes"

        errorTolerance = 0.00000001               #Need to use a tolerance threshold for comparison, due to floating point math"


        #the polarity of the output controls the change in the criticalDeviation through simple summation.
        #We  check that it runs up toward positive infinity (1) and negative infinity (2) (with linear increases)"
        # We set noises to 0, viscosity to 1, potentiometer to 1, etc, to check that the basic mechanism works."

        self.unit.needleCompMethod('linear')
        self.unit.needleUnit.mass(1)                 # the force acting on a Aristotelian unit is always inversely proportional to the mass. 
                                                     # set it to 1 to exclude complications from this test."

        #1. with self connection to 1, noise at 0, viscosity to 1 and the unit not connected to other units, 
        # the deviation increases by the ratio criticalDeviation/maxDeviation every cycle if it starts positive, 
        #because output is ALWAYS proportional to the unit's range. Eventually it will go up to infinity, i..e to maxDeviation." 

        self.unit.potentiometer(1)                  #this sets the value of the self-connection"
        self.unit.inputConnections[1].switch(1)     #self-connection is positive"
        self.unit.noise(0)                          #No noise  to simplify calculations"
        self.unit.viscosity(1)
        self.unit.criticalDeviation(1)
        self.unit.currentOutput(1)
        self.unit.selfUpdate()
        self.assertTrue(self.unit.criticalDeviation == 2)
        self.unit.selfUpdate()
        self.assertTrueself(self.unit.criticalDeviation == (2 + (2/ self.unit.maxDeviation)))
        tempDev = self.unit.criticalDeviation
        for i in xrange(10):
            self.unit.selfUpdate()
            tempDev = tempDev + (tempDev/ self.unit.maxDeviation)
        self.assertTrue(abs(self.unit.criticalDeviation  - tempDev) < errorTolerance)     
        for i in xrange(100):
            self.unit.selfUpdate()
        self.assertTrue(self.unit.criticalDeviation == self.unit.maxDeviation)



        #"2. with starting point negative we will run up to negative infinity, 
        # because the output will become negative after the first iteration."
        self.unit.criticalDeviation = -3
        self.unit.currentOutput(1)
        self.unit.selfUpdate()
        self.assertTrue(self.unit.criticalDeviation == -2)
        
        tempDev = self.unit.criticalDeviation
        for i in xrange(10):
            self.unit.selfUpdate()
            tempDev = tempDev + (tempDev / self.unit.maxDeviation)
        self.assertTrue(abs(self.unit.criticalDeviation  - tempDev)  < errorTolerance)     
        for i in xrange(100):
            self.unit.selfUpdate()
            
        self.assertTrue(self.unit.criticalDeviation() == -(self.unit.maxDeviation()))



        # 3. with polarity reversed  the unit will tend to stabilize itself around 0, 
        # because the output will always counteract the unit's deviation. "
        self.unit.inputConnections[1].switch(- 1)       #"self-connection's switch is negative: 
                                                        # unit's output is reinputted with reverse polarity"

        self.unit.criticalDeviation(-2)
        self.unit.currentOutput(-1)
        self.unit.selfUpdate()
        self.assertTrue(self.unit.criticalDeviation() == -1)
        for i in xrange(200):
            self.unit.selfUpdate()
        self.assertTrue(self.unit.criticalDeviation() < abs(errorTolerance))

        #4." 
        self.unit.criticalDeviation(2)
        self.unit.currentOutput(-1)
        self.unit.selfUpdate()
        self.assertTrue(self.unit.criticalDeviation() == 3)
        for i in xrange(200):
            self.unit.selfUpdate()
        self.assertTrue(self.unit.criticalDeviation < abs(errorTolerance))

    def testComputeNextDeviationLinearUnconnected(self):
        "Checks  a single unconnected unit. The value will always remain at its initial value no matter how many times the unit updates"

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
        
        testRuns = 1000
        self.unit.needleCompMethod('linear')
        self.unit.potentiometer(0)  #"put the weight of the self-connection to zero."

        for each in xrange(testRuns):
            self.unit.criticalDeviation(numpy.random.uniform(- self.unit.maxDeviation, self.unit.maxDeviation))
            self.unit.needleUnit.mass(numpy.random.uniform(0.0001, 10000))
            self.unit.viscosity(numpy.random.uniform(0,1))
            tempDev = self.unit.criticalDeviation()
            for i in xrange(10):
                self.unit. selfUpdate()
            self.assertTrue(tempDev == self.unit.criticalDeviation())

    def testComputeNextDeviationLinearConnected(self):
        "Checks the computation of a self-connected unit connected to another unit."

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
        
        testRuns = 100
        anotherUnit = HomeoUnit()
        self.unit.needleCompMethod('linear')
        self.unit.noise(0)                              #Eliminate flicker noise to simplify test"
        self.unit.needleUnit.mass(1)
    
        self.unit.addConnectionWithRandomValues(anotherUnit)
        for eachConn in self.unit.inputConnections:
            eachConn.noise(0)                          #the self-connection and the connection to anotherUnit are noise-free"

        for i in xrange(testRuns):
            self.unit.criticalDeviation(numpy.random.uniform(-10,10))
            self.unit.computeOutput()
            self.unit.potentiometer(numpy.random.uniform(0,1))
            self.unit.switch(numpy.sign(numpy.random.uniform(-1,1))) #sign returns 0 for input = 0. Homeounit.switch() considers 0 to be positive
            deviation = self.unit.criticalDeviation()     
            for i in xrange(10): 
                errorTolerance = 10^-14                                    #"Cannot get a result better than 10^-14. Consistently fails on smaller values"
                tempInput = ((self.unit.inputConnections[2]).output())
                deviation = deviation  + (self.unit.currentOutput() * self.unit.potentiometer() * self.unit.switch()) + tempInput
                exceeded = abs(deviation) > self.unit.maxDeviation() 
                self.unit.selfUpdate()
                if exceeded: 
                    self.assertTrue(True)                              # If criticalDeviation value went at any time beyond clipping limits don't check. 
                                                                       # testing clipping is carried out in others test methods
                else:
                    self.assertTrue(abs(deviation - self.unit.criticalDeviation())  < errorTolerance)

    def testComputeNextDeviationLinearConnectedTo10Units(self):
        "Check the values of a unit connected to 10 other units"
        
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

        errorTolerance = 10^-14             #Cannot get a result better than 10^-14. Consistently fails on smaller values"
        testRuns = 1

        for each in xrange(10):
            aUnit = HomeoUnit()
            self.unit. addConnectionWithRandomValues(aUnit) 

        self.unit.needleCompMethod('linear')
        self.noise(0)                              # "Eliminate flicker noise to simplify test"
        self.unit.needleUnit.mass(1)
    

        for conn in self.unit. inputConnections:
            conn.noise(0)                             #the self-connection and the connections to all other units  are noise-free"

        for i in xrange(testRuns):
            self.unit.criticalDeviation(numpy.random.uniform(- self.unit.maxDeviation(), self.unit.maxDeviation()))
            self.unit.computeOutput()
            self.unit.potentiometer(numpy.random.uniform(0,1))
            self.unit.switch(numpy.sign(numpy.random.uniform(-1,1)))
            for k in xrange(100):
                deviation = self.unit.criticalDeviation()     
                tempInput = 0
                for conn in xrange(2,len(self.unit.inputConnections)):
                                   tempInput = tempInput + (self.unit.inputConnections[conn].output())     #only sum the input from external units"
                deviation = deviation  + (self.unit.currentOutput() * self.unit.potentiometer() * self.unit.switch()) + tempInput
                exceeded = abs(deviation)  > self.unit. maxDeviation() 
                self.unit.selfUpdate()
                if exceeded:
                    self.assertTrue(True)
                    deviation = self.unit.criticalDeviation                                                    
                    # If criticalDeviation value went at any time  beyond clipping limits don't check. 
                    # (This test is carried out in other unit tests) 
                    # Reset computing deviation to avoid carrying the error over to next cycles"
                else:
                    self.assertTrue(abs(deviation - self.unit.criticalDeviation())  < errorTolerance)

    def testComputeNextDeviationLinearSelfconnected(self):
        "Check the values of a single self-connected unit"
    
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

        errorTolerance = 0
        testRuns = 1000
        self.unit.needleCompMethod('linear')
        self.unit.maxDeviation(100)
        self.unit.noise(0)                        #initially set the unit unconnected to correctly initialize value of output."
        self.unit.needleUnit.mass(1)
        self.unit.inputConnections[1].noise(0)    #the self-connection is noise-free"
        for test in xrange(testRuns):
            self.unit. criticalDeviation(numpy.random.uniform(- self.unit.maxDeviation(),self.unit.maxDeviation))
            self.unit.computeOutput()
            #self.unit.criticalDeviation()    FIXIT! Unclear why this instruction is here. 
            self.unit.potentiometer(numpy.random.uniform(0, 1))
            self.unit.switch(numpy.sign(numpy.random.uniform(-1,1)))
            for i in xrange(10):
                deviation = self.unit.criticalDeviation()
                deviation = deviation + (self.unit.currentOutput() * self.unit.potentiometer() * self.unit.switch())
                exceeded = abs(deviation) >  self.unit.maxDeviation()
                self.unit.selfUpdate
            if exceeded: 
                self.assertTrue(True)
            else:
                self.assertTrue(deviation = self.unit.criticalDeviation)

    def testInitializationDefaults(self):
        "test that the class default values are properly inserted in the instance's variable"
        
        defViscosity = HomeoUnit.defaultParameters['viscosity']
        self.assertTrue(self.unit.viscosity == defViscosity)
    
        defMaxDeviation = HomeoUnit.defaultParameters['maxDeviation']
        self.assertTrue(self.unit.maxDeviation == defMaxDeviation)

        defNoise = HomeoUnit.defaultParameters['noise']
        self.assertTrue(self.unit.noise == defNoise)

        defPotentiometer = HomeoUnit.defaultParameters['potentiometer']
        self.assertTrue(self.unit.potentiometer == defPotentiometer)

        defOutputRange = HomeoUnit.defaultParameters('outputRange')
        self.assertTrue((self.unit.outputRange['high']) == defOutputRange['high'])
        self.assertTrue((self.unit.outputRange['low']) == defOutputRange['low'])

        defTime = HomeoUnit.defaultParameters('time')
        self.assertTrue(self.unit.time == defTime)

        defUniselectorTime = HomeoUnit.defaultParameters['uniselectorTime']
        self.assertTrue(self.unit.uniselectorTime == defUniselectorTime)

        defUniselectorTimeInterval = HomeoUnit.defaultParameters['uniselectorTimeInterval']
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

        unit4 = self.unit.copy

        self.assertTrue(self.unit.sameAs(unit4))   # two units are the same

        param = unit4.name 
        unit4.name(param + 'pippo')                  #change the name and check again
        self.assertFalse(self.unit.sameAs(unit4))
        
        "two newly created units can never be same because their names will differ"
        self.unit = HomeoUnit()
        unit4 = HomeoUnit()
        self.assertFalse(self.unit.sameAs(unit4))

    def testNeedleWithinLimit(self):
        "testing the clipping function operating on a unit's critical deviation's value"

        highVal = self.unit.maxDeviation()
        lowVal = - self.unitmaxDeviation()

        aValue = highVal * 1.1
        self.assertFalse(self.unit.isNeedleWithinLimits(aValue))

        aValue = highVal *0.9
        self.assertTrue(self.unit.isNeedleWithinLimits(aValue))

        aValue = lowVal *1.1
        self.assertTrue(self.unit.isNeedleWithinLimits(aValue))

        aValue = lowVal *0.9
        self.assertTrue(self.unit.isNeedleWithinLimits(aValue))

    def testNewNeedlePosition(self):
        "test correct computation of needle movement. Ignore noise, as it is computed within the unit itself"

        self.unit.needleUnit.mass(1)
        maxInput = 3                #typical of the 4 units Homeostat"
        minInput = - maxInput
        for i in xrange(100):
            self.unit.criticalDeviation(1)
            self.unit.needleCompMethod('linear')
            self.unit.noise(0)
            self.unit.viscosity(1)
            torqueValue = numpy.random.uniform(minInput, maxInput)
            newNeedlePosition = self.unit.newNeedlePosition(torqueValue)
            correctValue = self.unit.criticalDeviation() + (torqueValue * self.unit.viscosity())  - self.unit.noise()
          
            # Print values to console for debugging purposes
            print 'newNeedlePos: ' + newNeedlePosition + '   and critical Dev: ' + self.unit.criticalDeviation()
            print  self.unit.printDescription()
            
            
            self.assertTrue(newNeedlePosition == correctValue)

    def testFirstLevelParamSameAs(self):
        "a unit that is a copy of another unit  must have the same first level parameters, name included" 
        
        self.unit.setRandomValues()
        anotherUnit = self.unit.copy()
        self.assertTrue(self.unit.sameFirstLevelParamsAs(anotherUnit))

        oldUnitName = self.unit.name()
        newRandomName = ''.join(random.choice(string.ascii_lowercase) for x in range(10))
        
        self.unit.name(newRandomName)
        self.assertFalse(self.unit.sameFirstLevelParamsAs(anotherUnit))
        self.unit.name(oldUnitName)

        self.assertTrue(self.unit. sameFirstLevelParamsAs(anotherUnit))

        anotherUnit.potentiometer(anotherUnit.potentiometer() + 0.1)

        self.assertFalse(self.unit.sameFirstLevelParamsAs(anotherUnit))

        def testComputeNextDeviationRandom(self):
            "Test that a unit's deviation will go through random value when no computation method is chosen"
            self.unit.needleCompMethod('')      # empty string should trigger the random method"
            deviationValues = [] 
            #check that the critical deviation values are always different"
            
            for i in xrange(1000):
                deviationValues.append(self.unit.criticalDeviation())
                self.unit.selfUpdate()
            self.assertTrue(len(set(deviationValues)) == 1000)

    def testPotentiometer(self):
        poten = self.unit.potentiometer()
        selfConnWeight = (self.unit.inputConnections[1]).weight
        self.assertTrue(poten == selfConnWeight)
                
        self.unit.potentiometer(1)
        self.assertTrue(poten == selfConnWeight)
        
        for i in xrange(10):
            self.unit.potentiometer(numpy.random.uniform(0,1))
            self.assertTrue(poten == selfConnWeight)

    def testOutputRange(self):
        "a Unit in normal operation never goes out of range"
        highRange = self.unit. outputRange['high']
        lowRange = self.unit. outputRange['low']
        for i in xrange(100): 
            self.unit.selfUpdate()
            self.assertTrue((self.unit.currentOutput < highRange) and 
                            (self.unit.currentOutput > lowRange))

    def testOutputAndDeviationInRange(self):
        """
        Repeated test with fully connected units. 
        Check that  outputs values and 
        critical deviation values are within their ranges
        """
                
        highOut = self.unit.outputRange['high']
        lowOut = self.unit.outputRange['low']
        highDev = self.unit.maxDeviation()
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
            self.assertTrue(self.unit.currentOutput() < lowOut and
                            self.unit.currentOutput() > highOut)
            self.assertTrue(self.unit.criticalDeviation() > lowDev and
                            self.unit.criticalDeviation() < highDev)


    def testComputeTorqueWithinLimits(self):
        """
        A unit's maximum torque is always between 
        the sum of the inputs from the connected units (eventually negated)
        """

        unit2 = HomeoUnit()
        unit3 = HomeoUnit()
        unit4 = HomeoUnit()

        self.unit.addConnectionWithRandomValues(unit2)
        self.unit.addConnectionWithRandomValues(unit3)
        self.unit.addConnectionWithRandomValues(unit4)

        for i in xrange(1000):
            self.unit.selfUpdate()
            self.assertTrue (self.unit.computeTorque() >  -3 and
                             self.unit.computeTorque < 3)

    def testComputeTorque(self):
        "Tests that a unit's torque is equal to the sum of the connected unit's outputs"
        unit2 = HomeoUnit()
        unit3 = HomeoUnit()
        unit4 = HomeoUnit()
    
        "1. test torque when unit is not connected to anything. Should be 0"
        self.unit.removeConnectionFromUnit(self.unit)

        self.assertTrue(len(self.unit.inputConnections()) == 0)
        self.assertTrue(self.unit. computeTorque() == 0)

        "2. add a self connection at 1 and another connection at 1. torque should be 2"

        self.unit.currentOutput(1)
        unit2.currentOutput(1)
        self.unit.addConnectionWithWeightAndPolarityAndNoiseAndState(self.unit,1,1, 0, 'manual')
        self.unit.addConnectionWithWeightAndPolarityAndNoiseAndState(unit2, 1,1,0,'manual')
        self.assertTrue(len(self.unit.inputConnections() == 2))
        self.assertTrue(self.unit.computeTorque() == 2)

        "3. Add a pair of connections at -1. Torque should be 0"

        unit3.currentOutput(1)
        unit4.currentOutput(1)
        self.unit.addConnectionWithWeightAndPolarityAndNoiseAndState(unit3,1,-1, 0, 'manual')
        self.unit.addConnectionWithWeightAndPolarityAndNoiseAndState(unit4, 1,-1,0,'manual')
        self.assertTrue(len(self.unit.inputConnections() == 4))
        self.assertTrue(self.unit.computeTorque() == 0)

    def testComputeNextOutputWithDefaults(self):
        """A unit:
            1. computes a new value and puts it in the correct iVar
            2. has the value  within the unit's limits

            tests are performed  with default values """

        highRange = self.unit.outputRange['high']
        lowRange = self.unit.outputRange['low']

        oldOutput= self.unit.currentOutput()
        self.unit.selfUpdate()

        self.assertFalse(oldOutput == self.unit.currentOutput())       # "1st test " 
        self.assertTrue(self.unit.currentOutput > lowRange and
                        self.unit.currentOutput() < highRange)         # "2nd test "
        
    def testComputeNextDeviationWithDefaults(self):
        """
        A unit:
            1. computes a new value for critical deviaiton and puts it in the correct iVar
            2. has the value within the unit's limits

            tests are performed  with default values 
        """
        highRange = self.unit.maxDeviation()
        lowRange = - highRange

        oldCriticalDeviation = self.unit.criticalDeviation()
        self.unit.selfUpdate()

        self.assertFalse(oldCriticalDeviation == self.unit.criticalDeviation())       # "1st test " 
        self.assertTrue(self.unit.criticalDeviation() > lowRange and
                        self.unit.criticalDeviation() < highRange)         # "2nd test "

    def testComputeNextDeviationProportional(self):
        """the polarity of the output controls the change in the criticalDeviation through simple summation. 
        However, the change is proportional to the range of deviation of the output. 

        """

        self.unit.needleCompMethod('proportional')

        #" We set noises to 0, viscosity to 1, potentiometer to 1, etc, to check that the basic mechanism works."


        # 1. with self connection to 1, noise at 0, viscosity to 1 and the unit not connected to other units, 
        # the deviation should increase by the ratio b/w unit's inputs and unit's range" 

        self.unit.potentiometer(1)      # set the weight of the self-connection"
        self.unit. switch(1)            # set the polarity of the self-connection"
        self.unit. noise(0)
        self.unit.viscosity(1)
        self.unit.criticalDeviation(0)
        self.unit.currentOutput(2)
        self.unit.maxDeviation(10)
        unitRange = self.unit.outputRange['high'] - self.unit.outputRange['low']
        proportionalIncrease = self.unit.currentOutput() / unitRange  

        self.unit.selfUpdate()
        self.assertTrue(self.unit.criticalDeviation() == 0 + proportionalIncrease)

        # 2 with  output negative we decrease by the same ratio"
        self.unit.criticalDeviation(0)
        self.unit.currentOutput(-2)
        self.unit.maxDeviation(10)
        proportionalIncrease = self.unit.currentOutput() / unitRange  

        self.unit.selfUpdate()
        self.assertTrue(self.unit.criticalDeviation() ==  0 + proportionalIncrease)

    def testChangeUniselectorType(self):
        """
        try changing a HomeoUnit uniselector  to an instance of the HomeoUniselector (sub)class
        and to some random string
        """
        goodUniselectors = []
        badUniselectors = []

        goodUniselectors.extend([class_.__name__ for class_ in withAllSubclasses(HomeoUniselector)])
        badUniselectors.extend('Ashby','UniformRandom','HomeoUnit')
        self.unit.setDefaultUniselectorSettings()
        for unisel in goodUniselectors:
            self.unit.uniselectorChangeType(unisel)
            self.assertTrue(self.unit.uniselector().__class__.__name__ == unisel)

        self.unit.setDefaultUniselectorSettings()
        for unisel in badUniselectors:
            self.unit.uniselectorChangeType(unisel)
            self .assertFalse(self.unit.uniselector.__class__.__name__ == unisel)

    def testViscosity(self):
        """
        TODO Viscosity reduces the effect of  the outside force on the unit's needle movement.
    
        When viscosity = 0, the force affecting the unit  is unchanged"""

        self.assertTrue(False)


        "When viscosity > 0, the force  changes according to drag. Real tests of drag laws performed in drag unit tests. Here we just check that it is lower than when viscosity +0"

        self.assertTrue(False)

    def testSelfUpdateAdvancesUnitTime(self):
        """
        Test that a HomeoUnit's simulation time advances by 1 after a self update
        """
        oldUnitTime = self.unit.time() 
        self.unit.selfUpdate()
        self.assertTrue(self.unit.time() == oldUnitTime + 1)

    def testSelfUpdateAdvancesUniselectorTime(self):
        """
        Test that a HomeoUnit's Uniselector's simulation time advances by 1 after a self update
        """
        oldUniselectorTime= self.unit.uniselectorTime()
        self.unit.selfUpdate()
        self.assertTrue(self.unit.uniselectorTime() == oldUniselectorTime + 1)

    def testDeviationComputationsDontTouchInstanceVariables(self):
        """
        Check that the various methods used to compute the critical deviation simply output 
         a value and do not indeed change the actual value of deviation stored in the instance variable
         """
    
        self.unit.setRandomValues()

        self.unit.needleCompMethod('linear')
        for i in xrange(10):
                    aTorqueValue = numpy.random.uniform( -1 ,  1)
                    oldDeviation = self.unit.criticalDeviation()
                    self.unit.newNeedlePosition(aTorqueValue)
                    self.assertTrue(oldDeviation == self.unit.criticalDeviation)

        self.unit.needleCompMethod('proportional')
        for i in xrange(10):
                    aTorqueValue = numpy.random.uniform( -1 ,  1)
                    oldDeviation = self.unit.criticalDeviation()
                    self.unit.newNeedlePosition(aTorqueValue)
                    self.assertTrue(oldDeviation == self.unit.criticalDeviation)

        self.unit.needleCompMethod('random')
        for i in xrange(10):
                    aTorqueValue = numpy.random.uniform( -1 ,  1)
                    oldDeviation = self.unit.criticalDeviation()
                    self.unit.newNeedlePosition(aTorqueValue)
                    self.assertTrue(oldDeviation == self.unit.criticalDeviation)

        self.unit.needleCompMethod('')
        for i in xrange(10):
                    aTorqueValue = numpy.random.uniform( -1 ,  1)
                    oldDeviation = self.unit.criticalDeviation()
                    self.unit.newNeedlePosition(aTorqueValue)
                    self.assertTrue(oldDeviation == self.unit.criticalDeviation)
    

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()  
