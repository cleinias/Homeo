# Copyright (C) 2026 Stefano Franchi
#
# This file is part of Homeo, a simulation of Ashby's homeostat and of
# homeostat-controlled robots.
#
# Homeo is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# Homeo is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with Homeo.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

'''
The recorded field: KheperaSimulation.fieldSnapshot samples the field the
chemical eyes read on a grid; RobotTrajectoryWriter writes it into the .traj
at the start (header) and the end (before "# Steps recorded");
TrajectoryGrapher reads it back, shades it, and warns about files without
one (fieldPanels).  The Webots twin is in WebotsBackendTest.
'''
import contextlib
import io
import os
import tempfile
import unittest
from math import hypot
from unittest import mock

import matplotlib
matplotlib.use('Agg')
import numpy as np

from Helpers import TrajectoryGrapher as TG
from KheperaSimulator.KheperaSimulator import (
    KheperaSimulation, KheperaRobotView, CHEMOTAXIS_FIELD, FIELD_GRID_POINTS, FIELD_GRID_REACH,
    FIELD_GRID_FRACTION, fieldContourRadius, fieldReach, _fieldShape)
from Unit_Tests.TrajectoryGrapherTest import writeTraj

CHEMOTAXIS = 'kheperaChemotaxis_HOMEO_World'


class _TmpTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def path(self, name):
        return os.path.join(self.tmp.name, name)

    def world(self, name=CHEMOTAXIS, fieldLaws=None):
        sim = KheperaSimulation()
        if fieldLaws:
            sim.fieldLaws = fieldLaws
        sim.setupWorld(name, self.tmp.name)
        self.addCleanup(lambda: sim.trajectoryWriter.posFile is None
                        or sim.trajectoryWriter.posFile.closed or sim.saveTrajectory())
        return sim


class FieldSnapshotTest(_TmpTest):

    def testTheSnapshotIsTheLawOnAGrid(self):
        '''Every grid point holds the food's intensity times its law's
        fall-off there; the grid is centred on the food and reaches to where
        the law falls to FIELD_GRID_FRACTION.'''
        sim = self.world()
        [(quality, (x0, y0, spacing, n, values))] = sim.fieldSnapshot().items()
        self.assertEqual((quality, n), ('organic', FIELD_GRID_POINTS))
        reach = fieldContourRadius(CHEMOTAXIS_FIELD, FIELD_GRID_FRACTION, outer=FIELD_GRID_REACH)
        self.assertAlmostEqual(spacing * (n - 1) / 2, reach)
        self.assertAlmostEqual(x0 + spacing * (n - 1) / 2, 7)
        self.assertAlmostEqual(y0 + spacing * (n - 1) / 2, 7)
        expected = [[100 * _fieldShape(CHEMOTAXIS_FIELD, hypot(x0 + i * spacing - 7,
                                                                y0 + j * spacing - 7))
                     for i in range(n)] for j in range(n)]
        np.testing.assert_allclose(values, expected, rtol=1e-12)
        self.assertEqual(values[50][50], 100)                       # inside the patch

    def testSeveralSourcesAndQualities(self):
        '''In the Vehicle 3c world with two field laws: one grid per quality,
        centred on its sources, the sum of their values; the light has none.'''
        gauss = {'law': 'gaussian', 'sigma': 1.0}
        sim = self.world('kheperaBraitenberg3c_HOMEO_World',
                         {'temperature': gauss, 'organic': CHEMOTAXIS_FIELD})
        snapshot = sim.fieldSnapshot()
        self.assertEqual(sorted(snapshot), ['organic', 'temperature'])
        x0, y0, spacing, n, values = snapshot['temperature']    # TEMP1 (7, 7), TEMP2 (1, 7)
        self.assertAlmostEqual(x0 + spacing * (n - 1) / 2, 4)
        self.assertAlmostEqual(y0 + spacing * (n - 1) / 2, 7)
        self.assertAlmostEqual(spacing * (n - 1) / 2, 3 + fieldReach(gauss))
        for i, j in ((0, 0), (50, 50), (17, 63), (100, 100)):
            x, y = x0 + i * spacing, y0 + j * spacing
            self.assertAlmostEqual(values[j][i], 80 * (_fieldShape(gauss, hypot(x - 7, y - 7))
                                                       + _fieldShape(gauss, hypot(x - 1, y - 7))))

    def testTheReach(self):
        self.assertAlmostEqual(fieldReach({'law': 'cone', 'radius': 3.0}), 3 * (1 - FIELD_GRID_FRACTION))
        self.assertEqual(fieldReach({'law': 'gaussian', 'sigma': 50.0}), FIELD_GRID_REACH)
        self.assertEqual(fieldReach({'law': 'inverse_square'}), FIELD_GRID_REACH)

    def testNoFieldNoSnapshot(self):
        self.assertEqual(self.world('kheperaBraitenberg2_HOMEO_World').fieldSnapshot(), {})
        self.assertEqual(KheperaSimulation().fieldSnapshot(), {})       # no world yet


