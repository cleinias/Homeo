'''
GenomeDecoder against the GA setups it decodes.

Each setup builds a homeostat from a genome; decoding the same genome must
give the body parameters the setup gave its evolved units: masses,
viscosities, OU timescales, maxDeviations and dt_fast for the weight-free
layouts; masses, viscosities, uniselector intervals and maxDeviations for
the classic one.
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
          'initializeBraiten3c_GA_continuous_weightfree_fixed',
          'initializeBraiten2_2_Full_GA_continuous_weightfree_fixed_v2',
          'initializeBraiten2_direct_GA_continuous_weightfree_v2',
          'initializeBraiten3c_GA_continuous_weightfree_open_v2']

CLASSIC_SETUPS = ['initializeBraiten2_2_Full_GA',
                  'initializeBraiten2_2_Full_GA_phototaxis',
                  'initializeBraiten2_2_Full_GA_scototaxis']
CLASSIC_GENOME_SIZE = 40            # 4 units x 4 body parameters + 4 x 6 weights


class GenomeDecoderRoundTripTest(unittest.TestCase):

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
            layout = setup.genomeLayout
            decoded = genomeDecoder(len(hom.homeoUnits), genome, noEvolvedUnits=evolved,
                                    layout=layout)
            perUnit = len(decoded) // evolved
            for i, unit in enumerate(hom.homeoUnits[:evolved]):
                actual = [unit.mass, unit.viscosity, unit.uniselector.tau_a, unit.maxDeviation]
                if layout == 'weightfree_dt':
                    actual += [unit.dt_fast, unit.mass / unit.dt_fast ** 2,
                               unit.viscosity / unit.dt_fast]
                np.testing.assert_allclose(decoded[i * perUnit:(i + 1) * perUnit], actual,
                                           rtol=1e-12, err_msg='%s, unit %s' % (name, unit.name))
            low, high = (0.25, 250) if layout == 'weightfree_v2' else (1, 10)
            self.assertTrue(all(low <= unit.mass <= high for unit in hom.homeoUnits[:evolved]))

    def testClassicDecoderMatchesTheSetups(self):
        "The uniselector interval is decoded as the whole number of ticks the unit uses"
        for name in CLASSIC_SETUPS:
            setup = getattr(HomeoExperiments, name)
            genome = np.random.uniform(0, 1, CLASSIC_GENOME_SIZE)
            backend = SimulatorBackendHOMEO(lock=threading.Lock(), robotName='Khepera')
            transducers = HomeoExperiments.basicBraiten2Tranducers(
                backend, 'kheperaBraitenberg2_HOMEO_World')
            hom = setup(genome, backendSimulator=backend, dataDir=self.dataDir,
                        transducers=transducers)
            evolved = setup.noEvolvedUnits
            decoded = genomeDecoder(len(hom.homeoUnits), genome, noEvolvedUnits=evolved,
                                    layout='classic')
            for i, unit in enumerate(hom.homeoUnits[:evolved]):
                actual = [unit.mass, unit.viscosity, unit.uniselectorTimeInterval, unit.maxDeviation]
                np.testing.assert_allclose(decoded[i * 4:(i + 1) * 4], actual,
                                           rtol=1e-12, err_msg='%s, unit %s' % (name, unit.name))
                self.assertIsInstance(decoded[i * 4 + 2], int)
