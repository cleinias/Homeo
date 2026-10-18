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

"""run_direct_vehicle_ga.py — GA experiments for the simplified 2+2 direct vehicle.

Runs a GA experiment on the 4-unit Braitenberg-2 vehicle (2 sensors + 2
motors, no eye intermediaries):

  Exp 1: GA + continuous uniselector, 8-gene genome (2 units x 4 params), the _v2 setup: mass and
         viscosity log-uniform

with fixed Braitenberg cross-wiring (Left Sensor -> Right Motor, Right
Sensor -> Left Motor) and negative motor self-connections.  The genome has
no dt_fast gene: dt_fast is a rescaling of mass and viscosity, which the
_v2 setup evolves.

Usage:
    python run_direct_vehicle_ga.py                  # orchestrate (all cores)
    python run_direct_vehicle_ga.py --exp 1 --workers 4
    python run_direct_vehicle_ga.py --pop 150 --gen 50   # override defaults
    python run_direct_vehicle_ga.py --noise-scheme genome
                                    # how evaluations get their noise: individual
                                    # (default), genome or generation -- see
                                    # NOISE_SCHEMES in Simulator/HomeoGenAlg.py
    python run_direct_vehicle_ga.py --evals-per-individual 3
                                    # each evaluation the mean of 3 runs (default 1);
                                    # the best 10 of the hall of fame are always
                                    # re-evaluated on 20 seeds at the end
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
DEFAULT_EVALS = 1


# ---------------------------------------------------------------------------
# Single-experiment runners (called in subprocess via --exp N)
# ---------------------------------------------------------------------------

def run_ga_experiment(exp_num, exp_name, n_workers, seed,
                      pop_size=DEFAULT_POP_SIZE, generations=DEFAULT_GENERATIONS,
                      steps=DEFAULT_STEPS, noise_scheme=DEFAULT_NOISE_SCHEME,
                      evals=DEFAULT_EVALS):
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
        noiseScheme=noise_scheme, evalsPerIndividual=evals)

    print("PROGRESS: Exp %d started — %s (%d pop x %d gen, %d workers, seed %d, noise %s, "
          "%d run(s) per evaluation)" % (
        exp_num, exp_name, pop_size, generations, n_workers, seed, noise_scheme, evals), flush=True)

    pop = ga.generateRandomPop(randomSeed=seed)
    ga.runGaSimulation(pop, progressCallback=progress)

    print("PROGRESS: Exp %d finished — best=%.4f" % (
        exp_num, ga.hof[0].fitness.values[0]), flush=True)


def run_exp1(n_workers, pop_size=DEFAULT_POP_SIZE, generations=DEFAULT_GENERATIONS,
             steps=DEFAULT_STEPS, noise_scheme=DEFAULT_NOISE_SCHEME, evals=DEFAULT_EVALS):
    """Exp 1: Direct 2+2, GA + continuous uniselector, 8-gene genome (mass and viscosity log-uniform)."""
    run_ga_experiment(1,
        "initializeBraiten2_direct_GA_continuous_weightfree_fixed_v2",
        n_workers, seed=44, pop_size=pop_size, generations=generations,
        steps=steps, noise_scheme=noise_scheme, evals=evals)


# ---------------------------------------------------------------------------
# Subprocess entry point (--exp N)
# ---------------------------------------------------------------------------

def run_single(exp_num, n_workers, pop_size, generations, steps,
               noise_scheme=DEFAULT_NOISE_SCHEME, evals=DEFAULT_EVALS):
    os.chdir(SRC_DIR)
    if SRC_DIR not in sys.path:
        sys.path.insert(0, SRC_DIR)

    runners = {
        1: run_exp1,
    }
    runners[exp_num](n_workers, pop_size=pop_size, generations=generations,
                     steps=steps, noise_scheme=noise_scheme, evals=evals)


# ---------------------------------------------------------------------------
# Orchestrator (default mode)
# ---------------------------------------------------------------------------

def orchestrate(pop_size=DEFAULT_POP_SIZE, generations=DEFAULT_GENERATIONS,
                steps=DEFAULT_STEPS, noise_scheme=DEFAULT_NOISE_SCHEME, evals=DEFAULT_EVALS):
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
    print("  Runs/eval    : %d" % evals)
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
                          '--noise-scheme', noise_scheme,
                          '--evals-per-individual', str(evals)]
                for exp_num in [1]}
    run_concurrently(commands, exp_labels, log_dir, SRC_DIR, label_width=35)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    "The command line's options (see the module docstring); unknown ones are refused."
    import argparse
    from Simulator.HomeoGenAlg import NOISE_SCHEMES
    parser = argparse.ArgumentParser(
        description='GA experiments for the 2+2 direct vehicle (see the module docstring).')
    parser.add_argument('--exp', type=int, choices=[1],
                        help='run this experiment in this process (default: orchestrate)')
    parser.add_argument('--workers', type=int, default=3,
                        help='GA worker processes with --exp (default 3)')
    parser.add_argument('--pop', type=int, default=DEFAULT_POP_SIZE)
    parser.add_argument('--gen', type=int, default=DEFAULT_GENERATIONS)
    parser.add_argument('--steps', type=int, default=DEFAULT_STEPS)
    parser.add_argument('--noise-scheme', choices=NOISE_SCHEMES, default=DEFAULT_NOISE_SCHEME)
    parser.add_argument('--evals-per-individual', type=int, default=DEFAULT_EVALS,
                        dest='evals')
    args = parser.parse_args(argv)
    if args.evals < 1:
        parser.error('--evals-per-individual must be at least 1')
    return args


if __name__ == '__main__':
    args = parse_args()
    if args.exp is not None:
        run_single(args.exp, args.workers, args.pop, args.gen, args.steps, args.noise_scheme,
                   args.evals)
    else:
        orchestrate(args.pop, args.gen, args.steps, args.noise_scheme, args.evals)
