'''
Created on Oct 13, 2026

@author: stefano

How Ashby's uniselector steps through its positions (review finding CD-02).
Each firing reads the weights of the current position, then steps to the
next; there are 25 positions and the switch wraps from the last to the
first.  The index came from the Smalltalk original, which counts from 1:
the switch had 26 positions over 25 rows, the first firing read the last
row and every 26th firing read the same row again, changing nothing.
'''
from Core.HomeoUniselectorAshby import HomeoUniselectorAshby

import unittest

import numpy as np

KINDS = ('randomized', 'equallySpaced', 'independentlyRandomized')


def _uniselector(kind):
    uniselector = HomeoUniselectorAshby()
    getattr(uniselector, kind)()
    return uniselector


def _fire(uniselector, connections):
    "One firing, as HomeoUnit.operateUniselector does it: read, then step."
    values = [uniselector.produceNewValue() for _ in range(connections)]
    uniselector.advance()
    return values


class AshbyUniselectorSteppingTest(unittest.TestCase):

    def testFiringsVisitEveryPositionInTurn(self):
        for kind in KINDS:
            with self.subTest(kind):
                np.random.seed(1)
                uniselector = _uniselector(kind)
                matrix = uniselector.matrix()
                rows, connections = matrix.shape[0], 3
                visited = []
                for _ in range(2 * rows):
                    values = _fire(uniselector, connections)
                    visited.append([r for r in range(rows)
                                    if list(matrix[r, :connections]) == values])
                self.assertEqual(visited, [[r] for r in range(rows)] * 2)

    def testNoFiringRepeatsThePreviousWeights(self):
        for kind in KINDS:
            with self.subTest(kind):
                np.random.seed(2)
                uniselector = _uniselector(kind)
                firings = [_fire(uniselector, 3) for _ in range(60)]
                for i in range(1, len(firings)):
                    self.assertNotEqual(firings[i], firings[i - 1], i)

    def testTheFirstFiringReadsTheFirstPosition(self):
        np.random.seed(3)
        uniselector = _uniselector('randomized')
        self.assertEqual(_fire(uniselector, 3), list(uniselector.matrix()[0, :3]))


if __name__ == '__main__':
    unittest.main()
