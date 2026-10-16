'''
Ashby's experiments from Design for a Brain, as reconstructed in
Simulator/AshbyOriginalExperiments.py (headless) and
Simulator/HomeoExperiments.py (GUI).
'''
import unittest
from unittest import mock

from Simulator.AshbyOriginalExperiments import (setup_exp1_basic_ultrastability, exp1_events,
                                                setup_exp3_training, make_trainer_callback, EXP3_END,
                                                EXP3_W23, EXP3_W31,
                                                EXP1_R1, EXP1_R2, EXP1_END,
                                                setup_exp2_self_reorganization,
                                                setup_exp4_alternating_environments,
                                                make_alternation_events, exp4_stable_for_both,
                                                exp4_reversal_event, EXP4_END,
                                                ashby_matrix, ashby_stable,
                                                setup_exp5_constraint, make_constraint_callback,
                                                exp5_events, exp5_fibre_matrix, EXP5_J, EXP5_R,
                                                EXP5_END,
                                                setup_exp6_habituation,
                                                setup_exp6b_habituation_ultrastable,
                                                make_stimulus_events, ResponseMeasurer, EXP6_END,
                                                EXP6B_DISPLACEMENT, EXP6B_INTERVAL, EXP6B_FIRST,
                                                EXP6B_END,
                                                setup_exp7_multistable, make_multistable_callback,
                                                exp7_test_events, exp7_pairs_stable, EXP7_TEST,
                                                EXP7_END,
                                                exp2_reversal_event, run_with_events,
                                                StabilityTracker, inject_stimulus, connection)
from Simulator.HomeoExperiments import (initializeAshbyExp1BasicUltrastability,
                                        initializeAshbyExp2SelfReorganization,
                                        initializeAshbyExp3Training,
                                        initializeAshbyExp4AlternatingEnvironments,
                                        initializeAshbyExp5Constraint,
                                        initializeAshbyExp6Habituation,
                                        initializeAshbyExp7Multistable)


def signedWeight(to_unit, from_unit):
    conn = connection(to_unit, from_unit)
    return conn.weight * conn.switch


def quiet(hom):
    hom._slowingFactor = 0
    hom.collectsData = False


class AshbyHelpersTest(unittest.TestCase):

    def testUnusedSlotsAreCutOff(self):
        "The GUI's inactive units have no live connection in either direction"
        hom = initializeAshbyExp1BasicUltrastability()
        self.assertEqual(len(hom.homeoUnits), 4)
        for unit in hom.homeoUnits:
            for conn in unit.inputConnections:
                if not (unit.isActive() and conn.incomingUnit.isActive()):
                    self.assertFalse(conn.isActive())

    def testStimulusStaysInRange(self):
        hom, seed, meta = setup_exp1_basic_ultrastability(1)
        unit = hom.homeoUnits[1]
        inject_stimulus(hom, 1, 3 * unit.maxDeviation)
        self.assertEqual(unit.criticalDeviation, unit.maxDeviation)
        self.assertEqual(unit.currentOutput, unit.outputRange['high'])

    def testTrackerCountsOnlyFiringsThatCanChangeSomething(self):
        "A unit with no uniselector-controlled input fires to no effect"
        hom, seed, meta = setup_exp1_basic_ultrastability(1)
        quiet(hom)
        u1, u2 = hom.homeoUnits[:2]
        u2.uniselectorActive = True               # it has no input to re-draw
        tracker = StabilityTracker(hom)
        run_with_events(hom, 3000, events=[(100, lambda h: inject_stimulus(h, 1, 10))],
                        tick_callback=lambda h, t: setattr(u2, 'criticalDeviation', u2.maxDeviation),
                        stability_tracker=tracker)
        self.assertGreater(u2.uniselectorActivationCount, 0)
        self.assertEqual(tracker.total_uniselector_firings, u1.uniselectorActivationCount)


