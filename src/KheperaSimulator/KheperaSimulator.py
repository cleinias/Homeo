'''
KheperaSimulator is a very simple robotic simulator back-end
built with the pyBox2D physics engine and the pyglet framework. 
It is meant to be used for fast 
simulations of Homeo controllers in GA experimental settings.
The basic robot is a kinematic differential drive Khepera-like vehicle (see
KheperaRobot.update),
equipped with directional "light" sensors that estimate the light irradiance
at the sensor's surface on the basis on incidence angle, light intensity, 
and an attenuation matrix.
The only other objects in the world are lights: static objects with a color and
an intensity. 

The simulator is meant to be used in headless mode (i.e. no graphics) 
for fast performance and to be portable to parallel environments 
(especially including remote clusters), but it includes elementary visualization
facilities for debugging purposes.

Created on Mar 13, 2015
@author: stefano
'''
from Box2D import *
import os
import pyglet

# pyglet creates a hidden "shadow window" the first time pyglet.window is
# imported, which needs an X display.  On a machine with none -- an HPC compute
# node, a headless server, a CI runner -- that import raises
#     pyglet.display.xlib.NoSuchDisplayException: Cannot connect to "None"
# and takes the whole process down before any simulation starts, even though
# nothing here is going to draw anything.  The option has to be set before
# pyglet.window is imported, so it belongs here rather than in a caller: by the
# time an experiment script runs, this module has already been imported.
if not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):
    pyglet.options['shadow_window'] = False

from pyglet import clock, font, image, window
from pyglet.gl import (glEnable, glBlendFunc, glHint, glClearColor, glClear,
                       GL_BLEND, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
                       GL_LINE_SMOOTH, GL_LINE_SMOOTH_HINT, GL_NICEST,
                       GL_COLOR_BUFFER_BIT,
                       GL_LINES, GL_LINE_STRIP, GL_LINE_LOOP, GL_TRIANGLE_FAN)
from pyglet.window import mouse, key
from pyglet.math import Mat4, Vec3
import numpy as np

from math import sin, cos, asin, acos, atan, pi, radians, degrees, sqrt, atan2, log
from Helpers.General_Helper_Functions import normalize, dated_data_dir
from Helpers.RobotTrajectoryWriter import RobotTrajectoryWriter
from time import sleep, time, strftime, localtime
from datetime import datetime

"pyglet 2.x shader program and utility functions"

_shape_program = None

def _get_shape_program():
    """Return the shapes ShaderProgram, creating it on first call.
    Requires an active OpenGL context (pyglet display available)."""
    global _shape_program
    if _shape_program is None:
        _shape_program = pyglet.shapes.get_default_shader()
    return _shape_program

def _has_gl_context():
    """Return True if a pyglet GL context is available (i.e. not fully headless)."""
    try:
        return pyglet.gl.current_context is not None
    except Exception:
        return False

def _make_vlist(count, draw_mode, vertices):
    """Create a pyglet 2.x vertex list from the shape shader program.
    Initializes colors/translation/rotation/zposition to defaults.
    Stores draw_mode on the vertex list as vlist._draw_mode for later use."""
    program = _get_shape_program()
    vlist = program.vertex_list(
        count, draw_mode,
        position=('f', vertices),
        colors=('f', [1.0, 1.0, 1.0, 1.0] * count),
        translation=('f', [0.0, 0.0] * count),
        rotation=('f', [0.0] * count),
        zposition=('f', [0.0] * count),
    )
    vlist._draw_mode = draw_mode
    return vlist

def makePygletCircle(center=(0,0), r=10, numPoints=100, orientation=0,
                     span=(2*pi), draw_mode=GL_TRIANGLE_FAN):
    """Create a vertex list representing a circle with a radius
       indicating the orientation. The circle is rotated according to the
       orientation parameter."""
    vertices = []
    vertices += [center[0], center[1]]
    orientRad = radians(orientation)
    for i in range(numPoints + 1):
        angle = orientRad + (float(i)/numPoints * span)
        x = (r * cos(angle)) + center[0]
        y = (r * sin(angle)) + center[1]
        vertices += [x, y]
    count = numPoints + 2

    if draw_mode == GL_LINE_STRIP:
        vertices += [vertices[2], vertices[3]]
        count += 1

    return _make_vlist(count, draw_mode, vertices)

def makePygletArc(center=(0,0), r=10, numPoints=100, orientation=0,
                  span=(2*pi), draw_mode=GL_LINE_STRIP):
    """Create a vertex list representing an arc with a radius
       indicating the orientation. The arc is rotated according to the
       orientation parameter."""
    vertices = []
    vertices += [center[0], center[1]]
    orientRad = radians(orientation)
    for i in range(numPoints + 1):
        angle = orientRad + (float(i)/numPoints * span) - span/2
        x = (r * cos(angle)) + center[0]
        y = (r * sin(angle)) + center[1]
        vertices += [x, y]
    vertices += [center[0], center[1]]
    vertices += [center[0], center[1]]
    count = numPoints + 4

    if draw_mode == GL_LINE_STRIP:
        vertices += [vertices[0], vertices[1]]
        count += 1

    return _make_vlist(count, draw_mode, vertices)

def makePygletBox(width, height, orientation=0, draw_mode=GL_TRIANGLE_FAN):
    """Create a vertex list representing a rectangle
       (or box, in Box2D language) with given size and orientation,
       centered at 0,0."""
    vertices = [width/2, height/2, -width/2, height/2,
                -width/2, -height/2, width/2, -height/2]
    count = 4

    if draw_mode == GL_LINE_STRIP:
        vertices += [vertices[0], vertices[1]]
        count = 5

    return _make_vlist(count, draw_mode, vertices)

def makePygletReceptor(r, tick, facing=0, numPoints=24):
    """Create a vertex list for a light receptor: a circle of radius r
       centred at 0,0 and a tick of length tick out of it along facing
       (degrees), the direction the receptor faces."""
    f = radians(facing)
    vertices = []
    for i in range(numPoints + 1):
        angle = f + 2 * pi * i / numPoints
        vertices += [r * cos(angle), r * sin(angle)]
    vertices += [(r + tick) * cos(f), (r + tick) * sin(f)]
    return _make_vlist(numPoints + 2, GL_LINE_STRIP, vertices)

def makePygletEyeField(receptors, centre, fieldOfView, r, numPoints=100):
    """Create a vertex list for the outer boundary of an eye's field, the
       union of its receptors' fields, each fieldOfView degrees wide about its
       facing: the outermost edge line on either side, each from the receptor
       it belongs to, out to the circle of radius r about the eye's centre,
       and the arc of that circle between them.  receptors: ((x, y), facing)
       as in KheperaRobot.addEye; the vertices are relative to centre."""
    half = fieldOfView / 2
    def edge(receptor, angle):
        "The receptor's position, and where its edge at angle meets the circle"
        (x, y), _ = receptor
        x, y = x - centre[0], y - centre[1]
        ux, uy = cos(angle), sin(angle)
        along = x * ux + y * uy
        t = -along + sqrt(along**2 - (x * x + y * y) + r * r)
        return (x, y), (x + t * ux, y + t * uy)
    lowReceptor = min(receptors, key=lambda receptor: receptor[1])
    highReceptor = max(receptors, key=lambda receptor: receptor[1])
    lowStart, lowEnd = edge(lowReceptor, radians(lowReceptor[1] - half))
    highStart, highEnd = edge(highReceptor, radians(highReceptor[1] + half))
    low = atan2(lowEnd[1], lowEnd[0])
    high = atan2(highEnd[1], highEnd[0])
    if high < low:
        high += 2 * pi
    vertices = list(lowStart)
    for i in range(numPoints + 1):
        angle = low + (high - low) * i / numPoints
        vertices += [r * cos(angle), r * sin(angle)]
    vertices += list(highStart)
    return _make_vlist(numPoints + 3, GL_LINE_STRIP, vertices)

def makePygletRing(r, numPoints=48):
    "Create a vertex list for a circle of radius r centred at 0,0, outline only"
    vertices = []
    for i in range(numPoints):
        angle = 2 * pi * i / numPoints
        vertices += [r * cos(angle), r * sin(angle)]
    return _make_vlist(numPoints, GL_LINE_LOOP, vertices)

# The radius of the eyes' field arcs in the visualizer, in metres: rendering
# only (an eye has no maximum distance).  10 before 15 Oct 2026, which drew
# each arc across the whole arena.
FIELD_RENDER_RANGE = 0.15

"""Add drawing pyglet-specific drawing functions
   to the box2D bodies used in Khepera world"""

def makePygletGrid(size, spacing=1, color=(1,1,1,1)):
    """Create a vertex list representing a
       size x size grid with indicated spacing in meters and centered at the
       origin. If spacing is not an exact divisor, the grid size will be slightly altered
       to make it the correct size.  Default color is white."""
    vertices = []
    steps = int(size/spacing)
    for x in range(steps+1):
        vertices += [x*spacing, 0]
        vertices += [x*spacing, -size]
        vertices += [0, -x*spacing]
        vertices += [size, -x*spacing]

    "Translating vertices to their real position with numpy arrays"
    translVertices = (np.reshape(vertices, (int(len(vertices)/2), -1)) +
                      np.array([-size/2, size/2])).flatten()
    vLength = int(len(vertices)/2)
    colors = list(color) * vLength

    program = _get_shape_program()
    vlist = program.vertex_list(
        vLength, GL_LINES,
        position=('f', translVertices.tolist()),
        colors=('f', colors),
        translation=('f', [0.0, 0.0] * vLength),
        rotation=('f', [0.0] * vLength),
        zposition=('f', [0.0] * vLength),
    )
    vlist._draw_mode = GL_LINES
    return vlist

def _drawShapes(userData, position, angle, fields=False):
    """Draw the shapes in a body's or a fixture's userData at position, turned
       by angle (radians, counterclockwise): userData['pygletShape'], a vertex
       list or a list of them, in userData['color'] or, for a list, the
       matching userData['colors']; and, when fields is true,
       userData['pygletField'] in userData['fieldColor'].
       The shape shader turns its rotation attribute clockwise, so it gets
       -angle in degrees.  Before 15 Oct 2026 it got +angle, and every shape
       was drawn turned the wrong way: a robot heading at 30 degrees was drawn
       heading at -30, its eyes' arcs facing likewise (where the shapes were
       placed was right)."""
    shapes = userData['pygletShape']
    if shapes is None:
        drawn = []
    elif isinstance(shapes, list):
        drawn = list(zip(shapes, userData['colors']))
    else:
        drawn = [(shapes, userData['color'])]
    if fields and userData.get('pygletField') is not None:
        drawn.append((userData['pygletField'], userData['fieldColor']))
    for vlist, color in drawn:
        count = vlist.count
        vlist.translation[:] = [position[0], position[1]] * count
        vlist.rotation[:] = [-degrees(angle)] * count
        vlist.colors[:] = list(color) * count
        vlist.draw(vlist._draw_mode)

