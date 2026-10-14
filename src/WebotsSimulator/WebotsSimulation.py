'''
Webots as Homeo's robot simulator: the Webots twin of KheperaSimulation.

Homeo runs Webots and is its robot's controller -- an *extern* controller,
in Homeo's own process, through Webots' Python controller library -- and a
supervisor, which reads the poses it records.  The world advances only when
Homeo steps it: once per homeostat tick (tickAdvance), after every unit has
updated, as KheperaSimulation's synchronous stepping does.  Nothing goes
over a socket of Homeo's own: the TCP bridge of 2013-2026 is gone.

WebotsSimulation offers the parts of KheperaSimulation's interface that
the experiments use -- allBodies (the robot and the lights), setupWorld,
tickAdvance, the trajectory writer and its files, dataDir, experimentName
-- so that SimulatorBackendWEBOTS can hand it out as its kheperaSimulation
and the experiment setups and transducers (HOMEO_DiffMotor,
HOMEO_LightSensor, HOMEO_QualitySensor) work unchanged.

The robot is the e-puck2 of Homeo's HomeoEpuck.proto (Webots/protos), the
same robot as KheperaRobot's model 'epuck2':
- its wheels take speeds in rad/s, capped at KheperaRobot's cap (24.3 mm/s
  at the rim);
- an eye's irradiance is the mean of its two LightSensors' readings (ls0
  and ls1 on the right, ls7 and ls6 on the left), whose lookup table is
  the identity, and the eye's response is KheperaRobot's (eyeResponse);
- the other qualities of the Vehicle 3c world (temperature, oxygen,
  organic) have no Webots physics: they are computed here, from the
  sensors' and the sources' poses, with exactly the Box2D formula
  (KheperaRobot.irradAtSensor) -- "virtual sensors" (decision of 14 Oct
  2026).  Real gradients (diffusion) are a TODO of the research journal.

One process can control one Webots robot (the controller library allows
one), so the simulation is shared: a second setupWorld in the same process
resets the world it runs, or loads another.

Darkness sources (negative intensity, --dark) are not physical lights and
are refused.

@author: stefano
'''
import atexit
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from math import atan2, degrees, cos, sin, sqrt

from Box2D import b2Vec2

from Helpers.RobotTrajectoryWriter import RobotTrajectoryWriter
from KheperaSimulator.KheperaSimulator import KheperaRobot


WEBOTS_PROJECT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                               os.pardir, 'Webots'))

# Homeo's worlds (KheperaSimulation's names) and their Webots files:
# (world file, the sources: name -> (quality, intensity)).  A source of
# quality 'light' is a PointLight of the same DEF name; the others are
# markers, whose positions are read from their DEF nodes.
WORLDS = {
    'kheperaBraitenberg2_HOMEO_World': ('homeo_braitenberg2.wbt',
                                        {'TARGET': ('light', None)}),
    'kheperaBraitenberg3c_HOMEO_World': ('homeo_braitenberg3c.wbt',
                                         {'LIGHT1': ('light', None),
                                          'TEMP1': ('temperature', 80),
                                          'TEMP2': ('temperature', 80),
                                          'OXY1': ('oxygen', 100),
                                          'ORG1': ('organic', 100)}),
}

ROBOT_DEF = 'ROBOT'
ROBOT_NAME = 'e-puck'


def webots_home():
    "Where Webots is installed: $WEBOTS_HOME, else from the webots command on the PATH."
    home = os.environ.get('WEBOTS_HOME')
    if home:
        return home
    exe = shutil.which('webots')
    if exe is None:
        raise RuntimeError('Webots not found: set WEBOTS_HOME or put webots on the PATH')
    exe = os.path.realpath(exe)
    for candidate in (os.path.dirname(exe), os.path.dirname(os.path.dirname(exe)),
                      '/usr/local/webots'):
        if os.path.isdir(os.path.join(candidate, 'lib', 'controller', 'python')):
            return candidate
    raise RuntimeError('Webots found at %s, but not its controller library' % exe)


def available():
    "Can this machine run Webots here (installed, and a display or xvfb-run)?"
    try:
        webots_home()
    except RuntimeError:
        return False
    return bool(os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')
                or shutil.which('xvfb-run'))


