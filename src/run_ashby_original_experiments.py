#!/usr/bin/env python3
'''
Run Ashby's original Homeostat experiments from Design for a Brain.

Usage:
    python run_ashby_original_experiments.py                  # run all 7
    python run_ashby_original_experiments.py --exp 1          # run experiment 1 only
    python run_ashby_original_experiments.py --exp 1 --seed 42 --ticks 5000
    python run_ashby_original_experiments.py --exp 6 --ticks 8000 --output-dir results/

Each experiment produces:
    - A .statelog TSV file with per-tick state data
    - A .json file with initial and final conditions
    - Console summary with timing, stability, and uniselector statistics

@author: stefano (with Claude)
'''

import argparse
import os
import sys
import time

# Add src/ to path so imports work
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from Simulator.AshbyOriginalExperiments import (
    setup_exp1_basic_ultrastability,
    setup_exp2_self_reorganization, exp2_reversal_event,
    setup_exp3_training, make_trainer_callback,
    setup_exp4_alternating_environments, make_alternation_events,
    setup_exp5_constraint, make_constraint_callback,
    setup_exp6_habituation, make_stimulus_events, ResponseMeasurer,
    setup_exp7_multistable, make_multistable_callback,
    run_with_events, StabilityTracker, AshbyStateLogger,
)
from Helpers.HomeostatConditionLogger import (
    log_homeostat_conditions_json)


def _output_path(output_dir, exp_num, seed, ext):
    '''Build an output file path.'''
    timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')
    fname = 'ashby_exp%d_seed%d_%s%s' % (exp_num, seed, timestamp, ext)
    return os.path.join(output_dir, fname)


