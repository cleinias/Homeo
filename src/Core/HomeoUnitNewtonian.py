'''
Created on Mar 17, 2013

@author: stefano
'''
from __future__  import division
from  Core.HomeoUnit import *
import numpy as np
from math import sqrt
from Helpers.General_Helper_Functions import *

class HomeoUnitNewtonian(HomeoUnit):
    '''
    HomeoUnitNewtonian is a HomeoUnit whose needle's displacement is computed according 
    to (a simplified version of) Newtonian physics. In brief, the needle's displacement
    is proportional to acceleration, not just velocity. 
    The computations take into account also the frictional forces acting on the needle
    due to the viscosity of the medium it goes through according to (a simplified version of)
    Stokes law. In brief, the frictional force exerted by the viscous medium is proportional to velocity
    
    The class does not add any instance variable to HomeoUnit, it just overrides some of 
    the computation methods.  
    '''
#===============================================================================
# Initialization methods and properties
#===============================================================================
    def __init__(self):
        '''
        The mass of the needle unit is directly responsible for the unit's inertia and, 
        therefore, for its sensitivity to external forces (inputs). We initialize it 
        to a rather large value (expressed in internal units) to ensure a minimum
        of stability 
        '''
        
        "initialize according to superclass first"
        super(HomeoUnitNewtonian, self).__init__()

        self.needleUnit.mass = 1000

    def clearFutureValues(self):
        "sets to 0 the internal values used for computing future states. "


        self.nextDeviation =  0
        self.inputTorque =  0
        self.currentOutput = 0
        self.currentVelocity = 0
        
    'Convenience property to get to the mass stored in the needleUnit'
    def getMass(self):
        return self._needleUnit.mass
        
    def setMass(self,aValue):
        try:
            self._needleUnit.mass = float(aValue)
        except ValueError:
            sys.stderr.write("Tried to assign a non-numeric value to unit  %s's Mass. The value was: %s\n" % (self.name, aValue))
        finally:
            QObject.emit(emitter(self), SIGNAL('massChanged'),  self.mass)
            QObject.emit(emitter(self), SIGNAL('massChangedLineEdit'), str(int( self.mass)))
            sys.stderr.write('%s emitted signals mass    Changed with value %f\n' % (self._name, self.mass))
            
        
    mass = property(fget = lambda self: self.getMass(),
                    fset = lambda self, value: self.setMass(value))
        
