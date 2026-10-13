'''
Created on Oct 13, 2026

@author: stefano

The weight matrices of Ashby's uniselector (review finding CD-11): one
column per connection it controls, each a shuffle of the same 25 values.
The equally spaced matrix's first column was the unshuffled ramp, so every
unit's first controlled connection stepped -1 to +1 in the same order on
every unit; the randomized matrix had an extra, unshuffled first column.
'''
from Core.HomeoUniselectorAshby import HomeoUniselectorAshby

import unittest

import numpy as np

KINDS = ('randomized', 'equallySpaced', 'independentlyRandomized')


def _uniselector(kind, connections=None):
    uniselector = HomeoUniselectorAshby()
    getattr(uniselector, kind)()
    if connections is not None:
        uniselector.unitsControlled = connections
    return uniselector


class AshbyUniselectorMatrixTest(unittest.TestCase):

    def testOneColumnPerConnection(self):
        for kind in KINDS:
            for connections in (None, 15):
                with self.subTest(kind=kind, connections=connections):
                    uniselector = _uniselector(kind, connections)
                    self.assertEqual(uniselector.matrix().shape,
                                     (25, uniselector.unitsControlled))

    def testEquallySpacedColumnsAreAllShuffled(self):
        np.random.seed(4)
        matrix = _uniselector('equallySpaced').matrix()
        ramp = np.linspace(-1, 1, 25)
        for column in matrix.T:
            self.assertTrue(np.array_equal(np.sort(column), ramp))
            self.assertFalse(np.array_equal(column, ramp))

    def testRandomizedColumnsShareTheirValues(self):
        np.random.seed(5)
        matrix = _uniselector('randomized').matrix()
        values = np.sort(matrix[:, 0])
        for column in matrix.T:
            self.assertTrue(np.array_equal(np.sort(column), values))
        self.assertEqual(len({tuple(column) for column in matrix.T}), matrix.shape[1])


if __name__ == '__main__':
    unittest.main()
