#!/usr/bin/env python3

'''
Created on Dec 28, 2014
Self-standing script that chart trajectories produced by the Homeo simulation package

Usage:
    python -m Helpers.TrajectoryGrapher run.traj [-o out.pdf] [--dark]
    python -m Helpers.TrajectoryGrapher run1.traj run2.traj ... [-o out.pdf]

With several files, all trajectories are drawn on one chart, each in its own
colour, with a legend below the plot that identifies each run by the part of
its filename that differs from the others (usually the timestamp).  In the
interactive window, clicking a legend entry hides/shows that trajectory, and
the first entry, "ALL on / off", hides or shows them all (keys: 'a' shows
all, 'n' hides all).  This works in the toolbar's zoom and pan modes too.

@author: stefano
'''
import matplotlib.pyplot as plt
#from matplotlib.axes.Axes import text
from matplotlib.patches import Circle
import os
import numpy as np
import pandas as pd
import sys
from math import sqrt, ceil

# Trajectories are thinned to at most this many points for plotting.  Long runs
# produce hundreds of MB of .traj data (300k ticks ~ 30 MB, 6M ticks ~ 600 MB),
# far more points than a chart can show.  The first and last points are always kept.
MAX_PLOT_POINTS = 50000


def main(argv):
    import argparse
    parser = argparse.ArgumentParser(description='Chart one or more Homeostat trajectories.')
    parser.add_argument('traj_files', nargs='+', metavar='traj_file',
                        help='Path(s) to .traj file(s); several files are drawn on one chart')
    parser.add_argument('--output', '-o', default=None,
                        help='Save figure to file (PDF, PNG, etc.) instead of displaying')
    parser.add_argument('--dark', action='store_true',
                        help='Treat the light source as a darkness source '
                             '(reverses the irradiance gradient)')
    parser.add_argument('--max-points', type=int, default=MAX_PLOT_POINTS,
                        help='Thin each trajectory to at most this many plotted points '
                             '(default %(default)s)')
    args = parser.parse_args(argv[1:])
    graphTrajectories(args.traj_files, output_path=args.output, dark=args.dark,
                      maxPoints=args.max_points)


