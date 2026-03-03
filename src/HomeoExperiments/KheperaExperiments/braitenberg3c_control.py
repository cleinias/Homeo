'''
Hand-wired control experiment for Braitenberg Vehicle 3c.

This replicates Braitenberg's description of Vehicle 3c's "system of
values" (Vehicles, p.12) with fixed connection weights and no online
learning.  The wiring implements four different sensor-motor relationships:

  Light       — crossed excitatory   (Vehicle 2b: aggression, charges at light)
  Temperature — uncrossed excitatory (Vehicle 2a: fear, turns away from heat)
  Oxygen      — crossed inhibitory   (Vehicle 3b: explorer, slows near O2)
  Organic     — uncrossed inhibitory (Vehicle 3a: love, stops near food)

The homeostat has 10 units: 2 motors + 8 sensor inputs, with all
connection weights set to fixed values (no uniselectors, no OU process).
This serves as a baseline for comparison with the self-organizing GA+OU
experiments.

Usage
-----
    # Headless (default 60k steps)
    python -m HomeoExperiments.KheperaExperiments.braitenberg3c_control

    # With visualizer
    python -m HomeoExperiments.KheperaExperiments.braitenberg3c_control --visualize

    # Custom steps and seed
    python -m HomeoExperiments.KheperaExperiments.braitenberg3c_control --steps 100000 --seed 42

@author: stefano
'''

import os
import time
import threading
from math import sqrt, degrees

import numpy as np


# Default connection weights for each quality
DEFAULT_WEIGHTS = {
    'light':   0.8,   # strongest excitatory — "even greater passion"
    'temp':    0.4,   # moderate excitatory
    'oxy':     0.6,   # strong inhibitory
    'org':     0.4,   # moderate inhibitory
}

# Source positions from kheperaBraitenberg3c_HOMEO_World
SOURCE_POSITIONS = {
    'LIGHT1': (7, 7),
    'TEMP1':  (7, 7),
    'TEMP2':  (1, 7),
    'OXY1':   (2, 2),
    'ORG1':   (6, 1),
}


