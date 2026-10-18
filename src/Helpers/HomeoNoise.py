# Copyright (C) 2006-2026 Stefano Franchi
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

