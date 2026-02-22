'''
Tests for the GUI helper modules TrajectoriesViewer and TrajectoryGrapher.

Verifies that both modules import correctly under the current venv
and that their core classes/functions work.

@author: stefano
'''

import unittest
import sys
import os
import tempfile

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
        """TrajectoryViewer widget can be instantiated."""
        from Helpers.TrajectoriesViewer import TrajectoryViewer

        viewer = TrajectoryViewer(appRef=app)
        self.assertIsNotNone(viewer)
        viewer.close()


if __name__ == '__main__':
    unittest.main()
