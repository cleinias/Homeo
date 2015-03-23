'''
KheperaSimulator is a very simple robotic simulator back-end
built with the pyBox2D physics engine. It is meant to be used for fast 
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
from Box2D import *
# import pygame
# from pygame.locals import *
from pyglet import clock, font, image, window
from pyglet.gl import *
from pyglet.window import mouse, key

import numpy as np

from math import sin, cos, pi
from time import sleep

"pyglet and openGL utility functions"

def makePygletCircle(center=(0,0), r=10, numPoints=100, orientation = 0):
    """Create an openGL vertex list representing a circle with a radius 
       indicating the orientation. The circle is rotated according to 
       rotation parameter"""
    vertices = [] 
    vertices += [center[0],center[1]]
    orientRad = orientation / 360 * 2 * pi
    for i in range(numPoints  + 1):
        angle = orientRad + (float(i)/numPoints * 2*pi)
        x = (r* cos(angle))  + center[0]
        y = (r * sin(angle)) + center[1]
        vertices += [x,y]
    return pyglet.graphics.vertex_list(numPoints + 2, 
                                       ('v2f', vertices))


"""Add drawing pyglet-specific drawing functions 
   to the box2D bodies used in Khepera world""" 
def pygletDraw(self):
    """Each b2Body knows how to draw itself in pyglet using its pre-computed pyglet shape (at initialization)"""
    
    """Since glTranslatef moves the world by a relative amount by changing the view matrix, we need to 
       save the current view matrix (by pushing it on the stack), moving the world, do our drawing and then 
       restore the previous view matrix by popping it off the stack"""
    glPushMatrix()
    glColor4f(self.userData['color'][0],self.userData['color'][1],self.userData['color'][2],self.userData['color'][3])
    glTranslatef(self.position[0], self.position[1],0)
    glRotatef(self.angle, 0,0,1)
    try:
        self.userData['pygletShape'].draw(self.userData['filled'])
    except KeyError:
        "Body does not know how to draw itself. Skip it"
        pass
    glPopMatrix()
    
b2Body.draw = pygletDraw

"Khepera simulation classes"
    
class KheperaSimulation(object):
    '''
    KheperaSimulation is the overall class managing the simulation.
    It is responsible for saving/loading of simulated worlds,
    as well for managing the simulation's operation: advancing, 
    stopping, resetting, etc.
    '''
    
    "make a static background surface for the world" 

    def __init__(self, timeStep = 0.032, vel_iters = 6, pos_iters = 2):
        '''
        Default time step is 1/60 of a second, values for velocity 
        and position iterations are those recommended by pyBox2D docs'''
        
        self.timeStep = timeStep
        self.vel_iters = vel_iters
        self.pos_iters = pos_iters
        self.world = self.createKheperaWorld()
    
    def changeBodyVelocity(self, name, velocity):
        for body in self.world.bodies:
            try:
                if body.userData['name'] == name:
                    body.linearVelocity = velocity
            except KeyError:
                "Body has no name---pass"
                pass

    def changeAngularVelocity(self, name, angVelocity):                                       
        for body in self.world.bodies:
            try:
                if body.userData['name'] == name:
                    body.angularVelocity = angVelocity
            except KeyError:
                "Body has no name---pass"
                pass

    def advanceSim(self):
        """For testing"""
        xVel = np.random.uniform(-5,5)
        yVel = np.random.uniform(-5,5)
#         self.changeBodyVelocity('Unspecified', (xVel, yVel))
        self.changeAngularVelocity('Unspecified', 100)
        self.world.Step(self.timeStep, self.vel_iters, self.pos_iters)
#         print "Position of TARGET is:", self.world.bodies[2].position
#         print "Position of robot is: ", self.world.bodies[1].position
    
    def resetSim(self):
        raise Exception("Not implemented yet")

    def createKheperaWorld(self):
        """Create an empty world with a khepera-like objects and a few lights"""
         
        'Constants'
        backgroundColor = (0.55,.95,1.0,1.0)               # light blue in openGl [0,1] float format ('c4f')
        kheperaRobotColor  = (1.0,0.0,0.0,1.0)             # solid red in openGl [0,1] float format ('c4f')
        kheperaRobotDefaultName = 'Unspecified'
        kheperaDefaultRadius = 0.063                        # diameter of Khepera junior is about 12.6 cm
        kheperaDefaultPosition = (4,4)
        lightColor = (1.0,1.0,0.0,1.0)                     # solid yellow in openGl [0,1] float format ('c4f')
        lightDefaultPosition = (7,7)
        lightDefaultRadius = .03
        kheperaWorld = b2World(gravity = (0,0))             #Setting gravity to 0 lets us simulate horizontal movement in the 2D world
        backgroundBody = kheperaWorld.CreateBody(self.backgroundBodyDef(backgroundColor))
        backgroundBody.CreateFixturesFromShapes(shapes = b2PolygonShape(box=(50,10)))
        
        kheperaRobotBody = kheperaWorld.CreateBody(self.KJuniorDef(kheperaRobotColor, kheperaRobotDefaultName,kheperaDefaultPosition))
        kheperaRobotBody.CreateFixturesFromShapes(shapes = b2CircleShape(radius = kheperaDefaultRadius)) 
        
        
        lightBody = kheperaWorld.CreateBody(self.KheperaWorldLightDef(lightColor, lightDefaultPosition))
        lightBody.CreateFixturesFromShapes(shapes = b2CircleShape(radius = lightDefaultRadius))

        "Caching the vertex lists for both robot and light and store the drawing mode for filled circles or not"
        kheperaRobotBody.userData['pygletShape'] = makePygletCircle(center = (0,0), r = kheperaDefaultRadius, numPoints=100, orientation = 0)
        kheperaRobotBody.userData['filled']=GL_LINE_LOOP

        lightBody.userData['pygletShape'] =  makePygletCircle(center = (0,0), r = lightDefaultRadius, numPoints=100, orientation = 0)
        lightBody.userData['filled'] = GL_POLYGON
        
        
        """FOR TESTING"""
        kheperaRobotBody.angle = 90

        """ End testing"""
        
        return kheperaWorld
        
    def backgroundBodyDef(self,color):
        "Definition of the static simulation background"
        
        userData = {'color': color} 
        backBodyDef = b2BodyDef(position = (-10,-10),
                                userData = userData,
                                type = b2_staticBody)
        return backBodyDef
                                    
    def KJuniorDef(self, color, name, position):
        """Builds a Khepera-like object similar to the K-Junior model 
           used in V-REP"""
        
        userData = {'name': name, 'color':color}
        robotDef = b2BodyDef(position = position,
                             type = b2_kinematicBody ,   # We just worry about position and speed
                             userData = userData)
        return robotDef
        
    def KheperaWorldLightDef(self, color, position, intensity=None, name=None):
        "Definition of a static light-like object."
        "position is a tuple (x,y)"
        
        if intensity is None:
            intensity = 100
        if name is None:
            name = 'TARGET'            
        userData = {'intensity' : intensity, 'color': color, 'name': name}             
        lightDef = b2BodyDef(position = position,
                                        userData = userData,
                                        type = b2_staticBody)        
        return lightDef

    def pygletDraw(self, zoom = 1):
        """Clear openGl buffer, and reset the model view matrix, then
           ask all the bodies in the world to draw themselves"""
        
        glClear(GL_COLOR_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        for body in self.world.bodies:
            body.draw()


 
class KheperaCamera(object):
    """The camera used by the the visualizer to set OpenGL's projections 
       required to convert simulation objects' world coordinates into 
       screen coordinate and to provide zoom, pan, and tilt."""
 
    def __init__(self, position, angle=0.0, zoom=1.0):
        self.x ,self.y =  position
        self.angle = angle
        self.zoom = zoom
#  
#     def worldProjection(self):
#         glMatrixMode(GL_PROJECTION)
#         glLoadIdentity()
#         aspect = self.win.width / self.win.height
#         gluOrtho2D(-self.zoom * aspect,
#                     self.zoom * aspect,
#                    -self.zoom,
#                     self.zoom)
    
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
    
    def __init__(self, width = 800, height = 400, initialZoom = 1):
        
        #As per pyglet prog guide"
        conf = Config(sample_buffers=0,  # This parameter and the parameter "samples" allow more than one color sample. Higher quality, lower performance
              depth_size=0)              # (usually) Required for 3D rendering. Typical size is 24 bits (Default). 0 for no depth buffer (we're in 2D)
        super(KheperaSimulationVisualizer, self).__init__(width, height,config = conf, resizable = True, fullscreen=False, visible=True, vsync=True)
        
        # --- constants ---
        self.TARGET_FPS=60
        self.TIME_STEP = 0.032 #32 msec

        self.sim    = KheperaSimulation(timeStep=self.TIME_STEP)
        clock.set_fps_limit(60)  #??? function of this line?

        self.init_gl(width, height)
        
        self.ZOOM_IN_FACTOR = 1.2
        
        self.camera = KheperaCamera((0, 0), zoom = initialZoom) #Camera initially centered at point (0,0), zoom, no tilt. 
        self.initialParam = {'width': width, 'height': height, 'zoom': initialZoom}

    def resetVisualization(self):
        "reset window to initialization parameters"
        self.width = self.initialParam['width']
        self.height = self.initialParam['height']
        self.camera.zoom = self.initialParam['zoom']
        
                
    def init_gl(self, width, height):
        # Set clear color (light grey)
#         glClearColor(.9, .9, .9, 1)

        # Set antialiasing
        glEnable( GL_LINE_SMOOTH )
        glEnable( GL_POLYGON_SMOOTH )
        glHint( GL_LINE_SMOOTH_HINT, GL_NICEST )

        # Set alpha blending
        glEnable( GL_BLEND )
        glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA )

        # Set viewport
#         glViewport( -100, -100, width, height)
#     
#     def on_resize(self, width, height):
#         # Set window values
#         self.width  = width
#         self.height = height
#         # Initialize OpenGL context
# #         self.init_gl(width, height)
        
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons == 1:
            print "camera position was at: %dx%d" % (self.camera.x, self.camera.y)
            self.camera.x += dx
            self.camera.y += dy
            
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            glTranslatef(dx, dy, 0.0)#,  # camera  (the "eye") is at x,y,z
#                       0,0, -1.0,  # and it looks at this point x,y,z
#                       0, 1, 0.0) # with this angle
    
            print "camera position is now at: %dx%d" % (self.camera.x, self.camera.y)
        elif buttons == 4:
            print "camera angle was at: %d" % (self.camera.angle)
            self.camera.angle += dx
            print "camera angle is now at: %d" % (self.camera.angle)
    
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
        print "you pressed", symbol
        if symbol == key.Z:
            self.resetVisualization()
        elif symbol == key.ESCAPE:
            pass
    
    def on_key_release(self,symbol,modifiers):
        pass
        
    def on_mouse_motion(self, x, y, dx, dy): 
        pass
        
    def on_draw(self):
        #advance simulation"
        self.sim.advanceSim()
        glClear( GL_COLOR_BUFFER_BIT )
        glLoadIdentity()
        print "Window size is %dx%d" %(self.width, self.height)
        self.camera.focus(self.width, self.height)
        self.sim.pygletDraw()
      
    def run(self):
        pyglet.app.run()

              
if __name__=="__main__":
    app = KheperaSimulationVisualizer()
    app.run()      