def b2PygletFixtureDraw(self, body, fields=False):
    """A fixture draws itself at its place on its body (see _drawShapes);
       fields: draw its field of view too, if it has one."""
    if self.userData is None:
        return
    try:
        rotMat = b2Rot(body.angle)
        worldPose = rotMat * self.shape.pos + body.position
        _drawShapes(self.userData, worldPose, body.angle, fields)
    except KeyError as e:
        print("Fixture does not know how to draw itself. Skipping it")
        print(e)


def b2PygletBodyDraw(self):
    "Each b2Body draws itself at its position and angle (see _drawShapes)"
    try:
        _drawShapes(self.userData, self.position, self.angle)
    except KeyError as e:
        print("Body does not know how to draw itself. Skipping it")
        print(e)

def b2BodyDefaultUpdate(self, dt=None):
    "Default update function for Box2D body: do nothing"
    pass
    
        
b2Body.draw = b2PygletBodyDraw
b2Fixture.draw = b2PygletFixtureDraw
b2Body.update = b2BodyDefaultUpdate

"Khepera simulation classes"

class KheperaRobot(object):
    """The body of a small two-wheeled robot: an e-puck2 by default, or the
       K-Junior of every run before 14 Oct 2026 (model='kjunior').
       The body is implemented as a simple circle with two wheels and light sensors.

       model='epuck2' (default since 14 Oct 2026): the e-puck2 of Webots'
       E-puck.proto (R2025a, version "2"), so that the Box2D and the Webots
       vehicles are one robot (see EPUCK2):
       - body 74 mm across (the PROTO's bounding cylinder; GCtronic's 70 mm
         is the shell), wheels of 20 mm radius, 52 mm apart;
       - top wheel speed capped at the K-Junior vehicle's 24.3 mm/s (1.2166
         rad/s), not the e-puck2's 151 mm/s, so that the homeostat's
         timescales keep their relation to the motion (decision of 14 Oct);
       - each eye is a pair of the e-puck's light sensors, ls0+ls1 on the
         right and ls7+ls6 on the left, at their real positions and facing
         their real directions (+-17.2 and +-45.8 degrees); the eye's
         irradiance is the mean of the pair's, and each sensor has a
         LightSensor's field: the cosine law, nothing from behind (180
         degrees).  No hoods.  A pair is one cosine eye facing about +-31.5
         degrees; together the eyes see the front 146 degrees, and neither
         sees an 88-degree sector behind.
       The K-Junior geometry below is model='kjunior', kept to reproduce the
       runs before 14 Oct 2026.
       Main physical parameters affecting KheperaBody's behavior are:
       - self.density (default is 0.7. It controls the bosy's mass, and hence the steering, since it affects the torque
                       that the wheels are capable of transmitting to the body. 
       
       By default, KheperaRobot uses the geometric parameters of  a standard Khepera Junior robot, expressed
       as ratios of the body's diameter:
       - diameter = 0.126 meters (= 126 mm)
       - wheel radius = 0.0156 meters (= 15.6mm) = 0.12380 of diameter
       - wheel thickness = 0.003 meters (= 3mm)  = 0.0238 of diameter
       - wheel separation = 0.096 meters (= 96mm) = 0.7619 of diameter
       - right eye position in degrees from y-axis  =  21.9017 
       - left eye position in degrees from y-axis   = -21.9017
       - center eye position in degrees from y-axis = 0
           Notice that the positions of rightEye and leftEye sensors are relative to the forward facing direction
           and lie on the radius at the indicated angle (drawn from K-Team specs) from the y axis.
           See addSensor function  for details on their implementation.
       - eyeRadiusRatio = 0.5: how far out along that radius the eyes sit, as a
           fraction of the body's radius.  Each eye faces outward along its
           radius and sees 45 degrees either side of it, so its field ends 23.1
           degrees inside the heading.  On the rim (1.0, every run before 13 Oct
           2026) the two inner edges crossed on the midline 0.1135 ahead of the
           centre, 0.05 beyond the rim: a light in that wedge was seen by
           neither eye.  The wedge's tip lies 1.80 r ahead of the centre for
           eyes at radius r, so half way in (r = 0.0315) puts it inside the
           body, and everything outside the body within 45 degrees of the
           heading is in view.  The angles and the fields are those of the rim
           eyes; the eyes are closer together (0.0235 apart, not 0.047).
           
        Finally, the 'name' of the KheperaRobot is internal ref used by the simulation software to refer to the robot.
        The 'ID', instead,  is the particular version of a robot, used by the Genetic Algorithm code to record fitnesses

        Motion: a differential drive.  With wheel speeds vR, vL
        (setRightSpeed/setLeftSpeed take rad/s; times the wheel radius, m/s)
        and wheel separation L, the body moves forward at v = (vR + vL)/2 and
        turns at omega = (vR - vL)/L (counterclockwise when the right wheel is
        faster), integrated exactly over each simulation step.  The wheels are
        bodies that follow the chassis, for rendering only.

        Speed units: maxWheelSpeed is in rad/s, the unit of setRightSpeed and
        setLeftSpeed, and getMaxSpeed returns it.  Its default, 1.55988 rad/s
        (0.0243 m/s), is the top speed every run before 13 Oct 2026 actually had:
        the motors' range was then reported as 100 rad/s * wheel radius = 1.55988
        (m/s), which setRightSpeed read as rad/s (review finding RS-03)."""

    MODELS = ('epuck2', 'kjunior')

    # The e-puck2 of Webots' E-puck.proto (R2025a), in metres, in the robot's
    # frame: x forward, y to the left (Webots' convention, and Box2D's for a
    # body at angle 0).  Light sensors: position and facing, in degrees, > 0
    # to the left.
    EPUCK2 = dict(diameter=0.074, wheelRadius=0.020, wheelThickness=0.005, wheelSeparation=0.052,
                  receptors={'ls0': ((0.030, -0.010), -17.235), 'ls1': ((0.022, -0.025), -45.882),
                             'ls6': ((0.022, 0.025), 45.791), 'ls7': ((0.030, 0.010), 17.143)},
                  eyes={'rightEye': ('ls0', 'ls1'), 'leftEye': ('ls7', 'ls6')},
                  fieldOfView=180)
    # The K-Junior vehicle's top rim speed, 0.0243322561 m/s, over the
    # e-puck2's wheel radius: the cap of 14 Oct 2026
    EPUCK2_CAPPED_WHEEL_SPEED = 0.0243322561 / 0.020         # rad/s

    def __init__(self, world, diameter = 126, wheelRadiusRatio = 0.12380, wheelThicknessRatio = 0.02380, wheelSepRatio = 0.76190, maxWheelSpeed = None,
                 rightEyeAngle = 21.9017, leftEyeAngle = -21.9017, centerEyeAngle = 0, density = 0.8, unit = 'mm',
                 color = (1.,0.,0.,0.5), name = "Khepera", ID = "Unspecified", initialPose = (0,0),
                 eyeRadiusRatio = None, model = 'epuck2'):
        '''model: 'epuck2' (default) or 'kjunior'.  diameter, the ratios, unit
        and eyeRadiusRatio (default 0.5) describe the K-Junior and apply only to
        it; maxWheelSpeed (rad/s) defaults to the model's.'''

        "create body"
        if unit == 'mm':
            factor = 0.001
        elif unit == 'cm':
            factor = 0.01
        elif unit == 'dm':
            factor = 0.1
        else:
            factor = 1
        if model not in self.MODELS:
            raise ValueError('model must be one of %s, not %r' % (self.MODELS, model))
        self.model = model
        self.density = density
        if model == 'epuck2':
            if eyeRadiusRatio is not None:
                raise ValueError("eyeRadiusRatio applies only to the K-Junior (model='kjunior')")
            self.eyeRadiusRatio = None
            self.diameter = self.EPUCK2['diameter']
            self.wheelRadius = self.EPUCK2['wheelRadius']
            self.wheelSeparation = self.EPUCK2['wheelSeparation']
            wheelThickness = self.EPUCK2['wheelThickness']
            if maxWheelSpeed is None:
                maxWheelSpeed = self.EPUCK2_CAPPED_WHEEL_SPEED
        else:
            if eyeRadiusRatio is None:
                eyeRadiusRatio = 0.5
            if not 0 < eyeRadiusRatio <= 1:
                raise ValueError('eyeRadiusRatio must be in (0, 1], not %r' % eyeRadiusRatio)
            self.eyeRadiusRatio = eyeRadiusRatio
            self.diameter = diameter * factor
            self.wheelRadius = self.diameter* wheelRadiusRatio
            self.wheelSeparation = self.diameter * wheelSepRatio
            wheelThickness = self.diameter * wheelThicknessRatio
            if maxWheelSpeed is None:
                maxWheelSpeed = 1.55988
        self.maxWheelSpeed = maxWheelSpeed                               # rad/s
        self.maxSpeed = maxWheelSpeed * self.wheelRadius                 # m/s

        bodyDef = b2BodyDef()
        bodyDef.type = b2_dynamicBody
        self.body = world.CreateBody(bodyDef)
        self.body.position = initialPose
        circleShape = b2CircleShape(radius=self.diameter/2.0)
        bodyFixtureDef = b2FixtureDef()
        bodyFixtureDef.density = self.density
        bodyFixtureDef.shape  = circleShape
        self.body.CreateFixture(bodyFixtureDef)
        self.body.userData = {'name': name, 'ID' : ID, 'color':color}

        "create ivars for wheels and sensors"
        self.wheels = {}  # Dictionary indexed by 'right' and 'left' 
        self.sensors = {} # Dictionary indexed by 'right' , 'center' , and 'left'
        self.rightSpeed = 0
        self.leftSpeed = 0
        self.speedIncrease = 1
        
        self.wheels = {side: KheperaWheel(world, thickness=wheelThickness,
                                          diameter=self.wheelRadius * 2, name=side)
                       for side in ('left', 'right')}
        self._placeWheels(self.body.position, self.body.angle)

        self.eyeReceptors = {}       # eye name -> [((x, y), facing in degrees), ...]
        if model == 'epuck2':
            self._addEpuckEyes()
        else:
            self._addSensors()

        "Add a pyglet shape to robot's body for rendering"
        self.setRenderingParameters(color = color)

    def _placeWheels(self, position, angle):
        "Put the wheels at their places on a chassis at (position, angle)"
        for side, offset in (('left', self.wheelSeparation / 2), ('right', -self.wheelSeparation / 2)):
            wheel = self.wheels[side].body
            wheel.transform = (b2Vec2(position[0] - offset * sin(angle),
                                      position[1] + offset * cos(angle)), angle)
            wheel.linearVelocity = (0, 0)
            wheel.angularVelocity = 0

    def _addSensors(self):
        "Sensors"
        """Positions of rightEye and leftEye sensors (in meters) relative to the center of Khepera's circular body,
           corresponding to a position on the outer surface of the body, at an angle of approximately +/- 21 degrees
           from the forward facing direction. 
           Both sensors are modeled with a 1 mm round shape placed on the body's surface, and distance measurements
           compute the minimum distance between the center of the 1mm sensor and the center of the target"""
        
        """ For consistency with other backends (V-REP, WEBOTS), the coordinates of the sensor 
            positions are expressed with respect to the vertical orientation (i.e. with the 
            robot aligned with the y axis). However, since Box2D's default orientation 
           is to the right (along the x axis), we rotate the sensor's position CW by 90 degrees when
           creating the sensors"""
                                    
        khepheraRightEyeDefaultPose = (0.0235,  0.0585)   # =  21.8858 degrees from the forward direction (to the *right* of y axis)
        khepheraLeftEyeDefaultPose  = (-0.0235, 0.0585)   # = -21.8858 degrees from the forward direction (to the *left* of y axis)
        # Moved in along their radii, same angles: see eyeRadiusRatio in the class docstring
        khepheraRightEyeDefaultPose = tuple(c * self.eyeRadiusRatio for c in khepheraRightEyeDefaultPose)
        khepheraLeftEyeDefaultPose  = tuple(c * self.eyeRadiusRatio for c in khepheraLeftEyeDefaultPose)
        self.eyePoses = {'leftEye': khepheraLeftEyeDefaultPose, 'rightEye': khepheraRightEyeDefaultPose}
        kheperaCenterEyeDefaultPose = (0,0.063)           # Straight center
        kheperaEyeDefaultMaxValue   = 100                 # Default saturation irradiance of eye sensors, same as in V_REP
        kheperaEyeDefaultMaxRange   = FIELD_RENDER_RANGE  # Radius of the eyes' field-of-view arc in the visualizer (rendering only)
        kheperaEyeDefaultAngleRange =  90                 # Default angle range for eye sensors, in degrees, same as in V_REP
        kheperaEyeDefaultDiameterRatio = 0.04             # Default size of the sensor radius as ratio of robot's size. For rendering only 
        kheperaEyeDefaultDiameterRatio = 0.1              # Default size of the sensor radius as ratio of robot's size. For rendering only 
        
        self.addSensor(khepheraLeftEyeDefaultPose, 'leftEye', diameter = self.diameter*kheperaEyeDefaultDiameterRatio, 
                       orientation = 0, maxRange = kheperaEyeDefaultMaxRange, angleRange = kheperaEyeDefaultAngleRange,
                       maxValue = kheperaEyeDefaultMaxValue)        
 
        self.addSensor(khepheraRightEyeDefaultPose, 'rightEye', diameter = self.diameter*kheperaEyeDefaultDiameterRatio, 
                       orientation = 0, maxRange = kheperaEyeDefaultMaxRange, angleRange = kheperaEyeDefaultAngleRange,
                       maxValue = kheperaEyeDefaultMaxValue)        

