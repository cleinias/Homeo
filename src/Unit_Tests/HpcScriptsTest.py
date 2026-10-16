'''
@author: stefano

The array scripts in hpc/:
run_array_local.sh's dry run -- which tasks it would run, with which seeds,
and which it skips as finished -- aggregate_array.py, which joins the
tasks' batch CSVs, and grace_fixedB2.slurm's task set-up, with srun, the
Python module and the venv replaced by stubs.  They run as the user runs
them, in a subprocess, on files made up in a temporary directory; nothing is
simulated.
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
        --seeds and --env-seeds, whatever the range: two ranges given the
        same lists take different entries.'''
        with tempfile.TemporaryDirectory() as rundir:
            out = self.dryRun(rundir, '-a', '3-4')
            self.assertIn('task 3: would run with seed 20260933\n', out)
            self.assertIn('task 4: would run with seed 20260934\n', out)
            lists = ('--seeds', '1,2,5,6', '--env-seeds', '11,12,7,8')
            out = self.dryRun(rundir, '-a', '3-4', *lists)
            self.assertIn('task 3: would run with seed 5, env seed 7\n', out)
            self.assertIn('task 4: would run with seed 6, env seed 8\n', out)
            out = self.dryRun(rundir, '-a', '1-2', *lists)
            self.assertIn('task 1: would run with seed 1, env seed 11\n', out)
            self.assertIn('task 2: would run with seed 2, env seed 12\n', out)

    def testOptionsAfterTwoDashesGoToTheExperiment(self):
        '''Anything after -- goes to the experiment as it is, and the run
        directory's PROVENANCE.txt records the command and the commit.'''
        with tempfile.TemporaryDirectory() as rundir:
            out = self.dryRun(rundir, '-a', '1-1', '--', '--stable-draws', '--dark')
            self.assertIn('task 1: would run with seed 20260931\n     and --stable-draws --dark\n',
                          out)
            provenance = open(os.path.join(rundir, 'PROVENANCE.txt')).read()
            self.assertIn('command hpc/run_array_local.sh --dry-run -n 1 -o %s -a 1-1 -- '
                          '--stable-draws --dark\n' % rundir, provenance)
            self.assertIn('experiment options --stable-draws --dark\n', provenance)
            version = subprocess.run(['git', '-C', SRC, 'describe', '--always', '--dirty'],
                                     capture_output=True, text=True).stdout.strip()
            self.assertIn('code %s ' % version, provenance)

    def testFinishedTasksOfAnEarlierDayAreSkipped(self):
        '''A task whose batch CSV is in an earlier day's SimsData-<date>/ is
        finished: resuming the array on a later day must not run it again,
        which would leave the run two CSVs for it.'''
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

    def testTasksFromSerialsAndTaskDirectories(self):
        '''The task index comes from the serial after the timestamp, or, for
        a run laid out in task_<i>/ directories, from the directory; a
        combined table written before is not an input.'''
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


class GraceFixedB2Test(unittest.TestCase):
    '''The slurm script up to its srun, which a stub replaces: it prints the
    arguments the task would run the experiment with.'''

    SCRIPT = 'grace_fixedB2.slurm'

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = self.tmp.name
        self.src = os.path.join(root, 'Homeo')
        os.makedirs(os.path.join(self.src, 'hpc'))
        os.makedirs(os.path.join(self.src, 'src'))
        with open(os.path.join(self.src, 'hpc', 'load_python.sh'), 'w') as f:
            f.write('homeo_load_python() { :; }\n')
        self.venv = os.path.join(root, 'venv')
        os.makedirs(os.path.join(self.venv, 'bin'))
        open(os.path.join(self.venv, 'bin', 'activate'), 'w').close()
        self.bin = os.path.join(root, 'bin')
        os.makedirs(self.bin)
        with open(os.path.join(self.bin, 'srun'), 'w') as f:
            f.write('#!/bin/sh\necho "SRUN $*"\n')
        os.chmod(os.path.join(self.bin, 'srun'), 0o755)
        self.scratch = os.path.join(root, 'scratch')

    def tearDown(self):
        self.tmp.cleanup()

    def task(self, task_id, *arguments):
        env = dict(os.environ, HOMEO_SRC=self.src, VENV=self.venv, SCRATCH=self.scratch,
                   SLURM_ARRAY_TASK_ID=str(task_id), SLURM_ARRAY_JOB_ID="999", TMPDIR=self.tmp.name,
                   PATH=self.bin + os.pathsep + os.environ['PATH'])
        return subprocess.Popen(['bash', os.path.join(HPC, self.SCRIPT)] + list(arguments),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)

    def run_task(self, task_id, *arguments):
        p = self.task(task_id, *arguments)
        out, err = p.communicate(timeout=120)
        self.assertEqual(p.returncode, 0, out + err)
        return out

    def testSpinIsComparedAsANumber(self):
        '''SPIN 0.0 is no spin, as 0 is: it is compared as a number, not a string.'''
        for spin in ('0', '0.0', '0.00'):
            out = self.run_task(1, '4', '8', spin)
            self.assertNotIn('--spin', out, spin)
            self.assertIn('fixedB2-r4to8-traj1-999', out, spin)
        out = self.run_task(1, '4', '8', '0.05')
        self.assertIn('--spin 0.05', out)
        self.assertIn('fixedB2-r4to8-cw0.05-traj1-999', out)
        out = self.run_task(1, '4', '8', '-0.05')
        self.assertIn('fixedB2-r4to8-ccw0.05-traj1-999', out)
        p = self.task(1, '4', '8', 'fast')
        p.communicate(timeout=120)
        self.assertNotEqual(p.returncode, 0)

    def testOneProvenanceAmongConcurrentTasks(self):
        '''Tasks starting together leave exactly one, whole PROVENANCE.txt
        and no temporary copies.'''
        tasks = [self.task(i, '2', '6') for i in range(1, 17)]
        for p in tasks:
            out, err = p.communicate(timeout=120)
            self.assertEqual(p.returncode, 0, out + err)
        rundir = os.path.join(self.scratch, 'homeo', 'fixedB2-r2to6-traj1-999')
        self.assertEqual(os.listdir(rundir), ['PROVENANCE.txt'])
        with open(os.path.join(rundir, 'PROVENANCE.txt')) as f:
            lines = f.read().splitlines()
        self.assertEqual(sum(l.startswith('generated by') for l in lines), 1)
        self.assertTrue(lines[-1].startswith('python '), lines)



class GraceOu6MTest(GraceFixedB2Test):
    '''grace_ou_6M.slurm up to its srun, as GraceFixedB2Test.'''

    SCRIPT = 'grace_ou_6M.slurm'

    def testOptionsAfterTwoDashesGoToTheExperiment(self):
        out = self.run_task(3, '--', '--stable-draws', '--robot', 'kjunior')
        srun = [l for l in out.splitlines() if l.startswith('SRUN ')][0]
        self.assertIn('--seed 20260933', srun)
        self.assertTrue(srun.endswith('--run-tag 03 --stable-draws --robot kjunior'), srun)
        self.assertIn('command grace_ou_6M.slurm -- --stable-draws --robot kjunior\n', out)
        self.assertIn('\ncode ', out)
        p = self.task(3, '--stable-draws')
        p.communicate(timeout=120)
        self.assertNotEqual(p.returncode, 0)

    # the fixed-weight array's own tests do not apply
    testSpinIsComparedAsANumber = None
    testOneProvenanceAmongConcurrentTasks = None


if __name__ == '__main__':
    unittest.main()
