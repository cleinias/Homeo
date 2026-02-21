'''
Phototaxis experiment using a Braitenberg type-2 vehicle
with the internal HOMEO Khepera simulator backend.

The experiment sets up a 6-unit homeostat controlling a Khepera robot
with cross-wired connections (right motor <- left eye, left motor <- right eye).
The robot starts at (4,4) and a light source is placed at (7,7).

The default homeostat parameters from initializeBraiten2_2 (mass=100,
viscosity=0.9*max) are tuned by the GA for long-term adaptation.
For responsive phototaxis, this experiment overrides them with lighter
dynamics and strong self-damping so the robot actively steers toward light.

Tuning rationale:
- mass=1, viscosity=0: fast signal propagation (no inertia or drag)
- self-connection weight=-0.9 on eyes and motors: deviation decays when
  input drops (without this, deviations stay at maxDeviation forever
  because the linear needle model has no natural damping)
- cross-connection weight=1.0: full signal strength from eye to motor
- switchingRate=0.5: moderate logistic slope for proportional motor response
- maxSpeedFraction=1.0: use full wheel speed range
- noise=0, uniselector off: clean deterministic behavior

Usage:
    # Headless run with trajectory printout
    python -m HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2

    # With visualizer
    python -m HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2 --visualize

@author: stefano
'''

import os
import time
import threading
from math import sqrt, degrees


def setup_phototaxis(backendSimulator=None):
    '''Set up a phototaxis experiment with a Braitenberg type-2 vehicle.

    Creates a SimulatorBackendHOMEO (unless one is provided), initializes
    a Braitenberg 2 positive homeostat, and tunes the parameters for
    responsive phototaxis behavior.

    Parameters:
        backendSimulator: optional SimulatorBackendHOMEO instance.
                          If None, one is created with default settings.

    Returns:
        (hom, backend) - the configured Homeostat and the backend simulator
    '''
    from Simulator.SimulatorBackend import SimulatorBackendHOMEO
    from Simulator.HomeoExperiments import initializeBraiten2_2Pos

    if backendSimulator is None:
        lock = threading.Lock()
        backendSimulator = SimulatorBackendHOMEO(lock=lock, robotName='Khepera')

    # Set log directory and experiment name before world setup
    # Create a per-day subdirectory under SimulationsData/
    sims_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'SimulationsData')
    log_dir = os.path.join(sims_root, 'SimsData-' + time.strftime("%Y-%m-%d"))
    os.makedirs(log_dir, exist_ok=True)
    backendSimulator.kheperaSimulation.dataDir = log_dir
    backendSimulator.kheperaSimulation.experimentName = 'phototaxis_braitenberg2'

    hom = initializeBraiten2_2Pos(backendSimulator=backendSimulator)

    _tune_for_phototaxis(hom)

    return hom, backendSimulator


def _tune_for_phototaxis(hom):
    '''Override default homeostat parameters for responsive phototaxis.

    The default parameters (mass=100, viscosity=0.9*max) are designed for
    long-term adaptation via genetic algorithm. Here we set lighter dynamics
    so the robot actively follows light in real time.
    '''

    # Eyes: fast pass-through with self-damping
    for u in hom.homeoUnits:
        if 'Eye' in u.name and 'Sensor' not in u.name:
            u.mass = 1
            u.viscosity = 0.0
            u.noise = 0
            u.uniselectorActive = False
            # Self-connection provides damping (deviation decays when input drops)
            u.inputConnections[0].status = True
            u.inputConnections[0].newWeight(-0.9)

    # Motors: responsive with self-damping and full speed range
    for u in hom.homeoUnits:
        if 'Motor' in u.name:
            u.mass = 1
            u.viscosity = 0.0
            u.noise = 0
            u.uniselectorActive = False
            u._switchingRate = 0.5
            u._maxSpeedFraction = 1.0
            u._maxSpeed = None  # force recalculation from transducer range
            # Self-connection provides damping
            u.inputConnections[0].status = True
            u.inputConnections[0].newWeight(-0.9)

    # Sensors: clean signal (no noise)
    for u in hom.homeoUnits:
        if 'Sensor' in u.name:
            u.noise = 0

    # Full-strength cross-connections with no noise
    for u in hom.homeoUnits:
        for conn in u.inputConnections:
            if conn.status and conn.incomingUnit != u:
                conn.newWeight(1.0)
                conn.noise = 0


