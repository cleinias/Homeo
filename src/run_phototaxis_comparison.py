#!/usr/bin/env python3
"""run_phototaxis_comparison.py — Launch all 4 phototaxis experiments concurrently.

Console shows only generation/completion summaries.
Full verbose output is saved to per-experiment log files.

Usage:
    python run_phototaxis_comparison.py                  # orchestrate all 4
    python run_phototaxis_comparison.py --exp 1          # run experiment 1 only
    python run_phototaxis_comparison.py --exp 3 --workers 4
"""

import sys
import os
import subprocess
import threading
import time
import datetime

SRC_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Single-experiment runners (called in subprocess via --exp N)
# ---------------------------------------------------------------------------

def run_exp1():
    """Exp 1: Standalone Ashby (discrete uniselector)."""
    from HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_Ashby import run_headless

    print("PROGRESS: Exp 1 started — Standalone Ashby, 60k steps", flush=True)
    result = run_headless(
        topology='fixed', total_steps=60000, report_interval=500,
        light_intensity=-100, quiet=True, uniselector_type='ashby')
    print("PROGRESS: Exp 1 concluded — final_dist=%.4f, min_dist=%.4f (t=%d)" % (
        result['final_dist'], result['min_dist'], result['min_t']), flush=True)


def run_exp2():
    """Exp 2: Standalone OU (continuous uniselector)."""
    from HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_Ashby import run_headless

    print("PROGRESS: Exp 2 started — Standalone OU, 60k steps", flush=True)
    result = run_headless(
        topology='fixed', total_steps=60000, report_interval=500,
        light_intensity=-100, quiet=True, uniselector_type='continuous')
    print("PROGRESS: Exp 2 concluded — final_dist=%.4f, min_dist=%.4f (t=%d)" % (
        result['final_dist'], result['min_dist'], result['min_t']), flush=True)


def run_ga_experiment(exp_num, exp_name, n_workers, seed):
    """Run a GA experiment with progress callback.

    All verbose GA output (mating, population lists, per-individual
    evaluation times) goes to stdout — the orchestrator captures it to
    a log file.  Only PROGRESS: lines reach the console.
    """
    from Simulator.HomeoGenAlgGui import HomeoGASimulation

    def progress(gen, record, best_fitness):
        print("PROGRESS: Generation %d of Exp %d concluded — best=%.4f, avg=%.4f" % (
            gen, exp_num, best_fitness, record['avg']), flush=True)

    ga = HomeoGASimulation(
        stepsSize=60000, popSize=150, generSize=100,
        exp=exp_name, simulatorBackend="HOMEO", nWorkers=n_workers)

    print("PROGRESS: Exp %d started — %s (150 pop x 100 gen, %d workers)" % (
        exp_num, exp_name, n_workers), flush=True)

    pop = ga.generateRandomPop(randomSeed=seed)
    ga.runGaSimulation(pop, progressCallback=progress)

    print("PROGRESS: Exp %d finished — best=%.4f" % (
        exp_num, ga.hof[0].fitness.values[0]), flush=True)


def run_exp3(n_workers):
    """Exp 3: GA + OU, fixed dt_fast=1.0, 16-gene genome."""
    run_ga_experiment(3,
        "initializeBraiten2_2_Full_GA_continuous_weightfree_fixed_dt",
        n_workers, seed=42)


def run_exp4(n_workers):
    """Exp 4: GA + OU, evolvable dt_fast, 20-gene genome."""
    run_ga_experiment(4,
        "initializeBraiten2_2_Full_GA_continuous_weightfree_fixed",
        n_workers, seed=43)


# ---------------------------------------------------------------------------
# Subprocess entry point (--exp N)
# ---------------------------------------------------------------------------

def run_single(exp_num, n_workers):
    os.chdir(SRC_DIR)
    if SRC_DIR not in sys.path:
        sys.path.insert(0, SRC_DIR)

    runners = {
        1: lambda: run_exp1(),
        2: lambda: run_exp2(),
        3: lambda: run_exp3(n_workers),
        4: lambda: run_exp4(n_workers),
    }
    runners[exp_num]()


# ---------------------------------------------------------------------------
# Orchestrator (default mode)
# ---------------------------------------------------------------------------

def orchestrate():
    timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')
    log_dir = os.path.join(SRC_DIR, '..', 'SimulationsData',
                           'phototaxis-comparison-' + timestamp)
    os.makedirs(log_dir, exist_ok=True)

    n_cores = os.cpu_count() or 8
    # 2 standalone experiments are single-process and fast.
    # Split remaining cores between 2 GA experiments.
    workers_per_ga = max(1, (n_cores - 2) // 2)

    print("=" * 60)
    print("  Phototaxis Comparison: 4 Experiments")
    print("=" * 60)
    print("  Log directory : %s" % os.path.abspath(log_dir))
    print("  CPU cores     : %d" % n_cores)
    print("  GA workers    : %d per experiment" % workers_per_ga)
    print("=" * 60)
    print()

    exp_labels = {
        1: 'Standalone Ashby',
        2: 'Standalone OU',
        3: 'GA+OU fixed dt (16 genes)',
        4: 'GA+OU variable dt (20 genes)',
    }

    # Launch all 4 as subprocesses
    procs = {}
    for exp_num in [1, 2, 3, 4]:
        cmd = [sys.executable, os.path.abspath(__file__),
               '--exp', str(exp_num), '--workers', str(workers_per_ga)]
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
    if '--exp' in sys.argv:
        exp_num = int(sys.argv[sys.argv.index('--exp') + 1])
        workers = 3
        if '--workers' in sys.argv:
            workers = int(sys.argv[sys.argv.index('--workers') + 1])
        run_single(exp_num, workers)
    else:
        orchestrate()
