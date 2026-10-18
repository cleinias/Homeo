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

"""
pytest configuration for the Homeo test suite.

Several test modules import KheperaSimulator, which imports pyglet.window.
pyglet connects to a display as a side effect of that import, so on a machine
with no display -- an HPC compute node, a CI runner -- the modules fail at
COLLECTION time, before any test runs:

    pyglet.display.xlib.NoSuchDisplayException: Cannot connect to "None"

and pytest then aborts the whole session with "Interrupted: N errors during
collection", so none of the other tests runs either.

The headless experiment scripts already avoid this by turning off pyglet's
shadow window before importing anything that touches pyglet. This file does the
same for the test suite. conftest.py is imported before any test module in its
directory, which is the only place early enough for it to take effect.

Only applied when there is genuinely no display, so a normal desktop run is
unaffected and the GUI tests keep exercising real windows.

It also adds the --no-qt option, which runs the suite as if PyQt5 were not
installed: the simulation core must work without it (Helpers/QObjectProxyEmitter
falls back to a null emitter), and this is how that is tested on a machine that
does have PyQt5.  With the option, PyQt5 imports are blocked before any test
module is collected, and the two modules that test Qt GUI code are not
collected at all.  Without it, nothing here changes.

Finally, every test runs on its own fixed random stream (_isolated_random_state
below), so no test's outcome depends on which tests ran before it, and with
the run environment (HOMEO_DATA_DIR, HOMEO_RUN_TAG) restored after every test
and every test class (_restored_run_environment): many tests point the data
directory at a temporary one and pop it after, which on a machine that sets
it would send every later test's files to the default directory.

The suite's data directory is a temporary one of its own, whatever
HOMEO_DATA_DIR says when pytest starts (pytest_configure): a test, or a script
a test runs, that writes a record without choosing a directory writes it
there, not into the SimulationsData of real runs.  It is deleted at the end.
"""
import os
import random
import shutil
import sys
import tempfile
import zlib
import importlib.abc

import numpy as np
import pytest

from Core.HomeoJIT import seed_jit_rng

if not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):
    try:
        import pyglet
        # No GL context is available, so do not let pyglet create its hidden
        # "shadow window" at import time.
        pyglet.options['shadow_window'] = False
    except Exception:          # pyglet missing or too old to have the option
        pass

    # A GUI test that constructs a Qt widget needs a platform plugin that does
    # not require a display.
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')


# --no-qt ---------------------------------------------------------------------

# Test modules that exercise Qt GUI code and import PyQt5 at module level.
_QT_GUI_TEST_MODULES = ('HelpersGUITest.py', 'HomeoQtSimulationTest.py', 'AshbyExperimentGuiTest.py')


def pytest_addoption(parser):
    parser.addoption(
        '--no-qt', action='store_true', default=False,
        help='run as if PyQt5 were not installed: block its import and skip '
             'the Qt GUI test modules')


class _BlockPyQt5(importlib.abc.MetaPathFinder):
    """Makes every import of PyQt5 fail as if it were not installed."""

    def find_spec(self, fullname, path, target=None):
        if fullname == 'PyQt5' or fullname.startswith('PyQt5.'):
            raise ModuleNotFoundError(
                "No module named %r (blocked by pytest --no-qt)" % fullname,
                name=fullname)
        return None


def pytest_configure(config):
    os.environ['HOMEO_DATA_DIR'] = tempfile.mkdtemp(prefix='homeo-suite-data-')
    if not config.getoption('--no-qt'):
        return
    # The emitter decides at import time whether Qt is there, so the block must
    # be in place before anything imports PyQt5.  If something (a plugin, say)
    # already has, blocking now would silently test the Qt path instead.
    loaded = sorted(m for m in sys.modules
                    if m == 'PyQt5' or m.startswith('PyQt5.'))
    if loaded:
        raise pytest.UsageError(
            '--no-qt: PyQt5 was imported before the suite started (%s), so it '
            'cannot be hidden from the tests' % ', '.join(loaded))
    sys.meta_path.insert(0, _BlockPyQt5())


def pytest_unconfigure(config):
    shutil.rmtree(os.environ.get('HOMEO_DATA_DIR', ''), ignore_errors=True)


def pytest_ignore_collect(collection_path, config):
    if config.getoption('--no-qt') and collection_path.name in _QT_GUI_TEST_MODULES:
        return True
    return None


# Random state --------------------------------------------------------------

@pytest.fixture(autouse=True)
def _isolated_random_state(request):
    """Give every test its own fixed random stream, and leave nothing behind.

    Without this, a test that seeds the global RNGs (the GA tests seed with 42,
    BraitenbergControlTest with 11 and 5) would fix the stream for every test
    that runs after it, so whether a statistical test passes would depend on
    test order, and a test could pass alone and fail in the full run.

    Each test is seeded from its own node id, so its draws are the same whether
    it runs alone or in the suite.  Python's and NumPy's states are restored
    afterwards.  Numba's separate state cannot be read back, so it is only
    seeded: that is enough, since every test seeds it again before running.
    """
    seed = zlib.crc32(request.node.nodeid.encode())
    np_state = np.random.get_state()
    py_state = random.getstate()
    np.random.seed(seed)
    random.seed(seed)
    seed_jit_rng(seed)
    yield
    np.random.set_state(np_state)
    random.setstate(py_state)


def pytest_report_header(config):
    if config.getoption('--no-qt'):
        return ('--no-qt: PyQt5 imports blocked; not collecting %s'
                % ', '.join(_QT_GUI_TEST_MODULES))
    return None


# The run environment ---------------------------------------------------------

_RUN_ENVIRONMENT = ('HOMEO_DATA_DIR', 'HOMEO_RUN_TAG')


def _restore_run_environment(saved):
    for key, value in saved.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@pytest.fixture(autouse=True, scope='class')
def _restored_run_environment_per_class():
    "The run environment as it was before the class (its setUpClass/tearDownClass)"
    saved = {key: os.environ.get(key) for key in _RUN_ENVIRONMENT}
    yield
    _restore_run_environment(saved)


@pytest.fixture(autouse=True)
def _restored_run_environment():
    "The run environment as it was before the test"
    saved = {key: os.environ.get(key) for key in _RUN_ENVIRONMENT}
    yield
    _restore_run_environment(saved)

