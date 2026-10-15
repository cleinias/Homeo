'''
Created on Oct 15, 2026

@author: stefano

The pyglet window of the phototaxis experiments' --visualize and the GA
replay (KheperaRobotView), drawn offscreen.

Each drawing runs in a subprocess with pyglet's headless (EGL) mode, which
must be chosen before pyglet opens a display; where no EGL context can be
made, those tests are skipped.  The view's camera controls need no GL and
run in-process.
'''
from KheperaSimulator.KheperaSimulator import KheperaRobotView
from pyglet.window import key, mouse

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from types import SimpleNamespace

SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_PREAMBLE = '''
import json, sys
import pyglet
pyglet.options['headless'] = True
try:
    window = pyglet.window.Window(width=400, height=400, visible=False)
except Exception as e:
    print('NOGL', e)
    sys.exit(0)
import numpy as np
from math import radians, cos, sin

def frame():
    "The window's colour buffer, as rows of RGBA from the bottom"
    image = pyglet.image.get_buffer_manager().get_color_buffer().get_image_data()
    data = image.get_data('RGBA', image.width * 4)
    return np.frombuffer(data, dtype=np.uint8).reshape(image.height, image.width, 4)
'''

# A robot heading at 60 degrees, drawn in a close-up: how many pixels of the
# outline's colour lie on the inner part of the rays at +60 and -60 degrees
# from its centre (the heading radius is on one of them)
_HEADING = _PREAMBLE + '''
from pyglet.gl import glEnable, glBlendFunc, GL_BLEND, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA
from pyglet.window import key
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
from KheperaSimulator.KheperaSimulator import KheperaSimulation, KheperaRobotView
sim = KheperaSimulation()
sim.setupWorld('kheperaBraitenberg2_HOMEO_World')
robot = sim.allBodies['Khepera']
robot.moveTo((3, 4))
robot.rotateTo(radians(60))
view = KheperaRobotView(window, sim)
view.on_key_press(key.C, 0)
window.switch_to()
view.draw()
pixels = frame().astype(int)
perPixel = view.metresPerPixel()
r = robot.diameter / 2
counts = {}
for ray in (60, -60):
    hits = set()
    for i in range(40):
        d = r * (0.15 + 0.3 * i / 39) / perPixel
        x = 200 + d * cos(radians(ray))
        y = 200 + d * sin(radians(ray))
        for px in (int(x), int(x) + 1):
            for py in (int(y), int(y) + 1):
                red, green = pixels[py, px, 0], pixels[py, px, 1]
                if red > 100 and green < 90:
                    hits.add((px, py))
    counts[ray] = len(hits)
bx = int(round(200 + 0.3 * r / perPixel * cos(radians(240))))
by = int(round(200 + 0.3 * r / perPixel * sin(radians(240))))
from math import atan2, degrees
fields = {}
for fixture in robot.body.fixtures:
    field = (fixture.userData or {}).get('pygletField')
    if field is not None:
        eye = [k[:-len('AngleRange')] for k in fixture.userData if k.endswith('AngleRange')]
        position = list(field.position)
        # A receptor, the arc's points, a receptor: the directions of the two
        # edge lines, from their receptors to the arc's ends
        low = (position[2] - position[0], position[3] - position[1])
        high = (position[-4] - position[-2], position[-3] - position[-1])
        fields[eye[0] if eye else 'receptor %d' % len(fields)] = [
            round(degrees(atan2(low[1], low[0])), 2), round(degrees(atan2(high[1], high[0])), 2)]
print('RESULT', json.dumps({'counts': counts, 'behind': pixels[by, bx, :3].tolist(),
                            'fields': fields}))
sim.trajectoryWriter.runOnce(transitionMessage='CLOSEFILE')
'''

# The --visualize window of the direct experiment: a close-up after half a
# second, then Q
_VISUALIZE = _PREAMBLE + '''
from pyglet.window import key
window.close()          # only to check that a context can be made
import runpy
def shot(dt):
    w = list(pyglet.app.windows)[0]
    w.dispatch_event('on_key_press', key.C, 0)
    w.switch_to()
    w.dispatch_event('on_draw')
    pixels = frame()
    h, w_ = pixels.shape[:2]
    print('RESULT', json.dumps({'centre': pixels[h // 2, w_ // 2, :3].tolist()}))
    list(pyglet.app.windows)[0].dispatch_event('on_key_press', key.Q, 0)
pyglet.clock.schedule_once(shot, 0.5)
sys.argv = ['x', '--visualize', '--seed', '3']
runpy.run_module('HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct',
                 run_name='__main__')
print('CLOSED')
'''

BACKGROUND = [140, 242, 255]    # glClearColor(0.55, 0.95, 1.0)


