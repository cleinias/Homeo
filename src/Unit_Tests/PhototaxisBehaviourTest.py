'''
Created on Oct 14, 2026

@author: stefano

The phototaxis experiments' setups and behaviour (review finding RE-07): the
adaptive setups' wiring, the uniselector types, what the fixed-weight
vehicles do (2b approaches the light, 2a turns away from it), the Newtonian
motors staying bounded, and the run's acquisition time and early stop.
'''
import contextlib
import io
import json
import os
import tempfile
import unittest

import HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_Ashby as A
import HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct as D
from HomeoExperiments.KheperaExperiments.phototaxis_common import (ACQUISITION_RADIUS,
                                                                   set_start_pose)
from Core.HomeoUniselectorAshby import HomeoUniselectorAshby
from Core.HomeoUniselectorContinuous import HomeoUniselectorContinuous
from Core.HomeoUniselectorUniformRandom import HomeoUniselectorUniformRandom


class _DataDirTest(unittest.TestCase):

    def setUp(self):
        # Cleanups run last-registered first: the directory goes after the
        # test's own cleanups (which close its trajectory files in it)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        saved = os.environ.get('HOMEO_DATA_DIR')
        os.environ['HOMEO_DATA_DIR'] = self.tmp.name
        self.addCleanup(lambda: os.environ.pop('HOMEO_DATA_DIR', None) if saved is None
                        else os.environ.__setitem__('HOMEO_DATA_DIR', saved))

    def setup(self, module, **kwargs):
        hom, backend, _ = module.setup_phototaxis(seed=5, **kwargs)
        self.addCleanup(backend.kheperaSimulation.saveTrajectory)
        return hom


def active(hom):
    "unit name -> {source name: (state, signed weight)} of its active connections"
    return {u.name: {c.incomingUnit.name: (c.state, c.switch * c.weight)
                     for c in u.inputConnections if c.status}
            for u in hom.homeoUnits}


class AdaptiveSetupsTest(_DataDirTest):

    def assertAdaptive(self, hom, adaptive):
        for u in hom.homeoUnits:
            self.assertEqual(u.uniselectorActive, u.name in adaptive, u.name)

    def testAshbyFixedTopology(self):
        '''Six units: sensors -> eyes -> crossed motors.  The eyes and motors
        adapt; their self-connections are manual, the others under the
        uniselector; the sensors are pure inputs.'''
        hom = self.setup(A)
        wiring = active(hom)
        expected = {'Left Eye': 'Left Sensor', 'Right Eye': 'Right Sensor',
                    'Left Motor': 'Right Eye', 'Right Motor': 'Left Eye'}
        for unit, source in expected.items():
            self.assertEqual(set(wiring[unit]), {unit, source})
            self.assertEqual(wiring[unit][unit][0], 'manual')
            self.assertEqual(wiring[unit][source][0], 'uniselector')
        self.assertEqual(wiring['Left Sensor'], {})
        self.assertEqual(wiring['Right Sensor'], {})
        self.assertAdaptive(hom, expected)

    def testAshbyRandomTopology(self):
        "Every connection of the eyes and motors on, all but self under the uniselector"
        hom = self.setup(A, topology='random')
        wiring = active(hom)
        names = [u.name for u in hom.homeoUnits]
        for unit in ('Left Eye', 'Right Eye', 'Left Motor', 'Right Motor'):
            self.assertEqual(set(wiring[unit]), set(names))
            for source, (state, _) in wiring[unit].items():
                self.assertEqual(state, 'manual' if source == unit else 'uniselector')
        self.assertEqual(wiring['Left Sensor'], {})

    def testDirectFixedTopology(self):
        '''Four units: each motor has its contralateral sensor (uniselector) and
        a negative manual self-connection, nothing else.'''
        hom = self.setup(D)
        wiring = active(hom)
        for unit, source in (('Left Motor', 'Right Sensor'), ('Right Motor', 'Left Sensor')):
            self.assertEqual(set(wiring[unit]), {unit, source})
            self.assertEqual(wiring[unit][unit][0], 'manual')
            self.assertLess(wiring[unit][unit][1], 0)
            self.assertEqual(wiring[unit][source][0], 'uniselector')
        self.assertAdaptive(hom, ('Left Motor', 'Right Motor'))

    def testDirectRandomTopology(self):
        hom = self.setup(D, topology='random')
        wiring = active(hom)
        names = [u.name for u in hom.homeoUnits]
        for unit in ('Left Motor', 'Right Motor'):
            self.assertEqual(set(wiring[unit]), set(names))
            for source, (state, weight) in wiring[unit].items():
                self.assertEqual(state, 'manual' if source == unit else 'uniselector')
            self.assertLess(wiring[unit][unit][1], 0)

    def testUniselectorTypes(self):
        kinds = {'ashby': HomeoUniselectorAshby, 'random': HomeoUniselectorUniformRandom,
                 'continuous': HomeoUniselectorContinuous}
        for module in (A, D):
            for kind, cls in kinds.items():
                with self.subTest(module=module.__name__, uniselector=kind):
                    hom = self.setup(module, uniselector_type=kind)
                    for u in hom.homeoUnits:
                        if u.uniselectorActive:
                            self.assertIs(type(u.uniselector), cls, u.name)