def _free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


class _Pose(object):
    "A body's pose, as KheperaSimulation's bodies offer it: position (b2Vec2) and angle"
    def __init__(self, node):
        self._node = node

    @property
    def position(self):
        x, y, _ = self._node.getPosition()
        return b2Vec2(x, y)

    @property
    def angle(self):
        R = self._node.getOrientation()
        return atan2(R[3], R[0])


class _Eye(object):
    "An eye's settings, kept as KheperaRobot keeps them on its fixtures"
    def __init__(self, name, receptors, fieldOfView):
        self.userData = {name + 'AngleRange': fieldOfView, name + 'Receptors': receptors}


class WebotsLight(object):
    '''A light source, as KheperaSimulation's light bodies offer it:
    userData (intensity, lightPos, attenVec, ambRatio, name, ...) and
    position.  For a PointLight, setting userData['intensity'] sets the
    light's intensity in Webots.'''

    class _UserData(dict):
        def __init__(self, light, *args):
            super().__init__(*args)
            self._light = light

        def __setitem__(self, key, value):
            super().__setitem__(key, value)
            if key in ('intensity', 'lightIntensity'):
                self._light._setIntensity(value)

    def __init__(self, name, quality, node, intensity=None, pointLight=True):
        self._node = node
        self._pointLight = pointLight
        if pointLight:
            location = node.getField('location').getSFVec3f()
            atten = tuple(node.getField('attenuation').getSFVec3f())
            ambient = node.getField('ambientIntensity').getSFFloat()
            intensity = node.getField('intensity').getSFFloat()
            if ambient != 0:
                raise ValueError('light %s: Homeo lights have no ambient part' % name)
        else:
            location = node.getPosition()
            atten = (0, 0, 1)
        self._position = b2Vec2(location[0], location[1])
        self.userData = self._UserData(self, {
            'name': name, 'quality': quality, 'intensity': intensity, 'lightIntensity': intensity,
            'lightPos': (location[0], 0, location[1]), 'attenVec': atten, 'ambRatio': 0,
            'lightIsOn': True})

    @property
    def position(self):
        return self._position

    def _setIntensity(self, value):
        if value < 0:
            raise ValueError('Webots has no darkness sources (negative intensity): use the '
                             'Box2D simulator for --dark runs')
        if self._pointLight:
            self._node.getField('intensity').setSFFloat(float(value))