class UniselectorFlagRowTest(unittest.TestCase):
    """Per-tick records: row t is the state after t
    updates, and the firing flag is in the same row as the deviation that
    triggered it and the weights it drew"""

    def testAFiringSharesItsRowWithItsTriggerAndItsWeights(self):
        import csv, os, tempfile
        from Simulator.AshbyOriginalExperiments import AshbyStateLogger
        hom, seed, meta = setup_exp1_basic_ultrastability(1)
        quiet(hom)
        u1 = hom.homeoUnits[0]
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'flag.statelog')
            logger = AshbyStateLogger(hom, path)
            run_with_events(hom, 400, events=[(50, lambda h: inject_stimulus(h, 1, 10))],
                            state_logger=logger)
            logger.close()
            with open(path) as f:
                rows = [r for r in csv.reader((l for l in f if not l.startswith('#')),
                                              delimiter='\t')]
        header, rows = rows[0], rows[1:]
        col = {name: i for i, name in enumerate(header)}
        fired = col['%s_unisel_fired' % u1.name]
        dev = col['%s_critDev' % u1.name]
        weights = [i for c, i in col.items() if c.startswith('w_%s<-' % u1.name)
                   and not c.endswith('<-%s' % u1.name)]
        firings = [k for k, r in enumerate(rows) if r[fired] == '1']
        self.assertGreater(len(firings), 0)
        threshold = u1.critThreshold * u1.maxDeviation
        for k in firings:
            self.assertGreaterEqual(abs(float(rows[k][dev])), threshold - 1e-6, rows[k])
            self.assertNotEqual([rows[k][i] for i in weights],
                                [rows[k - 1][i] for i in weights])


class StabilityTrackerTest(unittest.TestCase):
    """Stable stretches and their onsets, on a stand-in
    homeostat whose one unit is critical at the ticks given"""

    class Unit:
        critThreshold, maxDeviation = 0.9, 1.0
        uniselectorActivated = False
        def __init__(self):
            self.criticalDeviation = 0.0
        def isActive(self):
            return True

    def track(self, critical, ticks, window=200):
        unit = self.Unit()
        tracker = StabilityTracker(mock.Mock(homeoUnits=[unit]), window=window)
        for tick in range(1, ticks + 1):
            unit.criticalDeviation = 1.0 if tick in critical else 0.0
            tracker.check(tick)
        return tracker

    def testStableFromTheStartIsOnsetOne(self):
        "stable from tick 1, not from the end of a burn-in"
        tracker = self.track(set(), 4000)
        self.assertEqual(tracker.stability_achieved_at, 1)
        self.assertEqual(tracker.stable_since, 1)
        self.assertEqual(tracker.episodes, [[1, 4000]])

    def testTheOnsetIsTheStretchsFirstTick(self):
        "critical up to tick 500: stable from 501"
        tracker = self.track(set(range(1, 501)), 4000)
        self.assertEqual(tracker.stability_achieved_at, 501)

    def testNotStableUntilWindowTicks(self):
        tracker = self.track(set(), 199)
        self.assertFalse(tracker.currently_stable)
        self.assertIsNone(tracker.stability_achieved_at)
        tracker.check(200)
        self.assertTrue(tracker.currently_stable)

    def testStableSinceIsTheOnsetOfTheStretchInProgress(self):
        """the 'since' is the stretch's first tick, not the last tick minus
        window (3800 here), and a stretch from 1 to 300 is a first stability at 1"""
        tracker = self.track({301, 2000}, 4000)
        self.assertEqual(tracker.episodes, [[1, 300], [302, 1999], [2001, 4000]])
        self.assertEqual(tracker.stability_achieved_at, 1)
        self.assertEqual(tracker.stable_since, 2001)

    def testAShortStretchIsNotAnEpisode(self):
        tracker = self.track({100, 250}, 450)
        self.assertEqual(tracker.episodes, [[251, 450]])
        tracker = self.track({100, 250, 449}, 450)
        self.assertEqual(tracker.episodes, [])
        self.assertIsNone(tracker.stable_since)

    def testRestabilisation(self):
        tracker = self.track(set(range(1010, 1100)), 4000)
        self.assertEqual(tracker.restabilisation(1000, 3000), ('restabilised', 100))
        self.assertEqual(tracker.restabilisation(3000, 4000), ('held', None))
        tracker = self.track(set(range(1010, 3950)), 4000)
        self.assertEqual(tracker.restabilisation(1000, 4000), ('never', None))


