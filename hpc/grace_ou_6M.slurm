#!/bin/bash
#SBATCH --job-name=homeo-ou6M
#SBATCH --array=1-20
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=04:00:00
#SBATCH --output=logs/%x-%A_%a.out
#SBATCH --error=logs/%x-%A_%a.err
##SBATCH --account=XXXXXXXXXXXX      # <-- uncomment and set your project account
#
# Replication of the 2026-09-30 overnight batch with the three defects fixed:
#   - the OU uniselector now actually runs in headless mode
#   - numerically unstable (mass, viscosity) draws are rejected
#   - vehicles start at rest instead of mid-manoeuvre
#
# 20 independent runs, 6M steps each, one core per run.  Sequentially this took
# 12.5 hours; as an array it is one run's wall time.
#
# Submit from the directory containing this file:
#     mkdir -p logs && sbatch grace_ou_6M.slurm

set -euo pipefail

HOMEO_SRC="${HOMEO_SRC:-$SCRATCH/Homeo}"
VENV="${VENV:-$SCRATCH/homeo-venv}"

module purge
module load GCCcore/13.2.0 Python/3.11.5       # match grace_setup.sh
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
# --batch 1 (rather than a bare run) so each task writes a one-row summary CSV
# carrying seed, start pose, acquired, first_acq and final distance -- the whole
# array can then be aggregated by concatenating them.
srun python -m HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct \
     --continuous \
     --batch 1 \
     --steps 6000000 \
     --seed "$SEED" \
     --start-at-rest
echo "task $SLURM_ARRAY_TASK_ID done"