#         self.addSensor(kheperaCenterEyeDefaultPose, 'CenterEye', diameter = self.diameter*kheperaEyeDefaultDiameterRatio, 
#                        orientation = 0, maxRange = kheperaEyeDefaultMaxRange, angleRange = kheperaEyeDefaultAngleRange,
#                        maxValue = kheperaEyeDefaultMaxValue)        
        
        """Sensor's detectable objects.
           Each sensors will return the sum of irradiances gained from a list of 'lights'.
           The list of 'sensable' lights existing in the world is stored in the iVar
           'detectableLights' which is empty at robot's initialization and typically
           set by one to the world setting methods in the KheperaSimulation class'"""
        
        self.detectableLights = []
        self.detectableSources = {}   # quality -> [body, ...]

    def _addEpuckEyes(self):
        "The e-puck2's two eyes: ls0+ls1 on the right, ls7+ls6 on the left (see EPUCK2)"
        receptors = self.EPUCK2['receptors']
        for eye, names in self.EPUCK2['eyes'].items():
            self.addEye(eye, [receptors[n] for n in names], self.EPUCK2['fieldOfView'])
        self.detectableLights = []
        self.detectableSources = {}   # quality -> [body, ...]

    def addEye(self, eyeName, receptors, fieldOfView, threshold=0, saturation=100,
               response='linear', renderRange=FIELD_RENDER_RANGE):
        """Add an eye: one or more light receptors, each a ((x, y), facing) --
        a position in the robot's frame (x forward, y left) and a facing in
        degrees (> 0 left) -- each with the field fieldOfView (degrees, centred
        on its facing).  The eye's irradiance is the mean of its receptors'
        (irradAtSensor); its sensitivity (threshold, saturation, response) is
        the eye's (see eyeResponse).  renderRange: the radius of the receptors'
        field arcs in the visualizer, rendering only.
        Drawn: each receptor as a small circle with a tick along its facing,
        and, when the visualizer shows the fields, the outer boundary of the
        eye's field, its receptors' fields combined (makePygletEyeField); a
        left eye in blue, a right eye in orange."""
        receptors = [((float(p[0]), float(p[1])), float(f)) for p, f in receptors]
        cx = sum(p[0] for p, _ in receptors) / len(receptors)
        cy = sum(p[1] for p, _ in receptors) / len(receptors)
        eyeDef = b2FixtureDef()
        eyeDef.shape = b2CircleShape(radius=self.diameter * 0.02, pos=(cx, cy))
        eyeFixture = self.body.CreateFixture(eyeDef)
        eyeFixture.userData = {eyeName + 'AngleRange': fieldOfView,
                               eyeName + 'Receptors': receptors,
                               'pygletShape': None, 'color': (0., 0.8, 0., 0.5),
                               'position': eyeFixture.shape.pos}
        self.setEyeSensitivity(eyeName, threshold=threshold, saturation=saturation,
                               response=response, fixture=eyeFixture)
        self.sensors[eyeName] = eyeFixture
        self.eyeReceptors[eyeName] = receptors
        self.eyeFieldOfView = fieldOfView
        # One small fixture per receptor, for rendering only
        color = self._eyeColor(eyeName)
        for (x, y), facing in receptors:
            receptorDef = b2FixtureDef()
            receptorDef.shape = b2CircleShape(radius=self.diameter * 0.05, pos=(x, y))
            receptor = self.body.CreateFixture(receptorDef)
            receptor.userData = {'color': color, 'fieldColor': color[:3] + (0.4,),
                                 'position': receptor.shape.pos}
            self._receptorShapes(receptor.userData, facing, fieldOfView, renderRange)
            receptor.userData['pygletField'] = None
        eyeFixture.userData['fieldColor'] = color[:3] + (0.4,)
        eyeFixture.userData['pygletField'] = (
            makePygletEyeField(receptors, (cx, cy), fieldOfView, renderRange)
            if _has_gl_context() else None)

    @staticmethod
    def _eyeColor(eyeName):
        "A left eye's colour (blue) or a right eye's (orange), for rendering"
        return (0., 0.35, 1., 1.) if 'left' in eyeName.lower() else (1., 0.45, 0., 1.)

    def _receptorShapes(self, userData, facing, fieldOfView, renderRange):
        "Set a receptor's shapes in userData: a marker facing `facing` and its field arc"
        if _has_gl_context():
            userData['pygletShape'] = makePygletReceptor(self.diameter * 0.04, self.diameter * 0.25, facing)
            userData['pygletField'] = makePygletArc(r=renderRange, span=radians(fieldOfView),
                                                    orientation=facing, draw_mode=GL_LINE_STRIP)
        else:
            userData['pygletShape'] = None
            userData['pygletField'] = None

    def setModelName(self,ID_String):
        "Resets the ID, or modelName, of the robot"
        self.body.userData['ID'] = ID_String
        
    def getModelName(self):
        return self.body.userData['ID']
        
    def addSensor(self, position, sensorName, diameter = 5, orientation = 0, maxRange = FIELD_RENDER_RANGE, angleRange = 90,
                  maxValue = None, saturation = 100, threshold = 0, response = 'linear'):
        """Adds a Khepera-like object light sensor.
           Sensors are implemented as 5mm radius circle Box2D *fixture*  upon a KheperaRobotBody at
           a specified position. The irradiance is measured from the center of the circle
           Main parameters are:
        - orientation   (in degrees, default is 0, i/e normal to the robot's surface
                         through the center of sensor; > 0 turns the sensor to the left) 
        - angleRange    (default = 90 degrees (same as in V-REP)): the field of view
        - threshold, saturation, response: the eye's sensitivity -- the
                        irradiance below which it responds 0 (default 0), the
                        irradiance at which it responds 1 (default 100, as
                        V-REP's saturation value), and the shape of the
                        response in between, 'linear' or 'log' (Weber-Fechner).
                        See eyeResponse.
        - maxValue      older name for saturation, kept for existing callers
        - maxRange      radius of the field-of-view arc drawn by the visualizer;
                        rendering only.  An eye has no maximum distance: how far
                        it sees follows from the light's intensity and its threshold.
        - diameter      (default = 5mm, for rendering purposes only"""
        if maxValue is not None:
            saturation = maxValue

        rotMatrix = np.asmatrix('0,1;-1,0')     #CW 90 rotation matrix
        positionVector = np.reshape(position, (2,1))
        sensorFixtureDef = b2FixtureDef()
        circleShape = b2CircleShape(radius = diameter/2)
        circleShape.pos = (rotMatrix * positionVector).A1
        sensorFixtureDef.shape = circleShape
        
