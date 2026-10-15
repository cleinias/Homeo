'''
Created on Oct 14, 2026

@author: stefano

HomeostatStateLogger in a headless run, read back by StatelogAnalyzer
(review finding HN-08).  In headless mode the OU uniselector changes only
the JIT arrays, and the logger once read the connection objects instead, so
the whole state log sat at the initial weights (fixed in a8e2cda, with no
test): the logged weights must move, and end at the run's final weights.
'''
import glob
import os
import tempfile
import unittest

from Helpers import StatelogAnalyzer as SLA
from HomeoExperiments.KheperaExperiments import phototaxis_braitenberg2_direct as D


class HeadlessStateLogTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        os.environ['HOMEO_DATA_DIR'] = cls.tmp.name
        try:
            cls.result = D.run_headless(total_steps=400, quiet=True, seed=3,
                                        uniselector_type='continuous',
                                        state_log=True, state_log_interval=1)
        finally:
            os.environ.pop('HOMEO_DATA_DIR', None)
        cls.data = SLA.parse_statelog(cls.result['state_log_path'])
        SLA.enrich(cls.data)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def testTheFileParses(self):
        data = self.data
        self.assertEqual(data.metadata['log_interval'], 1)
        self.assertEqual(sorted(data.unit_names),
                         sorted(u.name for u in self.result['hom'].homeoUnits))
        self.assertIn('Left Motor', data.unit_names)          # names with spaces
        self.assertEqual(list(data.df['tick']), list(range(401)))
        self.assertEqual(sorted(data.self_conns), ['w_Left Motor<-Left Motor',
                                                  'w_Right Motor<-Right Motor'])
        self.assertIn('w_Right Motor<-Left Sensor', data.cross_conns)
        self.assertEqual(sorted(data.sigma_cols), ['sigma_Left Motor', 'sigma_Right Motor'])
        self.assertIn('drift_w_Right Motor<-Left Sensor', data.df.columns)

    def testLoggedWeightsMoveAndEndAtTheFinalWeights(self):
        hom, df = self.result['hom'], self.data.df
        moved = 0
        for unit in hom.homeoUnits:
            unit.flushJitArrays()
            for conn in unit.inputConnections:
                col = 'w_%s<-%s' % (unit.name, conn.incomingUnit.name)
                if col not in df.columns:
                    continue
                self.assertAlmostEqual(df[col].iloc[-1], conn.weight * conn.switch, places=6, msg=col)
                moved += df[col].iloc[-1] != df[col].iloc[0]
        self.assertGreaterEqual(moved, 2)               # the two sensor -> motor links


if __name__ == '__main__':
    unittest.main()
