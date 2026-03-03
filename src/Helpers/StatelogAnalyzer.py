#!/usr/bin/env python3
'''
Post-mortem analysis tools for Homeostat phototaxis state logs.

Reads .statelog files produced by HomeostatStateLogger and generates
diagnostic plots and text summaries to understand overshoot behaviour:
why the robot approaches the light then drifts past it.

Usage:
    python -m Helpers.StatelogAnalyzer file.statelog
    python -m Helpers.StatelogAnalyzer file.statelog --output ./analysis/
    python -m Helpers.StatelogAnalyzer file.statelog --summary
    python -m Helpers.StatelogAnalyzer file.statelog -p overview anatomy
    python -m Helpers.StatelogAnalyzer file.statelog --time-range 40000 60000

@author: stefano
'''

import os
import re
import sys
import argparse
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# A. Parser
# ---------------------------------------------------------------------------

@dataclass
class StatelogData:
    '''Parsed contents of a .statelog file.'''
    metadata: Dict                        # header key-value pairs
    df: pd.DataFrame                      # one row per logged tick
    unit_names: List[str] = field(default_factory=list)
    conn_keys: List[str] = field(default_factory=list)   # all w_X<-Y columns
    cross_conns: List[str] = field(default_factory=list)  # A != B
    self_conns: List[str] = field(default_factory=list)   # A == B
    sigma_cols: List[str] = field(default_factory=list)   # sigma_X columns
    stress_cols: List[str] = field(default_factory=list)  # X_stress columns


_KNOWN_UNIT_PARAMS = {
    'type', 'mass', 'viscosity', 'maxDeviation', 'dt_fast',
    'tau_a', 'theta', 'sigma_base', 'sigma_crit', 'stress_exponent', 'ou_dt',
}


def _parse_unit_key(key: str):
    '''Parse "unit_{name}_{param}" where name may contain spaces/underscores.

    Returns (unit_name, param) or (None, None) if key doesn't match.
    '''
    if not key.startswith('unit_'):
        return None, None
    rest = key[5:]  # strip "unit_"
    # Try matching longest known param suffixes first
    for param in sorted(_KNOWN_UNIT_PARAMS, key=len, reverse=True):
        if rest.endswith('_' + param):
            uname = rest[:-(len(param) + 1)]
            if uname:
                return uname, param
    return None, None


def parse_statelog(filepath: str) -> StatelogData:
    '''Parse a .statelog file into a StatelogData object.'''

    metadata = {}
    unit_meta = {}   # nested: unit_meta[unit_name][param] = value
    header_lines = 0

    with open(filepath, 'r') as f:
        for line in f:
            if not line.startswith('#'):
                break
            header_lines += 1
            line = line.lstrip('#').strip()
            if '\t' not in line:
                continue
            key, val = line.split('\t', 1)
            key = key.strip()
            val = val.strip()

            # Parse unit-specific metadata: "unit_{name}_{param}"
            # Unit names can contain spaces (e.g. "Left Motor") and some
            # param names contain underscores (e.g. "dt_fast", "sigma_base").
            # Match the longest known suffix first.
            uname, param = _parse_unit_key(key)
            if uname is not None:
                unit_meta.setdefault(uname, {})[param] = _auto_cast(val)
            else:
                metadata[key] = _auto_cast(val)

    metadata['units'] = unit_meta

    # Read the TSV data (comment='#' skips the header)
    df = pd.read_csv(filepath, sep='\t', comment='#')

    # Identify column groups
    unit_names = list(unit_meta.keys())
    conn_keys = [c for c in df.columns if c.startswith('w_')]
    sigma_cols = [c for c in df.columns if c.startswith('sigma_')]
    stress_cols = [c for c in df.columns if c.endswith('_stress')]

    cross_conns = []
    self_conns = []
    conn_pattern = re.compile(r'^w_(.+)<-(.+)$')
    for c in conn_keys:
        m = conn_pattern.match(c)
        if m:
            if m.group(1) != m.group(2):
                cross_conns.append(c)
            else:
                self_conns.append(c)

    return StatelogData(
        metadata=metadata,
        df=df,
        unit_names=unit_names,
        conn_keys=conn_keys,
        cross_conns=cross_conns,
        self_conns=self_conns,
        sigma_cols=sigma_cols,
        stress_cols=stress_cols,
    )


