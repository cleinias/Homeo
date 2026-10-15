from math import sqrt
import os
import re


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


def dated_data_dir():
    """Return today's data directory, simulations_data_dir()/SimsData-<date>,
    creating it if needed.

    The default home of output whose caller names no directory, and the same
    directory the experiment scripts write to.  Defaults used to be the current
    directory, so a run started anywhere other than a data directory left its
    files there -- typically in src/, where every replay and GA test left a
    stray trajData-ID-Unspecified-<timestamp>.traj.
    """
    import time
    path = os.path.join(simulations_data_dir(), 'SimsData-' + time.strftime("%Y-%m-%d"))
    os.makedirs(path, exist_ok=True)
    return path


def unique_stem(directory, stem, extensions):
    """stem, or stem-2, stem-3, ...: the first for which no file
    directory/<stem><ext> exists for any of extensions.

    Output names carry a whole-second timestamp (plus run_tag()), so two runs
    started in the same second in one process got the same name and the
    second overwrote, or appended to, the first's files (review finding
    HV-09).  Files written together (a run's .log, .json and .statelog; a
    .traj) take one stem from one call, so they stay paired."""
    candidate, n = stem, 1
    while any(os.path.exists(os.path.join(directory, candidate + ext)) for ext in extensions):
        n += 1
        candidate = '%s-%d' % (stem, n)
    return candidate


def report_ticks(report_interval, total_steps):
    """The ticks at which a run reports: every report_interval ticks, and at
    total_steps whatever its remainder.  The loops used
    range(report_interval, total_steps + 1, report_interval), which silently
    dropped the remainder (--steps 1250 ran 1000) and never ran at all when
    total_steps < report_interval (review finding RE-10)."""
    ticks = list(range(report_interval, total_steps, report_interval))
    if total_steps > 0:
        ticks.append(total_steps)
    return ticks


# The files a run's conditions are logged to (see unique_stem)
RUN_LOG_EXTENSIONS = ('.log', '.json', '.statelog')


def run_tag():
    """Return the current run's serial as a filename suffix, or '' if unset.

    Reads $HOMEO_RUN_TAG, set by --run-tag (see the experiment entry points) and
    by the HPC array scripts, which pass the array index.  The value is appended
    to every output filename just before the extension:

        phototaxis_..._continuous-2026-10-01-13-23-38-02.json

    Why this exists: output filenames were distinguished only by a
    "%Y-%m-%d-%H-%M-%S" timestamp, so two array tasks that started within the
    same second got byte-identical names.  That was harmless while each task
    wrote to its own directory, but it silently lost files the moment an array's
    results were merged into one folder -- which is now the default layout.  A
    serial makes the names unique by construction rather than by luck of the
    clock, and keeps them sortable by task.

    Only [A-Za-z0-9._-] survives sanitising, so a tag can never introduce a
    path separator or escape the output directory.
    """
    tag = os.environ.get('HOMEO_RUN_TAG', '')
    tag = re.sub(r'[^A-Za-z0-9._-]', '', tag).lstrip('-.')
    return '-' + tag if tag else ''


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

def scaleTo(fromRange,toRange, value):
    """Linearly scale a value from its original
       fromRange to toRange
       fromRange and toRange are 2-element lists of numbers"""
       
    return (value - fromRange[0]) * (toRange[1]-toRange[0]) / (fromRange[1]-fromRange[0]) + toRange[0]

def distance(pointA3D, pointB3D):
    "Return Euclidean distance between two 3D points"    
    return sqrt((pointA3D[0]-pointB3D[0])**2 + (pointA3D[1]-pointB3D[1])**2 + (pointA3D[2]-pointB3D[2])**2)

def normalize(vect):
    vectNorm = sqrt(vect[0]**2+vect[1]**2)
    if vectNorm == 0:
        return [0 for x in vect]
    else:
        return [x/vectNorm for x in vect]