class AshbyGuiIsHeadlessTest(unittest.TestCase):
    """Each GUI setup is the headless one: given the seed the headless
    setup would draw, the two homeostats are the same."""

    PAIRS = [
        (initializeAshbyExp1BasicUltrastability,
         lambda s: setup_exp1_basic_ultrastability(s, unused_slots=True)),
        (initializeAshbyExp2SelfReorganization, setup_exp2_self_reorganization),
        (initializeAshbyExp3Training, lambda s: setup_exp3_training(s, unused_slots=True)),
        (initializeAshbyExp4AlternatingEnvironments,
         lambda s: setup_exp4_alternating_environments(s, unused_slots=True)),
        (initializeAshbyExp5Constraint, lambda s: setup_exp5_constraint(s, unused_slots=True)),
        (initializeAshbyExp6Habituation, lambda s: setup_exp6_habituation(s, unused_slots=True)),
        (initializeAshbyExp7Multistable, lambda s: setup_exp7_multistable(s, unused_slots=True)),
    ]

    @staticmethod
    def describe(hom):
        units = [(u.name, u.isActive(), u.mass, u.viscosity, u.noise, u.potentiometer,
                  u.criticalDeviation, u.uniselectorActive, u.uniselectorTimeInterval)
                 for u in hom.homeoUnits]
        conns = [(c.weight * c.switch, c.state, c.status, c.noise)
                 for u in hom.homeoUnits for c in u.inputConnections]
        return units, conns

    def testSameSeedSameHomeostat(self):
        seed = 12345
        for gui_setup, headless_setup in self.PAIRS:
            with self.subTest(setup=gui_setup.__name__):
                with mock.patch('os.urandom', return_value=seed.to_bytes(4, 'big')):
                    gui = gui_setup()
                headless, _, _ = headless_setup(seed)
                self.assertEqual(self.describe(gui), self.describe(headless))


class AshbyExp1Test(unittest.TestCase):
    '''DfB 8/4, Fig. 8/4/1: two units, 1->2 hand-controlled, 2->1 on unit 1's
    uniselector.  Each hand reversal of 1->2 makes the system unstable, and
    unit 1's uniselector restores stability by reversing 2->1.'''

    def assertAshbyWiring(self, hom):
        u1, u2 = hom.homeoUnits[:2]
        self.assertEqual([u.uniselectorActive for u in (u1, u2)], [True, False])
        self.assertEqual([u.inputConnections[0].isActive() for u in (u1, u2)], [False, True])
        self.assertEqual(connection(u1, u2).state, 'uniselector')
        self.assertEqual(connection(u2, u1).state, 'manual')
        self.assertGreater(signedWeight(u1, u2), 0)
        self.assertLess(signedWeight(u2, u1), 0)

    def testWiringHeadless(self):
        hom, seed, meta = setup_exp1_basic_ultrastability(1)
        self.assertEqual(len(hom.homeoUnits), 2)
        self.assertAshbyWiring(hom)

    def testWiringGui(self):
        self.assertAshbyWiring(initializeAshbyExp1BasicUltrastability())

    def testAshbysSequence(self):
        "Stable, then after each reversal of 1->2 restabilised with 2->1 reversed"
        for seed in (1, 2, 3):
            hom, seed, meta = setup_exp1_basic_ultrastability(seed)
            quiet(hom)
            u1, u2 = hom.homeoUnits[:2]
            tracker = StabilityTracker(hom, window=200)
            atR = []

            def mark(h):
                atR.append((tracker.currently_stable, signedWeight(u1, u2),
                            u1.uniselectorActivationCount))

            events = [(EXP1_R1, mark), (EXP1_R2, mark)] + exp1_events()
            run_with_events(hom, EXP1_END, events=events, stability_tracker=tracker)
            atR.append((tracker.currently_stable, signedWeight(u1, u2),
                        u1.uniselectorActivationCount))
            self.assertEqual(atR[0][2], 0, 'seed %d: the uniselector acted before R1' % seed)
            for before, after in zip(atR, atR[1:]):
                self.assertTrue(before[0] and after[0], 'seed %d: not stable' % seed)
                self.assertGreater(after[2], before[2], 'seed %d: no uniselector change' % seed)
                self.assertLess(before[1] * after[1], 0, 'seed %d: 2->1 not reversed' % seed)


