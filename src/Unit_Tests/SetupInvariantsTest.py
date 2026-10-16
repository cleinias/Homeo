'''
@author: stefano

Invariants of every Braitenberg setup, GA and phototaxis: each builds; a
connection under uniselector control belongs to a unit whose uniselector is
active (else nothing could ever change it); the
'manual' connections keep their signed weights through a run, with or
without the headless (JIT) loop, while the uniselectors do change theirs;
and the classic GA setups honour noUnisel (the weight-free ones:
WeightfreeGASetupTest).  The wiring of the fixed-weight vehicles is in
BraitenbergControlTest, the Ashby experiments' in AshbyExperimentsTest.

Which connections are 'manual' is the setups' business: the invariants hold
whatever it is.
'''
import os
import tempfile
import threading
import unittest

import numpy as np

import Simulator.HomeoExperiments as HE
from Simulator.SimulatorBackend import SimulatorBackendHOMEO
from HomeoExperiments.KheperaExperiments import phototaxis_braitenberg2_direct as D
from HomeoExperiments.KheperaExperiments import phototaxis_braitenberg2_Ashby as A

GA_SETUPS = sorted(n for n in dir(HE)
                   if n.startswith('initialize') and hasattr(getattr(HE, n), 'fitnessSign'))
CLASSIC_GA_SETUPS = [n for n in GA_SETUPS if not hasattr(getattr(HE, n), 'genomeSize')]
PHOTOTAXIS_SETUPS = [(mod, topology, unisel) for mod in (D, A)
                     for topology in ('fixed', 'random') for unisel in ('ashby', 'continuous')]
TICKS = 300


def signed(hom, state):
    "{(unit, source): signed weight} of the active connections in this state"
    return {(u.name, c.incomingUnit.name): c.weight * c.switch
            for u in hom.homeoUnits for c in u.inputConnections
            if c.status and c.state == state}


class SetupInvariantsTest(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = tmp.name
        os.environ['HOMEO_DATA_DIR'] = tmp.name
        self.addCleanup(os.environ.pop, 'HOMEO_DATA_DIR', None)

    def buildGA(self, name, **kw):
        f = getattr(HE, name)
        backend = SimulatorBackendHOMEO(lock=threading.Lock(), robotName='Khepera')
        backend.kheperaSimulation.dataDir = self.tmp
        self.addCleanup(backend.kheperaSimulation.saveTrajectory)
        # a classic genome: 4 genes per evolved unit, and a weight per connection
        size = getattr(f, 'genomeSize',
                       f.noEvolvedUnits * 4 + f.noEvolvedUnits * getattr(f, 'noUnits', 6))
        return f(np.random.default_rng(1).uniform(0, 1, size), backendSimulator=backend, **kw)

    def buildPhototaxis(self, mod, topology, unisel):
        hom, backend, _ = mod.setup_phototaxis(topology=topology, uniselector_type=unisel, seed=3)
        self.addCleanup(backend.kheperaSimulation.saveTrajectory)
        return hom

    def setups(self):
        "(label, a function building the setup)"
        for name in GA_SETUPS:
            yield name, lambda name=name: self.buildGA(name)
        for mod, topology, unisel in PHOTOTAXIS_SETUPS:
            yield ('%s %s %s' % (mod.__name__.rsplit('_', 1)[1], topology, unisel),
                   lambda m=mod, t=topology, u=unisel: self.buildPhototaxis(m, t, u))

    def runHomeostat(self, hom, headless):
        hom.slowingFactor = 0
        hom.collectsData = False
        hom._headless = headless
        for u in hom.homeoUnits:
            u._headless = headless
        hom.runFor(TICKS)
        for u in hom.homeoUnits:
            u.flushJitArrays()          # the headless loop's weights onto the connections

    def testEveryUniselectorConnectionHasAnActiveUniselector(self):
        for label, build in self.setups():
            with self.subTest(label):
                hom = build()
                units = {u.name: u for u in hom.homeoUnits}
                controlled = signed(hom, 'uniselector')
                self.assertTrue(controlled)
                for unit, source in controlled:
                    self.assertTrue(units[unit].uniselectorActive, (unit, source))

    def testManualConnectionsKeepTheirSignedWeights(self):
        adapted = {False: [], True: []}
        for label, build in self.setups():
            for headless in (False, True):
                with self.subTest(label, headless=headless):
                    hom = build()
                    manual, controlled = signed(hom, 'manual'), signed(hom, 'uniselector')
                    self.assertTrue(manual)
                    self.runHomeostat(hom, headless)
                    self.assertEqual(signed(hom, 'manual'), manual)
                    adapted[headless].append(signed(hom, 'uniselector') != controlled)
        for headless, runs in adapted.items():         # the runs did adapt, on each path
            with self.subTest(headless=headless):
                self.assertGreater(sum(runs), len(runs) // 4)

    def testClassicGASetupsHonourNoUnisel(self):
        for name in CLASSIC_GA_SETUPS:
            for headless in (False, True):
                with self.subTest(name, headless=headless):
                    hom = self.buildGA(name, noUnisel=True)
                    self.assertEqual([u.name for u in hom.homeoUnits if u.uniselectorActive], [])
                    before = signed(hom, 'uniselector')
                    self.runHomeostat(hom, headless)
                    self.assertEqual(signed(hom, 'uniselector'), before)


if __name__ == '__main__':
    unittest.main()
