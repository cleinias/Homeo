'''
Created on Oct 2, 2026

@author: stefano

Reproducible GA runs: every fitness evaluation is seeded from the GA's seed by
the run's noise scheme (see Simulator/HomeoGenAlg.py, "Reproducible
evaluations").  The fast tests check the seed derivation and the seeding
helpers; the slow ones run small GAs end to end, for each noise scheme, and
check that a seed reproduces a run exactly, with one worker or two.
'''
from Simulator.HomeoGenAlg import (evaluation_seed, seeded_evaluation, NOISE_SCHEMES,
                                   HomeoGASimulation)

import json
import multiprocessing
import os
import random
import subprocess
import sys
import tempfile
import unittest

import numpy as np


class Ind(list):
    "Stands in for a DEAP individual: a genome with an ID"
    def __init__(self, genome, ID):
        super().__init__(genome)
        self.ID = ID


class EvaluationSeedTest(unittest.TestCase):
    """How each noise scheme derives an evaluation's seed."""

    def setUp(self):
        self.a = Ind([0.1, 0.2, 0.3], '001-001')
        self.b = Ind([0.4, 0.5, 0.6], '001-002')
        self.twin_of_a = Ind([0.1, 0.2, 0.3], '002-007')      # same genome, other ID

    def testSeedsAreRepeatableAndFitNumpy(self):
        "the same inputs give the same seed, a valid np.random.seed argument"
        for scheme in NOISE_SCHEMES:
            s = evaluation_seed(5, scheme, self.a, 1)
            self.assertEqual(s, evaluation_seed(5, scheme, self.a, 1))
            self.assertTrue(0 <= s < 2**32)
            np.random.seed(s)

    def testTheGASeedChangesEverySeed(self):
        "another GA seed gives other evaluation seeds, under every scheme"
        for scheme in NOISE_SCHEMES:
            self.assertNotEqual(evaluation_seed(5, scheme, self.a, 1),
                                evaluation_seed(6, scheme, self.a, 1))

    def testIndividualSchemeKeysOnTheID(self):
        "'individual': one seed per ID, whatever the genome"
        seed = lambda ind, gen: evaluation_seed(5, 'individual', ind, gen)
        self.assertNotEqual(seed(self.a, 1), seed(self.b, 1))
        self.assertNotEqual(seed(self.a, 1), seed(self.twin_of_a, 2))
        moved = Ind([0.9, 0.9, 0.9], self.a.ID)
        self.assertEqual(seed(self.a, 1), seed(moved, 1))
        self.assertIsInstance(seed(Ind([0.1], 'Unspecified'), 0), int)   # non-standard IDs work

    def testGenomeSchemeKeysOnTheGenome(self):
        "'genome': identical genomes share a seed, whatever their IDs"
        seed = lambda ind, gen: evaluation_seed(5, 'genome', ind, gen)
        self.assertEqual(seed(self.a, 1), seed(self.twin_of_a, 2))
        self.assertNotEqual(seed(self.a, 1), seed(self.b, 1))
        nudged = Ind([0.1, 0.2, 0.3 + 1e-12], 'x')
        self.assertNotEqual(seed(self.a, 1), seed(nudged, 1))

    def testGenerationSchemeKeysOnTheGeneration(self):
        "'generation': one seed for everyone in a generation, another for the next"
        seed = lambda ind, gen: evaluation_seed(5, 'generation', ind, gen)
        self.assertEqual(seed(self.a, 1), seed(self.b, 1))
        self.assertNotEqual(seed(self.a, 1), seed(self.a, 2))

    def testSchemesDoNotCoincide(self):
        "the three schemes give different seeds for the same individual"
        seeds = {evaluation_seed(5, scheme, self.a, 1) for scheme in NOISE_SCHEMES}
        self.assertEqual(len(seeds), 3)

    def testUnknownSchemeIsRejected(self):
        "an unknown scheme fails, in the helper and in the GA, before any file is made"
        with self.assertRaises(ValueError):
            evaluation_seed(5, 'per-planet', self.a, 1)
        with tempfile.TemporaryDirectory() as tmp:
            saved = HomeoGASimulation.dataDirRoot
            HomeoGASimulation.dataDirRoot = tmp
            try:
                with self.assertRaises(ValueError):
                    HomeoGASimulation(simulatorBackend=None, noiseScheme='per-planet')
                self.assertEqual(os.listdir(tmp), [])
            finally:
                HomeoGASimulation.dataDirRoot = saved


