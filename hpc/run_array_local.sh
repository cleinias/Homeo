#!/bin/bash
# Run the grace_ou_6M.slurm array on a local workstation instead of Grace.
#
#     bash hpc/run_array_local.sh                  # tasks 1-20, 4 workers
#     bash hpc/run_array_local.sh -a 3-20          # just tasks 3..20
#     bash hpc/run_array_local.sh -n 2 -s 200000   # 2 workers, short test runs
#     bash hpc/run_array_local.sh --dry-run
#     bash hpc/run_array_local.sh --state-log --log-interval 200   # + weight traces
#     bash hpc/run_array_local.sh --uniselector ashby      # discrete, not OU
#     bash hpc/run_array_local.sh --random-heading         # heading from the seed
#     bash hpc/run_array_local.sh --heading 45 --seeds 101,102,...
#                                                  # chosen seeds, fixed heading
#     bash hpc/run_array_local.sh --random-start --env-seed 7
#                                  # one start pose for every task, the homeostat
#                                  # varying with the task's seed
#     bash hpc/run_array_local.sh --random-start --seeds 5,5,5 --env-seeds 7,8,9
#                                  # one homeostat, three start poses; with both
#                                  # lists any crossed design (task i takes the
#                                  # i-th entry of each)
#                                  # The environment's seed (--env-seed, the start
#                                  # pose) defaults to the task's seed.
#     bash hpc/run_array_local.sh --fixed-weights --signs +- --uncrossed \
#          --random-start --start-range 4 8 -s 300000 -a 101-125
#                                  # non-adaptive Braitenberg 2 vehicle: wiring
#                                  # crossed (2b, default) or --uncrossed (2a);
#                                  # --signs left eye's sign then right eye's;
#                                  # random position 4-8 from the light, random
#                                  # heading
#     bash hpc/run_array_local.sh --fixed-weights --random-start --spin 0.05 ...
#                                  # + a slow clockwise baseline spin in place
#                                  # (fraction of max wheel speed; < 0 for CCW)
#     bash hpc/run_array_local.sh --fixed-weights --motor aristotelian ...
#                                  # the true Braitenberg vehicle: memoryless,
#                                  # linear motors (default: newtonian)
#     bash hpc/run_array_local.sh ... --eye-response log --eye-saturation 0.5
#                                  # the eyes' sensitivity: response linear|log,
#                                  # saturation distance, --eye-threshold I0
#     bash hpc/run_array_local.sh ... --robot kjunior
#                                  # the K-Junior (default: the e-puck2)
#     bash hpc/run_array_local.sh ... -- --stable-draws --dark
#                                  # anything after -- goes to the experiment
#                                  # as it is (see the options of
#                                  # phototaxis_braitenberg2_direct)
#
# Runs the array grace_ou_6M.slurm runs -- the same seeds (20260930 + task),
# the same options (--continuous --batch 1 --start-at-rest --traj-interval 200
# --run-tag <NN>, then the options after --), the same shared HOMEO_DATA_DIR
# and per-task NUMBA_CACHE_DIR -- so that `aggregate_array.py` reads either.
# The two give the same runs, run for run, when they run the same Homeo commit
# with the same options and both have numba, or both lack it: numba draws its
# noise from its own generator, so the same seed gives a different run with and
# without it.  PROVENANCE.txt records the command, the commit and the numba
# version (or "absent").
#
# LAYOUT.  All tasks write into ONE directory, <rundir>/SimsData-<date>/, and
# every filename ends with the task serial before its extension:
#
#     phototaxis_braitenberg2_direct_fixed_continuous-<timestamp>-07.json
#     batch_direct_continuous_light_<timestamp>-07.csv
#     run_task-07.out
#
# One directory, so the results need no merging, and a serial, because a
# "%Y-%m-%d-%H-%M-%S" timestamp alone does not tell tasks apart: tasks that
# start within the same second get byte-identical names.  The serial makes
# names unique by construction instead of by luck of the clock.
#
# Why this exists: an expired allocation, or anything else that makes Grace
# unavailable. Grace is still the better venue -- there all 20 tasks run on 20
# separate cores and the array finishes in one run's wall time (~37 min),
# whereas locally they queue through however many cores you have.
#
# On a 4-core 3.6 GHz Xeon: 2774 steps/s solo, so ~36 min per 6M-step
# run; 4 concurrent runs slow each other by ~1.25x, giving ~45 min per run and
# ~3.7 h for the full 20. Re-measure with `-n 1 -s 200000` on other hardware.
#
# Re-runnable: a task whose own batch CSV (batch_*-<NN>.csv) already exists, in
# any of the run's SimsData-<date>/ directories, is skipped, so an interrupted
# batch can be resumed, on any later day, by invoking the same command with -o
# pointing at the existing run directory.
#
# SPLITTING ACROSS TWO MACHINES.  The tasks are independent and seeded purely by
# index, so a split is exact -- provided both machines have numba, or both lack
# it (see above; compare the numba lines of their PROVENANCE.txt): the union of
# two partial runs is the same 20 runs one machine would have produced.  Give each machine a disjoint range, then
# copy one machine's data files in beside the other's -- the serials keep them
# from colliding -- and aggregate as usual.  Divide the ranges in
# proportion to measured throughput, and remember a machine finishes in whole
# waves of <workers> tasks, so a range that straddles a wave boundary buys
# nothing.  Example with a 4-core workstation (~45 min/task when 4 run at once)
# and a slower 4-core server (~53 min/task):
#
#     RUN=.../SimulationsData/ou6M-<date>
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
SEEDS=""
ENV_SEED=""
ENV_SEEDS=""
HEADING=""
RANDOM_HEADING=0
FIXED_WEIGHTS=0
SIGNS=""
UNCROSSED=0
RANDOM_START=0
START_RANGE=""
SPIN=""
MOTOR=""
EYE_ARGS=()
EXTRA_ARGS=()
UNISELECTOR=continuous