def graphTrajectory(trajDataFilename, output_path=None, dark=False, maxPoints=MAX_PLOT_POINTS):
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
        maxPoints: thin the trajectory to at most this many plotted points.
    """

    'Read header and (thinned) trajectory data'
    dataFileHeader, trajData, ticks = loadTrajectory(trajDataFilename, maxPoints)
    lightsOnDic = readLightsFromHeader(dataFileHeader)

    'Compute initial and final distance'
    target = _mainTarget(lightsOnDic)
    if target is not None:
        initialDistance = _distance(target, trajData[0])
        finalDistance = _distance(target, trajData[-1])
    else:
        initialDistance = finalDistance = 0.0

    'build plot'
    fig, ax = plt.subplots()
    xmin, xmax, ymin, ymax = _plotBounds([trajData], lightsOnDic)
    _drawIrradianceBackground(ax, lightsOnDic, (xmin, xmax, ymin, ymax), dark)

    ax.plot(trajData[:,0], trajData[:,1], zorder=2)
    ax.set_title(os.path.split(trajDataFilename)[1])
    if output_path is None:
        fig.canvas.manager.set_window_title(os.path.split(trajDataFilename)[1])

    'Add summary info above the plot'
    summary = ("Initial distance: {:.3f}    Final distance: {:.3f}    "
               "Time: {}".format(initialDistance, finalDistance, _formatTicks(ticks)))
    ax.set_xlabel(summary, fontsize=9)

    _drawSources(ax, lightsOnDic)
    startMark = Circle(tuple(trajData[0]), 0.05, alpha=1, color='green', zorder=3)
    ax.add_artist(startMark) #draw starting position in green
    endMark = Circle(tuple(trajData[-1]), 0.05, alpha=1, color='red', zorder=3)
    ax.add_artist(endMark)   # Draw end position in red
    ax.set_aspect('equal')   # Otherwise circle comes out as an ellipse
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

    _showOrSave(fig, output_path)


def graphTrajectories(trajDataFilenames, output_path=None, dark=False, maxPoints=MAX_PLOT_POINTS):
    """Chart several trajectories on the same axes.

    Each trajectory gets its own colour; its end point is marked with a dot of
    the same colour, the (shared) start point in green.  The axes are sized to
    show every trajectory in full.  A legend below the plot labels each run by
    the distinguishing ending of its filename, plus its final distance from the
    target.  A single file is charted with graphTrajectory().
    """
    if len(trajDataFilenames) == 1:
        return graphTrajectory(trajDataFilenames[0], output_path, dark, maxPoints)

    labels = _distinctEndings(trajDataFilenames)
    runs = []
    lightsOnDic = {}
    for filename, label in zip(trajDataFilenames, labels):
        print("Reading %s ..." % os.path.basename(filename), file=sys.stderr, flush=True)
        header, trajData, ticks = loadTrajectory(filename, maxPoints)
        for name, light in readLightsFromHeader(header).items():
            lightsOnDic.setdefault(name, light)
        runs.append((label, trajData, ticks))

    target = _mainTarget(lightsOnDic)
    colors = _distinctColors(len(runs))

    xmin, xmax, ymin, ymax = _plotBounds([t for _, t, _ in runs], lightsOnDic)
    # Size the figure to the data's aspect ratio (equal axes would otherwise leave
    # empty bands), plus room for the title, x label and legend rows.
    interactive = output_path is None
    nEntries = len(runs) + (1 if interactive else 0)    # + the "ALL on / off" entry
    ncol = min(nEntries, 4 if nEntries <= 12 else 5)
    legendRows = ceil(nEntries / ncol)
    width = 9.0
    plotHeight = width * min(max((ymax - ymin) / (xmax - xmin), 0.35), 1.5)
    fig, ax = plt.subplots(figsize=(width, plotHeight + 1.0 + 0.25 * legendRows),
                           layout='constrained')
    _drawIrradianceBackground(ax, lightsOnDic, (xmin, xmax, ymin, ymax), dark)

    finalDistances = []
    runArtists = []      # per run: [trajectory line, end marker, start marker]
    for (label, trajData, ticks), color in zip(runs, colors):
        if target is not None:
            finalDistance = _distance(target, trajData[-1])
            finalDistances.append(finalDistance)
            label = "%s  (d=%.2f)" % (label, finalDistance)
        line, = ax.plot(trajData[:,0], trajData[:,1], color=color, linewidth=0.8, alpha=0.85,
                        zorder=2, label=label)
        end, = ax.plot(*trajData[-1], marker='o', markersize=6, color=color,
                       markeredgecolor='black', linestyle='none', zorder=5)
        start, = ax.plot(*trajData[0], marker='o', markersize=4, color='green',
                         linestyle='none', zorder=4)
        runArtists.append([line, end, start])

    _drawSources(ax, lightsOnDic, asMarkers=True)
    ax.set_aspect('equal')
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

    common = _commonPrefix([os.path.splitext(os.path.basename(f))[0] for f in trajDataFilenames])
    title = "%d trajectories" % len(runs) + (": %s" % common.rstrip('-_ ') if common else "")
    ax.set_title(title, fontsize=10)
    if output_path is None:
        fig.canvas.manager.set_window_title(
            title + "   [click legend entries to hide/show; a = all, n = none]")
    if finalDistances:
        ax.set_xlabel("Final distance: mean %.3f   min %.3f   max %.3f    Time: %s"
                      % (np.mean(finalDistances), min(finalDistances), max(finalDistances),
                         _formatTicks(max(t for _, _, t in runs))), fontsize=9)

    handles, labels = ax.get_legend_handles_labels()
    if interactive:
        from matplotlib.lines import Line2D
        handles = [Line2D([], [], color='black')] + handles
        labels = ['ALL on / off'] + labels
    legend = fig.legend(handles, labels, loc='outside lower center', ncol=ncol, fontsize=8,
                        frameon=False, handlelength=2.0, columnspacing=1.5)
    for handle in legend.legend_handles:     # thick, opaque swatches: the plotted
        handle.set_linewidth(4)              # lines are thin and translucent
        handle.set_alpha(1.0)
    if interactive:
        legend.get_texts()[0].set_fontweight('bold')
        _enableLegendToggles(fig, legend, runArtists)

    _showOrSave(fig, output_path)


def _enableLegendToggles(fig, legend, runArtists):
    """Make the legend an on/off switch board for the trajectories.

    Clicking a legend entry (swatch or label) hides or shows that run's
    trajectory and its start/end markers; a hidden run's entry is dimmed.
    The first legend entry, "ALL on / off", hides every run if all are shown
    and shows every run otherwise.  Keys: 'a' shows all runs, 'n' hides all.
    runArtists must be in the order of the legend entries after the first.

    Clicks are hit-tested directly rather than through matplotlib pick
    events: the toolbar's zoom and pan modes lock the canvas and suppress
    pick events for as long as they stay active, whereas the legend lies
    outside the axes, where those tools ignore clicks.
    """
    allHandle, allText = legend.legend_handles[0], legend.get_texts()[0]
    entries = list(zip(runArtists, legend.legend_handles[1:], legend.get_texts()[1:]))
    for handle in legend.legend_handles:
        handle.set_pickradius(6)     # used by Line2D.contains() for the swatch

    def setVisible(entry, visible):
        artists, handle, text = entry
        for artist in artists:
            artist.set_visible(visible)
        handle.set_alpha(1.0 if visible else 0.2)
        text.set_alpha(1.0 if visible else 0.35)

    def setAllVisible(visible):
        for entry in entries:
            setVisible(entry, visible)
        fig.canvas.draw_idle()

    def onClick(event):
        if event.button != 1:
            return
        if allHandle.contains(event)[0] or allText.contains(event)[0]:
            setAllVisible(not all(entry[0][0].get_visible() for entry in entries))
            return
        for entry in entries:
            _, handle, text = entry
            if handle.contains(event)[0] or text.contains(event)[0]:
                setVisible(entry, not entry[0][0].get_visible())
                fig.canvas.draw_idle()
                return

    def onKey(event):
        if event.key in ('a', 'n'):
            setAllVisible(event.key == 'a')

    fig.canvas.mpl_connect('button_press_event', onClick)
    fig.canvas.mpl_connect('key_press_event', onKey)


def loadTrajectory(trajDataFilename, maxPoints=MAX_PLOT_POINTS):
    """Read a .traj file.

    Returns (header, xy, nRows): the header lines, an (N, 2) array of robot
    x, y positions thinned to at most about maxPoints rows (first and last
    rows always included), and the total number of data rows in the file.
    Reads in chunks, so very large files never have to fit in memory whole.
    Incomplete rows (e.g. the last line of a run still being written) are skipped.
    """
    header = readDataFileHeader(trajDataFilename)
    step = max(1, ceil(_countLines(trajDataFilename) / max(1, maxPoints)))
    kept = []
    nRows = 0
    last = None
    try:
        reader = pd.read_csv(trajDataFilename, sep=r'\s+', header=None, usecols=[0, 1],
                             skiprows=len(header), dtype=np.float64, chunksize=1_000_000)
        for chunk in reader:
            xy = chunk.to_numpy()
            xy = xy[~np.isnan(xy).any(axis=1)]
            if len(xy) == 0:
                continue
            kept.append(xy[(-nRows) % step::step])
            last = xy[-1]
            nRows += len(xy)
    except pd.errors.EmptyDataError:
        pass
    if nRows == 0:
        raise ValueError("The file contains a header but no trajectory data "
                         "(the simulation's trajectory was never written to disk).")
    xy = np.vstack(kept)
    if not np.array_equal(xy[-1], last):
        xy = np.vstack([xy, last])
    return header, xy, nRows


def _countLines(filename):
    "Count newline characters quickly (binary, 16 MB blocks)."
    n = 0
    with open(filename, 'rb') as f:
        for block in iter(lambda: f.read(1 << 24), b''):
            n += block.count(b'\n')
    return n


def _mainTarget(lightsOnDic):
    "Use TARGET if present, otherwise fall back to LIGHT1 or the first source."
    target = lightsOnDic.get('TARGET') or lightsOnDic.get('LIGHT1')
    if target is None and lightsOnDic:
        target = next(iter(lightsOnDic.values()))
    return target


def _distance(target, pos):
    return sqrt((target[0] - pos[0])**2 + (target[1] - pos[1])**2)


def _plotBounds(trajectories, lightsOnDic):
    """Axis limits enclosing every trajectory and every source, plus a margin
       (at least 1.5, or 5% of the larger span for trajectories that roam far)."""
    xs = [t[:,0] for t in trajectories] + [np.array([s[0] for s in lightsOnDic.values()] or [0])]
    ys = [t[:,1] for t in trajectories] + [np.array([s[1] for s in lightsOnDic.values()] or [0])]
    xmin = min(x.min() for x in xs); xmax = max(x.max() for x in xs)
    ymin = min(y.min() for y in ys); ymax = max(y.max() for y in ys)
    margin = max(1.5, 0.05 * max(xmax - xmin, ymax - ymin))
    return xmin - margin, xmax + margin, ymin - margin, ymax + margin


def _drawIrradianceBackground(ax, lightsOnDic, bounds, dark):
    "Draw a radial irradiance gradient around TARGET as the chart background."
    target = lightsOnDic.get('TARGET')
    if target is None:
        return
    xmin, xmax, ymin, ymax = bounds
    tx, ty = target[0], target[1]
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


def _drawSources(ax, lightsOnDic, asMarkers=False):
    """Mark each source, coloured by quality (from its name prefix).
       asMarkers=True draws fixed-size markers, which stay visible when the
       axes span a large area; otherwise circles of radius 0.15 world units."""
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
        if asMarkers:
            ax.plot(*lightPos, marker='o', markersize=10, color=marker_color,
                    markeredgecolor='black', linestyle='none', zorder=3)
        else:
            ax.add_artist(Circle(lightPos, 0.15, alpha=1, color=marker_color, zorder=3))


def _distinctColors(n):
    """n visually distinct colours: tab10 up to 10; tab20 up to 20, reordered so
       the 10 dark shades come before their light partners; 'turbo' beyond that."""
    if n <= 10:
        return [plt.get_cmap('tab10')(i) for i in range(n)]
    if n <= 20:
        tab20 = plt.get_cmap('tab20')
        order = list(range(0, 20, 2)) + list(range(1, 20, 2))
        return [tab20(i) for i in order[:n]]
    return [plt.get_cmap('turbo')(x) for x in np.linspace(0.05, 0.95, n)]


def _commonPrefix(names):
    "Longest common prefix of names, cut back to the last '-' or '_' separator."
    prefix = os.path.commonprefix(names)
    if len(prefix) == min(len(n) for n in names):
        return prefix
    cut = max(prefix.rfind('-'), prefix.rfind('_'))
    return prefix[:cut + 1] if cut >= 0 else ''


def _distinctEndings(filenames):
    """Short labels for filenames: the basename without extension, minus the
       prefix shared by all of them (cut at a '-'/'_' separator), e.g. the
       timestamp.  Falls back to parent folder + basename if they coincide."""
    names = [os.path.splitext(os.path.basename(f))[0] for f in filenames]
    prefix = _commonPrefix(names)
    labels = [n[len(prefix):] or n for n in names]
    if len(set(labels)) < len(labels):
        labels = [os.path.join(os.path.basename(os.path.dirname(os.path.abspath(f))), n)
                  for f, n in zip(filenames, names)]
    return labels


def _formatTicks(ticks):
    if ticks >= 1000000:
        return "{:,.0f}K".format(ticks / 1000)
    elif ticks >= 1000:
        return "{:.0f}K".format(ticks / 1000)
    return str(ticks)


def _showOrSave(fig, output_path):
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
