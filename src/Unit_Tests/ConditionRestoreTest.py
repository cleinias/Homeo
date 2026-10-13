'''
Restoring a homeostat from a logged snapshot (HomeostatConditionLogger).

A snapshot restored into a homeostat built from another seed must give the
same snapshot back: every unit and connection field the log records.  The
300k validation (run_validation_300k.restore_from_json) relies on it.
'''
import json
import os
import tempfile
import unittest

from Helpers.HomeostatConditionLogger import (_snapshot, log_homeostat_conditions_json,
                                              restore_homeostat_conditions)
import HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_Ashby as A


class ConditionRestoreTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ['HOMEO_DATA_DIR'] = self.tmp.name

    def tearDown(self):
        os.environ.pop('HOMEO_DATA_DIR', None)
        self.tmp.cleanup()

    def build(self, seed, uniselector_type='ashby'):
        hom, backend, _ = A.setup_phototaxis(topology='fixed', light_intensity=-100,
                                             uniselector_type=uniselector_type, seed=seed)
        self.addCleanup(backend.kheperaSimulation.saveTrajectory)
        return hom

    def testSnapshotRoundTrip(self):
        for kind in ('ashby', 'continuous'):
            with self.subTest(uniselector=kind):
                original = _snapshot(self.build(1, kind))
                other = self.build(2, kind)
                self.assertNotEqual(_snapshot(other), original)
                self.assertEqual(restore_homeostat_conditions(other, original), [])
                self.assertEqual(_snapshot(other), original)

    def testValidationRestoresTheSavedRun(self):
        import run_validation_300k as rv
        saved = self.build(1)
        path = os.path.join(self.tmp.name, 'run.json')
        log_homeostat_conditions_json(saved, path, 'INITIAL CONDITIONS', 'run', seed=1)
        log_homeostat_conditions_json(saved, path, 'FINAL CONDITIONS')
        other = self.build(2)
        self.assertEqual(rv.restore_from_json(other, path), 1)
        with open(path) as f:
            self.assertEqual(_snapshot(other), json.load(f)['FINAL CONDITIONS'])


if __name__ == '__main__':
    unittest.main()
