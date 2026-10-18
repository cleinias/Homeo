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
StatsAnalyzer's reports of a GA run: the
hall-of-fame table and the comparison of value files.
'''
import unittest

import numpy as np

from Helpers import StatsAnalyzer as SA


def _logbook(fitnesses, noUnits=6):
    "A logbook with no metadata (classic 6-unit layout): one record per individual."
    rng = np.random.default_rng(1)
    return [{'genome': list(rng.random(noUnits * 4 + noUnits * noUnits)),
             'fitness': (f,), 'indivId': '%03d-%03d' % (1, i)}
            for i, f in enumerate(fitnesses)]


class HallOfFameTest(unittest.TestCase):

    def testRowsAreAlignedWithTheHeaders(self):
        '''Each row is fitness, ID, then the genome, as long as the headers:
        the genome does not land under "Fitness".'''
        logbook = _logbook([3.0, 1.0, 2.0])
        table = SA.hallOfFame(logbook, num=2).splitlines()
        headers = [h.strip() for h in table[0].strip('|').split('|')]
        rows = [[c.strip() for c in line.strip('|').split('|')] for line in table[2:]]
        self.assertEqual(headers[:5], ['Fitness', 'IndivID', 'Evals', 'MeanFit', 'U1-mass'])
        self.assertEqual([len(r) for r in rows], [len(headers)] * 2)
        self.assertEqual([float(r[0]) for r in rows], [1.0, 2.0])
        self.assertEqual([r[1] for r in rows], ['001-001', '001-002'])

    def testOneRowPerGenomeThePostEvaluationFirst(self):
        '''A genome evaluated several times is one row, with its best and mean;
        with a post-evaluation its genomes come first, by their mean.'''
        logbook = _logbook([3.0, 1.0, 2.0])
        again = dict(logbook[0], fitness=(0.5,), indivId='002-001')    # genome 0, luckier
        logbook.append(again)
        table = SA.hallOfFame(logbook, num=3).splitlines()
        rows = [[c.strip() for c in line.strip('|').split('|')] for line in table[2:]]
        self.assertEqual([(r[1], float(r[0]), int(r[2]), float(r[3])) for r in rows],
                         [('001-000', 0.5, 2, 1.75), ('001-001', 1.0, 1, 1.0),
                          ('001-002', 2.0, 1, 2.0)])
        post = [{'indivId': '001-002', 'genome': logbook[2]['genome'], 'mean': 1.2, 'sd': 0.1,
                 'scores': [1.1, 1.3]},
                {'indivId': '002-001', 'genome': logbook[0]['genome'], 'mean': 2.5, 'sd': 0.2,
                 'scores': [2.3, 2.7]}]
        logbook.append({'finalIndivs': [], 'postEvaluation': post})
        table = SA.hallOfFame(logbook, num=3).splitlines()
        headers = [h.strip() for h in table[0].strip('|').split('|')]
        self.assertEqual(headers[:6], ['Fitness', 'IndivID', 'Evals', 'MeanFit',
                                       'PostMean', 'PostSD'])
        rows = [[c.strip() for c in line.strip('|').split('|')] for line in table[2:]]
        self.assertEqual([(r[1], r[4]) for r in rows],
                         [('001-002', '1.2'), ('001-000', '2.5'), ('001-001', '')])

    def testTheReplaysBestIsThePostEvaluationsBest(self):
        import contextlib, io, sys
        sys.argv = sys.argv[:1]
        import replay_best_with_statelog as R
        logbook = _logbook([3.0, 1.0, 2.0])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(R.find_best_individual(logbook)['indivId'], '001-001')
            logbook.append({'finalIndivs': [], 'postEvaluation': [
                {'indivId': '001-002', 'genome': logbook[2]['genome'], 'mean': 1.2, 'sd': 0.1,
                 'scores': [1.1, 1.3]}]})
            self.assertEqual(R.find_best_individual(logbook)['indivId'], '001-002')


class LogbookLayoutTest(unittest.TestCase):
    """The layout StatsAnalyzer reads from a GA run's own logbook: the
    classic and weight-free genomes, each decoded and labelled as its setup
    builds it."""

    def logbook(self, exp):
        import contextlib, io, tempfile
        from Simulator.HomeoGenAlg import HomeoGASimulation
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = HomeoGASimulation.dataDirRoot
        HomeoGASimulation.dataDirRoot = tmp.name
        self.addCleanup(setattr, HomeoGASimulation, 'dataDirRoot', root)
        with contextlib.redirect_stdout(io.StringIO()):
            ga = HomeoGASimulation(postEvalTop=0, stepsSize=5, popSize=4, generSize=1, exp=exp,
                                   simulatorBackend='HOMEO')
            ga.toolbox.register('evaluate', lambda ind: (float(sum(ind)),))
            ga.runGaSimulation(ga.generateRandomPop(randomSeed=1))
        return ga.logbook

    def testEachLayoutIsDecodedAndLabelledAsItsSetupBuildsIt(self):
        import contextlib, io
        from Helpers.GenomeDecoder import genomeDecoder
        for exp, genes, layout in (('initializeBraiten2_2_Full_GA', 40, None),
                                   ('initializeBraiten2_direct_GA_continuous_weightfree_fixed_v2', 8,
                                    'weightfree_v2')):
            with self.subTest(exp):
                logbook = self.logbook(exp)
                noUnits, noEvolved, found = SA._logbook_layout(logbook)
                self.assertEqual(found, layout)
                with contextlib.redirect_stdout(io.StringIO()):
                    indivs, _ = SA.indivsDecodedFromLogbook(logbook)
                records = [r for r in logbook if 'genome' in r]
                self.assertEqual(len(indivs), len(records))
                headers = SA._genome_headers(noUnits, noEvolved, found)
                for (decoded, fitness, name), record in zip(indivs, records):
                    self.assertEqual(len(record['genome']), genes)
                    self.assertEqual((fitness, name), (record['fitness'], record['indivId']))
                    self.assertEqual(decoded, genomeDecoder(noUnits, record['genome'],
                                                            noEvolvedUnits=noEvolved, layout=found))
                    self.assertEqual(len(headers), 2 + len(decoded))
                with contextlib.redirect_stdout(io.StringIO()):
                    table = SA.hallOfFame(logbook, num=1).splitlines()
                best = min(records, key=lambda r: r['fitness'][0])
                self.assertEqual(table[2].strip('|').split('|')[1].strip(), best['indivId'])


class ValueFilesTest(unittest.TestCase):
    '''The comparison of input and output value files fails on a missing or
    unreadable file and on files of different lengths, without raising, and
    checks the right eye's dummy files too.'''

    def setUp(self):
        import os, tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cwd = os.getcwd()
        os.chdir(self.tmp.name)
        self.addCleanup(os.chdir, self.cwd)

    @staticmethod
    def write(name, values):
        with open(name, 'w') as f:
            f.write('\n'.join(str(v) for v in values) + '\n')

    def testComparison(self):
        self.write('a', [1, 2, 3])
        self.write('b', [1, 2, 3])
        self.write('c', [1, 2, 4])
        self.write('d', [1, 2])
        self.assertIs(SA.areValueFilesIdentical('a', 'b'), True)
        self.assertIs(SA.areValueFilesIdentical('a', 'c'), False)
        self.assertIs(SA.areValueFilesIdentical('a', 'd'), False)
        self.assertIs(SA.areValueFilesIdentical('a', 'missing'), False)

    def testEveryKindOfFileIsChecked(self):
        self.write('LeftMotorCommands1', [1, 2])
        self.write('LeftMotorCommands2', [1, 2])
        self.assertTrue(SA.areAllInpAndOutpFilesIdentical())
        self.write('RightEyeDUMMYr1', [1, 2])
        self.write('RightEyeDUMMYr2', [1, 3])
        self.assertFalse(SA.areAllInpAndOutpFilesIdentical())


if __name__ == '__main__':
    unittest.main()