def run_headless(total_steps=10000, report_interval=500):
    '''Run the phototaxis experiment headless and print the trajectory.

    Trajectory data (robot position, heading, light position, distance)
    is logged every tick to a .traj file in SimulationsData/.

    Parameters:
        total_steps:     number of simulation steps to run
        report_interval: print robot state every this many steps

    Returns:
        (hom, backend) - the Homeostat and backend after the run
    '''
    from Helpers.HomeostatConditionLogger import (
        log_homeostat_conditions, log_homeostat_conditions_json)

    hom, backend = setup_phototaxis()
    sim = backend.kheperaSimulation
    robot = sim.allBodies['Khepera']
    target_pos = (7, 7)

    # Log initial conditions
    timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")
    log_dir = sim.dataDir
    log_path = os.path.join(log_dir, 'phototaxis_braitenberg2-' + timestamp + '.log')
    json_path = os.path.join(log_dir, 'phototaxis_braitenberg2-' + timestamp + '.json')
    log_homeostat_conditions(hom, log_path, 'INITIAL CONDITIONS')
    log_homeostat_conditions_json(hom, json_path, 'INITIAL CONDITIONS')

    def dist_to_target():
        rx, ry = robot.body.position[0], robot.body.position[1]
        return sqrt((rx - target_pos[0])**2 + (ry - target_pos[1])**2)

    print('=== Phototaxis: Braitenberg 2 (Positive) ===')
    print(f'Robot start: ({robot.body.position[0]:.3f}, {robot.body.position[1]:.3f})')
    print(f'Light target: {target_pos}')
    print(f'Initial distance: {dist_to_target():.3f}')
    print()
    print(f'{"Step":>6}  {"Robot X":>8}  {"Robot Y":>8}  {"Angle":>7}  {"Dist":>7}  {"L Sens":>7}  {"R Sens":>7}')
    print('-' * 65)

    min_dist = dist_to_target()
    min_t = 0

    for target_tick in range(report_interval, total_steps + 1, report_interval):
        hom.runFor(target_tick)
        rx, ry = robot.body.position[0], robot.body.position[1]
        d = dist_to_target()
        a = degrees(robot.body.angle) % 360
        lsensor = robot.getSensorRead('leftEye')
        rsensor = robot.getSensorRead('rightEye')

        if d < min_dist:
            min_dist = d
            min_t = target_tick

        print(f'{target_tick:>6}  {rx:>8.3f}  {ry:>8.3f}  {a:>7.1f}  {d:>7.3f}  {lsensor:>7.2f}  {rsensor:>7.2f}')

    print()
    print(f'Closest approach: {min_dist:.3f} at t={min_t}')
    print(f'Final distance:   {dist_to_target():.3f}')

    sim.saveTrajectory()

    # Log final conditions
    log_homeostat_conditions(hom, log_path, 'FINAL CONDITIONS')
    log_homeostat_conditions_json(hom, json_path, 'FINAL CONDITIONS')

    return hom, backend


def run_visualized():
    '''Run the phototaxis experiment with the pyglet visualizer.

    The window must be created before the simulation so that all
    vertex lists are allocated in the same GL context.

    Trajectory data is logged every tick to a .traj file in
    SimulationsData/.

    Press Q or Escape to close the window.
    Up/Down arrows adjust simulation speed (steps per frame).
    '''
    import pyglet
    from pyglet.gl import (glEnable, glBlendFunc, glHint, glClearColor, glClear,
                           GL_BLEND, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
                           GL_LINE_SMOOTH, GL_LINE_SMOOTH_HINT, GL_NICEST,
                           GL_COLOR_BUFFER_BIT)
    from KheperaSimulator.KheperaSimulator import KheperaCamera

    # Create the window first (establishes GL context)
    window = pyglet.window.Window(width=800, height=600, resizable=True,
                                  caption='Phototaxis - Braitenberg 2')

    glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glClearColor(0.55, 0.95, 1.0, 1.0)

    from Helpers.HomeostatConditionLogger import (
        log_homeostat_conditions, log_homeostat_conditions_json)

    # Now set up the simulation (vertex lists created in window's GL context)
    hom, backend = setup_phototaxis()
    sim = backend.kheperaSimulation
    robot = sim.allBodies['Khepera']
    target_pos = sim.allBodies['TARGET'].position

    # Log initial conditions
    timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")
    log_dir = sim.dataDir
    log_path = os.path.join(log_dir, 'phototaxis_braitenberg2-' + timestamp + '.log')
    json_path = os.path.join(log_dir, 'phototaxis_braitenberg2-' + timestamp + '.json')
    log_homeostat_conditions(hom, log_path, 'INITIAL CONDITIONS')
    log_homeostat_conditions_json(hom, json_path, 'INITIAL CONDITIONS')

    # Camera centered between robot start (4,4) and light (7,7), zoomed out
    # enough to see the whole scene (zoom=8 shows ~16 units across)
    camera = KheperaCamera(position=(5.5, 5.5), zoom=8.0)
    # state[0] = step counter, state[1] = steps per frame
    # Each step takes ~12ms, so 5 steps/frame ~ 60ms ~ 15 FPS
    state = [0, 5]

    @window.event
    def on_draw():
        glClear(GL_COLOR_BUFFER_BIT)
        camera.focus(window)
        sim.pygletDraw()

    def update(dt):
        state[0] += state[1]
        hom.runFor(state[0])
        # Update window title with progress
        rx, ry = robot.body.position[0], robot.body.position[1]
        dist = sqrt((rx - target_pos[0])**2 + (ry - target_pos[1])**2)
        window.set_caption(
            f'Phototaxis - t={state[0]}  speed={state[1]}  '
            f'dist={dist:.2f}  [{1/max(dt, 0.001):.0f} fps]')

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

    if '--visualize' in sys.argv:
        run_visualized()
    else:
        run_headless()
