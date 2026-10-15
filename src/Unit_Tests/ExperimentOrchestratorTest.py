'''
Created on Oct 14, 2026

@author: stefano

Helpers.ExperimentOrchestrator.run_concurrently, the loop the orchestrator
scripts (run_validation_300k, run_direct_vehicle_ga,
run_phototaxis_comparison) share since review finding SH-14: every
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


if __name__ == '__main__':
    unittest.main()
