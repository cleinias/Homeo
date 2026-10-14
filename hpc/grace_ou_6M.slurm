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
# Replication of the 2026-09-30 overnight batch with the three defects fixed:
#   - the OU uniselector now actually runs in headless mode
#   - numerically unstable (mass, viscosity) draws are rejected
#   - vehicles start at rest instead of mid-manoeuvre
#
# 20 independent runs, 6M steps each, one core per run.  Sequentially this took
# 12.5 hours; as an array it is one run's wall time.
#
# The project account is deliberately not in this file (public repo).  Either
# export it once on Grace --- Slurm honours it as a default:
#     export SBATCH_ACCOUNT=<your project account>     # e.g. in ~/.bashrc
# or pass it per submission:
#     sbatch --account=<your project account> grace_ou_6M.slurm
#
# Submit from the directory containing this file:
#     mkdir -p logs && sbatch grace_ou_6M.slurm [--env-seed E | --seed S]
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

FIXED_ENV_SEED=""; FIXED_SEED=""
while [ $# -gt 0 ]; do
    case "$1" in
        --env-seed) FIXED_ENV_SEED="$2"; shift 2;;
        --seed)     FIXED_SEED="$2"; shift 2;;
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
# cannot collide -- and the array needs no merging step afterwards.  Until
# 2026-10-01 each task wrote to task_$SLURM_ARRAY_TASK_ID/ and filenames were
# distinguished only by a whole-second timestamp, so merging the directories by
# hand silently overwrote the files of any two tasks that started in the same
# second.
# HOMEO_DATA_DIR is the data ROOT: the experiment appends "SimsData-<date>".
export HOMEO_DATA_DIR="$SCRATCH/homeo/ou6M${seed_tag}-$SLURM_ARRAY_JOB_ID"
mkdir -p "$HOMEO_DATA_DIR"

# Per-task numba cache: concurrent tasks must not share one.
export NUMBA_CACHE_DIR="${TMPDIR:-/tmp}/numba-$SLURM_ARRAY_TASK_ID"
mkdir -p "$NUMBA_CACHE_DIR"

cd "$HOMEO_SRC/src"

# Seed from the array index so the whole set is reproducible and distinct.
SEED=$(( 20260930 + SLURM_ARRAY_TASK_ID ))
ENV_SEED=$SEED
[ -n "$FIXED_ENV_SEED" ] && ENV_SEED=$FIXED_ENV_SEED
[ -n "$FIXED_SEED" ] && SEED=$FIXED_SEED
# Zero-padded so the filenames sort by task.
SERIAL=$(printf '%02d' "$SLURM_ARRAY_TASK_ID")

echo "task $SLURM_ARRAY_TASK_ID  seed $SEED  env seed $ENV_SEED  out $HOMEO_DATA_DIR"
# Provenance: which commit produced these results.
echo "code $(git -C "$HOMEO_SRC" log --oneline -1 2>/dev/null || echo 'unversioned checkout')"
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
     --run-tag "$SERIAL"
echo "task $SLURM_ARRAY_TASK_ID done"