#         sensorFixtureDef.position = (rotMatrix * positionVector).A1            
        sensorFixture = self.body.CreateFixture(sensorFixtureDef)
        
        "Store sensor's values"
        sensorFixture.userData = {}
        sensorFixture.userData[sensorName + 'AngleRange'] = angleRange
        self.eyeFieldOfView = angleRange
        self.setEyeSensitivity(sensorName, threshold=threshold, saturation=saturation,
                               response=response, fixture=sensorFixture)
        
                
        """Cache angles (in degrees) of eye sensors from robot's normal heading for future computation of irradiance:
           the direction of the sensor's position from the centre, plus orientation.  atan2, so that an
           eye in the rear half faces backward (atan(y/x) turned it forward), and the orientation is
           applied (it was ignored): review finding RS-07.  For the K-Junior's eyes, in front, the
           angle is the same as atan's to the last bit."""
        fx, fy = (rotMatrix * positionVector).A1
        sensorAngle = degrees(atan2(fy, fx)) + orientation
        sensorFixture.userData[sensorName + 'Angle']  = sensorAngle
        # One receptor, at the fixture, facing out along its radius
        sensorFixture.userData[sensorName + 'Receptors'] = [
            ((circleShape.pos[0], circleShape.pos[1]), sensorAngle)]
        self.eyeReceptors[sensorName] = sensorFixture.userData[sensorName + 'Receptors']
        self.sensors[sensorName] = sensorFixture
#         print "At time %s I added fixture %s to robot ID %s as %s" % (datetime.now().strftime('%Y:%m:%d:%H:%M:%S.%f'),id(sensorFixture), id(self), sensorName)
        
        "For openGL rendering: a marker and a field arc, as an eye's receptors (see addEye)"
        color = self._eyeColor(sensorName)
        sensorFixture.userData['color'] = color
        sensorFixture.userData['fieldColor'] = color[:3] + (0.4,)
        self._receptorShapes(sensorFixture.userData, sensorAngle, angleRange, maxRange)
        sensorFixture.userData['position'] = circleShape.pos

    def irradAtSensor(self, sensorName, lightsList):
        """Return a scalar representing the intensity of the light 
           (irradiance) falling upon the sensor sensorName as a function of 
           distance to the light source, its intensity, ambient ratio, attenuation vector,
           and incident angle.
           Return 0 if no lights are within eye's range (as both maxAngle and maxDistance) """
        
        """ Reference: lua function Homeo uses in V_REP (in 3D), which is the same function used in Webots
        
            function irrad(intens, ambRatio, vecToLight, distance, attenVect) 
            -- return the irradiance of a light source at the sensor surface
                local cosAngle = (dot({0,0,1},vecToLight)/norm3D(vecToLight))
                local directIntens = (intens * (1-ambRatio)) * cosAngle
                local attenuation = 1/(attenVect[1]+(attenVect[2]*distance)+(attenVect[3]*distance^2))
                return (directIntens + (intens*ambRatio)) * attenuation
            end
        """
        
#         print "                In irradAtSensor"
# #         try:
#         print "                    trying to acquire the fixture"
#         print "                    I am a: %s" % type(self)
#         print "                    with %.0f sensors, and I am looking for %s" % (len(self.sensors), sensorName)
#         print "                    At time %s  robot ID is %s and ID  of right wheel is %s " % (datetime.now().strftime('%Y:%m:%d:%H:%M:%S.%f'),id(self), id(self.wheels['right']))
#         print "                    trying to access right wheel's position: ", self.wheels['right'].body.position
#         print "                    At time %s robot ID is %s and ID of right eye is %s " %(datetime.now().strftime('%Y:%m:%d:%H:%M:%S.%f'), id(self), id(self.sensors['rightEye']))
#         print "                    right: ", self.sensors.values()[0] 
#         print "                    my sensors are: ", self.sensors
#         print "                    sensor is at: ", self.sensors['rightEye']
        sensorFixture = self.sensors[sensorName]
        receptors = sensorFixture.userData[sensorName + 'Receptors']
        eyeAngleRange = sensorFixture.userData[sensorName + 'AngleRange']
        rotMatrix = b2Rot(self.body.angle)
        sensorIrrad = 0
        for (rx, ry), facing in receptors:
            sensorIrrad += self._receptorIrrad(rotMatrix, b2Vec2(rx, ry), facing,
                                               eyeAngleRange, lightsList)
        # The eye's irradiance is its receptors' mean (an e-puck eye has two;
        # a K-Junior eye one, so its value is unchanged)
        return sensorIrrad / len(receptors)

    def _receptorIrrad(self, rotMatrix, relPosition, facing, eyeAngleRange, lightsList):
        "The irradiance on one receptor at relPosition (robot frame) facing `facing` degrees"
        sensorIrrad = 0
        sensorPosition = self.body.position + rotMatrix * relPosition
        "Compute vector of eye's normal from the robot's angle and the receptor's facing."
        eyeAngle = (self.body.angle + radians(facing))
        eyeNormalVec = np.array([cos(eyeAngle),sin(eyeAngle)])
        for targetLight in lightsList:
            targetPose = b2Vec2(targetLight.userData['lightPos'][0],targetLight.userData['lightPos'][2])
            vecToTarget = targetPose-sensorPosition
            targetDistance = vecToTarget.length
            lightIntensity = targetLight.userData['intensity']
            lightAttenVec = targetLight.userData['attenVec']
            lightAmbRatio = targetLight.userData['ambRatio']
            cosAngleToTarget = np.dot(normalize(vecToTarget),eyeNormalVec)
            "Is target in range?  (The dot product of unit vectors can round"
            "past +/-1, which acos refuses: review finding RS-06.)"
            if degrees(acos(min(1.0, max(-1.0, cosAngleToTarget)))) > eyeAngleRange / 2:
                continue
            directIntens = (lightIntensity * (1-lightAmbRatio)) * cosAngleToTarget
            attenuationFactor = 1/( lightAttenVec[0]+
                                   (lightAttenVec[1]*targetDistance)+
                                   (lightAttenVec[2]*targetDistance**2))
            sensorIrrad +=  (directIntens + (lightIntensity*lightAmbRatio)) * attenuationFactor
        return sensorIrrad

    def setRenderingParameters(self, color = (1.,0.,0.,0.5)):
        """Default rendering: a disc of `color`, faint, inside an outline of
           the same colour, darker, with a radius drawn along the heading"""
        if _has_gl_context():
            self.body.userData['pygletShape'] = [
                makePygletCircle(r=self.diameter / 2, draw_mode=GL_TRIANGLE_FAN),
                makePygletCircle(r=self.diameter / 2, draw_mode=GL_LINE_STRIP)]
        else:
            self.body.userData['pygletShape'] = None
        self.body.userData['color'] = color
        self.body.userData['colors'] = [tuple(color[:3]) + (0.35,),
                                        tuple(0.7 * c for c in color[:3]) + (1.,)]

        
    def update(self, dt=None):
        '''Update physical state before a simulation step of dt seconds.

        Set the chassis' velocities so that the step moves it exactly along
        the differential-drive arc (the wheel speeds are held over the step):
        heading theta -> theta + omega dt, and the position along the arc of
        radius v / omega.'''
        vR = max(-self.maxSpeed, min(self.maxSpeed, self.rightSpeed))
        vL = max(-self.maxSpeed, min(self.maxSpeed, self.leftSpeed))
        v = (vR + vL) / 2.0
        omega = (vR - vL) / self.wheelSeparation
        theta = self.body.angle
        if dt:
            turn = omega * dt
            if abs(turn) > 1e-9:
                dx = v / omega * (sin(theta + turn) - sin(theta))
                dy = -v / omega * (cos(theta + turn) - cos(theta))
            else:
                dx = v * dt * cos(theta + turn / 2.0)
                dy = v * dt * sin(theta + turn / 2.0)
            self.body.linearVelocity = (dx / dt, dy / dt)
            self._placeWheels(self.body.position + b2Vec2(dx, dy), theta + turn)
        else:
            self.body.linearVelocity = (v * cos(theta), v * sin(theta))
        self.body.angularVelocity = omega

    def setSpeed(self, newRightSpeed, newLeftSpeed):
        "Set both wheel speeds, in rad/s"
        self.setRightSpeed(newRightSpeed)
        self.setLeftSpeed(newLeftSpeed)
    
    def setRightSpeed(self, newSpeed):
        """Wheel speed is expressed in rad/sec.
           Convert to linear wheel speeds from wheel radius"""
        self.rightSpeed = newSpeed * self.wheelRadius

    def setLeftSpeed(self, newSpeed):
        """Wheel speed is expressed in rad/sec.
           Convert to linear wheel speeds from wheel radius"""
        self.leftSpeed = newSpeed * self.wheelRadius
    
    def getSpeed(self):
        return {'right':self.rightSpeed,'left':self.leftSpeed}
    
    def getMaxSpeed(self):
        "Maximum wheel speeds, in rad/s (the unit of setRightSpeed and setLeftSpeed)"
        return {'right': self.maxWheelSpeed, 'left': self.maxWheelSpeed}
    
    def getMaxSensorValue(self,sensorName):
        "Return the max value of the named sensor's response, which is normalised to [0, 1]"

        return 1.0

    EYE_RESPONSES = ('linear', 'log')

    def setEyeSensitivity(self, sensorName, threshold=None, saturation=None, response=None,
                          fixture=None):
        '''Set the named eye's threshold, saturation (both irradiances) and
        response shape; None leaves a value as it is.  See eyeResponse.  The
        new settings are checked before any is stored, so a refused call
        leaves the eye as it was (review finding RS-12).'''
        userData = (fixture if fixture is not None else self.sensors[sensorName]).userData
        I0 = float(threshold) if threshold is not None else userData[sensorName + 'Threshold']
        Isat = float(saturation) if saturation is not None else userData[sensorName + 'Saturation']
        shape = response if response is not None else userData[sensorName + 'Response']
        if shape not in self.EYE_RESPONSES:
            raise ValueError("eye response must be one of %s, got %r" % (self.EYE_RESPONSES, shape))
        if not 0 <= I0 < Isat:
            raise ValueError("eye %s needs 0 <= threshold < saturation, got %g, %g" % (sensorName, I0, Isat))
        if shape == 'log' and I0 <= 0:
            raise ValueError("a logarithmic eye needs a threshold > 0, got %g" % I0)
        userData[sensorName + 'Threshold'] = I0
        userData[sensorName + 'Saturation'] = Isat
        userData[sensorName + 'Response'] = shape

    def eyeSettings(self):
        """Every eye's (threshold, saturation, response), by sensor name: what
        the trajectory header records, so a chart can tell how far an eye sees."""
        return {name: (fixture.userData[name + 'Threshold'], fixture.userData[name + 'Saturation'],
                       fixture.userData[name + 'Response'])
                for name, fixture in self.sensors.items()}

    def eyeResponse(self, sensorName, irradiance):
        """The named eye's response to the irradiance falling on it, in [0, 1]:
        0 up to its threshold I0, 1 from its saturation Isat on, and in between
            linear:  (I - I0) / (Isat - I0)
            log:     log(I / I0) / log(Isat / I0)   (Weber-Fechner: S = k log(I / I0),
                                                     k set so that S = 1 at Isat)
        The response, not the irradiance, is what an eye reports: the physics
        stops at irradAtSensor.

        A source of negative intensity (a "darkness source", --dark) gives a
        negative irradiance, and the response is signed: minus the response to
        the irradiance's magnitude, in [-1, 0].  So a darkness source is a light
        whose stimulus has the opposite sign, as it was before the threshold and
        saturation were introduced (7170286), when negative irradiances reached
        the sensor units unchanged; without the sign the eye read 0 and --dark
        runs were blind (review finding RE-01)."""
        if irradiance < 0:
            return -self.eyeResponse(sensorName, -irradiance)
        userData = self.sensors[sensorName].userData
        I0 = userData[sensorName + 'Threshold']
        Isat = userData[sensorName + 'Saturation']
        if irradiance <= I0:
            return 0.0
        if irradiance >= Isat:
            return 1.0
        if userData[sensorName + 'Response'] == 'log':
            return log(irradiance / I0) / log(Isat / I0)
        return (irradiance - I0) / (Isat - I0)

    def getSensorRead(self,sensorName):
        """Return the response of sensor sensorName (see eyeResponse) to the
           sum of irradiances produced by all the existing lights in the
           robot's world."""
        
        return self.eyeResponse(sensorName, self.irradAtSensor(sensorName, self.detectableLights))

    def getSensorReadByQuality(self, sensorName, quality):
        """Return the response of sensorName to sources of the given quality only."""
        sources = self.detectableSources.get(quality, [])
        if not sources and quality == 'light':
            sources = self.detectableLights   # backward compat fallback
        return self.eyeResponse(sensorName, self.irradAtSensor(sensorName, sources))

    def rotateTo(self, angleRad):
        """Rotate robot and its wheels, about the robot's centre, to angleRad."""
        self._setPose(self.body.position, angleRad)

    def moveTo(self, posVec):
        """Move robot and its wheels to posVec."""
        self._setPose(b2Vec2(posVec[0], posVec[1]), self.body.angle)

    def _setPose(self, position, angle):
        "Put the chassis at (position, angle), the wheels with it"
        self.body.transform = (position, angle)
        self._placeWheels(position, angle)
              
