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

from Core.HomeoUniselector import *
from Helpers.General_Helper_Functions import *

class HomeoUniselectorUniformRandom(HomeoUniselector):
    '''
    HomeoUniselectorUniformRandom is a Uniselector that does NOT follow Ashby's model. 
    It provides a random value uniformly distributed in the interval [lowerbound, upperBound], 
    which is symmetric around 0, i.e. lowerbound = upperBound negated.
    The default values for the interval are [-1, +1], but other values can be chosen. 
    However, the accessors of lowerBound and upperBound enforce the constraint 
    by refusing positive (resp. negative) values for lowerBound (resp. upperBound) 
    and changing upperBound (resp. lowerBound) to the negated value of lowerBound (resp. upperBound)
    '''
    
    def advance(self):
        '''
        Do nothing because this uniselector has no concept of an index
        it produces a new uniformly distributed  random value every time it is called
        '''
        pass

    def setLowerBound(self,aNumber):
        '''The lowerBound of the interval the uniselector value is chosen from. As the interval must be symmetric around 0,
        we always set the lowerBound to a negative number and set the upperBound accordingly'''

        if aNumber <= 0:
            self._lowerBound = aNumber
            self._upperBound = - self._lowerBound
        else:
             self._lowerBound = -aNumber
             self._upperBound = aNumber

    def setUpperBound(self,aNumber):
        '''The upperBound of the interval the uniselector value is chosen from. As the interval must be symmetric around 0,
        we always set the upperBound to a positive  number and set the lowerBound accordingly'''

        if aNumber <= 0:
            self._lowerBound = aNumber
            self._upperBound = - self._lowerBound
        else:
             self._lowerBound = -aNumber
             self._upperBound = aNumber
             
    def produceNewValue(self):
        "produce a new random value uniformly distributed in the interval [lowerBoud, upperBound]"
#        if self._beeps:
#            pass
            #ring bell
        return numpy.random.uniform(self._lowerBound, self._upperBound)


    def __init__(self):
        '''
        Initializes according to superclass first.
        '''
        super(HomeoUniselectorUniformRandom, self).__init__()
        self.setDefaults()

    def setDefaults(self):
        "The default weights' range, [-1, 1], and no sound"
        self._lowerBound = -1
        self._upperBound = 1
        self._beeps = False
