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

'''
The Webots backend: Homeo runs Webots as its e-puck2's extern controller.
Each test runs its Webots in a subprocess -- one process can control one
Webots robot -- and compares it with the Box2D twin: the same eyes' irradiance, the same capped wheel speed,
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

# Two setups in one process, the first with its light at 50: what the second
# finds, in Webots (an eye) and in the light's records, and what Box2D's eye
# reads at 100
_RELIGHT = r'''
import json, sys
sys.path.insert(0, {src!r})
from KheperaSimulator.KheperaSimulator import KheperaSimulation
from WebotsSimulator.WebotsSimulation import WebotsSimulation

world = 'kheperaBraitenberg2_HOMEO_World'
webots = WebotsSimulation.shared()
webots.setupWorld(world, {data!r})
webots.allBodies['TARGET'].userData['intensity'] = 50
webots.tickAdvance()
webots.setupWorld(world, {data!r})
light, robot = webots.allBodies['TARGET'], webots.allBodies['Khepera']
box2d = KheperaSimulation()
box2d.setupWorld(world, {data!r})
br = box2d.allBodies['Khepera']
out = dict(field=light._node.getField('intensity').getSFFloat(),
           userData=light.userData['intensity'], eye=robot.lightIrradiance('leftEye'),
           box2dEye=br.irradAtSensor('leftEye', br.detectableLights))
webots.saveTrajectory()
box2d.saveTrajectory()
print('RELIT ' + json.dumps(out))
'''

# A decimated run of 5 ticks (10 steps) ended by a new setup, not a save:
# its file's last lines, and the robot's pose after its last step
_RESETUP = r'''
import glob, json, os, sys
sys.path.insert(0, {src!r})
from Helpers.RobotTrajectoryWriter import configureTrajectoryDefaults
from WebotsSimulator.WebotsSimulation import WebotsSimulation

configureTrajectoryDefaults(interval=3)
world = 'kheperaBraitenberg2_HOMEO_World'
webots = WebotsSimulation.shared()
webots.setupWorld(world, {data!r})
robot = webots.allBodies['Khepera']
robot.setSpeed(2.0, 1.0)
for i in range(5):
    webots.tickAdvance()
p = robot.body.position
final = '%f\t%f' % (p[0], p[1])
first = webots.trajectoryWriter.posFile.name
webots.setupWorld(world, {data!r})
webots.saveTrajectory()
with open(first) as f:
    last = f.read().splitlines()[-2:]
print('RESETUP ' + json.dumps(dict(final=final, last=last)))
'''

# A GA evaluation's step: the backend starts the genome's own .traj
# (setRobotModel); the files it leaves
_MODEL = r'''
import json, os, sys
sys.path.insert(0, {src!r})
from Simulator.SimulatorBackend import SimulatorBackendWEBOTS

backend = SimulatorBackendWEBOTS(dataDir={data!r})
backend.start('kheperaBraitenberg2_HOMEO_World')
sim = backend.kheperaSimulation
backend.setRobotModel('001-002')
for i in range(3):
    sim.tickAdvance()
sim.saveTrajectory()
files = {{}}
for f in sorted(os.listdir({data!r})):
    if f.endswith('.traj'):
        with open(os.path.join({data!r}, f)) as g:
            files[f] = g.read().splitlines()
print('MODEL ' + json.dumps(files))
'''

# A battery on the Webots robot: one tick 1 from the light, then an empty
# battery that paralyses the wheels for 20 ticks
_BATTERY = r'''
import json, sys
sys.path.insert(0, {src!r})
from KheperaSimulator.Battery import Battery
from WebotsSimulator.WebotsSimulation import WebotsSimulation
from HomeoExperiments.KheperaExperiments.phototaxis_common import set_start_pose

webots = WebotsSimulation.shared()
webots.setupWorld('kheperaBraitenberg2_HOMEO_World', {data!r})
robot = webots.allBodies['Khepera']
set_start_pose(robot, 6, 7, 0)
robot.battery = Battery(discharge_rate=0.01, recharge_factor=0.001, depletion='paralysis')
robot.battery.level = 0.5
webots.tickAdvance()
fed = robot.battery.level
robot.battery.level = 0.0
robot.battery.recharge_factor = 0.0
start = robot.body.position
robot.setSpeed(2.0, 2.0)
for i in range(20):
    webots.tickAdvance()
