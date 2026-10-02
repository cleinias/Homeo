'''
Created on Oct 2, 2026

@author: stefano

Headless simulation and GA runs without PyQt5.

HomeoQtSimulation is a QObject when PyQt5 is installed, and a plain object
with null signals when it is not, so that the GA's fitness evaluations -- and
any headless script built on it -- run on a machine with no Qt.  These tests
load a private copy of the module with PyQt5 hidden, so they exercise the
no-Qt path even where PyQt5 is installed, and run a small GA, serial and
parallel, in a subprocess where PyQt5 cannot be imported at all.
'''
from Helpers import QObjectProxyEmitter
from Simulator import HomeoQtSimulation as HomeoQtSimulationModule

import importlib.util
import multiprocessing
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock

_PYQT5_MODULES = ('PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'PyQt5.sip')


def _load_simulation_module_without_qt():
    """Return a fresh copy of Simulator.HomeoQtSimulation, loaded as if PyQt5
    were absent (a None entry in sys.modules makes that import fail)."""
    spec = importlib.util.spec_from_file_location(
        '_HomeoQtSimulation_without_qt', HomeoQtSimulationModule.__file__)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, {name: None for name in _PYQT5_MODULES}):
        spec.loader.exec_module(module)
    return module


class HomeoQtSimulationWithoutQtTest(unittest.TestCase):
    """HomeoQtSimulation with PyQt5 hidden."""

    @classmethod
    def setUpClass(cls):
        cls.module = _load_simulation_module_without_qt()

    def testIsAPlainObject(self):
        "without QtCore the class is not a QObject and there is no QApplication"
        self.assertEqual(self.module.HomeoQtSimulation.__bases__, (object,))
        self.assertIsNone(self.module.QApplication)

    def testSignalsAreNull(self):
        "both signals accept emit and refuse connect"
        sim = self.module.HomeoQtSimulation()
        for name in ('homeostatFilenameChanged', 'liveDataCritDevChanged'):
            signal = getattr(sim, name)
            self.assertIsInstance(signal, QObjectProxyEmitter.NullSignal)
            self.assertIsNone(signal.emit('x'))
            with self.assertRaises(RuntimeError):
                signal.connect(print)

    def testSettingTheFilenameEmitsHarmlessly(self):
        "a setter that emits works without Qt"
        sim = self.module.HomeoQtSimulation()
        sim.homeostatFilename = 'some-name'
        self.assertEqual(sim.homeostatFilename, 'some-name')

    def testStepAndGoRunTheHomeostat(self):
        "step() and go() advance the homeostat, live data on, no Qt anywhere"
        sim = self.module.HomeoQtSimulation()
        sim.initializeExperSetup()
        sim.initializeLiveData()
        sim.liveDataOn = True                 # makes updateLiveData emit on every step
        sim.maxRuns = 10
        for _ in range(5):
            sim.step()
        self.assertEqual(sim.homeostat.time, 5)
        sim.go()                              # default 1 ms delay per step
        self.assertEqual(sim.homeostat.time, 10)


@unittest.skipUnless(QObjectProxyEmitter.QT_AVAILABLE, 'PyQt5 is not available')
class HomeoQtSimulationWithQtTest(unittest.TestCase):
    """HomeoQtSimulation with PyQt5: unchanged, still a QObject with real signals."""

    def testIsAQObjectWithWorkingSignals(self):
        "the class is a QObject and its signals reach connected slots"
        from PyQt5.QtCore import QObject
        sim = HomeoQtSimulationModule.HomeoQtSimulation()
        self.assertIsInstance(sim, QObject)
        received = []
        sim.homeostatFilenameChanged.connect(received.append)
        sim.homeostatFilename = 'some-name'
        self.assertEqual(received, ['some-name'])


# Installed as sitecustomize in every Python process of the GA run -- the parent
# and the forkserver workers, which are fresh interpreters -- so none of them
# can import PyQt5.
_HIDE_PYQT5 = '''
import sys, importlib.abc
class _HidePyQt5(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path, target=None):
        if name == 'PyQt5' or name.startswith('PyQt5.'):
            raise ModuleNotFoundError('No module named %r (hidden by WithoutQtTest)' % name, name=name)
sys.meta_path.insert(0, _HidePyQt5())
'''

_GA_RUN = '''
import sys
sys.path.insert(0, {src!r})
if __name__ == '__main__':
    from Simulator.HomeoGenAlg import HomeoGASimulation
    HomeoGASimulation.dataDirRoot = {out!r}
    ga = HomeoGASimulation(stepsSize=100, popSize=4, generSize=1,
                           exp='initializeBraiten2_direct_GA_continuous_weightfree_fixed_dt',
                           simulatorBackend='HOMEO', nWorkers={workers})
    pop = ga.generateRandomPop(randomSeed=1)
    ga.runGaSimulation(pop)
    print('FITNESSES %r' % [ind.fitness.values[0] for ind in pop])
    print('PYQT5_LOADED %r' % sorted(n for n, m in sys.modules.items()
                                     if n.startswith('PyQt5') and m is not None))
'''


class GARunWithoutQtTest(unittest.TestCase):
    """A small GA, end to end, in processes that cannot import PyQt5."""

    def _runGA(self, workers):
        src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with tempfile.TemporaryDirectory() as tmp:
            hide_dir = os.path.join(tmp, 'hide')
            os.mkdir(hide_dir)
            with open(os.path.join(hide_dir, 'sitecustomize.py'), 'w') as f:
                f.write(_HIDE_PYQT5)
            script = os.path.join(tmp, 'ga_run.py')
            with open(script, 'w') as f:
                f.write(_GA_RUN.format(src=src_dir, out=tmp, workers=workers))
            env = dict(os.environ, PYTHONPATH=hide_dir,
                       NUMBA_CACHE_DIR=os.path.join(tmp, 'numba'))
            result = subprocess.run([sys.executable, script], cwd=src_dir, env=env,
                                    capture_output=True, text=True, timeout=600)
        self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-2000:])
        self.assertIn('PYQT5_LOADED []', result.stdout)
        fitnesses = eval(result.stdout.split('FITNESSES ')[1].splitlines()[0])
        self.assertEqual(len(fitnesses), 4)
        for value in fitnesses:
            self.assertTrue(0 <= value < 100, fitnesses)

    def testSerialGANeedsNoQt(self):
        "a GA with one worker (in-process evaluation) runs without PyQt5"
        self._runGA(workers=1)

    @unittest.skipUnless('forkserver' in multiprocessing.get_all_start_methods(),
                         'the GA pool uses the forkserver start method')
    def testParallelGANeedsNoQt(self):
        "a GA with two forkserver workers runs without PyQt5 in any process"
        self._runGA(workers=2)


if __name__ == "__main__":
    unittest.main()
