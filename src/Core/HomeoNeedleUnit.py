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

from  numpy import pi

class HomeoNeedleUnit(object):
    '''
    HomeoNeedleUnit holds parameters and methods describing the needle unit component of a homeostat unit
    '''
    
    ''' DefaultParameters is a  class variable holding the
    default values of all the various parameters of a needle unit.
    All 'physical' values are expressed in internal units.  
    Conversion to real physical units, if necessary, is done by Physical parameters dictionary in HomeoUnit
    HomeoUnit initialize'''

    DefaultParameters = dict(mass = 1.,                  # mass expressed in internal units
                             surfaceArea = pi,           # in internal units, equivalent to cross-section of a sphere of radius 1 unit
                             dragCoefficient = 1.        # dimensionless. used to compute drag acc to drag law for high Reynolds number
                                                         # 1 is the drag coefficient of a cube. A typical value  for a sphere is 0.47
                             )

    def __init__(self):
        '''
        Read default parameters
        '''
        
        self._mass = HomeoNeedleUnit.DefaultParameters['mass']
        self._surfaceArea = HomeoNeedleUnit.DefaultParameters['surfaceArea']
        self._dragCoefficient = HomeoNeedleUnit.DefaultParameters['dragCoefficient']

    def getMass(self):
        return self._mass
    
    def setMass(self, aValue):
        self._mass = aValue

    mass = property(fget = lambda self: self.getMass(),
                    fset = lambda self, value: self.setMass(value))
    
        
    def getDragCoefficient(self):
        return self._dragCoefficient
    
    def setDragCoefficient(self, aValue):
        self._dragCoefficient = aValue
    
    dragCoefficient = property(fget = lambda self: self.getDragCoefficient(),
                               fset = lambda self, value: self.setDragCoefficient(value))

    def getSurfaceArea(self):
        return self._surfaceArea
    
    def setSurfaceArea(self, aValue):
        self._surfaceArea = aValue
    surfaceArea = property(fget = lambda self: self.getSurfaceArea(),
                           fset = lambda self, value: self.setSurfaceArea(value))
     
   

        