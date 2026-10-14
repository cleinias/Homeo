'''
Created on Oct 14, 2026

@author: stefano

StatsAnalyzer's reports of a GA run (review findings HN-12, HN-13): the
hall-of-fame table and the comparison of value files.
'''
import unittest

import numpy as np

from Helpers import StatsAnalyzer as SA


def _logbook(fitnesses, noUnits=6):
    "An old-style logbook (no metadata, classic 6-unit layout): one record per individual."
    rng = np.random.default_rng(1)
    return [{'genome': list(rng.random(noUnits * 4 + noUnits * noUnits)),
             'fitness': (f,), 'indivId': '%03d-%03d' % (1, i)}
            for i, f in enumerate(fitnesses)]


class HallOfFameTest(unittest.TestCase):

    def testRowsAreAlignedWithTheHeaders(self):
        '''Each row is fitness, ID, then the genome, as long as the headers;
        until 14 Oct 2026 the whole genome landed under "Fitness" (HN-12).'''
        logbook = _logbook([3.0, 1.0, 2.0])
        table = SA.hallOfFame(logbook, num=2).splitlines()
        headers = [h.strip() for h in table[0].strip('|').split('|')]
        rows = [[c.strip() for c in line.strip('|').split('|')] for line in table[2:]]
        self.assertEqual(headers[:3], ['Fitness', 'IndivID', 'U1-mass'])
        self.assertEqual([len(r) for r in rows], [len(headers)] * 2)
        self.assertEqual([float(r[0]) for r in rows], [1.0, 2.0])
        self.assertEqual([r[1] for r in rows], ['001-001', '001-002'])


class ValueFilesTest(unittest.TestCase):
    '''The comparison of input and output value files fails on a missing or
    unreadable file and on files of different lengths, and checks the right
    eye's dummy files too; until 14 Oct 2026 the first counted as identical,
    the second raised and the third were skipped (HN-13).'''

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