def setup_braiten3c_control(seed=None, weights=None):
    '''Set up a hand-wired Braitenberg Vehicle 3c control experiment.

    Creates a 10-unit homeostat with fixed connection weights and no
    online learning (all uniselectors disabled, all connections manual).

    Parameters
    ----------
    seed : int or None
        RNG seed for reproducibility.  If None, a random seed is generated.
    weights : dict or None
        Override default weights.  Keys: 'light', 'temp', 'oxy', 'org'.
        Values are absolute weight magnitudes; signs are applied per the
        Braitenberg wiring table.

    Returns
    -------
    (hom, backend, seed) : tuple
        The configured Homeostat, the backend simulator, and the seed used.
    '''
    from Simulator.SimulatorBackend import SimulatorBackendHOMEO
    from Simulator.HomeoExperiments import braiten3cTransducers
    from Core.Homeostat import Homeostat
    from Core.HomeoUnit import HomeoUnit
    from Core.HomeoUnitNewtonian import HomeoUnitNewtonian
    from RobotSimulator.HomeoUnitNewtonianTransduc import (
        HomeoUnitNewtonianActuator, HomeoUnitInput)
    from Helpers.General_Helper_Functions import simulations_data_dir

    if seed is None:
        seed = int.from_bytes(os.urandom(4), 'big')
    np.random.seed(seed)

    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update(weights)

    lock = threading.Lock()
    backend = SimulatorBackendHOMEO(lock=lock, robotName='Khepera')

    # Set up logging directory
    sims_root = simulations_data_dir()
    log_dir = os.path.join(sims_root, 'SimsData-' + time.strftime("%Y-%m-%d"))
    os.makedirs(log_dir, exist_ok=True)
    backend.kheperaSimulation.dataDir = log_dir
    backend.kheperaSimulation.experimentName = 'braitenberg3c_control'

    world = 'kheperaBraitenberg3c_HOMEO_World'
    transducers = braiten3cTransducers(backend, world)

    # 1. Create homeostat and units
    hom = Homeostat()
    hom._host = backend.host
    hom._port = backend.port
    HomeoUnit.clearNames()

    leftMotor = HomeoUnitNewtonianActuator(transducer=transducers["leftWheelTransd"])
    rightMotor = HomeoUnitNewtonianActuator(transducer=transducers["rightWheelTransd"])

    leftLight  = HomeoUnitInput(transducer=transducers["leftLightTransd"])
    rightLight = HomeoUnitInput(transducer=transducers["rightLightTransd"])
    leftTemp   = HomeoUnitInput(transducer=transducers["leftTempTransd"])
    rightTemp  = HomeoUnitInput(transducer=transducers["rightTempTransd"])
    leftOxy    = HomeoUnitInput(transducer=transducers["leftOxyTransd"])
    rightOxy   = HomeoUnitInput(transducer=transducers["rightOxyTransd"])
    leftOrg    = HomeoUnitInput(transducer=transducers["leftOrgTransd"])
    rightOrg   = HomeoUnitInput(transducer=transducers["rightOrgTransd"])

    # 2. Build fully-connected homeostat
    all_units = [leftMotor, rightMotor,
                 leftLight, rightLight, leftTemp, rightTemp,
                 leftOxy, rightOxy, leftOrg, rightOrg]
    for unit in all_units:
        hom.addFullyConnectedUnit(unit)

    # 3. Name and configure units
    leftMotor.name = 'Left Motor'
    leftMotor.mass = 5
    leftMotor.noise = 0.05
    leftMotor._maxSpeedFraction = 0.8
    leftMotor._switchingRate = 0.5
    leftMotor._maxSpeed = None

    rightMotor.name = 'Right Motor'
    rightMotor.mass = 5
    rightMotor.noise = 0.05
    rightMotor._maxSpeedFraction = 0.8
    rightMotor._switchingRate = 0.5
    rightMotor._maxSpeed = None

    sensor_names = {
        leftLight: 'Left Light', rightLight: 'Right Light',
        leftTemp: 'Left Temp',   rightTemp: 'Right Temp',
        leftOxy: 'Left Oxy',     rightOxy: 'Right Oxy',
        leftOrg: 'Left Org',     rightOrg: 'Right Org',
    }
    for unit, name in sensor_names.items():
        unit.name = name
        unit.noise = 0.05

    # 4. Disable sensor-only units (pure input transducers)
    sensor_units = [leftLight, rightLight, leftTemp, rightTemp,
                    leftOxy, rightOxy, leftOrg, rightOrg]
    for su in sensor_units:
        su.uniselectorActive = False
        for conn in su.inputConnections:
            conn.status = False

    # 5. Configure motor connections — all manual, uniselectors disabled
    motors = [leftMotor, rightMotor]
    for motor in motors:
        motor.uniselectorActive = False

        # Self-connection: small negative (stability)
        motor.inputConnections[0].newWeight(-0.05)
        motor.inputConnections[0].noise = 0.05
        motor.inputConnections[0].state = 'manual'
        motor.inputConnections[0].status = True

        # Disable all other connections first
        for conn in motor.inputConnections[1:]:
            conn.status = False

    # Disable motor-to-motor cross-connections (already disabled above, but be explicit)
    for conn in leftMotor.inputConnections:
        if conn.incomingUnit is rightMotor:
            conn.status = False
    for conn in rightMotor.inputConnections:
        if conn.incomingUnit is leftMotor:
            conn.status = False

    # 6. Wire per Braitenberg's Vehicle 3c (Vehicles p.12):
    #   Light:       crossed excitatory   (2b: aggression)
    #   Temperature: uncrossed excitatory  (2a: fear)
    #   Oxygen:      crossed inhibitory    (3b: explorer)
    #   Organic:     uncrossed inhibitory   (3a: love)
    fixed_wiring = {
        leftMotor: [
            ('Right Light', +w['light']),
            ('Left Temp',   +w['temp']),
            ('Right Oxy',   -w['oxy']),
            ('Left Org',    -w['org']),
        ],
        rightMotor: [
            ('Left Light',  +w['light']),
            ('Right Temp',  +w['temp']),
            ('Left Oxy',    -w['oxy']),
            ('Right Org',   -w['org']),
        ],
    }
    for motor, wiring_list in fixed_wiring.items():
        for source_name, signed_weight in wiring_list:
            for conn in motor.inputConnections:
                if conn.incomingUnit.name == source_name:
                    conn.newWeight(signed_weight)
                    conn.noise = 0.05
                    conn.state = 'manual'
                    conn.status = True

    return hom, backend, seed


