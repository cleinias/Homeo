'''
Created on Oct 14, 2026

@author: stefano

The analysis helpers on the files the runs write (review finding HV-05):
RobotTrajectoryWriter -> TrajectoryGrapher.loadTrajectory, its thinning,
StripchartGrapher on a real .statelog, and HomeostatDiagramTikz on a real
.log.  TrajectoryGrapherTest, TrajectoryRecordTest and StripchartGrapherTest
cover the sensor range, the eye ring, the header and the smoothing.
'''
import contextlib
import io
import math
import os
import re
import tempfile
import unittest
from unittest import mock

import matplotlib
matplotlib.use('Agg')

from Helpers import StripchartGrapher as SG
from Helpers import TrajectoryGrapher as TG
from Helpers.HomeostatConditionLogger import log_homeostat_conditions
from Helpers.HomeostatDiagramTikz import generate_tikz_from_log, main as tikzMain
from Helpers.RobotTrajectoryWriter import configureTrajectoryDefaults
import HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct as D


class _DataDirTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        '''A temporary data directory for the class.  Its restoration is a
        class cleanup, which runs also when a subclass's setUpClass fails
        after this one (tearDownClass then does not run).'''
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        saved = os.environ.get('HOMEO_DATA_DIR')
        os.environ['HOMEO_DATA_DIR'] = cls.tmp.name
        cls.addClassCleanup(lambda: os.environ.pop('HOMEO_DATA_DIR', None) if saved is None
                            else os.environ.__setitem__('HOMEO_DATA_DIR', saved))
        cls.addClassCleanup(configureTrajectoryDefaults, 1, True)


def trajPath(r):
    return r['backend'].kheperaSimulation.trajectoryWriter.posFile.name


class TrajectoryRoundTripTest(_DataDirTest):
    '''What the writer writes, the reader reads back: decimated files end on
    the vehicle's final pose, and thinning keeps the first and last rows
    whatever the chunks.'''

    def run_vehicle(self, interval, total_steps=500):
        configureTrajectoryDefaults(interval=interval)
        r = D.run_headless(fixed_weights=True, heading=15, eye_response='log', quiet=True,
                           seed=1, total_steps=total_steps, report_interval=total_steps)
        return r, trajPath(r)

    def testDecimatedFilesEndOnTheFinalPose(self):
        for interval in (1, 3, 7):
            with self.subTest(interval=interval):
                r, path = self.run_vehicle(interval)
                header, xy, nRows = TG.loadTrajectory(path)
                perTick = int(re.search(r'(\d+) steps per homeostat tick', ''.join(header)).group(1))
                self.assertEqual(nRows, math.ceil(500 * perTick / interval))
                self.assertAlmostEqual(xy[-1][0], r['final_x'], delta=1e-6)
                self.assertAlmostEqual(xy[-1][1], r['final_y'], delta=1e-6)
                # a decimated file's last row is the final pose, whatever its step
                self.assertLessEqual(abs(TG.ticksFromRows(header, nRows) - 500), interval / perTick)
                # exactly, from the step count the closed file ends with
                steps = TG.readStepsRecorded(path)
                self.assertEqual(steps, 500 * perTick)
                self.assertEqual(TG.ticksFromRows(header, nRows, steps), 500)
                self.assertEqual(TG.readLightsFromHeader(header)['TARGET'][:3], [7.0, 7.0, 100.0])
                x, y, heading = map(float, TG.readInitPosFromHeader(header))
                self.assertAlmostEqual(x, r['start_x'], places=5)
                self.assertAlmostEqual(y, r['start_y'], places=5)
                self.assertAlmostEqual(heading, 15.0, places=1)
                self.assertAlmostEqual(xy[0][0], r['start_x'], delta=0.01)

    def testFilesWithoutAStepCount(self):
        "Older files, and those of runs killed before closing, have no step count"
        _, path = self.run_vehicle(3)
        with open(path) as f:
            lines = f.readlines()
        self.assertTrue(lines[-1].startswith('# Steps recorded\t'))
        with open(path, 'w') as f:
            f.writelines(lines[:-1])
        self.assertIsNone(TG.readStepsRecorded(path))
        header, xy, nRows = TG.loadTrajectory(path)
        self.assertEqual(TG.ticksFromRows(header, nRows, None), 501)   # 334 rows x 3 / 2

    def testThinningKeepsTheEndsWhateverTheChunks(self):
        _, path = self.run_vehicle(1)
        _, full, nRows = TG.loadTrajectory(path, maxPoints=10 ** 6)
        self.assertEqual(len(full), nRows)
        _, thin, n = TG.loadTrajectory(path, maxPoints=7)
        self.assertEqual(n, nRows)
        self.assertLessEqual(len(thin), 9)
        self.assertEqual(list(thin[0]), list(full[0]))
        self.assertEqual(list(thin[-1]), list(full[-1]))
        readCsv = TG.pd.read_csv

        def smallChunks(*args, **kwargs):
            kwargs['chunksize'] = 37
            return readCsv(*args, **kwargs)
        with mock.patch.object(TG.pd, 'read_csv', smallChunks):
            _, chunked, n = TG.loadTrajectory(path, maxPoints=7)
        self.assertEqual(n, nRows)
        self.assertEqual(chunked.tolist(), thin.tolist())
        # the rows kept are evenly spaced in the file
        index = [full.tolist().index(row) for row in thin.tolist()[:-1]]
        self.assertEqual(len(set(b - a for a, b in zip(index, index[1:]))), 1)


