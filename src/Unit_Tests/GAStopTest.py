'''
Created on Oct 14, 2026

@author: stefano

Stopping a GA run during a generation, and a crash in one (review findings
SG-01, SG-04): the run ends cleanly or re-raises, and what was evaluated is
saved.
'''
import contextlib
import glob
import io
import os
import pickle
import tempfile
import unittest

from Simulator.HomeoGenAlg import HomeoGASimulation

EXP = 'initializeBraiten2_direct_GA_continuous_weightfree_fixed_dt'


class GAStopTest(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = HomeoGASimulation.dataDirRoot
        HomeoGASimulation.dataDirRoot = tmp.name
        self.addCleanup(setattr, HomeoGASimulation, 'dataDirRoot', root)

    def ga(self, onCall):
        "A small serial GA whose k-th evaluation calls onCall(ga, k) first."
        with contextlib.redirect_stdout(io.StringIO()):
            ga = HomeoGASimulation(stepsSize=20, popSize=6, generSize=3, exp=EXP,
                                   simulatorBackend='HOMEO')
        evaluate, calls = ga.toolbox.evaluate, [0]

        def counting(ind):
            calls[0] += 1
            onCall(ga, calls[0])
            return evaluate(ind)
        ga.toolbox.register('evaluate', counting)
        return ga

    def savedLogbook(self, ga):
        paths = glob.glob(os.path.join(ga.dataDir, 'Logbook-*.lgb'))
        self.assertEqual(len(paths), 1, paths)
        with open(paths[0], 'rb') as f:
            return pickle.load(f)

    def testStopDuringAGeneration(self):
        '''Stop during generation 1's evaluations: the run ends without an
        error, the population is generation 0's, evaluated, and the logbook
        with every evaluation is saved.'''
        def stopOnTheEighth(ga, k):
            if k == 8:
                ga._stopRequested = True
        ga = self.ga(stopOnTheEighth)
        with contextlib.redirect_stdout(io.StringIO()):
            pop = ga.generateRandomPop(randomSeed=1)
            ga.runGaSimulation(pop)
        self.assertTrue(all(ind.fitness.valid for ind in pop))
        self.assertTrue(all(ind.ID.startswith('0') for ind in pop))
        logbook = self.savedLogbook(ga)
        self.assertEqual(len([r for r in logbook if 'indivId' in r]), 8)
        self.assertEqual([r['gen'] for r in logbook if 'gen' in r], [0])


    def testACrashInGenerationOneKeepsGenerationZero(self):
        '''A crash during generation 1 re-raises, and the logbook saved has
        generation 0's evaluations and statistics (SG-04).'''
        def crashOnTheEighth(ga, k):
            if k == 8:
                raise RuntimeError('simulated crash in generation 1')
        ga = self.ga(crashOnTheEighth)
        with contextlib.redirect_stdout(io.StringIO()):
            pop = ga.generateRandomPop(randomSeed=1)
            with self.assertRaises(RuntimeError):
                ga.runGaSimulation(pop)
        logbook = self.savedLogbook(ga)
        self.assertEqual(len([r for r in logbook if 'indivId' in r]), 7)
        self.assertEqual([r['gen'] for r in logbook if 'gen' in r], [0])


if __name__ == '__main__':
    unittest.main()
