'''
Created on Oct 14, 2026

@author: stefano

The Webots backend (Phase F of the 7 Oct 2026 review plan): Homeo runs
Webots as its e-puck2's extern controller.  Each test runs its Webots in a
subprocess -- one process can control one Webots robot -- and compares it
with the Box2D twin: the same eyes' irradiance, the same capped wheel speed,
the same virtual quality sensors, and a phototaxis run through the
experiments' own scripts.  Skipped where Webots cannot run (not installed,
or neither a display nor xvfb-run).
'''
import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest

from WebotsSimulator.WebotsSimulation import available

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Measures in Webots and in Box2D, for one world, and prints them as JSON
_MEASURE = r'''
import json, math, sys
sys.path.insert(0, {src!r})
from Box2D import b2Vec2
from KheperaSimulator.KheperaSimulator import KheperaSimulation
from WebotsSimulator.WebotsSimulation import WebotsSimulation
from HomeoExperiments.KheperaExperiments.phototaxis_common import set_start_pose

world = {world!r}
poses = [(4, 4, 0), (6.5, 6.2, 30), (7.3, 6.6, 160), (5, 8, -60), (8, 8, 45)]   # the last: light behind
webots = WebotsSimulation.shared()
webots.setupWorld(world, {data!r})
box2d = KheperaSimulation()
box2d.setupWorld(world, {data!r})
wr, br = webots.allBodies['Khepera'], box2d.allBodies['Khepera']
out = dict(eyes=[], qualities=[])
for x, y, h in poses:
    set_start_pose(wr, x, y, h)
    webots._supervisor.step(webots._timeStepMs)
    set_start_pose(br, x, y, h)
    for eye in ('leftEye', 'rightEye'):
        out['eyes'].append((wr.lightIrradiance(eye), br.irradAtSensor(eye, br.detectableLights)))
    for quality in [q for q in br.detectableSources if q != 'light']:
        for side in ('left', 'right'):
            name = side + {{'temperature': 'Temp', 'oxygen': 'Oxy', 'organic': 'Org'}}[quality] + 'Eye'
            out['qualities'].append((wr.getSensorReadByQuality(name, quality),
                                     br.getSensorReadByQuality(name, quality)))
# the capped top speed, straight ahead for 100 steps
set_start_pose(wr, 4, 4, 0)
webots._supervisor.step(webots._timeStepMs)
start = wr.body.position
wr.setSpeed(10.0, 10.0)                   # far above the cap
for i in range(100):
    webots.advanceSim()
end = wr.body.position
out['speed'] = (end - start).length / (100 * webots.timeStep)
out['maxSpeed'] = wr.maxSpeed
webots.saveTrajectory()
box2d.saveTrajectory()
print('MEASURES ' + json.dumps(out))
'''

# Places the robot in Webots and Box2D and, with no step in between, prints
# the pose and the eyes' irradiance each reports
_PLACE = r'''
import json, math, sys
sys.path.insert(0, {src!r})
from KheperaSimulator.KheperaSimulator import KheperaSimulation
from WebotsSimulator.WebotsSimulation import WebotsSimulation
from HomeoExperiments.KheperaExperiments.phototaxis_common import set_start_pose

world = 'kheperaBraitenberg2_HOMEO_World'
webots = WebotsSimulation.shared()
webots.setupWorld(world, {data!r})
box2d = KheperaSimulation()
box2d.setupWorld(world, {data!r})
wr, br = webots.allBodies['Khepera'], box2d.allBodies['Khepera']
out = []
for x, y, h in [(5.5, 3.0, 120), (6.0, 6.0, 45)]:
    set_start_pose(wr, x, y, h)
    set_start_pose(br, x, y, h)
    p = wr.body.position
    out.append(dict(pose=(x, y, h), webots=(p[0], p[1], math.degrees(wr.body.angle) % 360),
                    eyes=[(wr.lightIrradiance(e), br.irradAtSensor(e, br.detectableLights))
                          for e in ('leftEye', 'rightEye')]))
webots.saveTrajectory()
box2d.saveTrajectory()
print('PLACED ' + json.dumps(out))
'''


