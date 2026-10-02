#!/usr/bin/env python3

'''
Strip charts of the per-tick state logged by HomeostatStateLogger.

Self-standing script, the state-log counterpart of TrajectoryGrapher: that one
answers "where did the vehicle go", this one "what were its insides doing while
it went there".

Usage:
    python -m Helpers.StripchartGrapher run.statelog --value critDev
    python -m Helpers.StripchartGrapher run.statelog --unit "Left Motor" \
            --value critDev --value stress --value sigma
    python -m Helpers.StripchartGrapher run.statelog --cross -o weights.png
    python -m Helpers.StripchartGrapher a.statelog b.statelog --cross --overlay
    python -m Helpers.StripchartGrapher run.statelog --cross --from 0 --to 500000

One strip per series by default, stacked on a shared time axis; --overlay puts
every series of a file in one strip instead.  Several files are drawn as
separate strips (or, with --overlay, one strip per file).

SMOOTHING, AND WHY YOU USUALLY WANT IT.  The log samples every --log-interval
ticks, which can be far coarser than the process being logged.  A continuous
(OU) connection weight evolves by sigma*sqrt(dt) per tick: at the stock
sigma_crit = 0.1 and an interval of 200 ticks, a stressed weight moves
0.1*sqrt(200) = 1.41 between consecutive samples -- more than the whole [-1, 1]
range it is clipped to.  Samples inside such a burst are therefore independent
draws, and the raw trace is aliased noise that straddles zero no matter what the
weight is really doing: in the 2026-10-01 6M array the raw cross-weight traces
cross zero 123,717 times, while the same data smoothed over the OU's own
correlation time (tau_a/theta = 100,000 ticks) crosses 292 times, with 34 of the
40 traces never crossing at all.  --smooth-ticks takes that timescale directly;
--smooth takes it in samples.  The raw trace stays visible underneath so the
smoothing never hides what it was computed from.

@author: stefano
'''
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.colors import ListedColormap
from matplotlib.ticker import FuncFormatter
import os
import sys
import numpy as np

# Categorical hues, in fixed order.  Checked for colour-vision separation: the
# first two differ by dE 24.7 for protanopia, 33.6 for normal vision.
SERIES_COLORS = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100',
                 '#e87ba4', '#008300', '#4a3aa7', '#e34948']
INK, INK2, GRID, SURFACE, PALE = '#1a1a19', '#5c5b54', '#d8d7d0', '#fcfcfb', '#f2f1ea'
ACQ_COLOR = '#008300'

# Series whose sign is meaningful get a 0 line and a symmetric y range: for a
# connection weight the sign IS the polarity, and an asymmetric axis hides that.
SIGNED_PREFIXES = ('w_',)
SIGNED_SUFFIXES = ('_critDev', '_output', '_velocity', '_torque')


def readStatelog(path):
    """Read one .statelog.  Returns (meta, columns, data).

    meta    -- dict of the '# key<TAB>value' header lines, values left as text
    columns -- list of column names, in file order
    data    -- float64 array, one row per sample, one column per name
    """
    meta, columns, rows = {}, None, []
    with open(path) as f:
        for line in f:
            if line.startswith('#'):
                parts = line[1:].strip().split('\t')
                if len(parts) == 2:
                    meta[parts[0]] = parts[1]
                continue
            parts = line.rstrip('\n').split('\t')
            if columns is None:
                columns = parts
                continue
            rows.append(parts)
    if columns is None:
        raise ValueError('%s has no column header; is it a .statelog?' % path)
    return meta, columns, np.array(rows, dtype=np.float64)


def unitsIn(columns):
    "Unit names the log carries, in the order the homeostat lists them."
    seen = []
    for c in columns:
        if c.endswith('_critDev'):
            name = c[:-len('_critDev')]
            if name not in seen:
                seen.append(name)
    return seen


