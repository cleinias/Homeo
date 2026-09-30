'''
Hunger-driven chemotaxis experiment.

Adds an internal battery to a Braitenberg Vehicle 2 (direct, 2+2 topology).
The battery depletes at a constant rate and recharges when the robot is near
the light source.  A battery sensor unit feeds the battery level into the
homeostat as a standard HomeoUnitInput.

This script runs the experiment with hand-picked body parameters (no GA)
to verify that the battery mechanism works correctly: the battery should
deplete when far from the light and recharge when near it.

Usage
-----
    # Headless (default 60k steps)
    python -m HomeoExperiments.KheperaExperiments.hunger_chemotaxis

    # With visualizer
    python -m HomeoExperiments.KheperaExperiments.hunger_chemotaxis --visualize

    # Custom steps and seed
    python -m HomeoExperiments.KheperaExperiments.hunger_chemotaxis --steps 100000 --seed 42

@author: stefano
'''

import os
import time
import threading
from math import sqrt, degrees

import numpy as np


# Source positions for Braiten2 world
SOURCE_POSITIONS = {
    'TARGET': (7, 7),
}


def setup_hunger_phototaxis(seed=None, capacity=1.0, discharge_rate=0.001,
                            recharge_factor=0.01):
    '''Set up a Braiten2-direct vehicle with a battery sensor.

    Uses hand-picked body parameters (no GA) and OU continuous uniselectors.
    The homeostat has 5 units: 2 motors + 2 light sensors + 1 battery sensor.

    Parameters
    ----------
    seed : int or None
        RNG seed for reproducibility.
    capacity, discharge_rate, recharge_factor : float
        Battery model parameters.

    Returns
    -------
    (hom, backend, seed) : tuple
    '''
    from Simulator.SimulatorBackend import SimulatorBackendHOMEO
    from Simulator.HomeoExperiments import (
        _setup_continuous_weightfree_homeostat_direct,
        add_battery_to_homeostat)
    from Helpers.General_Helper_Functions import simulations_data_dir

    if seed is None:
        seed = int.from_bytes(os.urandom(4), 'big')
    np.random.seed(seed)

    lock = threading.Lock()
    backend = SimulatorBackendHOMEO(lock=lock, robotName='Khepera')

    # Set up logging directory
    sims_root = simulations_data_dir()
    log_dir = os.path.join(sims_root, 'SimsData-' + time.strftime("%Y-%m-%d"))
    os.makedirs(log_dir, exist_ok=True)
    backend.kheperaSimulation.dataDir = log_dir
    backend.kheperaSimulation.experimentName = 'hunger_phototaxis'

    # Hand-picked genome: moderate mass, viscosity, tau_a, maxDeviation, dt_fast
    genome = [0.3, 0.5, 0.5, 0.5, 0.5,   # left motor
              0.3, 0.5, 0.5, 0.5, 0.5]    # right motor

    hom = _setup_continuous_weightfree_homeostat_direct(
        genome, backend, dataDir=log_dir,
        noNoise=False, topology='fixed')

    add_battery_to_homeostat(hom, backend, recharge_quality='light',
                            capacity=capacity, discharge_rate=discharge_rate,
                            recharge_factor=recharge_factor, invert=True,
                            wire_stress=True)

    return hom, backend, seed


def run_headless(total_steps=60000, report_interval=500, seed=None,
                 state_log=False, state_log_interval=1,
                 capacity=1.0, discharge_rate=0.001, recharge_factor=0.01):
    '''Run the hunger-driven vehicle headless and print position + battery level.

    Parameters
    ----------
    total_steps : int
        Number of simulation steps to run.
    report_interval : int
        Print robot state every this many steps.
    seed : int or None
        RNG seed for reproducibility.
    state_log : bool
        If True, write per-tick .statelog file.
    state_log_interval : int
        Log every N-th tick (default 1).
    capacity, discharge_rate, recharge_factor : float
        Battery model parameters.

    Returns
    -------
    dict with keys: hom, backend, seed, steps_run, final_x, final_y,
                    distances, battery_level, battery_avg,
                    log_path, json_path, state_log_path
    '''
    from Helpers.HomeostatConditionLogger import (
        log_homeostat_conditions, log_homeostat_conditions_json)

    hom, backend, seed = setup_hunger_phototaxis(
        seed=seed, capacity=capacity, discharge_rate=discharge_rate,
        recharge_factor=recharge_factor)

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
        state_logger.log_tick(0)
        hom._state_logger = state_logger

    def dist_to(pos):
        rx, ry = robot.body.position[0], robot.body.position[1]
        return sqrt((rx - pos[0])**2 + (ry - pos[1])**2)

    print(f'=== Hunger-Driven Phototaxis (Braiten2-direct + battery) ===')
    print(f'Robot start: ({robot.body.position[0]:.3f}, {robot.body.position[1]:.3f})')
    print(f'Battery: capacity={capacity}, discharge={discharge_rate}, recharge={recharge_factor}')
    print(f'Sources:')
    for name, pos in SOURCE_POSITIONS.items():
        print(f'  {name:8s} at {pos}  dist={dist_to(pos):.3f}')
    print(f'Seed: {seed}')
    print()

    header = f'{"Step":>6}  {"Robot X":>8}  {"Robot Y":>8}  {"Angle":>7}  {"Dist":>8}  {"Battery":>8}  {"BatAvg":>8}'
    print(header)
    print('-' * len(header))

    for target_tick in range(report_interval, total_steps + 1, report_interval):
        hom.runFor(target_tick)
        rx, ry = robot.body.position[0], robot.body.position[1]
        a = degrees(robot.body.angle) % 360
        d = dist_to(SOURCE_POSITIONS['TARGET'])
        bat = robot.battery.level
        bat_avg = robot.battery.average_level()

        line = f'{target_tick:>6}  {rx:>8.3f}  {ry:>8.3f}  {a:>7.1f}  {d:>8.3f}  {bat:>8.4f}  {bat_avg:>8.4f}'
        print(line)

    # Final state
    distances = {name: dist_to(pos) for name, pos in SOURCE_POSITIONS.items()}
    final_x, final_y = robot.body.position[0], robot.body.position[1]
    battery_level = robot.battery.level
    battery_avg = robot.battery.average_level()

    print()
    print(f'Final distance to TARGET: {distances["TARGET"]:.3f}')
    print(f'Final battery level: {battery_level:.4f}')
    print(f'Average battery level: {battery_avg:.4f}')

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
                distances=distances, battery_level=battery_level,
                battery_avg=battery_avg,
                log_path=log_path, json_path=json_path,
                state_log_path=state_log_path)


def run_visualized(seed=None, capacity=1.0, discharge_rate=0.001,
                   recharge_factor=0.01):
    '''Run the hunger-driven vehicle with the pyglet visualizer.

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
                                  caption='Hunger Phototaxis')

    glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glClearColor(0.55, 0.95, 1.0, 1.0)

    hom, backend, seed = setup_hunger_phototaxis(
        seed=seed, capacity=capacity, discharge_rate=discharge_rate,
        recharge_factor=recharge_factor)
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

        d = dist_to(SOURCE_POSITIONS['TARGET'])
        bat = robot.battery.level
        bat_avg = robot.battery.average_level()
        fps = 1 / max(dt, 0.001)
        window.set_caption(
            f'Hunger Phototaxis - t={state[0]}  speed={state[1]}  '
            f'dist={d:.2f}  bat={bat:.3f}  avg={bat_avg:.3f}  [{fps:.0f} fps]')

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
