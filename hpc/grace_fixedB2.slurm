#!/bin/bash
#SBATCH --job-name=homeo-fixedB2
#SBATCH --array=1-200
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:30:00
#SBATCH --output=logs/%x-%A_%a.out
#SBATCH --error=logs/%x-%A_%a.err
#
# The fixed-weight Braitenberg 2 design as one 200-task array: the 8 wirings
# (crossed/uncrossed x signs ++ +- -+ --) x 25 random start poses, 300,000
# steps each, full trajectories (--traj-interval 1).
#
#     sbatch grace_fixedB2.slurm MIN MAX [SPIN [MOTOR [OPTIONS...]]]
#
# MIN MAX: the distance from the light of the random start (--start-range).
# SPIN:    baseline spin in place, fraction of max wheel speed, > 0 clockwise
#          (--spin; default 0, no spin).
# MOTOR:   newtonian (default) or aristotelian, the true Braitenberg vehicle
#          (--motor; memoryless linear motors).  Aristotelian runs go to
#          fixedB2-arist-...; e.g. the four Braitenberg baseline arrays:
#              sbatch grace_fixedB2.slurm 2 6 0 aristotelian
#              sbatch grace_fixedB2.slurm 4 8 0 aristotelian
#              sbatch grace_fixedB2.slurm 2 6 0.05 aristotelian
#              sbatch grace_fixedB2.slurm 4 8 0.05 aristotelian
# OPTIONS: the eyes, --eye-response linear|log, --eye-saturation D,
#          --eye-threshold I0; the robot, --robot epuck2|kjunior (default
#          e-puck2); passed to the experiment and named in the run directory, e.g.
#              sbatch grace_fixedB2.slurm 2 6 0.05 aristotelian --eye-response log --eye-saturation 0.5
#          writes to fixedB2-arist-r2to6-cw0.05-log-sat0.5-traj1-<jobid>.
#          And one of two seed options, for the environment x seed design:
#          --env-seed E  every task starts from the pose of environment seed E,
#                        the homeostat's seed varying as below (dir "-envE");
#          --seed S      every task has homeostat seed S, the start pose
#                        varying with the task's environment seed, which
#                        takes the per-task value below (dir "-seedS").
#
# Task -> run, identical to the 2026-10-03 polus baseline
# (SimulationsData/fixedB2-r4to8-traj1-2026-10-03), so the arrays pair
# run for run with it:
#     tasks   1- 25 crossed ++     101-125 uncrossed ++
#            26- 50 crossed +-     126-150 uncrossed +-
#            51- 75 crossed -+     151-175 uncrossed -+
#            76-100 crossed --     176-200 uncrossed --
#     seed = 20261004 + (task - 1) % 25
# The seed alone fixes the start pose -- it comes from the environment's
# stream, which the seed also seeds unless --env-seed/--seed say otherwise --
# so a seed has the same start pose in every variant, with or without a spin.
# (Before 14 Oct 2026 the pose came from the homeostat's stream, after the
# weights.)
#
# The "exploratory" arrays (2026-10-03), slow clockwise spin:
#     mkdir -p logs
#     sbatch grace_fixedB2.slurm 2 6 0.05
#     sbatch grace_fixedB2.slurm 4 8 0.05
#
# A reproduction check before trusting Grace: with SPIN 0 a task reproduces the
# polus baseline, e.g. task 37 (crossed +-, seed 20261015):
#     sbatch --array=37 grace_fixedB2.slurm 4 8
#     cmp <its .traj> <polus ...crossed_pm-...-37.traj>
#
# Each run takes ~2 min (131 s on polus's Xeon E3-1220).  Trajectories are
# ~30 MB per run, ~6 GB per array: hence $SCRATCH.
#
# The project account is deliberately not in this file (public repo); export
# SBATCH_ACCOUNT=<account> on Grace, or pass --account to sbatch.

set -euo pipefail

if [ $# -lt 2 ]; then
    echo "usage: sbatch grace_fixedB2.slurm MIN MAX [SPIN [MOTOR [OPTIONS...]]]" >&2; exit 2
fi
START_MIN="$1"; START_MAX="$2"; SPIN="${3:-0}"; MOTOR="${4:-newtonian}"
shift $(( $# < 4 ? $# : 4 ))
EYE_ARGS=(); eye_tag=""; FIXED_ENV_SEED=""; FIXED_SEED=""
while [ $# -gt 0 ]; do
    case "$1" in
        --env-seed)       FIXED_ENV_SEED="$2"; shift 2; continue;;
        --seed)           FIXED_SEED="$2"; shift 2; continue;;
        --robot)          [ "$2" != epuck2 ] && eye_tag+="-$2";;
        --eye-response)   [ "$2" = log ] && eye_tag+="-log";;
        --eye-saturation) eye_tag+="-sat$2";;
        --eye-threshold)  eye_tag+="-thr$2";;
        *) echo "unknown option: $1" >&2; exit 2;;
    esac
    EYE_ARGS+=("$1" "$2"); shift 2
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
if ! [[ "$SPIN" =~ ^-?[0-9]*\.?[0-9]+$ ]]; then
    echo "SPIN must be a number (fraction of max wheel speed, > 0 clockwise), got '$SPIN'" >&2; exit 2
fi
case "$MOTOR" in
    newtonian) motor_tag="";;
    aristotelian) motor_tag="-arist";;
    *) echo "MOTOR must be newtonian or aristotelian, got '$MOTOR'" >&2; exit 2;;
esac

HOMEO_SRC="${HOMEO_SRC:-$SCRATCH/Homeo}"
VENV="${VENV:-$SCRATCH/homeo-venv}"

