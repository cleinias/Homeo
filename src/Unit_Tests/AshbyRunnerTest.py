# Copyright (C) 2026 Stefano Franchi
#
# This file is part of Homeo, a simulation of Ashby's homeostat and of
# homeostat-controlled robots.
#
# Homeo is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# Homeo is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with Homeo.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

'''
run_ashby_original_experiments.py, the command line of Ashby's experiments:
its options, its seeding (one seed, one run), and the records and the
summary it writes (stable stretches, the outcome of each disturbance, the
protocol's own measures).  Short runs, in a temporary directory.
'''
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _rows(path):
    "A statelog's data, without its date line"
    with open(path) as f:
        return [line for line in f if not line.startswith('# date')]


class AshbyRunnerTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def cli(self, *args):
        return subprocess.run([sys.executable, 'run_ashby_original_experiments.py',
                               '--output-dir', self.tmp.name] + list(args),
                              cwd=SRC, capture_output=True, text=True, timeout=300)

    def testTheCommandLineRunsAnExperimentFromItsSeed(self):
        runs = [self.cli('--exp', '2', '--seed', '5', '--ticks', '300') for i in range(2)]
        for r in runs:
            self.assertEqual(r.returncode, 0, r.stdout[-1500:] + r.stderr[-1500:])
            self.assertIn('Seed: 5', r.stdout)
        statelogs = sorted(f for f in os.listdir(self.tmp.name) if f.endswith('.statelog'))
        jsons = sorted(f for f in os.listdir(self.tmp.name) if f.endswith('.json'))
        self.assertEqual(len(statelogs), 2)
        self.assertTrue(all(f.startswith('ashby_exp2_seed5_') for f in statelogs + jsons))
        first, second = [_rows(os.path.join(self.tmp.name, f)) for f in statelogs]
        self.assertGreater(len(first), 300)
        self.assertEqual(first, second)                     # one seed, one run
        with open(os.path.join(self.tmp.name, jsons[0])) as f:
            record = json.load(f)
        self.assertEqual(record['seed'], 5)
        self.assertIn('INITIAL CONDITIONS', record)
        self.assertIn('FINAL CONDITIONS', record)

    def testAnUnknownExperimentIsRefused(self):
        for args in (('--exp', '8'), ('--exp', '0'), ('--fig', '3')):
            with self.subTest(args=args):
                r = self.cli(*args)
                self.assertEqual(r.returncode, 2, r.stdout[-500:])
                self.assertIn('invalid choice', r.stderr)

    def testRunsOfOneSecondKeepTheirFiles(self):
        sys.path.insert(0, SRC)
        import run_ashby_original_experiments as R
        from unittest import mock
        with mock.patch.object(R.time, 'strftime', return_value='2026-01-01-00-00-00'), \
                contextlib.redirect_stdout(io.StringIO()):
            paths = [R.run_experiment(2, seed=5, total_ticks=50, output_dir=self.tmp.name)
                     ['statelog_path'] for i in range(2)]
        self.assertEqual([os.path.basename(p) for p in paths],
                         ['ashby_exp2_seed5_2026-01-01-00-00-00.statelog',
                          'ashby_exp2_seed5_2026-01-01-00-00-00-2.statelog'])

    def testTheSummary(self):
        sys.path.insert(0, SRC)
        import run_ashby_original_experiments as R
        with contextlib.redirect_stdout(io.StringIO()):
            s = R.run_experiment(1, seed=11, output_dir=self.tmp.name)
        self.assertEqual((s['experiment'], s['seed']), (1, 11))
        for key in ('stability_achieved_at', 'stable_since', 'currently_stable',
                    'stable_episodes', 'total_uniselector_firings', 'statelog_path',
                    'json_path', 'disturbances', 'protocol'):
            self.assertIn(key, s)
        # the stretches are [onset, end] pairs in order, inside the run
        episodes = s['stable_episodes']
        self.assertTrue(episodes)
        for (onset, end), following in zip(episodes, episodes[1:] + [[None, None]]):
            self.assertLessEqual(onset, end)
            self.assertLessEqual(end, s['total_ticks'])
            if following[0] is not None:
                self.assertLess(end, following[0])
        # each disturbance's outcome is one of the three, a latency only when re-stabilised
        self.assertTrue(s['disturbances'])
        for d in s['disturbances']:
            self.assertIn(d['outcome'], ('held', 'restabilised', 'never'))
            self.assertEqual(d['latency'] is not None, d['outcome'] == 'restabilised')
        self.assertEqual(s['currently_stable'], s['stable_since'] is not None)


if __name__ == '__main__':
    unittest.main()
