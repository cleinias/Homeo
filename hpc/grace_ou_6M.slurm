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
#     mkdir -p logs && sbatch grace_ou_6M.slurm

set -euo pipefail

HOMEO_SRC="${HOMEO_SRC:-$SCRATCH/Homeo}"
VENV="${VENV:-$SCRATCH/homeo-venv}"

source "$HOMEO_SRC/hpc/load_python.sh"
homeo_load_python || exit 1
source "$VENV/bin/activate"

# Output to scratch, one directory per array task.
export HOMEO_DATA_DIR="$SCRATCH/homeo/ou6M-$SLURM_ARRAY_JOB_ID/task_$SLURM_ARRAY_TASK_ID"
mkdir -p "$HOMEO_DATA_DIR"

# Per-task numba cache: concurrent tasks must not share one.
export NUMBA_CACHE_DIR="${TMPDIR:-/tmp}/numba-$SLURM_ARRAY_TASK_ID"
mkdir -p "$NUMBA_CACHE_DIR"

cd "$HOMEO_SRC/src"

# Seed from the array index so the whole set is reproducible and distinct.
SEED=$(( 20260930 + SLURM_ARRAY_TASK_ID ))

echo "task $SLURM_ARRAY_TASK_ID  seed $SEED  out $HOMEO_DATA_DIR"
# Provenance: which commit produced these results.
echo "code $(git -C "$HOMEO_SRC" log --oneline -1 2>/dev/null || echo 'unversioned checkout')"
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
     --start-at-rest \
     --traj-interval 200
echo "task $SLURM_ARRAY_TASK_ID done"