class WebotsRobot(object):
    '''The e-puck2, as KheperaRobot offers it to the transducers and the
    experiments: wheel speeds in rad/s, eyes read through eyeResponse, a
    body with a position and an angle, its geometry.'''

    # The eyes' and the virtual quality sensors' geometry and response: KheperaRobot's
    EPUCK2 = KheperaRobot.EPUCK2
    EYE_RESPONSES = KheperaRobot.EYE_RESPONSES
    setEyeSensitivity = KheperaRobot.setEyeSensitivity
    eyeSettings = KheperaRobot.eyeSettings
    eyeResponse = KheperaRobot.eyeResponse
    getMaxSensorValue = KheperaRobot.getMaxSensorValue
    irradAtSensor = KheperaRobot.irradAtSensor
    _receptorIrrad = KheperaRobot._receptorIrrad

    def __init__(self, supervisor, timeStep):
        self.model = 'epuck2'
        self.eyeRadiusRatio = None
        self.drive = 'webots'
        geometry = self.EPUCK2
        self.diameter = geometry['diameter']
        self.wheelRadius = geometry['wheelRadius']
        self.wheelSeparation = geometry['wheelSeparation']
        self.maxWheelSpeed = KheperaRobot.EPUCK2_CAPPED_WHEEL_SPEED
        self.maxSpeed = self.maxWheelSpeed * self.wheelRadius
        self.eyeFieldOfView = geometry['fieldOfView']
        self._node = supervisor.getSelf()
        self.body = _Pose(self._node)
        self.wheels = {}
        self.rightSpeed = self.leftSpeed = 0
        self._motors = {'left': supervisor.getDevice('left wheel motor'),
                        'right': supervisor.getDevice('right wheel motor')}
        for motor in self._motors.values():
            motor.setPosition(float('inf'))
            motor.setVelocity(0.0)
        self._lightSensors = {}
        self.sensors = {}
        self.eyeReceptors = {}
        for eye, names in geometry['eyes'].items():
            self._addEye(eye, names)
            devices = [supervisor.getDevice(n) for n in names]
            for device in devices:
                device.enable(timeStep)
            self._lightSensors[eye] = devices
        self.detectableLights = []
        self.detectableSources = {}

    def _addEye(self, eye, receptorNames):
        receptors = [self.EPUCK2['receptors'][n] for n in receptorNames]
        receptors = [((float(p[0]), float(p[1])), float(f)) for p, f in receptors]
        self.sensors[eye] = _Eye(eye, receptors, self.eyeFieldOfView)
        self.setEyeSensitivity(eye, threshold=0, saturation=100, response='linear')
        self.eyeReceptors[eye] = receptors

    def addVirtualEye(self, eyeName, likeEye):
        "A virtual eye with likeEye's receptors (the Vehicle 3c quality pairs)"
        self.sensors[eyeName] = _Eye(eyeName, self.eyeReceptors[likeEye], self.eyeFieldOfView)
        self.setEyeSensitivity(eyeName, threshold=0, saturation=100, response='linear')
        self.eyeReceptors[eyeName] = self.eyeReceptors[likeEye]

    # --- wheels, in rad/s, as KheperaRobot's -------------------------------

    def setRightSpeed(self, newSpeed):
        self._setSpeed('right', newSpeed)

    def setLeftSpeed(self, newSpeed):
        self._setSpeed('left', newSpeed)

    def setSpeed(self, newRightSpeed, newLeftSpeed):
        self.setRightSpeed(newRightSpeed)
        self.setLeftSpeed(newLeftSpeed)

    def _setSpeed(self, side, speed):
        speed = max(-self.maxWheelSpeed, min(self.maxWheelSpeed, speed))
        setattr(self, side + 'Speed', speed * self.wheelRadius)
        self._motors[side].setVelocity(speed)

    def getSpeed(self):
        return {'right': self.rightSpeed, 'left': self.leftSpeed}

    def getMaxSpeed(self):
        return {'right': self.maxWheelSpeed, 'left': self.maxWheelSpeed}

    # --- eyes --------------------------------------------------------------

    def lightIrradiance(self, eye):
        "The eye's irradiance from Webots' LightSensors: the mean of its two"
        devices = self._lightSensors[eye]
        return sum(d.getValue() for d in devices) / len(devices)

    def getSensorRead(self, sensorName):
        return self.eyeResponse(sensorName, self.lightIrradiance(sensorName))

    def getSensorReadByQuality(self, sensorName, quality):
        '''Light through the LightSensors of the eye with the same receptors;
        the other qualities through the virtual sensors (irradAtSensor on
        the sources' and the sensors' poses).'''
        if quality == 'light':
            eye = sensorName if sensorName in self._lightSensors else (
                'leftEye' if sensorName.startswith('left') else 'rightEye')
            return self.eyeResponse(sensorName, self.lightIrradiance(eye))
        return self.eyeResponse(sensorName, self.irradAtSensor(sensorName,
                                                               self.detectableSources.get(quality, [])))

    # --- pose and identity --------------------------------------------------

    def setPose(self, x=None, y=None, heading=None):
        '''Put the robot at (x, y), facing heading (degrees, as the .traj
        heading); None keeps a value.  Call before the run's first step.'''
        position = self._node.getPosition()
        nx = position[0] if x is None else x
        ny = position[1] if y is None else y
        angle = self.body.angle if heading is None else heading * 3.141592653589793 / 180
        self._node.getField('translation').setSFVec3f([nx, ny, position[2]])
        self._node.getField('rotation').setSFRotation([0, 0, 1, angle])
        self._node.resetPhysics()

    def setModelName(self, ID_String):
        self._modelName = ID_String

    def getModelName(self):
        return getattr(self, '_modelName', 'Unspecified')