class VehicleBehaviourTest(_DataDirTest):
    '''The fixed-weight vehicles from (4, 4), the light at (7, 7), with
    logarithmic eyes, for 3000 ticks.  At 15 and 75 degrees the light is 30
    degrees to one side; the two runs mirror each other.'''

    def run_vehicle(self, wiring, heading, **kwargs):
        options = dict(fixed_weights=True, wiring=wiring, signs='++', heading=heading,
                       eye_response='log', total_steps=3000, report_interval=500,
                       quiet=True, seed=1)
        options.update(kwargs)
        return D.run_headless(**options)

    def testCrossedApproachesUncrossedTurnsAway(self):
        '''Braitenberg's 2b ends facing the light, more than 2 closer; his 2a
        turns its back on it (the light more than 90 degrees off its heading)
        and gets nowhere near it.'''
        for heading in (15, 75):
            with self.subTest(heading=heading):
                b = self.run_vehicle('crossed', heading)
                a = self.run_vehicle('uncrossed', heading)
                self.assertTrue(b['start_sees_light'])
                self.assertLess(abs(b['final_bearing']), 5)
                self.assertLess(b['final_dist'], b['start_dist'] - 2)
                self.assertGreater(abs(a['final_bearing']), 90)
                self.assertGreater(a['min_dist'], b['start_dist'] - 0.1)

    def testMirrorImages(self):
        '''With the light 30 degrees to the left or to the right, the runs are
        mirror images: the same distance, opposite bearings (the e-puck's
        sensors are mirror-symmetric to 0.1 degree).'''
        for wiring in ('crossed', 'uncrossed'):
            with self.subTest(wiring=wiring):
                left, right = self.run_vehicle(wiring, 15), self.run_vehicle(wiring, 75)
                self.assertAlmostEqual(left['final_dist'], right['final_dist'], delta=0.005)
                self.assertAlmostEqual(left['final_bearing'], -right['final_bearing'], delta=1)

    def testNewtonianMotorsStayBounded(self):
        '''The fixed-weight motor's self-connection is a spring (no viscosity):
        its deviation oscillates, its amplitude set by the light it sees, and
        stays far from the clip at maxDeviation (about 1.2 of 10 here), for
        either wiring.'''
        for wiring in ('crossed', 'uncrossed'):
            with self.subTest(wiring=wiring):
                hom, backend, _ = D.setup_phototaxis(fixed_weights=True, wiring=wiring, seed=1)
                self.addCleanup(backend.kheperaSimulation.saveTrajectory)
                set_start_pose(backend.kheperaSimulation.allBodies['Khepera'], 4, 4, 45)
                hom.slowingFactor = 0
                hom.collectsData = False
                motors = [u for u in hom.homeoUnits if 'Motor' in u.name]
                deviations = []
                for tick in range(5, 3001, 5):     # sampled every 5 ticks
                    hom.runFor(tick)
                    deviations.append(max(abs(u.criticalDeviation) for u in motors))
                self.assertLess(max(deviations), 0.25 * motors[0].maxDeviation)