class AshbyExp2Test(unittest.TestCase):
    '''DfB 8/5, Fig. 8/5/1: the ring 1->2->3->1 is stable; reversing 2->3 at R
    makes it a vicious circle; unit 2's uniselector changes 1->2 until the
    ring is stable again, with 1->2 reversed ("the second reversal is
    compensatory to the first").'''

    def assertAshbyWiring(self, hom):
        u1, u2, u3 = hom.homeoUnits[:3]
        self.assertEqual([u.uniselectorActive for u in (u1, u2, u3)], [False, True, False])
        self.assertEqual([u.inputConnections[0].isActive() for u in (u1, u2, u3)], [True, False, True])
        self.assertEqual(connection(u2, u1).state, 'uniselector')
        self.assertGreater(connection(u2, u1).weight * connection(u2, u1).switch, 0)
        self.assertLess(connection(u1, u3).weight * connection(u1, u3).switch, 0)

    def testWiringHeadless(self):
        hom, seed, meta = setup_exp2_self_reorganization(1)
        self.assertAshbyWiring(hom)

    def testWiringGui(self):
        self.assertAshbyWiring(initializeAshbyExp2SelfReorganization())

    def testAshbysSequence(self):
        "Stable before R, then restabilised with 1->2 reversed by the uniselector"
        for seed in (1, 2, 3):
            hom, seed, meta = setup_exp2_self_reorganization(seed)
            quiet(hom)
            u1, u2 = hom.homeoUnits[:2]
            conn = connection(u2, u1)
            tracker = StabilityTracker(hom, window=200)
            atR = {}

            def reverse(h):
                atR['stable'] = tracker.currently_stable
                atR['weight'] = conn.weight * conn.switch
                atR['firings'] = u2.uniselectorActivationCount
                exp2_reversal_event(h)

            run_with_events(hom, 9000, events=[(3000, reverse)], stability_tracker=tracker)
            self.assertTrue(atR['stable'], 'seed %d: not stable before R' % seed)
            self.assertGreater(u2.uniselectorActivationCount, atR['firings'],
                               'seed %d: the uniselector never acted after R' % seed)
            self.assertLess(conn.weight * conn.switch * atR['weight'], 0,
                            'seed %d: 1->2 was not reversed' % seed)
            self.assertTrue(tracker.currently_stable, 'seed %d: not stable at the end' % seed)


class AshbyExp4Test(unittest.TestCase):
    '''DfB 8/10, Fig. 8/10/1: the commutator H (1->2) is reversed from time to
    time; unit 1's uniselector changes 2->1 until it finds a field stable for
    both positions of H, which is then kept through later reversals.'''

    def assertAshbyWiring(self, hom):
        u1, u2 = hom.homeoUnits[:2]
        self.assertEqual([u.uniselectorActive for u in (u1, u2)], [True, False])
        self.assertEqual([u.inputConnections[0].isActive() for u in (u1, u2)], [True, True])
        self.assertEqual(connection(u1, u2).state, 'uniselector')
        self.assertEqual(connection(u2, u1).state, 'manual')
        # Ashby's start: stable for this position of H, unstable for the other
        self.assertTrue(ashby_stable(ashby_matrix([u1, u2])))
        exp4_reversal_event(hom)
        self.assertFalse(ashby_stable(ashby_matrix([u1, u2])))

    def testWiringHeadless(self):
        hom, seed, meta = setup_exp4_alternating_environments(1)
        self.assertEqual(len(hom.homeoUnits), 2)
        self.assertAshbyWiring(hom)

    def testWiringGui(self):
        self.assertAshbyWiring(initializeAshbyExp4AlternatingEnvironments())

    def testAshbysSequence(self):
        "Changes after the first reversals, then a field stable for both H, kept"
        for seed in (1, 2):
            hom, seed, meta = setup_exp4_alternating_environments(seed)
            quiet(hom)
            u1 = hom.homeoUnits[0]
            events = make_alternation_events()
            counts = []
            marks = [(t, lambda h: counts.append(u1.uniselectorActivationCount)) for t, f in events]
            tracker = StabilityTracker(hom, window=200)
            run_with_events(hom, EXP4_END, events=marks + events, stability_tracker=tracker)
            counts.append(u1.uniselectorActivationCount)
            self.assertEqual(counts[0], 0, 'seed %d: changes before the first reversal' % seed)
            self.assertGreater(counts[1], counts[0], 'seed %d: no change after R1' % seed)
            self.assertEqual(counts[-1], counts[-4], 'seed %d: changes in the last 3 reversals' % seed)
            self.assertTrue(exp4_stable_for_both(hom), 'seed %d: not stable for both H' % seed)
            self.assertTrue(tracker.currently_stable, 'seed %d: not stable at the end' % seed)