def run_headless(total_steps=60000, report_interval=500, seed=None,
                 weights=None, state_log=False, state_log_interval=1):
    '''Run the control vehicle headless and print position + distances.

    Parameters
    ----------
    total_steps : int
        Number of simulation steps to run.
    report_interval : int
        Print robot state every this many steps.
    seed : int or None
        RNG seed for reproducibility.
    weights : dict or None
        Override default connection weights.
    state_log : bool
        If True, write per-tick .statelog file via HomeostatStateLogger.
    state_log_interval : int
        Log every N-th tick (default 1).

    Returns
    -------
    dict with keys: hom, backend, seed, steps_run, final_x, final_y,
                    distances (dict of source name -> final distance),
                    log_path, json_path, state_log_path
    '''
    from Helpers.HomeostatConditionLogger import (
        log_homeostat_conditions, log_homeostat_conditions_json)

    hom, backend, seed = setup_braiten3c_control(seed=seed, weights=weights)

    hom.slowingFactor = 0
    hom.collectsData = False
    hom._headless = True
    for u in hom.homeoUnits:
        u._headless = True

    sim = backend.kheperaSimulation
    robot = sim.allBodies['Khepera']
    exp_name = sim.experimentName

    # Log initial conditions
    timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")
    log_dir = sim.dataDir
    log_path = os.path.join(log_dir, exp_name + '-' + timestamp + '.log')
    json_path = os.path.join(log_dir, exp_name + '-' + timestamp + '.json')
    log_homeostat_conditions(hom, log_path, 'INITIAL CONDITIONS', exp_name)
    log_homeostat_conditions_json(hom, json_path, 'INITIAL CONDITIONS', exp_name,
                                  seed=seed)

    # Optional per-tick state logger
    state_log_path = None
    if state_log:
        from Helpers.HomeostatStateLogger import HomeostatStateLogger
        state_log_path = os.path.join(log_dir, exp_name + '-' + timestamp + '.statelog')
        state_logger = HomeostatStateLogger(
            hom, sim, state_log_path, log_interval=state_log_interval, seed=seed)
        state_logger.log_tick(0)  # capture initial state before any dynamics
        hom._state_logger = state_logger

    def dist_to(pos):
        rx, ry = robot.body.position[0], robot.body.position[1]
        return sqrt((rx - pos[0])**2 + (ry - pos[1])**2)

    print(f'=== Braitenberg Vehicle 3c — Control (hand-wired) ===')
    print(f'Robot start: ({robot.body.position[0]:.3f}, {robot.body.position[1]:.3f})')
    print(f'Sources:')
    for name, pos in SOURCE_POSITIONS.items():
        print(f'  {name:8s} at {pos}  dist={dist_to(pos):.3f}')
    print(f'Seed: {seed}')
    print()

    header = f'{"Step":>6}  {"Robot X":>8}  {"Robot Y":>8}  {"Angle":>7}'
    for name in SOURCE_POSITIONS:
        header += f'  {name:>8}'
    print(header)
    print('-' * len(header))

    for target_tick in range(report_interval, total_steps + 1, report_interval):
        hom.runFor(target_tick)
        rx, ry = robot.body.position[0], robot.body.position[1]
        a = degrees(robot.body.angle) % 360

        line = f'{target_tick:>6}  {rx:>8.3f}  {ry:>8.3f}  {a:>7.1f}'
        for pos in SOURCE_POSITIONS.values():
            line += f'  {dist_to(pos):>8.3f}'
        print(line)

    # Final distances
    distances = {name: dist_to(pos) for name, pos in SOURCE_POSITIONS.items()}
    final_x, final_y = robot.body.position[0], robot.body.position[1]

    print()
    print('Final distances:')
    for name, d in distances.items():
        print(f'  {name:8s}: {d:.3f}')

    sim.saveTrajectory()

    # Close state logger if active
    if state_log and hom._state_logger is not None:
        hom._state_logger.close()
        hom._state_logger = None

    # Log final conditions
    log_homeostat_conditions(hom, log_path, 'FINAL CONDITIONS')
    log_homeostat_conditions_json(hom, json_path, 'FINAL CONDITIONS')

    return dict(hom=hom, backend=backend, seed=seed,
                steps_run=target_tick, final_x=final_x, final_y=final_y,
                distances=distances, log_path=log_path, json_path=json_path,
                state_log_path=state_log_path)


