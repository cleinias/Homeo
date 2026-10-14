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



class SaveDialogTest(unittest.TestCase):
    """The GUI's save buttons save to the file chosen, and Cancel saves
    nothing (review finding SR-02): until 14 Oct 2026 they took PyQt5's
    (filename, filter) tuple for the filename, so none could save."""

    def testSaveSlots(self):
        gui = makeGui(self, 1)
        for _ in range(3):
            gui._simulation.step()
        outdir = tempfile.mkdtemp(dir=_tmpdir)
        slots = (('homeostat.pickled', gui.saveHomeostat, ()),
                 ('all.txt', gui.saveAllData, ()),
                 ('plot-w.txt', gui.savePlotData, (True,)),
                 ('plot.txt', gui.savePlotData, (False,)))
        for name, slot, args in slots:
            with self.subTest(name):
                path = os.path.join(outdir, name)
                with mock.patch.object(QFileDialog, 'getSaveFileName',
                                       return_value=(path, 'All (*)')):
                    slot(*args)
                self.assertGreater(os.path.getsize(path), 0)
        canceldir = tempfile.mkdtemp(dir=_tmpdir)
        gui._simulation.homeostatFilename = os.path.join(canceldir, 'current.pickled')
        gui._simulation.dataFilename = os.path.join(canceldir, 'current-data')
        for name, slot, args in slots:
            with mock.patch.object(QFileDialog, 'getSaveFileName', return_value=('', '')):
                slot(*args)
        self.assertEqual(os.listdir(canceldir), [])



class AshbyGuiSeedTest(unittest.TestCase):
    """The GUI builds an experiment's homeostat from a seed it shows and
    pickles, the headless setup's homeostat for that seed (SR-06): until 14
    Oct 2026 the seed was thrown away, and Exps 3-5 built a different
    homeostat from the same seed."""

    @staticmethod
    def describe(hom):
        return [(u.name, u.mass, u.viscosity, u.criticalDeviation,
                 [(c.weight, c.switch, c.noise, c.state, c.status)
                  for c in u.inputConnections if c.incomingUnit.isActive()])
                for u in hom.homeoUnits if u.isActive()]

    def testTheSeedIsShownAndBuildsTheHeadlessHomeostat(self):
        from Simulator.AshbyExperimentGui import AshbyExperimentGui
        from Simulator import AshbyOriginalExperiments as AOE
        setups = {1: AOE.setup_exp1_basic_ultrastability, 2: AOE.setup_exp2_self_reorganization,
                  3: AOE.setup_exp3_training, 4: AOE.setup_exp4_alternating_environments,
                  5: AOE.setup_exp5_constraint, 6: AOE.setup_exp6_habituation,
                  7: AOE.setup_exp7_multistable}
        for exp_num, setup in setups.items():
            with self.subTest(exp=exp_num):
                gui = AshbyExperimentGui(exp_num=exp_num, seed=11)
                self.addCleanup(closeGui, gui)
                hom = gui._simulation.homeostat
                self.assertEqual(hom.seed, 11)
                self.assertEqual(gui._seedLabel.text(), 'Seed: 11')
                self.assertEqual(self.describe(hom), self.describe(setup(seed=11)[0]))
        # New draws a new seed, and shows it; a saved homeostat keeps its seed
        gui.newHomeostat()
        new_seed = gui._simulation.homeostat.seed
        self.assertEqual(gui._seedLabel.text(), 'Seed: %d' % new_seed)
        path = os.path.join(_tmpdir, 'seeded.pickled')
        gui._simulation.homeostat.saveTo(path)
        self.assertEqual(Homeostat.readFrom(path).seed, new_seed)



class DelayPerTickTest(unittest.TestCase):
    """The GUI's delay box sets the only delay per tick (SR-08): until 14 Oct
    2026 it showed the homeostat's slowingFactor (10 ms) but set the
    simulation's delay, and both applied."""

    def testTheBoxIsTheDelay(self):
        gui = makeGui(self, 1)
        box = gui.slowingFactorSpinBox
        self.assertEqual(gui._simulation.homeostat.slowingFactor, 0)
        self.assertEqual(box.value(), gui._simulation.simulDelay)
        self.assertEqual(box.minimum(), 0)
        box.setValue(0)
        self.assertEqual(gui._simulation.simulDelay, 0)
        gui.newHomeostat()
        self.assertEqual(gui._simulation.homeostat.slowingFactor, 0)
        path = os.path.join(_tmpdir, 'slow.pickled')
        hom = gui._simulation.homeostat
        hom.slowingFactor = 10
        hom.saveTo(path)
        with mock.patch.object(QFileDialog, 'getOpenFileName', return_value=(path, '')):
            gui.loadHomeostat()
        self.assertIsNot(gui._simulation.homeostat, hom)
        self.assertEqual(gui._simulation.homeostat.slowingFactor, 0)



class ResumeThreadTest(unittest.TestCase):
    """Resume runs the simulation in its own thread, as Start does (SR-10):
    until 14 Oct 2026 it ran on the GUI thread."""

    def runUntil(self, sim, ticks, timeout=20.0):
        import time
        start = time.time()
        while sim.homeostat.time < ticks and time.time() - start < timeout:
            app.processEvents()
            time.sleep(0.01)
        self.assertGreaterEqual(sim.homeostat.time, ticks)

    def testResumeRunsInTheSimulationThread(self):
        from PyQt5.QtCore import QThread
        gui = makeGui(self, 1)
        sim = gui._simulation
        self.addCleanup(lambda: (gui._simulThread.quit(), gui._simulThread.wait(5000)))
        sim.setSimulDelay(0)
        threads = []
        sim.tick_observers.append(lambda hom, t: threads.append(QThread.currentThread()))
        sim.maxRuns = 20
        gui.resume()                        # the first run, as after New or Load
        self.runUntil(sim, 20)
        gui.pause()
        sim.maxRuns = 40
        gui.resume()                        # a run after a pause
        self.runUntil(sim, 40)
        self.assertEqual(len(threads), 40)
        self.assertTrue(all(t is not app.thread() for t in threads))


if __name__ == '__main__':
    unittest.main()
