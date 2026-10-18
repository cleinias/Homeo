# Copyright (C) 2026 Stefano Franchi
#
# This file is part of Homeo, a simulation of Ashby's homeostat and of
# homeostat-controlled robots.
#
# Homeo is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# Homeo is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with Homeo.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

'''
GenomeDecoder against the GA setups it decodes.

Each setup builds a homeostat from a genome; decoding the same genome must
give the body parameters the setup gave its evolved units: masses,
viscosities, the continuous uniselector's tau_a and maxDeviations for the
weight-free layout; masses, viscosities, uniselector intervals and
maxDeviations for the classic one.
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


SETUPS = ['initializeBraiten2_2_Full_GA_continuous_weightfree_v2',
          'initializeBraiten2_2_Full_GA_continuous_weightfree_fixed_v2',
          'initializeBraiten2_direct_GA_continuous_weightfree_v2',
          'initializeBraiten2_direct_GA_continuous_weightfree_fixed_v2',
          'initializeBraiten3c_GA_continuous_weightfree_fixed_v2',
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
            self.assertEqual(layout, 'weightfree_v2', name)
            decoded = genomeDecoder(len(hom.homeoUnits), genome, noEvolvedUnits=evolved,
                                    layout=layout)
            perUnit = len(decoded) // evolved
            for i, unit in enumerate(hom.homeoUnits[:evolved]):
                actual = [unit.mass, unit.viscosity, unit.uniselector.tau_a, unit.maxDeviation]
                np.testing.assert_allclose(decoded[i * perUnit:(i + 1) * perUnit], actual,
                                           rtol=1e-12, err_msg='%s, unit %s' % (name, unit.name))
            self.assertTrue(all(0.25 <= unit.mass <= 250 for unit in hom.homeoUnits[:evolved]))

    def testUnitCountsMatchTheSetups(self):
        "A GA setup's noUnits (6 when undeclared) is the number of units it builds"
        names = [name for name in dir(HomeoExperiments) if name.startswith('initialize')
                 and hasattr(getattr(HomeoExperiments, name), 'noEvolvedUnits')]
        self.assertEqual(len(names), 10)
        for name in names:
            setup = getattr(HomeoExperiments, name)
            size = getattr(setup, 'genomeSize', CLASSIC_GENOME_SIZE)
            backend = SimulatorBackendHOMEO(lock=threading.Lock(), robotName='Khepera')
            hom = setup(np.random.uniform(0, 1, size), backendSimulator=backend,
                        dataDir=self.dataDir)
            self.assertEqual(getattr(setup, 'noUnits', 6), len(hom.homeoUnits), name)

    def testNoSetupTakesTransducers(self):
        "Each GA setup builds its own transducers: none takes them as an argument"
        import inspect
        for name in dir(HomeoExperiments):
            setup = getattr(HomeoExperiments, name)
            if name.startswith('initialize') and hasattr(setup, 'noEvolvedUnits'):
                self.assertNotIn('transducers', inspect.signature(setup).parameters, name)

    def testClassicDecoderMatchesTheSetups(self):
        "The uniselector interval is decoded as the whole number of ticks the unit uses"
        for name in CLASSIC_SETUPS:
            setup = getattr(HomeoExperiments, name)
            genome = np.random.uniform(0, 1, CLASSIC_GENOME_SIZE)
            backend = SimulatorBackendHOMEO(lock=threading.Lock(), robotName='Khepera')
            hom = setup(genome, backendSimulator=backend, dataDir=self.dataDir)
            evolved = setup.noEvolvedUnits
            decoded = genomeDecoder(len(hom.homeoUnits), genome, noEvolvedUnits=evolved,
                                    layout='classic')
            for i, unit in enumerate(hom.homeoUnits[:evolved]):
                actual = [unit.mass, unit.viscosity, unit.uniselectorTimeInterval, unit.maxDeviation]
                np.testing.assert_allclose(decoded[i * 4:(i + 1) * 4], actual,
                                           rtol=1e-12, err_msg='%s, unit %s' % (name, unit.name))
                self.assertIsInstance(decoded[i * 4 + 2], int)