# Print the whole leading comment block, rather than a hardcoded line range:
# a range silently goes stale every time the header is edited.
usage() {
    awk 'NR == 1 { next }
         /^#/    { sub(/^# ?/, ""); print; next }
         { exit }' "${BASH_SOURCE[0]}"
    exit 0
}

INVOCATION=("$@")
while [ $# -gt 0 ]; do
    case "$1" in
        -n|--workers)  WORKERS="$2"; shift 2;;
        -a|--array)    FIRST="${2%%-*}"; LAST="${2##*-}"; shift 2;;
        -s|--steps)    STEPS="$2"; shift 2;;
        -o|--out)      RUNDIR="$2"; shift 2;;
        --traj-interval) TRAJ_INTERVAL="$2"; shift 2;;
        --state-log)     STATE_LOG=1; shift;;
        --log-interval)  LOG_INTERVAL="$2"; shift 2;;
        --seeds)         SEEDS="$2"; shift 2;;
        --env-seed)      ENV_SEED="$2"; shift 2;;
        --env-seeds)     ENV_SEEDS="$2"; shift 2;;
        --heading)       HEADING="$2"; shift 2;;
        --random-heading) RANDOM_HEADING=1; shift;;
        --fixed-weights) FIXED_WEIGHTS=1; shift;;
        --signs)         SIGNS="$2"; shift 2;;
        --uncrossed)     UNCROSSED=1; shift;;
        --random-start)  RANDOM_START=1; shift;;
        --start-range)   START_RANGE="$2 $3"; shift 3;;
        --spin)          SPIN="$2"; shift 2;;
        --motor)         MOTOR="$2"; shift 2;;
        --eye-response|--eye-threshold|--eye-saturation)
                         EYE_ARGS+=("$1" "$2"); shift 2;;
        --robot)         EYE_ARGS+=("$1" "$2"); shift 2;;
        --uniselector)   UNISELECTOR="$2"; shift 2;;
        --dry-run)     DRY_RUN=1; shift;;
        --)            shift; EXTRA_ARGS=("$@"); break;;
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