class AshbyExp5Test(unittest.TestCase):
    '''DfB 8/11, Fig. 8/11/1: three units, at first stable; joining the magnets
    of 1 and 2 with a glass fibre (J) makes them unstable; the uniselectors
    find a field stable with the fibre, which is unstable without it (R).'''

    def assertAshbyWiring(self, hom):
        units = hom.homeoUnits[:3]
        self.assertEqual([u.uniselectorActive for u in units], [True] * 3)
        self.assertEqual([u.inputConnections[0].isActive() for u in units], [False, False, True])
        for u in units:
            for v in units:
                if u is not v:
                    self.assertTrue(connection(u, v).isActive())
                    self.assertEqual(connection(u, v).state, 'uniselector')
        # Ashby's start: stable while free, unstable with the fibre
        A = ashby_matrix(units)
        self.assertTrue(ashby_stable(A))
        self.assertFalse(ashby_stable(exp5_fibre_matrix(A)))

    def testWiringHeadless(self):
        hom, seed, meta = setup_exp5_constraint(1)
        self.assertEqual(len(hom.homeoUnits), 3)
        self.assertAshbyWiring(hom)

    def testWiringGui(self):
        self.assertAshbyWiring(initializeAshbyExp5Constraint())

    def testFibreMovesThePairUnderBothTorques(self):
        "With the fibre the two magnets share position and velocity, the means of their own"
        hom, seed, meta = setup_exp5_constraint(1)
        u1, u2 = hom.homeoUnits[:2]
        u1.criticalDeviation, u1.currentVelocity = 2.0, 0.1
        u2.criticalDeviation, u2.currentVelocity = -1.0, 0.3
        fibre, flag = make_constraint_callback()
        fibre(hom, 0)
        self.assertEqual(u1.criticalDeviation, 2.0)        # not joined yet
        flag[0] = True
        fibre(hom, 0)
        for u in (u1, u2):
            self.assertAlmostEqual(u.criticalDeviation, 0.5)
            self.assertAlmostEqual(u.currentVelocity, 0.2)
            self.assertAlmostEqual(u.currentOutput, 0.5 / u.maxDeviation)

    def testAshbysSequence(self):
        "Stable; J destabilises; re-adapted with the fibre; R destabilises"
        for seed in (1, 2):
            hom, seed, meta = setup_exp5_constraint(seed)
            quiet(hom)
            units = hom.homeoUnits[:3]
            fibre, flag = make_constraint_callback()
            critical = []

            def record(h, t):
                fibre(h, t)
                if any(abs(u.criticalDeviation) >= u.critThreshold * u.maxDeviation for u in units):
                    critical.append(t)

            counts = []
            mark = lambda h: counts.append(sum(u.uniselectorActivationCount for u in units))
            run_with_events(hom, EXP5_END, events=[(EXP5_J, mark), (EXP5_R, mark)] + exp5_events(flag),
                            tick_callback=record)
            within = lambda a, b: any(a <= t < b for t in critical)
            self.assertFalse(within(EXP5_J - 500, EXP5_J), 'seed %d: not stable before J' % seed)
            self.assertTrue(within(EXP5_J, EXP5_R - 500), 'seed %d: J did not destabilise' % seed)
            self.assertGreater(counts[1], counts[0], 'seed %d: no change after J' % seed)
            self.assertFalse(within(EXP5_R - 500, EXP5_R), 'seed %d: not stable before R' % seed)
            self.assertTrue(within(EXP5_R, EXP5_END + 1), 'seed %d: R did not destabilise' % seed)