@unittest.skipUnless(available(), 'Webots cannot run here (not installed, or no display/xvfb-run)')
class WebotsBackendTest(unittest.TestCase):

    def measure(self, world):
        with tempfile.TemporaryDirectory() as tmp:
            script = os.path.join(tmp, 'measure.py')
            with open(script, 'w') as f:
                f.write(_MEASURE.format(src=SRC, world=world, data=tmp))
            r = subprocess.run([sys.executable, script], capture_output=True, text=True,
                               timeout=300, env=dict(os.environ, HOMEO_DATA_DIR=tmp))
        lines = [l for l in r.stdout.splitlines() if l.startswith('MEASURES ')]
        self.assertTrue(lines, r.stdout[-2000:] + r.stderr[-2000:])
        return json.loads(lines[0][len('MEASURES '):])

    def testBraitenberg2World(self):
        '''Webots' LightSensors read the Box2D eyes' irradiance (same
        positions, facings and light model; 0.5% for the sensors' float
        poses), and the wheels top out at the cap.'''
        m = self.measure('kheperaBraitenberg2_HOMEO_World')
        for webots, box2d in m['eyes']:
            self.assertAlmostEqual(webots, box2d, delta=0.005 * box2d + 1e-6)
        self.assertTrue(any(box2d > 0 for _, box2d in m['eyes']))
        self.assertTrue(any(box2d == 0 for _, box2d in m['eyes']))     # the light behind
        self.assertAlmostEqual(m['speed'], m['maxSpeed'], delta=0.02 * m['maxSpeed'])

    def testVehicle3cWorldsVirtualSensors(self):
        '''Temperature, oxygen and organic matter, computed from the Webots
        poses with the Box2D formula, read as in Box2D.'''
        m = self.measure('kheperaBraitenberg3c_HOMEO_World')
        self.assertEqual(len(m['qualities']), 5 * 3 * 2)
        for webots, box2d in m['qualities']:
            self.assertAlmostEqual(webots, box2d, delta=0.005 * abs(box2d) + 1e-6)
        for webots, box2d in m['eyes']:
            self.assertAlmostEqual(webots, box2d, delta=0.005 * box2d + 1e-6)

    def testAPhototaxisRun(self):
        '''The direct experiment runs on Webots, records it, and refuses what
        Webots cannot do (darkness sources, the K-Junior).'''
        with tempfile.TemporaryDirectory() as tmp:
            command = [sys.executable, '-m', 'HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct',
                       '--fixed-weights', '--eye-response', 'log', '--steps', '200', '--seed', '3',
                       '--batch', '1', '--simulator', 'webots']
            r = subprocess.run(command, cwd=SRC, capture_output=True, text=True, timeout=300,
                               env=dict(os.environ, HOMEO_DATA_DIR=tmp))
            self.assertEqual(r.returncode, 0, r.stdout[-2000:] + r.stderr[-2000:])
            data = os.path.join(tmp, os.listdir(tmp)[0])
            files = os.listdir(data)
            [traj] = [f for f in files if f.endswith('.traj')]
            [js] = [f for f in files if f.endswith('.json')]
            [csv] = [f for f in files if f.startswith('batch_')]
            self.assertIn('_webots', traj)
            self.assertIn('_webots', csv)
            with open(os.path.join(data, traj)) as f:
                self.assertIn('# Robot model\tepuck2 (Webots)\n', f.read())
            with open(os.path.join(data, js)) as f:
                self.assertEqual(json.load(f)['settings']['simulator'], 'webots')
            for extra in (['--dark'], ['--robot', 'kjunior']):
                r = subprocess.run(command + extra, cwd=SRC, capture_output=True, text=True,
                                   timeout=300, env=dict(os.environ, HOMEO_DATA_DIR=tmp))
                self.assertNotEqual(r.returncode, 0, extra)


    def testASeedReproducesAWebotsRun(self):
        '''An adaptive run (noise, a random start) repeats exactly from its
        seed: the worlds fix Webots' randomSeed and use one physics thread.'''
        rows = []
        for i in range(2):
            with tempfile.TemporaryDirectory() as tmp:
                command = [sys.executable, '-m', 'HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct',
                           '--steps', '400', '--seed', '5', '--random-start', '--simulator', 'webots']
                r = subprocess.run(command, cwd=SRC, capture_output=True, text=True, timeout=300,
                                   env=dict(os.environ, HOMEO_DATA_DIR=tmp))
                self.assertEqual(r.returncode, 0, r.stdout[-2000:] + r.stderr[-2000:])
                data = os.path.join(tmp, os.listdir(tmp)[0])
                [traj] = [f for f in os.listdir(data) if f.endswith('.traj')]
                with open(os.path.join(data, traj)) as f:
                    rows.append([line for line in f if not line.startswith('#')])
        self.assertGreater(len(rows[0]), 800)
        self.assertEqual(rows[0], rows[1])

    def testABatchsLaterRunsAreFreshRuns(self):
        '''A batch's runs share one Webots, reset between them.  Run 2 moves,
        and is row for row the run its seed gives in a fresh process.  (Until
        15 Oct 2026 the reset undid the motors' velocity control, and every
        run after the first stood still: R2-WEBOTS-1.)'''
        rows = {}
        for name, seed, batch in (('batch', '5', '2'), ('alone', '6', '1')):
            with tempfile.TemporaryDirectory() as tmp:
                command = [sys.executable, '-m', 'HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct',
                           '--steps', '300', '--seed', seed, '--batch', batch, '--simulator', 'webots']
                r = subprocess.run(command, cwd=SRC, capture_output=True, text=True, timeout=300,
                                   env=dict(os.environ, HOMEO_DATA_DIR=tmp))
                self.assertEqual(r.returncode, 0, r.stdout[-2000:] + r.stderr[-2000:])
                data = os.path.join(tmp, os.listdir(tmp)[0])
                trajs = sorted(f for f in os.listdir(data) if f.endswith('.traj'))
                with open(os.path.join(data, trajs[-1])) as f:
                    rows[name] = [line for line in f if not line.startswith('#') and len(line.split()) > 5]
        first, last = rows['batch'][0].split(), rows['batch'][-1].split()
        self.assertGreater(abs(float(last[0]) - float(first[0])) + abs(float(last[1]) - float(first[1])), 0.05)
        self.assertEqual(rows['batch'], rows['alone'])

    def testAPlacedRobotIsWhereItWasPut(self):
        '''set_start_pose takes effect at once, as in Box2D: the pose and the
        eyes are the new ones before any step, and a run records the start it
        had.  (Until 15 Oct 2026 Webots applied the pose only at the next
        step, and runs recorded the world's default, (4, 4) heading 0:
        R2-WEBOTS-2.)'''
        with tempfile.TemporaryDirectory() as tmp:
            script = os.path.join(tmp, 'place.py')
            with open(script, 'w') as f:
                f.write(_PLACE.format(src=SRC, data=tmp))
            r = subprocess.run([sys.executable, script], capture_output=True, text=True,
                               timeout=300, env=dict(os.environ, HOMEO_DATA_DIR=tmp))
        lines = [l for l in r.stdout.splitlines() if l.startswith('PLACED ')]
        self.assertTrue(lines, r.stdout[-2000:] + r.stderr[-2000:])
        for placed in json.loads(lines[0][len('PLACED '):]):
            for got, wanted in zip(placed['webots'], placed['pose']):
                self.assertAlmostEqual(got, wanted, delta=1e-3)
            for webots, box2d in placed['eyes']:
                self.assertAlmostEqual(webots, box2d, delta=0.005 * box2d + 1e-6)
        self.assertTrue(any(box2d > 0 for p in json.loads(lines[0][len('PLACED '):])
                            for _, box2d in p['eyes']))

        # a run's recorded start: the batch CSV, the .traj header, the first row
        with tempfile.TemporaryDirectory() as tmp:
            command = [sys.executable, '-m', 'HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct',
                       '--steps', '100', '--seed', '4', '--random-start', '--batch', '1',
                       '--simulator', 'webots']
            r = subprocess.run(command, cwd=SRC, capture_output=True, text=True, timeout=300,
                               env=dict(os.environ, HOMEO_DATA_DIR=tmp))
            self.assertEqual(r.returncode, 0, r.stdout[-2000:] + r.stderr[-2000:])
            data = os.path.join(tmp, os.listdir(tmp)[0])
            files = os.listdir(data)
            [summary] = [f for f in files if f.startswith('batch_')]
            [traj] = [f for f in files if f.endswith('.traj')]
            with open(os.path.join(data, summary)) as f:
                run = next(csv.DictReader(f))
            with open(os.path.join(data, traj)) as f:
                lines = f.read().splitlines()
        header = lines[lines.index("# Vehicle's initial position at:") + 1].split()
        first = [l for l in lines if not l.startswith('#') and len(l.split()) > 5][0].split()
        start = [float(run[k]) for k in ('start_x', 'start_y', 'start_heading')]
        self.assertNotAlmostEqual(start[0], 4.0, delta=1e-3)    # not the world's default
        for i, delta in enumerate((1e-3, 1e-3, 0.06)):          # the header's heading: 1 decimal
            self.assertAlmostEqual(start[i], float(header[i]), delta=delta)
        for i in range(2):                                      # one step's motion away
            self.assertAlmostEqual(start[i], float(first[i]), delta=0.01)


if __name__ == '__main__':
    unittest.main()
