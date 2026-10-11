'''
Ashby's experiments from Design for a Brain, as reconstructed in
Simulator/AshbyOriginalExperiments.py (headless) and
Simulator/HomeoExperiments.py (GUI).
'''
import unittest

from Simulator.AshbyOriginalExperiments import (setup_exp2_self_reorganization,
                                                exp2_reversal_event, run_with_events,
                                                StabilityTracker)
from Simulator.HomeoExperiments import initializeAshbyExp2SelfReorganization


def connection(to_unit, from_unit):
    return [c for c in to_unit.inputConnections if c.incomingUnit is from_unit][0]


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
            hom._slowingFactor = 0
            hom.collectsData = False
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
