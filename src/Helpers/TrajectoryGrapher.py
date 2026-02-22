#!/usr/bin/env python3

'''
Created on Dec 28, 2014
Self-standing script that chart trajectories produced by the Homeo simulation package
@author: stefano
'''
import matplotlib.pyplot as plt
#from matplotlib.axes.Axes import text
from matplotlib.patches import Circle
import os
import numpy as np
import sys
from math import sqrt


def main(argv):
    import argparse
    parser = argparse.ArgumentParser(description='Chart a Homeostat trajectory.')
    parser.add_argument('traj_file', help='Path to the .traj file')
    parser.add_argument('--output', '-o', default=None,
                        help='Save figure to file (PDF, PNG, etc.) instead of displaying')
    args = parser.parse_args(argv[1:])
    graphTrajectory(args.traj_file, output_path=args.output)


def graphTrajectory(trajDataFilename, output_path=None):
    """Chart the vehicle's trajectory with matplotlib.

    Args:
        trajDataFilename: path to a .traj file
        output_path: if provided, save the figure to this path (PDF, PNG, etc.)
                     instead of displaying interactively.
    """

    'Read simulation general data from header'
    dataFileHeader = readDataFileHeader(trajDataFilename)
    lightsOnDic = readLightsFromHeader(dataFileHeader)
    initPos = readInitPosFromHeader(dataFileHeader)

    'read trajectory data'
    try:
        trajData = np.loadtxt(trajDataFilename, skiprows=len(dataFileHeader))
    except Exception as e:
        print("Cannot open the file: ", e)

    'Compute final distance'
    finalPos = [trajData[:,0][-1],trajData[:,1][-1]]
    finalDistance = sqrt((lightsOnDic['TARGET'][0]- finalPos[0])**2+ (lightsOnDic['TARGET'][1] - finalPos[1])**2)

    'build plot'
    fig, ax = plt.subplots()
    ax.plot(trajData[:,0],trajData[:,1])
    ax.set_ylabel('y')
    ax.set_xlabel('x')
    ax.set_title(os.path.split(trajDataFilename)[1])
    if output_path is None:
        fig.canvas.manager.set_window_title(os.path.split(trajDataFilename)[1])

    'Add final distance to plot'
    finalDisString = "Final distance: "+ str(round(finalDistance,3))
    ax.text(0.15, 0.95,finalDisString,
     horizontalalignment='center',
     verticalalignment='center',
     transform = ax.transAxes)

    xmin = float(initPos[0]) - 2         # chart boundaries
    ymin = float(initPos[0]) - 2
    xmax = lightsOnDic['TARGET'][0] + 2.5
    ymax = lightsOnDic['TARGET'][1] + 2.5
    cMap = plt.get_cmap('Blues')  # Use a matplotlib color map to map lights' intensity
    for lightName, light in lightsOnDic.items():
        lightPos = (light[0],light[1])
        lightRadius = 1.5      # FIXME Provisional. Need to read from trajectory data file
        ax.add_artist(Circle(lightPos, 0.15, alpha=1,color = 'black')) # marks the center of the light cone
        # parametrize color value to light intensity
        ax.add_artist(Circle(lightPos, lightRadius, alpha = 0.25, color = cMap(light[2]))) # light cone
    startPose = (trajData[0][0],trajData[0][1])
    startMark = Circle(startPose, 0.05, alpha =1, color = 'green')
    ax.add_artist(startMark) #draw starting position in green
    endPose = (trajData[-1][0],trajData[-1][1])
    endMark = Circle(endPose, 0.05, alpha =1, color = 'red')
    ax.add_artist(endMark)   # Draw end position in red
    ax.axis('equal')         # Otherwise circle comes out as an ellipse
    ax.axis([xmin,xmax,ymin,ymax])

    if output_path:
        fig.savefig(output_path, bbox_inches='tight')
        plt.close(fig)
    else:
        plt.show()
    
def readLightsFromHeader(dataFileHeader):
    """Read the lights position from a trajectory file header""" 
    
    lightPosList = []
    lightsList = ["LIGHT" + str(i+1) for i in range(10)]
    lightsList.append("TARGET")
    lightsOnDic = {}
    for line in dataFileHeader:
        if (any(x in lightsList for x in line.split()) and ("True" in line.split())):
            lightsAt = [float(line.split()[1]),float(line.split()[2]),float(line.split()[3])]
            lightsOnDic[line.split()[0]]=lightsAt #dictionary of turned on lights, each represented as a list including x, y coordinates and light intensity
    return lightsOnDic
    'read initial position'

def readInitPosFromHeader(dataFileHeader):
    for lineNo in range(len(dataFileHeader)):
        if ('initial' in dataFileHeader[lineNo].split() and 'position' in dataFileHeader[lineNo].split()):
            try:
                return dataFileHeader[lineNo+1].split()
            except IndexError:
                return []
    return []

def readDataFileHeader(trajDataFilename):
    '''read the file header = all lines up to and including
       the column names line (contains "robot_x" or "coordinates")'''

    dataFileHeader = []
    dataFile = open(trajDataFilename,"r")
    for line in dataFile:
        dataFileHeader.append(line)
        words = line.split()
        if 'coordinates' in words or 'robot_x' in words or '# robot_x' in words:
            break
    dataFile.close()
    return dataFileHeader

  
if __name__ == "__main__":
   main(sys.argv[0])