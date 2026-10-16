'''
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

    def testNeedleCompMethodIsLinearOnly(self):
        '''Newton's second law is the 'linear' computation: a Newtonian unit
           refuses the others instead of crashing in its update.'''
        self.unit.needleCompMethod = 'linear'
        for method in ('proportional', 'random', ''):
            with self.assertRaises(ValueError):
                self.unit.needleCompMethod = method
        self.assertEqual(self.unit.needleCompMethod, 'linear')
        self.unit.selfUpdate()

    def testComputeNextDeviationLinear(self):
        """
        Test that the displacement of the needle of  Newtonian unit is computed
        according to Newtonian dynamics: s + v + 1/2ma (a free needle: without
        its self-connection, which acts as a spring; see
        HomeoUnitNewtonianSpringTest), without drag, from a moving needle
        (the velocity does not stay 0).  With drag and
        other timesteps: HomeoUnitNewtonianIntegratorTest.
        """
        self.unit.disactivateSelfConn()
        self.unit.viscosity = 0
        for i in range(1000):
            torque = numpy.random.uniform(-1,1)
            self.unit.needleUnit.mass = numpy.random.uniform(1,10000)
            self.unit.criticalDeviation = numpy.random.uniform(-5, 5)
            self.unit.currentVelocity = numpy.random.uniform(-1, 1)
            oldDev = self.unit.criticalDeviation
            oldVelocity = self.unit.currentVelocity
            newDev = self.unit.newLinearNeedlePosition(torque)
            "Check the computation is correct according to Newtonian dynamics"
            self.assertAlmostEqual(newDev, oldDev + oldVelocity + (1/2. * (torque / self.unit.needleUnit.mass)),
                                   places=12)
            self.assertEqual(self.unit.criticalDeviation, oldDev)

    def testComputeNextVelocityWithoutConnections(self):
        """
        Test computation of velocity according to Newtonian laws , NO connections
        (not even the self-connection, a spring: see HomeoUnitNewtonianSpringTest)
        """
        errorTolerance = 10**-13 
        testRuns = 1000
        self.unit.disactivateSelfConn()
        self.unit.criticalDeviation = 0
        self.unit.noise = 0
        self.unit.currentOutput = 0.1
        self.unit.inputConnections[0].noise = 0
        
        for index in range(testRuns):
            self.unit.needleUnit.mass = numpy.random.uniform(1,1000)
            oldVelocity = self.unit.currentVelocity
            
            "compute the torque as sum of the output coming from connected units"
            unitActiveInputs = [activeConn.output() for activeConn in self.unit.inputConnections if activeConn.isActive() and activeConn.incomingUnit.isActive()]
            torque = reduce(lambda x,y: x+y, unitActiveInputs, 0.0)
            
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
        parameter: Drag = - viscosity * velocity * |velocity|: it opposes the
        velocity, whichever its sign.
        """
        errorTolerance = 0.000000001
        testRuns = 1000

        "When the unit is started, velocity is zero, and dragForce should be zero"
        self.unit.currentVelocity = 0
        for i in range(testRuns):
            self.unit.viscosity = numpy.random.uniform(0, 10)
            dragForce = self.unit.dragEquationDrag()
            self.assertEqual(dragForce, 0)

        '''When Velocity is not zero, Drag = -viscosity * velocity * |velocity|'''

        for index in range(testRuns):
            self.unit.currentVelocity = numpy.random.uniform(-10, 10)
            self.unit.viscosity = numpy.random.uniform(0, 10)

            dragForce = self.unit.dragEquationDrag()
            expectedDrag = -self.unit.viscosity * self.unit.currentVelocity * abs(self.unit.currentVelocity)
            delta = abs(dragForce - expectedDrag)
            self.assertTrue(delta < errorTolerance)
            if self.unit.viscosity > 0:
                self.assertEqual(numpy.sign(dragForce), -numpy.sign(self.unit.currentVelocity))
            
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


class HomeoUnitNewtonianSpringTest(unittest.TestCase):
    """The self-connection as a spring, against the exact solution.

    A self-connection of signed weight W adds W x output to the torque, and
    between the stops the output is x / maxDeviation, so the needle obeys

        m x'' = F - k x - c x',   k = -W / maxDeviation

    a damped oscillator (k > 0, negative feedback) or an unstable one (k < 0).
    The step solves it exactly, so the unit must follow the solution at
    t = dt_fast, 2 dt_fast, ... whatever the damping: an undamped spring keeps
    its amplitude (the explicit step made it grow), an overdamped one relaxes
    without overshoot, positive feedback grows at its true rate.  Both paths.
    """

    def makeUnit(self, mass, viscosity, dtFast, selfWeight, torque, x0, headless):
        unit = HomeoUnitNewtonian()
        unit.noise = 0
        unit.uniselectorActive = False
        unit.needleUnit.mass = mass
        unit.viscosity = viscosity
        unit.dt_fast = dtFast
        unit.criticalDeviation = x0
        unit.computeOutput()
        unit.currentVelocity = 0
        selfConn = unit.inputConnections[0]
        selfConn.newWeight(selfWeight)
        selfConn.noise = 0
        selfConn.state = 'manual'
        driver = HomeoUnit()
        driver.currentOutput = 1.0
        unit.addConnectionWithRandomValues(driver)
        drive = unit.inputConnections[-1]
        drive.newWeight(torque)
        drive.noise = 0
        drive.state = 'manual'
        unit._headless = headless
        unit._jit_dirty = True
        self.driver = driver                    # keep the driving unit alive
        return unit

    @staticmethod
    def exact(mass, viscosity, stiffness, torque, x0, t):
        "x(t), v(t) of m x'' = F - k x - c x', x(0) = x0, v(0) = 0"
        from scipy.linalg import expm
        a = numpy.array([[0.0, 1.0, 0.0],
                         [-stiffness / mass, -viscosity / mass, torque / mass],
                         [0.0, 0.0, 0.0]])
        x, v, _ = expm(a * t) @ numpy.array([x0, 0.0, 1.0])
        return x, v

    def checkTrajectory(self, headless):
        steps = 60
        for dtFast in (0.5, 1.0, 2.0):
            for mass, viscosity, selfWeight, torque, x0 in (
                    (1.0, 0.0, -0.9, 0.053, 0.0),       # undamped spring
                    (2.0, 0.3, -0.5, 0.02, 0.5),        # underdamped
                    (0.001, 0.1, -1.0, 0.05, 0.0),      # Ashby's regime, c dt / m >= 50
                    (5.0, 2.0, -0.2, -0.03, -0.4),      # overdamped
                    (1.0, 0.0, 0.02, 0.0, 0.01)):       # positive feedback
                unit = self.makeUnit(mass, viscosity, dtFast, selfWeight, torque, x0, headless)
                stiffness = -selfWeight / unit.maxDeviation
                for step in range(1, steps + 1):
                    unit.selfUpdate()
                    x, v = self.exact(mass, viscosity, stiffness, torque, x0, step * dtFast)
                    msg = "step %d, dt %s, m %s, visc %s, W %s" % (step, dtFast, mass,
                                                                   viscosity, selfWeight)
                    self.assertLess(abs(unit.criticalDeviation), unit.maxDeviation, msg)
                    self.assertAlmostEqual(unit.criticalDeviation, x, delta=1e-9, msg=msg)
                    self.assertAlmostEqual(unit.currentVelocity, v, delta=1e-9, msg=msg)

    def testTrajectoryPythonPath(self):
        self.checkTrajectory(headless=False)

    def testTrajectoryHeadlessPath(self):
        self.checkTrajectory(headless=True)

    @staticmethod
    def textbook(p, q, f, v0, t):
        """The textbook solution of u'' + p u' + q u = f, u(0) = 0, u'(0) = v0,
        case by case"""
        if q == 0:                                  # no spring: drag only
            if p == 0:
                return v0 * t + f * t * t / 2, v0 + f * t
            e = math.exp(-p * t)
            return (f / p * t + (v0 - f / p) * (1 - e) / p,
                    f / p + (v0 - f / p) * e)
        ueq = f / q
        a = -ueq                                    # u(0) - u_eq
        g = p / 2
        disc = g * g - q
        if abs(disc) < 1e-14:                       # critically damped
            b = v0 + g * a
            e = math.exp(-g * t)
            return ueq + e * (a + b * t), e * (b - g * (a + b * t))
        if disc < 0:                                # underdamped
            w = math.sqrt(-disc)
            b = (v0 + g * a) / w
            e = math.exp(-g * t)
            c, s = math.cos(w * t), math.sin(w * t)
            return (ueq + e * (a * c + b * s),
                    e * ((b * w - g * a) * c - (a * w + g * b) * s))
        r1, r2 = -g + math.sqrt(disc), -g - math.sqrt(disc)   # overdamped, or q < 0
        c2 = (v0 - r1 * a) / (r2 - r1)
        c1 = a - c2
        return (ueq + c1 * math.exp(r1 * t) + c2 * math.exp(r2 * t),
                c1 * r1 * math.exp(r1 * t) + c2 * r2 * math.exp(r2 * t))

    def testStepIsTheTextbookSolution(self):
        """_jit_spring_step, one formula, against the textbook's cases"""
        from Core.HomeoJIT import _jit_spring_step
        cases = {'underdamped': (0.2, 0.5), 'critically damped': (1.0, 0.25),
                 'overdamped': (3.0, 0.5), 'positive feedback': (0.1, -0.02),
                 'undamped': (0.0, 0.09), 'drag only': (0.4, 0.0),
                 'free': (0.0, 0.0), 'stiff (Ashby)': (100.0, 100.0)}
        for name, (p, q) in cases.items():
            for t in (0.5, 1.0, 7.0):
                with self.subTest(case=name, t=t):
                    u, v = _jit_spring_step(p, q, 0.05, 0.3, t)
                    ue, ve = self.textbook(p, q, 0.05, 0.3, t)
                    self.assertAlmostEqual(u, ue, delta=1e-10 * max(1.0, abs(ue)))
                    self.assertAlmostEqual(v, ve, delta=1e-10 * max(1.0, abs(ve)))

    def testUndampedSpringKeepsItsAmplitude(self):
        """An undamped needle on its self-connection, under a constant input,
        swings between its start and twice its equilibrium for good"""
        unit = self.makeUnit(1.0, 0.0, 1.0, -0.9, 0.053, 0.0, headless=True)
        equilibrium = 0.053 / (0.9 / unit.maxDeviation)
        positions = []
        for step in range(5000):
            unit.selfUpdate()
            positions.append(unit.criticalDeviation)
        self.assertLess(max(positions), 2 * equilibrium + 1e-9)
        self.assertGreater(max(positions[-200:]), 2 * equilibrium - 1e-3)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

class HomeoUnitNewtonianTimeScaleTest(unittest.TestCase):
    """dt_fast is a rescaling of the needle, not a time step: a unit with mass m, viscosity c and dt_fast dt moves exactly as
    one with m / dt**2, c / dt and dt_fast 1 -- with noise (per tick either
    way), the self-connection's spring and the stops.  Both paths."""

    def trajectory(self, mass, viscosity, dtFast, selfWeight, torque, x0, headless, seed):
        import random
        from Core.HomeoJIT import seed_jit_rng
        unit = HomeoUnitNewtonianSpringTest.makeUnit(self, mass, viscosity, dtFast,
                                                     selfWeight, torque, x0, headless)
        unit.noise = 0.05
        for conn in unit.inputConnections:
            conn.noise = 0.05
        numpy.random.seed(seed)
        random.seed(seed)
        seed_jit_rng(seed)                      # numba's own stream, headless
        positions = []
        for _ in range(200):
            unit.selfUpdate()
            positions.append(unit.criticalDeviation)
        return positions

    def check(self, headless):
        for dtFast in (0.3, 1.7):
            for mass, viscosity, selfWeight, torque, x0 in (
                    (2.0, 0.3, -0.5, 0.02, 0.5),        # underdamped
                    (5.0, 4.0, -0.2, -0.03, -0.4),      # overdamped
                    (1.0, 0.0, 0.05, 0.2, 0.0)):        # positive feedback, to the stop
                scaled = self.trajectory(mass / dtFast**2, viscosity / dtFast, 1.0,
                                         selfWeight, torque, x0, headless, seed=7)
                original = self.trajectory(mass, viscosity, dtFast,
                                           selfWeight, torque, x0, headless, seed=7)
                for tick, (a, b) in enumerate(zip(original, scaled)):
                    self.assertAlmostEqual(a, b, delta=1e-9,
                                           msg="tick %d, dt %s, m %s, c %s" % (tick, dtFast,
                                                                               mass, viscosity))

    def testPythonPath(self):
        self.check(headless=False)

    def testHeadlessPath(self):
        self.check(headless=True)

    def testANewtonianViscosityHasNoCeiling(self):
        "a drag coefficient; HomeoUnit's own viscosity stays capped at maxViscosity"
        unit = HomeoUnitNewtonian()
        unit.viscosity = 50.0
        self.assertEqual(unit.viscosity, 50.0)
        from Core.HomeoUnit import HomeoUnitError
        with self.assertRaises(HomeoUnitError):
            unit.viscosity = -1.0
        with self.assertRaises(HomeoUnitError):
            HomeoUnit().viscosity = 50.0


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
