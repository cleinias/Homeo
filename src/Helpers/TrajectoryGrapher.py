#!/usr/bin/env python3
# Copyright (C) 2014-2026 Stefano Franchi
#
# This file is part of Homeo, a simulation of Ashby's homeostat and of
# homeostat-controlled robots.
#
# Homeo is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# Homeo is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with Homeo.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

'''
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
The figure keeps its full size however many runs the legend lists: when it
does not fit on the screen, the window scrolls instead of shrinking the plot.

The background is the field the file records (RobotTrajectoryWriter's field
snapshots: the chemical eyes' field, sampled on a grid at the run's start and
end), in grey on a log scale with contours at FIELD_CONTOURS of its peak.
--field-time picks the moment: end (the default), start, or both, two panels
side by side, whose trajectories the legend hides and shows together.  A file
that records no field gets a warning: one whose sources have no field law
(phototaxis) is shaded with a schematic of the light, 1 / (1 + d^2) around
TARGET; one with field laws but no snapshot is not shaded.  With several
files, the chart shows the first file's field that has one.
'''
import matplotlib.pyplot as plt
#from matplotlib.axes.Axes import text
from matplotlib.patches import Circle
import os
import re
import numpy as np
import pandas as pd
import sys
from math import sqrt, ceil

# Trajectories are thinned to at most this many points for plotting.  Long runs
# produce hundreds of MB of .traj data (300k ticks ~ 30 MB, 6M ticks ~ 600 MB),
# far more points than a chart can show.  The first and last points are always kept.
MAX_PLOT_POINTS = 50000

# The recorded field's shading: grey on a log scale from the field's peak down
# to FIELD_SHADING_FLOOR of it, with contours at FIELD_CONTOURS of the peak
# (the visualizer's, KheperaRobotView.FIELD_CONTOURS)
FIELD_SHADING_FLOOR = 0.001
FIELD_CONTOURS = (0.5, 0.1, 0.01)
FIELD_TIMES = ('end', 'start', 'both')

# The no-input ring: the radius, in world units, beyond which the main source
# gives the eyes no input at all, whatever the vehicle's heading.  Outside it
# the vehicle is driven by nothing but its own noise -- the no-input state the
# equilibrium analysis calls an attractor; a run ending outside it has reached
# it.
#
# An eye stops seeing a source of intensity I where the irradiance on its axis
# falls to its threshold I0, at sqrt(I / I0) (KheperaRobot.eyeResponse) --
# never for the default eye (I0 = 0), 10 units from an intensity-100 light for
# a log eye with I0 = 1.  The chart takes I0 from the trajectory's header or
# the run's JSON beside it, and draws no ring when neither says
# (noInputRadius); --sensor-range overrides it.


def main(argv=None):
    if argv is None:
        argv = sys.argv
    import argparse
    parser = argparse.ArgumentParser(description='Chart one or more Homeostat trajectories.')
    parser.add_argument('traj_files', nargs='+', metavar='traj_file',
                        help='Path(s) to .traj file(s); several files are drawn on one chart')
    parser.add_argument('--output', '-o', default=None,
                        help='Save figure to file (PDF, PNG, etc.) instead of displaying')
    parser.add_argument('--dark', action='store_true',
                        help='Treat the light source as a darkness source '
                             '(reverses the irradiance gradient).  A file that '
                             'records a negative intensity in its header says so '
                             'itself; needed only for a file that does not')
    parser.add_argument('--sensor-range', type=float, default=None,
                        help='Radius of the no-input ring drawn around the target, '
                             'the distance beyond which the eyes see nothing of it '
                             '(default: sqrt(intensity / eye threshold), from the '
                             "file's header or the run's JSON; no ring for eyes with "
                             'threshold 0 or when neither records it).  0 omits the '
                             'ring.')
    parser.add_argument('--max-points', type=int, default=MAX_PLOT_POINTS,
                        help='Thin each trajectory to at most this many plotted points '
                             '(default %(default)s)')
    parser.add_argument('--field-time', choices=FIELD_TIMES, default='end',
                        help='The recorded field to shade: at the run\'s end (the default), '
                             'at its start, or both, in two panels')
    args = parser.parse_args(argv[1:])
    graphTrajectories(args.traj_files, output_path=args.output, dark=args.dark,
                      maxPoints=args.max_points, sensorRange=args.sensor_range,
                      fieldTime=args.field_time)