class FieldRecordTest(_TmpTest):

    def written(self, steps=40):
        sim = self.world()
        for _ in range(steps):
            sim.advanceSim()
        snapshot = sim.fieldSnapshot()
        path = sim.trajectoryWriter.posFile.name
        sim.saveTrajectory()
        with open(path) as f:
            return sim, snapshot, path, f.read().splitlines()

    def testTheFileHasTheFieldAtTheStartAndAtTheEnd(self):
        _, _, path, lines = self.written()
        heads = [i for i, l in enumerate(lines) if l.startswith('# Field snapshot')]
        self.assertEqual([lines[i].split('\t')[1:3] for i in heads],
                         [['organic', 'start'], ['organic', 'end']])
        start, end = heads
        self.assertLess(start, lines.index("# Vehicle's initial position at:"))
        self.assertEqual(lines[end + FIELD_GRID_POINTS + 1], '# Steps recorded\t40')
        self.assertEqual(len(lines), end + FIELD_GRID_POINTS + 2)
        self.assertTrue(all(l.startswith('#\t') for l in lines[end + 1:end + 1 + FIELD_GRID_POINTS]))

    def testTheReadersReadTheFileAsBefore(self):
        _, _, path, lines = self.written()
        rows = [l for l in lines if l and not l.startswith('#') and l[0] in '-0123456789'
                and len(l.split('\t')) == 6]
        self.assertEqual(TG.readStepsRecorded(path), 40)
        header, xy, nRows = TG.loadTrajectory(path)
        self.assertEqual(nRows, 40)
        self.assertEqual(list(xy[-1]), [float(v) for v in rows[-1].split('\t')[:2]])
        self.assertEqual(TG.readLightsFromHeader(header), {'FOOD': [7.0, 7.0, 100.0]})
        self.assertEqual(TG.readInitPosFromHeader(header)[:2], ['4.000000', '4.000000'])

    def testTheGrapherReadsBackTheGridWritten(self):
        _, snapshot, path, _ = self.written(steps=3000)        # the end read back from far
        x0, y0, spacing, n, values = snapshot['organic']
        read = TG.readFieldSnapshots(path)
        self.assertEqual(sorted(read), ['end', 'start'])
        for moment in ('start', 'end'):
            grid = read[moment]['organic']
            self.assertEqual((grid['x0'], grid['y0'], grid['spacing'], grid['n']),
                             (x0, y0, spacing, n))
            np.testing.assert_allclose(grid['values'], values, rtol=5e-6)

    def testANewFileRecordsTheFieldToo(self):
        sim = self.world()
        sim.advanceSim()
        first = sim.trajectoryWriter.posFile.name
        sim.newTrajectoryFile()
        sim.advanceSim()
        second = sim.trajectoryWriter.posFile.name
        sim.saveTrajectory()
        for path in (first, second):
            self.assertEqual(sorted(TG.readFieldSnapshots(path)), ['end', 'start'], path)


def snapshotLines(moment, values, x0=6.0, y0=6.0, spacing=1.0, quality='organic'):
    n = len(values)
    return (['# Field snapshot\t%s\t%s\tx0\t%r\ty0\t%r\tspacing\t%r\tn\t%d\n'
             % (quality, moment, x0, y0, spacing, n)]
            + ['#\t' + '\t'.join('%.6g' % v for v in row) + '\n' for row in values])


FIELD_LAW = ['# Field\tTARGET\tlaw\tk0\tlength\t2.0\tradius\t0.06\n']
START = [[1, 10, 1], [10, 100, 10], [1, 10, 1]]
END = [[2, 20, 2], [20, 100, 20], [2, 20, 2]]


class _FileTest(_TmpTest):

    def traj(self, name, start=None, end=None, laws=True):
        "A .traj file, with field laws (laws) and the snapshots given"
        path = self.path(name)
        writeTraj(path, eyeLines=(FIELD_LAW if laws else [])
                  + (snapshotLines('start', start) if start else []))
        with open(path, 'a') as f:
            f.writelines((snapshotLines('end', end) if end else []) + ['# Steps recorded\t3\n'])
        return path