class SeededEvaluationTest(unittest.TestCase):
    """seeded_evaluation seeds an evaluation and hands the caller its state back."""

    def testCallerStreamsAreRestored(self):
        "numpy and Python random continue afterwards as if nothing had run"
        np.random.seed(1); random.seed(1)
        expected = (np.random.uniform(), random.random())
        np.random.seed(1); random.seed(1)
        with seeded_evaluation(99):
            np.random.uniform(size=50); random.random()
        self.assertEqual((np.random.uniform(), random.random()), expected)

    def testSameSeedSameDraws(self):
        "two evaluations from one seed draw the same numbers"
        draws = []
        for _ in range(2):
            with seeded_evaluation(42):
                draws.append((np.random.uniform(size=3).tolist(), random.random()))
        self.assertEqual(draws[0], draws[1])

    def testNoSeedChangesNothing(self):
        "None leaves the streams alone: no reseeding"
        np.random.seed(3)
        expected = np.random.uniform(size=2).tolist()
        np.random.seed(3)
        with seeded_evaluation(None):
            first = np.random.uniform()
        self.assertEqual([first, np.random.uniform()], expected)


# A small GA, run four ways under one noise scheme; prints the results as JSON.
_GA_RUNS = '''
import json, sys
sys.path.insert(0, {src!r})

def run(seed, workers):
    from Simulator.HomeoGenAlg import HomeoGASimulation
    HomeoGASimulation.dataDirRoot = {out!r}
    ga = HomeoGASimulation(stepsSize=100, popSize=4, generSize=1,
                           exp='initializeBraiten2_direct_GA_continuous_weightfree_fixed_dt',
                           simulatorBackend='HOMEO', nWorkers=workers,
                           noiseScheme={scheme!r})
    pop = ga.generateRandomPop(randomSeed=seed)
    ga.runGaSimulation(pop)
    evaluated = [dict(ID=r['indivId'], genome=r['genome'], fitness=list(r['fitness']),
                      evalSeed=r['evalSeed'])
                 for r in ga.logbook if 'indivId' in r]
    final = [dict(ID=ind.ID, genome=list(ind), fitness=list(ind.fitness.values))
             for ind in pop]
    params = [r for r in ga.logbook if 'noiseScheme' in r][-1]
    return dict(evaluated=evaluated, final=final,
                randomSeed=params['randomSeed'], noiseScheme=params['noiseScheme'])

if __name__ == '__main__':
    results = dict(serial=run(5, 1), serial_again=run(5, 1),
                   parallel=run(5, 2), other_seed=run(6, 1))
    print('RESULTS ' + json.dumps(results))
'''


class SeededGARunTest(unittest.TestCase):
    """Small GAs end to end: a seed reproduces a run, with any number of workers."""

    def _runs(self, scheme):
        src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with tempfile.TemporaryDirectory() as tmp:
            script = os.path.join(tmp, 'ga_runs.py')
            with open(script, 'w') as f:
                f.write(_GA_RUNS.format(src=src_dir, out=tmp, scheme=scheme))
            env = dict(os.environ, NUMBA_CACHE_DIR=os.path.join(tmp, 'numba'))
            result = subprocess.run([sys.executable, script], cwd=src_dir, env=env,
                                    capture_output=True, text=True, timeout=900)
        self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-2000:])
        return json.loads(result.stdout.split('RESULTS ', 1)[1].splitlines()[0])

    def _checkScheme(self, scheme):
        runs = self._runs(scheme)
        serial = runs['serial']
        self.assertEqual(serial['noiseScheme'], scheme)
        self.assertEqual(serial['randomSeed'], 5)
        self.assertEqual(runs['serial_again'], serial, 'same seed, same process: run differs')
        self.assertEqual(runs['parallel'], serial, '2 workers differ from 1')
        self.assertNotEqual(runs['other_seed']['evaluated'], serial['evaluated'])
        return serial['evaluated']

    @unittest.skipUnless('forkserver' in multiprocessing.get_all_start_methods(),
                         'the GA pool uses the forkserver start method')
    def testIndividualScheme(self):
        "'individual': reproducible; every evaluation has its own seed"
        evaluated = self._checkScheme('individual')
        seeds = [e['evalSeed'] for e in evaluated]
        self.assertEqual(len(seeds), len(set(seeds)))

    @unittest.skipUnless('forkserver' in multiprocessing.get_all_start_methods(),
                         'the GA pool uses the forkserver start method')
    def testGenomeScheme(self):
        "'genome': reproducible; seeds agree exactly when genomes do"
        evaluated = self._checkScheme('genome')
        for x in evaluated:
            for y in evaluated:
                self.assertEqual(x['evalSeed'] == y['evalSeed'], x['genome'] == y['genome'])

    @unittest.skipUnless('forkserver' in multiprocessing.get_all_start_methods(),
                         'the GA pool uses the forkserver start method')
    def testGenerationScheme(self):
        "'generation': reproducible; one seed per generation"
        evaluated = self._checkScheme('generation')
        by_generation = {}
        for e in evaluated:
            by_generation.setdefault(e['ID'].split('-')[0], set()).add(e['evalSeed'])
        self.assertEqual(sorted(by_generation), ['000', '001'])
        for seeds in by_generation.values():
            self.assertEqual(len(seeds), 1)
        self.assertEqual(len(set.union(*by_generation.values())), 2)