def _auto_cast(val: str):
    '''Try to cast a metadata value to int, float, or bool; else keep str.'''
    if val.lower() in ('true', 'false'):
        return val.lower() == 'true'
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        pass
    return val


# ---------------------------------------------------------------------------
# B. Derived quantities
# ---------------------------------------------------------------------------

def enrich(data: StatelogData, smooth: int = 500):
    '''Add derived columns to the DataFrame in-place.

    Parameters:
        data:   parsed StatelogData
        smooth: rolling window size for smoothed columns
    '''
    df = data.df
    meta = data.metadata

    # Weight changes per tick
    for col in data.conn_keys:
        df['d' + col] = df[col].diff()

    # Distance change per tick
    if 'distance' in df.columns:
        df['dd'] = df['distance'].diff()

    # OU drift decomposition for each cross-connection
    units_meta = meta.get('units', {})
    for col in data.cross_conns:
        m = re.match(r'^w_(.+)<-', col)
        if not m:
            continue
        uname = m.group(1)
        umeta = units_meta.get(uname, {})
        theta = umeta.get('theta', None)
        tau_a = umeta.get('tau_a', None)
        dt = umeta.get('dt_fast', 1.0)
        if theta is not None and tau_a is not None and tau_a > 0:
            drift_col = 'drift_' + col
            resid_col = 'diffusion_' + col
            df[drift_col] = -(theta / tau_a) * df[col] * dt
            df[resid_col] = df['d' + col] - df[drift_col]

    # Mean stress across all units
    if data.stress_cols:
        df['mean_stress'] = df[data.stress_cols].mean(axis=1)

    # Smoothed distance
    if 'distance' in df.columns and smooth > 1:
        df['distance_smooth'] = df['distance'].rolling(
            smooth, min_periods=1, center=True).mean()


# ---------------------------------------------------------------------------
# C. Diagnostic plots
# ---------------------------------------------------------------------------

def _setup_matplotlib():
    '''Configure matplotlib for non-interactive PDF output.'''
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        'figure.dpi': 150,
        'font.size': 9,
        'axes.titlesize': 10,
        'axes.labelsize': 9,
        'legend.fontsize': 8,
    })
    return plt


def plot_overview(data: StatelogData, smooth: int = 500,
                  time_range: Optional[Tuple[int, int]] = None) -> 'Figure':
    '''3 stacked panels: distance, cross-connection weights, stress.'''
    plt = _setup_matplotlib()
    df = _slice(data.df, time_range)
    tick = df['tick']

    fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)

    # Panel 1: Distance
    ax = axes[0]
    ax.plot(tick, df['distance'], alpha=0.3, lw=0.5, color='steelblue')
    if 'distance_smooth' in df.columns:
        ax.plot(tick, df['distance_smooth'], color='steelblue', lw=1.2,
                label='smoothed')
    min_idx = df['distance'].idxmin()
    min_tick = df.loc[min_idx, 'tick']
    min_dist = df.loc[min_idx, 'distance']
    ax.axvline(min_tick, color='green', ls='--', lw=0.8, alpha=0.7)
    ax.plot(min_tick, min_dist, 'v', color='green', ms=8,
            label='min dist %.3f @ %d' % (min_dist, min_tick))
    # Shade "good window" where distance < 1.5 * min_dist
    good_thresh = 1.5 * min_dist
    good_mask = df['distance'] <= good_thresh
    _shade_mask(ax, tick, good_mask, color='green', alpha=0.08)
    ax.set_ylabel('Distance to target')
    ax.legend(loc='upper right')
    ax.set_title('Overview')

    # Panel 2: Cross-connection weights
    ax = axes[1]
    for col in data.cross_conns:
        ax.plot(tick, df[col], lw=0.8, label=col)
    ax.axvline(min_tick, color='green', ls='--', lw=0.8, alpha=0.7)
    ax.axhline(0, color='grey', ls=':', lw=0.5)
    ax.set_ylabel('Cross-conn weight')
    ax.legend(loc='upper right', ncol=2, fontsize=7)

    # Panel 3: Stress
    ax = axes[2]
    for col in data.stress_cols:
        ax.plot(tick, df[col], lw=0.6, alpha=0.7, label=col.replace('_stress', ''))
    if 'mean_stress' in df.columns:
        ax.plot(tick, df['mean_stress'], color='black', lw=1.2, label='mean')
    ax.axvline(min_tick, color='green', ls='--', lw=0.8, alpha=0.7)
    ax.set_ylabel('Stress')
    ax.set_xlabel('Tick')
    ax.legend(loc='upper right', ncol=2, fontsize=7)

    fig.tight_layout()
    return fig


