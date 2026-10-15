'''
Created on Oct 13, 2026

@author: stefano

The weight-free GA setups (direct 2+2, 2_2_Full, 3c) honour the GA's
"No Uniselector" option (review finding SE-05): it used to be ignored, so a
GA run with it set still adapted every evolved unit's weights.
'''
from Simulator.SimulatorBackend import SimulatorBackendHOMEO
import Simulator.HomeoExperiments as HE

import tempfile
import threading
import unittest

import numpy as np

EXPERIMENTS = ['initializeBraiten2_direct_GA_continuous_weightfree_fixed',
               'initializeBraiten2_2_Full_GA_continuous_weightfree_fixed',
               'initializeBraiten3c_GA_continuous_weightfree_fixed',
               'initializeBraiten2_direct_GA_continuous_weightfree_fixed_v2',
               'initializeBraiten2_2_Full_GA_continuous_weightfree_fixed_v2',
               'initializeBraiten3c_GA_continuous_weightfree_fixed_v2']

V2 = ['initializeBraiten2_2_Full_GA_continuous_weightfree_v2',
      'initializeBraiten2_2_Full_GA_continuous_weightfree_fixed_v2',
      'initializeBraiten2_direct_GA_continuous_weightfree_v2',
      'initializeBraiten2_direct_GA_continuous_weightfree_fixed_v2',
      'initializeBraiten3c_GA_continuous_weightfree_fixed_v2',
      'initializeBraiten3c_GA_continuous_weightfree_open_v2']


class WeightfreeNoUniselTest(unittest.TestCase):

    def _build(self, name, **kwargs):
        tmp = tempfile.TemporaryDirectory()
        backend = SimulatorBackendHOMEO(lock=threading.Lock(), robotName='Khepera')
        backend.kheperaSimulation.dataDir = tmp.name
        self.addCleanup(tmp.cleanup)
        self.addCleanup(backend.quit)
        f = getattr(HE, name)
        return f(np.full(f.genomeSize, 0.5), backendSimulator=backend, **kwargs)

    def testNoUniselTurnsEveryUniselectorOff(self):
        for name in EXPERIMENTS:
            with self.subTest(name):
                hom = self._build(name, noUnisel=True)
                self.assertEqual([u.name for u in hom.homeoUnits if u.uniselectorActive], [])

    def testNoUniselKeepsTheWeights(self):
        for name in EXPERIMENTS:
            with self.subTest(name):
                hom = self._build(name, noUnisel=True)
                before = [c.weight for u in hom.homeoUnits for c in u.inputConnections]
                hom.runFor(50)      # not headless: the OU process acts on the connections
                self.assertEqual([c.weight for u in hom.homeoUnits for c in u.inputConnections],
                                 before)

    def testByDefaultTheEvolvedUnitsAdapt(self):
        for name in EXPERIMENTS:
            with self.subTest(name):
                hom = self._build(name)
                self.assertTrue(any(u.uniselectorActive for u in hom.homeoUnits))


class WeightfreeV2GenesTest(unittest.TestCase):
    """The _v2 setups (review finding CU-11): 4 genes per evolved unit, mass
    and viscosity log-uniform over [0.25, 250] and [0.05, 50], no dt_fast gene;
    the legacy setups decode as before"""

    @staticmethod
    def evolved(hom):
        return [u for u in hom.homeoUnits if u.uniselectorActive]

    def testV2Genes(self):
        for name in V2:
            f = getattr(HE, name)
            with self.subTest(name):
                self.assertEqual(f.genomeLayout, 'weightfree_v2')
                self.assertEqual(f.genomeSize, 4 * f.noEvolvedUnits)
                for gene, mass, viscosity in ((0.0, 0.25, 0.05), (0.5, 7.9057, 1.5811),
                                              (0.999999, 250.0, 50.0)):
                    hom = f(np.full(f.genomeSize, gene), backendSimulator=self._backend())
                    units = self.evolved(hom)
                    self.assertEqual(len(units), f.noEvolvedUnits)
                    for unit in units:
                        self.assertAlmostEqual(unit.mass, mass, delta=1e-3 * mass)
                        self.assertAlmostEqual(unit.viscosity, viscosity, delta=1e-3 * viscosity)
                        self.assertEqual(unit.dt_fast, 1.0)

    def testLegacyGenesAreUnchanged(self):
        "mass 1 + 9 g, viscosity 10 g, dt_fast 0.2 + 1.8 g"
        for name in ('initializeBraiten2_direct_GA_continuous_weightfree_fixed',
                     'initializeBraiten2_direct_GA_continuous_weightfree_fixed_dt'):
            f = getattr(HE, name)
            with self.subTest(name):
                hom = f(np.full(f.genomeSize, 0.5), backendSimulator=self._backend())
                for unit in self.evolved(hom):
                    self.assertAlmostEqual(unit.mass, 5.5)
                    self.assertAlmostEqual(unit.viscosity, 5.0)
                    self.assertAlmostEqual(unit.dt_fast, 1.1 if f.genomeSize == 10 else 1.0)

    def _backend(self):
        tmp = tempfile.TemporaryDirectory()
        backend = SimulatorBackendHOMEO(lock=threading.Lock(), robotName='Khepera')
        backend.kheperaSimulation.dataDir = tmp.name
        self.addCleanup(tmp.cleanup)
        self.addCleanup(backend.quit)
        return backend


if __name__ == '__main__':
    unittest.main()
