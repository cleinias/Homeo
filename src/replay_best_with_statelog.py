#!/usr/bin/env python3
"""Replay the best individual from a GA logbook with per-tick state logging.

Loads a genome from a DEAP logbook pickle, constructs the homeostat + robot
simulator, runs the simulation, and writes a .statelog file suitable for
analysis with Helpers.StatelogAnalyzer.

The experiment type (2-unit vs 4-unit, continuous vs discrete, weight-free
vs classic) is read from the logbook's metadata.

Usage:
    cd src
    python replay_best_with_statelog.py --logbook path.lgb
    python replay_best_with_statelog.py --logbook path.lgb --indiv 016-014
    python replay_best_with_statelog.py --logbook path.lgb --visualize
    python replay_best_with_statelog.py --logbook path.lgb --ashby --steps 100000

Reproducing a GA evaluation.  A GA logbook records each individual's
evalSeed.  The replay builds and runs the homeostat through the GA's own code
(prepare_genome_evaluation in Simulator/HomeoGenAlg.py), seeded with the
logged evalSeed, for the logged run length, and reports whether it reproduced
the logged fitness exactly.  An evaluation of k runs (--evals-per-individual
k) is replayed whole: each run from its seed, compared with its logged score,
and their mean with the logged fitness; the .statelog is run 1's, or run j's
with --run j.  --seed replays the same genome under other noise; --steps runs
it for another length.  A logbook without evalSeeds is
replayed only with --seed.  The visualizer builds the homeostat the same way
but runs it non-headless, unlike the GA, so it does not check the fitness.
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
    """Find a specific individual in a DEAP logbook, or the best: the
    post-evaluation's best when the logbook has a post-evaluation (under
    noise the lowest logged score is mostly a lucky draw), else the
    individual with the lowest logged fitness."""
    if indiv_id:
        for rec in logbook:
            if rec.get('indivId') == indiv_id:
                return rec
        raise ValueError("Individual %s not found in logbook" % indiv_id)

    from Helpers.StatsAnalyzer import postEvaluationOf
    post = postEvaluationOf(logbook)
    if post:
        print("  The post-evaluation's best: %s, mean %.5f over %d seeds"
              % (post[0]['indivId'], post[0]['mean'], len(post[0]['scores'])))
        return find_best_individual(logbook, post[0]['indivId'])

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
    light_intensity: the TARGET's, for setups that take it, as the logbook
    records it (HomeoExperiments.loggedLightIntensity).

    Returns the configured Homeostat instance.
    """
    extra = {} if light_intensity is None else {'lightIntensity': light_intensity}
    # Build homeostat (first pass — pre-reset).  Every stream, numba's
    # included, as a GA evaluation seeds them.
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
       .statelog (none if output_path is None): the GA's own setup
       (prepare_genome_evaluation), seeded with eval_seed, advanced with the
       same sim.step() calls.  Returns the final distance from the target."""
    from Simulator.HomeoGenAlg import prepare_genome_evaluation, seeded_evaluation

    data_dir = os.path.dirname(output_path) if output_path else simulations_data_dir()
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
        logger = None
        if output_path:
            logger = HomeostatStateLogger(
                hom, backend.kheperaSimulation, output_path,
                log_interval=log_interval,
                target_pos=(7, 7),
                seed=eval_seed)
            logger.log_tick(1)

        print("Running %d ticks ..." % steps)
        t0 = time.time()
        for tick in range(2, steps + 1):
            sim.step()
            if logger is not None:
                logger.log_tick(tick)
            if tick % 10000 == 0:
                if logger is not None:
                    logger.flush()
                print("  tick %d/%d  (%.1fs elapsed)" % (tick, steps, time.time() - t0))

        if logger is not None:
            logger.close()
        backend.kheperaSimulation.saveTrajectory()
        final_dist = backend.finalDisFromTarget()
    print("Done in %.1fs.  Final distance: %.4f" % (time.time() - t0, final_dist))
    if output_path:
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
    from Simulator.HomeoGenAlg import GA_ROBOT
    backend = SimulatorBackendHOMEO(lock=lock, robotName='Khepera', dataDir=data_dir,
                                    robotModel=GA_ROBOT)
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
    parser.add_argument('--logbook', required=True,
                        help='Path to DEAP logbook pickle (.lgb)')
    parser.add_argument('--indiv', default=None,
                        help='Individual ID to replay (default: best)')
    parser.add_argument('--steps', type=int, default=None,
                        help='Run length in homeostat ticks.  Default: the GA run length '
                             'recorded in the logbook, else %d' % DEFAULT_STEPS)
    parser.add_argument('--seed', type=int, default=None,
                        help="RNG seed.  Default: the individual's logged evalSeed, which "
                             "reproduces its GA evaluation (a logbook without one needs it)")
    parser.add_argument('--output', '-o', default=None,
                        help='Output .statelog path (default: auto-generated)')
    parser.add_argument('--log-interval', type=int, default=1,
                        help='Log every N-th tick (default: 1)')
    parser.add_argument('--run', type=int, default=1,
                        help='For an evaluation of k runs: the run whose .statelog is '
                             'written (1..k, default 1)')
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

    # The experiment, from the logbook's metadata
    exp_func, exp_name, meta = resolve_experiment_func(logbook)
    print("  Experiment: %s  (%s units, %s evolved, genome size %s)"
          % (exp_name, meta.get('noUnits', '?'), meta.get('noEvolvedUnits', '?'),
             meta.get('genomeSize', '?')))

    # The robot the run evaluated with: the GA's
    from Simulator.HomeoGenAlg import GA_ROBOT
    if meta.get('robot') != GA_ROBOT:
        sys.exit("Cannot replay: the logbook's robot is %r, the GA's %r (replay a logbook "
                 "that records no robot with the code that wrote it)"
                 % (meta.get('robot'), GA_ROBOT))
    print("  Robot: %s   Homeo: %s" % (meta['robot'], meta.get('homeo', 'unknown')))

    # The TARGET's intensity the run evaluated with
    import Simulator.HomeoExperiments as HE
    light_intensity = None
    if hasattr(exp_func, 'lightIntensity'):
        try:
            light_intensity = HE.loggedLightIntensity(exp_name, meta)
        except ValueError as e:
            sys.exit('Cannot replay: %s' % e)
        print("  Light intensity: %g" % light_intensity)

    # Find individual
    rec = find_best_individual(logbook, args.indiv)
    genome = rec['genome']
    indiv_id = rec['indivId']
    fitness = rec['fitness'][0]
    print("  Individual: %s  fitness: %.5f  genome: %s" % (
        indiv_id, fitness, [round(g, 4) for g in genome]))

    logged_seed = rec.get('evalSeed')
    if args.seed is None and logged_seed is None:
        sys.exit("The logbook records no evalSeed for %s: give --seed" % indiv_id)
    seed = logged_seed if args.seed is None else args.seed
    steps = args.steps if args.steps is not None else (meta or {}).get('length', DEFAULT_STEPS)
    print("  Seed: %d%s   Steps: %d" % (
        seed, " (the logged evalSeed)" if seed == logged_seed else "", steps))
    # The evaluation's runs: k with --evals-per-individual k, each from its
    # seed (repeat_seeds), the logged fitness their mean
    from Simulator.HomeoGenAlg import repeat_seeds, averaged_fitness
    scores = rec.get('scores', [fitness])
    run_seeds = repeat_seeds(seed, len(scores))
    if not 1 <= args.run <= len(scores):
        sys.exit("--run must be between 1 and %d" % len(scores))
    if len(scores) > 1:
        print("  An evaluation of %d runs, seeds %s; the statelog is run %d's"
              % (len(scores), run_seeds, args.run))

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

        as_logged = seed == logged_seed and steps == meta.get('length') and not args.ashby
        sign = meta.get('fitnessSign', 1)
        replayed = []
        for j, run_seed in enumerate(run_seeds, 1):
            if j != args.run and not as_logged:
                continue                # another seed or length: only the run asked for
            final_dist = replay_as_evaluated(
                genome, indiv_id, exp_name, meta, steps, run_seed,
                output_path if j == args.run else None,
                log_interval=args.log_interval, use_ashby=args.ashby,
                model_name=model_name, light_intensity=light_intensity)
            replayed.append(sign * final_dist)
        if as_logged:
            mean = averaged_fitness(replayed)[0]
            if replayed == list(scores) and mean == fitness:
                print("Reproduced the logged fitness exactly: %r" % fitness)
            else:
                sys.exit("MISMATCH: replayed %r (mean %r), logged %r (mean %r) -- the replay "
                         "does not repeat the GA's evaluation"
                         % (replayed, mean, list(scores), fitness))
        else:
            print("Not a reproduction of the GA evaluation (other seed, length or "
                  "uniselector): the logged fitness was %r" % fitness)


if __name__ == '__main__':
    main()
