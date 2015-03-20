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
    glColor4f(self.userData['color'][0],self.userData['color'][1],self.userData['color'][2],self.userData['color'][3])
    glTranslatef(self.position[0], self.position[1],0)
    glRotatef(self.angle, 0,0,1)
    try:
        self.userData['pygletShape'].draw(self.userData['filled'])
    except KeyError:
        "Body does not know how to draw itself. Skip it"
        pass
    
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
        self.changeBodyVelocity('Unspecified', (xVel, yVel))
        self.world.Step(self.timeStep, self.vel_iters, self.pos_iters)
    
    def resetSim(self):
        raise Exception("Not implemented yet")

    def createKheperaWorld(self):
        """Create an empty world with a khepera-like objects and a few lights"""
         
        'Constants'
        backgroundColor = (0.55,.95,1.0,1.0)               # light blue in openGl [0,1] float format ('c4f')
        kheperaRobotColor  = (1.0,0.0,0.0,1.0)             # solid red in openGl [0,1] float format ('c4f')
        lightColor = (1.0,1.0,0.0,1.0)                     # solid yellow in openGl [0,1] float format ('c4f')
        lightDefaultPosition = (7,7)
        lightDefaultRadius = .03
        kheperaRobotDefaultName = 'Unspecified'
        kheperaDefaultRadius = 0.063                        # diameter of Khepera junior is about 12.6 cm
        kheperaWorld = b2World(gravity = (0,0))             #Setting gravity to 0 lets us simulate horizontal movement in the 2D world
        backgroundBody = kheperaWorld.CreateBody(self.backgroundBodyDef(backgroundColor))
        backgroundBody.CreateFixturesFromShapes(shapes = b2PolygonShape(box=(50,10)))
        
        kheperaRobotBody = kheperaWorld.CreateBody(self.KJuniorDef(kheperaRobotColor, kheperaRobotDefaultName))
        kheperaRobotBody.CreateFixturesFromShapes(shapes = b2CircleShape(radius = kheperaDefaultRadius)) 
        
        
        lightBody = kheperaWorld.CreateBody(self.KheperaWorldLightDef(lightColor, lightDefaultPosition))
        lightBody.CreateFixturesFromShapes(shapes = b2CircleShape(radius = lightDefaultRadius))

        "Caching the vertex lists for both robot and light and store the drawing mode for filled circles or not"
        kheperaRobotBody.userData['pygletShape'] = makePygletCircle(center = (0,0), r = kheperaDefaultRadius, numPoints=100, orientation = 0)
        kheperaRobotBody.userData['filled']=GL_LINE_LOOP

        lightBody.userData['pygletShape'] =  makePygletCircle(center = (0,0), r = lightDefaultRadius, numPoints=100, orientation = 0)
        lightBody.userData['filled'] = GL_POLYGON
        return kheperaWorld
        
    def backgroundBodyDef(self,color):
        "Definition of the static simulation background"
        
        userData = {'color': color} 
        backBodyDef = b2BodyDef(position = (-10,-10),
                                userData = userData,
                                type = b2_staticBody)
        return backBodyDef
                                    
    def KJuniorDef(self, color, name):
        """Builds a Khepera-like object similar to the K-Junior model 
           used in V-REP"""
        
        userData = {'name': name, 'color':color}
        robotDef = b2BodyDef(position = (4,4),
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
    """KheperaCamera sets the OpenGL projections required to draw the simulation's objects.
       The KheperaCamera will eventually be able to pan and tilt."""
 
    def __init__(self, win, position, angle=0.0, zoom=1.0):
        self.win = win
        self.x ,self.y =  position
        self.angle = angle
        self.zoom = zoom
 
    def worldProjection(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        widthRatio = self.win.width / self.win.height
        gluOrtho2D(-self.zoom * widthRatio,
                    self.zoom * widthRatio,
                   -self.zoom,
                    self.zoom)
    
    def focus(self, win_width, win_height):
        """Set up projection matrix for 2D rendering to set proper zoom level,
           then set up Modelview matrix to allow pan and tilt"""
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        widthRatio = win_width / win_height
        gluOrtho2D(-self.zoom * widthRatio,
                    self.zoom * widthRatio,
                   -self.zoom,
                    self.zoom)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(self.x, self.y, +1.0, # camera  x,y,z
                  self.x, self.y, -1.0,  # look at x,y,z
                  sin(self.angle), cos(self.angle), 0.0) #tilt
        
         
class KheperaSimulationVisualizer(object):
    """Visualizer class for KheperaSimulation. Uses pyglet backend"""
    
    def __init__(self):
        # --- constants ---
        self.zoom =5
        self.TARGET_FPS=60
    #     TIME_STEP=1.0/TARGET_FPS
        self.TIME_STEP = 0.032 #32 msec
        self.SCREEN_WIDTH, self.SCREEN_HEIGHT=1000,800
        
        self.sim    = KheperaSimulation(timeStep=self.TIME_STEP)
        self.window = window.Window(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, "HOMEO Khepera Simulator", resizable = True, fullscreen=False, visible=True, vsync=True)
        self.camera = KheperaCamera(self.window, (0,0),zoom = self.zoom)    
        clock.set_fps_limit(60)  #??? function of this line?
        self.on_key_press = self.window.event(self.on_key_press)
        self.on_mouse_scroll = self.window.event(self.on_mouse_scroll)
        
    def on_key_press(self, symbol, modifiers):
        pass    
    
    def on_key_release(self,symbol,modifiers):
        pass
    
    def on_mouse_motion(self, x, y, dx, dy): 
        print "You moved the mouse"
        
    def on_mouse_scroll(self,x,y,scroll_x, scroll_y):
        if scroll_y > 0:
            self.camera.zoom *= 1.1
        else:
            self.camera.zoom /= 1.1 

    def run(self):
        # --- main simulation loop ---
        while not self.window.has_exit:
            self.window.dispatch_events()

            self.sim.advanceSim()

            self.camera.worldProjection()
            self.sim.pygletDraw()
            
            clock.tick()
            self.window.flip()
            
if __name__=="__main__":
    app = KheperaSimulationVisualizer()
    app.run()      
