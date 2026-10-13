'''
Two runs started in the same second must not share output files (review
finding HV-09): names carry a whole-second timestamp, and the second run's
files used to overwrite, or append to, the first's.
'''
import json
import os
import tempfile
import unittest

from Helpers.General_Helper_Functions import unique_stem
import HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct as D


class OutputNamesTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ['HOMEO_DATA_DIR'] = self.tmp.name

    def tearDown(self):
        os.environ.pop('HOMEO_DATA_DIR', None)
        self.tmp.cleanup()

    def testUniqueStem(self):
        d = self.tmp.name
        self.assertEqual(unique_stem(d, 'run', ('.log', '.json')), 'run')
        open(os.path.join(d, 'run.json'), 'w').close()
        self.assertEqual(unique_stem(d, 'run', ('.log', '.json')), 'run-2')
        self.assertEqual(unique_stem(d, 'run', ('.traj',)), 'run')
        open(os.path.join(d, 'run-2.log'), 'w').close()
        self.assertEqual(unique_stem(d, 'run', ('.log', '.json')), 'run-3')

    def testRunsInTheSameSecondKeepTheirFiles(self):
        runs = []
        for seed in (1, 2):
            r = D.run_headless(total_steps=500, report_interval=500, quiet=True, seed=seed)
            sim = r['backend'].kheperaSimulation
            sim.saveTrajectory()
            runs.append((r, sim.trajectoryWriter.posFile.name))
        (r1, traj1), (r2, traj2) = runs
        self.assertNotEqual(traj1, traj2)
        self.assertNotEqual(r1['json_path'], r2['json_path'])
        for r in (r1, r2):
            with open(r['json_path']) as f:
                self.assertEqual(json.load(f)['seed'], r['seed'])
        for traj in (traj1, traj2):
            with open(traj) as f:
                rows = [l for l in f if l.strip() and not l.startswith('#')
                        and l.count('\t') >= 5]
            self.assertEqual(len(rows), 1000)


if __name__ == '__main__':
    unittest.main()
