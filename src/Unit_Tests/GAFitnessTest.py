'''
Created on Oct 14, 2026

@author: stefano

What the GA optimises (review finding TS-09): an evaluation's fitness is
the experiment's fitnessSign times the final distance from the light, on
the serial and the parallel path; DEAP's FitnessMin makes lower better, so
phototaxis selects the nearer vehicle and scototaxis the farther; and
selTournamentRemove picks each tournament's best and removes it.
'''
import contextlib
import io
import random
import tempfile
import unittest
from unittest import mock

from deap import creator

from Simulator import HomeoGenAlg
from Simulator.HomeoGenAlg import HomeoGASimulation, selTournamentRemove, _run_genome_evaluation
from Simulator.SimulatorBackend import SimulatorBackendHOMEO


class Ind(list):
    "Stands in for a DEAP individual: a genome with an ID"
    def __init__(self, genome, ID):
        super().__init__(genome)
        self.ID = ID


class GATestCase(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = tmp.name
        root = HomeoGASimulation.dataDirRoot
        HomeoGASimulation.dataDirRoot = tmp.name
        self.addCleanup(setattr, HomeoGASimulation, 'dataDirRoot', root)

    def ga(self, exp, **kw):
        with contextlib.redirect_stdout(io.StringIO()):
            return HomeoGASimulation(stepsSize=5, popSize=4, exp=exp, simulatorBackend='HOMEO', **kw)


class FitnessSignTest(GATestCase):

    def testSerialEvaluationIsSignTimesDistance(self):
        for exp, sign in (('initializeBraiten2_2_Full_GA_phototaxis', 1),
                          ('initializeBraiten2_2_Full_GA_scototaxis', -1)):
            with self.subTest(exp=exp):
                ga = self.ga(exp)
                self.assertEqual(ga.fitnessSign, sign)
                ind = ga.toolbox.individual()
                ind.ID = '000-001'
                with mock.patch.object(ga.simulatorBackend, 'finalDisFromTarget', return_value=2.5), \
                        contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(ga.evaluateGenomeFitness(ind), (sign * 2.5,))

    def testParallelEvaluationIsSignTimesDistance(self):
        for sign in (1, -1):
            with self.subTest(sign=sign):
                config = {'experiment': 'initializeBraiten2_direct_GA_continuous_weightfree_fixed',
                          'experimentParams': {'dataDir': self.tmp, 'noNoise': False,
                                               'noUnisel': False},
                          'stepsSize': 5, 'dataDir': self.tmp, 'fitnessSign': sign}
                with mock.patch.dict(HomeoGenAlg._worker_config, config, clear=True), \
                        mock.patch.object(SimulatorBackendHOMEO, 'finalDisFromTarget', return_value=2.5), \
                        contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(_run_genome_evaluation(Ind([0.5] * 10, '000-001')), (sign * 2.5,))

    def testLowerIsBetter(self):
        '''With every vehicle in one tournament, phototaxis selects the
        nearest (fitness +distance), scototaxis the farthest (-distance).'''
        distances = [3.0, 1.0, 2.0]
        for exp, chosen in (('initializeBraiten2_2_Full_GA_phototaxis', 1.0),
                            ('initializeBraiten2_2_Full_GA_scototaxis', 3.0)):
            with self.subTest(exp=exp):
                ga = self.ga(exp, tournamentSize=50)
                pop = []
                for d in distances:
                    ind = ga.toolbox.individual()
                    ind.fitness.values = (ga.fitnessSign * d,)
                    ind.distance = d
                    pop.append(ind)
                random.seed(1)
                self.assertEqual({ind.distance for ind in ga.toolbox.select(pop, 3)}, {chosen})
                self.assertEqual(creator.FitnessMin.weights, (-1.0,))


class SelTournamentRemoveTest(unittest.TestCase):

    def setUp(self):
        # DEAP's classes, as HomeoGASimulation creates them
        from deap import base
        if not hasattr(creator, 'FitnessMin'):
            creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        if not hasattr(creator, 'Individual'):
            creator.create("Individual", list, fitness=creator.FitnessMin, ID=None)

    def population(self, values):
        pop = []
        for v in values:
            ind = creator.Individual([v])
            ind.fitness.values = (v,)
            pop.append(ind)
        return pop

    def testPicksTheBestAndRemovesIt(self):
        pop = self.population([5.0, 1.0, 3.0, 4.0, 2.0])
        original = list(pop)
        random.seed(2)
        chosen = selTournamentRemove(pop, 2, 50)      # tournaments that see everyone
        self.assertEqual([ind.fitness.values[0] for ind in chosen], [1.0, 2.0])
        self.assertEqual([ind.fitness.values[0] for ind in pop], [5.0, 3.0, 4.0])
        for ind in chosen:
            self.assertTrue(any(ind is o for o in original))      # references, not copies

    def testNoIndividualIsChosenTwice(self):
        pop = self.population([float(v) for v in range(10)])
        random.seed(3)
        chosen = selTournamentRemove(pop, 10, 3)
        self.assertEqual(sorted(ind.fitness.values[0] for ind in chosen), list(range(10)))
        self.assertEqual(pop, [])


if __name__ == '__main__':
    unittest.main()
