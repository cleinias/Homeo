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
The weight matrices of Ashby's uniselector: one column per connection it
controls, each a shuffle of the same 25 values.  No column is the
unshuffled ramp, so no unit's first controlled connection steps -1 to +1 in
the same order on every unit, and the randomized matrix has no extra column.
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
