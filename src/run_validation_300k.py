#!/usr/bin/env python3
"""run_validation_300k.py — Run best individuals from all 4 experiments for 300k steps.

Exp 1 & 2: Restore homeostat from saved final JSON state (weights + params).
Exp 3 & 4: Replay best GA genome with fresh OU weight discovery.

Usage:
    python run_validation_300k.py                  # orchestrate all 4
    python run_validation_300k.py --exp 1          # run experiment 1 only
    python run_validation_300k.py --steps 500000   # override step count
"""

import sys
import os
import subprocess
import threading
import time
import datetime
import json
import math

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SRC_DIR)

# Saved JSON condition files from the original 60k runs
EXP1_JSON = os.path.join(PROJECT_ROOT, 'SimulationsData', 'SimsData-2026-02-27',
    'phototaxis_braitenberg2_Ashby_fixed_dark-2026-02-27-00-39-03.json')
EXP2_JSON = os.path.join(PROJECT_ROOT, 'SimulationsData', 'SimsData-2026-02-27',
    'phototaxis_braitenberg2_Ashby_fixed_dark_continuous-2026-02-27-00-39-03.json')

# Best genomes from GA experiments (raw [0,1) values)
EXP3_GENOME = [0.591, 0.481, 0.608, 0.309, 0.824, 0.955,
               0.333, 0.398, 0.636, 0.325, 0.686, 0.798,
               0.822, 0.687, 0.114, 0.452]
EXP3_ID = '020-065'

EXP4_GENOME = [0.551, 0.303, 0.489, 0.762, 0.314, 0.820,
               0.818, 0.245, 0.381, 0.597, 0.797, 0.765,
               0.930, 0.502, 0.752, 0.770, 0.722, 0.437,
               0.537, 0.153]
EXP4_ID = '013-039'

DEFAULT_STEPS = 300000
REPORT_INTERVAL = 10000


# ---------------------------------------------------------------------------
# Restore homeostat weights from saved JSON
# ---------------------------------------------------------------------------

def restore_from_json(homeostat, json_path):
    """Restore connection weights and unit parameters from a saved JSON file.

    Reads the FINAL CONDITIONS snapshot and applies it to the homeostat,
    matching units by name and connections by (unit, from) pair.
    """
    with open(json_path, 'r') as f:
        data = json.load(f)

    final = data['FINAL CONDITIONS']

    # Build lookup for units by name
    unit_data = {u['name']: u for u in final['units']}

    for unit in homeostat.homeoUnits:
        if unit.name not in unit_data:
            continue
        saved = unit_data[unit.name]
        unit.criticalDeviation = saved['criticalDeviation']
        unit.currentOutput = saved['currentOutput']
        unit.potentiometer = saved['potentiometer']
        unit.switch = saved['switch']

    # Build lookup for connections by (unit, from)
    conn_data = {}
    for c in final['connections']:
        conn_data[(c['unit'], c['from'])] = c

    for unit in homeostat.homeoUnits:
        for conn in unit.inputConnections:
            key = (unit.name, conn.incomingUnit.name)
            if key in conn_data:
                saved = conn_data[key]
                # newWeight() takes a signed value in [-1, 1]
                signed_weight = saved['weight'] * saved['switch']
                conn.newWeight(signed_weight)


# ---------------------------------------------------------------------------
# Standalone experiment runners (Exp 1 & 2)
# ---------------------------------------------------------------------------

