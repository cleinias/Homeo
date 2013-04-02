'''
Created on Mar 29, 2013

@author: stefano
'''
import numpy as np

class Test_Property(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self._ivar = 0
    
    def setivar(self, aValue):
            self._ivar = np.random.uniform(aValue -1, aValue +1)
        
    def getivar(self):
        return self._ivar
    
    ivar = property(getivar,setivar)
    
    
class C(object):
    def __init__(self):
        self.__x__ = None
        self._y = None
#        self.x = None
    
    def getx(self):
        return self.__x__
    def setx(self, value):
        self.__x__ = value
        self._y = value
    def delx(self):
        del self.___x__
    x = property(fget = lambda self: self.getx(),
                 fset = lambda self,value: self.setx(value),
                 fdel = lambda self: self.delx())
    
class D(C):
    def __init__(self):
        self._x = None
        
class E(object):
    def __init__(self):
        self._x = 0
    
    def pippodai(self):
        return self._x
    def pippometti(self,value):
        self._x = -100
    x = property(fget = lambda self: self.pippodai(),
                 fset = lambda self, value: self.pippometti(value))
    
class F(object):
    def __init__(self):
        self.x = None
    def pippodai(self):
        return self._x
    def pippometti(self,value):
        self._x = -100
    x = property(fget = lambda self: self.pippodai(),
                 fset = lambda self, value: self.pippometti(value))
class G(object):
    def __init__(self):
        self.x = None
    def getx(self):
        return self._x
    def setx(self, value):
        self._x = value
    def delx(self):
        del self._x
    x = property(fget = lambda self: self.getx(),
                 fset = lambda self,value: self.setx(value))
    
        
    