source "$HOMEO_SRC/hpc/load_python.sh"
homeo_load_python || exit 1
source "$VENV/bin/activate"

# The variant and seed this task runs.
i=$(( SLURM_ARRAY_TASK_ID - 1 ))
WIRINGS=(crossed uncrossed)
SIGNS_LIST=('++' '+-' '-+' '--')
WIRING=${WIRINGS[$(( i / 100 ))]}
SIGNS=${SIGNS_LIST[$(( i / 25 % 4 ))]}
SEED=$(( 20261004 + i % 25 ))
# The environment's seed (the start pose): by default the same per-task value.
ENV_SEED=$SEED
[ -n "$FIXED_ENV_SEED" ] && ENV_SEED=$FIXED_ENV_SEED
[ -n "$FIXED_SEED" ] && SEED=$FIXED_SEED
# Zero-padded to 2 digits, as run_array_local.sh did on polus.
SERIAL=$(printf '%02d' "$SLURM_ARRAY_TASK_ID")

vehicle_args=(--fixed-weights --motor "$MOTOR" --signs "$SIGNS")
[ "$WIRING" = uncrossed ] && vehicle_args+=(--uncrossed)
spin_args=()
spin_tag=""
# Compared as a number: as a string, "0.0" or "0.00" was a spin (review
# finding SH-10), passed on as --spin 0.0 and tagged "-cw0.0".
if awk -v s="$SPIN" 'BEGIN { exit !(s + 0 != 0) }'; then
    spin_args=(--spin "$SPIN")
    case "$SPIN" in -*) spin_tag="-ccw${SPIN#-}";; *) spin_tag="-cw$SPIN";; esac
fi

# ONE output directory for the whole array; filenames carry the serial.
# HOMEO_DATA_DIR is the data ROOT: the experiment appends "SimsData-<date>".
RUN_NAME="fixedB2${motor_tag}-r${START_MIN}to${START_MAX}${spin_tag}${eye_tag}${seed_tag}-traj1-$SLURM_ARRAY_JOB_ID"
export HOMEO_DATA_DIR="$SCRATCH/homeo/$RUN_NAME"
mkdir -p "$HOMEO_DATA_DIR"

# Per-task numba cache: concurrent tasks must not share one.
export NUMBA_CACHE_DIR="${TMPDIR:-/tmp}/numba-$SLURM_ARRAY_TASK_ID"
mkdir -p "$NUMBA_CACHE_DIR"

CODE="$(git -C "$HOMEO_SRC" describe --always --dirty 2>/dev/null || echo 'unversioned checkout') $(git -C "$HOMEO_SRC" log -1 --format=%s 2>/dev/null || true)"
# numba draws its noise from its own generator: a seed gives a different run
# with and without it, so record which (compare before pairing with other machines)
PYENV="python $(python -c 'import platform; print(platform.python_version())' 2>/dev/null), numba $(python -c 'import numba; print(numba.__version__)' 2>/dev/null || echo absent)"
# The first task to get here writes the directory's provenance.  Every task
# writes its own copy and tries to hard-link it into place: ln fails if the
# file exists, and the check and the creation are one step, so of tasks
# starting together exactly one wins and the file is never half-written (they
# used to check, then write, and could interleave: review finding SH-10).
if [ ! -e "$HOMEO_DATA_DIR/PROVENANCE.txt" ]; then
    provenance_tmp="$HOMEO_DATA_DIR/.PROVENANCE.txt.$SLURM_ARRAY_TASK_ID"
    {
        echo "generated by hpc/grace_fixedB2.slurm, job $SLURM_ARRAY_JOB_ID, $(date -Is) on Grace"
        echo "tasks 1-200: 8 wirings x 25 seeds (20261004-20261028), 300000 steps, traj-interval 1"
        echo "random start $START_MIN-$START_MAX from the light"
        echo "spin $SPIN x max wheel speed (> 0 clockwise)"
        echo "motor $MOTOR"
        echo "eyes ${EYE_ARGS[*]:-default (linear, threshold 0, saturation 100)}"
        if [ -n "$FIXED_ENV_SEED" ]; then echo "env seed $FIXED_ENV_SEED for every task (one start pose)"
        elif [ -n "$FIXED_SEED" ]; then echo "seed $FIXED_SEED for every task; env seeds 20261004-20261028"
        else echo "env seed = seed"; fi
        echo "code $CODE"
        echo "cpu  $(lscpu 2>/dev/null | sed -n 's/^Model name: *//p' | head -1)"
        echo "$PYENV"
    } > "$provenance_tmp"
    ln "$provenance_tmp" "$HOMEO_DATA_DIR/PROVENANCE.txt" 2>/dev/null || true
    rm -f "$provenance_tmp"
fi

echo "task $SLURM_ARRAY_TASK_ID: $MOTOR $WIRING $SIGNS  seed $SEED  env seed $ENV_SEED  start $START_MIN-$START_MAX  spin $SPIN"
echo "out  $HOMEO_DATA_DIR"
echo "code $CODE"
echo "$PYENV"

cd "$HOMEO_SRC/src"
srun python -m HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct \
     "${vehicle_args[@]}" \
     --random-start --start-range "$START_MIN" "$START_MAX" \
     "${spin_args[@]}" \
     "${EYE_ARGS[@]}" \
     --batch 1 \
     --steps 300000 \
     --seed "$SEED" \
     --env-seed "$ENV_SEED" \
     --start-at-rest \
     --traj-interval 1 \
     --run-tag "$SERIAL"
echo "task $SLURM_ARRAY_TASK_ID done"
