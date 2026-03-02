#!/usr/bin/env python3
"""Replay the best individual from a GA logbook with per-tick state logging.

Loads a genome from a DEAP logbook pickle, constructs the homeostat + robot
simulator, runs the simulation, and writes a .statelog file suitable for
analysis with Helpers.StatelogAnalyzer.

The experiment type (2-unit vs 4-unit, continuous vs discrete, weight-free
vs classic) is auto-detected from the logbook metadata.  The --exp flag
can override the auto-detection for old logbooks without metadata.

Usage:
    cd src
    python replay_best_with_statelog.py --logbook path.lgb
    python replay_best_with_statelog.py --logbook path.lgb --indiv 016-014
    python replay_best_with_statelog.py --logbook path.lgb --visualize
    python replay_best_with_statelog.py --logbook path.lgb --ashby --steps 100000
"""

import os
import sys
import math
import pickle
import time
import threading
import argparse
import numpy as np
from math import sqrt

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SRC_DIR)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from Helpers.General_Helper_Functions import simulations_data_dir
from Simulator.SimulatorBackend import SimulatorBackendHOMEO
from Helpers.HomeostatStateLogger import HomeostatStateLogger

DEFAULT_LOGBOOK = os.path.join(
    simulations_data_dir(),
    'SimsData-2026-03-01-18-21-08',
    'Logbook-2026-03-01-18-21-08.lgb')
DEFAULT_STEPS = 60000

# ── Map logbook metadata 'exp' strings to importable function names ──────
# All live in Simulator.HomeoExperiments.
_EXP_FUNC_MAP = {
    # Classic 4+2 vehicle (6 units, 4 evolved, 40-gene genome)
    'initializeBraiten2_2_Full_GA_phototaxis':
        'initializeBraiten2_2_Full_GA_phototaxis',
    'initializeBraiten2_2_Full_GA_phototaxis_continuous':
        'initializeBraiten2_2_Full_GA_phototaxis_continuous',

    # Weight-free 4+2 vehicle (6 units, 4 evolved)
    'initializeBraiten2_2_Full_GA_continuous_weightfree':
        'initializeBraiten2_2_Full_GA_continuous_weightfree',
    'initializeBraiten2_2_Full_GA_continuous_weightfree_fixed':
        'initializeBraiten2_2_Full_GA_continuous_weightfree_fixed',
    'initializeBraiten2_2_Full_GA_continuous_weightfree_fixed_dt':
        'initializeBraiten2_2_Full_GA_continuous_weightfree_fixed_dt',

    # Weight-free 2+2 direct vehicle (4 units, 2 evolved)
    'initializeBraiten2_direct_GA_continuous_weightfree':
        'initializeBraiten2_direct_GA_continuous_weightfree',
    'initializeBraiten2_direct_GA_continuous_weightfree_fixed':
        'initializeBraiten2_direct_GA_continuous_weightfree_fixed',
    'initializeBraiten2_direct_GA_continuous_weightfree_fixed_dt':
        'initializeBraiten2_direct_GA_continuous_weightfree_fixed_dt',

    # Classic full GA variants
    'initializeBraiten2_2_Full_GA':
        'initializeBraiten2_2_Full_GA',
    'initializeBraiten2_2_Full_GA_scototaxis':
        'initializeBraiten2_2_Full_GA_scototaxis',
}


def _get_logbook_metadata(logbook):
    """Extract the metadata record from a DEAP logbook (last record with 'exp' but no 'genome')."""
    for rec in reversed(logbook):
        if 'exp' in rec and 'genome' not in rec:
            return rec
    return None