def plot_drift_vs_diffusion(data: StatelogData, smooth: int = 500,
                            time_range: Optional[Tuple[int, int]] = None) -> 'Figure':
    '''For each cross-connection: |drift| vs |diffusion residual| + rolling ratio.'''
    plt = _setup_matplotlib()
    df = _slice(data.df, time_range)
    tick = df['tick']

    n_conns = len(data.cross_conns)
    if n_conns == 0:
        return _empty_figure(plt, 'No cross-connections for drift/diffusion')

    fig, axes = plt.subplots(n_conns, 1, figsize=(12, 3.5 * n_conns), sharex=True)
    if n_conns == 1:
        axes = [axes]

    for ax, col in zip(axes, data.cross_conns):
        drift_col = 'drift_' + col
        resid_col = 'diffusion_' + col
        if drift_col not in df.columns:
            ax.set_title(col + ' (no OU params in metadata)')
            continue

        abs_drift = df[drift_col].abs()
        abs_resid = df[resid_col].abs()

        # Rolling means for readability
        roll_drift = abs_drift.rolling(smooth, min_periods=1, center=True).mean()
        roll_resid = abs_resid.rolling(smooth, min_periods=1, center=True).mean()

        ax.plot(tick, roll_drift, lw=0.9, label='|drift| (mean-reversion)')
        ax.plot(tick, roll_resid, lw=0.9, label='|diffusion| (noise)')

        # Ratio on secondary axis
        ax2 = ax.twinx()
        ratio = roll_resid / (roll_drift + 1e-12)
        ax2.plot(tick, ratio, color='red', lw=0.7, alpha=0.6, label='ratio')
        ax2.set_ylabel('|diffusion|/|drift|', color='red')
        ax2.tick_params(axis='y', colors='red')

        ax.set_ylabel('Magnitude')
        ax.set_title(col)
        ax.legend(loc='upper left', fontsize=7)

    axes[-1].set_xlabel('Tick')
    fig.suptitle('Drift vs Diffusion Decomposition', fontsize=11)
    fig.tight_layout()
    return fig


def plot_stress_vs_distance(data: StatelogData, smooth: int = 500,
                            time_range: Optional[Tuple[int, int]] = None) -> 'Figure':
    '''Dual-axis time series + hexbin scatter of distance vs stress.'''
    plt = _setup_matplotlib()
    df = _slice(data.df, time_range)
    tick = df['tick']

    if 'mean_stress' not in df.columns or 'distance' not in df.columns:
        return _empty_figure(plt, 'Missing stress or distance columns')

    fig, axes = plt.subplots(1, 2, figsize=(14, 5),
                             gridspec_kw={'width_ratios': [2, 1]})

    # Left: dual-axis time series
    ax = axes[0]
    ax.plot(tick, df['distance'], color='steelblue', lw=0.6, alpha=0.5)
    if 'distance_smooth' in df.columns:
        ax.plot(tick, df['distance_smooth'], color='steelblue', lw=1.2,
                label='distance')
    ax.set_ylabel('Distance', color='steelblue')
    ax.tick_params(axis='y', colors='steelblue')

    ax2 = ax.twinx()
    stress_smooth = df['mean_stress'].rolling(
        smooth, min_periods=1, center=True).mean()
    ax2.plot(tick, stress_smooth, color='orange', lw=1.0, label='mean stress')
    ax2.set_ylabel('Mean stress', color='orange')
    ax2.tick_params(axis='y', colors='orange')
    ax.set_xlabel('Tick')
    ax.set_title('Distance & Stress over time')

    # Right: hexbin scatter colored by time
    ax = axes[1]
    hb = ax.hexbin(df['distance'].values, df['mean_stress'].values,
                   C=tick.values, gridsize=40, cmap='viridis',
                   reduce_C_function=np.mean, mincnt=1)
    fig.colorbar(hb, ax=ax, label='Tick (mean)')
    ax.set_xlabel('Distance')
    ax.set_ylabel('Mean stress')
    ax.set_title('Stress vs Distance')

    fig.tight_layout()
    return fig


