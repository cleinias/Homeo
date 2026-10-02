'''
Created on Oct 2, 2026

@author: stefano

Tests for Helpers.QObjectProxyEmitter, with and without PyQt5.

With PyQt5 the emitter must behave exactly as it always has: one SignalHub
QObject per object, delivering to connected slots.  Without PyQt5 it must hand
back a null hub that swallows emits, so the simulation core runs on a machine
with no Qt.  The null path is tested here even when PyQt5 is installed, by
loading a private copy of the module with PyQt5 hidden.
'''
from Helpers import QObjectProxyEmitter
from Helpers.QObjectProxyEmitter import SIGNAL_NAMES

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


def _load_without_qt():
    """Return a fresh copy of QObjectProxyEmitter, loaded as if PyQt5 were absent.

    A None entry in sys.modules makes any import of that name raise ImportError,
    which is what the module sees on a machine without PyQt5."""
    hidden = {name: None for name in ('PyQt5', 'PyQt5.QtCore', 'PyQt5.sip')}
    spec = importlib.util.spec_from_file_location(
        '_QObjectProxyEmitter_without_qt', QObjectProxyEmitter.__file__)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, hidden):
        spec.loader.exec_module(module)
    return module


class Owner(object):
    "Stands in for a Core object that emits signals."
    pass


@unittest.skipUnless(QObjectProxyEmitter.QT_AVAILABLE, 'PyQt5 is not available')
class EmitterWithQtTest(unittest.TestCase):
    """The real, Qt-backed emitter."""

    def testSignalNamesMatchSignalHub(self):
        "SIGNAL_NAMES lists exactly the signals SignalHub declares"
        from PyQt5.QtCore import pyqtSignal
        declared = {name for name, value in vars(QObjectProxyEmitter.SignalHub).items()
                    if isinstance(value, pyqtSignal)}
        self.assertEqual(declared, set(SIGNAL_NAMES))
        self.assertEqual(len(SIGNAL_NAMES), len(set(SIGNAL_NAMES)))

    def testEmitReachesConnectedSlot(self):
        "a connected slot receives what is emitted"
        ob = Owner()
        received = []
        QObjectProxyEmitter.emitter(ob).massChanged.connect(received.append)
        QObjectProxyEmitter.emitter(ob).massChanged.emit(3.5)
        self.assertEqual(received, [3.5])

    def testOneHubPerObject(self):
        "the same object always gets the same hub, different objects different hubs"
        a, b = Owner(), Owner()
        self.assertIs(QObjectProxyEmitter.emitter(a), QObjectProxyEmitter.emitter(a))
        self.assertIsNot(QObjectProxyEmitter.emitter(a), QObjectProxyEmitter.emitter(b))

    def testSignalsDoNotCrossObjects(self):
        "an emit on one object does not reach a slot connected to another"
        a, b = Owner(), Owner()
        received = []
        QObjectProxyEmitter.emitter(a).nameChanged.connect(received.append)
        QObjectProxyEmitter.emitter(b).nameChanged.emit('b')
        self.assertEqual(received, [])


class EmitterWithoutQtTest(unittest.TestCase):
    """The null emitter used when PyQt5 is absent."""

    def setUp(self):
        self.module = _load_without_qt()

    def testQtReportedAbsent(self):
        "the module knows it has no Qt and defines no SignalHub"
        self.assertFalse(self.module.QT_AVAILABLE)
        self.assertFalse(hasattr(self.module, 'SignalHub'))

    def testEveryKnownSignalAcceptsEmit(self):
        "emit works, and does nothing, for every known signal and any arguments"
        hub = self.module.emitter(Owner())
        for name in self.module.SIGNAL_NAMES:
            self.assertIsNone(getattr(hub, name).emit())
            self.assertIsNone(getattr(hub, name).emit(1.0))
            self.assertIsNone(getattr(hub, name).emit(1.0, 2.0))

    def testUnknownSignalRaises(self):
        "a misspelt signal fails as it would on a real SignalHub"
        hub = self.module.emitter(Owner())
        with self.assertRaises(AttributeError):
            hub.massChangd.emit(1.0)

    def testConnectRaises(self):
        "connecting is a mistake when signals cannot be delivered"
        hub = self.module.emitter(Owner())
        with self.assertRaises(RuntimeError):
            hub.massChanged.connect(print)

    def testNothingStoredOnTheObject(self):
        "the null emitter leaves the object as it found it, so pickling is unaffected"
        ob = Owner()
        self.module.emitter(ob).massChanged.emit(1.0)
        self.assertEqual(vars(ob), {})


# Run in a fresh interpreter: hides PyQt5, runs a short headless phototaxis
# experiment, then reports whether any part of PyQt5 got imported anyway.
_HEADLESS_RUN = '''
import sys, runpy
for name in ('PyQt5', 'PyQt5.QtCore', 'PyQt5.sip'):
    sys.modules[name] = None
# --steps must be a multiple of the script's report interval (500)
sys.argv = ['phototaxis', '--batch', '1', '--steps', '500', '--seed', '1',
            '--start-at-rest', '--no-traj']
runpy.run_module('HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct',
                 run_name='__main__')
from Helpers import QObjectProxyEmitter
loaded = sorted(n for n, m in sys.modules.items() if n.startswith('PyQt5') and m is not None)
print('QT_AVAILABLE=%s PYQT5_LOADED=%s' % (QObjectProxyEmitter.QT_AVAILABLE, loaded))
'''


class HeadlessRunWithoutQtTest(unittest.TestCase):
    """A real headless experiment, end to end, in a process with no PyQt5."""

    def testHeadlessRunNeedsNoQt(self):
        "a short phototaxis run completes without importing PyQt5"
        src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, HOMEO_DATA_DIR=tmp,
                       NUMBA_CACHE_DIR=os.path.join(tmp, 'numba'))
            result = subprocess.run([sys.executable, '-c', _HEADLESS_RUN],
                                    cwd=src_dir, env=env, capture_output=True,
                                    text=True, timeout=600)
        self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-2000:])
        self.assertIn('QT_AVAILABLE=False PYQT5_LOADED=[]', result.stdout)


if __name__ == "__main__":
    unittest.main()
