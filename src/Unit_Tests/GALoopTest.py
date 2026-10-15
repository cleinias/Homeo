'''
Created on Oct 14, 2026

@author: stefano

The GA's own loop, run in-process with a fake, deterministic evaluate
(review finding SG-05): elitism, generation 0's statistics, clone
populations, the variation operators' bounds and the clean-up of
trajectory files.  Stopping and crashing are in GAStopTest, the
evaluation's length in GAEvaluationLengthTest.

What the elitism tests assert holds for a deterministic fitness only: how
elitism should treat noisy evaluations is an open decision (SG-06).
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

EXP = 'initializeBraiten2_direct_GA_continuous_weightfree_fixed_dt'


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
        params = dict(stepsSize=20, popSize=8, generSize=4, exp=EXP, simulatorBackend='HOMEO')
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
        '''In a generation where no offspring matches the best so far, the
        population is the offspring with its worst swapped for the best.'''
        replaced = 0
        for before, after in zip(self.generations, self.generations[1:]):
            offspring = sorted(f for _, f in after['evaluated'][len(before['evaluated']):])
            self.assertEqual(len(offspring), 8)            # all crossed and mutated
            if offspring[0] <= before['best']:
                continue
            replaced += 1
            self.assertEqual(sorted(f for _, f, _ in after['pop']),
                             sorted([before['best']] + offspring[:-1]))
            self.assertIn(before['best'], [f for _, f, _ in after['pop']])
        self.assertGreater(replaced, 0)


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
    '''A population of clones of a logged genome.  Whether a clone keeps the
    logged fitness or is re-evaluated is an open decision (SG-09): not
    asserted here.'''

    def testClonesShareTheGenomeAndTheRunRecordsThem(self):
        genome = [0.25, 0.5, 0.75, 0.1, 0.9] * 2
        ga = self.ga(generSize=1, popSize=6,
                     clonableGenome={'genome': genome, 'indivId': '007-003', 'fitness': (1.5,)})
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


class VariationOperatorsTest(GALoopTestCase):
    '''The toolbox's mate and mutate are DEAP's two-point crossover and
    Gaussian mutation, kept within [0, 1]: out-of-range genes are clipped,
    in-range ones left as the operator made them.'''

    def setUp(self):
        super().setUp()
        self.ga_ = self.ga(indivProb=1.0)

    def testMutateIsGaussianMutationClipped(self):
        genome = [0.0, 0.05, 0.5, 0.95, 1.0] * 4
        raw = self.ga_.toolbox.individual()
        raw[:] = genome
        mutant = self.ga_.toolbox.clone(raw)
        random.seed(11)
        tools.mutGaussian(raw, mu=0, sigma=0.2, indpb=1.0)
        random.seed(11)
        self.ga_.toolbox.mutate(mutant)
        self.assertEqual(list(mutant), [min(1.0, max(0.0, g)) for g in raw])
        self.assertTrue(any(g < 0 or g > 1 for g in raw))       # the clipping was exercised
        self.assertTrue(any(0 < g < 1 and g != o for g, o in zip(mutant, genome)))

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
        name go (review finding HV-10: the old pattern matched none of them);
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
