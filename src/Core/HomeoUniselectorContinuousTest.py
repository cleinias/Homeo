'''
Created on Feb 26, 2026

@author: stefano

Unit tests for HomeoUniselectorContinuous.
'''

from Core.HomeoUniselectorContinuous import HomeoUniselectorContinuous
from Core.HomeoUniselector import HomeoUniselector
from Core.HomeoConnection import HomeoConnection
from Core.HomeoUnitNewtonian import HomeoUnitNewtonian
from Helpers.General_Helper_Functions import withAllSubclasses

import unittest
import numpy as np


class HomeoUniselectorContinuousTest(unittest.TestCase):

    def setUp(self):
        self.unis = HomeoUniselectorContinuous()

    def tearDown(self):
        pass

    def testIsSubclassOfUniselector(self):
        '''HomeoUniselectorContinuous should be recognized as a uniselector type'''
        self.assertTrue(HomeoUniselector.includesType('HomeoUniselectorContinuous'))
        self.assertIsInstance(self.unis, HomeoUniselector)

    def testDefaultParameters(self):
        '''Check that default parameters are set correctly'''
        self.assertEqual(self.unis.tau_a, 1000.0)
        self.assertEqual(self.unis.theta, 0.01)
        self.assertEqual(self.unis.sigma_base, 0.001)
        self.assertEqual(self.unis.sigma_crit, 0.1)
        self.assertAlmostEqual(self.unis.stress_exponent, 2.0)

    def testSigmaAtZeroStress(self):
        '''At zero stress, sigma should equal sigma_base'''
        self.assertAlmostEqual(self.unis.sigma(0.0), self.unis.sigma_base)

    def testSigmaAtFullStress(self):
        '''At full stress, sigma should equal sigma_crit'''
        self.assertAlmostEqual(self.unis.sigma(1.0), self.unis.sigma_crit)

    def testSigmaMonotonic(self):
        '''Sigma should increase monotonically with stress level'''
        prev = self.unis.sigma(0.0)
        for s in np.linspace(0.01, 1.0, 50):
            current = self.unis.sigma(s)
            self.assertGreaterEqual(current, prev)
            prev = current

    def testSigmaClampsInput(self):
        '''Sigma should clamp stress values outside [0, 1]'''
        self.assertAlmostEqual(self.unis.sigma(-0.5), self.unis.sigma(0.0))
        self.assertAlmostEqual(self.unis.sigma(1.5), self.unis.sigma(1.0))

    def testEvolveWeightStaysInBounds(self):
        '''Evolved weight should always be in [-1, 1]'''
        for _ in range(1000):
            w = np.random.uniform(-1.0, 1.0)
            stress = np.random.uniform(0.0, 1.0)
            w_new = self.unis.evolve_weight(w, stress)
            self.assertGreaterEqual(w_new, -1.0)
            self.assertLessEqual(w_new, 1.0)

    def testEvolveWeightMeanReverts(self):
        '''Over many steps at zero stress, weights should drift toward 0
        (mean reversion due to theta term)'''
        # Use aggressive parameters so decay is visible:
        # drift per step = -(theta/tau_a) * w = -1.0 * w * dt
        # decay factor per step = (1 - 1.0) would be too much; use theta/tau_a = 0.01
        # so after 500 steps: (1-0.01)^500 ≈ exp(-5) ≈ 0.007
        unis = HomeoUniselectorContinuous()
        unis.sigma_base = 0.0  # no noise, pure drift
        unis.sigma_crit = 0.0
        unis.theta = 1.0       # strong mean reversion
        unis.tau_a = 100.0     # theta/tau_a = 0.01 per step
        w = 0.9
        for _ in range(500):
            w = unis.evolve_weight(w, 0.0)
        self.assertAlmostEqual(w, 0.0, places=1)

    def testEvolveWeightHighStressIncreasesVariance(self):
        '''At high stress, weight changes should be larger on average'''
        deltas_low = []
        deltas_high = []
        for _ in range(5000):
            w = 0.0
            w_new_low = self.unis.evolve_weight(w, 0.0)
            w_new_high = self.unis.evolve_weight(w, 1.0)
            deltas_low.append(abs(w_new_low - w))
            deltas_high.append(abs(w_new_high - w))
        self.assertGreater(np.mean(deltas_high), np.mean(deltas_low))

    def testEvolveWeightsJitInPlace(self):
        '''evolve_weights_jit should modify arrays in place'''
        weights = np.array([0.5, 0.3, 0.8], dtype=np.float64)
        switches = np.array([1.0, -1.0, 1.0], dtype=np.float64)
        weights_orig = weights.copy()
        switches_orig = switches.copy()

        # With high stress and many steps, values should change
        for _ in range(100):
            self.unis.evolve_weights_jit(weights, switches, 1.0)

        # At least some values should have changed
        changed = not (np.allclose(weights, weights_orig) and
                       np.allclose(switches, switches_orig))
        self.assertTrue(changed)

        # All weights should still be in [0, 1] and switches in {-1, 1}
        self.assertTrue(np.all(weights >= 0.0))
        self.assertTrue(np.all(weights <= 1.0))
        self.assertTrue(np.all(np.isin(switches, [-1.0, 1.0])))

    def testAdvanceIsNoop(self):
        '''advance() should not raise'''
        self.unis.advance()  # should be a no-op

    def testProduceNewValueFallback(self):
        '''produceNewValue should return a value in [-1, 1] for compatibility'''
        for _ in range(100):
            v = self.unis.produceNewValue()
            self.assertGreaterEqual(v, -1.0)
            self.assertLessEqual(v, 1.0)

    def testPropertySetters(self):
        '''Properties should accept valid values and reject invalid ones'''
        self.unis.tau_a = 500.0
        self.assertEqual(self.unis.tau_a, 500.0)
        self.unis.tau_a = -1.0  # should be ignored
        self.assertEqual(self.unis.tau_a, 500.0)

        self.unis.theta = 0.05
        self.assertEqual(self.unis.theta, 0.05)
        self.unis.theta = -0.1  # should be ignored
        self.assertEqual(self.unis.theta, 0.05)

        self.unis.sigma_base = 0.01
        self.assertEqual(self.unis.sigma_base, 0.01)

        self.unis.sigma_crit = 0.5
        self.assertEqual(self.unis.sigma_crit, 0.5)

        self.unis.stress_exponent = 3.0
        self.assertEqual(self.unis.stress_exponent, 3.0)
        self.unis.stress_exponent = 0.0  # should be ignored
        self.assertEqual(self.unis.stress_exponent, 3.0)