class KheperaRenderingTest(unittest.TestCase):

    def _draw(self, script):
        "Run script offscreen; return its RESULT and its whole output"
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'draw.py')
            with open(path, 'w') as f:
                f.write(textwrap.dedent(script))
            # Without numba's compiler: numba's LLVM and the one in Mesa's
            # software renderer (llvmpipe, offscreen) abort when one process
            # compiles with both
            env = dict(os.environ, HOME=tmp, PYTHONPATH=SRC_DIR, NUMBA_DISABLE_JIT='1')
            result = subprocess.run([sys.executable, path], cwd=tmp, env=env,
                                    capture_output=True, text=True, timeout=300)
        self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-2000:])
        if result.stdout.startswith('NOGL'):
            self.skipTest('no headless GL context: ' + result.stdout.strip())
        line = [l for l in result.stdout.splitlines() if l.startswith('RESULT ')]
        self.assertEqual(len(line), 1, result.stdout[-2000:] + result.stderr[-2000:])
        return json.loads(line[0][len('RESULT '):]), result.stdout

    def testTheRobotIsDrawnTurnedItsOwnWay(self):
        """a robot heading at 60 degrees is drawn with its heading radius at
        60, not -60: the shape shader turns clockwise (until 15 Oct 2026 each
        shape was drawn turned the wrong way)"""
        result, _ = self._draw(_HEADING)
        self.assertGreaterEqual(result['counts']['60'], 6, result)
        self.assertEqual(result['counts']['-60'], 0, result)

    def testTheRobotIsDrawnFilled(self):
        "inside the body, away from its outline and heading, the body's fill, not the background"
        result, _ = self._draw(_HEADING)
        self.assertTrue(all(abs(a - b) > 20 for a, b in zip(result['behind'], BACKGROUND)), result)

    def testEachEyeDrawsOneFieldBoundary(self):
        """the e-puck2's eyes each draw one field outline, the outer boundary
        of their two receptors' fields, not one arc per receptor"""
        result, _ = self._draw(_HEADING)
        self.assertEqual(sorted(result['fields']), ['leftEye', 'rightEye'], result)
        # ls7 at 17.143 and ls6 at 45.791 degrees, 180-degree fields
        self.assertEqual(result['fields']['leftEye'], [-72.86, 135.79])
        self.assertEqual(result['fields']['rightEye'], [-135.88, 72.77])

    def testTheVisualizerDrawsAndCloses(self):
        "--visualize opens, draws a close-up centred on the robot, and closes on Q"
        result, out = self._draw(_VISUALIZE)
        self.assertNotEqual(result['centre'], BACKGROUND, result)
        self.assertIn('CLOSED', out)


class KheperaRobotViewControlsTest(unittest.TestCase):
    "The view's mouse and keys, on a window and a simulation that only hold numbers"

    def setUp(self):
        self.robot = SimpleNamespace(diameter=0.074, body=SimpleNamespace(position=(2.0, 3.0)))
        self.sim = SimpleNamespace(allBodies={'Khepera': self.robot}, showFields=False)
        self.window = SimpleNamespace(width=800, height=600)
        self.view = KheperaRobotView(self.window, self.sim)

    def testItStartsOnTheWholeArena(self):
        self.assertFalse(self.view.follow)
        self.assertEqual((self.view.camera.x, self.view.camera.y), KheperaRobotView.OVERVIEW_CENTRE)
        self.assertEqual(self.view.camera.zoom, KheperaRobotView.OVERVIEW_ZOOM)

    def testCTogglesCloseUpAndArena(self):
        self.assertTrue(self.view.on_key_press(key.C, 0))
        self.assertTrue(self.view.follow)
        self.assertEqual(self.view.camera.zoom, KheperaRobotView.CLOSE_UP_ZOOM)
        self.view.on_key_press(key.C, 0)
        self.assertFalse(self.view.follow)
        self.assertEqual(self.view.camera.zoom, KheperaRobotView.OVERVIEW_ZOOM)
        self.assertEqual((self.view.camera.x, self.view.camera.y), KheperaRobotView.OVERVIEW_CENTRE)

    def testFAndVToggle(self):
        self.view.on_key_press(key.F, 0)
        self.assertTrue(self.view.follow)
        self.view.on_key_press(key.V, 0)
        self.assertTrue(self.sim.showFields)
        self.view.on_key_press(key.V, 0)
        self.assertFalse(self.sim.showFields)

    def testOtherKeysAreLeftToTheWindow(self):
        self.assertFalse(self.view.on_key_press(key.UP, 0))

    def testTheWheelZoomsAboutThePointer(self):
        "the world point under the pointer stays under it"
        x, y = 700, 100
        def under(view):
            perPixel = view.metresPerPixel()
            return (view.camera.x + (x - 400) * perPixel, view.camera.y + (y - 300) * perPixel)
        before = under(self.view)
        self.view.on_mouse_scroll(x, y, 0, 3)
        self.assertLess(self.view.camera.zoom, KheperaRobotView.OVERVIEW_ZOOM)
        for a, b in zip(under(self.view), before):
            self.assertAlmostEqual(a, b)

    def testDraggingPansAndStopsFollowing(self):
        self.view.follow = True
        x0 = self.view.camera.x
        self.view.on_mouse_drag(0, 0, 10, 0, mouse.LEFT, 0)
        self.assertFalse(self.view.follow)
        self.assertAlmostEqual(self.view.camera.x, x0 - 10 * self.view.metresPerPixel())


if __name__ == "__main__":
    unittest.main()