def graphTrajectory(trajDataFilename, output_path=None, dark=False, maxPoints=MAX_PLOT_POINTS,
                    sensorRange=None, fieldTime='end'):
    """Chart the vehicle's trajectory with matplotlib.

    The background is the field the file records at fieldTime (see
    fieldPanels; 'both': two panels).  A file whose sources have no field
    law gets a radial grey gradient centered on the light source instead, a
    schematic of the irradiance: for positive-intensity lights the centre is
    bright and the edges dark (the robot is avoiding brightness); for
    negative-intensity (dark) lights the centre is dark and the edges bright
    (the robot is seeking darkness).

    Args:
        trajDataFilename: path to a .traj file
        output_path: if provided, save the figure to this path (PDF, PNG, etc.)
                     instead of displaying interactively.
        dark: if True, treat the source as a "darkness source" (reverses
              the gradient direction).
        maxPoints: thin the trajectory to at most this many plotted points.
        sensorRange: the no-input ring's radius, 0 for none; None: the run's
                     own (noInputRadius).
        fieldTime: the recorded field to shade, one of FIELD_TIMES.
    """

    'Read header and (thinned) trajectory data'
    dataFileHeader, trajData, nRows = loadTrajectory(trajDataFilename, maxPoints)
    ticks = ticksFromRows(dataFileHeader, nRows, readStepsRecorded(trajDataFilename))
    lightsOnDic = readLightsFromHeader(dataFileHeader)
    dark = dark or _hasDarknessSource(lightsOnDic)
    if sensorRange is None:
        sensorRange = noInputRadius(dataFileHeader, lightsOnDic, trajDataFilename)

    'Compute initial and final distance'
    target = _mainTarget(lightsOnDic)
    if target is not None:
        initialDistance = _distance(target, trajData[0])
        finalDistance = _distance(target, trajData[-1])
    else:
        initialDistance = finalDistance = 0.0

    'build plot'
    panels = fieldPanels([trajDataFilename], [dataFileHeader], fieldTime)
    fig, axes = plt.subplots(1, len(panels), squeeze=False, figsize=(6.4 * len(panels), 4.8))
    xmin, xmax, ymin, ymax = _plotBounds([trajData], lightsOnDic, sensorRange)
    name = os.path.split(trajDataFilename)[1]
    if output_path is None:
        fig.canvas.manager.set_window_title(name)
    'Add summary info above the plot'
    summary = ("Initial distance: {:.3f}    Final distance: {:.3f}    "
               "Time: {}".format(initialDistance, finalDistance, _formatTicks(ticks)))

    for ax, (moment, background) in zip(axes[0], panels):
        _drawBackground(ax, background, lightsOnDic, (xmin, xmax, ymin, ymax), dark)
        _drawNoInputBoundary(ax, lightsOnDic, sensorRange)
        ax.plot(trajData[:,0], trajData[:,1], zorder=2)
        # two panels: the file's name once, above both
        ax.set_title(_momentTitle(moment).strip() if len(panels) > 1 else name + _momentTitle(moment))
        ax.set_xlabel(summary, fontsize=9)
        _drawSources(ax, lightsOnDic)
        startMark = Circle(tuple(trajData[0]), 0.05, alpha=1, color='green', zorder=3)
        ax.add_artist(startMark) #draw starting position in green
        endMark = Circle(tuple(trajData[-1]), 0.05, alpha=1, color='red', zorder=3)
        ax.add_artist(endMark)   # Draw end position in red
        ax.set_aspect('equal')   # Otherwise circle comes out as an ellipse
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
    if len(panels) > 1:
        fig.suptitle(name)

    _showOrSave(fig, output_path)


