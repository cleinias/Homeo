'''
Phototaxis experiment using a Braitenberg type-2 vehicle
with the internal HOMEO Khepera simulator backend.

The experiment sets up a 6-unit homeostat controlling a Khepera robot
with cross-wired connections (right motor <- left eye, left motor <- right eye).
The robot starts at (4,4) and a light source is placed at (7,7).


Parameter origin and tuning
---------------------------

The base homeostat topology and wiring come from initializeBraiten2_2()
in Simulator/HomeoExperiments.py.  That function creates 6 fully-connected
units (2 motors, 2 eyes, 2 sensor inputs), disables all connections
except self-connections, then activates the Braitenberg cross-connections
(left eye -> right motor, right eye -> left motor).  The default unit
parameters it sets (mass=100, viscosity=0.9*maxViscosity, noise=0.05,
connection weights=0.5, uniselector timing=100) were designed for
long-term optimization via genetic algorithm -- the GA searches over
those heavy, sluggish dynamics to find stable adaptive behavior.

For a direct phototaxis demonstration without GA, those defaults are
far too sluggish: with mass=100 each tick's input barely changes the
unit's deviation, so the robot essentially does not move.  The function
_tune_for_phototaxis() overrides them with values chosen by reasoning
about the model's equations (not empirically optimized):

- mass=1, viscosity=0:  The Newtonian needle equation computes
  acceleration = (force - viscosity*velocity) / mass.  Setting mass=1
  and viscosity=0 removes all inertia and drag, so each tick's input
  translates immediately into a change in deviation.  This is the
  simplest possible dynamics.

- self-connection weight=-0.9 on eyes and motors:  The linear needle
  computation model (needleCompMethod='linear') has no natural decay.
  Once a unit's deviation reaches maxDeviation it stays pinned there
  forever, even if input drops to zero.  A negative self-connection
  feeds the unit's own output back with opposite sign, acting as a
  damping term: deviation decays toward zero when external input
  diminishes.  The value -0.9 (close to -1) gives strong but not
  instantaneous decay per tick.

- cross-connection weight=1.0:  Full-strength signal transfer from
  eye to motor.  The gain is simply set to maximum so the sensor
  reading drives the motor as strongly as possible.

- switchingRate=0.5:  Controls the steepness of the logistic (sigmoid)
  function that maps a motor unit's deviation to wheel speed inside
  HomeoUnitNewtonianActuator.  A value of 0.5 gives a moderate slope,
  producing a proportional response in the mid-range of deviations
  rather than a sharp on/off switch.

- maxSpeedFraction=1.0:  Uses the full wheel speed range of the
  Khepera robot, rather than limiting it to a fraction.

- noise=0, uniselector off:  All stochastic elements are removed so
  the behavior is fully deterministic, which makes debugging easier.

These values are educated guesses, not optimized.  The robot does
approach the light (distance decreases steadily), but the parameters
have not been systematically searched or validated.  Proper tuning
would require either a GA run or a parameter sweep.


Usage
-----
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
    '''Override the heavy GA-oriented defaults with lightweight dynamics
    for real-time phototaxis.  See the module docstring for a detailed
    explanation of each parameter value and why it was chosen.
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
    log_homeostat_conditions(hom, log_path, 'INITIAL CONDITIONS', 'phototaxis_braitenberg2')
    log_homeostat_conditions_json(hom, json_path, 'INITIAL CONDITIONS', 'phototaxis_braitenberg2')

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
    log_homeostat_conditions(hom, log_path, 'INITIAL CONDITIONS', 'phototaxis_braitenberg2')
    log_homeostat_conditions_json(hom, json_path, 'INITIAL CONDITIONS', 'phototaxis_braitenberg2')

    # Camera centered between robot start (4,4) and light (7,7), zoomed out
    # enough to see the whole scene (zoom=8 shows ~16 units across)
    from KheperaSimulator.KheperaSimulator import _get_shape_program
    from pyglet.gl import GL_LINES

    camera = KheperaCamera(position=(5.5, 5.5), zoom=8.0)
    # state[0] = step counter, state[1] = steps per frame
    # Each step takes ~12ms, so 5 steps/frame ~ 60ms ~ 15 FPS
    state = [0, 5]
    trail_vlists = []  # list of vertex lists for trail segments
    trail_last = [None] # last recorded (x, y)
    TRAIL_MIN_DIST = 0.05  # minimum distance before adding a trail segment

    @window.event
    def on_draw():
        glClear(GL_COLOR_BUFFER_BIT)
        camera.focus(window)
        sim.pygletDraw()
        # Draw trail using the same shader (respects camera projection)
        program = _get_shape_program()
        program.use()
        for vl in trail_vlists:
            vl.draw(GL_LINES)
        program.stop()

    def update(dt):
        state[0] += state[1]
        hom.runFor(state[0])
        # Update window title with progress
        rx, ry = robot.body.position[0], robot.body.position[1]

        # Only add a trail segment when the robot has moved enough
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