def resolve_experiment_func(logbook, exp_override=None):
    """Determine the experiment function from logbook metadata or --exp override.

    Returns (func, exp_name, metadata_dict_or_None).
    """
    import Simulator.HomeoExperiments as HE

    meta = _get_logbook_metadata(logbook)

    if exp_override is not None:
        # Legacy --exp flag: 1 = fixed dt 2+2, 2 = variable dt 2+2
        if exp_override == 1:
            name = 'initializeBraiten2_direct_GA_continuous_weightfree_fixed_dt'
        elif exp_override == 2:
            name = 'initializeBraiten2_direct_GA_continuous_weightfree_fixed'
        else:
            raise ValueError("Unknown --exp value: %d" % exp_override)
        return getattr(HE, name), name, meta

    if meta is None:
        raise RuntimeError(
            "Logbook has no metadata record.  Use --exp to specify the "
            "experiment type manually (1=fixed dt 2+2, 2=variable dt 2+2).")

    exp_name = meta['exp']
    if exp_name not in _EXP_FUNC_MAP:
        raise RuntimeError(
            "Unknown experiment '%s' in logbook metadata.  Known types:\n  %s"
            % (exp_name, '\n  '.join(sorted(_EXP_FUNC_MAP))))

    func_name = _EXP_FUNC_MAP[exp_name]
    return getattr(HE, func_name), exp_name, meta


def find_best_individual(logbook, indiv_id=None):
    """Find the best (or a specific) individual in a DEAP logbook."""
    if indiv_id:
        for rec in logbook:
            if rec.get('indivId') == indiv_id:
                return rec
        raise ValueError("Individual %s not found in logbook" % indiv_id)

    best = None
    for rec in logbook:
        if 'fitness' not in rec:
            continue
        f = rec['fitness'][0]
        if best is None or f < best['fitness'][0]:
            best = rec
    return best


def _build_homeostat(genome, experiment_func, seed, backend, data_dir, use_ashby):
    """Build the homeostat from a genome, mirroring the GA evaluation sequence.

    Returns the configured Homeostat instance.
    """
    # Build homeostat (first pass — pre-reset)
    np.random.seed(seed)
    hom = experiment_func(
        homeoGenome=genome,
        backendSimulator=backend,
        dataDir=data_dir)

    # Reset world
    backend.reset()

    # Rebuild homeostat (post-reset, as the GA does)
    np.random.seed(seed)
    hom = experiment_func(
        homeoGenome=genome,
        backendSimulator=backend,
        dataDir=data_dir)

    # (optional) Swap OU uniselectors for Ashby discrete ones
    if use_ashby:
        from Core.HomeoUniselectorAshby import HomeoUniselectorAshby
        from Core.HomeoUniselectorContinuous import HomeoUniselectorContinuous
        for u in hom.homeoUnits:
            if isinstance(getattr(u, 'uniselector', None),
                          HomeoUniselectorContinuous):
                unis = HomeoUniselectorAshby()
                u.uniselector = unis
                print("  Swapped %s uniselector -> Ashby discrete" % u.name)

    return hom


def replay(genome, steps, experiment_func, seed, output_path, log_interval=1,
           use_ashby=False, model_name=None):
    """Replay a genome headless and write a .statelog file."""

    data_dir = os.path.dirname(output_path)

    # Create backend and start world
    lock = threading.Lock()
    backend = SimulatorBackendHOMEO(lock=lock, robotName='Khepera')
    backend.start('kheperaBraitenberg2_HOMEO_World')
    backend.setDataDir(data_dir)

    hom = _build_homeostat(genome, experiment_func, seed, backend, data_dir, use_ashby)

    # Label the robot model so .traj files get a meaningful name
    if model_name:
        backend.setRobotModel(model_name)

    # Enable headless mode (same as GA)
    hom._headless = True
    hom._collectsData = False
    hom._slowingFactor = 0
    for u in hom.homeoUnits:
        u._headless = True

    # Connect units
    hom.connectUnitsToNetwork()

    # Compute tick count based on dt_fast
    min_dt_fast = 1.0
    for u in hom.homeoUnits:
        dt = getattr(u, '_dt_fast', 1.0)
        if dt < min_dt_fast:
            min_dt_fast = dt
    actual_ticks = int(math.ceil(steps / min_dt_fast))

    # Run one tick so JIT arrays get created (headless mode initialises them
    # lazily on the first selfUpdate).  The logger constructor inspects
    # _jit_incoming_units to decide whether to read weights from JIT arrays
    # vs Connection objects, so we must do this before constructing it.
    hom.runOnce()

    # Attach state logger (after JIT init)
    logger = HomeostatStateLogger(
        hom, backend.kheperaSimulation, output_path,
        log_interval=log_interval,
        target_pos=(7, 7),
        seed=seed)

    print("Running %d ticks (%d sim-seconds, min_dt=%.2f) ..." % (
        actual_ticks, steps, min_dt_fast))
    t0 = time.time()

    # Log tick 1 (which we already ran above)
    logger.log_tick(1)

    for tick in range(2, actual_ticks + 1):
        hom.runOnce()
        logger.log_tick(tick)
        if tick % 10000 == 0:
            elapsed = time.time() - t0
            logger.flush()
            print("  tick %d/%d  (%.1fs elapsed)" % (tick, actual_ticks, elapsed))

    logger.close()
    elapsed = time.time() - t0

    final_dist = backend.finalDisFromTarget()
    print("Done in %.1fs.  Final distance: %.4f" % (elapsed, final_dist))
    print("Statelog written to: %s" % output_path)
    return final_dist