class FieldPanelsTest(_FileTest):
    '''The guard: what each kind of file is shaded with, and its warning.'''

    def panels(self, paths, fieldTime='end'):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            panels = TG.fieldPanels(paths, [TG.readDataFileHeader(p) for p in paths], fieldTime)
        return panels, err.getvalue()

    def testARecordedField(self):
        path = self.traj('a.traj', START, END)
        for fieldTime, moments, values in (('end', ['end'], [END]), ('start', ['start'], [START]),
                                           ('both', ['start', 'end'], [START, END])):
            panels, err = self.panels([path], fieldTime)
            self.assertEqual(err, '')
            self.assertEqual([m for m, _ in panels], moments)
            for (_, (kind, (quality, grid))), expected in zip(panels, values):
                self.assertEqual((kind, quality), ('field', 'organic'))
                np.testing.assert_array_equal(grid['values'], expected)

    def testAFileClosedBeforeItsEnd(self):
        panels, err = self.panels([self.traj('a.traj', START)])
        self.assertEqual([m for m, _ in panels], ['start'])
        self.assertIn('no field at the end', err)

    def testAPhototaxisFileGetsTheLightSchematic(self):
        path = self.traj('a.traj', laws=False)
        for fieldTime in TG.FIELD_TIMES:
            panels, err = self.panels([path], fieldTime)
            self.assertEqual(panels, [(None, ('light', None))])
            self.assertIn('a.traj: no recorded field: the shading is a schematic', err)

    def testFieldLawsButNoFieldGetNoShading(self):
        for fieldTime in TG.FIELD_TIMES:
            panels, err = self.panels([self.traj('a.traj')], fieldTime)
            self.assertEqual(panels, [(None, ('none', None))])
            self.assertIn('a.traj: field laws but no recorded field: not shaded', err)

    def testSeveralFiles(self):
        none, a, b, c = (self.traj('none.traj'), self.traj('a.traj', START, END),
                         self.traj('b.traj', START, END), self.traj('c.traj', START, START))
        panels, err = self.panels([none, a, b])
        self.assertIn("none.traj: field laws but no recorded field: the chart shows another file's",
                      err)
        self.assertNotIn('differs', err)
        np.testing.assert_array_equal(panels[0][1][1][1]['values'], END)
        _, err = self.panels([a, c])
        self.assertIn("c.traj: its field at the end differs from", err)


class FieldChartTest(_FileTest):

    def chart(self, paths, *options, interactive=False):
        "The figure main() draws, and the toggles' run artists if interactive"
        figures, toggles = [], []
        real = TG._enableLegendToggles

        def keep(fig, legend, runArtists):
            toggles.append(runArtists)
            real(fig, legend, runArtists)
        out = [] if interactive else ['-o', self.path('out.png')]
        with mock.patch.object(TG, '_showOrSave', side_effect=lambda fig, _: figures.append(fig)), \
                mock.patch.object(TG, '_enableLegendToggles', side_effect=keep), \
                contextlib.redirect_stderr(io.StringIO()):
            TG.main(['homeo-traj'] + list(paths) + list(options) + out)
        return figures[0], toggles

    def testTheFieldIsShaded(self):
        path = self.traj('a.traj', start=START, end=END)
        with mock.patch.object(TG, '_drawIrradianceBackground') as light:
            fig, _ = self.chart([path])
        light.assert_not_called()
        [ax] = fig.axes
        [image] = ax.get_images()
        shade = image.get_array()
        self.assertAlmostEqual(shade.max(), 1.0)            # the peak, white
        self.assertAlmostEqual(shade[0][0], 0.45 + 0.55 * np.log10(2 / 0.1) / 3)
        self.assertEqual(image.get_extent(), [5.5, 8.5, 5.5, 8.5])
        [contours] = [c for c in ax.collections if hasattr(c, 'levels')]
        np.testing.assert_allclose(sorted(contours.levels), [1, 10, 50])

    def testBothGivesTwoPanelsToggledTogether(self):
        a = self.traj('a.traj', start=START, end=END)
        b = self.traj('b.traj', start=START, end=END)
        fig, [runArtists] = self.chart([a, b], '--field-time', 'both', interactive=True)
        self.assertEqual(len(fig.axes), 2)
        for ax, moment in zip(fig.axes, ('start', 'end')):
            self.assertTrue(ax.get_title().endswith('field at the ' + moment))
        for artists in runArtists:
            self.assertEqual({artist.axes for artist in artists}, set(fig.axes))
        from matplotlib.backend_bases import KeyEvent
        fig.canvas.callbacks.process('key_press_event', KeyEvent('key_press_event', fig.canvas, 'n'))
        self.assertFalse(any(a.get_visible() for artists in runArtists for a in artists))
        fig.canvas.callbacks.process('key_press_event', KeyEvent('key_press_event', fig.canvas, 'a'))
        self.assertTrue(all(a.get_visible() for artists in runArtists for a in artists))

    def testOneFileBothPanels(self):
        fig, _ = self.chart([self.traj('a.traj', start=START, end=END)], '--field-time', 'both')
        self.assertEqual([ax.get_title() for ax in fig.axes],
                         ['field at the start', 'field at the end'])

    def testAPhototaxisFileIsChartedAsBefore(self):
        path = self.path('p.traj')
        writeTraj(path)
        with mock.patch.object(TG, '_drawFieldShading') as field:
            fig, _ = self.chart([path], '--field-time', 'both')
        field.assert_not_called()
        [ax] = fig.axes
        [image] = ax.get_images()
        self.assertEqual(ax.get_title(), 'p.traj')

    def testTheContoursAreTheVisualizers(self):
        self.assertEqual(TG.FIELD_CONTOURS, KheperaRobotView.FIELD_CONTOURS)


if __name__ == '__main__':
    unittest.main()
