from __future__ import division
from math import sqrt
from ctypes import c_ubyte
from string import zfill

def withAllSubclasses(aClass):
    """
    Return a list with aClass and all its first-level subclasses
    """
    subs = []
    subs.append(aClass)
    subs.extend([x for x in aClass.__subclasses__()])
    return subs

    
def rchop(aString, ending):
    if str(aString).endswith(ending):
        return str(aString)[:-len(ending)]
    return str(aString)    
    
class SubclassResponsibility(Exception):
    pass

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
    
def scaleTo(fromRange,toRange, value):
    """Linearly scale a value from its original
       fromRange to toRange
       fromRange and toRange are 2-element lists of numbers"""
       
    return (value - fromRange[0]) * (toRange[1]-toRange[0]) / (fromRange[1]-fromRange[0]) + toRange[0]

def distance(pointA3D, pointB3D):
    "Return Euclidean distance between two 3D points"    
    return sqrt((pointA3D[0]-pointB3D[0])**2 + (pointA3D[1]-pointB3D[1])**2 + (pointA3D[2]-pointB3D[2])**2)

def asByteArray(m_string):
    return (c_ubyte * len(m_string)).from_buffer_copy(m_string)

def fmtTimefromSecs(deltaInSeconds):
    """Python does not have built-in functions to format a timedelta in
       hour/minutes/seconds.
       Return a string formatted as hh:mm:ss"""
    hoursOut = deltaInSeconds // 3600
    minutesOut = (deltaInSeconds - (hoursOut*3600))  // 60
    secondsOut = deltaInSeconds - (hoursOut * 3600) - (minutesOut * 60)
    return str(hoursOut).zfill(2)+ ":"+str(minutesOut).zfill(2)+":"+str(secondsOut).zfill(2)