def graphTrajectories(trajDataFilenames, output_path=None, dark=False, maxPoints=MAX_PLOT_POINTS,
                      sensorRange=None, fieldTime='end'):
    """Chart several trajectories on the same axes.

    Each trajectory gets its own colour; its end point is marked with a dot of
    the same colour, the (shared) start point in green.  The axes are sized to
    show every trajectory in full.  A legend below the plot labels each run by
    the distinguishing ending of its filename, plus its final distance from the
    target.  A single file is charted with graphTrajectory().  With
    sensorRange None, the no-input ring is drawn only if every run has the same.
    The background is the first recorded field's at fieldTime (fieldPanels);
    with 'both', two panels, whose trajectories the legend toggles together.
    """
    if len(trajDataFilenames) == 1:
        return graphTrajectory(trajDataFilenames[0], output_path, dark, maxPoints, sensorRange,
                               fieldTime)

    labels = _distinctEndings(trajDataFilenames)
    runs = []
    headers = []
    lightsOnDic = {}
    radii = set()
    for filename, label in zip(trajDataFilenames, labels):
        print("Reading %s ..." % os.path.basename(filename), file=sys.stderr, flush=True)
        header, trajData, nRows = loadTrajectory(filename, maxPoints)
        headers.append(header)
        ticks = ticksFromRows(header, nRows, readStepsRecorded(filename))
        lights = readLightsFromHeader(header)
        for name, light in lights.items():
            lightsOnDic.setdefault(name, light)
        if sensorRange is None:
            radii.add(round(noInputRadius(header, lights, filename), 9))
        runs.append((label, trajData, ticks))
    if sensorRange is None:
        sensorRange = radii.pop() if len(radii) == 1 else 0.0
        if radii:
            print("The runs' eyes see to different distances: no no-input ring "
                  "(--sensor-range draws one)", file=sys.stderr)

    target = _mainTarget(lightsOnDic)
    colors = _distinctColors(len(runs))
    panels = fieldPanels(trajDataFilenames, headers, fieldTime)

    xmin, xmax, ymin, ymax = _plotBounds([t for _, t, _ in runs], lightsOnDic, sensorRange)
    # Size the figure to the data's aspect ratio (equal axes would otherwise leave
    # empty bands), plus room for the title, x label and legend rows.
    interactive = output_path is None
    nEntries = len(runs) + (1 if interactive else 0)    # + the "ALL on / off" entry
    ncol = min(nEntries, 4 if nEntries <= 12 else 5)
    legendRows = ceil(nEntries / ncol)
    width = 9.0 if len(panels) == 1 else 14.0
    plotHeight = (width / len(panels)) * min(max((ymax - ymin) / (xmax - xmin), 0.35), 1.5)
    fig, axes = plt.subplots(1, len(panels), squeeze=False,
                             figsize=(width, plotHeight + 1.0 + 0.25 * legendRows),
                             layout='constrained')
    dark = dark or _hasDarknessSource(lightsOnDic)
    common = _commonPrefix([os.path.splitext(os.path.basename(f))[0] for f in trajDataFilenames])
    title = "%d trajectories" % len(runs) + (": %s" % common.rstrip('-_ ') if common else "")
    if output_path is None:
        fig.canvas.manager.set_window_title(
            title + "   [click legend entries to hide/show; a = all, n = none]")

    finalDistances = []
    labels = []
    for label, trajData, ticks in runs:
        if target is not None:
            finalDistance = _distance(target, trajData[-1])
            finalDistances.append(finalDistance)
            label = "%s  (d=%.2f)" % (label, finalDistance)
        labels.append(label)
    # per run: its trajectory line, end marker and start marker, in every panel
    runArtists = [[] for _ in runs]
    for ax, (moment, background) in zip(axes[0], panels):
        _drawBackground(ax, background, lightsOnDic, (xmin, xmax, ymin, ymax), dark)
        _drawNoInputBoundary(ax, lightsOnDic, sensorRange)
        for artists, (_, trajData, _), label, color in zip(runArtists, runs, labels, colors):
            line, = ax.plot(trajData[:,0], trajData[:,1], color=color, linewidth=0.8,
                            alpha=0.85, zorder=2, label=label)
            end, = ax.plot(*trajData[-1], marker='o', markersize=6, color=color,
                           markeredgecolor='black', linestyle='none', zorder=5)
            start, = ax.plot(*trajData[0], marker='o', markersize=4, color='green',
                             linestyle='none', zorder=4)
            artists += [line, end, start]
        _drawSources(ax, lightsOnDic, asMarkers=True)
        ax.set_aspect('equal')
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.set_title(title + _momentTitle(moment), fontsize=10)
        if finalDistances:
            ax.set_xlabel("Final distance: mean %.3f   min %.3f   max %.3f    Time: %s"
                          % (np.mean(finalDistances), min(finalDistances), max(finalDistances),
                             _formatTicks(max(t for _, _, t in runs))), fontsize=9)

    handles, labels = axes[0][0].get_legend_handles_labels()
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
        _makeScrollable(fig)

    _showOrSave(fig, output_path)


