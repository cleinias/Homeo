#!/usr/bin/env python3
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

"""run_phototaxis_comparison.py — Launch the 3 phototaxis experiments concurrently.

  Exp 1: standalone Ashby (discrete uniselector)
  Exp 2: standalone continuous uniselector
  Exp 3: GA + continuous uniselector, 16-gene genome (4 units x 4 params), the _v2 setup
The genome has no dt_fast gene: dt_fast is a rescaling of mass and viscosity,
which the _v2 setup evolves.

Console shows only generation/completion summaries.
Full verbose output is saved to per-experiment log files.

Usage:
    python run_phototaxis_comparison.py                  # orchestrate all 3
    python run_phototaxis_comparison.py --exp 1          # run experiment 1 only
    python run_phototaxis_comparison.py --exp 3 --workers 4
"""

import sys
import os
import time

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
        light_intensity=100, quiet=True, uniselector_type='ashby')
    print("PROGRESS: Exp 1 concluded — final_dist=%.4f, min_dist=%.4f (t=%d)" % (
        result['final_dist'], result['min_dist'], result['min_t']), flush=True)


def run_exp2():
    """Exp 2: Standalone continuous uniselector."""
    from HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_Ashby import run_headless

    print("PROGRESS: Exp 2 started — Standalone OU, 60k steps", flush=True)
    result = run_headless(
        topology='fixed', total_steps=60000, report_interval=500,
        light_intensity=100, quiet=True, uniselector_type='continuous')
    print("PROGRESS: Exp 2 concluded — final_dist=%.4f, min_dist=%.4f (t=%d)" % (
        result['final_dist'], result['min_dist'], result['min_t']), flush=True)


def run_ga_experiment(exp_num, exp_name, n_workers, seed):
    """Run a GA experiment with progress callback.

    All verbose GA output (mating, population lists, per-individual
    evaluation times) goes to stdout — the orchestrator captures it to
    a log file.  Only PROGRESS: lines reach the console.
    """
    from Simulator.HomeoGenAlg import HomeoGASimulation

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
    """Exp 3: GA + continuous uniselector, 16-gene genome (mass and viscosity log-uniform)."""
    run_ga_experiment(3,
        "initializeBraiten2_2_Full_GA_continuous_weightfree_fixed_v2",
        n_workers, seed=42)


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
    }
    runners[exp_num]()


# ---------------------------------------------------------------------------
# Orchestrator (default mode)
# ---------------------------------------------------------------------------

def orchestrate():
    timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')
    from Helpers.General_Helper_Functions import simulations_data_dir
    from Helpers.ExperimentOrchestrator import run_concurrently
    log_dir = os.path.join(simulations_data_dir(),
                           'phototaxis-comparison-' + timestamp)
    os.makedirs(log_dir, exist_ok=True)

    n_cores = os.cpu_count() or 8
    # 2 standalone experiments are single-process and fast; the GA gets
    # the remaining cores.
    workers_per_ga = max(1, n_cores - 2)

    print("=" * 60)
    print("  Phototaxis Comparison: 3 Experiments")
    print("=" * 60)
    print("  Log directory : %s" % os.path.abspath(log_dir))
    print("  CPU cores     : %d" % n_cores)
    print("  GA workers    : %d per experiment" % workers_per_ga)
    print("=" * 60)
    print()

    exp_labels = {
        1: 'Standalone Ashby',
        2: 'Standalone OU',
        3: 'GA+OU (16 genes)',
    }

    commands = {exp_num: [sys.executable, os.path.abspath(__file__),
                          '--exp', str(exp_num), '--workers', str(workers_per_ga)]
                for exp_num in [1, 2, 3]}
    run_concurrently(commands, exp_labels, log_dir, SRC_DIR, label_width=35)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    "The command line's options (see the module docstring); unknown ones are refused."
    import argparse
    parser = argparse.ArgumentParser(
        description='The three phototaxis experiments (see the module docstring).')
    parser.add_argument('--exp', type=int, choices=[1, 2, 3],
                        help='run this experiment in this process (default: orchestrate)')
    parser.add_argument('--workers', type=int, default=3,
                        help='GA worker processes for experiment 3 (default 3)')
    return parser.parse_args(argv)


if __name__ == '__main__':
    args = parse_args()
    if args.exp is not None:
        run_single(args.exp, args.workers)
    else:
        orchestrate()
