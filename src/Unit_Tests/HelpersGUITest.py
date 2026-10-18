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
Tests for the GUI helper modules TrajectoriesViewer and TrajectoryGrapher.

Verifies that both modules import correctly under the current venv
and that their core classes/functions work.
'''

import unittest
import sys
import os
import tempfile

import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

app = QApplication.instance() or QApplication(sys.argv)


class TrajectoryGrapherImportTest(unittest.TestCase):
    """Test that TrajectoryGrapher imports and its helper functions work."""

    def test_import(self):
        """TrajectoryGrapher module imports without error."""
        from Helpers.TrajectoryGrapher import (
            graphTrajectory, readDataFileHeader,
            readLightsFromHeader, readInitPosFromHeader)

    def test_read_header(self):
        """readDataFileHeader parses a .traj header correctly."""
        from Helpers.TrajectoryGrapher import readDataFileHeader

        content = (
            "# Position data for Homeo simulation run\n"
            "#\n"
            "TARGET\t7.0\t7.0\t100.0\tTrue\n"
            "# Vehicle's initial position at:\n"
            "4.0\t 4.0\n"
            "\n"
            "# robot_x\trobot_y\theading\tlight_x\tlight_y\tdistance\n"
            "4.0\t4.0\t0.0\t7.0\t7.0\t4.24\n"
        )
        with tempfile.NamedTemporaryFile(mode='w', suffix='.traj', delete=False) as f:
            f.write(content)
            tmppath = f.name
        try:
            header = readDataFileHeader(tmppath)
            self.assertTrue(len(header) > 0)
            # header ends at the column-names line
            self.assertTrue(any('robot_x' in line for line in header))
            # data line should NOT be in header
            self.assertFalse(any(line.strip() == '4.0\t4.0\t0.0\t7.0\t7.0\t4.24' for line in header))
        finally:
            os.unlink(tmppath)

    def test_read_lights_from_header(self):
        """readLightsFromHeader extracts light positions from header lines."""
        from Helpers.TrajectoryGrapher import readLightsFromHeader

        header = [
            "# Position data\n",
            "TARGET\t7.0\t7.0\t100.0\tTrue\n",
            "# Vehicle's initial position at:\n",
            "4.0\t 4.0\n",
            "# robot_x\trobot_y\n",
        ]
        lights = readLightsFromHeader(header)
        self.assertIn('TARGET', lights)
        self.assertAlmostEqual(lights['TARGET'][0], 7.0)
        self.assertAlmostEqual(lights['TARGET'][1], 7.0)
        self.assertAlmostEqual(lights['TARGET'][2], 100.0)

    def test_read_init_pos_from_header(self):
        """readInitPosFromHeader extracts the initial position."""
        from Helpers.TrajectoryGrapher import readInitPosFromHeader

        header = [
            "# some line\n",
            "# Vehicle's initial position at:\n",
            "4.0\t 4.0\n",
            "# robot_x\trobot_y\n",
        ]
        pos = readInitPosFromHeader(header)
        self.assertEqual(len(pos), 2)
        self.assertAlmostEqual(float(pos[0]), 4.0)
        self.assertAlmostEqual(float(pos[1]), 4.0)


class TrajectoriesViewerImportTest(unittest.TestCase):
    """Test that TrajectoriesViewer imports and the widget can be created."""

    def test_import(self):
        """TrajectoriesViewer module imports without error."""
        from Helpers.TrajectoriesViewer import TrajectoryViewer

    def test_widget_instantiation(self):
        """TrajectoryViewer widget can be instantiated.  On an empty data
        directory of its own: on the real one the result would depend on the
        developer's data, and an unreadable logbook there would open a
        modal message box."""
        from unittest import mock
        from Helpers.TrajectoriesViewer import TrajectoryViewer

        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.dict(os.environ, {'HOMEO_DATA_DIR': tmp}):
            viewer = TrajectoryViewer(appRef=app)
            self.assertIsNotNone(viewer)
            self.assertEqual(os.path.realpath(viewer._dirPath), os.path.realpath(tmp))
            viewer.close()



class HallOfFameTableTest(unittest.TestCase):
    """The GA results table sorts fitness as numbers and keeps its row
    selection: 2.5 sorts before 10.2, and the widget, with its selection
    slots, is kept."""

    def testTheTableSortsNumbersAndSelectsRows(self):
        import contextlib, io
        from Helpers.TrajectoriesViewer import TrajectoryViewer
        fitnesses = [31.0, 2.5, 10.2, 0.75, 9.1]
        rng = np.random.default_rng(1)
        logbook = [{'genome': list(rng.random(60)), 'fitness': (f,),
                    'indivId': '001-%03d' % i} for i, f in enumerate(fitnesses)]
        viewer = TrajectoryViewer(appRef=app)
        self.addCleanup(viewer.close)
        table = viewer.hofWidget
        viewer._currentLogbook = logbook
        with contextlib.redirect_stdout(io.StringIO()):
            viewer.visualizeIndsData(all=True)
        self.addCleanup(table.close)
        self.assertIs(viewer.hofWidget, table)
        self.assertEqual([table.item(r, 0).data(Qt.DisplayRole) for r in range(5)],
                         sorted(fitnesses))
        self.assertEqual(table.windowTitle(), 'All individuals (5)')
        table.cellPressed.emit(2, 3)
        self.assertEqual([i.row() for i in table.selectionModel().selectedRows()], [2])


class LogbookRefreshTest(unittest.TestCase):
    """The viewer's 1-second refresh reads the logbook again only when the file
    changes, and reports an unreadable one once instead of aborting."""

    def testReloadOnlyOnChangeAndSurviveABadFile(self):
        import pickle
        from unittest import mock
        from Helpers import TrajectoriesViewer as TV
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.dict(os.environ, {'HOMEO_DATA_DIR': tmp}), \
                mock.patch.object(TV.QMessageBox, 'exec_') as shown:
            path = os.path.join(tmp, 'run.lgb')
            open(path, 'wb').close()                 # a GA has just created it
            viewer = TV.TrajectoryViewer(appRef=app)
            viewer.refreshTimer.stop()
            self.addCleanup(viewer.close)
            for i in range(3):
                viewer.refreshLogbook()
                viewer.visualizeGenInfo()
            self.assertEqual(shown.call_count, 1)
            self.assertIsNone(viewer._currentLogbook)

            logbook = [{'date': 'today', 'gens': 2}]
            with open(path, 'wb') as f:
                pickle.dump(logbook, f)
            with mock.patch.object(TV, '_load_pickle', wraps=TV._load_pickle) as load:
                for i in range(3):
                    viewer.refreshLogbook()
                self.assertEqual(load.call_count, 1)
                self.assertEqual(viewer._currentLogbook, logbook)
                logbook.append({'gen': 3})
                with open(path, 'wb') as f:
                    pickle.dump(logbook, f)
                viewer.refreshLogbook()
                self.assertEqual(load.call_count, 2)
                self.assertEqual(viewer._currentLogbook, logbook)
            self.assertEqual(shown.call_count, 1)


if __name__ == '__main__':
    unittest.main()
