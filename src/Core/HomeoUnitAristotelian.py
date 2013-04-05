'''
Created on Mar 17, 2013

@author: stefano
'''
from Core.HomeoUnit import  *

class HomeoUnitAristotelian(HomeoUnit):
    '''
    HomeoUnitAristotelian  is a HomeoUnit whose needle's displacement is computed according 
    to (a simplified version of) Aristotelian physics. In brief, the needle's displacement
    is proportional to  velocity, not acceleration. In other words, the needle will stop moving
    unless it is acted upon by a force (torque) coming from the other units.
       
    The computations take into account also the frictional forces acting on the needle
    due to the viscosity of the medium it goes through by subtracting from the input torque
    the viscosity of the medium.
    
    The class does not add any instance variable to HomeoUnit, it just overrides some of 
    the computation methods.  
    '''


    def __init__(self):
        '''
        Initialize accoding to superclass
        '''
        super(HomeoUnitAristotelian, self).__init__()
        
#===============================================================================
# Running methods
#===============================================================================

    def dragOn(self,aForce):
        '''Compute the frictional forces acting on the Aristotelian unit. 
           Only considers the viscosity of the medium in the trough the needle 
           moves through, disregarding other possible frictional forces'''
 
        "Converts the actual viscosity to a ratio"

        viscRatio = self.viscosity / (self.DefaultParameters['maxViscosity'])
        return - (aForce * viscRatio)

    def newLinearNeedlePosition(self, aTorqueValue):
        '''See method HomeoUnit>>newNeedlePosition for an extended comment 
           on how to compute the displacement of the needle. 
           Briefly, here we just sum aTorqueValue to the current deviation'''


        '''Compute the net force acting on the needle by adding the 
        (negative) force produduced by the drag and/ or frictional forces)'''
        
        totalForce = aTorqueValue + self.dragOn(aTorqueValue)              

        '''In an Aristotelian model, the change in displacement (= the velocity) 
           is equal to the force affecting the unit divided by the  mass: 
           F = mv or v = F/m'''
        
        newVelocity = totalForce / self.needleUnit.mass                              
        
        "Testing"
        if self.debugMode:
            outputString = ''
            outputString.append('New position at time: %u for unit %s will be %.3f ' %
                                self.time + 1,
                                self.name,
                                self.criticalDeviation + (aTorqueValue * self.viscosity))
            
        '''In an Aristotelian model, new displacement is 
           old displacement plus velocity: x = x0 + vt, with t obviously = 1.'''
        return self.criticalDeviation + newVelocity                                                               


        