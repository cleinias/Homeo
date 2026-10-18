'''
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
    '''

    @staticmethod
    def connNoise(current, noise):
        '''Distorting-normal-proportional noise for a connection carrying
           current: Gaussian(0, bound/3) clipped to +/-bound, bound = noise x
           |current|.  0.0 with no current or no noise.'''
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

