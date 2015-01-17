'''
Created on Mar 11, 2013

@author: stefano
'''
from __future__ import division

from   Core.HomeoUnit import HomeoUnit
from   Core.HomeoUnitNewtonian import HomeoUnitNewtonian
from   Core.HomeoUniselector import *
from   Core.HomeoDataCollector import *
from   Core.Homeostat import *
from   Helpers.HomeoNoise import  *

import unittest,numpy, math
import scipy.stats as stats

class HomeoUnitNewtonianTest(unittest.TestCase):


    def setUp(self):
        self.unit = HomeoUnitNewtonian()

    def testComputeNextDeviationLinear(self):
        """
        Test that the displacement of the needle of  Newtonian unit is computed
        according to Newtonian dynamics: s + v + 1/2ma 
        """
        self.unit.criticalDeviation = 0
        for i in xrange(1000): 
            torque = numpy.random.uniform(-1,1) 
            self.unit.needleUnit.mass = numpy.random.uniform(1,10000)
            oldDev = self.unit.criticalDeviation
            oldVelocity = self.unit.currentVelocity
            self.unit.criticalDeviation = self.unit.newLinearNeedlePosition(torque)
            "Check the computation is correct according to Newtonian dynamics"
            self.assertTrue(self.unit.criticalDeviation == (oldDev  + oldVelocity + (1/2. * (torque/ self.unit.needleUnit.mass))))      

    def testComputeNextVelocityWithoutConnections(self):
        """
        Test computation of velocity according to Newtonian laws , NO connections
        """
        errorTolerance = 10**-13 
        testRuns = 1000
        self.unit.criticalDeviation = 0
        self.unit.noise = 0
        self.unit.currentOutput = 0.1
        self.unit.inputConnections[0].noise = 0
        
        for index in xrange(testRuns):
            self.unit.needleUnit.mass = numpy.random.uniform(1,1000)
            oldVelocity = self.unit.currentVelocity
            
            "compute the torque as sum of the output coming from connected units"
            unitActiveInputs = [activeConn.output() for activeConn in self.unit.inputConnections if activeConn.isActive() and activeConn.incomingUnit.isActive()]
            torque = reduce(lambda x,y: x+y, unitActiveInputs) 
            
            "consider the drag affecting the force"
            torque = torque + self.unit.drag()
            
            "velocity value according to  Newtonian dynamics: v = v0 +at (where a is force / mass)"                                            
            computedVelocity = oldVelocity + (torque / self.unit.needleUnit.mass)    
            self.unit.selfUpdate()
            
            '''Do not compare calculations when the unit's needle would have gone 
            over the maximum limit, because the actual displacement is clipped at the maximum value. 
            Since actual velocity is computed on the basis of actual displacement 
            (as it should be), the theoretical value is bound to be off'''
            if (self.unit. criticalDeviation >= self.unit.maxDeviation) or (self.unit.criticalDeviation <= - (self.unit.maxDeviation)):
                velocityDelta = 0
            else:
                velocityDelta = abs(self.unit.currentVelocity - computedVelocity)
            
            self.assertTrue(velocityDelta < errorTolerance)
                            
                                    

    def testComputeNextVelocityWithConnections(self):
        """
        Test computation of velocity according to Newtonian laws when connections are present
        """
        
        errorTolerance = 10**-14
        testRuns = 1000
        anotherUnit = HomeoUnitNewtonian()
        anotherUnit.noise = 0
        self.unit.addConnectionWithRandomValues(anotherUnit)

        self.unit.inputConnections[1].noise = 0
        self.unit.criticalDeviation = 0
        self.unit.noise = 0
        for conn in self.unit.inputConnections:
            conn.noise = 0
        for conn in anotherUnit.inputConnections:
            conn.noise = 0
            
        for index in xrange(testRuns):
            self.unit.needleUnit.mass = numpy.random.uniform(1,1000)
            oldVelocity = self.unit.currentVelocity
            "compute the torque as sum of the output coming from connected units"
            unitActiveInputs = [activeConn.output() for activeConn in self.unit.inputConnections if activeConn.isActive() and activeConn.incomingUnit.isActive()]
            torque = reduce(lambda x,y: x+y, unitActiveInputs) 
            
            "consider the drag affecting the force"
            torque = torque + self.unit.drag()
            
            "velocity value according to Newtonian dynamics: v = v0 +at (where a is force / mass)"                                            
            computedVelocity = oldVelocity + (torque / self.unit.needleUnit.mass)    
            self.unit.selfUpdate()
            
            '''Do not compare calculations when the unit's needle would have gone 
            over the maximum limit, because the actual displacement is clipped at the maximum value. 
            Since actual velocity is computed on the basis of actual displacement 
            (as it should be), the theoretical value is bound to be off'''
            if (self.unit. criticalDeviation >= self.unit.maxDeviation) or (self.unit.criticalDeviation <= - (self.unit.maxDeviation)):
                velocityDelta = 0
            else:
                velocityDelta = abs(self.unit.currentVelocity - computedVelocity)
            print index, velocityDelta
            self.assertTrue(velocityDelta < errorTolerance)
   
    def testDragEquationDrag(self):
        """
        The Drag equation computes drag force on a surface of area A as
        Drag = Area * 1/2 * DragCoefficient * density * velocity^2
        We actually need to convert the unit's current velocity
        to real physical units to have a minimum of plausibility.
        HomeoUnit>>physicalVelocity does that on the basis of conversion parameters
        stored in the iVar physicalParameters
        """
        errorTolerance = 0.000000001
        testRuns = 1000

        "When the unit is started, velocity is zero, and dragForce should be zero"
        self.unit.currentVelocity = 0
        for i in xrange(testRuns):
            self.unit.density = numpy.random.uniform(1,1000)
            self.unit.needleUnit.surfaceArea = numpy.random.uniform((1/numpy.pi * 0.001), 1000)
            self.unit.needleUnit.dragCoefficient = numpy.random.uniform(0.3,2)
            dragForce = self.unit.dragEquationDrag()
            self.assertEqual(dragForce, 0)

        '''When Velocity is not zero, Drag Force follows drag's equation.
         We briefly test with random velocities,random densities, random surface areas, and random coefficients'''

        for index in xrange(testRuns):
            self.unit.currentVelocity = numpy.random.uniform(-10,10)
            self.unit.density = numpy.random.uniform(1,1000)
            self.unit.needleUnit.surfaceArea = numpy.random.uniform((1/numpy.pi * 0.001), 1000)
            self.unit.needleUnit.dragCoefficient = numpy.random.uniform(0.3, 2)

            dragForce = self.unit.dragEquationDrag()
            delta = abs((dragForce - (1/2 * self.unit.needleUnit.surfaceArea * self.unit.needleUnit.dragCoefficient * self.unit.density * self.unit.physicalVelocity()**2)))
            self.assertTrue(delta < errorTolerance)
            
    def testStokesDrag(self):
        """
        Stokes's law computes drag force on a sphere of radius r  as 6* pi * radius * viscosity * velocity.
        We use the radius of the surface area of the moving needle instead
        """
        testRuns = 1000
        
        "When the unit is started, velocity is zero, and dragForce should be zero"
        self.unit.currentVelocity = 0

        for index in xrange(testRuns):
            self.unit.viscosity = numpy.random.uniform(0.001,1)
            self.unit.needleUnit.surfaceArea = numpy.random.uniform((1/numpy.pi * 0.001), 1000)
            radius = math.sqrt(self.unit.needleUnit.surfaceArea / numpy.pi)
            dragForce = self.unit.stokesLawDrag()
            self.assertTrue(dragForce == 0)

        '''When Velocity is not zero, Drag Force follows Stokes's law.
           We briefly test with random velocities, random densities, and random surface areas'''
        for index in xrange(testRuns):
            self.unit.currentVelocity = numpy.random.uniform(-10,10)
            self.unit.viscosity = numpy.random.uniform(0.1,1)
            self.unit.needleUnit.surfaceArea = numpy.random.uniform((1/numpy.pi * 0.001),1000)
            radius = math.sqrt(self.unit.needleUnit.surfaceArea / numpy.pi)
            dragForce = self.unit.stokesLawDrag()
            "test with precision to 10 decimals"
            #self.assertAlmostEqual(dragForce , -(6 * numpy.pi * radius * self.unit.viscosity * self.unit.currentVelocity), 10)
            self.assertAlmostEqual(dragForce, -self.unit.viscosity * self.unit.currentVelocity, 10)

    def testUniselectorIsTriggered(self):
        """
        Test that a unit's uniselector is triggered when a unit's essential variable is critical and uniselectorTime is equal or exceeded
        """
        
        "Check a HomeoUnitNewtonian unit. Other kinds of unit have their test in their corresponding test class."
                
        '''Set the unit at the critical threshold and uniselectorTime to one step before the threshold 
          (so 't will reach it in the next update'''
        
        self.unit = HomeoUnitNewtonian()
        self.unit.criticalDeviation = (self.unit.maxDeviation * self.unit.critThreshold) 
        self.unit.uniselectorActive = True
        self.unit.uniselectorTime = self.unit.uniselectorTimeInterval
        
        "set self.unit connection to be positive, to insure positive feedback. 0 noise to simplify test"
        self.unit.inputConnections[0].newWeight(1)
        self.unit.inputConnections[0].noise = 0
        self.unit.selfUpdate()
        self.assertTrue(self.unit.uniselectorActivated == 1)
        
        "Run just one more step. UniselectorActivated should be back to 0 and uniselectorTime should be back to 1"
        self.unit.selfUpdate()
        self.assertTrue(self.unit.uniselectorActivated == 0)
        self.assertTrue(self.unit.uniselectorTime == 1)
    
    def tearDown(self):
        pass



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()