'''
Tests of the GUI: closed windows, the uniselector-type combo box, and the
Ashby experiments' New and Load.

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
from PyQt5.QtWidgets import QApplication, QComboBox, QFileDialog

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


class UniselectorComboTest(unittest.TestCase):
    '''The uniselector-type combo box shows the unit's type and changes it
    once per selection (it was connected once per uniselector class).'''

    def testOneChangePerSelection(self):
        from Core.HomeoUnit import HomeoUnit
        calls = []
        real = HomeoUnit.changeUniselectorType

        def spy(unit, *args):
            calls.append(unit)
            return real(unit, *args)

        with mock.patch.object(HomeoUnit, 'changeUniselectorType', spy):
            gui = makeGui(self, 1)
            unit = gui._simulation.homeostat.homeoUnits[0]
            combo = gui._homeostat_gui.findChild(QComboBox, 'unit1UniselectTypeComboBox')
            self.assertEqual('HomeoUniselector' + combo.currentText(),
                             type(unit.uniselector).__name__)
            del calls[:]
            combo.setCurrentIndex((combo.currentIndex() + 1) % combo.count())
        self.assertEqual(calls, [unit])
        self.assertEqual('HomeoUniselector' + combo.currentText(),
                         type(unit.uniselector).__name__)


class AshbyGuiNewAndLoadTest(unittest.TestCase):
    '''New and Load rebuild the homeostat and rebind the GUI to it, for
    every experiment (all of them have inactive units in empty slots).'''

    def assertGuiBoundTo(self, gui, hom):
        self.assertIs(gui._simulation.homeostat, hom)
        self.assertEqual(set(gui.pgChartsAndItems), set(hom.homeoUnits))

    def assertExperimentRunsOn(self, gui, hom, n_callbacks):
        '''The experiment's callbacks are installed and watch hom.'''
        self.assertEqual(len(gui._simulation.tick_callbacks), n_callbacks)
        self.assertIs(gui._stability_tracker.hom, hom)

    def testNew(self):
        for exp_num in range(1, 8):
            with self.subTest(exp=exp_num):
                gui = makeGui(self, exp_num)
                old = gui._simulation.homeostat
                n_callbacks = len(gui._simulation.tick_callbacks)
                gui.newHomeostat()
                new = gui._simulation.homeostat
                self.assertIsNot(new, old)
                self.assertTrue(any(not u.isActive() for u in new.homeoUnits))
                self.assertGuiBoundTo(gui, new)
                self.assertExperimentRunsOn(gui, new, n_callbacks)

    def testNewRestartsTheExperiment(self):
        '''Exp 5: a fibre joined before New is not joined after it, and the
        new fibre can be joined.'''
        gui = makeGui(self, 5)
        gui._joinExp5Constraint()
        self.assertTrue(gui._constraint_flag[0])
        gui.newHomeostat()
        self.assertFalse(gui._constraint_flag[0])
        self.assertTrue(gui._joinBtn.isEnabled())
        self.assertFalse(gui._releaseBtn.isEnabled())
        gui._joinExp5Constraint()
        self.assertTrue(gui._constraint_flag[0])

    def testLoad(self):
        for exp_num in (1, 3):
            with self.subTest(exp=exp_num):
                gui = makeGui(self, exp_num)
                path = os.path.join(_tmpdir, 'exp%d.pickled' % exp_num)
                gui._simulation.homeostat.saveTo(path)
                n_callbacks = len(gui._simulation.tick_callbacks)
                old = gui._simulation.homeostat
                with mock.patch.object(QFileDialog, 'getOpenFileName',
                                       return_value=(path, '')):
                    gui.loadHomeostat()
                hom = gui._simulation.homeostat
                self.assertIsNot(hom, old)
                self.assertGuiBoundTo(gui, hom)
                self.assertExperimentRunsOn(gui, hom, n_callbacks)


if __name__ == '__main__':
    unittest.main()