class WebotsSimulation(object):
    '''Webots, run by Homeo, with KheperaSimulation's interface (see the
    module's docstring).

    rendering: show Webots' window and render (for figures), or not
    (--no-rendering, --minimize: batch runs).  mode: Webots' run mode while
    Homeo steps it, 'fast' by default.  stepsPerTick, timeStep: as
    KheperaSimulation's, a tick is two 32 ms steps.'''

    _shared = None           # the one simulation this process runs

    def __init__(self, rendering=False, mode='fast', stepsPerTick=2, timeStep=0.032):
        self.rendering = rendering
        self.mode = mode
        self.stepsPerTick = stepsPerTick
        self.timeStep = timeStep
        self.synchronousStepping = True
        self.robotModel = 'epuck2'
        self.robotEyeRadiusRatio = None
        self.robotName = 'Khepera'
        self.allBodies = {}
        self.experimentName = None
        self.currentStep = 0
        self._process = None
        self._supervisor = None
        self._worldFile = None
        from Helpers.General_Helper_Functions import dated_data_dir
        self.dataDir = dated_data_dir()

    # --- the process ---------------------------------------------------------

    def _launch(self, worldFile):
        home = webots_home()
        port = _free_port()
        command = [os.path.join(home, 'webots') if os.path.exists(os.path.join(home, 'webots'))
                   else 'webots', '--batch', '--mode=%s' % self.mode, '--port=%d' % port,
                   '--stdout', '--stderr']
        env = dict(os.environ)
        if not self.rendering:
            command += ['--no-rendering', '--minimize']
            if not (env.get('DISPLAY') or env.get('WAYLAND_DISPLAY')):
                # No display (a cluster node): a virtual one, software OpenGL
                if shutil.which('xvfb-run') is None:
                    raise RuntimeError('no display, and no xvfb-run to make one for Webots')
                command = ['xvfb-run', '--auto-servernum'] + command
                env['LIBGL_ALWAYS_SOFTWARE'] = 'true'
        self._log = open(os.path.join(self.dataDir, 'webots-%d.log' % port), 'w')
        # Its own process group: `webots` is a script that starts webots-bin,
        # and quit() must stop both (and xvfb-run's server)
        self._process = subprocess.Popen(command + [worldFile], stdout=self._log,
                                         stderr=subprocess.STDOUT, env=env,
                                         start_new_session=True)
        atexit.register(self.quit)
        os.environ['WEBOTS_HOME'] = home
        os.environ['WEBOTS_CONTROLLER_URL'] = 'ipc://%d/%s' % (port, ROBOT_NAME)
        controllerPath = os.path.join(home, 'lib', 'controller', 'python')
        if controllerPath not in sys.path:
            sys.path.insert(0, controllerPath)
        from controller import Supervisor
        self._supervisor = Supervisor()
        self._worldFile = worldFile

    def quit(self):
        '''Stop Webots (at exit, or when asked).  The controller library is
        cleaned up first, while Webots still answers, and Webots is then
        terminated.  The other orders let the library end the process itself
        -- with status 1 if Webots goes first, or, if Webots is asked to quit,
        with that request's status, hiding the run's own (an exception).'''
        if self._supervisor is not None and self._process is not None and self._process.poll() is None:
            try:
                from controller.wb import wb
                wb.wb_robot_cleanup()
            except Exception:
                pass
        if self._process is not None:
            try:
                os.killpg(self._process.pid, signal.SIGTERM)
                self._process.wait(timeout=20)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                pass
            try:                        # whatever of the group ignored SIGTERM
                os.killpg(self._process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        self._process = None

    # --- worlds ----------------------------------------------------------------

    def setDataDir(self, dataDir):
        self.dataDir = dataDir

    def setupWorld(self, HomeoWorld=None, dataDir=None):
        '''Run (or reset) the Webots twin of the named Homeo world, put the
        robot and its lights in allBodies and open a trajectory file.'''
        if HomeoWorld is None:
            HomeoWorld = 'kheperaBraitenberg2_HOMEO_World'
        if HomeoWorld not in WORLDS:
            raise ValueError('no Webots world for %r (Webots worlds: %s)' % (HomeoWorld, tuple(WORLDS)))
        if dataDir is not None:
            self.dataDir = dataDir
        fileName, sources = WORLDS[HomeoWorld]
        worldFile = os.path.join(WEBOTS_PROJECT, 'worlds', fileName)
        if self._supervisor is None:
            self._launch(worldFile)
        elif worldFile != self._worldFile:
            raise RuntimeError('this process runs %s; one process runs one Webots world'
                               % self._worldFile)
        else:
            self._supervisor.simulationReset()
        self.homeoWorldToRun = HomeoWorld
        sup = self._supervisor
        self._timeStepMs = int(sup.getBasicTimeStep())
        if abs(self._timeStepMs / 1000 - self.timeStep) > 1e-9:
            raise ValueError('the Webots world steps %d ms, Homeo %g s' % (self._timeStepMs, self.timeStep))
        robot = WebotsRobot(sup, self._timeStepMs)
        self.allBodies = {self.robotName: robot}
        lights = []
        for name, (quality, intensity) in sources.items():
            node = sup.getFromDef(name)
            if node is None:
                raise ValueError('the world %s has no DEF %s' % (fileName, name))
            light = WebotsLight(name, quality, node, intensity, pointLight=(quality == 'light'))
            self.allBodies[name] = light
            lights.append(light)
            robot.detectableSources.setdefault(quality, []).append(light)
        robot.detectableLights = robot.detectableSources.get('light', [])
        if 'TARGET' not in self.allBodies:
            self.allBodies['TARGET'] = robot.detectableLights[0]
        for quality, prefix in (('temperature', 'Temp'), ('oxygen', 'Oxy'), ('organic', 'Org')):
            if quality in robot.detectableSources:
                for side in ('left', 'right'):
                    robot.addVirtualEye(side + prefix + 'Eye', side + 'Eye')
        sup.step(self._timeStepMs)           # the sensors' first readings
        self.currentStep = 0
        start = robot.body.position
        self.trajectoryWriter = RobotTrajectoryWriter('Unspecified', (start[0], 0, start[1]), lights,
                                                      dataDir=self.dataDir,
                                                      experimentName=self.experimentName)
        return HomeoWorld

    def resetWorld(self):
        self.setupWorld(self.homeoWorldToRun)

    # --- stepping -----------------------------------------------------------------

    def advanceSim(self):
        "One Webots step, and its trajectory row"
        robot = self.allBodies[self.robotName]
        if self.currentStep == 0:
            self.trajectoryWriter.stepsPerTick = self.stepsPerTick
            self.trajectoryWriter.eyes = robot.eyeSettings()
            self.trajectoryWriter.robotModel = 'epuck2 (Webots)'
            self.trajectoryWriter.writeHeaderNow(robot.body)
        if self._supervisor.step(self._timeStepMs) == -1:
            raise RuntimeError('Webots has stopped')
        self.currentStep += 1
        self.trajectoryWriter.runOnce(position=robot.body)

    def tickAdvance(self):
        "One homeostat tick: stepsPerTick Webots steps, once every unit has updated"
        for i in range(self.stepsPerTick):
            self.advanceSim()

    # --- records ---------------------------------------------------------------------

    def saveTrajectory(self):
        self.trajectoryWriter.runOnce(transitionMessage="CLOSEFILE")

    def newTrajectoryFile(self):
        self.trajectoryWriter.runOnce(transitionMessage="NEWFILE",
                                      modelName=self.allBodies[self.robotName].getModelName(),
                                      position=self.allBodies[self.robotName].body)

    def setRobotModelName(self, robotName, newID):
        self.allBodies[self.robotName].setModelName(newID)

    def finalDisFromTarget(self):
        robot = self.allBodies[self.robotName].body.position
        target = self.allBodies['TARGET'].position
        return sqrt((robot[0] - target[0]) ** 2 + (robot[1] - target[1]) ** 2)

    @classmethod
    def shared(cls, **kwargs):
        "The process's simulation, made on first use (kwargs then apply)"
        if cls._shared is None:
            cls._shared = cls(**kwargs)
        return cls._shared