def run_standalone(exp_num, uniselector_type, json_path, total_steps,
                   state_log=False, state_log_interval=100):
    """Run a standalone experiment with weights restored from JSON."""
    from HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_Ashby import setup_phototaxis
    from Helpers.HomeostatConditionLogger import (
        log_homeostat_conditions, log_homeostat_conditions_json)

    label = 'Ashby' if uniselector_type == 'ashby' else 'OU'
    print("PROGRESS: Exp %d started — Standalone %s (restored weights), %dk steps" % (
        exp_num, label, total_steps // 1000), flush=True)

    hom, backend = setup_phototaxis(
        topology='fixed', light_intensity=-100,
        uniselector_type=uniselector_type)

    # Restore final weights from original 60k run
    restore_from_json(hom, json_path)

    # Headless optimizations
    hom.slowingFactor = 0
    hom.collectsData = False
    hom._headless = True
    for u in hom.homeoUnits:
        u._headless = True

    sim = backend.kheperaSimulation
    robot = sim.allBodies['Khepera']
    target_pos = (7, 7)

    # Log initial conditions
    timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")
    log_dir = sim.dataDir
    exp_name = sim.experimentName + '-validation-300k'
    log_path = os.path.join(log_dir, exp_name + '-' + timestamp + '.log')
    json_log_path = os.path.join(log_dir, exp_name + '-' + timestamp + '.json')
    log_homeostat_conditions(hom, log_path, 'INITIAL CONDITIONS (restored)', exp_name)
    log_homeostat_conditions_json(hom, json_log_path, 'INITIAL CONDITIONS (restored)', exp_name)

    # Optional per-tick state logger
    if state_log:
        from Helpers.HomeostatStateLogger import HomeostatStateLogger
        state_log_path = os.path.join(log_dir, exp_name + '-' + timestamp + '.statelog')
        state_logger = HomeostatStateLogger(
            hom, sim, state_log_path, log_interval=state_log_interval)
        hom._state_logger = state_logger

    def dist_to_target():
        rx, ry = robot.body.position[0], robot.body.position[1]
        return math.sqrt((rx - target_pos[0])**2 + (ry - target_pos[1])**2)

    min_dist = dist_to_target()
    min_t = 0

    for target_tick in range(REPORT_INTERVAL, total_steps + 1, REPORT_INTERVAL):
        hom.runFor(target_tick)
        d = dist_to_target()
        if d < min_dist:
            min_dist = d
            min_t = target_tick
        print("PROGRESS: Exp %d t=%d/%d dist=%.3f min_dist=%.3f (t=%d)" % (
            exp_num, target_tick, total_steps, d, min_dist, min_t), flush=True)

    final_dist = dist_to_target()
    sim.saveTrajectory()

    # Close state logger if active
    if state_log and hom._state_logger is not None:
        hom._state_logger.close()
        hom._state_logger = None

    # Log final conditions
    log_homeostat_conditions(hom, log_path, 'FINAL CONDITIONS')
    log_homeostat_conditions_json(hom, json_log_path, 'FINAL CONDITIONS')

    print("PROGRESS: Exp %d finished — final_dist=%.4f, min_dist=%.4f (t=%d)" % (
        exp_num, final_dist, min_dist, min_t), flush=True)


# ---------------------------------------------------------------------------
# GA genome replay runners (Exp 3 & 4)
# ---------------------------------------------------------------------------

def run_ga_replay(exp_num, experiment_name, genome_raw, genome_id, total_steps,
                  state_log=False, state_log_interval=100):
    """Replay a GA genome for an extended run."""
    from deap import base, creator
    from Simulator.SimulatorBackend import SimulatorBackendHOMEO
    from Simulator.HomeoQtSimulation import HomeoQtSimulation

    label = '16-gene fixed-dt' if len(genome_raw) == 16 else '20-gene variable-dt'
    print("PROGRESS: Exp %d started — GA replay %s (ID %s), %dk steps" % (
        exp_num, label, genome_id, total_steps // 1000), flush=True)

    # Create DEAP Individual
    if not hasattr(creator, 'FitnessMin'):
        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    if not hasattr(creator, 'Individual'):
        creator.create("Individual", list, fitness=creator.FitnessMin, ID=None)
    genome = creator.Individual(genome_raw)
    genome.ID = genome_id

    # Set up data directory
    sims_root = os.path.join(PROJECT_ROOT, 'SimulationsData')
    log_dir = os.path.join(sims_root, 'SimsData-' + time.strftime("%Y-%m-%d"))
    os.makedirs(log_dir, exist_ok=True)

    # Create backend and simulation (following _evaluate_genome_worker pattern)
    backend = SimulatorBackendHOMEO(robotName='Khepera', lock=None)
    backend.setDataDir(log_dir)

    sim = HomeoQtSimulation(experiment=experiment_name, dataDir=log_dir)
    sim.maxRuns = total_steps

    params = {
        'homeoGenome': genome,
        'backendSimulator': backend,
    }

    sim.initializeExperSetup(
        message="Building Homeostat from genome %s" % genome.ID, **params)

    backend.connect()
    backend.reset()
    sim.initializeExperSetup(
        message="Rebuilding world after reset", **params)
    backend.close()
    backend.connect()

    backend.setRobotModel(genome.ID)
    sim.homeostat.connectUnitsToNetwork()
    sim.maxRuns = total_steps
    sim.initializeLiveData()

    # Headless optimizations
    hom = sim.homeostat
    hom._headless = True
    hom._collectsData = False
    hom._slowingFactor = 0
    for u in hom.homeoUnits:
        u._headless = True

    # Compute actual tick count (accounting for dt_fast)
    min_dt_fast = 1.0
    for u in hom.homeoUnits:
        dt = getattr(u, '_dt_fast', 1.0)
        if dt < min_dt_fast:
            min_dt_fast = dt
    actual_ticks = int(math.ceil(total_steps / min_dt_fast))

    # Get robot and target for distance tracking
    khep_sim = backend.kheperaSimulation
    robot = khep_sim.allBodies['Khepera']
    target_pos = (7, 7)

    # Optional per-tick state logger
    if state_log:
        from Helpers.HomeostatStateLogger import HomeostatStateLogger
        timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")
        exp_label = experiment_name.replace('initializeBraiten2_2_Full_', '')
        state_log_path = os.path.join(log_dir, exp_label + '-' + genome_id +
                                      '-' + timestamp + '.statelog')
        state_logger = HomeostatStateLogger(
            hom, khep_sim, state_log_path, log_interval=state_log_interval)
        hom._state_logger = state_logger

    def dist_to_target():
        rx, ry = robot.body.position[0], robot.body.position[1]
        return math.sqrt((rx - target_pos[0])**2 + (ry - target_pos[1])**2)

    min_dist = dist_to_target()
    min_t = 0
    next_report = REPORT_INTERVAL

    # Ticks per simulated step depends on dt_fast
    ticks_per_step = 1.0 / min_dt_fast

    for tick in range(actual_ticks):
        sim.step()
        simulated_time = int((tick + 1) * min_dt_fast)

        if simulated_time >= next_report:
            d = dist_to_target()
            if d < min_dist:
                min_dist = d
                min_t = simulated_time
            print("PROGRESS: Exp %d t=%d/%d dist=%.3f min_dist=%.3f (t=%d)" % (
                exp_num, simulated_time, total_steps, d, min_dist, min_t), flush=True)
            next_report += REPORT_INTERVAL

    final_dist = dist_to_target()
    if final_dist < min_dist:
        min_dist = final_dist
        min_t = total_steps

    khep_sim.saveTrajectory()

    # Close state logger if active
    if state_log and hom._state_logger is not None:
        hom._state_logger.close()
        hom._state_logger = None

    print("PROGRESS: Exp %d finished — final_dist=%.4f, min_dist=%.4f (t=%d)" % (
        exp_num, final_dist, min_dist, min_t), flush=True)


# ---------------------------------------------------------------------------
# Individual experiment entry points
# ---------------------------------------------------------------------------

def run_exp1(total_steps):
    run_standalone(1, 'ashby', EXP1_JSON, total_steps)

def run_exp2(total_steps):
    run_standalone(2, 'continuous', EXP2_JSON, total_steps)

def run_exp3(total_steps):
    run_ga_replay(3,
        'initializeBraiten2_2_Full_GA_continuous_weightfree_fixed_dt',
        EXP3_GENOME, EXP3_ID, total_steps)

def run_exp4(total_steps):
    run_ga_replay(4,
        'initializeBraiten2_2_Full_GA_continuous_weightfree_fixed',
        EXP4_GENOME, EXP4_ID, total_steps)


# ---------------------------------------------------------------------------
# Subprocess entry point (--exp N)
# ---------------------------------------------------------------------------

def run_single(exp_num, total_steps):
    os.chdir(SRC_DIR)
    if SRC_DIR not in sys.path:
        sys.path.insert(0, SRC_DIR)

    runners = {
        1: run_exp1,
        2: run_exp2,
        3: run_exp3,
        4: run_exp4,
    }
    runners[exp_num](total_steps)


# ---------------------------------------------------------------------------
# Orchestrator (default mode)
# ---------------------------------------------------------------------------

def orchestrate(total_steps):
    timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')
    log_dir = os.path.join(SRC_DIR, '..', 'SimulationsData',
                           'validation-300k-' + timestamp)
    os.makedirs(log_dir, exist_ok=True)

    print("=" * 60)
    print("  Validation: 4 Experiments x %dk Steps" % (total_steps // 1000))
    print("=" * 60)
    print("  Log directory : %s" % os.path.abspath(log_dir))
    print("=" * 60)
    print()

    exp_labels = {
        1: 'Standalone Ashby (restored weights)',
        2: 'Standalone OU (restored weights)',
        3: 'GA+OU fixed dt, genome 020-065',
        4: 'GA+OU variable dt, genome 013-039',
    }

    # Launch all 4 as subprocesses
    procs = {}
    for exp_num in [1, 2, 3, 4]:
        cmd = [sys.executable, os.path.abspath(__file__),
               '--exp', str(exp_num), '--steps', str(total_steps)]
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

    for t in threads:
        t.join()

    print()
    print("=" * 60)
    print("  All experiments complete")
    print("=" * 60)
    for exp_num, (proc, _, log_path) in procs.items():
        status = "OK" if proc.returncode == 0 else "FAILED (exit %d)" % proc.returncode
        print("  Exp %d %-40s %s" % (exp_num, exp_labels[exp_num], status))
    print()
    print("  Detailed logs: %s" % os.path.abspath(log_dir))
    print("=" * 60)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    total_steps = DEFAULT_STEPS
    if '--steps' in sys.argv:
        total_steps = int(sys.argv[sys.argv.index('--steps') + 1])

    if '--exp' in sys.argv:
        exp_num = int(sys.argv[sys.argv.index('--exp') + 1])
        run_single(exp_num, total_steps)
    else:
        orchestrate(total_steps)
