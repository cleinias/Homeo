'''
Tests of the Ashby experiment GUI: closed windows.

The GUI writes a pickled homeostat, a SimsData directory and
~/.HomeoSimDataDir.txt; all of them go to a temporary directory here.
'''

import gc
import os
import sys
import shutil
import tempfile
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PyQt5.QtWidgets import QApplication

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


if __name__ == '__main__':
    unittest.main()