moved = (robot.body.position - start).length
webots.saveTrajectory()
print('BATTERY ' + json.dumps(dict(fed=fed, ticks=robot.battery.ticks, speed=robot.getSpeed(),
                                   moved=moved, halted=webots.halted)))
'''

# The chemotaxis world's field snapshot in Webots, against the law at the grid
# points (from the food's position as the Supervisor reports it) and against
# Box2D's; and the snapshots a few steps' .traj records
_FIELD = r'''
import json, math, os, sys
sys.path.insert(0, {src!r})
from KheperaSimulator.KheperaSimulator import KheperaSimulation, _fieldShape
from WebotsSimulator.WebotsSimulation import WebotsSimulation
from Helpers.TrajectoryGrapher import readFieldSnapshots

world = 'kheperaChemotaxis_HOMEO_World'
webots = WebotsSimulation.shared()
webots.setupWorld(world, {data!r})
box2d = KheperaSimulation()
box2d.setupWorld(world, {data!r})
food = webots.allBodies['FOOD'].userData
fx, _, fy = food['lightPos']
[(quality, (x0, y0, spacing, n, values))] = webots.fieldSnapshot().items()
law = max(abs(values[j][i] - food['intensity'] * _fieldShape(
              food['law'], math.hypot(x0 + i * spacing - fx, y0 + j * spacing - fy)))
          for j in range(n) for i in range(n))
twin = box2d.fieldSnapshot()['organic']
for i in range(10):
    webots.advanceSim()
