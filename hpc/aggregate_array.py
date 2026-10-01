#!/usr/bin/env python3
"""Concatenate the per-task CSVs of a Homeo SLURM array into one table.

    python aggregate_array.py $SCRATCH/homeo/ou6M-<jobid>  [-o combined.csv]
"""
import argparse, glob, os, re, sys
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument('rundir', help='the ou6M-<jobid> run directory')
ap.add_argument('-o', '--output', default=None)
a = ap.parse_args()


def task_of(path):
    r"""Recover the array index of a per-task batch CSV.

    Two layouts, because the array's output moved into a single directory on
    2026-10-01.  Current: the index is a serial appended after the timestamp,

        batch_direct_continuous_light_2026-10-01-13-58-11-07.csv
                                      \_____ timestamp ____/ \/ serial

    Legacy: the filename ended at the timestamp and the index came from the
    enclosing task_<i>/ directory.

    The two cannot be told apart by "is there a trailing -NN", because a legacy
    name ends with the timestamp's own seconds field, which looks identical.
    So the whole %Y-%m-%d-%H-%M-%S shape is matched and the index is taken only
    from a group FOLLOWING it.  A non-numeric tag (--run-tag accepts any word)
    carries no index, so that falls back to the directory too.
    """
    stem = os.path.basename(path)[:-len('.csv')]
    # [-_] before the year: the CSV names join it with '_'
    # (batch_direct_continuous_light_2026-10-01-...), the .json/.log with '-'.
    m = re.search(r'[-_]\d{4}(?:-\d{2}){5}(?:-(\w+))?$', stem)
    if m and m.group(1) and m.group(1).isdigit():
        return int(m.group(1))
    for part in os.path.abspath(path).split(os.sep):
        if re.fullmatch(r'task_\d+', part):
            return int(part.split('_')[1])
    raise SystemExit(f'cannot tell which task this CSV belongs to: {path}')


# Both layouts: anywhere under the run directory, at any depth.
files = sorted(glob.glob(os.path.join(a.rundir, '**', 'batch_*.csv'), recursive=True))
# A previously written combined table is not an input.
files = [f for f in files if not os.path.basename(f).startswith('batch_direct_ALL')
         and '_ALL-' not in os.path.basename(f)]
if not files:
    sys.exit(f'no per-task CSVs under {a.rundir}')

df = pd.concat([pd.read_csv(f).assign(task=task_of(f)) for f in files],
               ignore_index=True).sort_values('task')

dupes = df.task[df.task.duplicated()].tolist()
if dupes:
    sys.exit(f'more than one CSV claims the same task index: {sorted(set(dupes))}')

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
