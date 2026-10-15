'''
Created on Mar 15, 2013

@author: stefano
'''
import random


class HomeoNoise(object):
    '''
    The noise of the homeostat's connections and units.  Both are
    "distorting normal" noise: a Gaussian draw with standard deviation
    bound/3, clipped to [-bound, bound] -- for a unit (unitNoise) the bound
    is its noise, "linear"; for a connection (connNoise) its noise times the
    current it carries, "proportional".  Headless runs draw the same noise
    with numba (_jit_unit_noise, _jit_conn_noise in Core/HomeoJIT.py).

    Until 14 Oct 2026 this was also a singleton offering twelve noise
    algorithms, mode (distorting/degrading) x distribution (constant/uniform/
    normal) x ratio (linear/proportional), chosen by name in getNoise().
    Units and connections always chose the two variants above, which were
    inlined here in Feb 2026 (0d474d2); the other algorithms were then used
    only by their own tests, and were deleted (review findings HN-06, HN-07,
    TS-13).  They are in the history of this file.
    '''

    @staticmethod
    def connNoise(current, noise):
        '''Distorting-normal-proportional noise for a connection carrying
           current: Gaussian(0, bound/3) clipped to +/-bound, bound = noise x
           |current|.  None on a connection carrying no current (review finding CU-13:
           it used to be the full noise at exactly 0).'''
        if noise == 0 or current == 0:
            return 0.0
        bound = noise * abs(current)
        val = random.gauss(0, bound / 3.0)
        if val < -bound:
            return -bound
        if val > bound:
            return bound
        return val

    @staticmethod
    def unitNoise(noise):
        '''Distorting-normal-linear noise for a unit: Gaussian(0, noise/3)
           clipped to +/-noise.'''
        if noise == 0:
            return 0.0
        val = random.gauss(0, noise / 3.0)
        if val < -noise:
            return -noise
        if val > noise:
            return noise
        return val