class StripchartOnAStatelogTest(_DataDirTest):
    '''StripchartGrapher on a direct adaptive run's .statelog (300 ticks,
    every 10).'''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        r = D.run_headless(total_steps=300, report_interval=300, quiet=True, seed=1,
                           state_log=True, state_log_interval=10, uniselector_type='continuous')
        cls.path = r['state_log_path']
        cls.hom = r['hom']

    def testReadingTheLog(self):
        meta, columns, data = SG.readStatelog(self.path)
        self.assertEqual(meta['log_interval'], '10')
        self.assertEqual(list(data[:, columns.index('tick')]), list(range(0, 301, 10)))
        self.assertEqual(SG.unitsIn(columns), [u.name for u in self.hom.homeoUnits])
        for value in ('critDev', 'output', 'stress', 'sigma', 'fires'):
            self.assertIn(value, SG.valueNames(columns))
        motor = self.hom.homeoUnits[0]
        self.assertAlmostEqual(data[-1, columns.index(motor.name + '_critDev')],
                               motor.criticalDeviation, places=4)

    def testResolvingTheSeries(self):
        _, columns, _ = SG.readStatelog(self.path)
        self.assertEqual(SG.resolveSeries(columns, [], [], True, []),
                         [('w_Left Motor<-Right Sensor', 'Left Motor<-Right Sensor'),
                          ('w_Right Motor<-Left Sensor', 'Right Motor<-Left Sensor')])
        self.assertEqual(SG.resolveSeries(columns, ['Left Motor'], ['critDev', 'sigma'], False, []),
                         [('Left Motor_critDev', 'Left Motor critDev'),
                          ('sigma_Left Motor', 'Left Motor sigma')])
        self.assertEqual(SG.resolveSeries(columns, [], ['distance'], False, ['robot_x']),
                         [('robot_x', 'robot_x'), ('distance', 'distance')])
        self.assertEqual(len(SG.resolveSeries(columns, [], ['critDev'], False, [])), 4)
        for bad in ((['nonsense'], []), ([], ['nonsense'])):
            with self.assertRaises(SystemExit):
                SG.resolveSeries(columns, [], bad[0], False, bad[1])

    def testBounds(self):
        meta, _, _ = SG.readStatelog(self.path)
        self.assertEqual(SG.seriesBounds('Left Motor_critDev', meta), (-10.0, 10.0))
        self.assertEqual(SG.seriesBounds('w_Left Motor<-Right Sensor', meta), (-1.0, 1.0))
        self.assertEqual(SG.seriesBounds('Left Motor_stress', meta), (0.0, 1.0))
        self.assertEqual(SG.seriesBounds('sigma_Left Motor', meta), (0.0, 1.0))
        self.assertIsNone(SG.seriesBounds('distance', meta))

    def testTheCommandLine(self):
        '''main() draws to -o, converts --smooth-ticks to samples with the
        log's interval, and --list lists the columns.'''
        out = os.path.join(self.tmp.name, 'strips.png')
        windows = []
        drawStrip = SG._drawStrip

        def spy(ax, tick, series, window, *args, **kwargs):
            windows.append(window)
            return drawStrip(ax, tick, series, window, *args, **kwargs)
        with mock.patch.object(SG, '_drawStrip', spy), contextlib.redirect_stdout(io.StringIO()):
            SG.main(['strip', self.path, '--cross', '--smooth-ticks', '50', '-o', out])
        self.assertGreater(os.path.getsize(out), 0)
        self.assertEqual(windows, [5, 5])
        listing = io.StringIO()
        with contextlib.redirect_stdout(listing):
            SG.main(['strip', self.path])
        self.assertIn('log_interval: 10 ticks', listing.getvalue())
        self.assertIn('   w_Left Motor<-Right Sensor\n', listing.getvalue())