# A small GA (experiment 2: evolvable dt_fast, so some evaluations stop at
# maxRuns before their planned tick count) whose logbook the replay reads.
_GA_FOR_REPLAY = '''
import sys, glob
sys.path.insert(0, {src!r})
if __name__ == '__main__':
    from Simulator.HomeoGenAlg import HomeoGASimulation
    HomeoGASimulation.dataDirRoot = {out!r}
    ga = HomeoGASimulation(stepsSize=100, popSize=6, generSize=1,
                           exp='initializeBraiten2_direct_GA_continuous_weightfree_fixed',
                           simulatorBackend='HOMEO', nWorkers=2)
    ga.runGaSimulation(ga.generateRandomPop(randomSeed=3))
    print('LOGBOOK ' + sorted(glob.glob(ga.dataDir + '/Logbook-*.lgb'))[-1])
'''


@unittest.skipUnless('forkserver' in multiprocessing.get_all_start_methods(),
                     'the GA pool uses the forkserver start method')
class ReplayReproducesEvaluationTest(unittest.TestCase):
    """replay_best_with_statelog.py repeats a logged GA evaluation exactly."""

    @classmethod
    def setUpClass(cls):
        cls.src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.tmp = tempfile.TemporaryDirectory()
        cls.env = dict(os.environ, NUMBA_CACHE_DIR=os.path.join(cls.tmp.name, 'numba'))
        script = os.path.join(cls.tmp.name, 'ga.py')
        with open(script, 'w') as f:
            f.write(_GA_FOR_REPLAY.format(src=cls.src, out=cls.tmp.name))
        result = subprocess.run([sys.executable, script], cwd=cls.src, env=cls.env,
                                capture_output=True, text=True, timeout=900)
        assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]
        cls.logbook = result.stdout.split('LOGBOOK ', 1)[1].splitlines()[0]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _replay(self, logbook, *args):
        out = os.path.join(self.tmp.name, 'replay', '%d.statelog' % len(os.listdir(self.tmp.name)))
        return subprocess.run([sys.executable, 'replay_best_with_statelog.py',
                               '--logbook', logbook, '--output', out] + list(args),
                              cwd=self.src, env=self.env, capture_output=True, text=True,
                              timeout=600)

    def _individuals(self, logbook):
        import pickle
        with open(logbook, 'rb') as f:
            return [r for r in pickle.load(f) if 'indivId' in r]

    def testEveryLoggedEvaluationIsReproduced(self):
        "each individual's replay, from its evalSeed, gives its logged fitness exactly"
        for rec in self._individuals(self.logbook):
            r = self._replay(self.logbook, '--indiv', rec['indivId'])
            self.assertEqual(r.returncode, 0, r.stdout[-1500:] + r.stderr[-1500:])
            self.assertIn('Reproduced the logged fitness exactly', r.stdout, rec['indivId'])

    def testAnotherSeedIsNotPassedOffAsAReproduction(self):
        "--seed replays the genome under other noise, and says so"
        r = self._replay(self.logbook, '--seed', '123')
        self.assertEqual(r.returncode, 0, r.stderr[-1500:])
        self.assertIn('Not a reproduction of the GA evaluation', r.stdout)

    def testOldLogbookKeepsTheOldReplay(self):
        "without evalSeeds the replay works as before and says it cannot reproduce"
        import pickle
        with open(self.logbook, 'rb') as f:
            logbook = pickle.load(f)
        for rec in logbook:
            rec.pop('evalSeed', None)
        old = os.path.join(self.tmp.name, 'old.lgb')
        with open(old, 'wb') as f:
            pickle.dump(logbook, f)
        r = self._replay(old, '--steps', '100')
        self.assertEqual(r.returncode, 0, r.stdout[-1500:] + r.stderr[-1500:])
        self.assertIn('predates seeded GA evaluations', r.stdout)
        self.assertIn('Seed: 45', r.stdout)


if __name__ == "__main__":
    unittest.main()