class KheperaWheel(object):
    """A wheel of a Khepera-like robot, seen from above: a box of
       diameter x thickness.  It is a kinematic body that collides with
       nothing and follows the chassis (KheperaRobot._placeWheels): the
       robot's motion comes from its differential drive, the wheels are
       there to be drawn."""

    def __init__(self, world, thickness = 2, diameter = 31.2, name = None):
        bodyDef = b2BodyDef()
        bodyDef.type = b2_kinematicBody
        self.body = world.CreateBody(bodyDef)
        polygonShape = b2PolygonShape()
        polygonShape.SetAsBox(diameter/2, thickness/2)

        fixtureDef = b2FixtureDef()
        fixtureDef.shape = polygonShape
        fixtureDef.maskBits = 0
        self.body.CreateFixture(fixtureDef)

        "set up pyglet shape and color for rendering"
        self.body.userData = {}
        self.setRenderingParameters(diameter,thickness)

        if name is not None:
            self.name = name

    def setRenderingParameters(self, thickness, diameter, color = (0.,0.,0.,1)):
        "default openGL rendering: box in black color"
        if _has_gl_context():
            self.body.userData['pygletShape'] = makePygletBox(thickness, diameter, draw_mode=GL_TRIANGLE_FAN)
        else:
            self.body.userData['pygletShape'] = None
        self.body.userData['color'] = color


# class KheperaSensor(object):
#     """Implements a Khepera-like object light sensor. It knows how to return a 
#        scalar value representing the intensity (irradiance) of light falling
#        upon its point-like surface.
#        Sensors are implemented as 5mm radius circle Box2D bodies welded upon a KheperaRobotBody at
#        a specified position. The irradiance is measured from the center of the circle
#        Main parameters are:
#        - orientation  (in degrees, default is 0, i/e normal to the robot's surface
#                       through the center of sensor) 
#        - maxRange     (default = 10 meters, (same as in V-REP))
#        - angleRange   (default = 90 degrees (same as in V-REP))
#        - maxValue     (default = 100, saturation value (same as in V-REP))
#        - diameter      (default = 5mm, for rendering purposes only"""
# 
#     def __init__(self, world, name, diameter = 5, orientation = 0, maxRange = 10, angleRange = 90, maxValue = 100):
# 
#         "setting sensors's parameters"
#         self.orientation = orientation
#         self.maxRange = maxRange
#         self.angleRange = angleRange
#         self.maxValue = maxValue
#         
#         "creating body and fixture"
#         bodyDef = b2BodyDef()
#         bodyDef.type = b2_dynamicBody
#         self.body = world.CreateBody(bodyDef)
#         circleShape = b2CircleShape(radius=0.001)
#         fixtureDef = b2FixtureDef()
#         fixtureDef.shape = circleShape
#         fixtureDef.density = 0.01
# 
#         self.body.userData = {}
#         self.setRenderingParameters(diameter)
#         
#         if name is not None:
#             self.name = name
#         
#             
#     def setRenderingParameters(self, diameter, color = (0.,0.,1.,1)):
#         "default openGl rendering: blue circle"
#         
#         self.body.userData['pygletShape'] = makePygletCircle(r = diameter/2) 
#         self.body.userData['color'] = color
#         self.body.userData['filled'] = GL_POLYGON

   
class KheperaSimulation(object):
    """
    KheperaSimulation is the overall class managing the simulation.
    It is responsible for saving/loading of simulated worlds,
    as well for managing the simulation's operation: advancing, 
    stopping, resetting, etc.
    """
    
    def __init__(self, timeStep = 0.032, vel_iters = 6, pos_iters = 2, running = False,
                 stepsPerTick = 2,
                 robotEyeRadiusRatio = None, robotModel = 'epuck2'):
        '''
        Default time step is 0.032 s, values for velocity 
        and position iterations are those recommended by pyBox2D docs
        robotModel: the robots' model, 'epuck2' (default since 14 Oct 2026) or
            'kjunior' (every run before); see KheperaRobot.
        robotEyeRadiusRatio: for the K-Junior only, where its eyes sit along
            their radii, 0.5 (half way in, no blind wedge between them; the
            default) or 1.0 (on the rim, as in every run before 13 Oct 2026).
        Stepping: the motors only set their wheel speeds, and the world
            advances by stepsPerTick steps once per homeostat tick, after every
            unit has updated (tickAdvance, called by Homeostat.runFor).
            stepsPerTick = 2: a tick is 2 x timeStep, with two trajectory rows.
        
        The experimental world to simulate is passed in HomeoWorld as the name of the initializing
        method.'''
        
        self.running = running
        self.robotEyeRadiusRatio = robotEyeRadiusRatio
        self.robotModel = robotModel
        self.stepsPerTick = stepsPerTick
        self.timeStep = timeStep
        self.vel_iters = vel_iters
        self.pos_iters = pos_iters
        # Where trajectory files go until a caller sets its own directory: each
        # world set up opens one at once, so the default must be a data
        # directory, not the current one.
        self.dataDir = dated_data_dir()
        self.experimentName = None
        self.allBodies = {} #Dictionary containing refs to all relevant bodies in the world
   
        "Pyglet grid is created lazily (requires GL context)"
        self.gridDefaultSize = 40
        self.gridDefaultSpacing = 0.5
        self._grid = None
        self.showFields = False    # the visualizer draws the eyes' field arcs

#         self.setupWorld(self.dataDir)                    #  The called function will set up the class's Trajectory writer as well                

#         self.sensorTesting()

    @property
    def grid(self):
        if self._grid is None and _has_gl_context():
            self._grid = makePygletGrid(self.gridDefaultSize, self.gridDefaultSpacing)
        return self._grid

    @grid.setter
    def grid(self, value):
        self._grid = value

    def setupWorld(self, HomeoWorld = None, dataDir = None):
        """Create a world to run experiments in by calling the method stored in the homeoWorldToRun ivar,
           which will also set up a trajectory writer with a proper (even though provisional) data directory.
           Each method will also setup a list of 'lights' in the robots' ivar 'targets', which the robot's sensors will
           be able to sense.      
        """
        if HomeoWorld is not None:
            self.homeoWorldToRun = HomeoWorld
         
        if dataDir is not None:
            self.dataDir = dataDir
        # Each world-setting method creates a new trajectory writer, which opens
        # a file at once.  Close the current writer's file first: resetWorld
        # does, but a world set up again without a reset (a GA evaluation builds
        # the homeostat, resets, and builds again) would otherwise leave it open.
        previousWriter = getattr(self, 'trajectoryWriter', None)
        if previousWriter is not None:
            previousWriter.runOnce(transitionMessage = "CLOSEFILE")
        
#         if len(self.allBodies)>0:
#             print "Robot is currently at: ", self.allBodies[self.robotName].body.position
        
        # Look the builder up, then call it outside the try: an error inside a
        # builder used to come out as one of these two messages (RS-14)
        if not isinstance(getattr(self, 'homeoWorldToRun', None), str):
            raise Exception("Cannot run simulation without an experiment to run")
        builder = getattr(self, self.homeoWorldToRun, None)
        if builder is None:
            raise Exception("Cannot find ** %s ** among my experiment setup methods" % self.homeoWorldToRun)
        self.world = builder()
        self.currentStep = 0