class AshbyExp6Test(unittest.TestCase):
    '''DfB 14/6: repeated displacements D of unit 1.  While D drives the system
    critical the uniselector changes; the first value (Fig. 14/6/1) or field
    (Fig. 14/6/2) for which it does not is retained, and the response stays
    small: habituation.'''

    def assertAshbyWiring(self, hom):
        u1, u2 = hom.homeoUnits[:2]
        self.assertEqual([u.uniselectorActive for u in (u1, u2)], [False, True])
        self.assertEqual(connection(u2, u1).state, 'uniselector')
        self.assertTrue(connection(u2, u1).isActive())
        self.assertFalse(connection(u1, u2).isActive())            # no 2->1
        for u in (u1, u2):
            self.assertLess(signedWeight(u, u), 0)                  # they return to rest

    def testWiringHeadless(self):
        hom, seed, meta = setup_exp6_habituation(1)
        self.assertEqual(len(hom.homeoUnits), 2)
        self.assertAshbyWiring(hom)

    def testWiringGui(self):
        self.assertAshbyWiring(initializeAshbyExp6Habituation())

    def runStimuli(self, hom, events, end):
        quiet(hom)
        measurer = ResponseMeasurer(hom, 1, [t for t, f in events])
        run_with_events(hom, end, events=events, tick_callback=lambda h, t: measurer.check(t))
        return measurer

    def testHabituation(self):
        """Fig. 14/6/1: some D's change 1->2, then one value is kept and the response is small.
        21 of seeds 1-30 habituate; seed 1 does not (its first 1->2 already
        gives a small response).  Seeds that do."""
        for seed in (2, 3):
            hom, seed, meta = setup_exp6_habituation(seed)
            m = self.runStimuli(hom, make_stimulus_events(), EXP6_END)
            self.assertTrue(m.habituated(), 'seed %d: %s, %s' % (seed, m.changes, m.critical))

    def testHabituationUltrastable(self):
        "Fig. 14/6/2: both links on the uniselectors"
        hom, seed, meta = setup_exp6b_habituation_ultrastable(2)
        u1, u2 = hom.homeoUnits[:2]
        self.assertEqual([connection(u2, u1).state, connection(u1, u2).state], ['uniselector'] * 2)
        events = make_stimulus_events(delta=EXP6B_DISPLACEMENT, interval=EXP6B_INTERVAL,
                                      settle_first=EXP6B_FIRST)
        m = self.runStimuli(hom, events, EXP6B_END)
        self.assertTrue(m.habituated(), '%s, %s' % (m.changes, m.critical))


