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
The weight-free GA setups (direct 2+2, 2_2_Full, 3c) honour the GA's
"No Uniselector" option: a GA run with it set does not adapt the evolved
units' weights.
'''
from Simulator.SimulatorBackend import SimulatorBackendHOMEO
import Simulator.HomeoExperiments as HE

import tempfile
import threading
import unittest

import numpy as np

EXPERIMENTS = ['initializeBraiten2_direct_GA_continuous_weightfree_fixed_v2',
               'initializeBraiten2_2_Full_GA_continuous_weightfree_fixed_v2',
               'initializeBraiten3c_GA_continuous_weightfree_fixed_v2']

V2 = ['initializeBraiten2_2_Full_GA_continuous_weightfree_v2',
      'initializeBraiten2_2_Full_GA_continuous_weightfree_fixed_v2',
      'initializeBraiten2_direct_GA_continuous_weightfree_v2',
      'initializeBraiten2_direct_GA_continuous_weightfree_fixed_v2',
      'initializeBraiten3c_GA_continuous_weightfree_fixed_v2',
      'initializeBraiten3c_GA_continuous_weightfree_open_v2',
      'initializeHungerPhototaxis_GA_continuous_weightfree_fixed_v2',
      'initializeHunger3c_GA_continuous_weightfree_fixed_v2']


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
                hom.runFor(50)      # not headless: the continuous uniselector acts on the connections
                self.assertEqual([c.weight for u in hom.homeoUnits for c in u.inputConnections],
                                 before)

    def testByDefaultTheEvolvedUnitsAdapt(self):
        for name in EXPERIMENTS:
            with self.subTest(name):
                hom = self._build(name)
                self.assertTrue(any(u.uniselectorActive for u in hom.homeoUnits))


class WeightfreeV2GenesTest(unittest.TestCase):
    """The weight-free setups: 4 genes per evolved unit, mass and viscosity
    log-uniform over [0.25, 250] and [0.05, 50], no dt_fast gene"""

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

    def testTheWeightfreeSetupsAreTheV2Ones(self):
        "Every weight-free GA setup has the 'weightfree_v2' layout"
        names = [n for n in dir(HE) if n.startswith('initialize') and 'weightfree' in n]
        self.assertEqual(sorted(names), sorted(V2))
        self.assertEqual(HE.WEIGHTFREE_GENES_PER_UNIT, {'weightfree_v2': 4})

    def _backend(self):
        tmp = tempfile.TemporaryDirectory()
        backend = SimulatorBackendHOMEO(lock=threading.Lock(), robotName='Khepera')
        backend.kheperaSimulation.dataDir = tmp.name
        self.addCleanup(tmp.cleanup)
        self.addCleanup(backend.quit)
        return backend


class GALightTest(unittest.TestCase):
    """The GA phototaxis setups' TARGET is a light, +100, as their names say
    and the phototaxis CLIs use; lightIntensity=-100 makes it a darkness
    source, and a replay takes the intensity its logbook records"""

    SETUPS = ['initializeBraiten2_2_Full_GA_phototaxis',
              'initializeBraiten2_2_Full_GA_phototaxis_continuous'] + V2

    def _backend(self):
        return WeightfreeV2GenesTest._backend(self)

    def _target(self, name, **kwargs):
        f = getattr(HE, name)
        backend = self._backend()
        f(np.full(getattr(f, 'genomeSize', 40), 0.5), backendSimulator=backend, **kwargs)
        return backend.kheperaSimulation.allBodies['TARGET'].userData

    def testTheTargetIsALight(self):
        for name in self.SETUPS:
            with self.subTest(name):
                target = self._target(name)
                self.assertEqual(target['intensity'], 100)
                self.assertEqual(getattr(HE, name).lightIntensity, 100)

    def testADarknessSourceOnRequest(self):
        for name in ('initializeBraiten2_2_Full_GA_phototaxis',
                     'initializeBraiten2_direct_GA_continuous_weightfree_fixed_v2',
                     'initializeBraiten3c_GA_continuous_weightfree_fixed_v2'):
            with self.subTest(name):
                self.assertEqual(self._target(name, lightIntensity=-100)['intensity'], -100)

    def testAReplayTakesTheLoggedLight(self):
        logged = HE.loggedLightIntensity
        for name in ('initializeBraiten2_2_Full_GA_phototaxis',
                     'initializeBraiten2_direct_GA_continuous_weightfree_fixed_v2'):
            with self.subTest(name):
                self.assertEqual(logged(name, {'lightIntensity': -100}), -100)
                self.assertEqual(logged(name, {'lightIntensity': 100}), 100)
                for meta in (None, {}, {'exp': name}):
                    with self.assertRaisesRegex(ValueError, 'records no light intensity'):
                        logged(name, meta)

if __name__ == '__main__':
    unittest.main()