class TikzFromALogTest(_DataDirTest):
    '''HomeostatDiagramTikz on a log written by HomeostatConditionLogger: one
    node per unit with its deviation and output, one edge per active
    connection with its signed weight, styled by its state.'''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        hom, backend, _ = D.setup_phototaxis(seed=1)
        cls.log = os.path.join(cls.tmp.name, 'run.log')
        log_homeostat_conditions(hom, cls.log, 'INITIAL CONDITIONS', 'tikz_test')
        cls.initial = cls.snapshot(hom)
        hom.slowingFactor = 0
        hom.runFor(200)
        log_homeostat_conditions(hom, cls.log, 'FINAL CONDITIONS')
        cls.final = cls.snapshot(hom)
        backend.kheperaSimulation.saveTrajectory()

    @staticmethod
    def snapshot(hom):
        units = {u.name: (u.criticalDeviation, u.currentOutput) for u in hom.homeoUnits}
        conns = {(c.incomingUnit.name, u.name): (c.switch * round(c.weight, 6), c.state, c.status)
                 for u in hom.homeoUnits for c in u.inputConnections}
        return units, conns

    def check(self, tex, snapshot, showInactive=False):
        units, conns = snapshot
        nodes = re.findall(r'\\node\[(\w+)\] \((\w+)\) at .*?\{\\textbf\{([^}]*)\}\\\\critDev: '
                           r'(\S+)\\\\out: (\S+)\};', tex)
        self.assertEqual(sorted(n[2] for n in nodes), sorted(units))
        for style, _, name, critDev, out in nodes:
            self.assertAlmostEqual(float(critDev), units[name][0], delta=0.0015)
            self.assertAlmostEqual(float(out), units[name][1], delta=0.0015)
            self.assertIn(style, ('active', 'saturated', 'inactive'))
        ids = {n[1]: n[2] for n in nodes}
        edges = re.findall(r'\\draw\[(manual conn|unisel conn|inactive conn)\] \((\w+)\) '
                           r'to\[[^]]*\] node\[[^]]*\] \{([+-][\d.]+)\} \((\w+)\);', tex)
        drawn = {}
        for style, src, weight, dst in edges:
            drawn[(ids[src], ids[dst])] = (style, float(weight))
        expected = {k: v for k, v in conns.items() if v[2] or showInactive}
        self.assertEqual(set(drawn), set(expected))
        for key, (weight, state, active) in expected.items():
            style = 'inactive conn' if not active else (
                'manual conn' if state == 'manual' else 'unisel conn')
            self.assertEqual(drawn[key][0], style, key)
            self.assertAlmostEqual(drawn[key][1], weight, delta=0.0006)

    def testBothSections(self):
        self.check(generate_tikz_from_log(self.log, section='INITIAL'), self.initial)
        self.check(generate_tikz_from_log(self.log, section='FINAL'), self.final)
        self.check(generate_tikz_from_log(self.log, section='FINAL', show_inactive=True),
                   self.final, showInactive=True)
        self.assertNotEqual(self.initial, self.final)

    def testTheCommandLine(self):
        out = os.path.join(self.tmp.name, 'final.tex')
        tikzMain([self.log, '--section', 'FINAL', '-o', out])
        with open(out) as f:
            self.check(f.read(), self.final)
        with self.assertRaises(ValueError):
            generate_tikz_from_log(self.log, section='MIDDLE')


if __name__ == '__main__':
    unittest.main()
