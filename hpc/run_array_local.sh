#!/bin/bash
# Run the grace_ou_6M.slurm array on a local workstation instead of Grace.
#
#     bash hpc/run_array_local.sh                  # tasks 1-20, 4 workers
#     bash hpc/run_array_local.sh -a 3-20          # just tasks 3..20
#     bash hpc/run_array_local.sh -n 2 -s 200000   # 2 workers, short test runs
#     bash hpc/run_array_local.sh --dry-run
#     bash hpc/run_array_local.sh --state-log --log-interval 200   # + weight traces
#
# Mirrors grace_ou_6M.slurm exactly -- same seeds (20260930 + task), same flags
# (--continuous --batch 1 --start-at-rest --traj-interval 200 --run-tag <NN>),
# same shared HOMEO_DATA_DIR and per-task NUMBA_CACHE_DIR -- so the output is
# directly comparable with a Grace array and `aggregate_array.py` reads it
# unchanged.
#
# LAYOUT.  All tasks write into ONE directory, <rundir>/SimsData-<date>/, and
# every filename ends with the task serial before its extension:
#
#     phototaxis_braitenberg2_direct_fixed_continuous-<timestamp>-07.json
#     batch_direct_continuous_light_<timestamp>-07.csv
#     run_task-07.out
#
# Until 2026-10-01 each task got its own task_<i>/ directory and filenames were
# distinguished only by a "%Y-%m-%d-%H-%M-%S" timestamp.  Both halves of that
# were a mistake: the per-task directories had to be merged by hand before the
# results could be used, and the merge silently overwrote files, because tasks
# that started within the same second produced byte-identical names.  In the
# 2026-10-01 20-run array, tasks 2 and 3 both stamped 13-23-38.  The serial
# makes names unique by construction instead of by luck of the clock.
#
# Why this exists: an expired allocation, or anything else that makes Grace
# unavailable. Grace is still the better venue -- there all 20 tasks run on 20
# separate cores and the array finishes in one run's wall time (~37 min),
# whereas locally they queue through however many cores you have.
#
# Measured on a 4-core Xeon W-2123: 2774 steps/s solo, so ~36 min per 6M-step
# run; 4 concurrent runs slow each other by ~1.25x, giving ~45 min per run and
# ~3.7 h for the full 20. Re-measure with `-n 1 -s 200000` on other hardware.
#
# Re-runnable: a task whose own batch CSV (batch_*-<NN>.csv) already exists is
# skipped, so an interrupted batch can be resumed by invoking the same command
# with -o pointing at the existing run directory.
#
# SPLITTING ACROSS TWO MACHINES.  The tasks are independent and seeded purely by
# index, so a split is exact: the union of two partial runs is the same 20 runs
# one machine would have produced.  Give each machine a disjoint range, then
# copy one machine's data files in beside the other's -- the serials keep them
# from colliding -- and aggregate as usual.  Divide the ranges in
# proportion to measured throughput, and remember a machine finishes in whole
# waves of <workers> tasks, so a range that straddles a wave boundary buys
# nothing.  Example with a 4-core workstation (~45 min/task when 4 run at once)
# and a slower 4-core server (~53 min/task):
#
#     RUN=.../SimulationsData/ou6M-2026-10-01
#     # the faster machine takes 12, i.e. 3 waves:
#     bash hpc/run_array_local.sh -a 1-12 -o "$RUN"
#     # the slower one takes 8, i.e. 2 waves (PYTHON= if its venv is elsewhere):
#     ssh server 'cd ~/Homeo && PYTHON=$HOME/homeo-venv/bin/python \
#         nohup bash hpc/run_array_local.sh -a 13-20 -o $HOME/ou6M &'
#     # then pull its results in and aggregate the lot:
#     rsync -a server:ou6M/SimsData-*/ "$RUN"/SimsData-*/
#     python3 hpc/aggregate_array.py "$RUN"
#
# Put the output on real disk: a tmpfs /tmp is RAM, and 20 tasks of trajectory
# data in RAM on a small server will not end well.
set -uo pipefail          # deliberately NOT -e: one failed task must not kill the batch

_hpc_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOMEO_SRC="${HOMEO_SRC:-$(cd "$_hpc_dir/.." && pwd)}"

# Pick an interpreter that can actually run the experiment.  Falling back to a
# bare `python3` is a trap on any machine where the dependencies live in a venv:
# the system interpreter often has numpy and nothing else, so every task dies
# identically on the first missing import and the real cause is buried in eight
# tracebacks.  Prefer an explicit $PYTHON, then an active venv, then the
# conventional venv locations, and only then python3.
if [ -z "${PYTHON:-}" ]; then
    # Build the candidate list guarding every variable: an unset VIRTUAL_ENV
    # would make "${VIRTUAL_ENV:-}/bin/python" collapse to the absolute path
    # /bin/python, which exists on most systems and would win the search.
    _cands=()
    [ -n "${VIRTUAL_ENV:-}" ] && _cands+=("$VIRTUAL_ENV/bin/python")
    _cands+=("$HOMEO_SRC/.venv/bin/python" "$HOME/homeo-venv/bin/python")
    [ -n "${SCRATCH:-}" ] && _cands+=("$SCRATCH/homeo-venv/bin/python")
    for _cand in "${_cands[@]}"; do
        if [ -x "$_cand" ]; then PYTHON="$_cand"; break; fi
    done
    PYTHON="${PYTHON:-python3}"
