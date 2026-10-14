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
