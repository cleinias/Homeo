#!/usr/bin/env python3
"""run_direct_vehicle_ga.py — GA experiments for the simplified 2+2 direct vehicle.

Runs a GA experiment on the 4-unit Braitenberg-2 vehicle (2 sensors + 2
motors, no eye intermediaries):

  Exp 1: GA + OU, 8-gene genome (2 units x 4 params), the _v2 setup: mass and
         viscosity log-uniform

with fixed Braitenberg cross-wiring (Left Sensor -> Right Motor, Right
Sensor -> Left Motor) and negative motor self-connections.  Exp 2 (an
evolvable dt_fast, 10 genes) was retired on 15 Oct 2026: dt_fast is a
rescaling of mass and viscosity, which the _v2 setup evolves over the ranges
dt_fast reached (review finding CU-11).

Usage:
    python run_direct_vehicle_ga.py                  # orchestrate (all cores)
    python run_direct_vehicle_ga.py --exp 1 --workers 4
    python run_direct_vehicle_ga.py --pop 150 --gen 50   # override defaults
    python run_direct_vehicle_ga.py --noise-scheme genome
                                    # how evaluations get their noise: individual
                                    # (default), genome or generation -- see
                                    # NOISE_SCHEMES in Simulator/HomeoGenAlg.py
"""

import sys
import os
import time

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SRC_DIR)
from Helpers.General_Helper_Functions import simulations_data_dir
from Helpers.ExperimentOrchestrator import run_concurrently
SIMS_DATA = simulations_data_dir()

# Default GA parameters
DEFAULT_POP_SIZE = 150
DEFAULT_GENERATIONS = 50
DEFAULT_STEPS = 60000
DEFAULT_NOISE_SCHEME = 'individual'


# ---------------------------------------------------------------------------
# Single-experiment runners (called in subprocess via --exp N)
# ---------------------------------------------------------------------------

def run_ga_experiment(exp_num, exp_name, n_workers, seed,
                      pop_size=DEFAULT_POP_SIZE, generations=DEFAULT_GENERATIONS,
                      steps=DEFAULT_STEPS, noise_scheme=DEFAULT_NOISE_SCHEME):
    """Run a GA experiment with progress callback."""
    from Simulator.HomeoGenAlg import HomeoGASimulation

    # Point data directory to Cybernetics-research
    HomeoGASimulation.dataDirRoot = SIMS_DATA

    def progress(gen, record, best_fitness):
        print("PROGRESS: Generation %d/%d of Exp %d — best=%.4f, avg=%.4f" % (
            gen, generations, exp_num, best_fitness, record['avg']), flush=True)

    ga = HomeoGASimulation(
        stepsSize=steps, popSize=pop_size, generSize=generations,
        exp=exp_name, simulatorBackend="HOMEO", nWorkers=n_workers,
        noiseScheme=noise_scheme)

    print("PROGRESS: Exp %d started — %s (%d pop x %d gen, %d workers, seed %d, noise %s)" % (
        exp_num, exp_name, pop_size, generations, n_workers, seed, noise_scheme), flush=True)

    pop = ga.generateRandomPop(randomSeed=seed)
    ga.runGaSimulation(pop, progressCallback=progress)

    print("PROGRESS: Exp %d finished — best=%.4f" % (
        exp_num, ga.hof[0].fitness.values[0]), flush=True)


def run_exp1(n_workers, pop_size=DEFAULT_POP_SIZE, generations=DEFAULT_GENERATIONS,
             steps=DEFAULT_STEPS, noise_scheme=DEFAULT_NOISE_SCHEME):
    """Exp 1: Direct 2+2, GA + OU, 8-gene genome (mass and viscosity log-uniform)."""
    run_ga_experiment(1,
        "initializeBraiten2_direct_GA_continuous_weightfree_fixed_v2",
        n_workers, seed=44, pop_size=pop_size, generations=generations,
        steps=steps, noise_scheme=noise_scheme)


# ---------------------------------------------------------------------------
# Subprocess entry point (--exp N)
# ---------------------------------------------------------------------------

def run_single(exp_num, n_workers, pop_size, generations, steps,
               noise_scheme=DEFAULT_NOISE_SCHEME):
    os.chdir(SRC_DIR)
    if SRC_DIR not in sys.path:
        sys.path.insert(0, SRC_DIR)

    runners = {
        1: run_exp1,
    }
    runners[exp_num](n_workers, pop_size=pop_size, generations=generations,
                     steps=steps, noise_scheme=noise_scheme)


# ---------------------------------------------------------------------------
# Orchestrator (default mode)
# ---------------------------------------------------------------------------

def orchestrate(pop_size=DEFAULT_POP_SIZE, generations=DEFAULT_GENERATIONS,
                steps=DEFAULT_STEPS, noise_scheme=DEFAULT_NOISE_SCHEME):
    timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')
    log_dir = os.path.join(SIMS_DATA,
                           'direct-vehicle-ga-' + timestamp)
    os.makedirs(log_dir, exist_ok=True)

    n_cores = os.cpu_count() or 8
    workers_per_ga = n_cores

    print("=" * 60)
    print("  Direct 2+2 Vehicle: GA Experiments")
    print("=" * 60)
    print("  Population   : %d" % pop_size)
    print("  Generations  : %d" % generations)
    print("  Steps/indiv  : %d" % steps)
    print("  Noise scheme : %s" % noise_scheme)
    print("  Log directory: %s" % os.path.abspath(log_dir))
    print("  CPU cores    : %d" % n_cores)
    print("  GA workers   : %d per experiment" % workers_per_ga)
    print("=" * 60)
    print()

    exp_labels = {
        1: 'GA+OU (8 genes)',
    }

    commands = {exp_num: [sys.executable, os.path.abspath(__file__),
                          '--exp', str(exp_num),
                          '--workers', str(workers_per_ga),
                          '--pop', str(pop_size),
                          '--gen', str(generations),
                          '--steps', str(steps),
                          '--noise-scheme', noise_scheme]
                for exp_num in [1]}
    run_concurrently(commands, exp_labels, log_dir, SRC_DIR, label_width=35)


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
    noise_scheme = DEFAULT_NOISE_SCHEME
    if '--noise-scheme' in sys.argv:
        noise_scheme = sys.argv[sys.argv.index('--noise-scheme') + 1]
        from Simulator.HomeoGenAlg import NOISE_SCHEMES
        if noise_scheme not in NOISE_SCHEMES:
            sys.exit("--noise-scheme must be one of %s, got %r"
                     % (', '.join(NOISE_SCHEMES), noise_scheme))

    if '--exp' in sys.argv:
        exp_num = int(sys.argv[sys.argv.index('--exp') + 1])
        workers = 3
        if '--workers' in sys.argv:
            workers = int(sys.argv[sys.argv.index('--workers') + 1])
        run_single(exp_num, workers, pop_size, generations, steps, noise_scheme)
    else:
        orchestrate(pop_size, generations, steps, noise_scheme)
