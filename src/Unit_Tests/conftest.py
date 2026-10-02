"""
pytest configuration for the Homeo test suite.

Several test modules import KheperaSimulator, which imports pyglet.window.
pyglet connects to a display as a side effect of that import, so on a machine
with no display -- an HPC compute node, a CI runner -- the modules fail at
COLLECTION time, before any test runs:

    pyglet.display.xlib.NoSuchDisplayException: Cannot connect to "None"

and pytest then aborts the whole session with "Interrupted: N errors during
collection", so the other 180-odd tests never run either.

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
"""
import os
import sys
import importlib.abc

import pytest

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
_QT_GUI_TEST_MODULES = ('HelpersGUITest.py', 'HomeoQtSimulationTest.py')


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


def pytest_ignore_collect(collection_path, config):
    if config.getoption('--no-qt') and collection_path.name in _QT_GUI_TEST_MODULES:
        return True
    return None


def pytest_report_header(config):
    if config.getoption('--no-qt'):
        return ('--no-qt: PyQt5 imports blocked; not collecting %s'
                % ', '.join(_QT_GUI_TEST_MODULES))
    return None
