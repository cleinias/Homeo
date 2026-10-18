#!/bin/bash
#SBATCH --job-name=homeo-ou6M
#SBATCH --array=1-20
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=04:00:00
#SBATCH --output=logs/%x-%A_%a.out
#SBATCH --error=logs/%x-%A_%a.err
#
# Copyright (C) 2026 Stefano Franchi
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
#
# 20 independent runs of the direct phototaxis experiment
# (phototaxis_braitenberg2_direct) with the continuous uniselector, 6M steps
# each, one core per run: the robot (the e-puck2) starts at rest at the default
# pose, and each motor's (mass, viscosity) is drawn from the full distribution.
# Sequentially the array takes about 12.5 hours; on Grace, one run's wall time.
# hpc/run_array_local.sh runs the same array on a workstation.
#
# The project account is deliberately not in this file (public repo).  Either
# export it once on Grace --- Slurm honours it as a default:
#     export SBATCH_ACCOUNT=<your project account>     # e.g. in ~/.bashrc
# or pass it per submission:
#     sbatch --account=<your project account> grace_ou_6M.slurm
#
# Submit from the directory containing this file:
#     mkdir -p logs && sbatch grace_ou_6M.slurm [--env-seed E | --seed S] [-- OPTIONS]
#
# OPTIONS, after --, go to the experiment as they are, e.g.
#     sbatch grace_ou_6M.slurm -- --stable-draws      # redraw unstable (mass, viscosity)
#     sbatch grace_ou_6M.slurm -- --robot kjunior --dark
#
# The task's seed seeds both the homeostat and the environment (the start
# pose; the default pose draws nothing).  For the environment x seed design:
#     --env-seed E  every task has environment seed E, the homeostat's seed
#                   varying with the task (run directory ou6M-envE-<job>);
#     --seed S      every task has homeostat seed S, the environment's seed
#                   varying with the task (ou6M-seedS-<job>).
# They matter only with a random start pose, which this array does not use as
# it stands: add --random-heading or --random-start to the command below.

set -euo pipefail

FIXED_ENV_SEED=""; FIXED_SEED=""; EXTRA_ARGS=()
INVOCATION=("$@")
while [ $# -gt 0 ]; do
    case "$1" in
        --env-seed) FIXED_ENV_SEED="$2"; shift 2;;
        --seed)     FIXED_SEED="$2"; shift 2;;
        --)         shift; EXTRA_ARGS=("$@"); break;;
        *) echo "unknown option: $1" >&2; exit 2;;
    esac
done
if [ -n "$FIXED_ENV_SEED" ] && [ -n "$FIXED_SEED" ]; then
    echo "--env-seed and --seed are mutually exclusive" >&2; exit 2
fi
for s in "$FIXED_ENV_SEED" "$FIXED_SEED"; do
    if [ -n "$s" ] && ! [[ "$s" =~ ^[0-9]+$ ]]; then
        echo "a seed must be a non-negative integer, got '$s'" >&2; exit 2
    fi
done
seed_tag="${FIXED_ENV_SEED:+-env$FIXED_ENV_SEED}${FIXED_SEED:+-seed$FIXED_SEED}"

HOMEO_SRC="${HOMEO_SRC:-$SCRATCH/Homeo}"
VENV="${VENV:-$SCRATCH/homeo-venv}"

source "$HOMEO_SRC/hpc/load_python.sh"
homeo_load_python || exit 1
source "$VENV/bin/activate"

# Output to scratch, ONE directory shared by every array task.  Each task's
# filenames carry its array index (--run-tag below), so a shared directory
# cannot collide -- and the array needs no merging step afterwards.
# HOMEO_DATA_DIR is the data ROOT: the experiment appends "SimsData-<date>".
export HOMEO_DATA_DIR="$SCRATCH/homeo/ou6M${seed_tag}-$SLURM_ARRAY_JOB_ID"
mkdir -p "$HOMEO_DATA_DIR"

# Per-task numba cache: concurrent tasks must not share one.
export NUMBA_CACHE_DIR="${TMPDIR:-/tmp}/numba-$SLURM_ARRAY_TASK_ID"
mkdir -p "$NUMBA_CACHE_DIR"

cd "$HOMEO_SRC/src"

# Seed from the array index so the whole set is reproducible and distinct.
SEED=$(( 20260930 + SLURM_ARRAY_TASK_ID ))         # an arbitrary base
ENV_SEED=$SEED
[ -n "$FIXED_ENV_SEED" ] && ENV_SEED=$FIXED_ENV_SEED
[ -n "$FIXED_SEED" ] && SEED=$FIXED_SEED
# Zero-padded so the filenames sort by task.
SERIAL=$(printf '%02d' "$SLURM_ARRAY_TASK_ID")

echo "task $SLURM_ARRAY_TASK_ID  seed $SEED  env seed $ENV_SEED  out $HOMEO_DATA_DIR"
# Provenance: the command and the commit ("-dirty" with uncommitted changes)
echo "command grace_ou_6M.slurm ${INVOCATION[*]}"
echo "code $(git -C "$HOMEO_SRC" describe --always --dirty 2>/dev/null || echo 'unversioned checkout') $(git -C "$HOMEO_SRC" log -1 --format=%s 2>/dev/null || true)"
# numba draws its noise from its own generator: a seed gives a different run
# with and without it, so record which.
echo "python $(python -c 'import platform; print(platform.python_version())' 2>/dev/null), numba $(python -c 'import numba; print(numba.__version__)' 2>/dev/null || echo absent)"
# --batch 1 (rather than a bare run) so each task writes a one-row summary CSV
# carrying seed, start pose, acquired, first_acq and final distance -- the whole
# array can then be aggregated by concatenating them.
# --traj-interval 200: one row per 100 homeostat ticks, so 6M steps yield ~60k
# trajectory points (~3 MB) instead of 12M (~600 MB).  The whole 20-task array
# writes ~60 MB rather than 11.5 GB.  The vehicle's true final pose is always
# written regardless of the interval, so final-distance figures are exact, and
# the grapher thins to 50,000 points anyway.
srun python -m HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct \
     --continuous \
     --batch 1 \
     --steps 6000000 \
     --seed "$SEED" \
     --env-seed "$ENV_SEED" \
     --start-at-rest \
     --traj-interval 200 \
     --run-tag "$SERIAL" \
     "${EXTRA_ARGS[@]}"
echo "task $SLURM_ARRAY_TASK_ID done"
