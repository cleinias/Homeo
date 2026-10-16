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

Reproducing a GA evaluation.  Logbooks written since GA runs became seeded
(October 2026) record each individual's evalSeed.  For those, the replay builds
and runs the homeostat through the GA's own code (prepare_genome_evaluation in
Simulator/HomeoGenAlg.py), seeded with the logged evalSeed, for the logged run
length, and reports whether it reproduced the logged fitness exactly.  --seed
replays the same genome under other noise; --steps runs it for another length.
Older logbooks have no evalSeed: their replay works as it always did (seed 45,
60000 steps by default) and cannot reproduce the logged fitness.  The
visualizer always uses the older path (it runs non-headless, unlike the GA).
"""

import os
import sys
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

    # Classic full GA variants
    'initializeBraiten2_2_Full_GA':
        'initializeBraiten2_2_Full_GA',
    'initializeBraiten2_2_Full_GA_scototaxis':
        'initializeBraiten2_2_Full_GA_scototaxis',

    # The weight-free setups: the 4+2 vehicle (6 units, 4 evolved), the 2+2
    # direct vehicle (4 units, 2 evolved) and Vehicle 3c (10 units, 2 evolved)
    'initializeBraiten2_2_Full_GA_continuous_weightfree_v2':
        'initializeBraiten2_2_Full_GA_continuous_weightfree_v2',
    'initializeBraiten2_2_Full_GA_continuous_weightfree_fixed_v2':
        'initializeBraiten2_2_Full_GA_continuous_weightfree_fixed_v2',
    'initializeBraiten2_direct_GA_continuous_weightfree_v2':
        'initializeBraiten2_direct_GA_continuous_weightfree_v2',
    'initializeBraiten2_direct_GA_continuous_weightfree_fixed_v2':
        'initializeBraiten2_direct_GA_continuous_weightfree_fixed_v2',
    'initializeBraiten3c_GA_continuous_weightfree_fixed_v2':
        'initializeBraiten3c_GA_continuous_weightfree_fixed_v2',
    'initializeBraiten3c_GA_continuous_weightfree_open_v2':
        'initializeBraiten3c_GA_continuous_weightfree_open_v2',
}


def _get_logbook_metadata(logbook):
    """Extract the metadata record from a DEAP logbook (last record with 'exp' but no 'genome')."""
    for rec in reversed(logbook):
        if 'exp' in rec and 'genome' not in rec:
            return rec
    return None


def resolve_experiment_func(logbook):
    """Determine the experiment function from the logbook's metadata.

    Returns (func, exp_name, metadata_dict).
    """
    import Simulator.HomeoExperiments as HE

    meta = _get_logbook_metadata(logbook)
    if meta is None:
        raise RuntimeError("Logbook has no metadata record: its experiment is unknown.")

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


def _build_homeostat(genome, experiment_func, seed, backend, data_dir, use_ashby,
                     light_intensity=None):
    """Build the homeostat from a genome, mirroring the GA evaluation sequence.
    light_intensity: the TARGET's, for setups that take it (see
    HomeoExperiments.loggedLightIntensity).

    Returns the configured Homeostat instance.
    """
    extra = {} if light_intensity is None else {'lightIntensity': light_intensity}
    # Build homeostat (first pass — pre-reset).  Every stream, numba's
    # included, as a GA evaluation seeds them (SH-03).
    from Simulator.HomeoGenAlg import seed_evaluation
    seed_evaluation(seed)
    hom = experiment_func(
        homeoGenome=genome,
        backendSimulator=backend,
        dataDir=data_dir, **extra)

    # Reset world
    backend.reset()

    # Rebuild homeostat (post-reset, as the GA does)
    seed_evaluation(seed)
    hom = experiment_func(
        homeoGenome=genome,
        backendSimulator=backend,
        dataDir=data_dir, **extra)

    # (optional) Swap OU uniselectors for Ashby discrete ones
    if use_ashby:
        _swap_to_ashby(hom)

    return hom


def replay(genome, steps, experiment_func, seed, output_path, log_interval=1,
           use_ashby=False, model_name=None, light_intensity=None):
    """Replay a genome headless and write a .statelog file."""

    data_dir = os.path.dirname(output_path)

    # Create backend and start world
    # The data directory goes to the constructor: start() sets up the world,
    # which opens a trajectory file at once.
    lock = threading.Lock()
    backend = SimulatorBackendHOMEO(lock=lock, robotName='Khepera', dataDir=data_dir)
    backend.start('kheperaBraitenberg2_HOMEO_World')

    hom = _build_homeostat(genome, experiment_func, seed, backend, data_dir, use_ashby,
                           light_intensity)

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

    # steps counts ticks, as the GA's evaluation does (SG-02)
    print("Running %d ticks ..." % steps)
    t0 = time.time()

    # Log tick 1 (which we already ran above)
    logger.log_tick(1)

    for tick in range(2, steps + 1):
        hom.runOnce()
        logger.log_tick(tick)
        if tick % 10000 == 0:
            elapsed = time.time() - t0
            logger.flush()
            print("  tick %d/%d  (%.1fs elapsed)" % (tick, steps, elapsed))

    logger.close()
    backend.kheperaSimulation.saveTrajectory()
    elapsed = time.time() - t0

    final_dist = backend.finalDisFromTarget()
    print("Done in %.1fs.  Final distance: %.4f" % (elapsed, final_dist))
    print("Statelog written to: %s" % output_path)
    return final_dist


class _Genome(list):
    "A genome as the GA evaluates it: the genes, plus the individual's ID."
    def __init__(self, genes, ID):
        super().__init__(genes)
        self.ID = ID


def _swap_to_ashby(hom):
    "Replace OU continuous uniselectors with Ashby discrete ones."
    from Core.HomeoUniselectorAshby import HomeoUniselectorAshby
    from Core.HomeoUniselectorContinuous import HomeoUniselectorContinuous
    for u in hom.homeoUnits:
        if isinstance(getattr(u, 'uniselector', None), HomeoUniselectorContinuous):
            u.uniselector = HomeoUniselectorAshby()
            print("  Swapped %s uniselector -> Ashby discrete" % u.name)


def replay_as_evaluated(genome, indiv_id, exp_name, meta, steps, eval_seed, output_path,
                        log_interval=1, use_ashby=False, model_name=None,
                        light_intensity=None):
    """Replay a genome headless exactly as the GA evaluated it, writing a
       .statelog: the GA's own setup (prepare_genome_evaluation), seeded with
       eval_seed, advanced with the same sim.step() calls.  Returns the final
       distance from the target."""
    from Simulator.HomeoGenAlg import prepare_genome_evaluation, seeded_evaluation

    data_dir = os.path.dirname(output_path)
    params = {'dataDir': data_dir,
              'noNoise': meta.get('noNoise', False),
              'noUnisel': meta.get('noUnisel', False)}
    if light_intensity is not None:
        params['lightIntensity'] = light_intensity
    with seeded_evaluation(eval_seed):
        sim, backend = prepare_genome_evaluation(
            _Genome(genome, indiv_id), exp_name, params, steps, data_dir,
            modelName=model_name,
            adjustHomeostat=_swap_to_ashby if use_ashby else None)
        hom = sim.homeostat

        # Run one tick so JIT arrays get created (headless mode initialises
        # them lazily on the first selfUpdate): the logger constructor
        # inspects _jit_incoming_units, so it must come after.
        sim.step()
        logger = HomeostatStateLogger(
            hom, backend.kheperaSimulation, output_path,
            log_interval=log_interval,
            target_pos=(7, 7),
            seed=eval_seed)

        print("Running %d ticks ..." % steps)
        t0 = time.time()
        logger.log_tick(1)
        for tick in range(2, steps + 1):
            sim.step()
            logger.log_tick(tick)
            if tick % 10000 == 0:
                logger.flush()
                print("  tick %d/%d  (%.1fs elapsed)" % (tick, steps, time.time() - t0))

        logger.close()
        backend.kheperaSimulation.saveTrajectory()
        final_dist = backend.finalDisFromTarget()
    print("Done in %.1fs.  Final distance: %.4f" % (time.time() - t0, final_dist))
    print("Statelog written to: %s" % output_path)
    return final_dist


def replay_visualized(genome, experiment_func, seed, data_dir,
                      use_ashby=False, model_name=None, light_intensity=None):
    """Replay a genome with the pyglet visualizer.

    Press Q or Escape to close.  Up/Down arrows adjust simulation speed.
    """
    import pyglet
    from pyglet.gl import (glEnable, glBlendFunc, glHint, glClearColor,
                           GL_BLEND, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
                           GL_LINE_SMOOTH, GL_LINE_SMOOTH_HINT, GL_NICEST)
    from KheperaSimulator.KheperaSimulator import KheperaRobotView

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
    backend = SimulatorBackendHOMEO(lock=lock, robotName='Khepera', dataDir=data_dir)
    backend.start('kheperaBraitenberg2_HOMEO_World')

    hom = _build_homeostat(genome, experiment_func, seed, backend, data_dir, use_ashby,
                           light_intensity)

    if model_name:
        backend.setRobotModel(model_name)

    # Non-headless: keep normal Python objects for Connection weights
    # (no JIT) so the simulation matches the visualized state exactly.
    hom._collectsData = False
    hom._slowingFactor = 0


    sim = backend.kheperaSimulation
    robot = sim.allBodies['Khepera']
    target_pos = sim.allBodies['TARGET'].position

    view = KheperaRobotView(window, sim)
    print('Q/Esc: quit   Up/Down: speed   ' + view.HELP)
    state = [0, 5]             # [cumulative_tick, ticks_per_frame]

    @window.event
    def on_draw():
        view.draw()

    def update(dt):
        state[0] += state[1]
        hom.runFor(state[0])
        view.extendTrail()
        rx, ry = robot.body.position[0], robot.body.position[1]
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
        else:
            view.on_key_press(symbol, modifiers)

    window.push_handlers(on_mouse_scroll=view.on_mouse_scroll,
                         on_mouse_drag=view.on_mouse_drag)

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
    parser.add_argument('--steps', type=int, default=None,
                        help='Run length in homeostat ticks.  Default: the GA run length '
                             'recorded in the logbook for logbooks with evalSeeds, '
                             'else %d' % DEFAULT_STEPS)
    parser.add_argument('--seed', type=int, default=None,
                        help="RNG seed.  Default: the individual's logged evalSeed, which "
                             "reproduces its GA evaluation; 45 for older logbooks")
    parser.add_argument('--output', '-o', default=None,
                        help='Output .statelog path (default: auto-generated)')
    parser.add_argument('--log-interval', type=int, default=1,
                        help='Log every N-th tick (default: 1)')
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
    exp_func, exp_name, meta = resolve_experiment_func(logbook)
    if meta:
        print("  Experiment: %s  (%d units, %d evolved, genome size %d)"
              % (exp_name, meta.get('noUnits', '?'), meta.get('noEvolvedUnits', '?'),
                 meta.get('genomeSize', '?')))
    else:
        print("  Experiment: %s  (no metadata, using --exp override)" % exp_name)

    # The TARGET's intensity the run evaluated with: the GA phototaxis
    # setups' was -100 until 15 Oct 2026, +100 since
    import Simulator.HomeoExperiments as HE
    light_intensity = None
    if hasattr(exp_func, 'lightIntensity'):
        light_intensity = HE.loggedLightIntensity(exp_name, meta)
        print("  Light intensity: %g" % light_intensity)

    # Find individual
    rec = find_best_individual(logbook, args.indiv)
    genome = rec['genome']
    indiv_id = rec['indivId']
    fitness = rec['fitness'][0]
    print("  Individual: %s  fitness: %.5f  genome: %s" % (
        indiv_id, fitness, [round(g, 4) for g in genome]))

    logged_seed = rec.get('evalSeed')
    as_evaluated = logged_seed is not None and not args.visualize
    if logged_seed is None:
        print("  This logbook predates seeded GA evaluations (no evalSeed): the replay "
              "cannot reproduce the logged fitness.")
    if as_evaluated:
        seed = logged_seed if args.seed is None else args.seed
        steps = args.steps if args.steps is not None else (meta or {}).get('length', DEFAULT_STEPS)
    else:
        seed = 45 if args.seed is None and logged_seed is None else (
            logged_seed if args.seed is None else args.seed)
        steps = args.steps if args.steps is not None else DEFAULT_STEPS
    print("  Seed: %d%s   Steps: %d" % (
        seed, " (the logged evalSeed)" if seed == logged_seed else "", steps))

    # Build a descriptive model name for the .traj file
    unisel_tag = 'ashby' if args.ashby else 'OU'
    model_name = 'replay-%s-%s-s%d' % (indiv_id, unisel_tag, seed)

    if args.visualize:
        # Output dir for trajectory files
        timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')
        data_dir = os.path.join(simulations_data_dir(),
                                'replay-%s' % timestamp)
        os.makedirs(data_dir, exist_ok=True)
        replay_visualized(genome, exp_func, seed, data_dir,
                          use_ashby=args.ashby, model_name=model_name,
                          light_intensity=light_intensity)
    else:
        # Output path for statelog
        if args.output:
            output_path = os.path.abspath(args.output)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        else:
            timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')
            output_dir = os.path.join(simulations_data_dir(),
                                      'replay-%s' % timestamp)
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir,
                                       'replay-%s-%dk.statelog' % (indiv_id, steps // 1000))

        if not as_evaluated:
            replay(genome, steps, exp_func, seed, output_path,
                   log_interval=args.log_interval, use_ashby=args.ashby,
                   model_name=model_name, light_intensity=light_intensity)
            return

        final_dist = replay_as_evaluated(
            genome, indiv_id, exp_name, meta or {}, steps, seed, output_path,
            log_interval=args.log_interval, use_ashby=args.ashby,
            model_name=model_name, light_intensity=light_intensity)
        if seed == logged_seed and steps == (meta or {}).get('length') and not args.ashby:
            replayed = (meta or {}).get('fitnessSign', 1) * final_dist
            if replayed == fitness:
                print("Reproduced the logged fitness exactly: %r" % fitness)
            else:
                sys.exit("MISMATCH: replayed fitness %r, logged %r -- the replay does not "
                         "repeat the GA's evaluation" % (replayed, fitness))
        else:
            print("Not a reproduction of the GA evaluation (other seed, length or "
                  "uniselector): the logged fitness was %r" % fitness)


if __name__ == '__main__':
    main()
