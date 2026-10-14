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
                                 synchronous_stepping=False, stable_draws=True,
                                 eye_response='log')
                self.assertFalse(r['synchronous_stepping'])
                self.assertTrue(r['stable_draws'])
                self.assertEqual(r['eye_threshold'], 1.0)
                text = json.dumps(json.load(open(r['json_path'])))
                self.assertIn('"synchronous_stepping": false', text)
                self.assertIn('"eye_response": "log"', text)

    def testRimEyes(self):
        '''--rim-eyes puts the eyes back on the rim (eyeRadiusRatio 1), as in
        the runs before 13 Oct 2026; the runs record where the eyes sat.'''
        import json
        self.assertEqual(D.common.parse_common_args(['x'])['eye_radius_ratio'], 0.5)
        self.assertEqual(D.common.parse_common_args(['x', '--rim-eyes'])['eye_radius_ratio'], 1.0)
        for name, M in EXPERIMENTS.items():
            for ratio, tag in ((0.5, ''), (1.0, '_rimeyes')):
                with self.subTest(name, ratio=ratio):
                    r = self.quietly(M.run_headless, total_steps=20, seed=3, quiet=True,
                                     eye_radius_ratio=ratio)
                    robot = r['backend'].kheperaSimulation.allBodies['Khepera']
                    self.assertEqual(robot.eyeRadiusRatio, ratio)
                    self.assertEqual(r['eye_radius_ratio'], ratio)
                    self.assertEqual('_rimeyes' in os.path.basename(r['log_path']), bool(tag))
                    text = json.dumps(json.load(open(r['json_path'])))
                    self.assertIn('"eye_radius_ratio": %s' % ratio, text)
        with mock.patch.object(D, 'run_headless') as run:
            self.quietly(D.main, ['x', '--rim-eyes'])
        self.assertEqual(run.call_args.kwargs['eye_radius_ratio'], 1.0)

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
                '--eye-response', 'log', '--spin', '0.05', '--async-stepping',
                '--stable-draws', '--continuous']
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
                self.assertFalse(kwargs['synchronous_stepping'])
                self.assertTrue(kwargs['stable_draws'])
                self.assertEqual(kwargs['uniselector_type'], 'continuous')


if __name__ == '__main__':
    unittest.main()
