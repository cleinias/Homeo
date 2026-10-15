'''
Created on Oct 14, 2026

@author: stefano

The array scripts in hpc/ (review findings SH-05, SH-06, SH-07):
run_array_local.sh's dry run -- which tasks it would run, with which seeds,
and which it skips as finished -- and aggregate_array.py, which joins the
tasks' batch CSVs.  Both run as the user runs them, in a subprocess, on files
made up in a temporary directory; nothing is simulated.
'''
import os
import subprocess
import sys
import tempfile
import unittest

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HPC = os.path.join(os.path.dirname(SRC), 'hpc')

CSV_HEADER = 'seed,env_seed,acquired,first_acq,final_dist,min_dist,min_t,steps_run,wall_time\n'


def write_batch_csv(directory, serial, seed=1, stamp='2026-10-01-13-58-11'):
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, 'batch_direct_continuous_light_%s-%02d.csv' % (stamp, serial))
    with open(path, 'w') as f:
        f.write(CSV_HEADER)
        f.write('%d,%d,True,1000,0.5,0.4,900,6000,12.5\n' % (seed, seed))
    return path


class RunArrayLocalDryRunTest(unittest.TestCase):

    def dryRun(self, rundir, *options):
        env = dict(os.environ, PYTHON=sys.executable,
                   PYTHONPATH=SRC + os.pathsep + os.environ.get('PYTHONPATH', ''))
        r = subprocess.run(['bash', os.path.join(HPC, 'run_array_local.sh'), '--dry-run',
                            '-n', '1', '-o', rundir] + list(options),
                           capture_output=True, text=True, timeout=300, env=env)
        self.assertEqual(r.returncode, 0, r.stdout[-2000:] + r.stderr[-2000:])
        return r.stdout

    def testSeedsByTaskIndexOrByList(self):
        '''Task i runs seed 20260930 + i, as on Grace, or the i-th entry of
        --seeds and --env-seeds, counting from the first task of the range.'''
        with tempfile.TemporaryDirectory() as rundir:
            out = self.dryRun(rundir, '-a', '3-4')
            self.assertIn('task 3: would run with seed 20260933\n', out)
            self.assertIn('task 4: would run with seed 20260934\n', out)
            out = self.dryRun(rundir, '-a', '3-4', '--seeds', '5,5', '--env-seeds', '7,8')
            self.assertIn('task 3: would run with seed 5, env seed 7\n', out)
            self.assertIn('task 4: would run with seed 5, env seed 8\n', out)

    def testFinishedTasksOfAnEarlierDayAreSkipped(self):
        '''A task whose batch CSV is in an earlier day's SimsData-<date>/ is
        finished: resuming the array on a later day must not run it again
        (SH-05: it was run again, and the run then had two CSVs for it).'''
        with tempfile.TemporaryDirectory() as rundir:
            write_batch_csv(os.path.join(rundir, 'SimsData-2020-01-01'), 2)
            write_batch_csv(os.path.join(rundir, 'SimsData-2020-01-02'), 12)
            out = self.dryRun(rundir, '-a', '1-3')
            self.assertIn('task 2: already complete, skipping', out)
            self.assertIn('task 1: would run', out)
            self.assertIn('task 3: would run', out)
            self.assertNotIn('task 2: would run', out)


class AggregateArrayTest(unittest.TestCase):

    def aggregate(self, rundir, *options):
        return subprocess.run([sys.executable, os.path.join(HPC, 'aggregate_array.py'), rundir]
                              + list(options), capture_output=True, text=True, timeout=120)

    def testTasksFromSerialsAndLegacyDirectories(self):
        '''The task index comes from the serial after the timestamp, or, for
        the old layout, from the task_<i>/ directory; a combined table
        written before is not an input.'''
        with tempfile.TemporaryDirectory() as rundir:
            write_batch_csv(os.path.join(rundir, 'SimsData-2026-10-01'), 7, seed=107)
            write_batch_csv(os.path.join(rundir, 'SimsData-2026-10-02'), 12, seed=112)
            legacy = os.path.join(rundir, 'task_3', 'SimsData-2026-09-30')
            os.makedirs(legacy)
            with open(os.path.join(legacy, 'batch_direct_continuous_light_2026-09-30-10-00-07.csv'), 'w') as f:
                f.write(CSV_HEADER + '103,103,False,,2.0,1.5,500,6000,10.0\n')
            out = os.path.join(rundir, 'combined.csv')
            r = self.aggregate(rundir, '-o', out)
            self.assertEqual(r.returncode, 0, r.stderr)
            import pandas as pd
            df = pd.read_csv(out)
            self.assertEqual(df.task.tolist(), [3, 7, 12])
            self.assertEqual(df.seed.tolist(), [103, 107, 112])
            self.assertIn('acquired: 2/3', r.stdout)
            # the combined table under the run directory is not read back
            with open(os.path.join(rundir, 'batch_direct_ALL.csv'), 'w') as f:
                f.write(open(out).read())
            r = self.aggregate(rundir)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn('runs: 3', r.stdout)

    def testTwoCSVsForOneTaskAreRefused(self):
        with tempfile.TemporaryDirectory() as rundir:
            write_batch_csv(os.path.join(rundir, 'SimsData-2026-10-01'), 4)
            write_batch_csv(os.path.join(rundir, 'SimsData-2026-10-02'), 4)
            r = self.aggregate(rundir)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn('more than one CSV claims the same task index: [4]', r.stderr)

    def testAnEmptyRunDirectory(self):
        with tempfile.TemporaryDirectory() as rundir:
            r = self.aggregate(rundir)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn('no per-task CSVs', r.stderr)


if __name__ == '__main__':
    unittest.main()
