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
"""
import os

if not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):
    try:
        import pyglet
        # No GL context is available, so do not let pyglet create its hidden
        # "shadow window" at import time.
        pyglet.options['shadow_window'] = False
    except Exception:          # pyglet missing or too old to have the option
        pass

    # Qt is only used for its signal/slot machinery in headless runs (the Core
    # classes emit through a QObject), but a GUI test that constructs a widget
    # needs a platform plugin that does not require a display.
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
