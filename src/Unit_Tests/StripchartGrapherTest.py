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
StripchartGrapher's smoothing: a smoothed trace is drawn at the centres of
its windows, so a feature is not shifted in time.  And its robustness: a log
still being written, a smoothing window longer than the log, --symmetric
with unsigned series.
'''
import os
import tempfile
import unittest
from unittest import mock

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from Helpers import StripchartGrapher as SG


class SmoothingTest(unittest.TestCase):

    def testAStepIsSmoothedWhereItHappens(self):
        '''A weight that changes sign between ticks 98 and 100 has its smoothed
        zero crossing at 99, not at the end of its smoothing window.'''
        tick = np.arange(0, 400, 2.0)                   # logged every 2 ticks
        values = np.where(tick < 100, -1.0, 1.0)
        fig, ax = plt.subplots()
        self.addCleanup(plt.close, fig)
        SG._drawStrip(ax, tick, [(values, 'w', '#000000')], window=25, signed=True,
                      showRaw=False)
        smoothed, crossings = ax.lines[1], ax.lines[2]
        self.assertAlmostEqual(np.interp(0.0, smoothed.get_ydata(), smoothed.get_xdata()),
                               99.0, delta=1.0)
        self.assertEqual(len(crossings.get_xdata()), 1)
        self.assertAlmostEqual(crossings.get_xdata()[0], 99.0, delta=2.0)



def writeStatelog(directory, rows, partial=None):
    "A small .statelog: tick, a signed weight and an unsigned stress"
    path = os.path.join(directory, 'run.statelog')
    with open(path, 'w') as f:
        f.write('# log_interval\t1\n')
        f.write('tick\tw_A_from_B\tA_stress\n')
        for t in range(rows):
            f.write('%d\t%f\t%f\n' % (t, 0.1 * (-1) ** t, 5.0 + t))
        if partial is not None:
            f.write(partial)
    return path


class RobustnessTest(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = tmp.name

    def testALogStillBeingWritten(self):
        "a half-written last line is skipped, not an error"
        for partial in ('20\t0.1', '20\t0.1\t', '20\t0.1\t5.'):
            path = writeStatelog(self.dir, 20, partial)
            meta, columns, data = SG.readStatelog(path)
            self.assertEqual(data.shape, (20 if partial != '20\t0.1\t5.' else 21, 3), partial)
        path = writeStatelog(self.dir, 0)
        self.assertEqual(SG.readStatelog(path)[2].shape, (0, 3))

    def drawn(self, **options):
        "graphStripcharts on the log; the arguments of each strip drawn"
        calls = []
        with mock.patch.object(SG, '_drawStrip', side_effect=lambda *a: calls.append(a)):
            SG.graphStripcharts([self.path], columns=('w_A_from_B', 'A_stress'),
                                output_path=os.path.join(self.dir, 'out.png'), **options)
        return calls

    def testAWindowLongerThanTheLog(self):
        "smooths over the whole log: one point, the mean"
        self.path = writeStatelog(self.dir, 10)
        [weight, stress] = self.drawn(window=50)
        self.assertEqual(weight[3], 10)
        self.assertEqual(SG._running(stress[2][0][0], stress[3]).tolist(), [9.5])

    def testSymmetricSpansTheSignedStripsOnly(self):
        "the stress (unsigned, up to 14) does not set the weights' range"
        self.path = writeStatelog(self.dir, 10)
        [weight, stress] = self.drawn(symmetric=True)
        self.assertAlmostEqual(weight[6][1], 1.12 * 0.1)
        self.assertIsNone(stress[6])


if __name__ == '__main__':
    unittest.main()