class AshbyExp7Test(unittest.TestCase):
    '''DfB 16/8, Fig. 16/8/1: 2 <-> 1 <-> 3 with bars that stop 2 and 3 above the
    centre; unit 1's uniselector changes 2->1 and 3->1 until both pairs are
    stable, and then keeps them.'''

    def assertAshbyWiring(self, hom):
        u1, u2, u3 = hom.homeoUnits[:3]
        self.assertEqual([u.uniselectorActive for u in (u1, u2, u3)], [True, False, False])
        self.assertEqual([u.inputConnections[0].isActive() for u in (u1, u2, u3)], [False, True, True])
        self.assertEqual([connection(u1, u2).state, connection(u1, u3).state], ['uniselector'] * 2)
        self.assertEqual([connection(u2, u1).state, connection(u3, u1).state], ['manual'] * 2)
        self.assertLess(signedWeight(u2, u1), 0)
        self.assertGreater(signedWeight(u3, u1), 0)
        self.assertFalse(connection(u2, u3).isActive() or connection(u3, u2).isActive())

    def testWiringHeadless(self):
        hom, seed, meta = setup_exp7_multistable(1)
        self.assertEqual(len(hom.homeoUnits), 3)
        self.assertAshbyWiring(hom)

    def testWiringGui(self):
        self.assertAshbyWiring(initializeAshbyExp7Multistable())

    def testBars(self):
        "Units 2 and 3 cannot move above the centre; unit 1 can"
        hom, seed, meta = setup_exp7_multistable(1)
        for u in hom.homeoUnits:
            u.criticalDeviation, u.currentVelocity = 3.0, 0.5
        make_multistable_callback()(hom, 0)
        u1, u2, u3 = hom.homeoUnits[:3]
        self.assertEqual(u1.criticalDeviation, 3.0)
        for u in (u2, u3):
            self.assertEqual((u.criticalDeviation, u.currentVelocity, u.currentOutput), (0, 0, 0))

    def testAshbysSequence(self):
        "Changes stop at values stable for both pairs, and the tests cause no more"
        for seed in (1, 3):
            hom, seed, meta = setup_exp7_multistable(seed)
            quiet(hom)
            u1 = hom.homeoUnits[0]
            count = []
            events = [(EXP7_TEST, lambda h: count.append(u1.uniselectorActivationCount))]
            run_with_events(hom, EXP7_END, events=events + exp7_test_events(),
                            tick_callback=make_multistable_callback())
            self.assertGreater(count[0], 0, 'seed %d: unit 1 never changed' % seed)
            self.assertEqual(u1.uniselectorActivationCount, count[0], 'seed %d: changes in the tests' % seed)
            self.assertEqual(exp7_pairs_stable(hom), (True, True))


class AshbyExp3Test(unittest.TestCase):
    '''DfB 8/9, Fig. 8/9/1: the operator forces 1 down; while 2 does not move
    the opposite way the trainer forces 3 to an extreme; the punishment makes
    unit 2's uniselector change 1->2 until 2 responds as desired, and the
    punishments cease.'''

    def assertAshbyWiring(self, hom):
        u1, u2, u3 = hom.homeoUnits[:3]
        self.assertEqual([u.uniselectorActive for u in (u1, u2, u3)], [False, True, False])
        for u in (u1, u2, u3):
            self.assertLess(signedWeight(u, u), 0)
        self.assertEqual(connection(u2, u1).state, 'uniselector')
        self.assertGreater(signedWeight(u2, u1), 0)                 # forbidden at the start
        self.assertAlmostEqual(signedWeight(u3, u2), EXP3_W23)
        self.assertAlmostEqual(signedWeight(u1, u3), EXP3_W31)
        self.assertTrue(ashby_stable(ashby_matrix([u1, u2, u3])))

    def testWiringHeadless(self):
        hom, seed, meta = setup_exp3_training(1)
        self.assertEqual(len(hom.homeoUnits), 3)
        self.assertAshbyWiring(hom)

    def testWiringGui(self):
        self.assertAshbyWiring(initializeAshbyExp3Training())

    def testTraining(self):
        """Punished, then 1->2 changed by a punishment, then the desired response.
        Training succeeds for most seeds, not all (25 of seeds 1-40): seeds
        that do."""
        for seed in (1, 3):
            hom, seed, meta = setup_exp3_training(seed)
            quiet(hom)
            trainer, punishments = make_trainer_callback()
            run_with_events(hom, EXP3_END, tick_callback=trainer)
            self.assertEqual(len(trainer.sequence), 10)
            self.assertEqual(len(punishments), trainer.sequence.count('P'))
            self.assertTrue(trainer.trained(hom), 'seed %d: %s, %s' % (
                seed, ''.join(trainer.sequence), trainer.changes_per_punishment))

    def testNoPunishmentNoTraining(self):
        "Without the trainer the same tests leave 1->2 alone"
        hom, seed, meta = setup_exp3_training(2)
        quiet(hom)
        u1, u2 = hom.homeoUnits[:2]
        before = signedWeight(u2, u1)
        trainer, punishments = make_trainer_callback(punish=False)
        run_with_events(hom, EXP3_END, tick_callback=trainer)
        self.assertEqual(punishments, [])
        self.assertNotIn('d', trainer.sequence)
        self.assertEqual(signedWeight(u2, u1), before)
