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
Helpers.ExperimentOrchestrator.run_concurrently, the loop the orchestrator
scripts (run_direct_vehicle_ga, run_phototaxis_comparison) share: every
experiment's output in its own log, only its PROGRESS lines on the console,
and the exit codes reported.  The experiments here are tiny Python
one-liners.
'''
import contextlib
import io
import os
import sys
import tempfile
import unittest

from Helpers.ExperimentOrchestrator import run_concurrently


def child(code):
    return [sys.executable, '-c', code]


class RunConcurrentlyTest(unittest.TestCase):

    def testLogsProgressAndExitCodes(self):
        with tempfile.TemporaryDirectory() as log_dir:
            commands = {
                1: child('print("PROGRESS: one started"); print("detail 1"); '
                         'import sys; print("oops", file=sys.stderr)'),
                2: child('print("detail 2"); raise SystemExit(3)'),
            }
            console = io.StringIO()
            with contextlib.redirect_stdout(console):
                codes = run_concurrently(commands, {1: 'first', 2: 'second'}, log_dir,
                                         cwd=log_dir, label_width=10)
            self.assertEqual(codes, {1: 0, 2: 3})
            with open(os.path.join(log_dir, 'exp1.log')) as f:
                log1 = f.read().splitlines()
            self.assertEqual(sorted(log1), sorted(['PROGRESS: one started', 'detail 1', 'oops']))
            with open(os.path.join(log_dir, 'exp2.log')) as f:
                self.assertEqual(f.read(), 'detail 2\n')
            shown = console.getvalue()
            self.assertIn('] one started\n', shown)
            self.assertNotIn('detail', shown)
            self.assertIn('  Exp 1 first      OK\n', shown)
            self.assertIn('  Exp 2 second     FAILED (exit 3)\n', shown)
            self.assertIn('Detailed logs: %s' % os.path.abspath(log_dir), shown)



class OrchestratorOptionsTest(unittest.TestCase):
    '''The orchestrators read their options with argparse: values are
    converted and checked, and an unknown option is refused.'''

    def quietly(self, parse, argv):
        with contextlib.redirect_stderr(io.StringIO()):
            return parse(argv)

    def testTheDirectVehicleGA(self):
        import run_direct_vehicle_ga as R
        a = R.parse_args(['--exp', '1', '--workers', '4', '--pop', '20', '--gen', '3',
                          '--steps', '100', '--noise-scheme', 'genome',
                          '--evals-per-individual', '2'])
        self.assertEqual((a.exp, a.workers, a.pop, a.gen, a.steps, a.noise_scheme, a.evals),
                         (1, 4, 20, 3, 100, 'genome', 2))
        self.assertIsNone(R.parse_args([]).exp)
        for argv in (['--pops', '20'], ['--noise-scheme', 'any'], ['--exp', '2'],
                     ['--evals-per-individual', '0'], ['--steps', 'many']):
            with self.subTest(argv=argv):
                with self.assertRaises(SystemExit):
                    self.quietly(R.parse_args, argv)

    def testThePhototaxisComparison(self):
        import run_phototaxis_comparison as R
        a = R.parse_args(['--exp', '3', '--workers', '2'])
        self.assertEqual((a.exp, a.workers), (3, 2))
        for argv in (['--exp', '4'], ['--seed', '1']):
            with self.subTest(argv=argv):
                with self.assertRaises(SystemExit):
                    self.quietly(R.parse_args, argv)


if __name__ == '__main__':
    unittest.main()
