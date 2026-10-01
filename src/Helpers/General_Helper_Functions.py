from math import sqrt
from ctypes import c_ubyte
import os


def simulations_data_dir():
    """Return the root SimulationsData directory.

    Resolution order:
      1. $HOMEO_DATA_DIR, if set (for HPC jobs writing to scratch)
      2. Cybernetics-research/SimulationsData/, when Homeo is a submodule of it
      3. Sibling Cybernetics-research/SimulationsData/ (pre-2026-10-01 layout)
      4. Homeo/SimulationsData/ (standalone checkout fallback)

    The directory is created if it does not exist.

    ~/.HomeoSimDataDir.txt is deliberately NOT consulted: HomeoGeneralGUI and
    SimulatorBackend write the *current session* directory there (for Webots
    controllers), so using it as the root nested every later run inside the
    last session's folder.
    """
    # 1. Explicit override, e.g. $SCRATCH on a cluster.  An environment
    #    variable, deliberately not a file: the old ~/.HomeoSimDataDir.txt
    #    mechanism conflated "current session" with "root directory".
    env_dir = os.environ.get('HOMEO_DATA_DIR')
    if env_dir:
        os.makedirs(env_dir, exist_ok=True)
        return env_dir

    # Locate Homeo project root  (…/Homeo)
    # General_Helper_Functions.py lives at  src/Helpers/
    _this = os.path.dirname(os.path.abspath(__file__))      # src/Helpers
    _src  = os.path.dirname(_this)                           # src
    _homeo = os.path.dirname(_src)                           # Homeo
    _parent = os.path.dirname(_homeo)                        # parent of Homeo

    # 2. Homeo is a submodule of Cybernetics-research, so the research repo is
    #    Homeo's own parent directory.  This is the layout since 2026-10-01.
    if os.path.basename(_parent) == "Cybernetics-research":
        research = os.path.join(_parent, "SimulationsData")
        os.makedirs(research, exist_ok=True)
        return research

    # 3. Pre-2026-10-01 layout: Cybernetics-research sat next to Homeo.
    sibling = os.path.join(_parent, "Cybernetics-research")
    if os.path.isdir(sibling):
        research = os.path.join(sibling, "SimulationsData")
        os.makedirs(research, exist_ok=True)
        return research

    # 4. Standalone checkout (e.g. $SCRATCH on the cluster): keep data in the repo.
    legacy = os.path.join(_homeo, "SimulationsData")
    os.makedirs(legacy, exist_ok=True)
    return legacy


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
    for angle in range(0 + step, 180+step, step):
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
    
