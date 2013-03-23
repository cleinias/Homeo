'''
Created on Feb 21, 2013

@author: stefano
'''
import numpy

class HomeoNeedleUnit:
    '''
    HomeoNeedleUnit holds parameters and methods describing the needle unit component of a homeostat unit
    '''
    
    ''' DefaultParameters is a  class variable holding the
    default values of all the various parameters of future needle units.
    All 'physical' values are expressed in internal units.  
    Conversion to real physical units, if necessary, is done by Physical parameters dictionary in HomeoUnit
    HomeoUnit initialize'''

    DefaultParameters = dict(mass = 1.,                  # mass expressed in internal units
                             surfaceArea = 1/numpy.pi,   # in internal units, eq. to a circle of radius 1 unit
                             dragCoefficient = 1.        # dimensionless. used to compute drag acc to drag law for high velocities
                             )

    def __init__(self):
        '''
        Read default parameters
        '''
        
        self._mass = HomeoNeedleUnit.DefaultParameters['mass']
        self._surfaceArea = HomeoNeedleUnit.DefaultParameters['surfaceArea']
        self._dragCoefficient = HomeoNeedleUnit.DefaultParameters['dragCoefficient']

    @property
    def mass(self):
        return self._mass
    
    @mass.setter
    def mass(self,aValue):
        self._mass = aValue
        
    @property
    def surfaceArea(self):
        return self._surfaceArea
    
    @surfaceArea.setter
    def surfaceArea(self, aValue):
        self._surfaceArea = aValue
        
    @property    
    def dragCoefficient(self):
        return self._dragCoefficient
    
    @dragCoefficient.setter
    def dragCoefficient(self,aValue):
        self._dragCoefficient = aValue
   

        