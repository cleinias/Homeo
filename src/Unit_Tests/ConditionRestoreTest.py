'''
Restoring a homeostat from a logged snapshot (HomeostatConditionLogger).

A snapshot restored into a homeostat built from another seed must give the
same snapshot back: every unit and connection field the log records, also
when the snapshot is read back from a run's JSON.
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

    def testAnUnknownUniselectorModelIsRefused(self):
        "A snapshot whose continuous uniselector has another model is not restored"
        snapshot = _snapshot(self.build(1, 'continuous'))
        for row in snapshot['units']:
            if 'model' in row['uniselector']:
                row['uniselector']['model'] = 'legacy'
        with self.assertRaisesRegex(ValueError, "model 'legacy'"):
            restore_homeostat_conditions(self.build(2, 'continuous'), snapshot)

    def testDynamicStateRoundTrip(self):
        "After a run: velocities, uniselector timers and positions come back too"
        for kind in ('ashby', 'continuous'):
            with self.subTest(uniselector=kind):
                ran = self.build(1, kind)
                ran.slowingFactor = 0
                ran.collectsData = False
                ran.runFor(400)
                original = _snapshot(ran)
                self.assertTrue(any(row.get('currentVelocity') for row in original['units']))
                other = self.build(2, kind)
                restore_homeostat_conditions(other, original)
                self.assertEqual(_snapshot(other), original)

    def testJsonRecordsTheEnvironment(self):
        path = os.path.join(self.tmp.name, 'env.json')
        log_homeostat_conditions_json(self.build(1), path, 'INITIAL CONDITIONS', 'run')
        with open(path) as f:
            env = json.load(f)['environment']
        self.assertEqual(set(env), {'python', 'numpy', 'numba', 'host', 'homeo'})
        try:
            import numba
            self.assertEqual(env['numba'], numba.__version__)
        except ImportError:
            self.assertEqual(env['numba'], 'absent')

    def testARunsJsonRestoresItsFinalConditions(self):
        saved = self.build(1)
        path = os.path.join(self.tmp.name, 'run.json')
        log_homeostat_conditions_json(saved, path, 'INITIAL CONDITIONS', 'run', seed=1)
        log_homeostat_conditions_json(saved, path, 'FINAL CONDITIONS')
        other = self.build(2)
        with open(path) as f:
            data = json.load(f)
        self.assertEqual(data['seed'], 1)
        self.assertEqual(restore_homeostat_conditions(other, data['FINAL CONDITIONS']), [])
        self.assertEqual(_snapshot(other), data['FINAL CONDITIONS'])


if __name__ == '__main__':
    unittest.main()