def run_visualized(seed=None, weights=None):
    '''Run the control vehicle with the pyglet visualizer.

    Press Q or Escape to close the window.
    Up/Down arrows adjust simulation speed (steps per frame).
    '''
    import pyglet
    from pyglet.gl import (glEnable, glBlendFunc, glHint, glClearColor, glClear,
                           GL_BLEND, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
                           GL_LINE_SMOOTH, GL_LINE_SMOOTH_HINT, GL_NICEST,
                           GL_COLOR_BUFFER_BIT)
    from KheperaSimulator.KheperaSimulator import KheperaCamera
    from Helpers.HomeostatConditionLogger import (
        log_homeostat_conditions, log_homeostat_conditions_json)

    window = pyglet.window.Window(width=800, height=600, resizable=True,
                                  caption='Braitenberg 3c — Control')

    glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glClearColor(0.55, 0.95, 1.0, 1.0)

    hom, backend, seed = setup_braiten3c_control(seed=seed, weights=weights)
    sim = backend.kheperaSimulation
    robot = sim.allBodies['Khepera']
    exp_name = sim.experimentName

    # Log initial conditions
    timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")
    log_dir = sim.dataDir
    log_path = os.path.join(log_dir, exp_name + '-' + timestamp + '.log')
    json_path = os.path.join(log_dir, exp_name + '-' + timestamp + '.json')
    log_homeostat_conditions(hom, log_path, 'INITIAL CONDITIONS', exp_name)
    log_homeostat_conditions_json(hom, json_path, 'INITIAL CONDITIONS', exp_name,
                                  seed=seed)

    from KheperaSimulator.KheperaSimulator import _get_shape_program
    from pyglet.gl import GL_LINES

    camera = KheperaCamera(position=(5.5, 5.5), zoom=8.0)
    state = [0, 5]   # [tick_count, steps_per_frame]
    trail_vlists = []
    trail_last = [None]
    TRAIL_MIN_DIST = 0.05

    def dist_to(pos):
        rx, ry = robot.body.position[0], robot.body.position[1]
        return sqrt((rx - pos[0])**2 + (ry - pos[1])**2)

    @window.event
    def on_draw():
        glClear(GL_COLOR_BUFFER_BIT)
        camera.focus(window)
        sim.pygletDraw()
        program = _get_shape_program()
        program.use()
        for vl in trail_vlists:
            vl.draw(GL_LINES)
        program.stop()

    def update(dt):
        state[0] += state[1]
        hom.runFor(state[0])
        rx, ry = robot.body.position[0], robot.body.position[1]

        if trail_last[0] is not None:
            px, py = trail_last[0]
            if sqrt((rx - px)**2 + (ry - py)**2) >= TRAIL_MIN_DIST:
                program = _get_shape_program()
                vl = program.vertex_list(
                    2, GL_LINES,
                    position=('f', [px, py, rx, ry]),
                    colors=('f', [0.8, 0.2, 0.2, 0.7] * 2),
                    translation=('f', [0.0, 0.0] * 2),
                    rotation=('f', [0.0] * 2),
                    zposition=('f', [0.0] * 2),
                )
                trail_vlists.append(vl)
                trail_last[0] = (rx, ry)
        else:
            trail_last[0] = (rx, ry)

        # Build caption with distances to each source type
        parts = [f't={state[0]}  speed={state[1]}']
        for name, pos in SOURCE_POSITIONS.items():
            parts.append(f'{name}={dist_to(pos):.2f}')
        fps = 1 / max(dt, 0.001)
        parts.append(f'[{fps:.0f} fps]')
        window.set_caption('Braiten 3c Control - ' + '  '.join(parts))

    @window.event
    def on_key_press(symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE or symbol == pyglet.window.key.Q:
            window.close()
        elif symbol == pyglet.window.key.UP:
            state[1] = min(state[1] * 2, 200)
        elif symbol == pyglet.window.key.DOWN:
            state[1] = max(state[1] // 2, 1)

    @window.event
    def on_close():
        sim.saveTrajectory()
        log_homeostat_conditions(hom, log_path, 'FINAL CONDITIONS')
        log_homeostat_conditions_json(hom, json_path, 'FINAL CONDITIONS')

    pyglet.clock.schedule(update)
    pyglet.app.run()


if __name__ == '__main__':
    import sys

    # Parse --steps N (default 60000)
    total_steps = 60000
    if '--steps' in sys.argv:
        idx = sys.argv.index('--steps')
        if idx + 1 < len(sys.argv):
            total_steps = int(sys.argv[idx + 1])

    # Parse --seed N
    seed = None
    if '--seed' in sys.argv:
        idx = sys.argv.index('--seed')
        if idx + 1 < len(sys.argv):
            seed = int(sys.argv[idx + 1])

    # Parse --state-log and --state-log-interval N
    state_log = '--state-log' in sys.argv
    state_log_interval = 1
    if '--state-log-interval' in sys.argv:
        idx = sys.argv.index('--state-log-interval')
        if idx + 1 < len(sys.argv):
            state_log_interval = int(sys.argv[idx + 1])

    if '--visualize' in sys.argv:
        run_visualized(seed=seed)
    else:
        run_headless(total_steps=total_steps, seed=seed,
                     state_log=state_log, state_log_interval=state_log_interval)