def _makeScrollable(fig):
    """Put the figure's canvas in a scroll area, with the figure's own size as
    its minimum.

    The figure is sized for its legend, 0.25 in per row, so with many runs it is
    taller than the screen.  Qt then fits the window to the screen and the
    constrained layout, which must keep the whole legend visible, takes the
    difference out of the plot: at 200 runs the plot would be a thumbnail.  Here the
    canvas can grow with the window but never shrinks below the figure's size;
    a smaller window scrolls instead.  The mouse wheel scrolls the window too.

    A no-op on non-Qt backends.
    """
    window = getattr(fig.canvas.manager, 'window', None)
    if window is None or not hasattr(window, 'takeCentralWidget'):
        return
    from matplotlib.backends.qt_compat import QtWidgets
    canvas = fig.canvas
    width, height = canvas.get_width_height()    # logical pixels, as Qt sizes widgets
    window.takeCentralWidget()    # setCentralWidget alone would delete the canvas
    scroll = QtWidgets.QScrollArea()
    scroll.setWidgetResizable(True)
    canvas.setMinimumSize(width, height)
    scroll.setWidget(canvas)
    window.setCentralWidget(scroll)

    # Matplotlib accepts every wheel event; pass them on to the scroll area.
    wheelEvent = canvas.wheelEvent
    def scrollingWheelEvent(event):
        wheelEvent(event)
        event.ignore()
    canvas.wheelEvent = scrollingWheelEvent

    # Open as large as the figure, but no larger than the screen.
    frame = 2 * scroll.frameWidth() + scroll.verticalScrollBar().sizeHint().width()
    toolbar = getattr(fig.canvas.manager, 'toolbar', None)
    extra = toolbar.sizeHint().height() if toolbar is not None else 0
    available = window.screen().availableGeometry()
    window.resize(min(width + frame, available.width()),
                  min(height + frame + extra, int(available.height() * 0.95)))
    canvas.setFocus()


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
    Incomplete rows (e.g. the last line of a run still being written) are
    skipped: rows with a missing field, and a last line with no newline, which
    may be cut in the middle of a number.
    """
    header = readDataFileHeader(trajDataFilename)
    step = max(1, ceil(_countLines(trajDataFilename) / max(1, maxPoints)))
    complete = _endsWithNewline(trajDataFilename)
    kept = []
    nRows = 0
    last = None

    def take(chunk):
        nonlocal nRows, last
        xy = chunk.to_numpy()
        xy = xy[~np.isnan(xy).any(axis=1)]
        if len(xy) == 0:
            return
        kept.append(xy[(-nRows) % step::step])
        last = xy[-1]
        nRows += len(xy)

    try:
        # comment='#': the last line of a closed file is "# Steps recorded"
        reader = pd.read_csv(trajDataFilename, sep=r'\s+', header=None, usecols=[0, 1],
                             skiprows=len(header), dtype=np.float64, chunksize=1_000_000,
                             comment='#')
        pending = None          # one chunk behind, so the file's last row can be dropped
        for chunk in reader:
            if pending is not None:
                take(pending)
            pending = chunk
        if pending is not None:
            take(pending if complete else pending.iloc[:-1])
    except pd.errors.EmptyDataError:
        pass
    if nRows == 0:
        raise ValueError("The file contains a header but no trajectory data "
                         "(the simulation's trajectory was never written to disk).")
    xy = np.vstack(kept)
    if not np.array_equal(xy[-1], last):
        xy = np.vstack([xy, last])
    return header, xy, nRows


def _endsWithNewline(filename):
    "Does the file end with a newline (or is it empty)?"
    with open(filename, 'rb') as f:
        f.seek(0, os.SEEK_END)
        if f.tell() == 0:
            return True
        f.seek(-1, os.SEEK_END)
        return f.read(1) == b'\n'


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


def _plotBounds(trajectories, lightsOnDic, boundaryRadius=0.0):
    """Axis limits enclosing every trajectory and every source, plus a margin
       (at least 1.5, or 5% of the larger span for trajectories that roam far).

       boundaryRadius, when given, also encloses the no-input ring around the
       main target: a run that never leaves the lit region would otherwise put
       the ring outside the axes, where it cannot be seen."""
    xs = [t[:,0] for t in trajectories] + [np.array([s[0] for s in lightsOnDic.values()] or [0])]
    ys = [t[:,1] for t in trajectories] + [np.array([s[1] for s in lightsOnDic.values()] or [0])]
    if boundaryRadius:
        target = _mainTarget(lightsOnDic)
        if target is not None:
            xs.append(np.array([target[0] - boundaryRadius, target[0] + boundaryRadius]))
            ys.append(np.array([target[1] - boundaryRadius, target[1] + boundaryRadius]))
    xmin = min(x.min() for x in xs); xmax = max(x.max() for x in xs)
    ymin = min(y.min() for y in ys); ymax = max(y.max() for y in ys)
    margin = max(1.5, 0.05 * max(xmax - xmin, ymax - ymin))
    return xmin - margin, xmax + margin, ymin - margin, ymax + margin


def fieldPanels(trajDataFilenames, headers, fieldTime='end'):
    """What each panel's background shows, [(moment, background)]: one panel,
    or two for fieldTime 'both' (start, end).  background is ('field',
    (quality, grid)), the field the first file with a snapshot records at
    that moment (readFieldSnapshots); ('light', None), the light schematic,
    when no file has a snapshot and none has field laws; ('none', None) when
    no file has a snapshot and some have field laws.  Warnings on stderr:
    each file with no snapshot; a missing moment (its other is shown);
    snapshots that differ between files; qualities not shaded."""
    moments = ('start', 'end') if fieldTime == 'both' else (fieldTime,)
    snapshots = [readFieldSnapshots(f, h) for f, h in zip(trajDataFilenames, headers)]
    recorded = [i for i, snapshot in enumerate(snapshots) if snapshot]
    for filename, header, snapshot in zip(trajDataFilenames, headers, snapshots):
        if snapshot:
            continue
        if _hasFieldLaws(header):
            _warn("%s: field laws but no recorded field: %s" % (
                filename, "not shaded" if not recorded else "the chart shows another file's"))
        else:
            _warn("%s: no recorded field: the shading is a schematic of the light, "
                  "1 / (1 + d^2), not a recorded field" % filename)
    if not recorded:
        anyLaws = any(_hasFieldLaws(header) for header in headers)
        return [(None, ('none' if anyLaws else 'light', None))]
    first = recorded[0]
    panels = []
    for moment in moments:
        shown = moment if moment in snapshots[first] else next(iter(snapshots[first]))
        if shown != moment:
            _warn("%s: no field at the %s (a run not closed?): showing the %s"
                  % (trajDataFilenames[first], moment, shown))
        snapshot = snapshots[first][shown]
        for i in recorded[1:]:
            other = snapshots[i].get(shown)
            if other is not None and not _sameSnapshot(snapshot, other):
                _warn("%s: its field at the %s differs from %s's, which the chart shows"
                      % (trajDataFilenames[i], shown, trajDataFilenames[first]))
        quality = sorted(snapshot)[0]
        if len(snapshot) > 1:
            _warn("%s: fields of %s recorded; the chart shades %s"
                  % (trajDataFilenames[first], ', '.join(sorted(snapshot)), quality))
        panels.append((shown, ('field', (quality, snapshot[quality]))))
    return panels


def readFieldSnapshots(trajDataFilename, dataFileHeader=None):
    """The fields a .traj file records (RobotTrajectoryWriter.writeFieldSnapshots),
    {moment: {quality: grid}}, moment 'start' or 'end'; grid a dict of x0, y0,
    spacing, n and values, an n x n array whose row j is at y0 + j spacing.
    The start comes from the header, the end from the file's last lines, read
    back from its end; a file closed before the run ended has no end.  {}
    for a file with no field."""
    if dataFileHeader is None:
        dataFileHeader = readDataFileHeader(trajDataFilename)
    snapshots = {}
    start = _parseFieldSnapshots(dataFileHeader).get('start')
    if start:
        snapshots['start'] = start
    # The end snapshot is about as long as the start one
    startBytes = sum(len(line) for line in dataFileHeader
                     if line.startswith('#\t') or line.startswith('# Field snapshot'))
    with open(trajDataFilename, 'rb') as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        tailSize = min(size, 2 * startBytes + 65536)
        f.seek(size - tailSize)
        lines = f.read().decode('ascii', 'replace').split('\n')
    if tailSize < size:
        lines = lines[1:]           # cut in the middle
    end = _parseFieldSnapshots(lines).get('end')
    if end:
        snapshots['end'] = end
    return snapshots


def _parseFieldSnapshots(lines):
    "The complete snapshot blocks in lines, {moment: {quality: grid}} (readFieldSnapshots)"
    found = {}
    pattern = re.compile(r'# Field snapshot\t(\S+)\t(start|end)\tx0\t(\S+)\ty0\t(\S+)'
                         r'\tspacing\t(\S+)\tn\t(\d+)\s*$')
    i = 0
    while i < len(lines):
        m = pattern.match(lines[i])
        i += 1
        if not m:
            continue
        quality, moment = m.group(1), m.group(2)
        x0, y0, spacing, n = float(m.group(3)), float(m.group(4)), float(m.group(5)), int(m.group(6))
        rows = lines[i:i + n]
        try:
            values = np.array([[float(v) for v in row.rstrip('\n').split('\t')[1:]]
                               for row in rows], dtype=float)
        except ValueError:
            continue
        if values.shape != (n, n) or not all(row.startswith('#\t') for row in rows):
            continue
        i += n
        found.setdefault(moment, {})[quality] = {'x0': x0, 'y0': y0, 'spacing': spacing,
                                                 'n': n, 'values': values}
    return found


def _sameSnapshot(a, b):
    "Do two snapshots ({quality: grid}) record the same field, to their 6 digits?"
    if sorted(a) != sorted(b):
        return False
    for quality in a:
        ga, gb = a[quality], b[quality]
        if (ga['n'], ga['x0'], ga['y0'], ga['spacing']) != (gb['n'], gb['x0'], gb['y0'],
                                                            gb['spacing']):
            return False
        if not np.allclose(ga['values'], gb['values'], rtol=1e-5, atol=0, equal_nan=True):
            return False
    return True


def _hasFieldLaws(dataFileHeader):
    "Does the header give its sources' field laws (\"# Field\" lines)?"
    return any(re.match(r'#\s*Field\t', line) for line in dataFileHeader)


def _warn(message):
    print("Warning: " + message, file=sys.stderr)


def _momentTitle(moment):
    return "" if moment is None else "\nfield at the %s" % moment


def _drawBackground(ax, background, lightsOnDic, bounds, dark):
    "A panel's background (fieldPanels): the recorded field, the light schematic, or none"
    kind, field = background
    if kind == 'field':
        _drawFieldShading(ax, *field)
    elif kind == 'light':
        _drawIrradianceBackground(ax, lightsOnDic, bounds, dark)


def _drawFieldShading(ax, quality, grid):
    """The recorded field as the background: grey on a log scale, from its
    peak (white) down to FIELD_SHADING_FLOOR of it and below (the darkest
    grey, which also fills the axes beyond the grid, where the field is
    below that), with contour lines at FIELD_CONTOURS of the peak, labelled,
    in the quality's colour."""
    x0, y0, spacing, n = grid['x0'], grid['y0'], grid['spacing'], grid['n']
    values = np.abs(grid['values'])
    finite = values[np.isfinite(values)]
    peak = finite.max() if finite.size else 0.0
    if not peak > 0:
        return
    values = np.where(np.isfinite(values), values, peak)
    floor = peak * FIELD_SHADING_FLOOR
    level = np.clip(np.log10(np.maximum(values, floor) / floor) / np.log10(peak / floor), 0, 1)
    dimmest = 0.45                  # the light schematic's range, [0.45, 1]
    ax.set_facecolor((dimmest,) * 3)
    half = spacing / 2
    far = (n - 1) * spacing
    ax.imshow(dimmest + (1 - dimmest) * level, extent=[x0 - half, x0 + far + half,
                                                       y0 - half, y0 + far + half],
              origin='lower', cmap='gray', vmin=0, vmax=1, aspect='equal', zorder=0,
              interpolation='bilinear')
    coordinates = np.arange(n) * spacing
    X, Y = np.meshgrid(x0 + coordinates, y0 + coordinates)
    contours = ax.contour(X, Y, values, levels=sorted(peak * f for f in FIELD_CONTOURS),
                          colors=_QUALITY_COLORS.get(quality, 'black'), linewidths=0.7,
                          zorder=1)
    ax.clabel(contours, fmt=lambda value: '%g%%' % round(100 * value / peak, 6), fontsize=6)


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