path = webots.trajectoryWriter.posFile.name
webots.saveTrajectory()
box2d.saveTrajectory()
read = readFieldSnapshots(path)
print('FIELD ' + json.dumps(dict(
    quality=quality, n=n, law=law, grid=(x0, y0, spacing), twin=twin[:3],
    twinValues=max(abs(a - b) for ra, rb in zip(values, twin[4]) for a, b in zip(ra, rb)),
    moments=sorted(read),
    readBack=max(abs(read['end']['organic']['values'][j][i] - values[j][i]) / max(values[j][i], 1e-300)
                 for j in range(n) for i in range(n)))))
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

    def testTheChemotaxisWorldsChemicalEyes(self):
        '''The chemotaxis world's chemical eyes, computed from the Webots
        poses with the Box2D field, read as in Box2D; no light.'''
        m = self.measure('kheperaChemotaxis_HOMEO_World')
        self.assertEqual(len(m['qualities']), 5 * 2)
        for webots, box2d in m['qualities']:
            self.assertAlmostEqual(webots, box2d, delta=1e-4)
        self.assertTrue(all(box2d > 0 for _, box2d in m['qualities']))
        self.assertTrue(all(webots == 0 for webots, _ in m['eyes']))

    def testTheChemotaxisWorldsFieldSnapshot(self):
        '''Webots records the field as Box2D does: the law's values on the same
        grid (to the Supervisor's float positions), at the start and the end.'''
        with tempfile.TemporaryDirectory() as tmp:
            script = os.path.join(tmp, 'field.py')
            with open(script, 'w') as f:
                f.write(_FIELD.format(src=SRC, data=tmp))
            r = subprocess.run([sys.executable, script], capture_output=True, text=True,
                               timeout=300, env=dict(os.environ, HOMEO_DATA_DIR=tmp))
        lines = [l for l in r.stdout.splitlines() if l.startswith('FIELD ')]
        self.assertTrue(lines, r.stdout[-2000:] + r.stderr[-2000:])
        m = json.loads(lines[0][len('FIELD '):])
        self.assertEqual((m['quality'], m['n']), ('organic', 101))
        self.assertEqual(m['law'], 0)
        for webots, box2d in zip(m['grid'], m['twin']):
            self.assertAlmostEqual(webots, box2d, delta=1e-5)
        self.assertLess(m['twinValues'], 1e-3)
        self.assertEqual(m['moments'], ['end', 'start'])
        self.assertLess(m['readBack'], 5e-6)

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
        '''A batch's runs share one Webots, reset between them.  Run 2 moves
        (the reset keeps the motors' velocity control), and is row for row the
        run its seed gives in a fresh process.'''
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
        had, not the world's default, (4, 4) heading 0.'''
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

    def testAResetWorldHasItsOwnLight(self):
        '''A reset puts the lights back as the world file has them: a run
        after one that set the light to 50 has it at 100, in Webots and in
        its records.'''
        with tempfile.TemporaryDirectory() as tmp:
            script = os.path.join(tmp, 'relight.py')
            with open(script, 'w') as f:
                f.write(_RELIGHT.format(src=SRC, data=tmp))
            r = subprocess.run([sys.executable, script], capture_output=True, text=True,
                               timeout=300, env=dict(os.environ, HOMEO_DATA_DIR=tmp))
        lines = [l for l in r.stdout.splitlines() if l.startswith('RELIT ')]
        self.assertTrue(lines, r.stdout[-2000:] + r.stderr[-2000:])
        out = json.loads(lines[0][len('RELIT '):])
        self.assertEqual(out['field'], 100)
        self.assertEqual(out['userData'], 100)
        self.assertGreater(out['box2dEye'], 0)
        self.assertAlmostEqual(out['eye'], out['box2dEye'], delta=0.005 * out['box2dEye'])

    def testANewSetupClosesTheRunsFile(self):
        '''A run ended by a new setup, not a save, still gets a complete
        .traj: its true final row (held back by decimation) and the closing
        "# Steps recorded" line.'''
        with tempfile.TemporaryDirectory() as tmp:
            script = os.path.join(tmp, 'resetup.py')
            with open(script, 'w') as f:
                f.write(_RESETUP.format(src=SRC, data=tmp))
            r = subprocess.run([sys.executable, script], capture_output=True, text=True,
                               timeout=300, env=dict(os.environ, HOMEO_DATA_DIR=tmp))
        lines = [l for l in r.stdout.splitlines() if l.startswith('RESETUP ')]
        self.assertTrue(lines, r.stdout[-2000:] + r.stderr[-2000:])
        out = json.loads(lines[0][len('RESETUP '):])
        self.assertEqual(out['last'][1], '# Steps recorded\t10')
        self.assertTrue(out['last'][0].startswith(out['final']), out)

    def testAGenomesOwnTrajectoryFile(self):
        '''setRobotModel, as a GA evaluation or a replay calls it, starts a
        .traj named after the genome, complete.'''
        with tempfile.TemporaryDirectory() as tmp:
            script = os.path.join(tmp, 'model.py')
            with open(script, 'w') as f:
                f.write(_MODEL.format(src=SRC, data=tmp))
            r = subprocess.run([sys.executable, script], capture_output=True, text=True,
                               timeout=300, env=dict(os.environ, HOMEO_DATA_DIR=tmp))
        lines = [l for l in r.stdout.splitlines() if l.startswith('MODEL ')]
        self.assertTrue(lines, r.stdout[-2000:] + r.stderr[-2000:])
        files = json.loads(lines[0][len('MODEL '):])
        [genome] = [lines for name, lines in files.items() if '001-002' in name]
        self.assertIn("# Vehicle's initial position at:", genome)
        self.assertEqual(sum(1 for l in genome if l and not l.startswith('#')
                             and len(l.split()) > 5), 6)
        self.assertEqual(genome[-1], '# Steps recorded\t6')

    def testTheBatteryInWebots(self):
        '''The Webots world ticks the robot's battery once per tick, feeding
        it as in Box2D (1 from a light of 100: food 100), and an empty
        battery with depletion 'paralysis' stops the wheels.'''
        with tempfile.TemporaryDirectory() as tmp:
            script = os.path.join(tmp, 'battery.py')
            with open(script, 'w') as f:
                f.write(_BATTERY.format(src=SRC, data=tmp))
            r = subprocess.run([sys.executable, script], capture_output=True, text=True,
                               timeout=300, env=dict(os.environ, HOMEO_DATA_DIR=tmp))
        lines = [l for l in r.stdout.splitlines() if l.startswith('BATTERY ')]
        self.assertTrue(lines, r.stdout[-2000:] + r.stderr[-2000:])
        out = json.loads(lines[0][len('BATTERY '):])
        self.assertAlmostEqual(out['fed'], 0.59, places=4)
        self.assertEqual(out['ticks'], 21)
        self.assertEqual(out['speed'], {'right': 0.0, 'left': 0.0})
        self.assertLess(out['moved'], 1e-4)
        self.assertFalse(out['halted'])


if __name__ == '__main__':
    unittest.main()