def resolveSeries(columns, units, values, crossOnly, explicit):
    """Work out which columns to draw, and what to call them.

    units x values is a cross product: --unit "Left Motor" --value critDev
    --value stress gives that unit's two columns.  With no --unit, every unit
    that has the requested value is drawn.  --column names a column outright,
    for the ones that belong to no single unit (distance, left_sensor, ...).
    """
    chosen = []

    if crossOnly:
        # The cross-sensor connections: each sensor driving the OPPOSITE motor.
        for c in columns:
            if not c.startswith('w_'):
                continue
            target, _, source = c[2:].partition('<-')
            if 'Sensor' in source and 'Motor' in target:
                side = lambda s: 'Left' if s.startswith('Left') else 'Right'
                if side(source) != side(target):
                    chosen.append((c, c[2:]))

    for name in explicit:
        if name not in columns:
            raise SystemExit("no column %r in the log; --list shows them all" % name)
        chosen.append((name, name))

    known = unitsIn(columns)
    for value in values:
        wanted = units or known
        for u in wanted:
            # sigma and the firing count are prefixed, the rest suffixed
            for cand in ('%s_%s' % (u, value), '%s_%s' % (value, u),
                         'unisel_%s_%s' % (value, u)):
                if cand in columns:
                    chosen.append((cand, '%s %s' % (u, value)))
                    break
            else:
                if units:
                    raise SystemExit(
                        "unit %r has no value %r in this log; --list shows the columns" % (u, value))

    if not chosen:
        raise SystemExit('nothing to draw: give --value, --column or --cross (--list shows the columns)')
    # de-duplicate, keeping order
    out, seen = [], set()
    for col, label in chosen:
        if col not in seen:
            seen.add(col); out.append((col, label))
    return out


def abbreviate(label):
    """Shorten unit names to initials for axis labels: 'Left Motor' -> 'LM'.

    Full names are kept in the legend, where there is room; the y label sits in
    a narrow margin and a long name is simply clipped off the figure.
    """
    out = label
    for full, short in (('Left Motor', 'LM'), ('Right Motor', 'RM'),
                        ('Left Sensor', 'LS'), ('Right Sensor', 'RS')):
        out = out.replace(full, short)
    return out


def isSigned(column):
    return (column.startswith(SIGNED_PREFIXES)
            or column.endswith(SIGNED_SUFFIXES))


def smoothWindow(args, meta):
    "Smoothing window in SAMPLES, from --smooth or --smooth-ticks."
    if args.smooth:
        return max(1, args.smooth)
    if args.smooth_ticks:
        interval = float(meta.get('log_interval', 1)) or 1.0
        return max(1, int(round(args.smooth_ticks / interval)))
    return 1


def _running(v, w):
    if w <= 1:
        return v
    return np.convolve(v, np.ones(w) / w, mode='valid')


def _segment(data, columns, fromTick, toTick):
    tick = data[:, columns.index('tick')]
    keep = np.ones(len(tick), dtype=bool)
    if fromTick is not None:
        keep &= tick >= fromTick
    if toTick is not None:
        keep &= tick <= toTick
    if not keep.any():
        raise SystemExit('the --from/--to window selects no samples '
                         '(log covers ticks %g to %g)' % (tick[0], tick[-1]))
    return data[keep]


def _formatTicks(v):
    return '%.1fM' % (v / 1e6) if v >= 1e6 else ('%.0fk' % (v / 1e3) if v >= 1e3 else '%g' % v)


def _drawStrip(ax, tick, series, window, signed, showRaw, ylim=None):
    """One strip: every series in `series` as (values, label, colour)."""
    if signed:
        ax.axhline(0, color=INK, lw=1.0, zorder=5)
    for values, label, color in series:
        if showRaw and window > 1:
            ax.plot(tick, values, color=color, lw=0.3, alpha=0.18,
                    zorder=2, rasterized=True)
        sm = _running(values, window)
        t = tick[window - 1:] if window > 1 else tick
        ax.plot(t, sm, color=color, lw=1.5 if window > 1 else 0.6,
                label=label, zorder=6, rasterized=(window <= 1))
        if signed and window > 1:
            cross = np.where(np.diff(np.sign(sm + 1e-30)) != 0)[0]
            if len(cross):
                ax.plot(t[cross], np.zeros(len(cross)), 'o', ms=4.5,
                        mfc=SURFACE, mec=color, mew=1.4, zorder=7)
    ax.set_xlim(tick[0], tick[-1])
    if ylim is not None:
        ax.set_ylim(*ylim)
    for sp in ('top', 'right'):
        ax.spines[sp].set_visible(False)
    for sp in ('left', 'bottom'):
        ax.spines[sp].set_color(GRID)
    ax.tick_params(labelsize=7, length=2, colors=INK2)


def _drawRibbon(ax, tick, values, window, color, label):
    "Sign of a signed series over time: a polarity change is a colour change."
    sm = _running(values, window)
    t = tick[window - 1:] if window > 1 else tick
    ax.imshow((sm > 0).astype(float)[None, :], aspect='auto', interpolation='nearest',
              cmap=ListedColormap([PALE, color]), vmin=0, vmax=1,
              extent=[t[0], t[-1], 0, 1], rasterized=True)
    ax.set_xlim(tick[0], tick[-1]); ax.set_ylim(0, 1)
    ax.set_yticks([0.5]); ax.set_yticklabels([abbreviate(label)], fontsize=6, color=INK2)
    for sp in ax.spines.values():
        sp.set_color(GRID)
    ax.tick_params(length=0, colors=INK2)