#===============================================================================  
# Running methods
#===============================================================================

    def drag(self):
        '''Output the drag force acting on the unit as
           a result of the viscosity in the trough and 
           the velocity of the needle.'''

        return self.stokesLawDrag()


    def dragDummy(self):
        "Used for testing purposes"

        return  0

    def dragEquationDrag(self):
        '''Compute the drag on the needle according to the drag equation 
           for high Reynolds numbers: 
           D = 1/2  C A rho  v^2.
           Outputs a number representing the drag expressed as force measured in Newtons'''


        return  1/2.  * self.density * self.needleUnit.dragCoefficient * pow(self.physicalVelocity(),2) * (self.needleUnit.surfaceArea)

    def newLinearNeedlePosition(self, aTorqueValue):
        '''Computes the new position of the needle taking into consideration 
           (a simplified version of) the forces acting on the needle'''


        '''First, add to the  force acting on the needle the drag force 
           produced by the fluid in the trough the  needle is moving through. 
           In the original Homeostat,  other factors related to the  physical 
           characteristics of the device, affect the net force affecting the needle,  
           including the potential through the trough, the friction at the vane, etc. 
           These factors are ignored here'''
        
        totalForce = aTorqueValue + self.drag()
            
        "Then compute displacement according to Newton's second law"    
            
        acceleration = totalForce / self.needleUnit.mass                   # As per  Newton's second law 
        displacement = self.currentVelocity + (1 / 2. * acceleration)      #  x - x0 = v0t + 1/2 a t, with t obviously =  1 
    
        "Testing"
        if self.debugMode:      
            outputString = ""
            outputString += ("At time: %u unit %s current pos is %.3f and the new pos. is %.3f with velocity %.3f, new acc. %.3f, displacement of %.3f and new torque. %.3f \n" %
                                (self.time + 1, 
                                self.name, 
                                self.criticalDeviation, 
                                (self.criticalDeviation + self.currentVelocity), 
                                self.currentVelocity, 
                                displacement, 
                                acceleration, 
                                aTorqueValue))
            sys.stderr.write(outputString)

            if (((self.criticalDeviation + displacement) > self.maxDeviation) or  ((self.criticalDeviation + displacement) < self.minDeviation)):
                outputString = "NEW CRITICAL DEVIATION WOULD BE OVER LIMITS WITH VALUE: %.3f \n" % (self.criticalDeviation + displacement)
                sys.stderr.write(outputString)
        
        return self.criticalDeviation + displacement

    def newNeedlePosition(self, aTorqueValue):
        '''Compute the new needle position on the basis of aTorqueValue, 
           which represents the torque applied to the unit's needle'''
    
        if self.needleCompMethod == 'linear':
            return self.newLinearNeedlePosition(aTorqueValue)
        else:
            return self.newRandomNeedlePosition       # defaults to a random computation method if the method is not specified

    def physicalForce(self, aTorqueValue):
        '''Converts the torque coming into a unit into 
           a force expressed in real physical units n (i.e. Newtons)'''

        return aTorqueValue * (self.physicalParameters['massEquivalent'] * 
                               self.physicalParameters['lengthEquivalent']) / (pow(self.physicalParameters['timeEquivalent'],2))

    def reynoldsNumber(self):
        '''Compute the Reynolds number of the physical flow (the needle in the trough), 
           according to the formula:
           Re = 2 a rho v / eta'''

        viscosityInSiUnits = self.viscosity / 1000  # convert viscosity from centiPoise to Pascal/second"

        return  (2 * self.needleUnit.surfaceArea * self.density * self. physicalVelocity) / viscosityInSiUnits

    def selfUpdate(self):
        '''This is the master loop for the unit. It goes through the following sequence:
           1. compute new needle's deviation (nextDeviation (includes reading inputs))
           2. updates the current output on the basis of the deviation.
           3. check whether it's time to check the essential value and if so do it and 
              update the counter (uniselectorTime) [this might change the weight of the connections]
           4. Compute the new velocity on the basis of the displacement
           5. Move the needle to new position and compute new output'''

        
        "1. compute where the needle should move to"

        self.computeNextDeviation()

        "2. update times"
        self.updateTime()
        self.updateUniselectorTime()

        '''3. check whether it's time to check the uniselector/detection mechanism and if so do it. 
           Register that the uniselector is active in an instance variable'''
        
        if (self.uniselectorTime >= self.uniselectorTimeInterval and
            self.uniselectorActive):
            if self.essentialVariableIsCritical():
                if self.debugMode == True:
                    sys.stderr.write(('############################################ Operating uniselector for unit %s' % self.name))
                self.operateUniselector()
                self.uniselectorActivated = 1
            else:
                self.uniselectorActivated = 0
            self.uniselectorTime = 0
        else:
            self.uniselectorActivated = 0        

        ''''4. Compute new current velocity according to classic Newtonian formula: x-x0 = 1/2t (v-v0)  where:
        x0 = criticalDeviation
        x = newDeviation
        v0 = currentVelocity
        Solving for v we get: v = 2(x-x0) -v0'''
        
        if not (self.minDeviation < self.nextDeviation < self.maxDeviation):
            newDeviation = self.clipDeviation(self.nextDeviation)
            self.currentVelocity = 0
            "currentVelocity := newDeviation-criticalDeviation."             #old version"
        else:
            newDeviation = self.nextDeviation
            self.currentVelocity = 2 * (newDeviation -self. criticalDeviation) - self.currentVelocity

        "5. updates the needle's position (critical deviation) with clipping, if necessary, and updates the output"
    
        self.criticalDeviation =  newDeviation
        self.computeOutput()
        nextDeviation = 0

    def stokesLawDrag(self):
        '''Compute the physical drag on the needle according to Stokes equation: 
           D = 6 pi r eta v.
          Output is negated, since Drag's sign is always  opposite  to velocity.
          Instead of the radius of the sphere (as in Stokes' law), it uses the surface area of the needle.'''

        return - 6 * np.pi * (sqrt(self.needleUnit.surfaceArea / np.pi) * self.viscosity * self.currentVelocity) 
