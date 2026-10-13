'''
Created on Oct 13, 2026

@author: stefano

How long a GA evaluation runs (review finding SG-02).  stepsSize counts
homeostat ticks, whatever the units' dt_fast.  The evaluation used to call
sim.step() stepsSize / min(dt_fast) times, and the simulation stopped at
stepsSize ticks anyway: the extra calls did nothing, and the log reported
ticks that never ran.
'''
from Simulator import HomeoGenAlg
from Simulator.HomeoGenAlg import _run_genome_evaluation
from Simulator.HomeoQtSimulation import HomeoQtSimulation

import os
import tempfile
import unittest
from unittest import mock


class Ind(list):
    "Stands in for a DEAP individual: a genome with an ID"
    def __init__(self, genome, ID):
        super().__init__(genome)
        self.ID = ID


class EvaluationLengthTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.steps = 20
        config = {'experiment': 'initializeBraiten2_direct_GA_continuous_weightfree_fixed',
                  'experimentParams': {'dataDir': self.tmp.name, 'noNoise': False,
                                       'noUnisel': False},
                  'stepsSize': self.steps,
                  'dataDir': self.tmp.name}
        patcher = mock.patch.dict(HomeoGenAlg._worker_config, config, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)

    def testEvaluationRunsStepsSizeTicksWhateverDtFast(self):
        # dt_fast genes 0 give dt_fast 0.2: the old code called step() 5x stepsSize times
        genome = Ind([0.5, 0.5, 0.5, 0.5, 0.0] * 2, '001-001')
        calls, times = [], []
        original = HomeoQtSimulation.step

        def counting_step(sim):
            calls.append(1)
            original(sim)
            times.append(sim.homeostat.time)

        with mock.patch.object(HomeoQtSimulation, 'step', counting_step):
            _run_genome_evaluation(genome)
        self.assertEqual(len(calls), self.steps)
        self.assertEqual(times[-1], self.steps)


if __name__ == '__main__':
    unittest.main()