def graphStripcharts(paths, units=(), values=(), columns=(), crossOnly=False,
                     fromTick=None, toTick=None, window=1, smoothTicks=None,
                     overlay=False, ribbons=False, showRaw=True,
                     symmetric=False, output_path=None, title=None):
    """Draw strip charts for every (file, series) pair.  See main() for the CLI."""
    loaded = []
    for p in paths:
        meta, cols, data = readStatelog(p)
        data = _segment(data, cols, fromTick, toTick)
        w = window
        if smoothTicks:
            interval = float(meta.get('log_interval', 1)) or 1.0
            w = max(1, int(round(smoothTicks / interval)))
        picked = resolveSeries(cols, list(units), list(values), crossOnly, list(columns))
        loaded.append((p, meta, cols, data, picked, w))

    # one strip per series, or one per file when overlaying
    strips = []
    for p, meta, cols, data, picked, w in loaded:
        tick = data[:, cols.index('tick')]
        if overlay:
            series = [(data[:, cols.index(c)], lab, SERIES_COLORS[i % len(SERIES_COLORS)])
                      for i, (c, lab) in enumerate(picked)]
            strips.append((p, tick, series, w, any(isSigned(c) for c, _ in picked), picked))
        else:
            for i, (c, lab) in enumerate(picked):
                strips.append((p, tick, [(data[:, cols.index(c)], lab,
                                          SERIES_COLORS[i % len(SERIES_COLORS)])],
                               w, isSigned(c), [(c, lab)]))

    nRibbon = sum(1 for s in strips if ribbons and s[4] for _ in s[2])
    rowsPer = [1 + (len(s[2]) if ribbons and s[4] else 0) for s in strips]
    heights = []
    for s, extra in zip(strips, rowsPer):
        heights.append(6)
        heights.extend([1] * (extra - 1))
    nSeries = len({lab for s_ in strips for _, lab, _ in s_[2]})
    titleIn, legendIn, bottomIn = 0.52, (0.30 if nSeries > 1 else 0.0), 0.55
    plotIn = 0.30 * sum(heights)
    figH = plotIn + titleIn + legendIn + bottomIn
    fig = plt.figure(figsize=(12, figH))
    fig.patch.set_facecolor(SURFACE)
    gs = GridSpec(len(heights), 1, height_ratios=heights, hspace=0.35,
                  left=0.145, right=0.985,
                  top=1 - (titleIn + legendIn) / figH, bottom=bottomIn / figH)

    ylim = None
    if symmetric:
        m = max(np.abs(_running(v, s[3])).max() for s in strips for v, _, _ in s[2])
        ylim = (-1.12 * m, 1.12 * m)

    row = 0
    axes = []
    for s in strips:
        p, tick, series, w, signed, picked = s
        ax = fig.add_subplot(gs[row]); row += 1
        _drawStrip(ax, tick, series, w, signed, showRaw, ylim if signed else None)
        label = os.path.basename(p)
        ax.set_ylabel('\n'.join(abbreviate(lab) for _, lab, _ in series)
                      if len(series) <= 2 else '%d series' % len(series),
                      rotation=0, ha='right', va='center', fontsize=7.5,
                      color=INK, labelpad=8)
        if len(paths) > 1:
            ax.text(0.002, 1.04, label, transform=ax.transAxes, fontsize=6.5,
                    color=INK2, va='bottom')
        axes.append(ax)
        if ribbons and signed:
            for values, lab, color in series:
                rax = fig.add_subplot(gs[row]); row += 1
                _drawRibbon(rax, tick, values, w, color, lab)
                axes.append(rax)

    # One legend for the figure, below the title: an in-axes legend sits on top
    # of the data, and with ribbons the strips are too short to spare the room.
    handles, labels = [], []
    for s_ in strips:
        for _, lab, color in s_[2]:
            if lab not in labels:
                labels.append(lab); handles.append(plt.Line2D([], [], color=color, lw=2))
    if len(handles) > 1:
        fig.legend(handles, labels, loc='upper center',
                   bbox_to_anchor=(0.5, 1 - titleIn / figH),
                   ncol=min(5, len(handles)), frameon=False, fontsize=8, labelcolor=INK)

    for ax in axes[:-1]:
        ax.set_xticklabels([])
    axes[-1].tick_params(labelsize=7, labelbottom=True)
    # Format ticks as 1.5M / 300k rather than letting matplotlib hang a '1e6'
    # offset off the corner, where a tight figure clips it away.
    axes[-1].xaxis.set_major_formatter(FuncFormatter(lambda v, _: _formatTicks(v)))
    axes[-1].set_xlabel('tick', fontsize=8, color=INK2)

    span = '%s to %s' % (_formatTicks(strips[0][1][0]), _formatTicks(strips[0][1][-1]))
    sub = 'samples %s' % span
    if strips[0][3] > 1:
        interval = float(loaded[0][1].get('log_interval', 1))
        sub += ('   ·   bold = running mean over %d samples (%s ticks); faint = raw'
                % (strips[0][3], _formatTicks(strips[0][3] * interval)))
    fig.suptitle((title or 'Homeostat state strip chart') + '\n' + sub,
                 fontsize=10, color=INK, y=1 - 0.04 / figH, va='top')

    if output_path:
        fig.savefig(output_path, dpi=150, facecolor=fig.get_facecolor())
        print('written: %s' % output_path)
        plt.close(fig)
    else:
        if fig.canvas.manager is not None:
            fig.canvas.manager.set_window_title(title or 'Homeostat state strip chart')
        plt.show()


