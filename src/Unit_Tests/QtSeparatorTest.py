'''
Created on Oct 14, 2026

@author: stefano

The GUI's Separator widget (review finding HV-13): every documented way of
building one works, and its source compiles without invalid escapes.
'''
import os
import unittest
import warnings

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget

from Helpers import QtSeparator
from Helpers.QtSeparator import Separator

app = QApplication.instance() or QApplication([])


class SeparatorTest(unittest.TestCase):

    def setUp(self):
        self.parent = QWidget()
        self.addCleanup(self.parent.deleteLater)

    def testEveryWayOfBuildingOne(self):
        cases = [(Separator(), None, Qt.Horizontal),
                 (Separator(self.parent), self.parent, Qt.Horizontal),
                 (Separator(Qt.Vertical, self.parent), self.parent, Qt.Vertical),
                 (Separator(orientation=Qt.Vertical, parent=self.parent), self.parent, Qt.Vertical)]
        for sep, parent, orientation in cases:
            self.assertIs(sep.parent(), parent)
            self.assertEqual(sep.orientation, orientation)
        extent = cases[2][0].style().pixelMetric(cases[2][0].style().PM_ToolBarSeparatorExtent)
        self.assertEqual(cases[2][0].width(), extent)

    def testNoInvalidEscapes(self):
        with open(os.path.splitext(QtSeparator.__file__)[0] + '.py') as f:
            source = f.read()
        with warnings.catch_warnings():
            warnings.simplefilter('error')
            compile(source, QtSeparator.__file__, 'exec')


if __name__ == '__main__':
    unittest.main()
