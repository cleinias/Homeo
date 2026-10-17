'''
@author: stefano

Unit tests for HomeoUniselectorContinuous.
'''

from Core.HomeoUniselectorContinuous import HomeoUniselectorContinuous
from Core.HomeoUniselector import HomeoUniselector
from Core.HomeoConnection import HomeoConnection
from Core.HomeoUnitNewtonian import HomeoUnitNewtonian
from Helpers.General_Helper_Functions import withAllSubclasses

import math
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
        self.assertEqual(self.unis.model, 'diffusion')
        self.assertEqual(self.unis.tau_a, 1000.0)
        self.assertEqual(self.unis.sigma_base, 0.0)
        self.assertEqual(self.unis.sigma_crit, 1.0)
        self.assertAlmostEqual(self.unis.stress_exponent, 2.0)

    def testTwoModels(self):
        '''The models are 'diffusion' and 'ou'; a parameter they do not have is
        refused, through the phototaxis setups too'''
        self.assertEqual(HomeoUniselectorContinuous.MODELS, ('diffusion', 'ou'))
        from HomeoExperiments.KheperaExperiments.phototaxis_common import set_uniselector_type
        from Core.HomeoUnit import HomeoUnit
        with self.assertRaises(ValueError):
            set_uniselector_type(HomeoUnit(), 'continuous', {'drift': 0.5})

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

        self.unis.sigma_base = 0.01
        self.assertEqual(self.unis.sigma_base, 0.01)

        self.unis.sigma_crit = 0.5
        self.assertEqual(self.unis.sigma_crit, 0.5)

        self.unis.stress_exponent = 3.0
        self.assertEqual(self.unis.stress_exponent, 3.0)
        self.unis.stress_exponent = 0.0  # should be ignored
        self.assertEqual(self.unis.stress_exponent, 3.0)


class HomeoUniselectorContinuousModelsTest(unittest.TestCase):
    """The statistics of the two models (see HomeoUniselectorContinuous).

    'diffusion' and 'ou' have tau_a as their timescale and reflect at +-1.
    Many weights are stepped at once through step(); the tolerances are
    several standard errors wide.
    """

    WEIGHTS = 20000

    def walk(self, model, tau_a, stress, steps, w0=0.0, sigma_crit=None):
        unis = HomeoUniselectorContinuous()
        unis.model = model
        unis.tau_a = tau_a
        if sigma_crit is not None:
            unis.sigma_crit = sigma_crit
        w = np.full(self.WEIGHTS, float(w0))
        for i in range(steps):
            w = unis.step(w, stress, np.random.randn(self.WEIGHTS))
        return w

    def testDiffusionKeepsWeightsWithoutStress(self):
        "A stable unit keeps its weights exactly"
        unis = HomeoUniselectorContinuous()
        for w in (-0.7, 0.0, 0.42, 1.0):
            self.assertEqual(unis.evolve_weight(w, 0.0), w)

    def testDiffusionSpreadGrowsAsTimeOverTauA(self):
        "Short-time variance 2 sigma^2 t / tau_a: tau_a sets the speed of the search"
        for tau_a in (10000.0, 100000.0):
            w = self.walk('diffusion', tau_a, 1.0, 100)
            self.assertAlmostEqual(w.var() / (2 * 100 / tau_a), 1.0, delta=0.05)

    def testDiffusionFillsTheRangeWithoutAtoms(self):
        "Under stress the weights end uniform on [-1, 1], none stuck at the bounds"
        w = self.walk('diffusion', 100.0, 1.0, 1000, w0=0.5)
        self.assertEqual(np.sum(np.abs(w) == 1.0), 0)
        self.assertAlmostEqual(w.std(), 1 / np.sqrt(3), delta=0.01)
        self.assertAlmostEqual(w.mean(), 0.0, delta=0.02)

    def testOUDecaysOverTauA(self):
        "Without noise an 'ou' weight relaxes towards 0 with time constant tau_a"
        unis = HomeoUniselectorContinuous()
        unis.model = 'ou'
        unis.tau_a = 50.0
        w = 0.8
        for i in range(100):
            w = unis.evolve_weight(w, 0.0)
        self.assertAlmostEqual(w, 0.8 * (1 - 1 / 50.0) ** 100, places=12)

    def testOUStationarySpreadAndCorrelationTime(self):
        "Stationary sd sigma, autocorrelation e^-1 after tau_a ticks"
        tau_a, sigma = 50.0, 0.3
        w0 = self.walk('ou', tau_a, 1.0, 500, sigma_crit=sigma)     # 10 tau_a: stationary
        self.assertAlmostEqual(w0.std(), sigma, delta=0.01)
        unis = HomeoUniselectorContinuous()
        unis.model, unis.tau_a, unis.sigma_crit = 'ou', tau_a, sigma
        w = w0.copy()
        for i in range(int(tau_a)):
            w = unis.step(w, 1.0, np.random.randn(self.WEIGHTS))
        self.assertAlmostEqual(np.corrcoef(w0, w)[0, 1], np.exp(-1), delta=0.03)

    def testJitPathFollowsThePythonPath(self):
        "evolve_weights_jit and evolve_weight draw the same noise in the same order"
        signed = np.array([0.5, -0.3, 0.9, -1.0])
        for model in HomeoUniselectorContinuous.MODELS:
            unis = HomeoUniselectorContinuous()
            unis.model, unis.tau_a = model, 20.0
            state = np.random.get_state()
            python = [unis.evolve_weight(w, 0.8) for w in signed]
            np.random.set_state(state)
            weights, switches = np.abs(signed), np.sign(signed)
            unis.evolve_weights_jit(weights, switches, 0.8)
            np.testing.assert_allclose(weights * switches, python, rtol=0, atol=1e-15)

    def testUnknownModelIsRejected(self):
        with self.assertRaises(ValueError):
            HomeoUniselectorContinuous().model = 'brownian'


