'''
The direct phototaxis experiment's parameter draws (stable_draws).

The motors' (mass, viscosity) come from their full distribution;
--stable-draws keeps only draws with viscosity*dt/mass below
STABILITY_MARGIN, a filter the exact drag step does not need.  Runs and batch
files record which was used.
'''
import csv
import glob
import json
import os
import tempfile
import unittest

import HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct as D


def motorRatios(hom):
    return [D.common.integration_ratio(u) for u in hom.homeoUnits if 'Motor' in u.name]


class StableDrawsTest(unittest.TestCase):

    SEEDS = range(20)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ['HOMEO_DATA_DIR'] = self.tmp.name

    def tearDown(self):
        os.environ.pop('HOMEO_DATA_DIR', None)
        self.tmp.cleanup()

    def ratios(self, **kwargs):
        ratios = []
        for seed in self.SEEDS:
            hom, backend, _ = D.setup_phototaxis(seed=seed, **kwargs)
            backend.kheperaSimulation.saveTrajectory()
            ratios += motorRatios(hom)
        return ratios

    def testFullDistributionByDefault(self):
        "Without the filter some motors have viscosity*dt/mass above STABILITY_MARGIN"
        self.assertTrue(any(r >= D.STABILITY_MARGIN for r in self.ratios()))

    def testStableDrawsKeepTheBound(self):
        self.assertTrue(all(r <= D.STABILITY_MARGIN
                            for r in self.ratios(stable_draws=True)))

    def testRunsRecordTheSetting(self):
        for stable in (False, True):
            # A directory per run: output names have one-second resolution
            os.environ['HOMEO_DATA_DIR'] = os.path.join(self.tmp.name, str(stable))
            with self.subTest(stable_draws=stable):
                results = D.run_batch(n_runs=1, total_steps=20, report_interval=10,
                                      seed=1, stable_draws=stable)
                self.assertEqual(results[0]['stable_draws'], stable)
                with open(results[0]['json_path']) as f:
                    self.assertEqual(json.load(f)['settings']['stable_draws'], stable)
                tag = '_stabledraws' if stable else ''
                csvs = glob.glob(os.path.join(os.path.dirname(results[0]['log_path']),
                                              'batch_direct_*.csv'))
                self.assertEqual(len(csvs), 1, csvs)
                self.assertIn('ashby' + tag + '_light', os.path.basename(csvs[0]))
                with open(csvs[0]) as f:
                    self.assertEqual(next(csv.DictReader(f))['stable_draws'], str(stable))


if __name__ == '__main__':
    unittest.main()
