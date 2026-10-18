'''
@author: stefano

HomeostatStateLogger in a headless run, read back by StatelogAnalyzer.  In
headless mode the continuous uniselector changes only the JIT arrays, not the
connection objects, so a logger reading the connections would log the
initial weights throughout: the logged weights must move, and end at the
run's final weights.
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
        from Helpers.General_Helper_Functions import homeo_version
        self.assertEqual(str(data.metadata['homeo']), homeo_version())
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


class HeadlessAshbyStateLogTest(unittest.TestCase):
    """With discrete (Ashby) uniselectors a firing writes its weights to the
    connections, and the JIT arrays catch up only at the next tick: each row
    must show a firing with the weights it drew, as the Python path does --
    the arrays alone would log them one row late, and never on the last
    tick."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        saved = os.environ.get('HOMEO_DATA_DIR')
        os.environ['HOMEO_DATA_DIR'] = self.tmp.name
        self.addCleanup(lambda: os.environ.__setitem__('HOMEO_DATA_DIR', saved) if saved is not None
                        else os.environ.pop('HOMEO_DATA_DIR', None))

    def loggedRun(self, seed, ticks):
        """A headless Ashby phototaxis run with a state logger; returns the
        logged rows, the firing counts and the live connections' signed
        weights, both read after each tick."""
        from HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_Ashby import setup_phototaxis
        from Helpers.HomeostatStateLogger import HomeostatStateLogger
        from Helpers.StripchartGrapher import readStatelog

        hom, backend, _ = setup_phototaxis(seed=seed)
        self.addCleanup(backend.kheperaSimulation.saveTrajectory)
        hom._headless = True
        for unit in hom.homeoUnits:
            unit._headless = True
        path = os.path.join(self.tmp.name, 'run.statelog')
        logger = HomeostatStateLogger(hom, backend.kheperaSimulation, path, seed=seed)
        logger.log_tick(0)
        live = []

        class Spy(object):
            def log_tick(self, tick):
                logger.log_tick(tick)
                live.append([conn.weight * conn.switch for _, _, conn, _ in logger._conn_sources])

            def close(self):
                logger.close()

        hom._state_logger = Spy()
        hom.runFor(ticks)
        logger.close()
        _, cols, data = readStatelog(path)
        weights = data[1:, [cols.index(k) for k in logger._conn_keys]]
        fires = data[:, [i for i, c in enumerate(cols) if c.startswith('unisel_fires_')]].sum(axis=1)
        return weights, fires, live

    def testAFiringRowHoldsTheWeightsItDrew(self):
        weights, fires, live = self.loggedRun(12345, 3000)
        firing = [t for t in range(1, len(fires)) if fires[t] > fires[t - 1]]
        self.assertGreater(len(firing), 5)
        for t in firing:
            for logged, now in zip(weights[t - 1], live[t - 1]):
                self.assertAlmostEqual(logged, now, places=5, msg='tick %d' % t)

    def testAFiringOnTheLastTickIsRecorded(self):
        weights, fires, live = self.loggedRun(3, 1)        # seed 3 fires at tick 1
        self.assertEqual(fires[-1] - fires[0], 1)
        for logged, now in zip(weights[-1], live[-1]):
            self.assertAlmostEqual(logged, now, places=5)


if __name__ == '__main__':
    unittest.main()