if [ -n "$ENV_SEED" ] && [ -n "$ENV_SEEDS" ]; then
    echo "--env-seed and --env-seeds are mutually exclusive" >&2; exit 2
fi
if [ -n "$ENV_SEED" ] && ! [[ "$ENV_SEED" =~ ^[0-9]+$ ]]; then
    echo "--env-seed needs a non-negative integer, got '$ENV_SEED'" >&2; exit 2
fi
if [ -n "$HEADING" ] && [ "$RANDOM_HEADING" -eq 1 ]; then
    echo "--heading and --random-heading are mutually exclusive" >&2; exit 2
fi
if [ "$RANDOM_START" -eq 1 ] && { [ -n "$HEADING" ] || [ "$RANDOM_HEADING" -eq 1 ]; }; then
    echo "--random-start draws the heading too: drop --heading/--random-heading" >&2; exit 2
fi
if [ -n "$START_RANGE" ] && [ "$RANDOM_START" -eq 0 ]; then
    echo "--start-range applies only with --random-start" >&2; exit 2
fi
if [ "$FIXED_WEIGHTS" -eq 0 ] && { [ -n "$SIGNS" ] || [ "$UNCROSSED" -eq 1 ] || [ -n "$MOTOR" ]; }; then
    echo "--signs, --uncrossed and --motor apply only with --fixed-weights" >&2; exit 2
fi
case "$MOTOR" in
    ""|newtonian|aristotelian) ;;
    *) echo "--motor must be newtonian or aristotelian, got '$MOTOR'" >&2; exit 2;;
esac
case "$SIGNS" in
    ""|"++"|"+-"|"-+"|"--") ;;
    *) echo "--signs must be ++, +-, -+ or --, got '$SIGNS'" >&2; exit 2;;
esac

if [ -n "$SPIN" ] && ! [[ "$SPIN" =~ ^-?[0-9]*\.?[0-9]+$ ]]; then
    echo "--spin needs a number (fraction of max wheel speed, > 0 clockwise), got '$SPIN'" >&2; exit 2
fi

case "$UNISELECTOR" in
    continuous|ashby) ;;
    *) echo "--uniselector must be 'continuous' or 'ashby', got '$UNISELECTOR'" >&2; exit 2;;
esac

n_tasks=$(( LAST - FIRST + 1 ))
waves=$(( (n_tasks + WORKERS - 1) / WORKERS ))

# Preflight: prove the chosen interpreter can import what a run needs, BEFORE
# starting anything.  One clear message beats N identical buried tracebacks.
# It imports the run's own modules rather than a list of packages, so it tests
# what a task actually does: a bare `import pyglet` succeeds on a node with no
# libGL, where importing KheperaSimulator then fails.  HomeostatConditionLogger
# is listed because the experiment imports it lazily, inside run_headless, and
# it is what pulls in tabulate.  PyQt5 is not needed: without it the Core falls
# back to a null signal emitter (Helpers/QObjectProxyEmitter).
missing=$(cd "$HOMEO_SRC/src" && "$PYTHON" - <<'PYEOF' 2>/dev/null
import importlib
need = ['Core.Homeostat', 'Simulator.HomeoExperiments',
        'KheperaSimulator.KheperaSimulator', 'Helpers.HomeostatConditionLogger',
        'HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct']
for m in need:
    try:
        importlib.import_module(m)
    except Exception as e:
        print('      %s -- %s: %s' % (m, type(e).__name__, e))
PYEOF
)
if [ -n "${missing:-}" ] || ! "$PYTHON" -c 'pass' 2>/dev/null; then
    echo "!! $PYTHON cannot run the experiment." >&2
    [ -n "${missing:-}" ] && printf '   cannot import:\n%s\n' "$missing" >&2
    echo "   Point PYTHON at the interpreter that has them, e.g." >&2
    echo "       PYTHON=\$HOME/homeo-venv/bin/python bash $0 $*" >&2
    echo "   or activate the venv first." >&2
    exit 1
