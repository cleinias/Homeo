#!/usr/bin/env python3
"""run_direct_vehicle_ga.py — GA experiments for the simplified 2+2 direct vehicle.

Runs 2 GA experiments concurrently using the 4-unit Braitenberg-2 vehicle
(2 sensors + 2 motors, no eye intermediaries):

  Exp 1: GA + OU, fixed dt_fast=1.0, 8-gene genome (2 units x 4 params)
  Exp 2: GA + OU, evolvable dt_fast, 10-gene genome (2 units x 5 params)

Both use fixed Braitenberg cross-wiring (Left Sensor -> Right Motor,
Right Sensor -> Left Motor) with negative motor self-connections.

Usage:
    python run_direct_vehicle_ga.py                  # orchestrate both
    python run_direct_vehicle_ga.py --exp 1          # run experiment 1 only
    python run_direct_vehicle_ga.py --exp 2 --workers 4
    python run_direct_vehicle_ga.py --pop 150 --gen 50   # override defaults
"""

import sys
import os
import subprocess
import threading
import time
import datetime

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SRC_DIR)
from Helpers.General_Helper_Functions import simulations_data_dir
SIMS_DATA = simulations_data_dir()

# Default GA parameters
DEFAULT_POP_SIZE = 150
DEFAULT_GENERATIONS = 50
DEFAULT_STEPS = 60000


# ---------------------------------------------------------------------------
# Single-experiment runners (called in subprocess via --exp N)
# ---------------------------------------------------------------------------

def run_ga_experiment(exp_num, exp_name, n_workers, seed,
                      pop_size=DEFAULT_POP_SIZE, generations=DEFAULT_GENERATIONS,
                      steps=DEFAULT_STEPS):
    """Run a GA experiment with progress callback."""
    from Simulator.HomeoGenAlgGui import HomeoGASimulation

    # Point data directory to Cybernetics-research
    HomeoGASimulation.dataDirRoot = SIMS_DATA

    def progress(gen, record, best_fitness):
        print("PROGRESS: Generation %d/%d of Exp %d — best=%.4f, avg=%.4f" % (
            gen, generations, exp_num, best_fitness, record['avg']), flush=True)

    ga = HomeoGASimulation(
        stepsSize=steps, popSize=pop_size, generSize=generations,
        exp=exp_name, simulatorBackend="HOMEO", nWorkers=n_workers)

    print("PROGRESS: Exp %d started — %s (%d pop x %d gen, %d workers)" % (
        exp_num, exp_name, pop_size, generations, n_workers), flush=True)

    pop = ga.generateRandomPop(randomSeed=seed)
    ga.runGaSimulation(pop, progressCallback=progress)

    print("PROGRESS: Exp %d finished — best=%.4f" % (
        exp_num, ga.hof[0].fitness.values[0]), flush=True)


def run_exp1(n_workers, pop_size=DEFAULT_POP_SIZE, generations=DEFAULT_GENERATIONS,
             steps=DEFAULT_STEPS):
    """Exp 1: Direct 2+2, GA + OU, fixed dt_fast=1.0, 8-gene genome."""
    run_ga_experiment(1,
        "initializeBraiten2_direct_GA_continuous_weightfree_fixed_dt",
        n_workers, seed=44, pop_size=pop_size, generations=generations,
        steps=steps)


def run_exp2(n_workers, pop_size=DEFAULT_POP_SIZE, generations=DEFAULT_GENERATIONS,
             steps=DEFAULT_STEPS):
    """Exp 2: Direct 2+2, GA + OU, evolvable dt_fast, 10-gene genome."""
    run_ga_experiment(2,
        "initializeBraiten2_direct_GA_continuous_weightfree_fixed",
        n_workers, seed=45, pop_size=pop_size, generations=generations,
        steps=steps)


# ---------------------------------------------------------------------------
# Subprocess entry point (--exp N)
# ---------------------------------------------------------------------------

