'''
Created on Oct 13, 2026

@author: stefano

The classic GA setup, initializeBraiten2_2_Full_GA, builds the homeostat its
genome describes (review finding SE-09).
'''
from Core.HomeoUnit import HomeoUnitError
from Simulator.SimulatorBackend import SimulatorBackendHOMEO
from Simulator.HomeoExperiments import initializeBraiten2_2_Full_GA

import tempfile
import threading
import unittest

import numpy as np


class ClassicGASetupTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.backend = SimulatorBackendHOMEO(lock=threading.Lock(), robotName='Khepera')
        self.backend.kheperaSimulation.dataDir = self.tmp.name
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self.backend.quit)

    def testUnitGenesAreSlicedByNoHomeoParameters(self):
        # 4 units x 5 parameters, then the connections: the connection offset
        # used 5, the unit slices 4, so the genome was silently misread (SE-09)
        genome = np.random.random(4 * 5 + 4 * 6)
        with self.assertRaises(HomeoUnitError):
            initializeBraiten2_2_Full_GA(genome, noHomeoParameters=5,
                                         backendSimulator=self.backend)

    def testUnitGenesAreTheFirstOnes(self):
        genome = np.random.random(4 * 4 + 4 * 6)
        hom = initializeBraiten2_2_Full_GA(genome, backendSimulator=self.backend)
        for i, unit in enumerate(hom.homeoUnits[:4]):
            self.assertEqual(unit.mass, unit.massFromWeight(genome[4 * i]))


if __name__ == '__main__':
    unittest.main()