class ContinuousUniselectorFlagTest(unittest.TestCase):
    """An OU uniselector never fires: its unit's uniselectorActivated is 0,
    even if a discrete uniselector had left it at 1"""

    def testTheFlagIsCleared(self):
        from Core.HomeoUnit import HomeoUnit
        for cls in (HomeoUnit, HomeoUnitNewtonian):
            for headless in (False, True):
                with self.subTest(cls=cls.__name__, headless=headless):
                    unit = cls()
                    other = cls()
                    unit.addConnectionWithRandomValues(other)
                    unit.inputConnections[-1].state = 'uniselector'
                    unit.uniselector = HomeoUniselectorContinuous()
                    unit.uniselectorActive = True
                    unit._headless = headless
                    unit._jit_dirty = True
                    unit.uniselectorActivated = 1
                    unit.selfUpdate()
                    self.assertEqual(unit.uniselectorActivated, 0)


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

    def testUnitDtFastIsTheVerletStep(self):
        '''With dt_fast=1.0 and no viscosity, displacement is the
        Verlet-derived result, displacement = v + 0.5*a (implicit dt=1).
        With viscosity the step is the exact solution of
        m dv/dt = torque - viscosity * v (an explicit step would be unstable
        for viscosity * dt_fast / mass > 2).  A free needle: the self-connection,
        a spring, is off (see HomeoUnitNewtonianSpringTest).'''
        self.unit.disactivateSelfConn()
        self.unit.dt_fast = 1.0
        self.unit._criticalDeviation = 0.0
        self.unit._currentVelocity = 0.3
        self.unit._viscosity = 0.0
        self.unit._needleUnit._mass = 10.0
        torque = 2.0
        result = self.unit.newLinearNeedlePosition(torque)
        self.assertAlmostEqual(result, 0.3 + 0.5 * torque / 10.0, places=12)

        self.unit._viscosity = 0.5
        terminal = torque / 0.5
        expected_pos = terminal * 1.0 + (0.3 - terminal) * (10.0 / 0.5) * (1 - math.exp(-0.5 / 10.0))
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
