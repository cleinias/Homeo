'''
Created on Oct 14, 2026

@author: stefano

StripchartGrapher's smoothing (review finding HV-07): a smoothed trace is
drawn at the centres of its windows, so a feature is not shifted in time.
'''
import unittest

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from Helpers import StripchartGrapher as SG


class SmoothingTest(unittest.TestCase):

    def testAStepIsSmoothedWhereItHappens(self):
        '''A weight that changes sign between ticks 98 and 100 has its smoothed
        zero crossing at 99; until 14 Oct 2026, with a 50-tick window, at 123.'''
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


if __name__ == '__main__':
    unittest.main()