#         sleep(1.5)
#         print "Now leaving setupWorld. Robot is at: ", self.allBodies[self.robotName].body.position

    def resetWorld(self):
        "Reset world to the setup specified in self.homeoWorldToRun"
        
        self.trajectoryWriter.runOnce(transitionMessage = "CLOSEFILE")
        self.currentStep = 0
        self.destroyWorld()
        self.setupWorld()
#         self.trajectoryWriter.runOnce(transitionMessage="SAVE")

    def destroyWorld(self):
        """Destroy the Box2D world and nulls the variables containing 
           references to box2D objects"""
        list(self.allBodies.values())[0].sensors = None
        del(self.allBodies)
        self.allBodies = {}
        del(self.world)
             
    def setRobotModelName(self,robotName,newID):
        "Resets the ID, or modelName, of robot robotName"
        self.allBodies[robotName].body.userData['ID'] = newID
            
    def advanceSim(self):
        """Advances simulation one step and writes trajectory data to file """
#         "For testing"
#         self.braiten2b()
#         "end testing"
        if self.currentStep == 0:
            # The trajectory header records the world as the experiment set it up
            self.trajectoryWriter.stepsPerTick = self.stepsPerTick
            robot = self.allBodies[self.robotName]
            self.trajectoryWriter.eyes = robot.eyeSettings()
            self.trajectoryWriter.eyeRadiusRatio = robot.eyeRadiusRatio
            self.trajectoryWriter.robotModel = robot.model
            self.trajectoryWriter.writeHeaderNow(robot.body)
        for body in self.allBodies.values():
            body.update(self.timeStep)
        self.world.Step(self.timeStep, self.vel_iters, self.pos_iters)
        self.currentStep += 1
        
        self.trajectoryWriter.runOnce(position=self.allBodies[self.robotName].body)
    
    def tickAdvance(self):
        '''Advance the world by one homeostat tick (stepsPerTick steps), once
        every unit has updated.'''
        for i in range(self.stepsPerTick):
            self.advanceSim()

    def saveTrajectory(self):
        "Asks the TrajectorytWriter to save the robot's trajectory"
        self.trajectoryWriter.runOnce(transitionMessage = "CLOSEFILE")

    def newTrajectoryFile(self):
        "Asks the trajectoryWriter to open a new trajectory file for the robot"
        self.trajectoryWriter.runOnce(transitionMessage = "NEWFILE", 
                                      modelName = self.allBodies[self.robotName].body.userData['ID'], 
                                      position = (self.allBodies[self.robotName].body.position[0],0,self.allBodies[self.robotName].body.position[1]),
                                      lights = self.allBodies[self.robotName].detectableLights)
        
    #===============================================================================
    #                             EXPERIMENTAL WORLDS
    # 
    # Each world for HOMEO's experiments is setup by one of the following methods,
    # which return a properly configured Box2D world.
    # Each world-setting method is also responsible for setting up the 
    # trajectoryWriter instance  with a proper (even if provisional) data directory.
    #===============================================================================

    def kheperaBraitenberg2_HOMEO_World(self):
        """Create an empty world with a Khepera-like objects and one or more lights.
           Set up the trajectory writer with appropriate initial values"""
                
        'Constants'
        kheperaRobotDefaultColor  = (1.0,0.0,0.0,0.5)            # partially transparent red,  in openGl [0,1] float format ('c4f')
        kheperaRobotDefaultName = "Khepera"
        kheperaRobotDefaultID = 'Unspecified'
        kheperaDefaultPosition = (4,4)
        lightColor = (1.0,1.0,0.,1.0)                            # solid yellow in openGl [0,1] float format ('c4f')
        lightDefaultPosition = (7,7)
        lightDefaultRadius = .06
        lightDefaultName = "TARGET"
        lightDefaultIntensity = 100
        
        "Create the Box2D world"
        kheperaWorld = b2World(gravity = (0,0))                   #Setting gravity to 0 lets us simulate horizontal movement in the 2D world

        'Add a robot'
        self.robotName = kheperaRobotDefaultName
        self.allBodies[self.robotName] = KheperaRobot(world=kheperaWorld, 
                                                      unit = 'mm', 
                                                      color = kheperaRobotDefaultColor, 
                                                      name = kheperaRobotDefaultName, 
                                                      ID = kheperaRobotDefaultID,
                                                      initialPose = kheperaDefaultPosition,
                                                      eyeRadiusRatio = self.robotEyeRadiusRatio,
                                                      model = self.robotModel)

        'Add a light'
        
        lightBody = kheperaWorld.CreateBody(self.KheperaWorldLightDef(lightColor, lightDefaultPosition, intensity = lightDefaultIntensity, name = lightDefaultName))
        lightFixtures = self.KheperaWorldLightFixtureDefs(lightDefaultRadius)
        for fixtureDef in lightFixtures:
            lightBody.CreateFixture(fixtureDef)
            
        "Create a smaller (1mm) fixture at the center of the light body, will be used to compute distance to sensors in irradiance function "
        self.allBodies[lightDefaultName] = lightBody
        
        """Cache the light vertex lists and store the drawing mode for filled circles or not"""        

        if _has_gl_context():
            lightBody.userData['pygletShape'] = makePygletCircle(center=(0,0), r=lightDefaultRadius, numPoints=100, orientation=0, draw_mode=GL_TRIANGLE_FAN)
        else:
            lightBody.userData['pygletShape'] = None
        
        "Now set up an appropriate Trajectory writer"
        "First create a list with the lights. Use Webots convention of putting y coordinate in 3rd position  "
        
        lightBody.userData['name'] = lightDefaultName 
        lightBody.userData['lightPos'] =  (lightDefaultPosition[0],0,lightDefaultPosition[1])
        lightBody.userData['lightIntensity'] =  lightDefaultIntensity
        lightBody.userData['lightIsOn'] =  True
        
        lights = [lightBody]        
        self.trajectoryWriter = RobotTrajectoryWriter(kheperaRobotDefaultID, (kheperaDefaultPosition[0],0,kheperaDefaultPosition[1]), lights, dataDir = self.dataDir, experimentName = self.experimentName)
        
        "Finally, inform the robot of the existing detectable lights"
        self.allBodies[kheperaRobotDefaultName].detectableLights = lights                  
        
        return kheperaWorld

    def kheperaBraitenberg3c_HOMEO_World(self):
        """Create a multi-quality environment for Braitenberg Vehicle 3c.

        The world contains 5 point sources of 4 different qualities
        (light, temperature, oxygen, organic matter) and a robot with
        8 sensors (one pair per quality).

        Source layout:
          LIGHT1  at (7,7) yellow  intensity 100
          TEMP1   at (7,7) red     intensity  80  (co-located with light)
          TEMP2   at (1,7) red     intensity  80
          OXY1    at (2,2) cyan    intensity 100
          ORG1    at (6,1) green   intensity 100
        """

        'Constants'
        kheperaRobotDefaultColor  = (1.0, 0.0, 0.0, 0.5)
        kheperaRobotDefaultName = "Khepera"
        kheperaRobotDefaultID = 'Unspecified'
        kheperaDefaultPosition = (4, 4)
        lightDefaultRadius = .06

        "Create the Box2D world"
        kheperaWorld = b2World(gravity=(0, 0))

        'Add a robot'
        self.robotName = kheperaRobotDefaultName
        self.allBodies[self.robotName] = KheperaRobot(
            world=kheperaWorld, unit='mm',
            color=kheperaRobotDefaultColor,
            name=kheperaRobotDefaultName,
            ID=kheperaRobotDefaultID,
            initialPose=kheperaDefaultPosition,
            eyeRadiusRatio=self.robotEyeRadiusRatio,
            model=self.robotModel)
        robot = self.allBodies[self.robotName]

        'Add extra sensor pairs to the robot'
        """Each extra pair has the light eyes' receptors and field (see
        KheperaRobot): the four modalities share one geometry,
        so they differ only in how they are wired, and none has a blind wedge
        ahead.  Before 13 Oct 2026 the pairs sat on the rim at +/-45 (temperature),
        +/-10 (oxygen) and +/-35 degrees (organic), with wedges reaching 0.078 and
        0.257 from the centre and, for temperature, a strip straight ahead never
        seen.  Other layouts (direction-free sensing of heat and chemicals, more
        sensors per modality): research note "Khepera sensor placement for
        Vehicle 3c"."""
        for modality in ('Temp', 'Oxy', 'Org'):
            for side in ('left', 'right'):
                robot.addEye(side + modality + 'Eye', robot.eyeReceptors[side + 'Eye'],
                             robot.eyeFieldOfView, saturation=100)

        'Define source specifications: (name, quality, position, color, intensity)'
        source_specs = [
            ('LIGHT1', 'light',       (7, 7), (1.0, 1.0, 0.0, 1.0), 100),
            ('TEMP1',  'temperature',  (7, 7), (1.0, 0.2, 0.2, 1.0),  80),
            ('TEMP2',  'temperature',  (1, 7), (1.0, 0.2, 0.2, 1.0),  80),
            ('OXY1',   'oxygen',       (2, 2), (0.0, 0.8, 0.8, 1.0), 100),
            ('ORG1',   'organic',      (6, 1), (0.2, 0.8, 0.2, 1.0), 100),
        ]

        allLightBodies = []
        for srcName, quality, position, color, intensity in source_specs:
            body = kheperaWorld.CreateBody(
                self.KheperaWorldLightDef(color, position,
                                          intensity=intensity, name=srcName))
            for fixDef in self.KheperaWorldLightFixtureDefs(lightDefaultRadius):
                body.CreateFixture(fixDef)

            if _has_gl_context():
                body.userData['pygletShape'] = makePygletCircle(
                    center=(0, 0), r=lightDefaultRadius, numPoints=100,
                    orientation=0, draw_mode=GL_TRIANGLE_FAN)
            else:
                body.userData['pygletShape'] = None

            body.userData['name'] = srcName
            body.userData['quality'] = quality
            body.userData['lightPos'] = (position[0], 0, position[1])
            body.userData['lightIntensity'] = intensity
            body.userData['lightIsOn'] = True

            self.allBodies[srcName] = body
            allLightBodies.append(body)

            # Populate detectableSources by quality
            robot.detectableSources.setdefault(quality, []).append(body)

        # Backward compat: detectableLights = light-quality sources
        robot.detectableLights = robot.detectableSources.get('light', [])

        # TARGET alias points to LIGHT1 for fitness computation compatibility
        self.allBodies['TARGET'] = self.allBodies['LIGHT1']

        "Set up trajectory writer with all source bodies"
        self.trajectoryWriter = RobotTrajectoryWriter(
            kheperaRobotDefaultID,
            (kheperaDefaultPosition[0], 0, kheperaDefaultPosition[1]),
            allLightBodies, dataDir=self.dataDir,
            experimentName=self.experimentName)

        return kheperaWorld

   #============================================================================
   # END EXPERIMENTAL WORLD SETUP
   #============================================================================


    #===========================================================================
    # TESTING METHODS
    # 
    # Simple methods to test the simulator in elementary scenarios
    #===========================================================================

    def braiten2a(self):
        """Simulate a Braitenberg type 2a vehicle: parallel-connected motors/sensors, 'the more, the more'.
           Assume the kheperaBraitenberg2_HOMEO_World is running."""
        light = self.allBodies['TARGET']
        leftEyeReading = self.allBodies[self.robotName].irradAtSensor('leftEye', [light])
        rightEyeReading = self.allBodies[self.robotName].irradAtSensor('rightEye', [light])
        print("right eye sees: %3.f  left eye sees: %.3f" % (rightEyeReading, leftEyeReading))
        self.allBodies[self.robotName].setSpeed(rightEyeReading,leftEyeReading)    
    
    def braiten2b(self):
        """Simulate a Braitenberg type 2b vehicle: cross-connected motors/sensors, 'the more, the more'"
           Assume the kheperaBraitenberg2_HOMEO_World is running."""

        light = self.allBodies['TARGET']
        leftEyeReading = self.allBodies[self.robotName].irradAtSensor('leftEye', [light])
        rightEyeReading = self.allBodies[self.robotName].irradAtSensor('rightEye', [light])
        self.allBodies[self.robotName].setSpeed(leftEyeReading, rightEyeReading)    


                                    
    def sensorTesting(self):
        """FOR TESTING"""        
        """for testing irradiance values:"""
        """Assume the kheperaBraitenberg2_HOMEO_World is running."""

        """move robot slightly behind origin, so that center sensor is exactly  at (0,0).
           and target exactly in front"""