class HomeoUnitStressLevelTest(unittest.TestCase):
    '''Test the stressLevel method on HomeoUnit'''

    def testStressLevelAtEquilibrium(self):
        '''At zero deviation, stress should be 0'''
        unit = HomeoUnitNewtonian()
        unit._criticalDeviation = 0.0
        self.assertAlmostEqual(unit.stressLevel(), 0.0)

    def testStressLevelAtMax(self):
        '''At max deviation, stress should be 1'''
        unit = HomeoUnitNewtonian()
        unit._criticalDeviation = unit.maxDeviation
        self.assertAlmostEqual(unit.stressLevel(), 1.0)

    def testStressLevelAtNegativeMax(self):
        '''At negative max deviation, stress should be 1'''
        unit = HomeoUnitNewtonian()
        unit._criticalDeviation = unit.minDeviation
        self.assertAlmostEqual(unit.stressLevel(), 1.0)

    def testStressLevelIntermediate(self):
        '''At half max deviation, stress should be 0.5'''
        unit = HomeoUnitNewtonian()
        unit._criticalDeviation = unit.maxDeviation / 2.0
        self.assertAlmostEqual(unit.stressLevel(), 0.5)


class HomeoUnitDtFastTest(unittest.TestCase):
    '''Test dt_fast property on HomeoUnitNewtonian'''

    def setUp(self):
        self.unit = HomeoUnitNewtonian()

    def testDefaultDtFast(self):
        '''Default dt_fast should be 1.0'''
        self.assertEqual(self.unit.dt_fast, 1.0)

    def testSetDtFast(self):
        '''dt_fast setter should accept positive values'''
        self.unit.dt_fast = 0.5
        self.assertEqual(self.unit.dt_fast, 0.5)

    def testRejectNonPositiveDtFast(self):
        '''dt_fast setter should reject non-positive values'''
        self.unit.dt_fast = 0.5
        self.unit.dt_fast = 0
        self.assertEqual(self.unit.dt_fast, 0.5)
        self.unit.dt_fast = -1.0
        self.assertEqual(self.unit.dt_fast, 0.5)

    def testBackwardsCompatibility(self):
        '''With dt_fast=1.0, displacement formula should match the old Verlet-derived result.
        Old: displacement = v + 0.5*a (implicit dt=1)
        New: displacement = v*dt_fast + 0.5*a*dt_fast^2 = v + 0.5*a when dt_fast=1'''
        self.unit.dt_fast = 1.0
        self.unit._criticalDeviation = 0.0
        self.unit._currentVelocity = 0.3
        self.unit._viscosity = 0.5
        self.unit._needleUnit._mass = 10.0

        torque = 2.0
        drag = -0.5 * 0.3  # -viscosity * velocity
        total_force = torque + drag
        acceleration = total_force / 10.0
        expected_displacement = 0.3 * 1.0 + 0.5 * acceleration * 1.0**2
        expected_pos = 0.0 + expected_displacement

        result = self.unit.newLinearNeedlePosition(torque)
        self.assertAlmostEqual(result, expected_pos, places=10)

    def testDisplacementScalesWithDtFast(self):
        '''Displacement should scale with dt_fast: smaller dt_fast -> smaller displacement'''
        self.unit._criticalDeviation = 0.0
        self.unit._currentVelocity = 0.3
        self.unit._viscosity = 0.5
        self.unit._needleUnit._mass = 10.0

        self.unit.dt_fast = 1.0
        pos_dt1 = self.unit.newLinearNeedlePosition(2.0)

        self.unit._criticalDeviation = 0.0
        self.unit._currentVelocity = 0.3
        self.unit.dt_fast = 0.5
        pos_dt05 = self.unit.newLinearNeedlePosition(2.0)

        # With smaller dt_fast, displacement should be smaller
        self.assertLess(abs(pos_dt05), abs(pos_dt1))


