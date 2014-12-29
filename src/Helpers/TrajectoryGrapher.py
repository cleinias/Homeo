#!/usr/bin/python2

'''
Created on Dec 28, 2014
Self-standing script that chart trajectories produced by the Homeo simulation package
@author: stefano
'''
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import os
import numpy as np
import sys


def main(argv):
    try:
        graphTrajectory(sys.argv[1])
    except IndexError:
        print "Usage: TrajectoryGraph filename"
    except:
            print "You entered filename: ", sys.argv[1]
            print "File not found"


def graphTrajectory(trajDataFilename):
    "Chart the vehicle's trajectory with matplotlib"
     
    headerLength = 13 #FIXME: compute the header length from the data file 
    try:
        trajData = np.loadtxt(trajDataFilename, skiprows=headerLength)
    except:
        print "cannot open the file"
    fig = plt.figure()
    plt.plot(trajData[:,0],trajData[:,1]) 
    plt.ylabel('y')
    plt.xlabel('x')
    plt.title(trajDataFilename)
    ax = fig.add_subplot(111)
    xmin = ymin = 0         # chart boundaries
    xmax =  ymax = 18
    # read light positions"
    dataFileHeader = []
    dataFile = open(trajDataFilename,"r")
    for i, line in enumerate(dataFile):
        if i < headerLength:
            dataFileHeader.append(line)
        else:
            break
    dataFile.close()
    lightPosList = []
    lightsList = ["LIGHT" + str(i+1) for i in xrange(10)]
    lightsList.append("TARGET")
    lightsOn = [] 
    for line in dataFileHeader:
        if (any(x in lightsList for x in line.split()) and ("True" in line.split())):
            lightsAt = [float(line.split()[1]),float(line.split()[2]),float(line.split()[3])]
            lightsOn.append(lightsAt) #list of turned on lights, each represented as a list including x, y coordinates and light intensity
    cMap = plt.get_cmap('Blues')  # Use a matplotlib color map to map lights' intensity
    for light in lightsOn:
        lightPos = (light[0],light[1])  
        lightRadius = 1.5      # FIXME Provisional. Need to read from trajectory data file
        ax.add_artist(Circle(lightPos, 0.05, alpha=1,color = 'black')) # marks the center of the light cone
        print "the light intensity is %f/n", light[2]
        # parametrize color value to light intensity 
        ax.add_artist(Circle(lightPos, lightRadius, alpha = 0.25, color = cMap(light[2]))) # light cone
    startPose = (trajData[0][0],trajData[0][1])
    startMark = Circle(startPose, 0.05, alpha =1, color = 'green')
    ax.add_artist(startMark) #draw starting position in green
    endPose = (trajData[-1][0],trajData[-1][1])
    endMark = Circle(endPose, 0.05, alpha =1, color = 'red')
    ax.add_artist(endMark)   #draw end position in red
    ax.axis('equal')         # Otherwise circle comes out as an ellipse
    ax.axis([xmin,xmax,ymin,ymax])
    plt.show()
    
if __name__ == "__main__":
   main(sys.argv[0])