#         
        self.allBodies[self.robotName].rotateTo(radians(90))
        self.world.Step(self.timeStep, self.vel_iters, self.pos_iters)
        self.allBodies[self.robotName].moveTo( (0,0 - (self.allBodies[self.robotName].diameter/2)))
        self.allBodies['TARGET'].position = (0,1)
#         self.setSpeed("Khepera",10,-10)

#         "additional testing:"
#         """move robot slightly behind origin, so that center sensor is exactly  at (0,0).
#            and target exactly at 45% wrt to origin.
#            The target would thus be at about 48deg to the left, hence out of range.
#            If the robot rotates slowly to the left, it would go in range 
#            after (appr.) a 3.6 deg rotation and go out of range again
#            after a 90 deg rotation """
        
#         kheperaRobotBody.position = (0,0 - kheperaDefaultRadius)
#         kheperaRobotBody.angle = 0
#         lightBody.position = (1,1)
#         self.setSpeed("Khepera",100,-100)
        
        #=======================================================================
        #  END TESTING METHODS
        #=======================================================================
    
    def KheperaWorldLightDef(self, color, position, intensity=None, ambRatio = 0, attenVec = (0,0,1), name=None):
        "Definition of a static light-like object."
        """We are using Webots's model of lights irradiance for consistency among Homeo's backends.
           See Webots manual for details on the model: 
           http://www.cyberbotics.com/dvd/common/doc/webots/reference/section3.44.html
           ambRatio is the percentage of the light intensity
           that is *not* affected by incident angle to the sensor (i.e the 'ambient light' component),
           attenVec stores the constant, linear, and quadratic attenuation factors (sum is 1)
           the default value assumes all light decays quadratically.
           Position is a tuple (x,y)"""
        
        if intensity is None:
            intensity = 100
        if name is None:
            name = 'TARGET'            
        userData = {'intensity' : intensity, 'ambRatio': ambRatio, 'attenVec': attenVec, 'color': color, 'name': name}             
        lightDef = b2BodyDef(position = position,
                                        userData = userData,
                                        type = b2_staticBody)        
        return lightDef
    
    def KheperaWorldLightFixtureDefs(self, mainFixtureRadius):
        """Return a tuple with 2 Box2D fixtures defs to use for lights.
           One is the visible object, the other one is a 1mm fixture used for 
           computations of irradiance.
           Set maskBits for both to 0 to make either non-collidable"""
         
        fixtureDef1 = b2FixtureDef()
        widerShape = b2CircleShape(radius = mainFixtureRadius)
        fixtureDef1.shape = widerShape
        fixtureDef1.maskBits = 0
        fixtureDef2 = b2FixtureDef()
        smallerShape = b2CircleShape(radius = 0.001)
        fixtureDef2.shape = smallerShape
        fixtureDef2.maskBits = 0x0000
        return (fixtureDef1, fixtureDef2)

    def pygletDraw(self):
        """Ask all the bodies in the world and their fixtures to draw themselves,
        with the eyes' fields if self.showFields.
        The shape shader program must be active for translation/rotation
        attributes to take effect."""
        program = _get_shape_program()
        program.use()
        try:
            if self.grid is not None:
                self.grid.draw(self.grid._draw_mode)
            for body in self.world.bodies:
                body.draw()
                for fixture in body.fixtures:
                    fixture.draw(body, self.showFields)
        finally:
            program.stop()
                
    def run(self):
        "Run simulation perpetually until asked to stop"
        while self.running:
#             print "Khepera Simulation running"
            self.advanceSim()
            
    def getDistance(self,obj1Name, obj2Name):
        "return Euclidean distance between obj1 and obj2 "
        
        try:
            obj1Pos = self.allBodies[obj1Name].position
        except (KeyError, AttributeError):
            try:
                obj1Pos = self.allBodies[obj1Name].body.position
            except (KeyError, AttributeError):
                print("Cannot find object %s among the simulation's objects" % obj1Name)
                raise
        try:
            obj2Pos = self.allBodies[obj2Name].position
        except (KeyError, AttributeError):
            try:
                obj2Pos = self.allBodies[obj2Name].body.position
            except (KeyError, AttributeError):
                print("Cannot find object %s among the simulation's objects" % obj2Name)
                raise  
        
        return (obj2Pos - obj1Pos).length
    
    def setDataDir(self, dataDir):
        "Tells the trajectory writer the directory to save the trajectory files to"        
        self.dataDir = dataDir
         
class KheperaCamera(object):
    """The camera used by the the visualizer to set projection and view
       matrices for converting simulation objects' world coordinates into
       screen coordinates and to provide zoom, pan, and tilt."""

    def __init__(self, position, angle=0.0, zoom=1.0):
        self.x, self.y = position
        self.angle = angle
        self.zoom = zoom

    def focus(self, window):
        """Set projection and view matrices on the pyglet window."""
        aspect = window.width / window.height

        window.projection = Mat4.orthogonal_projection(
            -self.zoom * aspect,    # left
             self.zoom * aspect,    # right
            -self.zoom,             # bottom
             self.zoom,             # top
            -1.0,                   # z_near
             1.0                    # z_far
        )

        translation = Mat4.from_translation(Vec3(-self.x, -self.y, 0.0))
        rotation = Mat4.from_rotation(self.angle, Vec3(0.0, 0.0, 1.0))
        window.view = translation @ rotation
                            
class KheperaRobotView(object):
    """What a window shows of a robot's run in a KheperaSimulation, and the
       mouse and keys that change it; used by the phototaxis experiments'
       --visualize (phototaxis_common.run_visualized) and the GA replay.
       Drawn: the world (KheperaSimulation.pygletDraw), the robot's trail
       and, while the robot is drawn smaller than LOCATOR_PIXELS across, a
       ring of that radius around it, to find it by.
       - mouse wheel: zoom (about the pointer, or the robot when following);
       - drag: pan (and stop following);
       - F: follow the robot, or stop;
       - C: a close-up following the robot, or the whole arena;
       - V: the eyes' field arcs, or not.
       The window first shows the whole arena."""

    OVERVIEW_CENTRE = (5.5, 5.5)
    OVERVIEW_ZOOM = 8.0         # half the window's height, in metres
    CLOSE_UP_ZOOM = 0.25
    MIN_ZOOM, MAX_ZOOM = 0.03, 20.0
    ZOOM_STEP = 1.15            # per notch of the mouse wheel
    LOCATOR_PIXELS = 12
    TRAIL_MIN_DIST = 0.05       # metres moved before the trail grows
    TRAIL_COLOR = (0.8, 0.2, 0.2, 0.7)
    LOCATOR_COLOR = (0.8, 0., 0., 0.8)
    HELP = 'mouse wheel: zoom   drag: pan   F: follow   C: close-up/arena   V: eye fields'

    def __init__(self, window, sim, robotName='Khepera'):
        self.window = window
        self.sim = sim
        self.robot = sim.allBodies[robotName]
        self.camera = KheperaCamera(self.OVERVIEW_CENTRE, zoom=self.OVERVIEW_ZOOM)
        self.follow = False
        self.trail = []             # vertex lists, one per segment
        self._trailLast = None
        self._locator = None
        self._locatorRadius = None

    def metresPerPixel(self):
        return 2 * self.camera.zoom / self.window.height

    def draw(self):
        "Draw a frame"
        glClear(GL_COLOR_BUFFER_BIT)
        x, y = self.robot.body.position
        if self.follow:
            self.camera.x, self.camera.y = x, y
        self.camera.focus(self.window)
        self.sim.pygletDraw()
        program = _get_shape_program()
        program.use()
        try:
            for segment in self.trail:
                segment.draw(GL_LINES)
            radius = self.LOCATOR_PIXELS * self.metresPerPixel()
            if self.robot.diameter < radius:
                if radius != self._locatorRadius:
                    if self._locator is not None:
                        self._locator.delete()
                    self._locator = makePygletRing(radius)
                    self._locatorRadius = radius
                count = self._locator.count
                self._locator.translation[:] = [x, y] * count
                self._locator.colors[:] = list(self.LOCATOR_COLOR) * count
                self._locator.draw(self._locator._draw_mode)
        finally:
            program.stop()

    def extendTrail(self):
        "Add a segment to the trail if the robot has moved far enough since the last"
        x, y = self.robot.body.position
        if self._trailLast is None:
            self._trailLast = (x, y)
            return
        px, py = self._trailLast
        if sqrt((x - px)**2 + (y - py)**2) >= self.TRAIL_MIN_DIST:
            self.trail.append(_make_vlist(2, GL_LINES, [px, py, x, y]))
            self.trail[-1].colors[:] = list(self.TRAIL_COLOR) * 2
            self._trailLast = (x, y)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        before = self.metresPerPixel()
        self.camera.zoom = min(self.MAX_ZOOM, max(self.MIN_ZOOM,
                               self.camera.zoom * self.ZOOM_STEP ** -scroll_y))
        if not self.follow:
            # Keep the point under the pointer where it is
            change = before - self.metresPerPixel()
            self.camera.x += (x - self.window.width / 2) * change
            self.camera.y += (y - self.window.height / 2) * change

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons & mouse.LEFT:
            self.follow = False
            self.camera.x -= dx * self.metresPerPixel()
            self.camera.y -= dy * self.metresPerPixel()

    def on_key_press(self, symbol, modifiers):
        "Handle F, C and V; return True for those, False for any other key"
        if symbol == key.F:
            self.follow = not self.follow
        elif symbol == key.C:
            if self.follow and self.camera.zoom <= self.CLOSE_UP_ZOOM:
                self.follow = False
                self.camera.x, self.camera.y = self.OVERVIEW_CENTRE
                self.camera.zoom = self.OVERVIEW_ZOOM
            else:
                self.follow = True
                self.camera.zoom = self.CLOSE_UP_ZOOM
        elif symbol == key.V:
            self.sim.showFields = not self.sim.showFields
        else:
            return False
        return True