def run_experiment(exp_num, seed=None, total_ticks=5000, output_dir='.'):
    '''Run a single experiment and return a summary dict.'''

    os.makedirs(output_dir, exist_ok=True)

    # ---- Setup ----
    if exp_num == 1:
        hom, seed, meta = setup_exp1_basic_ultrastability(seed)
        events = []
        tick_callback = None
    elif exp_num == 2:
        hom, seed, meta = setup_exp2_self_reorganization(seed)
        reversal_tick = total_ticks // 2
        events = [(reversal_tick, exp2_reversal_event)]
        tick_callback = None
        meta['reversal_tick'] = reversal_tick
    elif exp_num == 3:
        hom, seed, meta = setup_exp3_training(seed)
        events = []
        trainer, punishment_log = make_trainer_callback()
        tick_callback = trainer
    elif exp_num == 4:
        hom, seed, meta = setup_exp4_alternating_environments(seed)
        interval = max(total_ticks // 10, 200)
        events = make_alternation_events(interval=interval, n_reversals=8)
        tick_callback = None
        meta['alternation_interval'] = interval
    elif exp_num == 5:
        hom, seed, meta = setup_exp5_constraint(seed)
        release_tick = total_ticks * 2 // 3
        constrain_cb, flag = make_constraint_callback(
            leader_idx=0, follower_idx=1, active=True)
        events = [(release_tick, lambda h: flag.__setitem__(0, False))]
        tick_callback = constrain_cb
        meta['constraint_release_tick'] = release_tick
    elif exp_num == 6:
        hom, seed, meta = setup_exp6_habituation(seed)
        settle = total_ticks // 10
        interval = (total_ticks - settle) // 10
        stim_events = make_stimulus_events(
            unit_index=0, delta=5.0,
            interval=interval, n_stimuli=10, settle_first=settle)
        events = stim_events
        stim_ticks = [e[0] for e in stim_events]
        tick_callback = None
        meta['stimulus_ticks'] = stim_ticks
    elif exp_num == 7:
        hom, seed, meta = setup_exp7_multistable(seed)
        events = []
        tick_callback = make_multistable_callback()
    else:
        print('Unknown experiment number: %d' % exp_num)
        sys.exit(1)

    # ---- Loggers ----
    statelog_path = _output_path(output_dir, exp_num, seed, '.statelog')
    json_path = _output_path(output_dir, exp_num, seed, '.json')

    state_logger = AshbyStateLogger(hom, statelog_path, seed=seed)
    stability_tracker = StabilityTracker(hom, window=200)

    # Response measurer for Exp 6
    response_measurer = None
    if exp_num == 6:
        response_measurer = ResponseMeasurer(
            hom, target_unit_index=1,
            stimulus_ticks=stim_ticks, measure_window=interval // 3)

    # ---- Log initial conditions ----
    log_homeostat_conditions_json(
        hom, json_path, label='INITIAL CONDITIONS',
        experiment_name=meta['experiment'], seed=seed)

    # ---- Run ----
    print('=' * 60)
    print(meta['experiment'])
    print('  Reference: %s' % meta['reference'])
    print('  Seed: %d' % seed)
    print('  Ticks: %d' % total_ticks)
    print('  Statelog: %s' % statelog_path)
    print('=' * 60)

    t0 = time.time()

    def combined_callback(hom, tick):
        if tick_callback is not None:
            tick_callback(hom, tick)
        if response_measurer is not None:
            response_measurer.check(tick)

    run_with_events(
        hom, total_ticks,
        events=events,
        tick_callback=combined_callback,
        state_logger=state_logger,
        stability_tracker=stability_tracker,
    )

    elapsed = time.time() - t0

    # ---- Log final conditions ----
    log_homeostat_conditions_json(
        hom, json_path, label='FINAL CONDITIONS',
        experiment_name=meta['experiment'])
    state_logger.close()

    # ---- Summary ----
    summary = {
        'experiment': exp_num,
        'seed': seed,
        'total_ticks': total_ticks,
        'elapsed_seconds': elapsed,
        'stability_achieved_at': stability_tracker.stability_achieved_at,
        'last_stability_at': stability_tracker.last_stability_at,
        'currently_stable': stability_tracker.currently_stable,
        'total_uniselector_firings': stability_tracker.total_uniselector_firings,
        'statelog_path': statelog_path,
        'json_path': json_path,
    }

    print('\nResults:')
    print('  Elapsed: %.1f s' % elapsed)
    if stability_tracker.stability_achieved_at is not None:
        print('  First stability at tick: %d' %
              stability_tracker.stability_achieved_at)
    else:
        print('  Stability NOT achieved within %d ticks' % total_ticks)
    if stability_tracker.currently_stable:
        print('  Currently stable (since tick %d)' %
              stability_tracker.last_stability_at)
    elif stability_tracker.stability_achieved_at is not None:
        print('  Currently UNSTABLE (was stable earlier)')
    print('  Total uniselector firings: %d' %
          stability_tracker.total_uniselector_firings)

    if exp_num == 3:
        print('  Punishments delivered: %d' % len(punishment_log))
        summary['punishments'] = len(punishment_log)
        summary['punishment_ticks'] = punishment_log

    if exp_num == 6 and response_measurer is not None:
        print('  Response amplitudes: %s' % [
            '%.3f' % r for r in response_measurer.responses])
        summary['response_amplitudes'] = response_measurer.responses

    # Final unit states
    print('\n  Final unit states:')
    for unit in hom.homeoUnits:
        if unit.isActive():
            print('    %s: critDev=%.3f, output=%.3f' % (
                unit.name, unit.criticalDeviation, unit.currentOutput))

    print()
    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Run Ashby's original Homeostat experiments")
    parser.add_argument('--exp', type=int, default=None,
                        help='Experiment number (1-7). Omit to run all.')
    parser.add_argument('--seed', type=int, default=None,
                        help='RNG seed (default: random)')
    parser.add_argument('--ticks', type=int, default=5000,
                        help='Number of ticks to simulate (default: 5000)')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Output directory (default: SimulationsData/AshbyExperiments/)')
    args = parser.parse_args()

    if args.output_dir is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        args.output_dir = os.path.join(base, 'SimulationsData', 'AshbyExperiments')

    if args.exp is not None:
        run_experiment(args.exp, seed=args.seed,
                       total_ticks=args.ticks, output_dir=args.output_dir)
    else:
        print('Running all 7 Ashby experiments...\n')
        summaries = []
        for exp_num in range(1, 8):
            summary = run_experiment(
                exp_num, seed=args.seed,
                total_ticks=args.ticks, output_dir=args.output_dir)
            summaries.append(summary)

        print('\n' + '=' * 60)
        print('SUMMARY OF ALL EXPERIMENTS')
        print('=' * 60)
        for s in summaries:
            stab = s['stability_achieved_at']
            stab_str = 'tick %d' % stab if stab is not None else 'NOT achieved'
            end_str = 'stable' if s['currently_stable'] else 'UNSTABLE'
            print('  Exp %d: first_stability=%s, end=%s, firings=%d, time=%.1fs' % (
                s['experiment'], stab_str, end_str,
                s['total_uniselector_firings'], s['elapsed_seconds']))


if __name__ == '__main__':
    main()
