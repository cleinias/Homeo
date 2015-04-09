'''
KheperaSimulator is a very simple robotic simulator back-end
built with the pyBox2D physics engine and the pyglet framework. 
It is meant to be used for fast 
simulations of Homeo controllers in GA experimental settings.
The basic robot is a kinematics-only differential drive Khepera-like vehicle,
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
from __future__ import division

from Box2D import *
from pyglet import clock, font, image, window
from pyglet.gl import *
from pyglet.window import mouse, key

import numpy as np

from math import sin, cos, asin, acos, atan, pi, radians, degrees, sqrt, atan2
from Helpers.General_Helper_Functions import normalize
from time import sleep
from pip._vendor.distlib.wheel import Wheel

"pyglet and openGL utility functions"

def makePygletCircle(center=(0,0), r=10, numPoints=100, orientation = 0, span = (2*pi)):
    """Create an openGL vertex list representing a circle with a radius 
       indicating the orientation. The circle is rotated according to the
       orientation parameter"""
    vertices = [] 
    vertices += [center[0],center[1]]
    orientRad = radians(orientation) 
    for i in range(numPoints  + 1):
        angle = orientRad + (float(i)/numPoints * span)
        x = (r* cos(angle))  + center[0]
        y = (r * sin(angle)) + center[1]
        vertices += [x,y]
    return pyglet.graphics.vertex_list(numPoints + 2, 
                                       ('v2f', vertices))
    
def makePygletArc(center=(0,0), r=10, numPoints=100, orientation = 0, span = (2*pi)):
    """Create an openGL vertex list representing an arc with a radius 
       indicating the orientation. The circle is rotated according to the
       orientation parameter"""
    vertices = []
    vertices += [center[0],center[1]]
    orientRad = radians(orientation) 
    for i in range(numPoints  + 1):
        angle = orientRad + (float(i)/numPoints * span) - span/2
        x = (r* cos(angle))  + center[0]
        y = (r * sin(angle)) + center[1]
        vertices += [x,y]
    vertices += [center[0],center[1]]
    vertices += [center[0],center[1]]
    return pyglet.graphics.vertex_list(numPoints + 4, 
                                       ('v2f', vertices))

def makePygletBox(width, height, orientation=0):
    """Create am openGL vertex list representing a rectangle
       (or box, in Box2D language) with given size and orientation,
       centered at 0,0"""
    vertices = [width/2, height/2, -width/2,height/2,-width/2,-height/2,width/2,-height/2]
    return pyglet.graphics.vertex_list(4,
                                       ('v2f',vertices))

"""Add drawing pyglet-specific drawing functions 
   to the box2D bodies used in Khepera world""" 

def makePygletGrid(size, spacing = 1, color = (1,1,1,1)):
    """Create an openGL vertex list representing a 
       size x size grid with indicated spacing in meters and centered at the 
       origin. If spacing is not an exact divisor, the grid size will be slightly altered
       to make it the correct size.  Default color is white"""
    vertices = []
    steps = int(size/spacing)
    for x in xrange(steps+1):
        vertices += [x*spacing,0]                            # Top vertex for T-B line
        vertices += [x*spacing,-size]                        # Bottom vertex for T-B line
        vertices += [0, -x*spacing]                          # Left vertex for L-R line
        vertices += [size,-x*spacing]                        # Right vertex for L-R line

    "Translating vertices to their real position with numpy arrays "
    translVertices = (np.reshape(vertices,(int(len(vertices)/2),-1)) + np.array([-size/2,size/2])).flatten()
    colors = color * int(len(vertices)/2)
    vLength = int(len(vertices)/2)
    return pyglet.graphics.vertex_list(vLength,('v2f',translVertices), ('c4f',colors))

def b2PygletFixtureDraw(self, body):
    """A fixture knows how to draw itself pyglet using its pre-computed shape 
       (created at initialization), but it needs the position and angle 
       of the body it is connected to to properly render itself"""
    try:
        glPushMatrix()
        if self.userData is not None:
            rotMat = b2Rot(body.angle)              # Rotation matrix for the current angle (Box2d utility)
            rotatedPose = rotMat * self.shape.pos   # Relative position of the fixture with rotation considered
            worldPose = rotatedPose + body.position # Position in world coordinates
            glTranslatef(worldPose[0], worldPose[1],0)
            glRotatef(degrees(body.angle), 0,0,1)    
            glColor4f(self.userData['color'][0],self.userData['color'][1],self.userData['color'][2],self.userData['color'][3])
            self.userData['pygletShape'].draw(self.userData['filled'])
        glPopMatrix()    
    except KeyError as e:
        print "Fixture does not know how to draw itself. Skipping it"
        print e
#         raise
#         pass
    
    
    
def b2PygletBodyDraw(self):
    """Each b2Body knows how to draw itself in pyglet using its pre-computed pyglet shape (created at initialization)"""
    
    """Since glTranslatef moves the world by a relative amount by changing the view matrix, we need to 
       save the current view matrix (by pushing it on the stack), moving the world, do our drawing and then 
       restore the previous view matrix by popping it off the stack"""
    glPushMatrix()
    glColor4f(self.userData['color'][0],self.userData['color'][1],self.userData['color'][2],self.userData['color'][3])
    glTranslatef(self.position[0], self.position[1],0)
    forwardNormal = self.GetWorldVector((1,0))
    forwardDirectionAngle = degrees(atan2(forwardNormal[1],forwardNormal[0]))
    glRotatef(forwardDirectionAngle, 0,0,1)
    try:
        self.userData['pygletShape'].draw(self.userData['filled'])
    except KeyError as e:
        print "Body does not know how to draw itself. Skipping it"
        print e
#         raise
        pass
    glPopMatrix()

def b2BodyDefaultUpdate(self):
    "Default update function for Box2D body: do nothing"
    pass
    
        
b2Body.draw = b2PygletBodyDraw
b2Fixture.draw = b2PygletFixtureDraw
b2Body.update = b2BodyDefaultUpdate

"Khepera simulation classes"

class KheperaRobot(object):
    """The body of a Khepera-like robot.
       The body is implemented as a simple circle with two wheels and light sensors.
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
           Notice that the positions of RightEye and LeftEye sensors are relative to the forward facing direction
           and correspond to a position on the outer surface of the body, at the indicated angle (drawn from K-Team specs)
           from the y axis. See addSensor function  for details on their implementation.
           
        Finally, the 'name' of the KheperaRobot is internal ref used by the simulation software to refer to the robot.
        The 'ID', instead,  is the particular version of a robot, used by the Genetic Algorithm code to record fitnesses"""

       
    def __init__(self, world, diameter = 126, wheelRadiusRatio = 0.12380, wheelThicknessRatio = 0.02380, wheelSepRatio = 0.76190, maxWheelSpeed = 100,
                 rightEyeAngle = 21.9017, leftEyeAngle = -21.9017, centerEyeAngle = 0, density = 0.8, unit = 'mm',
                 color = (1.,0.,0.,0.5), name = "Khepera", ID = "Unspecified", initialPose = (0,0)):
        
        "create body"        
        if unit == 'mm':
            factor = 0.001
        elif unit == 'cm':
            factor = 0.01
        elif unit == 'dm':
            factor = 0.1
        else:
            factor = 1
        self.diameter = diameter * factor
        self.density = density
        self.wheelRadius = self.diameter* wheelRadiusRatio
        self.maxSpeed = maxWheelSpeed * self.diameter* wheelRadiusRatio # maxSpeed is in rad/sec. convert to m/s
        
        bodyDef = b2BodyDef()
        bodyDef.type = b2_dynamicBody
        self.body = world.CreateBody(bodyDef)
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
        
        'Left wheel'       
        frontLeftWheel = KheperaWheel(world, thickness = self.diameter * wheelThicknessRatio,  diameter = self.diameter* wheelRadiusRatio*2,
                                        maxForwardSpeed = self.maxSpeed,  maxBackwardSpeed = -self.maxSpeed, name = 'Left')
        frontLeftWheel.body.position = self.body.worldCenter + (0, self.diameter * wheelSepRatio/2)
        jointDef = b2RevoluteJointDef()
        jointDef.bodyA = self.body
        jointDef.enableLimit = True
        jointDef.lowerAngle = 0
        jointDef.upperAngle = 0
        jointDef.localAnchorB = (0,0)
         
        jointDef.bodyB = frontLeftWheel.body
        jointDef.localAnchorA = (0, self.diameter * wheelSepRatio/2)
        world.CreateJoint(jointDef)
        self.wheels = {'Left': frontLeftWheel}

        'Right wheel'
        frontRightWheel = KheperaWheel(world, thickness = self.diameter * wheelThicknessRatio,  diameter = self.diameter * wheelRadiusRatio*2,
                                        maxForwardSpeed = self.maxSpeed,  maxBackwardSpeed = -self.maxSpeed, name = 'Right')  
        frontRightWheel.body.position = self.body.worldCenter + (0, -self.diameter * wheelSepRatio/2)
        jointDef = b2RevoluteJointDef()
        jointDef.bodyA = self.body
        jointDef.enableLimit = True
        jointDef.lowerAngle = 0
        jointDef.upperAngle = 0
        jointDef.localAnchorB = (0,0)
        jointDef.bodyB = frontRightWheel.body
        jointDef.localAnchorA = (0, -self.diameter * wheelSepRatio/2)
        world.CreateJoint(jointDef)
        self.wheels['Right']= frontRightWheel
        
        
        "Sensors"
        """Positions of RightEye and LeftEye sensors (in meters) relative to the center of Khepera's circular body,
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
        kheperaCenterEyeDefaultPose = (0,0.063)           # Straight center
        kheperaEyeDefaultMaxValue   = 100                 # Default clipping value (saturation value) for eye sensors, same as in V_REP
        kheperaEyeDefaultMaxRange   =  10                 # Default max range (in meters) for eye sensors, same as in V_REP
        kheperaEyeDefaultAngleRange =  90                 # Default angle range for eye sensors, in degrees, same as in V_REP
        kheperaEyeDefaultDiameterRatio = 0.04             # Default size of the sensor radius as ration of robot's size. For rendering only 
        kheperaEyeDefaultDiameterRatio = 0.1              # Default size of the sensor radius as ration of robot's size. For rendering only 
        
        self.addSensor(khepheraLeftEyeDefaultPose, 'LeftEye', diameter = self.diameter*kheperaEyeDefaultDiameterRatio, 
                       orientation = 0, maxRange = kheperaEyeDefaultMaxRange, angleRange = kheperaEyeDefaultAngleRange,
                       maxValue = kheperaEyeDefaultMaxValue)        
 
        self.addSensor(khepheraRightEyeDefaultPose, 'RightEye', diameter = self.diameter*kheperaEyeDefaultDiameterRatio, 
                       orientation = 0, maxRange = kheperaEyeDefaultMaxRange, angleRange = kheperaEyeDefaultAngleRange,
                       maxValue = kheperaEyeDefaultMaxValue)        

#         self.addSensor(kheperaCenterEyeDefaultPose, 'CenterEye', diameter = self.diameter*kheperaEyeDefaultDiameterRatio, 
#                        orientation = 0, maxRange = kheperaEyeDefaultMaxRange, angleRange = kheperaEyeDefaultAngleRange,
#                        maxValue = kheperaEyeDefaultMaxValue)        
        
        
        "Add a pyglet shape to robot's body for rendering"
        self.body.userData = {}
        self.setRenderingParameters(color = color)

    def addSensor(self, position, sensorName, diameter = 5, orientation = 0, maxRange = 10, angleRange = 90, maxValue = 100):
        """Adds a Khepera-like object light sensor that knows how to return a 
           scalar value representing the intensity (irradiance) of light falling
           upon its point-like surface.
           Sensors are implemented as 5mm radius circle Box2D *fixture*  upon a KheperaRobotBody at
           a specified position. The irradiance is measured from the center of the circle
           Main parameters are:
        - orientation   (in degrees, default is 0, i/e normal to the robot's surface
                         through the center of sensor) 
        - maxRange      (default = 10 meters, (same as in V-REP))
        - angleRange    (default = 90 degrees (same as in V-REP))
        - maxValue      (default = 100, saturation value (same as in V-REP))
        - diameter      (default = 5mm, for rendering purposes only"""

        rotMatrix = np.mat('0,1;-1,0')     #CW 90 rotation matrix  
        sensorDefaultRadius = 0.001
        positionVector = np.reshape(position, (2,1))
        sensorFixtureDef = b2FixtureDef()
        circleShape = b2CircleShape(radius = diameter/2)
        circleShape.pos = (rotMatrix * positionVector).A1
        sensorFixtureDef.shape = circleShape
        
#         sensorFixtureDef.position = (rotMatrix * positionVector).A1            
        sensorFixture = self.body.CreateFixture(sensorFixtureDef)
        
        "Store sensor's values"
        sensorFixture.userData = {}
        sensorFixture.userData[sensorName + 'MaxValue'] = maxValue
        sensorFixture.userData[sensorName + 'MaxRange'] = maxRange
        sensorFixture.userData[sensorName + 'AngleRange'] = angleRange
        
                
        "Cache angles (in degrees) of eye sensors from robot's normal heading for future computation of irradiance"
        sensorAngle = degrees(atan((rotMatrix * positionVector).A1[1]  / (rotMatrix * positionVector).A1[0]))
        sensorFixture.userData[sensorName + 'Angle']  = sensorAngle
        self.sensors[sensorName] = sensorFixture
        
        "For openGl rendering: cache vertices for a blue circle"        
        sensorFixture.userData['pygletShape'] = makePygletArc(r = maxRange, span = radians(angleRange), orientation = sensorAngle)  
        sensorFixture.userData['color'] = (0.,0.,1.,0.2)
        sensorFixture.userData['filled'] =  GL_LINE_LOOP # GL_POLYGON # 
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
        try:
            sensorFixture = self.sensors[sensorName]
        except KeyError as e:
            print "Cannot find the desired sensor: %s, KeyError: %s" % (sensorName, e)
            return 0
        
        sensorIrrad = 0 
        
        rotMatrix = b2Rot(self.body.angle)
        sensorRelPosition = rotMatrix * sensorFixture.shape.pos
        sensorPosition = self.body.position + sensorRelPosition
        
        for targetLight in lightsList:
            targetPose = targetLight.position
            vecToTarget = targetPose-sensorPosition
            targetDistance = vecToTarget.length
            lightIntensity = targetLight.userData['intensity']
            lightAttenVec = targetLight.userData['attenVec']
            eyeMaxValue = sensorFixture.userData[sensorName+'MaxValue']
            eyeAngleRange = sensorFixture.userData[sensorName+'AngleRange']
            eyeMaxRange = sensorFixture.userData[sensorName+'MaxRange']
            lightAmbRatio = targetLight.userData['ambRatio']
        
        
            "Compute vector of eye's normal from the robot's angle and cached eyeAngle."
            eyeAngle = (self.body.angle + radians(sensorFixture.userData[sensorName+'Angle']))
            eyeNormalVec = b2Vec2(cos(eyeAngle), sin(eyeAngle))
#             print "eye normal vector length = %.12f (numpy) %.12f (Box2D)" % (np.linalg.norm(eyeNormalVec), eyeNormalVec.length)
            cosAngleToTarget = b2Dot(vecToTarget/vecToTarget.length,eyeNormalVec)
#             targetAngle = atan(vecToTarget[1]/vecToTarget[0])
#             cosAngleToTarget = cos(eyeAngle - targetAngle)
#             print "cosAngle to Target = ", cosAngleToTarget
            "Testing"
#             print "V2T: %.3f,%.3f   eyeNormV: %.12f,%.12f normV2T: %.3f,%.3f   NormNormzdV2T: %.3f NormNormalEyeVec: %.13f, eyeAngle: %.12f, cos:%.3f"% (vecToTarget[0], vecToTarget[1], 
#                                                                                   eyeNormalVec[0],eyeNormalVec[1], 
#                                                                                   normalize(vecToTarget)[0], normalize(vecToTarget)[1], 
#                                                                                   np.linalg.norm(normalize(vecToTarget)), np.linalg.norm(eyeNormalVec),
#                                                                                   degrees(eyeAngle),
#                                                                                   cosAngleToTarget)
            assert -1 <= cosAngleToTarget <= 1
            np.testing.assert_allclose(np.linalg.norm(eyeNormalVec), 1)
            np.testing.assert_allclose(np.linalg.norm(normalize(vecToTarget)),1.0)      

            "End testing"
        
            "Is target in range?"
    #         print "to target: %.3f, robot's angle: %3f, angle to target: %.3f, vectToTarget: %s, OUT OF RANGE ==> %s" %(targetDistance, 
    #                                                                                            self.allBodies['Khepera'].angle,
    #                                                                                            degrees(acos(cosAngleToTarget)),
    #                                                                                            vecToTarget,
    #                                                                                            (targetDistance > eyeMaxRange or abs(degrees(acos(cosAngleToTarget))) > eyeAngleRange/2))
    #         print targetDistance, degrees(acos(cosAngleToTarget))
            if targetDistance > eyeMaxRange or (abs(degrees(acos(cosAngleToTarget))) > eyeAngleRange / 2):
                sensorIrrad +=  0
            else:        
                directIntens = (lightIntensity * (1-lightAmbRatio)) * cosAngleToTarget
                attenuationFactor = 1/( lightAttenVec[0]+
                                       (lightAttenVec[1]*targetDistance)+
                                       (lightAttenVec[2]*targetDistance**2))
    #             print "Irradiance: %.5f" % min((directIntens + (lightIntensity*lightAmbRatio)) * attenuationFactor, eyeMaxValue)            
                sensorIrrad +=  min((directIntens + (lightIntensity*lightAmbRatio)) * attenuationFactor, eyeMaxValue) # clip sensor's output to its max value
        
        return sensorIrrad
    
    def setRenderingParameters(self, color = (1.,0.,0.,0.5)):
        "default rendering: circle of partially transparent red color"
        self.body.userData['pygletShape'] = makePygletCircle(r = self.diameter / 2) 
        self.body.userData['color'] = color
        self.body.userData['filled'] =  GL_LINE_LOOP #GL_POLYGON # 

        
    def update(self):
        "Update physical state"
        self.wheels['Right'].update(self.rightSpeed)
        self.wheels['Left'].update(self.leftSpeed)
#         print "rightWheel is at: %s, leftWheel is at: %s" %(self.wheels['Right'].body.position, self.wheels['Left'].body.position)
    
    def setSpeed(self, rightSpeed, leftSpeed):
        """Wheel speed is expressed in rad/sec.
           Convert to linear wheel speeds from wheel radius"""
        self.rightSpeed = rightSpeed * self.wheelRadius
        self.leftSpeed = leftSpeed * self.wheelRadius
#         print "Wheel speeds now: L: %f, R: %f" % (self.rightSpeed ,self.leftSpeed)
    
    def getSpeed(self):
        return (self.leftSpeed, self.rightSpeed)
        
    def rotateTo(self, angleRad):
        """Rotate robot and its jointed bodies to angleRad.
          Calling function must also call the step function of the containing world
          to update positions"""
          
        self.body.angle = angleRad
        for wheel in self.wheels.values():
            wheel.body.angle = angleRad
            
    def moveTo(self, posVec):
        """Move robot and its jointed bodies to posVec.
          Calling function must also call the step function of the containing world
          to update positions"""
        self.body.position = posVec
        for wheel in self.wheels.values():
            wheel.body.position = wheel.body.position + posVec 
              
class KheperaWheel(object):
    """The Khepera-like robot's wheel-motor class. 
       KheperaWheel implements the motorized wheel of a Khepera-like
       differential drive robot. Geometrically, a wheel is implemented 
       as viewed from the top down, i.e. as a box. 
       Physically, it is a 2D block which can move forward and backward by:
       - controlling its speed (up to the maximum); or
       - sending it a force to propel it /forward/backward for brief periods of time.
       The wheel implements a constant correction of its lateral velocity component 
       to make it perform as a tire (velocity correction code 
       borrowed from http://www.iforce2d.net/b2dtut/top-down-car).
       The main parameters used to tune the wheel's behavior are:
       - self.killAngVelParam which controls the forward behavior (default 0.1)
       - self.maxForwardSpeed (default 10)   
       - self.maxBackwardSpeed (default -10)
       - self.density (the mass-controlling parameter, default 1)
       - self.tireFriction (controlling how fast the tire slows down, default -2)
       
       
       IMPORTANT: at creation, the default orientation of a wheel is 0,
                    i.e lying along the normal vector (1,0), or pointing to the right.
                    THEREFORE, the forward velocity vector is to the right and side
                    velocity is from the vector (0,-1). The methods getForwardNormal
                    and getRightNormal behave accordingly"""
       
    def __init__(self, world, thickness = 2, diameter = 31.2, 
                 killAngVelParam = 0.1, maxForwardSpeed=1, maxBackwardSpeed=-1, 
                tireFriction= -0.18, density = 1, name = None):
        
        """A wheel for the Khepera robot. Creates a rectangular body 
           of diameter X thickness size (i.e. its vertical projection)"""
        self.maxForwardSpeed =   maxForwardSpeed
        self.maxBackwardSpeed =  maxBackwardSpeed
        self.killAngVelParam = killAngVelParam
        self.tireFriction = tireFriction
                 
        bodyDef = b2BodyDef()
        bodyDef.type = b2_dynamicBody
        self.body = world.CreateBody(bodyDef)
        polygonShape = b2PolygonShape()
        polygonShape.SetAsBox(diameter/2, thickness/2)

        fixtureDef = b2FixtureDef()
        fixtureDef.density = density
        fixtureDef.shape = polygonShape
        self.body.CreateFixture(fixtureDef)
        self.force = 0
        
        "set up pyglet shape and color for rendering"
        self.body.userData = {}
        self.setRenderingParameters(diameter,thickness)
        
        if name is not None:
            self.name = name
        
        "for testing: an impulse counter"
        self.impulseCounter = 0
            
    def setRenderingParameters(self, thickness, diameter, color = (0.,0.,0.,1)):
        "default openGl rendering: box in black color"
        
        self.body.userData['pygletShape'] = makePygletBox(thickness, diameter) 
        self.body.userData['color'] = color
        self.body.userData['filled'] = GL_POLYGON
       
    def getForwardNormal(self):
        """Default forward velocity at creation is to the right (along (1,0) vector)"""
        return self.body.GetWorldVector(b2Vec2(1,0))
    
    def getRightNormal(self):
        """Default forward velocity at creation is to the right (along (1,0) vector),
           hence lateral velocity *to* the right is along (0,-1) vector"""
#         return self.body.GetWorldVector(b2Vec2(0,-1))
        return self.body.GetWorldVector(b2Vec2(0,-1))

    def getLeftNormal(self):
        """Default forward velocity at creation is to the right (along (1,0) vector),
           hence lateral velocity to the left is along (-1,0) vector"""
        return self.body.GetWorldVector(b2Vec2(0,1))

    def getRightLateralVelocity(self):
        """Component of velocity (in world coords) orthogonal to wheel's forward direction."""
        
        return b2Dot(self.getRightNormal(),self.body.linearVelocity) * self.getRightNormal()
    
    def getForwardVelocity(self):
        """Component of velocity (in world coords) in wheel's forward direction"""
        
        return b2Dot(self.getForwardNormal(),self.body.linearVelocity) * self.getForwardNormal()
    
    def getCurrentSpeed(self):
        "Current speed (norm of forward velocity) * sign"
#         print "FW vel vector %s and sign %f" % (self.getForwardVelocity(), np.sign(self.getForwardVelocity()[0])) 
        return self.getForwardVelocity().Normalize() 
        
    def updateFriction(self):
        """Cancels all of lateral velocity and part of the angular velocity,
           to make wheel's body behave more like a tire.
           Progressively slow down forward speed to simulate ground friction"""
         
        "kill lateral velocity"
        impulseRight = self.body.mass * -self.getRightLateralVelocity()
        bodyOrig = self.body.GetWorldPoint((0,0))
        self.body.ApplyLinearImpulse(impulseRight, bodyOrig, True)
                
        "kill part of angular velocity" 
        self.body.ApplyAngularImpulse(self.killAngVelParam * self.body.inertia * - self.body.angularVelocity, True)
        
#         "Apply a drag force to simulate ground friction"
#         dragForceMagnitude = self.tireFriction*0.8* self.getCurrentSpeed()
#         self.body.ApplyForce(dragForceMagnitude * self.getForwardNormal(), bodyOrig,True)           

    def updateDriveImpulse(self, desiredSpeed):
        "Apply impulse to self.body to ramp up to desiredSpeed (almost) immediately"
        
        if desiredSpeed > self.maxForwardSpeed:
            desiredSpeed = self.maxForwardSpeed
        elif desiredSpeed < self.maxBackwardSpeed:
            desiredSpeed = self.maxBackwardSpeed
            
        velChange = desiredSpeed - self.getCurrentSpeed()
        impulse = self.body.mass * velChange
        impulseVec = impulse * self.getForwardNormal()
        if self.name == 'Right':
            self.impulseCounter += 1
            print "Applying impulse # %d to wheel: %s, currently going at: %.3f " % (self.impulseCounter, self.name, self.getCurrentSpeed())
        self.body.ApplyLinearImpulse(impulseVec, self.body.GetWorldPoint((0,0)),True)
        
#         print "%s wheel: FW normal: %s, Right normal: %s" % (self.name, self.getForwardNormal(), self.getRightNormal())
        if abs(desiredSpeed) <0.001:
            self.body.fixtures[0].friction = 1 

    def updateDriveVelocity(self, desiredSpeed):
        "Apply impulse to self.body to ramp up to desiredSpeed (almost) immediately"
        
        if desiredSpeed > self.maxForwardSpeed:
            desiredSpeed = self.maxForwardSpeed
        elif desiredSpeed < self.maxBackwardSpeed:
            desiredSpeed = self.maxBackwardSpeed

        newVelocity = self.getForwardNormal() * desiredSpeed
        self.body.linearVelocity = newVelocity
#         print "Velocity changing from %s to: %s" %(self.getForwardVelocity(), newVelocity)
        
#         print "%s wheel: FW normal: %s, Right normal: %s" % (self.name, self.getForwardNormal(), self.getRightNormal())
        if abs(desiredSpeed) <0.001:
            self.body.fixtures[0].friction = 1 
        else:
            self.body.fixtures[0].friction = 0.2 

    
    def update(self, desiredSpeed):
        self.updateFriction()
#         self.updateDriveImpulse(desiredSpeed)
        self.updateDriveVelocity(desiredSpeed)
        
        
class KheperaSensor(object):
    """Implements a Khepera-like object light sensor. It knows how to return a 
       scalar value representing the intensity (irradiance) of light falling
       upon its point-like surface.
       Sensors are implemented as 5mm radius circle Box2D bodies welded upon a KheperaRobotBody at
       a specified position. The irradiance is measured from the center of the circle
       Main parameters are:
       - orientation  (in degrees, default is 0, i/e normal to the robot's surface
                      through the center of sensor) 
       - maxRange     (default = 10 meters, (same as in V-REP))
       - angleRange   (default = 90 degrees (same as in V-REP))
       - maxValue     (default = 100, saturation value (same as in V-REP))
       - diamter      (default = 5mm, for rendering purposes only"""

    def __init__(self, world, name, diameter = 5, orientation = 0, maxRange = 10, angleRange = 90, maxValue = 100):

        "setting sensors's parameters"
        self.orientation = orientation
        self.maxRange = maxRange
        self.angleRange = angleRange
        self.maxValue = maxValue
        
        "creating body and fixture"
        bodyDef = b2BodyDef()
        bodyDef.type = b2_dynamicBody
        self.body = world.CreateBody(bodyDef)
        circleShape = b2CircleShape(radius=0.001)
        fixtureDef = b2FixtureDef()
        fixtureDef.shape = circleShape
        fixtureDef.density = 0.01

        self.body.userData = {}
        self.setRenderingParameters(diameter)
        
        if name is not None:
            self.name = name
        
            
    def setRenderingParameters(self, diameter, color = (0.,0.,1.,1)):
        "default openGl rendering: blue circle"
        
        self.body.userData['pygletShape'] = makePygletCircle(r = diameter/2) 
        self.body.userData['color'] = color
        self.body.userData['filled'] = GL_POLYGON


   
class KheperaSimulation(object):
    '''
    KheperaSimulation is the overall class managing the simulation.
    It is responsible for saving/loading of simulated worlds,
    as well for managing the simulation's operation: advancing, 
    stopping, resetting, etc.
    '''
    
    "make a static background surface for the world" 

    def __init__(self, HomeoExperiment = None, timeStep = 0.032, vel_iters = 6, pos_iters = 2):
        '''
        Default time step is 1/60 of a second, values for velocity 
        and position iterations are those recommended by pyBox2D docs'''
        
        self.timeStep = timeStep
        self.vel_iters = vel_iters
        self.pos_iters = pos_iters
        self.allBodies = {} #Dictionary containing refs to all relevant bodies in the world
        "Create and cache a pyglet grid"
        self.gridDefaultSize = 20
        self.gridDefaultSpacing = 0.5
        self.grid = makePygletGrid(self.gridDefaultSize, self.gridDefaultSpacing)       #Default grid is 20x20m, 0.1 spacing

        self.world = self.createKheperaWorld()
#         self.sensorTesting()
        

    def resetWorld(self):
        self.world = self.createKheperaWorld()
        
    def braiten2a(self):
        "simulate a Braitenberg type 2a vehicle: parallel-connected motors/sensors, 'the more, the more'"
        light = self.allBodies['TARGET']
        leftEyeReading = self.allBodies['kheperaPhys'].irradAtSensor('LeftEye', [light])
        rightEyeReading = self.allBodies['kheperaPhys'].irradAtSensor('RightEye', [light])
        print "right eye sees: %3.f  left eye sees: %.3f" % (rightEyeReading, leftEyeReading)
        self.allBodies['kheperaPhys'].setSpeed(rightEyeReading,leftEyeReading)    
    
    def braiten2b(self):
        "simulate a Braitenberg type 2b vehicle: cross-connected motors/sensors, 'the more, the more'"
        light = self.allBodies['TARGET']
        leftEyeReading = self.allBodies['kheperaPhys'].irradAtSensor('LeftEye', [light])
        rightEyeReading = self.allBodies['kheperaPhys'].irradAtSensor('RightEye', [light])
        self.allBodies['kheperaPhys'].setSpeed(leftEyeReading, rightEyeReading)    

    def advanceSim(self):
        """For testing"""
        self.braiten2b()
        for body in self.allBodies.values():
            body.update()
        self.world.Step(self.timeStep, self.vel_iters, self.pos_iters)
        "for testing irradiance function"
#         print self.allBodies["kheperaPhys"].irradAtSensor('CenterEye', [self.allBodies['TARGET']])
#         print "kheperaPhys vels: %.5f , %.5f  FW_speeds: %.3f, %.3f location: %s  angle: %.3f. LeftWheel W-FW-vector:%s RightWheel W-FW-vector:%s " % (self.allBodies['kheperaPhys'].wheels['Left'].getCurrentSpeed(),
#                                                                                                         self.allBodies['kheperaPhys'].wheels['Right'].getCurrentSpeed(),
#                                                                                                         self.allBodies['kheperaPhys'].leftSpeed,
#                                                                                                         self.allBodies['kheperaPhys'].rightSpeed,
#                                                                                                         self.allBodies['kheperaPhys'].body.position, 
#                                                                                                         self.allBodies['kheperaPhys'].body.angle,
#                                                                                                         self.allBodies['kheperaPhys'].wheels['Left'].getForwardNormal(),
#                                                                                                         self.allBodies['kheperaPhys'].wheels['Right'].getForwardNormal())
    
    def resetSim(self):
        raise NotImplementedError

    def createKheperaWorld(self):
        """Create an empty world with a Khepera-like objects and one or more lights"""
                
        'Constants'
        kheperaRobotDefaultColor  = (1.0,0.0,0.0,0.5)             # solid red in openGl [0,1] float format ('c4f')
        kheperaRobotDefaultName = "Khepera"
        kheperaRobotDefaultID = 'Unspecified'
        kheperaDefaultPosition = (4,4)
        lightColor = (1.0,1.0,0.,1.0)                            # solid yellow in openGl [0,1] float format ('c4f')
        lightDefaultPosition = (7,7)
        lightDefaultRadius = .06
        lightDefaultName = "TARGET"
        
        "Create the Box2D world"
        kheperaWorld = b2World(gravity = (0,0))                   #Setting gravity to 0 lets us simulate horizontal movement in the 2D world

        'Add a robot'
        self.allBodies['kheperaPhys'] = KheperaRobot(world=kheperaWorld, unit = 'mm', color = kheperaRobotDefaultColor, name = kheperaRobotDefaultName, ID = kheperaRobotDefaultID)

        'Add a light'
        
        lightBody = kheperaWorld.CreateBody(self.KheperaWorldLightDef(lightColor, lightDefaultPosition, name = lightDefaultName))
        lightFixtures = self.KheperaWorldLightFixtureDefs(lightDefaultRadius)
        for fixtureDef in lightFixtures:
            lightBody.CreateFixture(fixtureDef)
            
        "Create a smaller (1mm) fixture at the center of the light body, will be used to compute distance to sensors in irradiance function "
        self.allBodies[lightDefaultName] = lightBody
        
        """Cache the light vertex lists and store the drawing mode for filled circles or not"""        

        lightBody.userData['pygletShape'] =  makePygletCircle(center = (0,0), r = lightDefaultRadius, numPoints=100, orientation = 0)
        lightBody.userData['filled'] = GL_POLYGON
                   
        return kheperaWorld
                                    
    def sensorTesting(self):
        """FOR TESTING"""        
        """for testing irradiance values:"""

        """move robot slightly behind origin, so that center sensor is exactly  at (0,0).
           and target exactly in front"""
#         
        self.allBodies['kheperaPhys'].rotateTo(radians(90))
        self.world.Step(self.timeStep, self.vel_iters, self.pos_iters)
        self.allBodies['kheperaPhys'].moveTo( (0,0 - (self.allBodies['kheperaPhys'].diameter/2)))
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
        
        """ End testing"""
    
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
        """Ask all the bodies in the world and their fixtures to draw themselves"""
        "Draw the grid first"
        self.grid.draw(GL_LINES)
        for body in self.world.bodies:
            body.draw()
            for fixture in body.fixtures:
                fixture.draw(body)
 
class KheperaCamera(object):
    """The camera used by the the visualizer to set OpenGL's projections 
       required to convert simulation objects' world coordinates into 
       screen coordinate and to provide zoom, pan, and tilt."""
 
    def __init__(self, position, angle=0.0, zoom=1.0):
        self.x ,self.y =  position
        self.angle = angle
        self.zoom = zoom
    
    def focus(self, win_width, win_height):
        """Set up projection matrix for 2D rendering to set proper zoom level,
           then set up Modelview matrix to allow pan and tilt"""
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = win_width / win_height
        gluOrtho2D(-self.zoom * aspect,
                    self.zoom * aspect,
                   -self.zoom,
                    self.zoom)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(self.x, self.y, +1.0,  # camera  (the "eye") is at x,y,z
                  self.x, self.y, -1.0,  # and it looks at this point x,y,z
                  sin(self.angle), cos(self.angle), 0.0) # with this angle
#         print "looking at %dx%d" % (self.x, self.y)
                            
class KheperaSimulationVisualizer(pyglet.window.Window):
    """Visualizer class for KheperaSimulation. Uses pyglet backend"""
    
    def __init__(self, Box2D_timeStep = 0.032, Box2D_vel_iter = 6, Box2D_pos_iter = 2,  HomeoExperiment = None, width = 800, height = 400, initialZoom = 0.2):
        
        #As per pyglet prog guide"
        conf = Config(sample_buffers=0,  # This parameter and the parameter "samples" allow more than one color sample. Higher quality, lower performance
              depth_size=0)              # (usually) Required for 3D rendering. Typical size is 24 bits (Default). 0 for no depth buffer (we're in 2D)
        super(KheperaSimulationVisualizer, self).__init__(width, height,config = conf, resizable = True, fullscreen=False, visible=True, vsync=True)
        
        # --- constants ---
        self.TARGET_FPS=60
        self.TIME_STEP = Box2D_timeStep # defaults to 0.032 = 32 msec

        self.sim = KheperaSimulation(timeStep=self.TIME_STEP, HomeoExperiment = HomeoExperiment)
        clock.set_fps_limit(60)  #??? function of this line?

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
        # Set clear color (aka as background color)
#         glClearColor(self.sim.background)

        # Set antialiasing
        glEnable( GL_LINE_SMOOTH )
        glEnable( GL_POLYGON_SMOOTH )
        glHint( GL_LINE_SMOOTH_HINT, GL_NICEST )

        # Set alpha blending
        glEnable( GL_BLEND )
        glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA )
        glClearColor(0.55,.95,1.0,1.0)   # light blue

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
            currentSpeeds = self.sim.allBodies['kheperaPhys'].getSpeed()
            self.sim.allBodies['kheperaPhys'].setSpeed(currentSpeeds[0], currentSpeeds[1]+1)
        elif symbol == key.L:     # decrease left wheel speed
            currentSpeeds = self.sim.allBodies['kheperaPhys'].getSpeed()
            self.sim.allBodies['kheperaPhys'].setSpeed(currentSpeeds[0], currentSpeeds[1]-1)
        elif symbol == key.Q:    # increase left wheel speed
            currentSpeeds = self.sim.allBodies['kheperaPhys'].getSpeed()
            self.sim.allBodies['kheperaPhys'].setSpeed(currentSpeeds[0]+1, currentSpeeds[1])
        elif symbol == key.A:    # decrease left wheel speed
            currentSpeeds = self.sim.allBodies['kheperaPhys'].getSpeed()
            self.sim.allBodies['kheperaPhys'].setSpeed(currentSpeeds[0]-1, currentSpeeds[1])
        elif symbol == key.F1:
            self.step()
        elif symbol == key.ESCAPE:
            pyglet.app.exit()
            pass
    
    def on_key_release(self,symbol,modifiers):
        pass
        
    def on_mouse_motion(self, x, y, dx, dy): 
        pass
        
    def on_draw(self):
        #advance simulation if necessary"
        glClear( GL_COLOR_BUFFER_BIT )
        glLoadIdentity()
#         print "Window size is %dx%d" %(self.width, self.height)
        self.camera.focus(self.width, self.height)
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

def runKheperaSimulator(headless = False, Box2D_timeStep = 0.032, Box2D_vel_iter = 6, Box2D_pos_iter = 2, HomeoExperiment = None, window_width = 800, window_height = 400, window_initialZoom = 0.2):
    """Runs the Khepera simulator either in headless mode (no graphics, for fast simulations) or with the openGl visualization class"""
    if not headless:
        app = KheperaSimulationVisualizer(Box2D_timeStep=Box2D_timeStep, Box2D_vel_iter=Box2D_vel_iter, 
                                          Box2D_pos_iter=Box2D_pos_iter, HomeoExperiment = HomeoExperiment,
                                          width = window_width, height = window_height, 
                                          initialZoom = window_initialZoom)
        app.run(app)
    else:
        sim = KheperaSimulation(Box2D_timeStep=Box2D_timeStep, Box2D_vel_iter=Box2D_vel_iter, 
                                Box2D_pos_iter=Box2D_pos_iter, HomeoExperiment = HomeoExperiment)
        sim.advanceSim()
     
if __name__=="__main__":
#     app = KheperaSimulationVisualizer()
#     app.run()
    runKheperaSimulator()      