def noInputRadius(dataFileHeader, lightsOnDic, trajDataFilename=None):
    """The distance beyond which the eyes see nothing of the main source,
    sqrt(|intensity| / I0) for the least threshold I0 of the light eyes
    (leftEye, rightEye; else of any eye), on the eyes' axis.  I0 comes from
    the header's eye lines or else from the run's JSON beside the file (same
    name, eye_threshold in its settings).  0 -- no ring -- for eyes with threshold 0, which see any
    source at any distance, or when neither records the threshold."""
    target = _mainTarget(lightsOnDic)
    if target is None:
        return 0.0
    eyes = readEyesFromHeader(dataFileHeader)
    thresholds = ([eyes[name][0] for name in ('leftEye', 'rightEye') if name in eyes]
                  or [eye[0] for eye in eyes.values()])
    if not thresholds and trajDataFilename is not None:
        thresholds = _eyeThresholdsFromJson(trajDataFilename)
    if not thresholds or min(thresholds) <= 0:
        return 0.0
    return sqrt(abs(target[2]) / min(thresholds))


def readEyesFromHeader(dataFileHeader):
    "The header's eye lines, {name: (threshold, saturation, response)}; {} if none."
    eyes = {}
    for line in dataFileHeader:
        m = re.match(r'#\s*Eye\t(\S+)\tthreshold\t(\S+)\tsaturation\t(\S+)\tresponse\t(\S+)',
                     line)
        if m:
            eyes[m.group(1)] = (float(m.group(2)), float(m.group(3)), m.group(4))
    return eyes