def plot_connection_anatomy(data: StatelogData, smooth: int = 500,
                            time_range: Optional[Tuple[int, int]] = None) -> 'Figure':
    '''Distance + all weight trajectories overlaid (dual axis).'''
    plt = _setup_matplotlib()
    df = _slice(data.df, time_range)
    tick = df['tick']

    fig, ax1 = plt.subplots(figsize=(12, 5))

    # Distance on primary axis
    ax1.plot(tick, df['distance'], color='steelblue', lw=0.5, alpha=0.3)
    if 'distance_smooth' in df.columns:
        ax1.plot(tick, df['distance_smooth'], color='steelblue', lw=1.2,
                 label='distance')
    min_idx = df['distance'].idxmin()
    min_tick = df.loc[min_idx, 'tick']
    min_dist = df.loc[min_idx, 'distance']
    ax1.axvline(min_tick, color='green', ls='--', lw=0.8, alpha=0.7)
    ax1.set_ylabel('Distance', color='steelblue')
    ax1.tick_params(axis='y', colors='steelblue')

    # Weights on secondary axis
    ax2 = ax1.twinx()
    for col in data.cross_conns:
        ax2.plot(tick, df[col], lw=0.8, label=col)
        # Mark zero-crossings
        vals = df[col].values
        sign_changes = np.where(np.diff(np.sign(vals)))[0]
        if len(sign_changes) > 0:
            cross_ticks = tick.iloc[sign_changes].values
            ax2.plot(cross_ticks, np.zeros(len(cross_ticks)), 'x',
                     ms=4, alpha=0.5)
    for col in data.self_conns:
        ax2.plot(tick, df[col], lw=0.6, ls='--', alpha=0.6, label=col)

    ax2.axhline(0, color='grey', ls=':', lw=0.5)
    ax2.set_ylabel('Connection weight')
    ax2.legend(loc='upper right', fontsize=7, ncol=2)
    ax1.set_xlabel('Tick')
    ax1.set_title('Connection Anatomy (solid=cross, dashed=self)')

    fig.tight_layout()
    return fig


def plot_sigma_and_weight_detail(data: StatelogData, conn: Optional[str] = None,
                                 smooth: int = 500,
                                 time_range: Optional[Tuple[int, int]] = None) -> 'Figure':
    '''4 stacked panels for one connection: sigma, stress, weight, |dw|.'''
    plt = _setup_matplotlib()
    df = _slice(data.df, time_range)
    tick = df['tick']

    # Pick a connection to detail
    if conn is None:
        conn = data.cross_conns[0] if data.cross_conns else None
    if conn is None:
        return _empty_figure(plt, 'No cross-connections to detail')

    m = re.match(r'^w_(.+)<-', conn)
    uname = m.group(1) if m else None

    fig, axes = plt.subplots(4, 1, figsize=(12, 9), sharex=True)

    # Panel 1: Sigma
    sigma_col = 'sigma_%s' % uname if uname else None
    ax = axes[0]
    if sigma_col and sigma_col in df.columns:
        ax.plot(tick, df[sigma_col], lw=0.6, color='purple')
        ax.set_ylabel('sigma')
    else:
        ax.text(0.5, 0.5, 'No sigma column', transform=ax.transAxes, ha='center')
    ax.set_title('Detail: %s' % conn)

    # Panel 2: Stress
    stress_col = '%s_stress' % uname if uname else None
    ax = axes[1]
    if stress_col and stress_col in df.columns:
        ax.plot(tick, df[stress_col], lw=0.6, color='orange')
        ax.set_ylabel('Stress')
    else:
        ax.text(0.5, 0.5, 'No stress column', transform=ax.transAxes, ha='center')

    # Panel 3: Weight
    ax = axes[2]
    ax.plot(tick, df[conn], lw=0.7, color='teal')
    ax.axhline(0, color='grey', ls=':', lw=0.5)
    ax.set_ylabel('Weight')

    # Panel 4: |dw|
    dw_col = 'd' + conn
    ax = axes[3]
    if dw_col in df.columns:
        abs_dw = df[dw_col].abs()
        roll_dw = abs_dw.rolling(smooth, min_periods=1, center=True).mean()
        ax.plot(tick, roll_dw, lw=0.7, color='crimson')
        ax.set_ylabel('|dw| (smoothed)')
    else:
        ax.text(0.5, 0.5, 'No dw column', transform=ax.transAxes, ha='center')
    ax.set_xlabel('Tick')

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Plotting helpers
# ---------------------------------------------------------------------------