def main(argv):
    import argparse
    parser = argparse.ArgumentParser(
        description='Strip charts of logged homeostat state (.statelog files).',
        epilog='With no --value/--column/--cross, --list is implied.')
    parser.add_argument('statelog_files', nargs='+', metavar='statelog',
                        help='Path(s) to .statelog file(s)')
    parser.add_argument('--unit', action='append', default=[], metavar='NAME',
                        help='Unit to draw, repeatable (default: every unit that '
                             'has the requested value). Quote names with spaces.')
    parser.add_argument('--value', action='append', default=[], metavar='NAME',
                        help='Logged value to draw, repeatable: critDev, output, '
                             'velocity, torque, stress, sigma, fires')
    parser.add_argument('--column', action='append', default=[], metavar='NAME',
                        help='A column by its exact name, repeatable; for columns '
                             'belonging to no single unit (distance, left_sensor, ...)')
    parser.add_argument('--cross', action='store_true',
                        help="Draw the cross-sensor connection weights (each sensor "
                             "to the opposite motor)")
    parser.add_argument('--list', action='store_true',
                        help='List the columns and units of the first file, then exit')
    parser.add_argument('--from', dest='from_tick', type=float, default=None,
                        metavar='TICK', help='First tick to draw (default: start of log)')
    parser.add_argument('--to', dest='to_tick', type=float, default=None,
                        metavar='TICK', help='Last tick to draw (default: end of log)')
    parser.add_argument('--smooth', type=int, default=0, metavar='N',
                        help='Running mean over N samples')
    parser.add_argument('--smooth-ticks', type=float, default=None, metavar='T',
                        help='Running mean over T ticks (converted using the '
                             "log's own log_interval). For an OU weight, the "
                             'honest window is tau_a/theta.')
    parser.add_argument('--no-raw', action='store_true',
                        help='Omit the faint raw trace under a smoothed line')
    parser.add_argument('--ribbons', action='store_true',
                        help='Add a sign ribbon under each signed series, so a '
                             'polarity change reads as a colour change')
    parser.add_argument('--overlay', action='store_true',
                        help='Draw all of a file\'s series in one strip')
    parser.add_argument('--symmetric', action='store_true',
                        help='Force a symmetric y range about 0 on signed series')
    parser.add_argument('--title', default=None)
    parser.add_argument('--output', '-o', default=None,
                        help='Save to file (PNG, PDF, ...) instead of displaying')
    args = parser.parse_args(argv[1:])

    if args.list or not (args.value or args.column or args.cross):
        meta, cols, _ = readStatelog(args.statelog_files[0])
        print('units: %s' % ', '.join(unitsIn(cols)))
        print('log_interval: %s ticks' % meta.get('log_interval', '?'))
        print('columns:')
        for c in cols:
            print('   %s' % c)
        return

    graphStripcharts(args.statelog_files, units=args.unit, values=args.value,
                     columns=args.column, crossOnly=args.cross,
                     fromTick=args.from_tick, toTick=args.to_tick,
                     window=args.smooth, smoothTicks=args.smooth_ticks,
                     overlay=args.overlay, ribbons=args.ribbons,
                     showRaw=not args.no_raw, symmetric=args.symmetric,
                     output_path=args.output, title=args.title)


if __name__ == "__main__":
    main(sys.argv)