def replay_visualized(genome, experiment_func, seed, data_dir,
                      use_ashby=False, model_name=None):
    """Replay a genome with the pyglet visualizer.

    Press Q or Escape to close.  Up/Down arrows adjust simulation speed.
    """
    import pyglet
    from pyglet.gl import (glEnable, glBlendFunc, glHint, glClearColor, glClear,
                           GL_BLEND, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
                           GL_LINE_SMOOTH, GL_LINE_SMOOTH_HINT, GL_NICEST,
                           GL_COLOR_BUFFER_BIT, GL_LINES)
    from KheperaSimulator.KheperaSimulator import KheperaCamera, _get_shape_program

    unisel_tag = 'Ashby' if use_ashby else 'OU'
    caption_prefix = 'Replay %s (%s)' % (model_name or '', unisel_tag)

    # Create the pyglet window BEFORE the backend, so the GL context exists
    # when KheperaSimulator creates pyglet shapes for bodies.
    window = pyglet.window.Window(width=800, height=600, resizable=True,
                                  caption=caption_prefix)
    glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glClearColor(0.55, 0.95, 1.0, 1.0)

    lock = threading.Lock()
    backend = SimulatorBackendHOMEO(lock=lock, robotName='Khepera')
    backend.start('kheperaBraitenberg2_HOMEO_World')
    backend.setDataDir(data_dir)

    hom = _build_homeostat(genome, experiment_func, seed, backend, data_dir, use_ashby)

    if model_name:
        backend.setRobotModel(model_name)

    # Non-headless: keep normal Python objects for Connection weights
    # (no JIT) so the simulation matches the visualized state exactly.
    hom._collectsData = False
    hom._slowingFactor = 0

    hom.connectUnitsToNetwork()

    sim = backend.kheperaSimulation
    robot = sim.allBodies['Khepera']
    target_pos = sim.allBodies['TARGET'].position

    camera = KheperaCamera(position=(5.5, 5.5), zoom=8.0)
    state = [0, 5]             # [cumulative_tick, ticks_per_frame]
    trail_vlists = []
    trail_last = [None]
    TRAIL_MIN_DIST = 0.05

    @window.event
    def on_draw():
        glClear(GL_COLOR_BUFFER_BIT)
        camera.focus(window)
        sim.pygletDraw()
        program = _get_shape_program()
        program.use()
        for vl in trail_vlists:
            vl.draw(GL_LINES)
        program.stop()

    def update(dt):
        state[0] += state[1]
        hom.runFor(state[0])
        rx, ry = robot.body.position[0], robot.body.position[1]

        # Trail segment
        if trail_last[0] is not None:
            px, py = trail_last[0]
            if sqrt((rx - px)**2 + (ry - py)**2) >= TRAIL_MIN_DIST:
                program = _get_shape_program()
                vl = program.vertex_list(
                    2, GL_LINES,
                    position=('f', [px, py, rx, ry]),
                    colors=('f', [0.8, 0.2, 0.2, 0.7] * 2),
                    translation=('f', [0.0, 0.0] * 2),
                    rotation=('f', [0.0] * 2),
                    zposition=('f', [0.0] * 2),
                )
                trail_vlists.append(vl)
                trail_last[0] = (rx, ry)
        else:
            trail_last[0] = (rx, ry)

        dist = sqrt((rx - target_pos[0])**2 + (ry - target_pos[1])**2)
        window.set_caption(
            '%s - t=%d  speed=%d  dist=%.2f  [%.0f fps]'
            % (caption_prefix, state[0], state[1], dist, 1 / max(dt, 0.001)))

    @window.event
    def on_key_press(symbol, modifiers):
        if symbol in (pyglet.window.key.ESCAPE, pyglet.window.key.Q):
            window.close()
        elif symbol == pyglet.window.key.UP:
            state[1] = min(state[1] * 2, 200)
        elif symbol == pyglet.window.key.DOWN:
            state[1] = max(state[1] // 2, 1)

    @window.event
    def on_close():
        sim.saveTrajectory()

    pyglet.clock.schedule(update)
    pyglet.app.run()


def main():
    parser = argparse.ArgumentParser(
        description='Replay a GA individual with per-tick state logging or visualization.')
    parser.add_argument('--logbook', default=DEFAULT_LOGBOOK,
                        help='Path to DEAP logbook pickle (.lgb)')
    parser.add_argument('--indiv', default=None,
                        help='Individual ID to replay (default: best)')
    parser.add_argument('--steps', type=int, default=DEFAULT_STEPS,
                        help='Simulation steps (sim-seconds, default %d)' % DEFAULT_STEPS)
    parser.add_argument('--seed', type=int, default=45,
                        help='RNG seed (default: 45)')
    parser.add_argument('--output', '-o', default=None,
                        help='Output .statelog path (default: auto-generated)')
    parser.add_argument('--log-interval', type=int, default=1,
                        help='Log every N-th tick (default: 1)')
    parser.add_argument('--exp', type=int, default=None, choices=[1, 2],
                        help='Override experiment type (legacy: 1=fixed dt 2+2, '
                             '2=variable dt 2+2).  Normally auto-detected from logbook.')
    parser.add_argument('--ashby', action='store_true',
                        help='Replace OU continuous uniselectors with Ashby discrete ones')
    parser.add_argument('--visualize', action='store_true',
                        help='Run with pyglet visualizer instead of headless')
    args = parser.parse_args()

    # Load logbook
    print("Loading logbook: %s" % args.logbook)
    with open(args.logbook, 'rb') as f:
        logbook = pickle.load(f)
    print("  %d records" % len(logbook))

    # Resolve experiment function (auto-detect or --exp override)
    exp_func, exp_name, meta = resolve_experiment_func(logbook, args.exp)
    if meta:
        print("  Experiment: %s  (%d units, %d evolved, genome size %d)"
              % (exp_name, meta.get('noUnits', '?'), meta.get('noEvolvedUnits', '?'),
                 meta.get('genomeSize', '?')))
    else:
        print("  Experiment: %s  (no metadata, using --exp override)" % exp_name)

    # Find individual
    rec = find_best_individual(logbook, args.indiv)
    genome = rec['genome']
    indiv_id = rec['indivId']
    fitness = rec['fitness'][0]
    print("  Individual: %s  fitness: %.5f  genome: %s" % (
        indiv_id, fitness, [round(g, 4) for g in genome]))

    # Build a descriptive model name for the .traj file
    unisel_tag = 'ashby' if args.ashby else 'OU'
    model_name = 'replay-%s-%s-s%d' % (indiv_id, unisel_tag, args.seed)

    if args.visualize:
        # Output dir for trajectory files
        timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')
        data_dir = os.path.join(simulations_data_dir(),
                                'replay-%s' % timestamp)
        os.makedirs(data_dir, exist_ok=True)
        replay_visualized(genome, exp_func, args.seed, data_dir,
                          use_ashby=args.ashby, model_name=model_name)
    else:
        # Output path for statelog
        if args.output:
            output_path = args.output
        else:
            timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')
            output_dir = os.path.join(simulations_data_dir(),
                                      'replay-%s' % timestamp)
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir,
                                       'replay-%s-%dk.statelog' % (indiv_id, args.steps // 1000))

        replay(genome, args.steps, exp_func, args.seed, output_path,
               log_interval=args.log_interval, use_ashby=args.ashby,
               model_name=model_name)


if __name__ == '__main__':
    main()
