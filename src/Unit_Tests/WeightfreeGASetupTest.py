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
               'initializeBraiten3c_GA_continuous_weightfree_fixed']


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


if __name__ == '__main__':
    unittest.main()
