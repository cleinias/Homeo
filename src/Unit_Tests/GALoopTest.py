'''
@author: stefano

The GA's own loop, run in-process with a fake, deterministic evaluate:
elitism, generation 0's statistics, clone populations, the variation
operators' bounds and the clean-up of trajectory files.  Stopping and crashing are in GAStopTest, the
evaluation's length in GAEvaluationLengthTest.

Noisy evaluation: everyone is evaluated afresh each generation (unless the
noise scheme is 'genome'), the previous generation's best genome survives,
an evaluation can average several runs, and the hall of fame's best are
re-evaluated at the end (NoisyEvaluationTest).
'''
import contextlib
import io
import os
import random
import tempfile
import unittest

import numpy as np
from deap import tools

from Helpers.RobotTrajectoryWriter import RobotTrajectoryWriter
from Simulator.HomeoGenAlg import HomeoGASimulation

EXP = 'initializeBraiten2_direct_GA_continuous_weightfree_fixed_v2'


def fitnessOf(genome):
    "A deterministic fitness, minimal at every gene = 0.3"
    return float(sum((g - 0.3) ** 2 for g in genome))


class GALoopTestCase(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = HomeoGASimulation.dataDirRoot
        HomeoGASimulation.dataDirRoot = tmp.name
        self.addCleanup(setattr, HomeoGASimulation, 'dataDirRoot', root)

    def ga(self, **kw):
        "A GA whose evaluations are fitnessOf, recorded in self.evaluated"
        params = dict(stepsSize=20, popSize=8, generSize=4, exp=EXP, simulatorBackend='HOMEO',
                      postEvalTop=0)
        params.update(kw)
        with contextlib.redirect_stdout(io.StringIO()):
            ga = HomeoGASimulation(**params)
        self.evaluated = []

        def evaluate(ind):
            self.evaluated.append((ind.ID, fitnessOf(ind)))
            return fitnessOf(ind),
        ga.toolbox.register('evaluate', evaluate)
        return ga

    def runGA(self, ga, pop, callback=None):
        with contextlib.redirect_stdout(io.StringIO()):
            ga.runGaSimulation(pop, progressCallback=callback)


class ElitismTest(GALoopTestCase):
    '''Every offspring is crossed and mutated (all genes), so the best genome
    is lost each generation unless elitism puts it back.'''

    def setUp(self):
        super().setUp()
        self.ga_ = self.ga(cxProb=1.0, mutationProb=1.0, indivProb=1.0)
        self.pop = self.ga_.generateRandomPop(randomSeed=3)
        self.generations = []

        def callback(g, record, best):
            self.generations.append(dict(g=g, record=record, best=best,
                                         pop=[(ind.ID, ind.fitness.values[0], list(ind))
                                              for ind in self.pop],
                                         evaluated=list(self.evaluated)))
        self.runGA(self.ga_, self.pop, callback)

    def testTheBestNeverGetsWorse(self):
        mins = [gen['record']['min'] for gen in self.generations]
        self.assertEqual(len(mins), 5)
        for previous, this in zip(mins, mins[1:]):
            self.assertLessEqual(this, previous)
        self.assertEqual(self.ga_.hof[0].fitness.values[0], mins[-1])
        self.assertIn(list(self.ga_.hof[0]), [list(ind) for ind in self.pop])

    def testTheElitistReplacesTheWorstOffspring(self):
        '''In a generation where no offspring has the previous generation's
        best genome, that genome is evaluated with them (a ninth evaluation)
        and the population is the offspring with its worst swapped for it.'''
        replaced = 0
        for before, after in zip(self.generations, self.generations[1:]):
            evaluated = [f for _, f in after['evaluated'][len(before['evaluated']):]]
            bestBefore = min(f for _, f, _ in before['pop'])
            if len(evaluated) == 8:                        # all crossed and mutated
                continue
            self.assertEqual(len(evaluated), 9)
            offspring, elite = sorted(evaluated[:8]), evaluated[8]
            self.assertEqual(elite, bestBefore)            # a deterministic fitness
            replaced += 1
            self.assertEqual(sorted(f for _, f, _ in after['pop']),
                             sorted([elite] + offspring[:-1]))
        self.assertGreater(replaced, 0)


class NoisyEvaluationTest(GALoopTestCase):
    '''Noisy evaluation: an evaluate whose score is drawn from the
    evaluation's seeded numpy stream, so every evaluation differs and a seed
    repeats it.'''

    def noisyGA(self, **kw):
        ga = self.ga(**kw)
        self.evaluated = []

        def run(genome):
            score = fitnessOf(genome) + np.random.normal()
            self.evaluated.append((genome.ID, score))
            return score,
        ga.evaluateGenomeFitness = run
        ga.toolbox.register('evaluate', ga.evaluateGenomeFitnessSeeded)
        return ga

    def testSurvivorsAreEvaluatedAfresh(self):
        "nothing changes the genomes, yet every generation evaluates all eight"
        ga = self.noisyGA(cxProb=0.0, mutationProb=0.0, generSize=3)
        self.runGA(ga, ga.generateRandomPop(randomSeed=4))
        self.assertEqual([r['evaluations'] for r in ga.logbook if 'gen' in r], [8, 8, 8, 8])
        IDs = [ID for ID, _ in self.evaluated]
        self.assertEqual(len(set(IDs)), len(IDs))          # a new ID, so new noise

    def testUnderTheGenomeSchemeUnchangedGenomesKeepTheirScore(self):
        ga = self.noisyGA(cxProb=0.0, mutationProb=0.0, generSize=3, noiseScheme='genome')
        self.runGA(ga, ga.generateRandomPop(randomSeed=4))
        self.assertEqual([r['evaluations'] for r in ga.logbook if 'gen' in r], [8, 0, 0, 0])

    def testTheBestGenomeSurvives(self):
        ga = self.noisyGA(cxProb=1.0, mutationProb=1.0, indivProb=1.0, generSize=4)
        pop = ga.generateRandomPop(randomSeed=3)
        bests = []
        self.runGA(ga, pop, lambda g, record, best: bests.append(
            list(min(pop, key=lambda ind: ind.fitness.values[0]))))
        populations = []
        for gen, best in enumerate(bests[:-1]):
            genomes = [list(r['genome']) for r in ga.logbook
                       if 'genome' in r and r['indivId'].startswith('%03d-' % (gen + 1))]
            self.assertIn(best, genomes)

    def testAnEvaluationAveragesItsRuns(self):
        ga = self.noisyGA(generSize=1, evalsPerIndividual=3)
        self.runGA(ga, ga.generateRandomPop(randomSeed=6))
        records = [r for r in ga.logbook if 'genome' in r]
        self.assertEqual(len(self.evaluated), 3 * len(records))
        from Simulator.HomeoGenAlg import repeat_seeds
        for r in records:
            self.assertEqual(len(r['scores']), 3)
            self.assertAlmostEqual(r['fitness'][0], np.mean(r['scores']))
            # the first run is the one the logged evalSeed repeats
            np.random.seed(r['evalSeed'])
            self.assertAlmostEqual(r['scores'][0], fitnessOf(r['genome']) + np.random.normal())
        self.assertEqual(repeat_seeds(17, 1), [17])
        self.assertEqual(len(set(repeat_seeds(17, 4))), 4)
        self.assertEqual(repeat_seeds(None, 2), [None, None])

    def testTheHallOfFameIsReEvaluated(self):
        ga = self.noisyGA(generSize=2, postEvalTop=3, postEvalSeeds=5)
        self.runGA(ga, ga.generateRandomPop(randomSeed=7))
        post = ga.postEvaluation
        self.assertEqual([e['indivId'] for e in sorted(post, key=lambda e: e['indivId'])],
                         sorted(ind.ID for ind in list(ga.hof)[:3]))
        self.assertEqual([e['mean'] for e in post], sorted(e['mean'] for e in post))
        for e in post:
            self.assertEqual(len(e['scores']), 5)
            self.assertAlmostEqual(e['mean'], np.mean(e['scores']))
        [summary] = [r for r in ga.logbook if 'finalIndivs' in r]
        self.assertEqual(summary['postEvaluation'], post)

    def testThePostEvaluationRunsOncePerSeed(self):
        "with k runs per evaluation, the post-evaluation still runs each seed once"
        ga = self.noisyGA(generSize=1, evalsPerIndividual=3, postEvalTop=2, postEvalSeeds=4)
        self.runGA(ga, ga.generateRandomPop(randomSeed=7))
        post = [ID for ID, _ in self.evaluated if ID.startswith('post-')]
        self.assertEqual(len(post), 2 * 4)
        for e in ga.postEvaluation:
            self.assertEqual(len(e['scores']), 4)
            fitnesses = [r['fitness'][0] for r in ga.logbook
                         if 'genome' in r and r['genome'] == e['genome']]
            self.assertEqual(e['evaluations'], len(fitnesses))
            self.assertEqual(e['loggedBest'], min(fitnesses))
            self.assertAlmostEqual(e['loggedMean'], np.mean(fitnesses))


class SecondRunTest(GALoopTestCase):

    def testASecondRunRecordsOnlyItself(self):
        "run 2 on the same object: its logbook, hall of fame and history are its own"
        ga = self.ga(generSize=1, postEvalTop=2, postEvalSeeds=1)
        self.runGA(ga, ga.generateRandomPop(randomSeed=7))
        first = {tuple(r['genome']) for r in ga.logbook if 'genome' in r}
        self.runGA(ga, ga.generateRandomPop(randomSeed=8))
        second = [r for r in ga.logbook if 'genome' in r]
        IDs = [r['indivId'] for r in second]
        self.assertEqual(len(IDs), len(set(IDs)))
        self.assertEqual([r['gen'] for r in ga.logbook if 'gen' in r], [0, 1])
        self.assertFalse(first & {tuple(r['genome']) for r in second})
        genomes = {tuple(r['genome']) for r in second}
        self.assertTrue(all(tuple(ind) in genomes for ind in ga.hof))
        self.assertTrue(all(tuple(e['genome']) in genomes for e in ga.postEvaluation))
        self.assertTrue(all(tuple(g) in genomes or tuple(g) not in first
                            for g in ga.hist.genealogy_history.values()))
        [summary] = [r for r in ga.logbook if 'finalIndivs' in r]
        self.assertEqual(summary['randomSeed'], 8)


class GenerationZeroTest(GALoopTestCase):

    def testGenerationZeroStatisticsAreItsEvaluations(self):
        ga = self.ga(generSize=1)
        pop = ga.generateRandomPop(randomSeed=5)
        records = []
        self.runGA(ga, pop, lambda g, record, best: records.append((g, record, best)))
        fitnesses = [f for _, f in self.evaluated[:8]]
        g, record, best = records[0]
        self.assertEqual(g, 0)
        self.assertAlmostEqual(record['min'], min(fitnesses))
        self.assertAlmostEqual(record['max'], max(fitnesses))
        self.assertAlmostEqual(record['avg'], np.mean(fitnesses))
        self.assertAlmostEqual(best, min(fitnesses))
        [gen0] = [r for r in ga.logbook if r.get('gen') == 0]
        self.assertEqual(gen0['evaluations'], 8)
        self.assertAlmostEqual(gen0['min'], min(fitnesses))
        self.assertEqual([ID for ID, _ in self.evaluated[:8]],
                         ['000-%03d' % i for i in range(1, 9)])


class ClonePopulationTest(GALoopTestCase):
    '''A population of clones of a logged genome: each clone starts without a
    fitness and generation 0 evaluates it; the logged fitness is kept in the
    summary as cloneSourceFitness.'''

    def testClonesAreEvaluatedNotGivenTheLoggedFitness(self):
        genome = [0.25, 0.5, 0.75, 0.1] * 2
        ga = self.ga(generSize=0, popSize=4,
                     clonableGenome={'genome': genome, 'indivId': '007-003', 'fitness': (1.5,),
                                     'genomeLayout': 'weightfree_v2'})
        pop = ga.generatePopOfClones(cloneName='007-003', randomSeed=2)
        self.assertFalse(any(ind.fitness.valid for ind in pop))
        self.runGA(ga, pop)
        self.assertEqual(len(self.evaluated), 4)
        for ind in pop:
            self.assertEqual(ind.fitness.values, (fitnessOf(genome),))
        [summary] = [r for r in ga.logbook if 'finalIndivs' in r]
        self.assertEqual(summary['cloneSourceFitness'], (1.5,))

    def testClonesShareTheGenomeAndTheRunRecordsThem(self):
        genome = [0.25, 0.5, 0.75, 0.1] * 2
        ga = self.ga(generSize=1, popSize=6,
                     clonableGenome={'genome': genome, 'indivId': '007-003', 'fitness': (1.5,),
                                     'genomeLayout': 'weightfree_v2'})
        pop = ga.generatePopOfClones(cloneName='007-003', randomSeed=2)
        self.assertEqual(len(pop), 6)
        for ind in pop:
            self.assertEqual(list(ind), genome)
        self.assertEqual(len({id(ind) for ind in pop}), 6)          # six objects, not one
        self.runGA(ga, pop)
        self.assertEqual(ga.randomSeed, 2)
        [summary] = [r for r in ga.logbook if 'finalIndivs' in r]
        self.assertEqual(summary['type'], 'clones')
        self.assertEqual(summary['cloneName'], '007-003')
        self.assertEqual(summary['randomSeed'], 2)

    def testAGenomeThatDoesNotFitTheSetupIsRefused(self):
        "a clone needs the setup's layout, named, and its number of genes"
        clone = {'indivId': '007-003', 'fitness': (1.5,)}
        for genome, layout, message in (([0.5] * 10, 'weightfree_v2', '10 genes'),
                                        ([0.5] * 8, 'weightfree', "layout 'weightfree'"),
                                        ([0.5] * 8, None, "layout None")):
            with self.subTest(message):
                with self.assertRaisesRegex(ValueError, message):
                    self.ga(clonableGenome=dict(clone, genome=genome, genomeLayout=layout))
        with self.assertRaisesRegex(ValueError, 'does not say its layout'):
            self.ga(clonableGenome=dict(clone, genome=[0.5] * 8))

    def testTheLogbooksGenomeCarriesItsLayout(self):
        import glob
        from Helpers.StatsAnalyzer import extractGenomeOfIndID
        ga = self.ga(generSize=0, popSize=2)
        self.runGA(ga, ga.generateRandomPop(randomSeed=1))
        [logbook] = glob.glob(os.path.join(ga.dataDir, 'Logbook-*.lgb'))
        genome = extractGenomeOfIndID('000-002', logbook)
        self.assertEqual(genome['genomeLayout'], 'weightfree_v2')
        self.assertEqual(len(genome['genome']), 8)
        self.ga(clonableGenome=genome)                 # fits


class VariationOperatorsTest(GALoopTestCase):
    '''The toolbox's mate and mutate are DEAP's two-point crossover and
    Gaussian mutation, kept within [0, 1]: a mutation's out-of-range genes are
    reflected back, in-range ones left as the operator made them.'''

    def setUp(self):
        super().setUp()
        self.ga_ = self.ga(indivProb=1.0)

    def testMutateIsGaussianMutationReflected(self):
        genome = [0.0, 0.05, 0.5, 0.95, 1.0] * 4
        raw = self.ga_.toolbox.individual()
        raw[:] = genome
        mutant = self.ga_.toolbox.clone(raw)
        random.seed(11)
        tools.mutGaussian(raw, mu=0, sigma=0.2, indpb=1.0)
        random.seed(11)
        self.ga_.toolbox.mutate(mutant)
        reflected = [-g if g < 0 else 2 - g if g > 1 else g for g in raw]
        for g, want in zip(mutant, reflected):
            self.assertAlmostEqual(g, want, places=12)
        self.assertTrue(any(g < 0 or g > 1 for g in raw))       # the reflection was exercised
        self.assertTrue(all(0 < g < 1 and isinstance(g, float) for g in mutant))

    def testReflect(self):
        reflect = self.ga_.reflect
        for value, want in ((1.07, 0.93), (-0.05, 0.05), (0.3, 0.3), (2.25, 0.25),
                            (-1.25, 0.75), (1.0, 1.0), (0.0, 0.0)):
            self.assertAlmostEqual(reflect(value), want, places=12)

    def testMutationKeepsAUniformSpreadUniform(self):
        '''After 50 reflected mutations no gene is exactly 0 or 1 and each
        tenth holds about 10% (clipping would leave 23% of genes exactly on 0
        or 1 and 18% in each edge tenth)'''
        ind = self.ga_.toolbox.individual()
        rng = np.random.default_rng(3)
        ind[:] = rng.random(4000).tolist()
        random.seed(5)
        for _ in range(50):
            self.ga_.toolbox.mutate(ind)
        genes = np.array(ind)
        self.assertFalse(np.any((genes == 0) | (genes == 1)))
        tenths = np.histogram(genes, bins=10, range=(0, 1))[0] / genes.size
        for share in tenths:
            self.assertAlmostEqual(share, 0.1, delta=0.02)

    def testMateSwapsGenesWithoutChangingThem(self):
        a, b = self.ga_.toolbox.individual(), self.ga_.toolbox.individual()
        a[:] = [0.1 * i / 2 for i in range(20)]
        b[:] = [1 - 0.1 * i / 2 for i in range(20)]
        before = list(zip(a, b))
        random.seed(4)
        self.ga_.toolbox.mate(a, b)
        for (x, y), (p, q) in zip(zip(a, b), before):
            self.assertEqual(sorted((x, y)), sorted((p, q)))
        self.assertNotEqual(list(zip(a, b)), before)


class TrajectoryCleanUpTest(GALoopTestCase):

    def testOnlyTheUnspecifiedRobotsTrajectoriesGo(self):
        """The files the trajectory writer names for the robot without a model
        name go;
        the individuals' trajectories and other files stay."""
        ga = self.ga()
        writer = RobotTrajectoryWriter('Unspecified', (0, 0, 0), [], dataDir=ga.dataDir,
                                       enabled=False)
        unspecified = [os.path.basename(writer.buildTrajFilename('Unspecified'))]
        open(os.path.join(ga.dataDir, unspecified[0]), 'w').close()
        unspecified.append(os.path.basename(writer.buildTrajFilename('Unspecified')))  # -2
        kept = [os.path.basename(writer.buildTrajFilename('001-002')),
                'Unspecified-notes.txt']
        for name in unspecified[1:] + kept:
            open(os.path.join(ga.dataDir, name), 'w').close()
        self.assertEqual(len(os.listdir(ga.dataDir)), 4)
        ga.cleanUpTrajFiles()
        self.assertEqual(sorted(os.listdir(ga.dataDir)), sorted(kept))


if __name__ == '__main__':
    unittest.main()
