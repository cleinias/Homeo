'''
Created on Mar 11, 2013

@author: stefano
'''
from functools import reduce

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
        for i in range(1000): 
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
        
        for index in range(testRuns):
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
            
        for index in range(testRuns):
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
            print(index, velocityDelta)
            self.assertTrue(velocityDelta < errorTolerance)
   
    def testDragEquationDrag(self):
        """
        The implementation of dragEquationDrag simplifies the full drag equation
        by absorbing all constants (area, drag coefficient, 1/2) into the viscosity
        parameter: Drag = - viscosity * velocity^2.
        Sign is negative because drag opposes velocity.
        """
        errorTolerance = 0.000000001
        testRuns = 1000

        "When the unit is started, velocity is zero, and dragForce should be zero"
        self.unit.currentVelocity = 0
        for i in range(testRuns):
            self.unit.viscosity = numpy.random.uniform(0, 10)
            dragForce = self.unit.dragEquationDrag()
            self.assertEqual(dragForce, 0)

        '''When Velocity is not zero, Drag = -viscosity * velocity^2'''

        for index in range(testRuns):
            self.unit.currentVelocity = numpy.random.uniform(-10, 10)
            self.unit.viscosity = numpy.random.uniform(0, 10)

            dragForce = self.unit.dragEquationDrag()
            expectedDrag = -self.unit.viscosity * pow(self.unit.currentVelocity, 2)
            delta = abs(dragForce - expectedDrag)
            self.assertTrue(delta < errorTolerance)
            
    def testStokesDrag(self):
        """
        Stokes's law computes drag force on a sphere of radius r  as 6* pi * radius * viscosity * velocity.
        We use the radius of the surface area of the moving needle instead
        """
        testRuns = 1000
        
        "When the unit is started, velocity is zero, and dragForce should be zero"
        self.unit.currentVelocity = 0

        for index in range(testRuns):
            self.unit.viscosity = numpy.random.uniform(0.001,1)
            self.unit.needleUnit.surfaceArea = numpy.random.uniform((1/numpy.pi * 0.001), 1000)
            radius = math.sqrt(self.unit.needleUnit.surfaceArea / numpy.pi)
            dragForce = self.unit.stokesLawDrag()
            self.assertTrue(dragForce == 0)

        '''When Velocity is not zero, Drag Force follows Stokes's law.
           We briefly test with random velocities, random densities, and random surface areas'''
        for index in range(testRuns):
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

class HomeoUnitNewtonianIntegratorTest(unittest.TestCase):
    """The integrator, step by step, against the exact solution.

    The tests above leave the velocity at 0, the viscosity at its default of 0
    and dt_fast at 1, so they check only the 1/2 a term.  Here a unit driven by
    a constant torque F, with Stokes drag c = viscosity, must follow the
    solution of m dv/dt = F - c v at t = dt_fast, 2 dt_fast, ...:

        v(t) = F/c + (v0 - F/c) e^(-c t / m)
        x(t) = F t / c + (v0 - F/c) (m / c) (1 - e^(-c t / m))

    (v0 + F t / m and v0 t + F t^2 / 2m without viscosity), on the Python
    path and on the headless (JIT) path, for any c dt / m.  The needle stays
    well inside its limits.
    """

    def makeUnit(self, mass, viscosity, dtFast, v0, torque, headless):
        unit = HomeoUnitNewtonian()
        unit.noise = 0
        unit.uniselectorActive = False
        unit.needleUnit.mass = mass
        unit.viscosity = viscosity
        unit.dt_fast = dtFast
        unit.criticalDeviation = 0
        unit.currentVelocity = v0
        unit.disactivateSelfConn()
        driver = HomeoUnit()
        driver.currentOutput = 1.0
        unit.addConnectionWithRandomValues(driver)
        drive = unit.inputConnections[-1]
        drive.newWeight(torque)
        drive.noise = 0
        unit._headless = headless
        unit._jit_dirty = True
        self.driver = driver                    # keep the driving unit alive
        return unit

    def expectedTrajectory(self, mass, viscosity, dtFast, v0, torque, steps):
        xs, vs = [], []
        for i in range(1, steps + 1):
            t = i * dtFast
            if viscosity == 0:
                xs.append(v0 * t + torque * t ** 2 / (2 * mass))
                vs.append(v0 + torque * t / mass)
            else:
                terminal = torque / viscosity
                decay = math.exp(-viscosity * t / mass)
                xs.append(terminal * t + (v0 - terminal) * mass / viscosity * (1 - decay))
                vs.append(terminal + (v0 - terminal) * decay)
        return xs, vs

    def checkTrajectory(self, headless):
        steps = 30
        for dtFast in (0.5, 1.0, 2.0):
            for mass, viscosity, v0, torque in ((5.0, 2.0, 0.3, 0.05),
                                                (20.0, 0.5, -0.05, -0.02),
                                                (2.0, 0.0, 0.05, 0.002),
                                                (1.0, 10.0, 0.2, 0.1),        # c dt / m up to 20
                                                (100.0, 1e-3, 0.01, 0.01)):   # c dt / m ~ 1e-5
                unit = self.makeUnit(mass, viscosity, dtFast, v0, torque, headless)
                xs, vs = self.expectedTrajectory(mass, viscosity, dtFast, v0, torque, steps)
                for step in range(steps):
                    unit.selfUpdate()
                    self.assertLess(abs(unit.criticalDeviation), unit.maxDeviation)
                    self.assertAlmostEqual(unit.criticalDeviation, xs[step], delta=1e-9,
                                           msg="x at step %d, dt %s, m %s, visc %s" % (step, dtFast, mass, viscosity))
                    self.assertAlmostEqual(unit.currentVelocity, vs[step], delta=1e-9,
                                           msg="v at step %d, dt %s, m %s, visc %s" % (step, dtFast, mass, viscosity))

    def testTrajectoryPythonPath(self):
        self.checkTrajectory(headless=False)

    def testTrajectoryHeadlessPath(self):
        self.checkTrajectory(headless=True)

    def testClippingStopsTheNeedle(self):
        "A needle driven past its limit sits at the limit with zero velocity"
        unit = self.makeUnit(1.0, 0.0, 1.0, 5.0, 1.0, headless=False)
        for step in range(20):
            unit.selfUpdate()
        self.assertEqual(unit.criticalDeviation, unit.maxDeviation)
        self.assertEqual(unit.currentVelocity, 0)