class KheperaSimulationVisualizer(pyglet.window.Window):
    """Visualizer class for KheperaSimulation. Uses pyglet backend"""
    
    def __init__(self, Box2D_timeStep = 0.032, Box2D_vel_iter = 6, Box2D_pos_iter = 2,  dataDir = None, HomeoWorld = None, width = 1200, height = 800, initialZoom = 0.2):

        super(KheperaSimulationVisualizer, self).__init__(width, height, resizable=True, fullscreen=False, visible=True, vsync=True)

        # --- constants ---
        self.TARGET_FPS=60
        self.TIME_STEP = Box2D_timeStep # defaults to 0.032 = 32 msec

        self.sim = KheperaSimulation(timeStep=self.TIME_STEP)
        self.sim.setupWorld(HomeoWorld, dataDir)

        self.init_gl(width, height)
        
        self.ZOOM_IN_FACTOR = 1.02
        self.H_DRAG_FACTOR = 0.4
        self.V_DRAG_FACTOR = 0.4
 
        self.camera = KheperaCamera((0, 0), zoom = initialZoom) #Camera initially centered at point (0,0), zoom, no tilt. 
        self.initialParam = {'width': width, 'height': height, 'zoom': initialZoom}
        
        self.simStopped = True          #Whether the simulation is stopped"

    def resetVisualization(self):
        "reset window to initialization parameters"
        self.width = self.initialParam['width']
        self.height = self.initialParam['height']
        self.camera.zoom = self.initialParam['zoom']
        self.camera.x = 0
        self.camera.y = 0   
                
    def init_gl(self, width, height):
        # Set antialiasing
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

        # Set alpha blending
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0.55, 0.95, 1.0, 1.0)   # light blue

#     def on_resize(self, width, height):
#         # Set window values
#         self.camera.x = width
#         self.camera.y = height
        
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons == 1:
#             print "camera position was at: %dx%d" % (self.camera.x, self.camera.y)
            self.camera.x -= dx * self.H_DRAG_FACTOR
            self.camera.y -= dy * self.V_DRAG_FACTOR
                
#             print "camera position is now at: %dx%d" % (self.camera.x, self.camera.y)
        elif buttons == 4:
#             print "camera angle was at: %d" % (self.camera.angle)
            self.camera.angle += dx
#             print "camera angle is now at: %d" % (self.camera.angle)
    
    def on_mouse_scroll(self, x, y, dx, dy):
        # Get proper zoom factor
        if dy > 0:
            zf = self.ZOOM_IN_FACTOR  
        elif  dy < 0:
            zf = 1/self.ZOOM_IN_FACTOR
        else:
            zf = 1

        if .2 < self.camera.zoom * zf < 50:
            self.camera.zoom *= zf

    def on_key_press(self, symbol, modifiers):
#         print "you pressed", symbol
        if symbol == key.Z and not modifiers == key.MOD_SHIFT:
            self.resetVisualization()
        elif symbol == key.Z and modifiers == key.MOD_SHIFT:
            self.sim.resetWorld()
        elif symbol == key.SPACE:
            self.simStopped = not self.simStopped
        elif symbol == key.R:
            self.sim.resetWorld()
        elif symbol == key.MINUS:
            self.sim.gridDefaultSpacing *= 0.75           
            self.sim.grid = makePygletGrid(self.sim.gridDefaultSize, self.sim.gridDefaultSpacing)
        elif symbol == key.PLUS:
            self.sim.gridDefaultSpacing /= 0.75           
            self.sim.grid = makePygletGrid(self.sim.gridDefaultSize, self.sim.gridDefaultSpacing)
        elif symbol == key.O:     # increase right wheel speed
            nudgeWheels(self.sim, 1, 0)
        elif symbol == key.L:     # decrease right wheel speed
            nudgeWheels(self.sim, -1, 0)
        elif symbol == key.Q:    # increase left wheel speed
            nudgeWheels(self.sim, 0, 1)
        elif symbol == key.A:    # decrease left wheel speed
            nudgeWheels(self.sim, 0, -1)
        elif symbol == key.F1:
            self.step()
        elif symbol == key.V:
            self.sim.showFields = not self.sim.showFields
        elif symbol == key.ESCAPE:
            pyglet.app.exit()
            pass
    
    def on_key_release(self,symbol,modifiers):
        pass
        
    def on_mouse_motion(self, x, y, dx, dy): 
        pass
        
    def on_draw(self):
        glClear(GL_COLOR_BUFFER_BIT)
        self.camera.focus(self)
        self.update(0)
      
    def run(self, app):
        pyglet.clock.schedule(app.update)
        pyglet.app.run()

    def step(self):
        if self.simStopped:
            self.sim.advanceSim()
            self.sim.pygletDraw()

    def update(self,dt):
        if not self.simStopped:
            self.sim.advanceSim()
        self.sim.pygletDraw()

def nudgeWheels(sim, dRight, dLeft):
    """Change the speeds of sim's robot's wheels by dRight and dLeft rad/s
    (the visualizer's O/L and Q/A keys).  The keys used to index getSpeed()'s
    dict by position, and a robotName the visualizer does not have, and
    crashed (review finding RS-09)."""
    robot = sim.allBodies[sim.robotName]
    speeds = robot.getSpeed()                 # m/s at the rim
    robot.setSpeed(speeds['right'] / robot.wheelRadius + dRight,
                   speeds['left'] / robot.wheelRadius + dLeft)


def runKheperaSimulator(headless = False, dataDir = None, HomeoWorld = None, Box2D_timeStep = 0.032, Box2D_vel_iter = 6, Box2D_pos_iter = 2, window_width = 800, window_height = 400, window_initialZoom = 0.2):
    """Runs the Khepera simulator either in headless mode (no graphics, for fast simulations) or with the openGl visualization class"""
    
    if dataDir is None:
        dataDir = dated_data_dir()
    print(dataDir)
    if not headless:
        app = KheperaSimulationVisualizer(Box2D_timeStep=Box2D_timeStep, Box2D_vel_iter=Box2D_vel_iter, 
                                          Box2D_pos_iter=Box2D_pos_iter, HomeoWorld = HomeoWorld,                                          
                                          dataDir = dataDir, width = window_width, height = window_height, 
                                          initialZoom = window_initialZoom)
        app.run(app)
        return app
    else:
        sim = KheperaSimulation(running=True, timeStep=Box2D_timeStep, vel_iters=Box2D_vel_iter,
                                pos_iters=Box2D_pos_iter)
        sim.setupWorld(HomeoWorld, dataDir)
        return sim
     
if __name__=="__main__":
    """Testing code"""

#     app = KheperaSimulationVisualizer()
#     app.run()

    "Testing the deterministic features of the  simulator in headless mode"

    a = runKheperaSimulator(headless=True, HomeoWorld = "kheperaBraitenberg2_HOMEO_World")
#     a = runKheperaSimulator(headless=False,HomeoWorld = "kheperaBraitenberg2_HOMEO_World")  
 
    steps = 10
    runs = 1
    for run in range(runs):
        timeNow  = time()
        dis = a.getDistance(a.robotName, 'TARGET')
        print("%d Initial distance to target is %.3f  " % (run+1, dis), end=' ')
        for k in range(steps):
            a.advanceSim()
            dis = a.getDistance(a.robotName, 'TARGET')
#             print("sim's current step is", a.currentStep)
        print("%d: Final distance to target is %.3f, time elapsed is %f" % (run+1, dis, time()- timeNow))
        print("resetting simulation...")
        a.resetWorld()
# #         print "Starting simulation again"
#         print "distance to target is %.3f, time elapsed is %f" % (dis, time()- timeNow)

#     "Testing the deterministic features of the  simulator in graphic mode"
#     vis = KheperaSimulationVisualizer(HomeoWorld = "kheperaBraitenberg2_HOMEO_World")      
# #     runKheperaSimulator(headless=False,HomeoWorld = "kheperaBraitenberg2_HOMEO_World")  
#     a = vis.sim
#     steps = 12000
#     runs = 5
#     for run in xrange(runs):
#         timeNow  = time()
#         dis = a.getDistance(self.robotName, 'TARGET')    
#         print "%d Initial distance to target is %.3f  " % (run+1, dis),
#         for k in xrange(steps):
#             vis.step()
#             dis = a.getDistance(self.robotName, 'TARGET')
# #             print "sim's current step is", a.currentStep
#         print "%d: Final distance to target is %.3f, time elapsed is %f" % (run+1, dis, time()- timeNow)
#         print "resetting simulation..."
#         a.resetWorld()
# #         print "Starting simulation again"
#         print "distance to target is %.3f, time elapsed is %f" % (dis, time()- timeNow)
    
    
    "End of testing code"
    