def _slice(df: pd.DataFrame, time_range: Optional[Tuple[int, int]]) -> pd.DataFrame:
    '''Restrict DataFrame to a tick range.'''
    if time_range is None:
        return df
    t0, t1 = time_range
    mask = (df['tick'] >= t0) & (df['tick'] <= t1)
    return df.loc[mask].copy()


def _shade_mask(ax, x, mask, color='green', alpha=0.1):
    '''Shade contiguous True regions of mask on axis.'''
    vals = mask.values if hasattr(mask, 'values') else np.asarray(mask)
    xvals = x.values if hasattr(x, 'values') else np.asarray(x)
    changes = np.diff(vals.astype(int))
    starts = np.where(changes == 1)[0] + 1
    ends = np.where(changes == -1)[0] + 1
    if vals[0]:
        starts = np.r_[0, starts]
    if vals[-1]:
        ends = np.r_[ends, len(vals) - 1]
    for s, e in zip(starts, ends):
        ax.axvspan(xvals[s], xvals[e], color=color, alpha=alpha)


def _empty_figure(plt, msg: str) -> 'Figure':
    '''Return a figure with a centered text message.'''
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.text(0.5, 0.5, msg, transform=ax.transAxes, ha='center', fontsize=12)
    ax.set_axis_off()
    return fig


# ---------------------------------------------------------------------------
# D. Text summary
# ---------------------------------------------------------------------------

def print_summary(data: StatelogData, file=None):
    '''Print a text diagnostic summary.'''
    if file is None:
        file = sys.stdout
    df = data.df
    out = lambda s='': print(s, file=file)

    out('=' * 60)
    out('STATELOG SUMMARY')
    out('=' * 60)

    n_ticks = len(df)
    out('Ticks logged: %d  (tick range %d - %d)' % (
        n_ticks, df['tick'].iloc[0], df['tick'].iloc[-1]))

    if 'distance' not in df.columns:
        out('No distance column found.')
        return

    # Min / final distance
    min_idx = df['distance'].idxmin()
    min_tick = df.loc[min_idx, 'tick']
    min_dist = df.loc[min_idx, 'distance']
    final_dist = df['distance'].iloc[-1]
    out()
    out('Distance')
    out('  Min distance:   %.4f  at tick %d' % (min_dist, min_tick))
    out('  Final distance: %.4f' % final_dist)

    # Overshoot tick: first tick after min where distance > 1.5 * min_dist
    overshoot_thresh = 1.5 * min_dist
    post_min = df.loc[min_idx:]
    overshoot_mask = post_min['distance'] > overshoot_thresh
    if overshoot_mask.any():
        overshoot_idx = overshoot_mask.idxmax()
        overshoot_tick = df.loc[overshoot_idx, 'tick']
        out('  Overshoot begins: tick %d  (distance > %.4f)' % (
            overshoot_tick, overshoot_thresh))
    else:
        out('  No overshoot detected (distance stays < %.4f)' % overshoot_thresh)

    # Weight sign flips for cross-connections
    out()
    out('Weight sign flips (cross-connections)')
    for col in data.cross_conns:
        vals = df[col].values
        sign_changes = np.where(np.diff(np.sign(vals)))[0]
        n_flips = len(sign_changes)
        # First flip after min-distance tick
        post_min_flips = sign_changes[sign_changes >= (min_idx - df.index[0])]
        if len(post_min_flips) > 0:
            first_post = df['tick'].iloc[post_min_flips[0]]
            out('  %-25s  %3d flips, first after min @ tick %d' % (
                col, n_flips, first_post))
        else:
            out('  %-25s  %3d flips, none after min-distance' % (col, n_flips))

    # Drift vs diffusion ratio
    out()
    out('Drift vs Diffusion (cross-connections)')
    for col in data.cross_conns:
        drift_col = 'drift_' + col
        resid_col = 'diffusion_' + col
        if drift_col not in df.columns:
            out('  %-25s  (no OU params in metadata)' % col)
            continue
        abs_drift = df[drift_col].abs()
        abs_resid = df[resid_col].abs()
        ratio = abs_resid / (abs_drift + 1e-12)
        med = ratio.median()
        p90 = ratio.quantile(0.9)
        out('  %-25s  median ratio: %.2f  90th pct: %.2f' % (col, med, p90))

    # Stress-distance correlation
    out()
    out('Stress-Distance Pearson Correlation')
    if 'mean_stress' in df.columns:
        # Approaching phase: up to min-distance
        approach = df.loc[:min_idx]
        if len(approach) > 2:
            corr_a = approach['distance'].corr(approach['mean_stress'])
            out('  Approaching phase (tick %d-%d): r = %.4f' % (
                approach['tick'].iloc[0], approach['tick'].iloc[-1], corr_a))
        # Retreating phase: after min-distance
        retreat = df.loc[min_idx:]
        if len(retreat) > 2:
            corr_r = retreat['distance'].corr(retreat['mean_stress'])
            out('  Retreating phase  (tick %d-%d): r = %.4f' % (
                retreat['tick'].iloc[0], retreat['tick'].iloc[-1], corr_r))
    else:
        out('  (no mean_stress column)')

    out()
    out('=' * 60)


