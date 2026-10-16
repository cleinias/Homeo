'''
Created on Oct 13, 2026

@author: stefano

The two phototaxis experiments share their seeding, uniselectors, runners,
records and options (phototaxis_common; review findings RE-06, RE-09): the
Ashby experiment had no seeds in its batches, no run tag in its file names,
no stepping, stability or eye options, and an unknown uniselector type, or
'random' in a batch's name, passed as Ashby's.  --visualize dropped most
options.
'''
import contextlib
import csv
import io
import os
import tempfile
import unittest
from unittest import mock

import HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct as D
import HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_Ashby as A
from Helpers.RobotTrajectoryWriter import configureTrajectoryDefaults

EXPERIMENTS = {'direct': D, 'ashby': A}


class PhototaxisCommonTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ['HOMEO_DATA_DIR'] = self.tmp.name
        configureTrajectoryDefaults(enabled=False)

    def tearDown(self):
        configureTrajectoryDefaults(enabled=True)
        os.environ.pop('HOMEO_DATA_DIR', None)
        os.environ.pop('HOMEO_RUN_TAG', None)
        self.tmp.cleanup()

    def quietly(self, f, *args, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return f(*args, **kwargs)

    def testUnknownUniselectorTypeIsAnError(self):
        for name, M in EXPERIMENTS.items():
            with self.subTest(name):
                with self.assertRaises(ValueError):
                    M.setup_phototaxis(seed=1, uniselector_type='ashbyy')

    def testBatchesAreSeededAndTagged(self):
        for name, M in EXPERIMENTS.items():
            with self.subTest(name):
                results = self.quietly(M.run_batch, n_runs=2, total_steps=50, seed=5,
                                       uniselector_type='random')
                self.assertEqual([r['seed'] for r in results], [5, 6])
                csv_dir = os.path.dirname(results[0]['log_path'])
                names = [f for f in os.listdir(csv_dir)
                         if f.startswith('batch_%s_random_light' % name)]
                self.assertEqual(len(names), 1, os.listdir(csv_dir))
                rows = list(csv.DictReader(open(os.path.join(csv_dir, names[0]))))
                self.assertEqual([r['seed'] for r in rows], ['5', '6'])
                # each run of the batch has its own files
                self.assertIn('r01', results[0]['log_path'])
                self.assertIn('r02', results[1]['log_path'])

    def testRunsRecordTheirSettings(self):
        import json
        for name, M in EXPERIMENTS.items():
            with self.subTest(name):
                r = self.quietly(M.run_headless, total_steps=20, seed=3, quiet=True,
                                 stable_draws=True, eye_response='log')
                self.assertTrue(r['stable_draws'])
                self.assertEqual(r['eye_threshold'], 1.0)
                text = json.dumps(json.load(open(r['json_path'])))
                self.assertIn('"eye_response": "log"', text)

    def testTheRobot(self):
        '''The robot is the e-puck2 by default; --robot kjunior gives the
        K-Junior.  Runs record the robot.'''
        import json
        parse = D.common.parse_common_args
        self.assertEqual(parse(['x'])['robot'], 'epuck2')
        self.assertEqual(parse(['x', '--robot', 'kjunior'])['robot'], 'kjunior')
        for argv in (['x', '--robot', 'khepera'], ['x', '--robot', 'kjunior-rim'],
                     ['x', '--rim-eyes']):
            with self.assertRaises(SystemExit):
                self.quietly(parse, argv)
        for name, M in EXPERIMENTS.items():
            for robot, ratio, tag in (('epuck2', None, ''), ('kjunior', 0.5, '_kjunior')):
                with self.subTest(name, robot=robot):
                    r = self.quietly(M.run_headless, total_steps=20, seed=3, quiet=True,
                                     robot=robot)
                    body = r['backend'].kheperaSimulation.allBodies['Khepera']
                    self.assertEqual((body.model, body.eyeRadiusRatio), (robot, ratio))
                    self.assertEqual(r['robot'], robot)
                    stem = os.path.basename(r['log_path'])
                    self.assertEqual('_kjunior' in stem, bool(tag))
                    settings = json.load(open(r['json_path']))['settings']
                    self.assertEqual(settings['robot'], robot)
        with mock.patch.object(D, 'run_headless') as run:
            self.quietly(D.main, ['x', '--robot', 'kjunior'])
        self.assertEqual(run.call_args.kwargs['robot'], 'kjunior')

    @staticmethod
    def homeostat(r):
        "The run's homeostat as built: every unit's parameters and its input weights."
        return [(u.name, u.mass, u.viscosity, u.noise,
                 [(c.weight, c.switch, c.noise, c.status) for c in u.inputConnections])
                for u in r['hom'].homeoUnits]

    @staticmethod
    def pose(r):
        return (r['start_x'], r['start_y'], r['start_heading'])

    def testTheStartPoseHasItsOwnStream(self):
        '''The environment's stream (--env-seed) draws the start pose; the
        homeostat's (--seed) everything else.  Until 14 Oct 2026 the pose
        came from the homeostat's stream, after the units: one seed drove
        both, and the pose depended on the vehicle's setup.'''
        import numpy as np
        for name, M in EXPERIMENTS.items():
            with self.subTest(name):
                hom, backend, seed = M.setup_phototaxis(seed=3)
                robot = backend.kheperaSimulation.allBodies['Khepera']
                before = np.random.get_state()[1].copy()
                M.common.place_robot(robot, random_start=True, env_seed=7)
                self.assertTrue((np.random.get_state()[1] == before).all())

        def run(M, seed, env_seed):
            return self.quietly(M.run_headless, total_steps=20, quiet=True, seed=seed,
                                env_seed=env_seed, random_start=True)
        for name, M in EXPERIMENTS.items():
            with self.subTest(name):
                a, b, c = run(M, 3, 7), run(M, 3, 8), run(M, 4, 7)
                self.assertEqual(self.homeostat(a), self.homeostat(b))
                self.assertNotEqual(self.pose(a), self.pose(b))
                self.assertEqual(self.pose(a), self.pose(c))
                self.assertNotEqual(self.homeostat(a), self.homeostat(c))
                self.assertEqual((a['seed'], a['env_seed']), (3, 7))
        # one environment seed, one start pose, whatever the vehicle
        self.assertEqual(self.pose(run(D, 3, 7)), self.pose(run(A, 5, 7)))

    def testTheEnvironmentSeedDefaultsToTheSeed(self):
        import json
        r = self.quietly(D.run_headless, total_steps=20, quiet=True, seed=3,
                         random_heading=True)
        self.assertEqual(r['env_seed'], 3)
        self.assertEqual(json.load(open(r['json_path']))['settings']['env_seed'], 3)
        self.assertEqual(self.pose(r), self.pose(self.quietly(
            D.run_headless, total_steps=20, quiet=True, seed=4, env_seed=3,
            random_heading=True)))

    def testBatchesVaryOneStreamOrBoth(self):
        for vary, seeds, env_seeds in (('both', [5, 6, 7], [9, 10, 11]),
                                       ('homeostat', [5, 6, 7], [9, 9, 9]),
                                       ('env', [5, 5, 5], [9, 10, 11])):
            with self.subTest(vary):
                results = self.quietly(D.run_batch, n_runs=3, total_steps=20, seed=5,
                                       env_seed=9, batch_vary=vary, random_start=True)
                self.assertEqual([r['seed'] for r in results], seeds)
                self.assertEqual([r['env_seed'] for r in results], env_seeds)
                self.assertEqual(len({self.pose(r) for r in results}),
                                 1 if vary == 'homeostat' else 3)
        csv_dir = os.path.dirname(results[0]['log_path'])
        name = [f for f in os.listdir(csv_dir) if f.startswith('batch_')][0]
        rows = list(csv.DictReader(open(os.path.join(csv_dir, name))))
        self.assertIn('env_seed', rows[0])
        # an unset env seed follows the seed, and a fixed stream gets one seed
        results = self.quietly(D.run_batch, n_runs=2, total_steps=20, seed=5)
        self.assertEqual([r['env_seed'] for r in results], [5, 6])
        results = self.quietly(D.run_batch, n_runs=2, total_steps=20, batch_vary='env')
        self.assertEqual(results[0]['seed'], results[1]['seed'])
        self.assertEqual(results[1]['env_seed'], results[0]['env_seed'] + 1)

    def testAnUnknownOptionIsRefused(self):
        "A misspelt or unknown option stops the run instead of being ignored"
        for M in EXPERIMENTS.values():
            for argv in (['x', '--stable-draw'], ['x', '--steps', '10', '--frobnicate']):
                with mock.patch.object(D.common, 'run_headless') as run:
                    with self.assertRaisesRegex(SystemExit, 'Unknown option'):
                        self.quietly(M.main, argv)
                run.assert_not_called()
        with mock.patch.object(D.common, 'run_headless') as run:
            self.quietly(D.main, ['x', '--fixed-weights', '--signs', '--', '--motor',
                                  'aristotelian', '--start-range', '1', '2', '--random-start',
                                  '--steps', '10'])
        run.assert_called_once()
        with mock.patch.object(D.common, 'run_headless'):
            with self.assertRaisesRegex(SystemExit, 'Unknown option'):
                self.quietly(A.main, ['x', '--fixed-weights'])

    def testSeedOptions(self):
        parse = D.common.parse_common_args
        o = parse(['x', '--env-seed', '7', '--batch', '2', '--batch-vary', 'env'])
        self.assertEqual((o['env_seed'], o['batch_vary']), (7, 'env'))
        self.assertEqual((parse(['x'])['env_seed'], parse(['x'])['batch_vary']), (None, 'both'))
        for argv in (['x', '--env-seed', 'a'], ['x', '--batch', '2', '--batch-vary', 'all'],
                     ['x', '--batch-vary', 'env']):
            with self.assertRaises(SystemExit):
                self.quietly(parse, argv)
        with mock.patch.object(D.common, 'run_batch') as batch:
            self.quietly(D.main, ['x', '--batch', '2', '--env-seed', '7',
                                  '--batch-vary', 'homeostat'])
        self.assertEqual((batch.call_args.kwargs['env_seed'],
                          batch.call_args.kwargs['vary']), (7, 'homeostat'))
        with mock.patch.object(D.common, 'run_visualized') as visualize:
            self.quietly(D.main, ['x', '--visualize', '--env-seed', '7'])
        self.assertEqual(visualize.call_args.kwargs['env_seed'], 7)

    def testVisualizeTakesEveryOption(self):
        argv = ['x', '--visualize', '--dark', '--seed', '3', '--heading', '45',
                '--eye-response', 'log', '--spin', '0.05', '--stable-draws',
                '--continuous']
        for name, M in EXPERIMENTS.items():
            with self.subTest(name):
                with mock.patch.object(M.common, 'run_visualized') as visualize, \
                        mock.patch.object(M, 'setup_phototaxis') as setup:
                    self.quietly(M.main, argv)
                    run_setup = visualize.call_args.args[0]
                    run_setup()
                kwargs = dict(visualize.call_args.kwargs, **setup.call_args.kwargs)
                self.assertEqual(kwargs['light_intensity'], -100)
                self.assertEqual(kwargs['seed'], 3)
                self.assertEqual(kwargs['heading'], 45)
                self.assertEqual(kwargs['eye_response'], 'log')
                self.assertEqual(kwargs['spin'], 0.05)
                self.assertTrue(kwargs['stable_draws'])
                self.assertEqual(kwargs['uniselector_type'], 'continuous')


if __name__ == '__main__':
    unittest.main()
