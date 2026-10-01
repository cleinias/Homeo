#!/usr/bin/env python3
"""Concatenate the per-task CSVs of a Homeo SLURM array into one table.

    python aggregate_array.py $SCRATCH/homeo/ou6M-<jobid>  [-o combined.csv]
"""
import argparse, glob, os, sys
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument('rundir', help='the ou6M-<jobid> directory holding task_* subdirs')
ap.add_argument('-o', '--output', default=None)
a = ap.parse_args()

files = sorted(glob.glob(os.path.join(a.rundir, 'task_*', '**', 'batch_*.csv'),
                         recursive=True))
if not files:
    sys.exit(f'no per-task CSVs under {a.rundir}')

df = pd.concat([pd.read_csv(f).assign(
        task=int(os.path.basename(os.path.dirname(os.path.dirname(f))).split('_')[1]))
        for f in files], ignore_index=True).sort_values('task')

cols = [c for c in ('task', 'seed', 'acquired', 'first_acq', 'final_dist',
                    'min_dist', 'min_t', 'steps_run', 'wall_time') if c in df]
print(df[cols].to_string(index=False))
print()
n = len(df)
print(f'runs: {n}   acquired: {int(df.acquired.sum())}/{n}')
if df.acquired.any():
    acq = df.loc[df.acquired, 'first_acq']
    print(f'time to acquisition: min {acq.min():,.0f}  median {acq.median():,.0f}  max {acq.max():,.0f}')
    for T in (60_000, 300_000, 1_000_000, 2_000_000, 4_000_000, 6_000_000):
        print(f'   acquired by t={T:>9,}: {int((acq <= T).sum()):2d}/{n}')
print(f'final distance: mean {df.final_dist.mean():.3f}  median {df.final_dist.median():.3f}')

if a.output:
    df.to_csv(a.output, index=False)
    print(f'\nwritten: {a.output}')