class HomeoUnitConversionFunctionsTest(unittest.TestCase):
    '''Test tauAFromWeight and dtFastFromWeight class methods'''

    def testTauAFromWeightBoundaries(self):
        '''tauAFromWeight(0) = 100, tauAFromWeight(1) = 10000'''
        from Core.HomeoUnit import HomeoUnit
        self.assertAlmostEqual(HomeoUnit.tauAFromWeight(0.0), 100.0)
        self.assertAlmostEqual(HomeoUnit.tauAFromWeight(1.0), 10000.0)

    def testTauAFromWeightMonotonic(self):
        '''tauAFromWeight should be monotonically increasing'''
        from Core.HomeoUnit import HomeoUnit
        prev = HomeoUnit.tauAFromWeight(0.0)
        for p in np.linspace(0.01, 1.0, 50):
            current = HomeoUnit.tauAFromWeight(p)
            self.assertGreater(current, prev)
            prev = current

    def testTauAFromWeightMidpoint(self):
        '''tauAFromWeight(0.5) should be geometric mean of 100 and 10000 = 1000'''
        from Core.HomeoUnit import HomeoUnit
        self.assertAlmostEqual(HomeoUnit.tauAFromWeight(0.5), 1000.0)

    def testDtFastFromWeightBoundaries(self):
        '''dtFastFromWeight(0) = 0.2, dtFastFromWeight(1) = 2.0'''
        from Core.HomeoUnit import HomeoUnit
        self.assertAlmostEqual(HomeoUnit.dtFastFromWeight(0.0), 0.2)
        self.assertAlmostEqual(HomeoUnit.dtFastFromWeight(1.0), 2.0)

    def testDtFastFromWeightMonotonic(self):
        '''dtFastFromWeight should be monotonically increasing'''
        from Core.HomeoUnit import HomeoUnit
        prev = HomeoUnit.dtFastFromWeight(0.0)
        for p in np.linspace(0.01, 1.0, 50):
            current = HomeoUnit.dtFastFromWeight(p)
            self.assertGreater(current, prev)
            prev = current

    def testDtFastFromWeightMidpoint(self):
        '''dtFastFromWeight(0.5) should be 1.1 (linear midpoint of [0.2, 2.0])'''
        from Core.HomeoUnit import HomeoUnit
        self.assertAlmostEqual(HomeoUnit.dtFastFromWeight(0.5), 1.1)


if __name__ == "__main__":
    unittest.main()