fi

spin_dir() { case "$SPIN" in -*) echo counter-clockwise;; *) echo clockwise;; esac; }

# The Homeo code the tasks run: the commit ("-dirty" with uncommitted changes)
# and its subject line
homeo_code() {
    local version subject
    version=$(git -C "$HOMEO_SRC" describe --always --dirty 2>/dev/null) || {
        echo 'unversioned checkout'; return; }
    subject=$(git -C "$HOMEO_SRC" log -1 --format=%s 2>/dev/null)
    echo "$version $subject"
}

echo "== local array run"
echo "   tasks      : $FIRST-$LAST  ($n_tasks tasks)"
echo "   workers    : $WORKERS concurrent  ->  $waves waves"
echo "   steps/task : $STEPS   traj-interval $TRAJ_INTERVAL"
if [ "$FIXED_WEIGHTS" -eq 1 ]; then
    echo "   vehicle    : fixed weights (no homeostat), ${MOTOR:-newtonian} motors, $([ "$UNCROSSED" -eq 1 ] && echo uncrossed || echo crossed), signs ${SIGNS:-++} (left eye, right eye)"
else
    echo "   uniselector: $UNISELECTOR"
fi
[ -n "$HEADING" ] && echo "   heading    : $HEADING deg (fixed)"
[ "$RANDOM_HEADING" -eq 1 ] && echo "   heading    : random, drawn from each run's environment seed"
[ -n "$SPIN" ]    && echo "   spin       : $SPIN x max wheel speed ($(spin_dir))"
[ ${#EYE_ARGS[@]} -gt 0 ] && echo "   eyes       : ${EYE_ARGS[*]}"
[ "$RANDOM_START" -eq 1 ] && echo "   start      : random position ${START_RANGE/ /-} from the light (default 2-6), random heading"
[ -n "$SEEDS" ]   && echo "   seeds      : explicit -- $SEEDS"
[ -n "$ENV_SEED" ]  && echo "   env seed   : $ENV_SEED for every task"
[ -n "$ENV_SEEDS" ] && echo "   env seeds  : explicit -- $ENV_SEEDS"
if [ "$STATE_LOG" -eq 1 ]; then
    echo "   state log  : on, every $LOG_INTERVAL ticks (weights, stress, sigma)"
fi
[ ${#EXTRA_ARGS[@]} -gt 0 ] && echo "   options    : ${EXTRA_ARGS[*]} (to the experiment)"
echo "   output     : $DATADIR"
echo "                (one directory for all tasks; filenames carry the serial)"
echo "   code       : $(homeo_code)"
echo

# Provenance alongside the results, so the directory is self-describing.
# Appended, not overwritten: a design run as several invocations into one
# directory (e.g. one per wiring of the fixed-weight design)
# would otherwise keep only the last invocation's record.
{
    echo "----"
    echo "generated by hpc/run_array_local.sh on $(date -Is) on $(hostname)"
    echo "command hpc/run_array_local.sh ${INVOCATION[*]}"
    echo "tasks $FIRST-$LAST, $WORKERS workers, $STEPS steps, traj-interval $TRAJ_INTERVAL"
    [ "$STATE_LOG" -eq 1 ] && echo "state log every $LOG_INTERVAL ticks"
    if [ "$FIXED_WEIGHTS" -eq 1 ]; then
        echo "fixed weights, ${MOTOR:-newtonian} motors, $([ "$UNCROSSED" -eq 1 ] && echo uncrossed || echo crossed), signs ${SIGNS:-++}"
    else
        echo "uniselector $UNISELECTOR"
    fi
    [ -n "$HEADING" ] && echo "fixed heading $HEADING deg"
    [ "$RANDOM_HEADING" -eq 1 ] && echo "random heading per run"
    [ "$RANDOM_START" -eq 1 ] && echo "random start ${START_RANGE/ /-} from the light (default 2-6)"
    [ -n "$SPIN" ] && echo "spin $SPIN x max wheel speed ($(spin_dir))"
    [ ${#EYE_ARGS[@]} -gt 0 ] && echo "eyes ${EYE_ARGS[*]}"
    [ -n "$SEEDS" ] && echo "seeds $SEEDS"
    [ -n "$ENV_SEED" ] && echo "env seed $ENV_SEED for every task"
    [ -n "$ENV_SEEDS" ] && echo "env seeds $ENV_SEEDS"
    [ ${#EXTRA_ARGS[@]} -gt 0 ] && echo "experiment options ${EXTRA_ARGS[*]}"
    echo "code $(homeo_code)"
    echo "cpu  $(lscpu 2>/dev/null | sed -n 's/^Model name: *//p' | head -1)"
    echo "python $("$PYTHON" -c 'import platform; print(platform.python_version())' 2>/dev/null), numba $("$PYTHON" -c 'import numba; print(numba.__version__)' 2>/dev/null || echo absent)"
} >> "$RUNDIR/PROVENANCE.txt"

task_done() {   # a task counts as finished once its own batch CSV exists
    # The CSV is named ...-<serial>.csv, so a task is identified by its serial
    # rather than by a directory.  It is looked for in every dated directory of
    # the run, not only today's: an array resumed with -o on a later day, or
    # one straddling midnight, has finished tasks under an earlier date (run
    # again, they would leave two CSVs for one task).  A per-task task_<i>/
    # directory is accepted too, so that an array written in that layout can
    # be resumed with -o.
    local s; s=$(printf '%02d' "$1")
    compgen -G "$RUNDIR/SimsData-*/batch_*-$s.csv" >/dev/null 2>&1 ||
        compgen -G "$RUNDIR/task_$1/*/batch_*.csv" >/dev/null 2>&1
}

# Task i's entry in a comma-separated list: the i-th, whatever the range, so
# that a range split across machines, or a narrowed resume, takes each task's
# own entry from the same list.
list_entry() {   # list_entry <list> <option name> <task>
    local value
    value=$(echo "$1" | cut -d, -f"$3")
    if [ -z "$value" ]; then
        echo "   task $3: no $3-th entry in $2" >&2
        return 1
    fi
    echo "$value"
}

# Task i's seed (the homeostat's): 20260930 (an arbitrary base) + i, unless
# --seeds gives it.
# --seeds is needed whenever the seeds are chosen rather than enumerated --
# e.g. picked so that each connection-polarity class is represented a fixed
# number of times, which no arithmetic rule can give.
task_seed() {
    if [ -n "$SEEDS" ]; then list_entry "$SEEDS" --seeds "$1"; else echo $(( 20260930 + $1 )); fi
}

# Task i's environment seed (the start pose): --env-seed, the task's entry in
# --env-seeds, or nothing -- the experiment then uses the task's seed.
task_env_seed() {
    if [ -n "$ENV_SEEDS" ]; then list_entry "$ENV_SEEDS" --env-seeds "$1"; else echo "$ENV_SEED"; fi
}

run_task() {
    local i="$1" seed env_seed serial state_log_args heading_args
    serial=$(printf '%02d' "$i")
    seed=$(task_seed "$i") || return 1
    env_seed=$(task_env_seed "$i") || return 1
    local env_seed_args=()
    [ -n "$env_seed" ] && env_seed_args=(--env-seed "$env_seed")
    heading_args=""
    if [ -n "$HEADING" ]; then
        heading_args="--heading $HEADING"
    elif [ "$RANDOM_HEADING" -eq 1 ]; then
        # Drawn from the environment's own stream (--env-seed; by default the
        # run's seed), never from the homeostat's, so one seed gives the same
        # homeostat, noise included, at heading 0 and at a random heading --
        # which is what makes a random-heading batch a paired comparison
        # against a heading-0 one rather than an independent sample.
        heading_args="--random-heading"
    fi
    # The experiment selects the uniselector by the presence of --continuous;
    # omitting it gives Ashby's discrete one.
    local unisel_args=""
    if [ "$UNISELECTOR" = continuous ] && [ "$FIXED_WEIGHTS" -eq 0 ]; then
        unisel_args="--continuous"
    fi
    # The non-adaptive vehicle and the random start pose, as an array so that
    # each word stays intact -- including a --signs value of '--'.
    local vehicle_args=()
    if [ "$FIXED_WEIGHTS" -eq 1 ]; then
        vehicle_args+=(--fixed-weights)
        [ -n "$SIGNS" ] && vehicle_args+=(--signs "$SIGNS")
        [ "$UNCROSSED" -eq 1 ] && vehicle_args+=(--uncrossed)
        [ -n "$MOTOR" ] && vehicle_args+=(--motor "$MOTOR")
    fi
    if [ "$RANDOM_START" -eq 1 ]; then
        vehicle_args+=(--random-start)
        # shellcheck disable=SC2206  # two numbers, split on purpose
        [ -n "$START_RANGE" ] && vehicle_args+=(--start-range $START_RANGE)
    fi
    [ -n "$SPIN" ] && vehicle_args+=(--spin "$SPIN")
    vehicle_args+=("${EYE_ARGS[@]}")
    # Per-tick state log: the weight, stress and sigma trajectories.  Left
    # unquoted at the call site so an empty value expands to nothing.
    state_log_args=""
    if [ "$STATE_LOG" -eq 1 ]; then
        state_log_args="--state-log --log-interval $LOG_INTERVAL"
    fi
    mkdir -p "$DATADIR" "$RUNDIR/.numba/task_$i"
    # ALL tasks write into one directory, so the results need no merging.
    # A whole-second timestamp alone does not tell apart tasks that start in
    # the same second; --run-tag makes every filename carry the task serial, so
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
        $unisel_args \
        --batch 1 \
        --steps "$STEPS" \
        --seed "$seed" \
        "${env_seed_args[@]}" \
        --start-at-rest \
        --traj-interval "$TRAJ_INTERVAL" \
        --run-tag "$serial" \
        $state_log_args \
        $heading_args \
        "${vehicle_args[@]}" \
        "${EXTRA_ARGS[@]}" \
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
        echo "   task $i: would run with seed $(task_seed "$i")$(e=$(task_env_seed "$i") && [ -n "$e" ] && echo ", env seed $e")"
        [ ${#EXTRA_ARGS[@]} -gt 0 ] && echo "     and ${EXTRA_ARGS[*]}"
        continue
    fi
    # Block until a worker slot frees up.
    while [ "$(jobs -rp | wc -l)" -ge "$WORKERS" ]; do wait -n 2>/dev/null || break; done
    ( run_task "$i" \
        && echo "   task $i done   ($(date +%H:%M:%S))" \
        || echo "   task $i FAILED -- see $DATADIR/run_task-$(printf '%02d' "$i").out" ) &
    started=$(( started + 1 ))
done

wait
[ "$DRY_RUN" -eq 1 ] && { echo; echo "dry run: nothing executed"; exit 0; }

elapsed=$(( $(date +%s) - t0 ))
echo
printf '== finished: %d started, %d skipped, %dh%02dm elapsed\n' \
       "$started" "$skipped" $(( elapsed / 3600 )) $(( elapsed % 3600 / 60 ))

# Finished tasks of THIS invocation's range, by the same test that skips them:
# counting every batch CSV under the run directory would also count other
# ranges' and other invocations' tasks.
ok=0
for i in $(seq "$FIRST" "$LAST"); do task_done "$i" && ok=$(( ok + 1 )); done
echo "   tasks with results: $ok/$n_tasks"
if [ "$ok" -lt "$n_tasks" ]; then
    echo "   !! missing results -- check $DATADIR/run_task-*.out"
    echo "      re-run the same command with -o $RUNDIR to retry only the missing tasks"
fi
echo
echo "aggregate with:"
echo "   $PYTHON $_hpc_dir/aggregate_array.py $RUNDIR"
