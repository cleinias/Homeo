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
    parser.add_argument('--dark', action='store_true',
                        help='Treat the light source as a darkness source '
                             '(reverses the irradiance gradient)')
    args = parser.parse_args(argv[1:])
    graphTrajectory(args.traj_file, output_path=args.output, dark=args.dark)


def graphTrajectory(trajDataFilename, output_path=None, dark=False):
    """Chart the vehicle's trajectory with matplotlib.

    The background shows a radial grey gradient centered on the light
    source, representing the irradiance field.  For positive-intensity
    lights the centre is bright and the edges dark (the robot is avoiding
    brightness); for negative-intensity (dark) lights the centre is dark
    and the edges bright (the robot is seeking darkness).

    Args:
        trajDataFilename: path to a .traj file
        output_path: if provided, save the figure to this path (PDF, PNG, etc.)
                     instead of displaying interactively.
        dark: if True, treat the source as a "darkness source" (reverses
              the gradient direction).
    """

    'Read simulation general data from header'
    dataFileHeader = readDataFileHeader(trajDataFilename)
    lightsOnDic = readLightsFromHeader(dataFileHeader)
    initPos = readInitPosFromHeader(dataFileHeader)

    'read trajectory data'
    trajData = np.loadtxt(trajDataFilename, skiprows=len(dataFileHeader), ndmin=2)
    if trajData.shape[0] == 0:
        raise ValueError("The file contains a header but no trajectory data "
                         "(the simulation's trajectory was never written to disk).")

    'Compute initial and final distance'
    initPosData = [trajData[:,0][0], trajData[:,1][0]]
    finalPos = [trajData[:,0][-1],trajData[:,1][-1]]
    # Use TARGET if present, otherwise fall back to LIGHT1 or first source
    target = lightsOnDic.get('TARGET') or lightsOnDic.get('LIGHT1')
    if target is None and lightsOnDic:
        target = next(iter(lightsOnDic.values()))
    if target is not None:
        initialDistance = sqrt((target[0] - initPosData[0])**2 + (target[1] - initPosData[1])**2)
        finalDistance = sqrt((target[0] - finalPos[0])**2 + (target[1] - finalPos[1])**2)
    else:
        initialDistance = finalDistance = 0.0
    ticks = len(trajData)

    'build plot'
    fig, ax = plt.subplots()

    margin = 1.5
    # Compute bounds from all sources plus trajectory
    all_source_x = [s[0] for s in lightsOnDic.values()] if lightsOnDic else [0]
    all_source_y = [s[1] for s in lightsOnDic.values()] if lightsOnDic else [0]
    xmin = min(trajData[:,0].min(), min(all_source_x)) - margin
    xmax = max(trajData[:,0].max(), max(all_source_x)) + margin
    ymin = min(trajData[:,1].min(), min(all_source_y)) - margin
    ymax = max(trajData[:,1].max(), max(all_source_y)) + margin

    # Draw radial irradiance gradient as background
    target = lightsOnDic.get('TARGET')
    if target is not None:
        tx, ty, intensity = target[0], target[1], target[2]
        nx, ny = 300, 300
        x_grid = np.linspace(xmin, xmax, nx)
        y_grid = np.linspace(ymin, ymax, ny)
        X, Y = np.meshgrid(x_grid, y_grid)
        D = np.sqrt((X - tx)**2 + (Y - ty)**2)
        # Irradiance falloff matching the simulator: 1/d² attenuation.
        # Use 1/(1+d²) which naturally maps to [0,1] and avoids the
        # singularity at d=0 while preserving the 1/d² proportionality.
        irrad_norm = 1.0 / (1.0 + D**2)
        # Positive light: bright at centre (high irradiance = white)
        # Negative light (dark): dark at centre (high proximity = dark)
        if dark:
            gray = 1.0 - irrad_norm
        else:
            gray = irrad_norm
        # Map to grey range [0.45, 1.0] so trajectory line stays readable
        gray = 0.45 + 0.55 * gray
        ax.imshow(gray, extent=[xmin, xmax, ymin, ymax], origin='lower',
                  cmap='gray', vmin=0, vmax=1, aspect='equal', zorder=0)

    ax.plot(trajData[:,0], trajData[:,1], zorder=2)
    ax.set_title(os.path.split(trajDataFilename)[1])
    if output_path is None:
        fig.canvas.manager.set_window_title(os.path.split(trajDataFilename)[1])

    'Add summary info above the plot'
    if ticks >= 1000000:
        time_str = "{:,.0f}K".format(ticks / 1000)
    elif ticks >= 1000:
        time_str = "{:.0f}K".format(ticks / 1000)
    else:
        time_str = str(ticks)
    summary = ("Initial distance: {:.3f}    Final distance: {:.3f}    "
               "Time: {}".format(initialDistance, finalDistance, time_str))
    ax.set_xlabel(summary, fontsize=9)

    for lightName, light in lightsOnDic.items():
        lightPos = (light[0],light[1])
        # Color markers by quality based on source name prefix
        marker_color = 'black'
        name_lower = lightName.lower()
        if name_lower.startswith('temp'):
            marker_color = _QUALITY_COLORS['temperature']
        elif name_lower.startswith('oxy'):
            marker_color = _QUALITY_COLORS['oxygen']
        elif name_lower.startswith('org'):
            marker_color = _QUALITY_COLORS['organic']
        elif name_lower.startswith('light') or name_lower == 'target':
            marker_color = _QUALITY_COLORS['light']
        ax.add_artist(Circle(lightPos, 0.15, alpha=1, color=marker_color, zorder=3))
    startPose = (trajData[0][0],trajData[0][1])
    startMark = Circle(startPose, 0.05, alpha=1, color='green', zorder=3)
    ax.add_artist(startMark) #draw starting position in green
    endPose = (trajData[-1][0],trajData[-1][1])
    endMark = Circle(endPose, 0.05, alpha=1, color='red', zorder=3)
    ax.add_artist(endMark)   # Draw end position in red
    ax.set_aspect('equal')   # Otherwise circle comes out as an ellipse
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

    if output_path:
        fig.savefig(output_path, bbox_inches='tight')
        plt.close(fig)
    else:
        plt.show()
    
_QUALITY_COLORS = {
    'light':       'gold',
    'temperature': 'red',
    'oxygen':      'cyan',
    'organic':     'limegreen',
}

def readLightsFromHeader(dataFileHeader):
    """Read source positions from a trajectory file header.

    Recognizes any header line with format:
        NAME  x  y  intensity  True
    where NAME is any non-numeric word.  Returns a dict of
    {name: [x, y, intensity]} for sources that are turned on.
    """

    lightsOnDic = {}
    for line in dataFileHeader:
        parts = line.split()
        if len(parts) >= 5 and parts[-1] == 'True':
            name = parts[0]
            try:
                x = float(parts[1])
                y = float(parts[2])
                intensity = float(parts[3])
                lightsOnDic[name] = [x, y, intensity]
            except (ValueError, IndexError):
                continue
    return lightsOnDic

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
   main(sys.argv)