def _eyeThresholdsFromJson(trajDataFilename):
    "The eye threshold the run's JSON (same name as the .traj) records, as a list; [] if none."
    import json
    try:
        with open(os.path.splitext(trajDataFilename)[0] + '.json') as f:
            threshold = json.load(f).get('settings', {}).get('eye_threshold')
    except (OSError, ValueError):
        return []
    return [] if threshold is None else [float(threshold)]


def _drawNoInputBoundary(ax, lightsOnDic, radius=0.0):
    """Ring each source at the radius beyond which it gives no sensor input.

    Everything outside the ring is the no-input region: zero irradiance at any
    heading, so the vehicle is driven by nothing but its own noise.
    """
    if not radius:
        return
    target = _mainTarget(lightsOnDic)
    if target is None:
        return
    ax.add_artist(Circle((target[0], target[1]), radius, fill=False,
                         edgecolor='#5c5b54', linestyle=(0, (6, 4)), linewidth=1.2,
                         alpha=0.9, zorder=2.5))
    ax.annotate('no input beyond r=%g' % radius,
                xy=(target[0], target[1] + radius), xytext=(0, 4),
                textcoords='offset points', ha='center', va='bottom',
                fontsize=7, color='#5c5b54', zorder=2.5)


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

def readStepsRecorded(trajDataFilename):
    '''The number of simulator steps a .traj file recorded, from its last
    line, "# Steps recorded<TAB>S" (written on closing); None for a file
    without that line, as for runs killed before the file was closed.'''
    with open(trajDataFilename, 'rb') as f:
        f.seek(0, os.SEEK_END)
        f.seek(max(0, f.tell() - 256))
        tail = f.read().decode('ascii', 'replace')
    m = re.search(r'#\s*Steps recorded\s+(\d+)\s*$', tail)
    return int(m.group(1)) if m else None


