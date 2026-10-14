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


if __name__ == '__main__':
    unittest.main()