fi

# Default to PHYSICAL cores, not nproc.  nproc counts hyperthreads, and these
# runs are CPU-bound floating-point work that gains nothing from a second thread
# on the same core -- oversubscribing just makes every run slower.
default_workers() {
    local phys
    phys=$(lscpu -p=Core,Socket 2>/dev/null | grep -v '^#' | sort -u | wc -l)
    [ "${phys:-0}" -ge 1 ] 2>/dev/null && echo "$phys" || echo 1
}

WORKERS=$(default_workers)
FIRST=1
LAST=20
STEPS=6000000
TRAJ_INTERVAL=200
RUNDIR=""
DRY_RUN=0
STATE_LOG=0
LOG_INTERVAL=200

# Print the whole leading comment block, rather than a hardcoded line range:
# the range silently went stale every time the header was edited.
usage() {
    awk 'NR == 1 { next }
         /^#/    { sub(/^# ?/, ""); print; next }
         { exit }' "${BASH_SOURCE[0]}"
    exit 0
}

while [ $# -gt 0 ]; do
    case "$1" in
        -n|--workers)  WORKERS="$2"; shift 2;;
        -a|--array)    FIRST="${2%%-*}"; LAST="${2##*-}"; shift 2;;
        -s|--steps)    STEPS="$2"; shift 2;;
        -o|--out)      RUNDIR="$2"; shift 2;;
        --traj-interval) TRAJ_INTERVAL="$2"; shift 2;;
        --state-log)     STATE_LOG=1; shift;;
        --log-interval)  LOG_INTERVAL="$2"; shift 2;;
        --dry-run)     DRY_RUN=1; shift;;
        -h|--help)     usage;;
        *) echo "unknown option: $1" >&2; exit 2;;
    esac
done

# Where the results go.  Default beside the Grace layout but clearly marked
# local, under whatever simulations_data_dir() resolves to.
if [ -z "$RUNDIR" ]; then
    data_root=$(cd "$HOMEO_SRC/src" && "$PYTHON" -c \
        'from Helpers.General_Helper_Functions import simulations_data_dir; print(simulations_data_dir())') || {
        echo "!! could not resolve the SimulationsData directory" >&2; exit 1; }
    RUNDIR="$data_root/ou6M-local-$(date +%Y-%m-%d-%H-%M-%S)"
fi
# One directory for every task's output.  Kept as a dated subdirectory rather
# than $RUNDIR itself so that PROVENANCE.txt and the numba cache do not sit
# among the data files, and so the name matches what the experiment code
# produces on its own ("SimsData-<date>").
# This must match the name the experiment derives for itself from the date, so
# that the .out logs land beside the data and task_done() looks in the right
# place.  An array straddling midnight is the one case where it will not: the
# tasks after midnight make their own dated directory.
DATADIR="$RUNDIR/SimsData-$(date +%Y-%m-%d)"
mkdir -p "$DATADIR"

n_tasks=$(( LAST - FIRST + 1 ))
waves=$(( (n_tasks + WORKERS - 1) / WORKERS ))

# Preflight: prove the chosen interpreter can import what a run needs, BEFORE
# starting anything.  One clear message beats N identical buried tracebacks.
# tabulate is listed because it is imported early, well before Box2D, so a
# half-provisioned interpreter fails there and the error looks unrelated.
missing=$(cd "$HOMEO_SRC/src" && "$PYTHON" - <<'PYEOF' 2>/dev/null
import importlib, sys
need = ['numpy', 'Box2D', 'pyglet', 'tabulate', 'PyQt5.QtCore']
bad = []
for m in need:
    try:
        importlib.import_module(m)
    except Exception:
        bad.append(m)
print(' '.join(bad))
PYEOF
)
if [ -n "${missing:-}" ] || ! "$PYTHON" -c 'pass' 2>/dev/null; then
    echo "!! $PYTHON cannot run the experiment." >&2
    [ -n "${missing:-}" ] && echo "   missing modules: $missing" >&2
    echo "   Point PYTHON at the interpreter that has them, e.g." >&2
    echo "       PYTHON=\$HOME/homeo-venv/bin/python bash $0 $*" >&2
    echo "   or activate the venv first." >&2
    exit 1
fi

echo "== local array run"
echo "   tasks      : $FIRST-$LAST  ($n_tasks tasks)"
echo "   workers    : $WORKERS concurrent  ->  $waves waves"
echo "   steps/task : $STEPS   traj-interval $TRAJ_INTERVAL"
if [ "$STATE_LOG" -eq 1 ]; then
    echo "   state log  : on, every $LOG_INTERVAL ticks (weights, stress, sigma)"
