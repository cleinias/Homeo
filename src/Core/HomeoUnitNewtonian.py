'''
Created on Mar 17, 2013

@author: stefano
'''
from  Core.HomeoUnit import *
from Core.HomeoJIT import _jit_needle_position_newtonian
from Core.HomeoUniselectorContinuous import HomeoUniselectorContinuous
import numpy as np
from math import sqrt
from Helpers.General_Helper_Functions import *
from Helpers.ExceptionAndDebugClasses import hDebug

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
        self._dt_fast = 1.0
        self._lastAcceleration = 0.0

    # dt_fast: how much of the needle's own time passes in one tick.  Only the
    # needle step reads it; noise, the connections, both uniselectors and the
    # world advance once per tick whatever its value.  It is no time step but
    # a rescaling of the needle: (mass m, viscosity c, dt_fast dt) moves
    # exactly as (m / dt**2, c / dt, 1) -- the spring of the self-connection
    # and the stops are unchanged (HomeoUnitNewtonianTest).  Kept, at 1 by
    # default, only to replay the genomes of the GA setups that evolved it,
    # before 15 Oct 2026; the setups since evolve mass and viscosity over
    # ranges that cover what it reached (review finding CU-11).
    def getDtFast(self):
        return self._dt_fast

    def setDtFast(self, value):
        if value > 0:
            self._dt_fast = float(value)

    dt_fast = property(fget=lambda self: self.getDtFast(),
                       fset=lambda self, value: self.setDtFast(value))

    def setViscosity(self, aValue):
        '''The needle's drag coefficient (Stokes drag, -viscosity * v): any
        value >= 0.  HomeoUnit's ceiling, maxViscosity, belongs to its own
        model, where viscosity is the fraction viscosity / maxViscosity of the
        torque cancelled; a drag coefficient has none, and the GA setups since
        15 Oct 2026 draw it up to 50 (review finding CU-11).'''
        try:
            aValue = float(aValue)
        except ValueError:
            sys.stderr.write("Tried to assign a non-numeric value to unit  %s's Viscosity. The value was: %s\n" % (self.name, aValue))
            return
        if aValue < 0:
            raise HomeoUnitError("The viscosity of a Newtonian unit must not be negative")
        self._viscosity = aValue
        emitter(self).viscosityChanged.emit(self._viscosity)
        emitter(self).viscosityChangedLineEdit.emit(str(round(self._viscosity, 4)))

    def clearFutureValues(self):
        "As HomeoUnit's, and the needle stops."

        super(HomeoUnitNewtonian, self).clearFutureValues()
        self.currentVelocity = 0
        self._lastAcceleration = 0.0
        
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
           Drag's sign is always opposite to velocity: -viscosity * v * |v|
           (it was -viscosity * v^2, which pushed a needle moving backwards
           further back: review finding CU-12).  Unused by the dynamics,
           whose step uses Stokes drag (drag()).
        '''

        if self.debugMode == True:
            print("Computing drag's equation drag")

        return - self.viscosity * self.currentVelocity * abs(self.currentVelocity)


    def stokesLawDrag(self):
        '''The  physical drag on the needle is, according to Stokes equation: 
           D = 6 pi r eta v.
           Output is negated, since Drag's sign is always  opposite  to velocity.
           We compact all the constant parameters (6, pi, r, and eta) into the single viscosity parameter
           and simply return the product of viscosity and current velocity
        '''
        if self.debugMode == True:
            print("Computing Stokes law's Drag")

        return - self.viscosity * self.currentVelocity 

    
    def newLinearNeedlePosition(self, aTorqueValue):
        '''Computes the new position of the needle taking into consideration
           (a simplified version of) the forces acting on the needle'''

        '''Newton's second law with the drag force produced by the fluid in
           the trough the needle moves through (Stokes drag, -viscosity * v),
           the torque held constant over the step.  The step is the exact
           solution of m dv/dt = torque - viscosity * v (see
           _jit_needle_position_newtonian, which both paths use): an explicit
           step for the drag is unstable when viscosity * dt_fast / mass > 2.
           In the original Homeostat,  other factors related to the  physical
           characteristics of the device, affect the net force affecting the needle,
           including the potential through the trough, the friction at the vane, etc.
           These factors are ignored here'''

        torque, stiffness = self.selfSpring(aTorqueValue)
        new_pos, acceleration = _jit_needle_position_newtonian(
            torque, self._viscosity, self._currentVelocity,
            self._needleUnit._mass, self._criticalDeviation, self._dt_fast,
            stiffness)
        self._lastAcceleration = acceleration
        if self._headless:
            return new_pos
        displacement = new_pos - self.criticalDeviation

        try:
            #print "My name is %s and I have a fileOut object to write to: %s " % (self.name, self._fileOut)
            #===================================================================
            # print "critDev: %3f\t curVel: %3f\t inputTorque: %3f\t torque: %3f\t drag: %3f\t acc: %3f\t mass: %3f\t displ: %3f\t newCrit: %3f\t noise: %3f" % (self.criticalDeviation,
            #                                                                                                                                 self.currentVelocity,
            #                                                                                                                                 self.inputTorque,
            #                                                                                                                                  aTorqueValue,
            #                                                                                                                                 self.drag(),
            #                                                                                                                                 acceleration,
            #                                                                                                                                 self.needleUnit.mass,
            #                                                                                                                                 displacement,
            #                                                                                                                                 self.criticalDeviation + displacement,
            #                                                                                                                                 self.noise)
            #===================================================================

            self._fileOut.write(str(self.criticalDeviation) + ',')
            self._fileOut.write(str(self.currentVelocity) + ',')
            self._fileOut.write(str(aTorqueValue) + ',')
            self._fileOut.write(str(self.drag()) + ',')
            self._fileOut.write(str(acceleration) + ',')
            self._fileOut.write(str(self.needleUnit.mass) + ',')
            self._fileOut.write(str(displacement) + ',')
            self._fileOut.write(str(self.criticalDeviation + displacement) + ',')
            self._fileOut.write(str(self.noise) + '\n')
            self._fileOut.flush()            
        except AttributeError:
            pass
            #print "My name is %s and type is %s" %(self.name, type(self))
        
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

    def selfSpring(self, aTorqueValue):
        '''The self-connection as a spring: (torque, stiffness) for the step.

        aTorqueValue includes the self-connection's term W * output, W its
        signed weight, the output read before the step.  Between the stops the
        output is linear in the deviation, output = s x + o, so the self-term
        is a force W (s x + o) that changes with the needle's position during
        the step: a spring of stiffness k = -W s (negative feedback, k > 0)
        or a negative spring (positive feedback).  Returned: the torque at the
        needle's current position, with the self-term at that position, and
        k, for the exact step (_jit_needle_position_newtonian).  The
        self-connection's noise stays in the torque, held over the step.
        Without an active self-connection: (aTorqueValue, 0.0).'''
        if self._headless:
            i = getattr(self, '_jit_self', None)
            if i is None:                       # arrays built before this attribute
                self._sync_jit_arrays()
                i = self._jit_self
            if i < 0:
                return aTorqueValue, 0.0
            w = self._jit_weights[i] * self._jit_switches[i]
            out = self._jit_outputs[i]
        else:
            conn = next((c for c in self.inputConnections
                         if c._incomingUnit is self), None)
            if conn is None or not (conn.isActive() and self.isActive()):
                return aTorqueValue, 0.0
            w = conn.weight * conn.switch
            out = self._currentOutput
        if w == 0.0:
            return aTorqueValue, 0.0
        low_dev = self.minDeviation
        slope = ((self._outputRange['high'] - self._outputRange['low'])
                 / (self._maxDeviation - low_dev))
        out_here = (self._criticalDeviation - low_dev) * slope + self._outputRange['low']
        return aTorqueValue + w * (out_here - out), -w * slope

    # Newton's second law is the 'linear' computation; the others have no
    # Newtonian version (a needle with mass and velocity).
    NEEDLE_COMP_METHODS = ('linear',)

    def newNeedlePosition(self, aTorqueValue):
        '''Compute the new needle position on the basis of aTorqueValue, 
           which represents the torque applied to the unit's needle.  Only
           'linear' (setNeedleCompMethod refuses the others: they crashed here,
           review finding CU-16).'''
    
        return self.newLinearNeedlePosition(aTorqueValue)

    def selfUpdate(self):
        '''This is the master loop for the unit. It goes through the following sequence:
           1. compute new needle's deviation (nextDeviation (includes reading inputs))
           2. weight adaptation: either discrete uniselector (periodic check + random resampling)
              or continuous uniselector (Ornstein-Uhlenbeck drift every timestep)
           3. Compute the new velocity on the basis of the displacement
           4. Move the needle to new position and compute new output'''


        "1. compute where the needle should move to"

        self.computeNextDeviation()

        "2. update times"
        self.updateTime()

        '''3. Weight adaptation --- two modes depending on uniselector type.
           Discrete (Ashby/UniformRandom): periodic check + random resampling.
           Continuous (OU process): evolve weights every timestep.'''

        if self.uniselectorActive:
            if isinstance(self.uniselector, HomeoUniselectorContinuous):
                "Continuous mode: evolve weights at every timestep"
                # An OU uniselector never fires: the flag stays 0, even after
                # a discrete uniselector left it at 1 (review finding CD-12)
                self.uniselectorActivated = 0
                stress = self.stressLevel()
                if self._headless:
                    if self._jit_dirty:
                        self._sync_jit_arrays()
                    self.uniselector.evolve_weights_jit(
                        self._jit_weights, self._jit_switches, stress,
                        self._jit_evolvable)
                    '''Do NOT mark the arrays dirty here -- see the identical
                       branch in HomeoUnit.selfUpdate() for why.'''
                else:
                    self.uniselector.evolve_weights(self.inputConnections, stress)
                    self._jit_dirty = True
            else:
                "Discrete mode: steps while critical, at most once per interval"
                self.operateUniselectorIfCritical()
        else:
            self.uniselectorActivated = 0

        '''4. Compute new current velocity: v_new = v_old + a * dt_fast, with a
        the step's mean acceleration (see newLinearNeedlePosition).  At a stop
        the needle halts.'''

        if not (self.minDeviation < self.nextDeviation < self.maxDeviation):
            newDeviation = self.clipDeviation(self.nextDeviation)
            self.currentVelocity = 0
        else:
            newDeviation = self.nextDeviation
            self.currentVelocity = self.currentVelocity + self._lastAcceleration * self._dt_fast

        "5. updates the needle's position (critical deviation) with clipping, if necessary, and updates the output"

        self.criticalDeviation = newDeviation
        self.computeOutput()
        self.nextDeviation = 0
        if self.debugMode:
            print("%s has crit dev of: %f and output of: %f" % (self.name, self.criticalDeviation, self.currentOutput))
