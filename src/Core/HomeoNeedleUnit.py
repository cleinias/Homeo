'''
Created on Feb 21, 2013

@author: stefano
'''
from  numpy import pi

class HomeoNeedleUnit(object):
    '''
    HomeoNeedleUnit holds parameters and methods describing the needle unit component of a homeostat unit
    '''
    
    ''' DefaultParameters is a  class variable holding the
    default values of all the various parameters of future needle units.
    All 'physical' values are expressed in internal units.  
    Conversion to real physical units, if necessary, is done by Physical parameters dictionary in HomeoUnit
    HomeoUnit initialize'''

    DefaultParameters = dict(mass = 1.,                  # mass expressed in internal units
                             surfaceArea = 1/pi,   # in internal units, eq. to a circle of radius 1 unit
                             dragCoefficient = 1.        # dimensionless. used to compute drag acc to drag law for high velocities
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
     
   

        