fi
echo "   output     : $DATADIR"
echo "                (one directory for all tasks; filenames carry the serial)"
echo "   code       : $(git -C "$HOMEO_SRC" log --oneline -1 2>/dev/null || echo 'unversioned checkout')"
echo

# Provenance alongside the results, so the directory is self-describing.
{
    echo "generated by hpc/run_array_local.sh on $(date -Is) on $(hostname)"
    echo "tasks $FIRST-$LAST, $WORKERS workers, $STEPS steps, traj-interval $TRAJ_INTERVAL"
    [ "$STATE_LOG" -eq 1 ] && echo "state log every $LOG_INTERVAL ticks" 
    echo "code $(git -C "$HOMEO_SRC" log --oneline -1 2>/dev/null || echo 'unversioned')"
    echo "cpu  $(lscpu 2>/dev/null | sed -n 's/^Model name: *//p' | head -1)"
} > "$RUNDIR/PROVENANCE.txt"

task_done() {   # a task counts as finished once its own batch CSV exists
    # The CSV is named ...-<serial>.csv, so a task is identified by its serial
    # rather than by a directory.  The legacy per-task path is still accepted so
    # that an array started under the old layout can be resumed with -o.
    local s; s=$(printf '%02d' "$1")
    compgen -G "$DATADIR/batch_*-$s.csv" >/dev/null 2>&1 ||
        compgen -G "$RUNDIR/task_$1/*/batch_*.csv" >/dev/null 2>&1
}

run_task() {
    local i="$1" seed=$(( 20260930 + $1 )) serial state_log_args
    serial=$(printf '%02d' "$i")
    # Per-tick state log: the weight, stress and sigma trajectories.  Left
    # unquoted at the call site so an empty value expands to nothing.
    state_log_args=""
    if [ "$STATE_LOG" -eq 1 ]; then
        state_log_args="--state-log --log-interval $LOG_INTERVAL"
    fi
    mkdir -p "$DATADIR" "$RUNDIR/.numba/task_$i"
    # ALL tasks write into one directory.  They used to get one directory each,
    # which meant the results had to be merged by hand afterwards -- and that
    # merge was lossy, because filenames were distinguished only by a
    # whole-second timestamp and tasks starting in the same second produced
    # identical names.  --run-tag makes every filename carry the task serial, so
    # a shared directory is collision-free by construction.
    # NB: HOMEO_DATA_DIR is the data ROOT, not the final directory -- the
    # experiment appends "SimsData-<date>" to it itself.  Pointing it at
    # $DATADIR (which already ends in SimsData-<date>) would nest a second one.
    export HOMEO_DATA_DIR="$RUNDIR"
    # The numba cache, by contrast, MUST stay per-task: concurrent tasks
    # corrupt a shared cache.  It is a build artifact, not data.
    export NUMBA_CACHE_DIR="$RUNDIR/.numba/task_$i"
    cd "$HOMEO_SRC/src" || return 1
    "$PYTHON" -m HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct \
        --continuous \
        --batch 1 \
        --steps "$STEPS" \
        --seed "$seed" \
        --start-at-rest \
        --traj-interval "$TRAJ_INTERVAL" \
        --run-tag "$serial" \
        $state_log_args \
        > "$DATADIR/run_task-$serial.out" 2>&1
}

started=0; skipped=0
t0=$(date +%s)

for i in $(seq "$FIRST" "$LAST"); do
    if task_done "$i"; then
        echo "   task $i: already complete, skipping"
        skipped=$(( skipped + 1 ))
        continue
    fi
    if [ "$DRY_RUN" -eq 1 ]; then
        echo "   task $i: would run with seed $(( 20260930 + i ))"
        continue
    fi
    # Block until a worker slot frees up.
    while [ "$(jobs -rp | wc -l)" -ge "$WORKERS" ]; do wait -n 2>/dev/null || break; done
    ( run_task "$i" \
        && echo "   task $i done   ($(date +%H:%M:%S))" \
        || echo "   task $i FAILED -- see $RUNDIR/logs/task_$i.out" ) &
    started=$(( started + 1 ))
done

wait
[ "$DRY_RUN" -eq 1 ] && { echo; echo "dry run: nothing executed"; exit 0; }

elapsed=$(( $(date +%s) - t0 ))
echo
printf '== finished: %d started, %d skipped, %dh%02dm elapsed\n' \
       "$started" "$skipped" $(( elapsed / 3600 )) $(( elapsed % 3600 / 60 ))

ok=$(find "$RUNDIR" -name 'batch_*.csv' 2>/dev/null | wc -l)   # one per task
echo "   tasks with results: $ok/$n_tasks"
if [ "$ok" -lt "$n_tasks" ]; then
    echo "   !! missing results -- check $DATADIR/run_task-*.out"
    echo "      re-run the same command with -o $RUNDIR to retry only the missing tasks"
fi
echo
echo "aggregate with:"
echo "   $PYTHON $_hpc_dir/aggregate_array.py $RUNDIR"
