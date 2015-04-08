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

def normalize(vect):
    vectNorm = sqrt(vect[0]**2+vect[1]**2)
    if vectNorm == 0:
        return [0 for x in vect]
    else:
        return [x/vectNorm for x in vect]

def sensorCoordsFromAngle(radius = 0.063, step= 1, rotation = 0):
    """Returns a dictionary of coordinates for all sensors positions on the outer surface 
       of a circle of radius 'radius' (representing a simplified Khepera-like
       robot) at 'step' degrees  intervals  from the forward facing position
       (i.e. the Y axis in 2D geometry. Positive positions are to the right side, 
       and negative positions are to the left side. 
       The coordinates are rotated counterclockwise
       by the 'rotation' amount in degrees (in order to convert to standard Cartesian
       coordinates, enter a rotation of 270, equal  = 90 CW"""
    
    from math import pi, sin, cos,  radians
    forFacAngle = pi/2   
    coords = {}
    for angle in xrange(0 + step, 180+step, step):
        coords[angle]=[(radius * cos(forFacAngle - radians(angle))), (radius * sin(forFacAngle - radians(angle)))]
        coords[-angle]=[(radius * cos(forFacAngle + radians(angle))), (radius * sin(forFacAngle + radians(angle)))]
    if rotation == 0:
        return coords
    else:
        from numpy import mat, reshape
        rotAng = radians(rotation)
        rotMatrix = mat([cos(rotAng), -sin(rotAng)],[sin(rotAng),cos(rotAng)])
        for key in coords:
            coordVector = reshape(coords[key], (2,1))  
            coords[key] = (rotMatrix * coordVector).A1
        return coords
    
