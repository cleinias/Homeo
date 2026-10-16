#!/usr/bin/env python3
'''
Run Ashby's original Homeostat experiments from Design for a Brain.

Usage:
    python run_ashby_original_experiments.py                  # run all 7
    python run_ashby_original_experiments.py --exp 1          # run experiment 1 only
    python run_ashby_original_experiments.py --exp 1 --seed 42 --ticks 9600
    python run_ashby_original_experiments.py --exp 6 --fig 2 --output-dir results/

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
    setup_exp1_basic_ultrastability, exp1_events, EXP1_END, connection,
    setup_exp2_self_reorganization, exp2_reversal_event, EXP2_R, EXP2_END,
    setup_exp3_training, make_trainer_callback, EXP3_END,
    setup_exp4_alternating_environments, make_alternation_events,
    exp4_stable_for_both, EXP4_END,
    setup_exp5_constraint, make_constraint_callback, exp5_events,
    EXP5_J, EXP5_R, EXP5_END,
    setup_exp6_habituation, make_stimulus_events, ResponseMeasurer,
    setup_exp6b_habituation_ultrastable, EXP6_END, EXP6B_END,
    EXP6B_DISPLACEMENT, EXP6B_INTERVAL, EXP6B_FIRST,
    setup_exp7_multistable, make_multistable_callback,
    exp7_test_events, exp7_pairs_stable, EXP7_TEST, EXP7_END,
    run_with_events, StabilityTracker, AshbyStateLogger,
)
from Helpers.HomeostatConditionLogger import (
    log_homeostat_conditions_json)


def _output_stem(output_dir, exp_num, seed):
    '''The run's file stem in output_dir, ashby_exp<N>_seed<S>_<timestamp>,
    with -2, -3, ... when a run of the same second has it (unique_stem).'''
    from Helpers.General_Helper_Functions import unique_stem
    timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')
    return os.path.join(output_dir, unique_stem(
        output_dir, 'ashby_exp%d_seed%d_%s' % (exp_num, seed, timestamp), ('.statelog', '.json')))


# Default run length per experiment: long enough for its protocol
DEFAULT_TICKS = {1: EXP1_END, 2: EXP2_END, 3: EXP3_END, 4: EXP4_END, 5: EXP5_END, 6: EXP6_END, 7: EXP7_END}


def _marker(record, name, hom_fn):
    '''An event that records hom_fn(hom) under name.  Put it before the events
    of the same tick, which run in list order.'''
    return lambda hom: record.__setitem__(name, hom_fn(hom))


def run_experiment(exp_num, seed=None, total_ticks=None, output_dir='.', figure=1):
    '''Run a single experiment and return a summary dict.  figure: for Exp 6,
    Ashby's Fig. 14/6/1 (1) or 14/6/2 (2).'''

    os.makedirs(output_dir, exist_ok=True)
    if total_ticks is None:
        total_ticks = EXP6B_END if (exp_num, figure) == (6, 2) else DEFAULT_TICKS[exp_num]
    protocol = {}            # values recorded at the protocol's events

    # ---- Setup ----
    if exp_num == 1:
        hom, seed, meta = setup_exp1_basic_ultrastability(seed)
        u1, u2 = hom.homeoUnits[:2]
        c21 = connection(u1, u2)
        state21 = lambda h: (c21.weight * c21.switch, u1.uniselectorActivationCount)
        events = exp1_events()
        reversals = [t for t, f in events if f.__name__ == 'exp1_reversal_event']
        # markers first: events at the same tick run in list order
        events = [(t, _marker(protocol, 'R%d' % (i + 1), state21))
                  for i, t in enumerate(reversals)] + events
        tick_callback = None
        disturbances = reversals
    elif exp_num == 2:
        hom, seed, meta = setup_exp2_self_reorganization(seed)
        u1, u2 = hom.homeoUnits[:2]
        c12 = connection(u2, u1)
        state12 = lambda h: (c12.weight * c12.switch, u2.uniselectorActivationCount)
        events = [(EXP2_R, _marker(protocol, 'R', state12)), (EXP2_R, exp2_reversal_event)]
        tick_callback = None
        meta['reversal_tick'] = EXP2_R
        disturbances = [EXP2_R]
    elif exp_num == 3:
        hom, seed, meta = setup_exp3_training(seed)
        events = []
        trainer, punishment_log = make_trainer_callback()
        tick_callback = trainer
        disturbances = []        # the trainer acts whenever the operator's unit is wrong
    elif exp_num == 4:
        hom, seed, meta = setup_exp4_alternating_environments(seed)
        u1 = hom.homeoUnits[0]
        events = make_alternation_events()
        reversals = [t for t, f in events]
        events = [(t, _marker(protocol, t, lambda h: u1.uniselectorActivationCount))
                  for t in reversals] + events
        tick_callback = None
        meta['reversal_ticks'] = reversals
        disturbances = reversals
    elif exp_num == 5:
        hom, seed, meta = setup_exp5_constraint(seed)
        constrain_cb, flag = make_constraint_callback()
        events = exp5_events(flag)
        tick_callback = constrain_cb
        meta['join_tick'], meta['release_tick'] = EXP5_J, EXP5_R
        disturbances = [EXP5_J, EXP5_R]
    elif exp_num == 6:
        if figure == 2:
            hom, seed, meta = setup_exp6b_habituation_ultrastable(seed)
            stim_events = make_stimulus_events(delta=EXP6B_DISPLACEMENT, interval=EXP6B_INTERVAL,
                                               settle_first=EXP6B_FIRST)
        else:
            hom, seed, meta = setup_exp6_habituation(seed)
            stim_events = make_stimulus_events()
        events = stim_events
        stim_ticks = [e[0] for e in stim_events]
        tick_callback = None
        meta['stimulus_ticks'] = stim_ticks
        disturbances = stim_ticks
    elif exp_num == 7:
        hom, seed, meta = setup_exp7_multistable(seed)
        u1 = hom.homeoUnits[0]
        events = [(EXP7_TEST, _marker(protocol, 'test', lambda h: u1.uniselectorActivationCount))]
        events += exp7_test_events()
        tick_callback = make_multistable_callback()
        disturbances = [t for t, f in exp7_test_events()]
    else:
        print('Unknown experiment number: %d' % exp_num)
        sys.exit(1)

    # ---- Loggers ----
    stem = _output_stem(output_dir, exp_num, seed)
    statelog_path = stem + '.statelog'
    json_path = stem + '.json'

    state_logger = AshbyStateLogger(hom, statelog_path, seed=seed)
    stability_tracker = StabilityTracker(hom, window=200)

    # Response measurer for Exp 6
    response_measurer = None
    if exp_num == 6:
        response_measurer = ResponseMeasurer(
            hom, target_unit_index=1, stimulus_ticks=stim_ticks)

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

    critical_ticks = []      # ticks at which some active unit is critical

    def combined_callback(hom, tick):
        if tick_callback is not None:
            tick_callback(hom, tick)
        if any(stability_tracker._is_critical(u) for u in hom.homeoUnits if u.isActive()):
            critical_ticks.append(tick)
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
        'stable_since': stability_tracker.stable_since,
        'currently_stable': stability_tracker.currently_stable,
        'stable_episodes': [list(e) for e in stability_tracker.episodes],
        'total_uniselector_firings': stability_tracker.total_uniselector_firings,
        'statelog_path': statelog_path,
        'json_path': json_path,
    }

    print('\nResults:')
    print('  Elapsed: %.1f s' % elapsed)
    first = stability_tracker.stability_achieved_at
    if first is not None:
        print('  First stability at tick: %d%s' % (first, ' (from the start)' if first == 1 else ''))
    else:
        print('  Stability NOT achieved within %d ticks' % total_ticks)
    if stability_tracker.currently_stable:
        print('  Currently stable (since tick %d)' % stability_tracker.stable_since)
    elif first is not None:
        print('  Currently UNSTABLE (was stable earlier)')
    print('  Stable stretches: %d' % len(stability_tracker.episodes))
    # What each disturbance did, judged up to the next one (or the run's end)
    after = []
    for t, until in zip(disturbances, list(disturbances[1:]) + [total_ticks]):
        outcome, latency = stability_tracker.restabilisation(t, until)
        after.append({'tick': t, 'outcome': outcome, 'latency': latency})
    if after:
        print('  After each disturbance: %s' % '; '.join(
            '%d %s' % (a['tick'], 're-stabilised after %d' % a['latency']
                       if a['outcome'] == 'restabilised' else a['outcome'])
            for a in after))
    summary['disturbances'] = after
    print('  Total uniselector firings: %d' %
          stability_tracker.total_uniselector_firings)

    if exp_num == 1:
        # Ashby: each reversal of 1->2 is followed by uniselector changes that
        # leave 2->1 reversed ("This reversal compensated for the reversal")
        protocol['end'] = state21(hom)
        marks = [k for k in ('R1', 'R2', 'end') if k in protocol]
        for a, b in zip(marks, marks[1:]):
            (wa, fa), (wb, fb) = protocol[a], protocol[b]
            print('  %s: 2->1 = %+.3f; %d uniselector change(s) of unit 1 by %s, '
                  '2->1 = %+.3f (%s)' % (a, wa, fb - fa, b, wb,
                                        'compensated' if wa * wb < 0 else 'NOT compensated'))
        summary['protocol'] = protocol

    if exp_num == 2 and 'R' in protocol:
        # Ashby: after R, unit 2's uniselector reverses 1->2 ("the second
        # reversal is compensatory to the first")
        (w0, f0), (w1, f1) = protocol['R'], state12(hom)
        print('  1->2 at R: %+.3f; %d uniselector change(s) of unit 2 after R; at the end '
              '%+.3f (%s)' % (w0, f1 - f0, w1, 'compensated' if w0 * w1 < 0 else 'NOT compensated'))
        summary['protocol'] = protocol

    if exp_num == 4:
        # Ashby: changes after the first reversals, then a field stable for
        # both positions of H, kept through the later reversals
        counts = [protocol[t] for t in reversals if t in protocol] + [u1.uniselectorActivationCount]
        changes = [b - a for a, b in zip(counts, counts[1:])]
        print('  Uniselector changes of unit 1 after each reversal of H: %s' % changes)
        quiet = len(changes) - max([i + 1 for i, n in enumerate(changes) if n], default=0)
        print('  Reversals with no change since the last change: %d' % quiet)
        both = exp4_stable_for_both(hom)
        print('  Final field stable for both positions of H: %s' % both)
        summary.update(changes_per_reversal=changes, quiet_reversals=quiet, stable_for_both=both)

    def critical_in(start, end):
        return any(start <= t < end for t in critical_ticks)

    if exp_num == 5:
        # Ashby: stable, made unstable by the fibre (J), re-adapted with it,
        # unstable again when it is removed (R)
        steps = {'stable before J': not critical_in(EXP5_J - 500, EXP5_J),
                 'unstable after J': critical_in(EXP5_J, EXP5_R - 500),
                 'stable before R': not critical_in(EXP5_R - 500, EXP5_R),
                 'unstable after R': critical_in(EXP5_R, total_ticks + 1)}
        for name, ok in steps.items():
            print('  %s: %s' % (name, ok))
        summary['protocol'] = steps

    if exp_num == 7:
        # Ashby: unit 1's uniselector changes until 2->1 and 3->1 make both
        # pairs stable; then 1 interacts with 2 and 3 without loss of stability
        before = protocol.get('test', u1.uniselectorActivationCount)
        pairs = exp7_pairs_stable(hom)
        print('  Uniselector changes of unit 1: %d before the tests, %d during them' %
              (before, u1.uniselectorActivationCount - before))
        print('  Pair 1-2 stable: %s; pair 1-3 stable: %s' % pairs)
        print('  Unit critical during the tests: %s' % critical_in(EXP7_TEST, total_ticks + 1))
        summary.update(changes=before, pairs_stable=pairs)

    if exp_num == 3:
        # Ashby: punished at first, then a change of 1->2 by the punishment,
        # then the desired response (2 moves opposite to 1) without punishment
        u1, u2 = hom.homeoUnits[:2]
        c12 = connection(u2, u1)
        print('  Tests (P punished, d desired response): %s' % ''.join(trainer.sequence))
        print('  Responses of unit 2: %s' % ['%+.2f' % r for r in trainer.responses])
        print('  Uniselector changes of unit 2 during each punishment: %s' %
              trainer.changes_per_punishment)
        print('  1->2 at the end: %+.3f' % (c12.weight * c12.switch))
        print('  Trained (Ashby, DfB 8/9): %s' % trainer.trained(hom))
        summary.update(sequence=''.join(trainer.sequence), punishments=len(punishment_log),
                       punishment_ticks=punishment_log, trained=trainer.trained(hom))

    if exp_num == 6 and response_measurer is not None:
        m = response_measurer
        print('  Response of unit 2 to each D: %s' % ['%.2f' % r for r in m.responses])
        print('  Uniselector changes after each D: %s' % m.changes)
        print("  D's that drove the system critical: %s" %
              [i + 1 for i, c in enumerate(m.critical) if c])
        since = m.retained_since()
        print('  Value retained since D%s' % (since + 1) if since is not None
              else '  Value not retained (the last D caused a change)')
        print('  Habituation (Ashby, DfB 14/6): %s' % m.habituated())
        summary.update(response_amplitudes=m.responses, changes_per_stimulus=m.changes,
                       habituated=m.habituated())

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
    parser.add_argument('--exp', type=int, default=None, choices=range(1, 8),
                        help='Experiment number (1-7). Omit to run all.')
    parser.add_argument('--seed', type=int, default=None,
                        help='RNG seed (default: random)')
    parser.add_argument('--ticks', type=int, default=None,
                        help="Number of ticks to simulate (default: the experiment's protocol length)")
    parser.add_argument('--fig', type=int, default=1, choices=(1, 2),
                        help="Exp 6 only: Ashby's Fig. 14/6/1 (default) or 14/6/2")
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Output directory (default: SimulationsData/AshbyExperiments/)')
    args = parser.parse_args()

    if args.output_dir is None:
        from Helpers.General_Helper_Functions import simulations_data_dir
        args.output_dir = os.path.join(simulations_data_dir(), 'AshbyExperiments')

    if args.exp is not None:
        run_experiment(args.exp, seed=args.seed,
                       total_ticks=args.ticks, output_dir=args.output_dir, figure=args.fig)
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
