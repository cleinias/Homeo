'''
@author: stefano

What a run with a battery records: its parameters in the run's JSON
settings and in the .traj and .statelog headers, its level, the wheels'
efficiency and whether the robot is alive in the statelog, and its run in
the result (and so in a batch file).
'''
import csv
import glob
import json
import os
import tempfile
import unittest

from HomeoExperiments.KheperaExperiments import phototaxis_common as common
from HomeoExperiments.KheperaExperiments import phototaxis_braitenberg2_direct as direct
from Simulator.HomeoExperiments import add_battery_to_homeostat


def battery_setup(seed=1, **battery):
    "The fixed-weight vehicle with a battery"
    def setup():
        hom, backend, seed_ = direct.setup_phototaxis(fixed_weights=True, seed=seed)
        add_battery_to_homeostat(hom, backend, **battery)
        return hom, backend, seed_
    return setup


class BatteryRecordTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        saved = os.environ.get('HOMEO_DATA_DIR')
        os.environ['HOMEO_DATA_DIR'] = self.tmp.name
        self.addCleanup(lambda: os.environ.__setitem__('HOMEO_DATA_DIR', saved)
                        if saved is not None else os.environ.pop('HOMEO_DATA_DIR', None))

    def run_one(self, **battery):
        return common.run_headless(battery_setup(**battery), 'battery', total_steps=300,
                                   report_interval=100, quiet=True, state_log=True)

    def testTheRunsRecords(self):
        r = self.run_one(depletion='graded', critical_level=0.25)
        with open(r['json_path']) as f:
            settings = json.load(f)['settings']
        self.assertEqual(settings['depletion'], 'graded')
        self.assertEqual(settings['battery_critical_level'], 0.25)
        self.assertEqual(settings['food_quality'], 'light')
        [traj] = glob.glob(os.path.join(os.path.dirname(r['json_path']), '*.traj'))
        with open(traj) as f:
            [line] = [l for l in f if l.startswith('# Battery\t')]
        fields = line.rstrip('\n').split('\t')[1:]
        self.assertEqual(dict(zip(fields[::2], fields[1::2]))['depletion'], 'graded')
        with open(r['state_log_path']) as f:
            lines = f.read().splitlines()
        self.assertIn('# depletion\tgraded', lines)
        header = [l for l in lines if not l.startswith('#')][0].split('\t')
        self.assertEqual(header[-3:], ['battery_level', 'motor_efficiency', 'alive'])
        last = lines[-1].split('\t')
        self.assertAlmostEqual(float(last[-3]), r['battery_final'], places=6)
        self.assertEqual(last[-1], '1')

    def testTheResultHasTheBatterysRun(self):
        r = self.run_one(discharge_rate=1e-3)
        self.assertEqual(r['battery_ticks'], 300)
        self.assertTrue(r['alive'])
        self.assertIsNone(r['death_tick'])
        self.assertLess(r['battery_min'], 1.0)
        self.assertGreater(r['battery_mean'], r['battery_min'])

    def testDeathEndsTheRun(self):
        r = self.run_one(discharge_rate=0.0625, recharge_factor=0.0, depletion='death')
        self.assertFalse(r['alive'])
        self.assertEqual(r['death_tick'], 16)
        self.assertEqual(r['steps_run'], 16)

    def testABatchFileHasTheBatteryColumns(self):
        results = common.run_batch(lambda seed, env_seed: common.run_headless(
            battery_setup(), 'battery', total_steps=100, quiet=True, env_seed=env_seed),
            2, 'test', 'battery', total_steps=100, seed=5)
        [path] = glob.glob(os.path.join(os.path.dirname(results[0]['log_path']), 'batch_*.csv'))
        with open(path) as f:
            rows = list(csv.DictReader(f))
        self.assertIn('battery_mean', rows[0])
        self.assertIn('death_tick', rows[0])

    def testRunsWithoutABatteryRecordNone(self):
        r = common.run_headless(lambda: direct.setup_phototaxis(fixed_weights=True, seed=1),
                                'no battery', total_steps=100, quiet=True, state_log=True)
        self.assertNotIn('battery_mean', r)
        with open(r['json_path']) as f:
            self.assertNotIn('depletion', json.load(f)['settings'])
        with open(r['state_log_path']) as f:
            self.assertNotIn('battery_level', f.read())


if __name__ == '__main__':
    unittest.main()