# ---------------------------------------------------------------------------
# E. CLI
# ---------------------------------------------------------------------------

PLOT_FUNCS = {
    'overview': plot_overview,
    'drift': plot_drift_vs_diffusion,
    'stress': plot_stress_vs_distance,
    'anatomy': plot_connection_anatomy,
    'detail': plot_sigma_and_weight_detail,
}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Analyze Homeostat .statelog files for overshoot diagnostics.')
    parser.add_argument('statelog', help='Path to the .statelog file')
    parser.add_argument('--output', '-o', default=None,
                        help='Directory to save PDF plots (default: display summary)')
    parser.add_argument('--plot', '-p', nargs='+',
                        choices=list(PLOT_FUNCS.keys()),
                        default=None,
                        help='Which plots to generate (default: all)')
    parser.add_argument('--smooth', type=int, default=500,
                        help='Rolling window size for smoothing (default: 500)')
    parser.add_argument('--summary', action='store_true',
                        help='Print text summary only (no plots)')
    parser.add_argument('--time-range', nargs=2, type=int, default=None,
                        metavar=('START', 'END'),
                        help='Restrict analysis to tick range [START, END]')

    args = parser.parse_args(argv)

    # Parse
    print('Parsing %s ...' % args.statelog)
    data = parse_statelog(args.statelog)
    print('  %d ticks, %d columns' % (len(data.df), len(data.df.columns)))
    print('  Units: %s' % ', '.join(data.unit_names))
    print('  Cross-connections: %s' % ', '.join(data.cross_conns))

    # Enrich
    enrich(data, smooth=args.smooth)

    time_range = tuple(args.time_range) if args.time_range else None

    # Summary
    if args.summary or args.output is None and args.plot is None:
        print_summary(data)
        if args.summary:
            return

    # Plots
    if args.output is None and args.plot is None:
        # summary-only mode (already printed above)
        return

    plot_names = args.plot or list(PLOT_FUNCS.keys())
    output_dir = args.output or '.'
    os.makedirs(output_dir, exist_ok=True)

    for name in plot_names:
        fn = PLOT_FUNCS[name]
        print('  Generating %s ...' % name)
        fig = fn(data, smooth=args.smooth, time_range=time_range)
        path = os.path.join(output_dir, 'statelog_%s.pdf' % name)
        fig.savefig(path, bbox_inches='tight')
        import matplotlib.pyplot as plt
        plt.close(fig)
        print('    -> %s' % path)

    print('Done.')


if __name__ == '__main__':
    main(sys.argv[1:])