class AcquisitionTest(_DataDirTest):
    '''first_acq is the first report tick at which the vehicle is within
    ACQUISITION_RADIUS of the light; an early stop ends the run at the first
    report within its distance.'''

    def run_vehicle(self, total_steps, **kwargs):
        return D.run_headless(fixed_weights=True, wiring='crossed', signs='++', heading=45,
                              eye_response='log', total_steps=total_steps, report_interval=100,
                              quiet=True, seed=1, **kwargs)

    def testFirstAcquisition(self):
        r = self.run_vehicle(5000)
        first = r['first_acq']
        self.assertIsNotNone(first)
        self.assertTrue(r['acquired'])
        self.assertEqual(first % 100, 0)
        before = self.run_vehicle(first - 100)
        self.assertIsNone(before['first_acq'])
        self.assertGreaterEqual(before['min_dist'], ACQUISITION_RADIUS)
        at = self.run_vehicle(first)
        self.assertLess(at['final_dist'], ACQUISITION_RADIUS)
        self.assertEqual(at['first_acq'], first)

    def testNeverAcquired(self):
        r = self.run_vehicle(500)
        self.assertIsNone(r['first_acq'])
        self.assertFalse(r['acquired'])

    def testEarlyStop(self):
        r = self.run_vehicle(5000, early_stop_distance=2.0)
        self.assertTrue(r['early_stopped'])
        self.assertLess(r['final_dist'], 2.0)
        self.assertEqual(r['steps_run'], r['hom'].time)
        before = self.run_vehicle(r['steps_run'] - 100)
        self.assertGreaterEqual(before['final_dist'], 2.0)
        self.assertFalse(self.run_vehicle(500, early_stop_distance=2.0)['early_stopped'])

    def testTheRunRecordsItsEarlyStop(self):
        for distance in (2.0, None):
            r = self.run_vehicle(500, early_stop_distance=distance)
            with open(r['json_path']) as f:
                self.assertEqual(json.load(f)['settings']['early_stop_distance'], distance)

    def testADarkRunThatReachesTheSourceIsAcquired(self):
        '''--dark runs as light runs do: no early stop, so a vehicle that
        reaches the darkness source is acquired.  (With a stop at 1.5 this
        run would end at t=2800, 1.479 from the source, not acquired.)'''
        options = D.common.parse_common_args(['x', '--dark'])
        self.assertIsNone(options['early_stop_distance'])
        r = D.run_headless(fixed_weights=True, wiring='crossed', signs='--', heading=45,
                           eye_response='log', total_steps=5000, report_interval=100,
                           quiet=True, seed=1, light_intensity=options['light_intensity'],
                           early_stop_distance=options['early_stop_distance'])
        self.assertFalse(r['early_stopped'])
        self.assertTrue(r['acquired'])
        self.assertEqual(r['steps_run'], 5000)

    def testAnEarlyStopOutsideTheAcquisitionRadiusIsWarned(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(D.common.parse_common_args(['x', '--early-stop', '0.5'])
                             ['early_stop_distance'], 0.5)
        self.assertEqual(err.getvalue(), '')
        with contextlib.redirect_stderr(err):
            D.common.parse_common_args(['x', '--early-stop', '1.5'])
        self.assertIn('acquisition radius', err.getvalue())


if __name__ == '__main__':
    unittest.main()
