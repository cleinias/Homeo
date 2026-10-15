'''
Created on Oct 14, 2026

@author: stefano

The array scripts in hpc/ (review findings SH-05, SH-06, SH-07):
run_array_local.sh's dry run: which tasks it would run, with which seeds,
and which it skips as finished.  It runs as the user runs it, in a
subprocess, on files made up in a temporary directory; nothing is simulated.
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


if __name__ == '__main__':
    unittest.main()