def run_single(exp_num, n_workers, pop_size, generations, steps):
    os.chdir(SRC_DIR)
    if SRC_DIR not in sys.path:
        sys.path.insert(0, SRC_DIR)

    runners = {
        1: run_exp1,
        2: run_exp2,
    }
    runners[exp_num](n_workers, pop_size=pop_size, generations=generations,
                     steps=steps)


# ---------------------------------------------------------------------------
# Orchestrator (default mode)
# ---------------------------------------------------------------------------

def orchestrate(pop_size=DEFAULT_POP_SIZE, generations=DEFAULT_GENERATIONS,
                steps=DEFAULT_STEPS):
    timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')
    log_dir = os.path.join(SIMS_DATA,
                           'direct-vehicle-ga-' + timestamp)
    os.makedirs(log_dir, exist_ok=True)

    n_cores = os.cpu_count() or 8
    # Split cores between 2 GA experiments
    workers_per_ga = max(1, n_cores // 2)

    print("=" * 60)
    print("  Direct 2+2 Vehicle: GA Experiments")
    print("=" * 60)
    print("  Population   : %d" % pop_size)
    print("  Generations  : %d" % generations)
    print("  Steps/indiv  : %d" % steps)
    print("  Log directory: %s" % os.path.abspath(log_dir))
    print("  CPU cores    : %d" % n_cores)
    print("  GA workers   : %d per experiment" % workers_per_ga)
    print("=" * 60)
    print()

    exp_labels = {
        1: 'GA+OU fixed dt (8 genes)',
        2: 'GA+OU variable dt (10 genes)',
    }

    # Launch both as subprocesses
    procs = {}
    for exp_num in [1, 2]:
        cmd = [sys.executable, os.path.abspath(__file__),
               '--exp', str(exp_num),
               '--workers', str(workers_per_ga),
               '--pop', str(pop_size),
               '--gen', str(generations),
               '--steps', str(steps)]
        log_path = os.path.join(log_dir, 'exp%d.log' % exp_num)
        log_file = open(log_path, 'w', buffering=1)
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            bufsize=1, text=True, cwd=SRC_DIR)
        procs[exp_num] = (proc, log_file, log_path)

    # Reader threads: save all output to log, print only PROGRESS: lines
    def reader(exp_num, proc, log_file):
        for line in proc.stdout:
            line = line.rstrip('\n')
            log_file.write(line + '\n')
            if line.startswith("PROGRESS:"):
                ts = datetime.datetime.now().strftime("%H:%M:%S")
                msg = line[len("PROGRESS:"):].strip()
                print("[%s] %s" % (ts, msg), flush=True)
        proc.wait()
        log_file.close()

    threads = []
    for exp_num, (proc, log_file, _) in procs.items():
        t = threading.Thread(target=reader, args=(exp_num, proc, log_file),
                             daemon=True)
        t.start()
        threads.append(t)

    # Wait for all experiments to finish
    for t in threads:
        t.join()

    # Report exit codes
    print()
    print("=" * 60)
    print("  All experiments complete")
    print("=" * 60)
    for exp_num, (proc, _, log_path) in procs.items():
        status = "OK" if proc.returncode == 0 else "FAILED (exit %d)" % proc.returncode
        print("  Exp %d %-35s %s" % (exp_num, exp_labels[exp_num], status))
    print()
    print("  Detailed logs: %s" % os.path.abspath(log_dir))
    print("=" * 60)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    pop_size = DEFAULT_POP_SIZE
    generations = DEFAULT_GENERATIONS
    steps = DEFAULT_STEPS

    if '--pop' in sys.argv:
        pop_size = int(sys.argv[sys.argv.index('--pop') + 1])
    if '--gen' in sys.argv:
        generations = int(sys.argv[sys.argv.index('--gen') + 1])
    if '--steps' in sys.argv:
        steps = int(sys.argv[sys.argv.index('--steps') + 1])

    if '--exp' in sys.argv:
        exp_num = int(sys.argv[sys.argv.index('--exp') + 1])
        workers = 3
        if '--workers' in sys.argv:
            workers = int(sys.argv[sys.argv.index('--workers') + 1])
        run_single(exp_num, workers, pop_size, generations, steps)
    else:
        orchestrate(pop_size, generations, steps)
