'''
Created on Oct 14, 2026

@author: stefano

The GA's logbook (review finding SG-08): one run summary, the latest, and
generation 0's statistics whether or not a progress callback is given.
'''
import contextlib
import glob
import io
import os
import pickle
import tempfile
import unittest

from Simulator.HomeoGenAlg import HomeoGASimulation


class GALogbookTest(unittest.TestCase):

    def testOneSummaryAndEveryGeneration(self):
        '''Until 14 Oct 2026 every save appended a summary (a run of G
        generations had G+1) and generation 0 was recorded only with a
        progress callback.'''
        with tempfile.TemporaryDirectory() as tmp:
            root = HomeoGASimulation.dataDirRoot
            HomeoGASimulation.dataDirRoot = tmp
            self.addCleanup(setattr, HomeoGASimulation, 'dataDirRoot', root)
            with contextlib.redirect_stdout(io.StringIO()):
                ga = HomeoGASimulation(postEvalTop=0, stepsSize=20, popSize=4, generSize=3,
                                       exp='initializeBraiten2_direct_GA_continuous_weightfree_fixed_v2',
                                       simulatorBackend='HOMEO')
                ga.runGaSimulation(ga.generateRandomPop(randomSeed=1))
            [path] = glob.glob(os.path.join(ga.dataDir, 'Logbook-*.lgb'))
            with open(path, 'rb') as f:
                saved = pickle.load(f)
        for logbook in (ga.logbook, saved):
            self.assertEqual([r['gen'] for r in logbook if 'gen' in r], [0, 1, 2, 3])
            summaries = [r for r in logbook if 'finalIndivs' in r]
            self.assertEqual(len(summaries), 1)
            self.assertEqual(summaries[0]['finalPop'], 4)
            # how the genes decode (a layout's size does not identify it)
            self.assertEqual(summaries[0]['genomeLayout'], 'weightfree_v2')
            self.assertEqual(summaries[0]['lightIntensity'], 100)    # a light


if __name__ == '__main__':
    unittest.main()
