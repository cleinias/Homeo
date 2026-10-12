'''
Tests of the Ashby experiment GUI: closed windows, New and Load.

The GUI writes a pickled homeostat, a SimsData directory and
~/.HomeoSimDataDir.txt; all of them go to a temporary directory here.
'''

import gc
import os
import sys
import shutil
import tempfile
import unittest
from unittest import mock

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PyQt5.QtWidgets import QApplication, QFileDialog

from Core.Homeostat import Homeostat
from Core.HomeoUnitNewtonian import HomeoUnitNewtonian

app = QApplication.instance() or QApplication(sys.argv)

_saved_env = {}
_tmpdir = None


def setUpModule():
    global _tmpdir
    _tmpdir = tempfile.mkdtemp(prefix='ashbygui-')
    for key in ('HOME', 'HOMEO_DATA_DIR'):
        _saved_env[key] = os.environ.get(key)
        os.environ[key] = _tmpdir


def tearDownModule():
    for key, value in _saved_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    shutil.rmtree(_tmpdir, ignore_errors=True)


def closeGui(gui):
    for window in (gui._homeostat_gui, gui):
        try:
            window.close()
        except RuntimeError:                # already deleted by Qt
            pass


def makeGui(test, exp_num):
    from Simulator.AshbyExperimentGui import AshbyExperimentGui
    gui = AshbyExperimentGui(exp_num=exp_num)
    test.addCleanup(closeGui, gui)
    return gui


class ClosedWindowsTest(unittest.TestCase):
    '''Garbage collection of closed GUIs must not crash the interpreter
    (as "Change Experiment" leaves them).'''

    def testCollectingClosedGuis(self):
        from Simulator.AshbyExperimentGui import AshbyExperimentGui
        for exp_num in (1, 3):
            gui = AshbyExperimentGui(exp_num=exp_num)
            closeGui(gui)
            gui = None
            gc.collect()
        makeGui(self, 5)
        gc.collect()                        # segfaulted with named plots


class BareUnitSignalsTest(unittest.TestCase):
    '''A unit whose switch was never set must still report its values.'''

    def testAllValuesChangedOnAFreshUnit(self):
        hom = Homeostat()
        unit = HomeoUnitNewtonian()
        hom.addFullyConnectedUnit(unit)
        unit.allValuesChanged()                     # raised AttributeError
        self.assertEqual(unit.switch, unit.inputConnections[0].switch)


class AshbyGuiNewAndLoadTest(unittest.TestCase):
    '''New and Load rebuild the homeostat and rebind the GUI to it, for
    every experiment (all of them have inactive units in empty slots).'''

    def assertGuiBoundTo(self, gui, hom):
        self.assertIs(gui._simulation.homeostat, hom)
        self.assertEqual(set(gui.pgChartsAndItems), set(hom.homeoUnits))

    def testNew(self):
        for exp_num in range(1, 8):
            with self.subTest(exp=exp_num):
                gui = makeGui(self, exp_num)
                old = gui._simulation.homeostat
                gui.newHomeostat()
                new = gui._simulation.homeostat
                self.assertIsNot(new, old)
                self.assertTrue(any(not u.isActive() for u in new.homeoUnits))
                self.assertGuiBoundTo(gui, new)

    def testLoad(self):
        for exp_num in (1, 3):
            with self.subTest(exp=exp_num):
                gui = makeGui(self, exp_num)
                path = os.path.join(_tmpdir, 'exp%d.pickled' % exp_num)
                gui._simulation.homeostat.saveTo(path)
                old = gui._simulation.homeostat
                with mock.patch.object(QFileDialog, 'getOpenFileName',
                                       return_value=(path, '')):
                    gui.loadHomeostat()
                hom = gui._simulation.homeostat
                self.assertIsNot(hom, old)
                self.assertGuiBoundTo(gui, hom)


if __name__ == '__main__':
    unittest.main()
