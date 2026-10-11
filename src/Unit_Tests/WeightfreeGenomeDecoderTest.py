'''
GenomeDecoder against the weight-free GA setups it decodes.

Each setup builds a homeostat from a genome; decoding the same genome must
give the masses, viscosities, OU timescales, maxDeviations and dt_fast that
the setup gave its evolved units.
'''
import os
import shutil
import tempfile
import threading
import unittest

import numpy as np

import Simulator.HomeoExperiments as HomeoExperiments
from Simulator.SimulatorBackend import SimulatorBackendHOMEO
from Helpers.GenomeDecoder import genomeDecoder


SETUPS = ['initializeBraiten2_2_Full_GA_continuous_weightfree',
          'initializeBraiten2_2_Full_GA_continuous_weightfree_fixed_dt',
          'initializeBraiten2_direct_GA_continuous_weightfree',
          'initializeBraiten2_direct_GA_continuous_weightfree_fixed_dt',
          'initializeBraiten3c_GA_continuous_weightfree_fixed']


class WeightfreeGenomeDecoderTest(unittest.TestCase):

    def setUp(self):
        self.dataDir = tempfile.mkdtemp()
        self.oldDataDir = os.environ.get('HOMEO_DATA_DIR')
        os.environ['HOMEO_DATA_DIR'] = self.dataDir

    def tearDown(self):
        if self.oldDataDir is None:
            os.environ.pop('HOMEO_DATA_DIR', None)
        else:
            os.environ['HOMEO_DATA_DIR'] = self.oldDataDir
        shutil.rmtree(self.dataDir, ignore_errors=True)

    def testDecoderMatchesTheSetups(self):
        for name in SETUPS:
            setup = getattr(HomeoExperiments, name)
            genome = np.random.uniform(0, 1, setup.genomeSize)
            backend = SimulatorBackendHOMEO(lock=threading.Lock(), robotName='Khepera')
            hom = setup(genome, backendSimulator=backend, dataDir=self.dataDir)
            evolved = setup.noEvolvedUnits
            perUnit = setup.genomeSize // evolved
            decoded = genomeDecoder(len(hom.homeoUnits), genome, noEvolvedUnits=evolved,
                                    layout='weightfree_dt' if perUnit == 5 else 'weightfree')
            for i, unit in enumerate(hom.homeoUnits[:evolved]):
                actual = [unit.mass, unit.viscosity, unit.uniselector.tau_a, unit.maxDeviation]
                if perUnit == 5:
                    actual.append(unit.dt_fast)
                np.testing.assert_allclose(decoded[i * perUnit:(i + 1) * perUnit], actual,
                                           rtol=1e-12, err_msg='%s, unit %s' % (name, unit.name))
            self.assertTrue(all(1 <= unit.mass <= 10 for unit in hom.homeoUnits[:evolved]))
