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
        therefore, for its sensitivity to external forces (inputs). The default value is stored
        in the superclass (HomeoUnit) dictionary. We need to initialize it 
        to a rather large value (expressed in internal units) to ensure a minimum
        of stability 
        '''
        
        "initialize according to superclass first"
        super(HomeoUnitNewtonian, self).__init__()


    def clearFutureValues(self):
        "sets to 0 the internal values used for computing future states. "


        self.nextDeviation =  0
        self.inputTorque =  0
        self.currentOutput = 0
        self.currentVelocity = 0
        
#===============================================================================  
# Running methods
#===============================================================================

    def drag(self):
        '''Output the drag force acting on the unit as
           a result of the viscosity in the trough and 
           the velocity of the needle.'''
        #=======================================================================
        # sys.stderr.write("The dragEquation drag for unit %s is %e\n The velocity is %f and the physical velocity is %f\n" % (self.name, 
        #                                                                                                                    self.dragEquationDrag(),
        #                                                                                                                    self.currentVelocity,
        #                                                                                                                    self.physicalVelocity()))
        # sys.stderr.write("The stokesLawDrag is %f\n" % self.stokesLawDrag())
        # sys.stderr.write("The delta between dragEquation drag and stokesLawDrag is %f\n" % (self.stokesLawDrag() - self.dragEquationDrag()))
        #=======================================================================
#        return self.dragEquationDrag()
        return self.stokesLawDrag()

    def dragDummy(self):
        "Used for testing purposes"

        return  0

    def dragEquationDrag(self):
        '''The drag equation for high Reynolds numbers: 
           
           D = 1/2  C A rho  v^2, where:
           
           D = Drag                                  (in Newton)
           C = drag coefficient                      (dimensionless---set to 1 as default by NeedleUnit)
           rho = mass density of fluid               (kg/m^3 --- density of the fluid)
           A = reference area                        ( ---cross-sectional area of the needle)
           v = velocity of object relative to fluid  (m/s ---)
           
           Considering that drag coefficient, reference area and 1/2 are all constants, we include all of them into the 
           density parameters and simply return a force equal to the density times the square of velocity. We also
           use viscosity instead of density, since the physical difference between the two is irrelevant in the context
           of our model.
           Output is negated, since Drag's sign is always opposite  to velocity.
        '''

        if self.debugMode == True:
            print "Computing drag's equation drag"

        return  - self.viscosity * pow(self.currentVelocity,2)


    def stokesLawDrag(self):
        '''The  physical drag on the needle is, according to Stokes equation: 
           D = 6 pi r eta v.
           Output is negated, since Drag's sign is always  opposite  to velocity.
           We compact all the constant parameters (6, pi, r, and eta) into the single viscosity parameter
           and simply return the product of viscosity and current velocity
        '''
        if self.debugMode == True:
            print "Computing Stokes law's Drag"

        return - self.viscosity * self.currentVelocity 

    
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

    def selfUpdate(self):
        '''This is the master loop for the unit. It goes through the following sequence:
           1. compute new needle's deviation (nextDeviation (includes reading inputs))
           2. check whether it's time to check the essential value and if so do it and 
              update the counter (uniselectorTime) [this might change the weight of the connections]
           3. Compute the new velocity on the basis of the displacement
           4. Move the needle to new position and compute new output'''

        
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
        self.nextDeviation = 0
        if self.debugMode:
            print "%s has crit dev of: %f and output of: %f" % (self.name, self.criticalDeviation, self.currentOutput)