def ticksFromRows(dataFileHeader, nRows, stepsRecorded=None):
    '''Homeostat ticks covered by nRows data rows of a .traj file.

    A row is one simulator step, or one every N steps when the file was
    decimated, and a tick is two steps (stepsPerTick).  A file's header says
    both: "# Sampled every N simulator steps, M steps per homeostat tick".  A
    header with "# Sampled every N ticks" means N steps, at 2 steps per tick;
    a header with no sampling line is undecimated, at 2 steps per tick.

    Exact with stepsRecorded, the count a closed file ends with (see
    readStepsRecorded), and for an undecimated file.  Otherwise a decimated
    file ends on the final pose, written wherever the run stopped, so its
    rows give the run's length only to within a sampling interval: the
    result may exceed the true count by less than N/M ticks (e.g. 501 for
    500 at N = 3, M = 2).'''
    every, perTick = 1, 2
    for line in dataFileHeader:
        m = re.match(r'#\s*Sampled every (\d+) simulator steps, (\d+) steps per homeostat tick',
                     line)
        if m:
            every, perTick = int(m.group(1)), int(m.group(2))
            break
        m = re.match(r'#\s*Sampled every (\d+) ticks', line)
        if m:
            every = int(m.group(1))
            break
    if stepsRecorded is not None:
        return int(round(stepsRecorded / perTick))
    return int(round(nRows * every / perTick))


def _hasDarknessSource(lightsOnDic):
    "A source of negative intensity (--dark runs) is a darkness source."
    return any(light[2] < 0 for light in lightsOnDic.values())


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
