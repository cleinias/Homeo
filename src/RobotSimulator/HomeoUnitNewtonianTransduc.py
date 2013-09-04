'''
Created on Sep 3, 2013

@author: stefano
'''
from Core.HomeoUnitNewtonian import HomeoUnitNewtonian


class HomeoUnitNewtonianTransducer(HomeoUnitNewtonian):
    '''
    HomeoUnitNewtonianTransducer is a HomeoUnitNewtonian Unit with 
    an added transducer. Whe it self updates, it also transmits
    its own value to the transducer.
    Notice that proper setup of the transducer is responsibility 
    of the calling class/instance
    Instance variable:
    transducer <aTransducer> an instance of Transducer or a subclass thereof 
    '''


    def __init__(selfparams):
        '''
        Initialize according to superclass
        '''
        super(HomeoUnitNewtonianTransducer, self).__init__()
    
    def setTransducer(self, aTransducer):
        self._transducer = aTransducer
    def getTransducer(self):
        return self._transducer
    transducer = property(fget = lambda self: self.getTransducer(),
                          fset = lambda self, aValue: self.setTransducer(aValue))
    
    def selfUpdate(self):
        '''First run the self-update function of superclass, 
            then convert unit-value to actuator value,
            then operate actuator'''
        super(HomeoUnitNewtonianTransducer, self).selfUpdate()
#===============================================================================
# 
# to finish from here on        
#        
#        self._transducer.func??????????????
#        self._transducer.runOnce()
#===============================================================================