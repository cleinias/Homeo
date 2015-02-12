'''
Created on Feb 7, 2015

@author: stefano

Script testing Player-Stage determinist runs.
Runs Player Stage repeatedly with a deterministic
series of random motor commands (over TCP/IP)

Assumes:
1. Stage world Homeo-world-one-light.cfg (or different world passed on command line) 
   is present in 'worlds' subdir of $HOMEO/src/Player-Stage/Homeo-Experiments/worlds 
2. player can be launched from command line
3. Khepera robot's controller listens on localhost:6665
'''



import math
from playercpp import *
import os 
from time import sleep
from subprocess import  call
import numpy as np

# # 1. Start player
# worldsDir = '/home/stefano/Documents/Projects/Homeostat/Simulator/Python-port/Homeo/src/Player-Stage/Homeo-Experiments/worlds'
# world = 'Homeo-world-one-light.cfg'   
# os.environ["PLAYERPATH"] = "/usr/local/lib:/usr/local/lib64"
# OLD_LIBRAY_PATH = os.environ["LD_LIBRARY_PATH"]
# os.environ["LD_LIBRARY_PATH"] = OLD_LIBRAY_PATH + ":" + "/usr/local/lib:/usr/local/lib64"
# os.environ["STAGEPATH"]="/usr/local/lib:/usr/local/lib64"
# call(["/home/stefano/Documents/Projects/Homeostat/Simulator/Python-port/Homeo/src/Player-Stage/Homeo-Experiments/worlds/launch-player.sh"])

def dtor(d):
    'Convert degrees to radians'
    return (d % 360) * math.pi /180

class TestPlayerStageDeterm(object):
    
    def __init__(self):
        self.target = "Target"
        self.origPos = [4, 4, 0]
        self.port = 6665
    
    def connectAll(self):
        # Create a client object and test connection
        self.khepera = PlayerClient('localhost', self.port)
        self.khepera.SetDataMode(2)
        if not self.khepera.Connected():
          raise Exception
        else:
            print "CONNECTED TO KHEPERA"
         
        # Create a proxy for position2d:0
        self.position = Position2dProxy(self.khepera,0)
         
        # create a proxy for the simulation
        self.simulation = SimulationProxy(self.khepera,0)
        
    def doOneRun(self,nRuns):
        # Start the robot going randomly
        np.random.seed(1)
        for i in xrange(nRuns):
            speed = np.random.uniform(100)
            speedTime = self.simulation.GetElapsedTime()
            turn = -360 + np.random.uniform(720)
            turnTime = self.simulation.GetElapsedTime()
#             print "speed is %.2f at %f and turn is %.2f at %f" % (speed, speedTime,turn,turnTime)
            self.position.SetSpeed(speed, dtor(turn))
            sleep(0.03)

    def stopAndReset(self): 
        # # Now stop
        self.position.SetSpeed(0.0, 0.0)
        # bring robot back to original position
        self.distanceFromTarget()
        self.simulation.SetPose2d("khepera1", self.origPos[0], self.origPos[1], self.origPos[2])
    
    def distanceFromTarget(self):
        x_t = new_doublePtr()
        y_t = new_doublePtr()
        r_t = new_doublePtr()
        self.simulation.GetPose2d("Target", x_t, y_t, r_t)
        targetPos = [doublePtr_value(x_t),doublePtr_value(y_t)]
        x_k = new_doublePtr()
        y_k = new_doublePtr()
        r_k = new_doublePtr()
        self.simulation.GetPose2d("khepera1",x_k,y_k,r_k)
        khepPos = [doublePtr_value(x_k),doublePtr_value(y_k)]
        delete_doublePtr(x_t)
        delete_doublePtr(y_t)
        delete_doublePtr(r_t)
        delete_doublePtr(x_k)
        delete_doublePtr(y_k)
        delete_doublePtr(r_k)
#         print "target is at:\t %.3f\t%.3f" % (targetPos[0],targetPos[1])
        print "khepera is at:\t %.3f\t%.3f" % (khepPos[0],khepPos[1]),
        disToTarget = math.sqrt((targetPos[0]-khepPos[0])**2 + (targetPos[1] - khepPos[1])**2)
        print "Distance from target is: %.3f " % disToTarget  
        return disToTarget

        
        
        
if __name__ == "__main__":
    devnull = open(os.devnull, 'w')
    playerTestDeterm = TestPlayerStageDeterm()
    playerTestDeterm.connectAll()
    for x in xrange(10):
        playerTestDeterm.doOneRun(80)
        playerTestDeterm.stopAndReset()
    print "done"
