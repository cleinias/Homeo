'''
Ashby-style phototaxis experiment using a Braitenberg type-2 vehicle
with the internal HOMEO Khepera simulator backend.

This is the self-organizing counterpart to phototaxis_braitenberg2_control.py.
Instead of hand-picked parameters, all unit parameters (mass, viscosity,
noise, potentiometer, switch) and connection weights start at random values.
The uniselectors are active on the four real units (motors and eyes), so
that when a unit's essential variable stays critical for too long
(deviation >= critThreshold * maxDeviation for uniselectorTimeInterval ticks),
the uniselector fires and randomly reassigns the weights of that unit's
incoming connections.  This is Ashby's core idea: the system searches
through parameter space by random trial until it finds a configuration
where all units remain within their viable range.

The experiment uses the same 6-unit Braitenberg topology as the control:
2 motors, 2 eyes, 2 sensor inputs, with the robot starting at (4,4) and
a light source at (7,7).


Two initialization modes
-------------------------

1. Fixed topology (default, --fixed-topology):
   The Braitenberg cross-wiring is preserved (left eye -> right motor,
   right eye -> left motor, right eye <- right sensor, left eye <- left
   sensor).  Only the already-active connections are present; disabled
   connections stay disabled.  Unit parameters and connection weights
   are randomized.  Self-connections use state='manual' (protected from
   the uniselector, as in Ashby's original design).  Cross-connections
   use state='uniselector' so the uniselector can change their weights.
   This tests whether Ashby's mechanism can tune a known-good topology.

2. Random topology (--random-topology):
   All connections between the 4 real units start active with random
   weights, noise, and state='uniselector'.  The uniselector can change
   any connection.  The system must discover both useful topology and
   weights.  This is much harder and may not converge within a short run.
   Sensor-only units remain input-only (all their connections disabled)
   since they are pure transducers.

In both modes the sensor-only units (Left Sensor, Right Sensor) have
their uniselectors disabled — they are pure input transducers and should
not self-organize.


Motor and mass overrides
------------------------

Three default values in the base homeostat conspire to make the robot
nearly immobile with random parameters:

1. mass=100 (from HomeoUnit.DefaultParameters, not touched by
   setRandomValues()) makes the Newtonian needle equation
   acceleration = (force - viscosity*velocity) / mass extremely
   sluggish.  We override mass to a random value in [1, 10].

2. _maxSpeedFraction=0.2 in HomeoUnitNewtonianActuator limits the
   motor to 20% of the available wheel speed range, compressing
   effective speeds to a tiny band (~[-0.04, 0.04] m/s).  We set
   it to 0.8.

3. _switchingRate=0.1 makes the logistic sigmoid that maps deviation
   to wheel speed very gentle — moderate deviations produce almost
   no speed.  We set it to 0.5 for a more responsive curve.

All three can be passed as parameters to setup_phototaxis() and the
_ashby_* functions for systematic exploration.


Usage
-----
    # Headless, fixed topology (default)
    python -m HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_Ashby

    # Headless, random topology
    python -m HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_Ashby --random-topology

    # With visualizer
    python -m HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_Ashby --visualize

    # Combined
    python -m HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_Ashby --random-topology --visualize

@author: stefano
'''

import os
import time
import threading
from math import sqrt, degrees

import numpy as np


def setup_phototaxis(topology='fixed', backendSimulator=None,
                     mass_range=(1, 10), max_speed_fraction=0.8,
                     switching_rate=0.5, light_intensity=100,
                     uniselector_type='ashby', continuous_params=None):
    '''Set up an Ashby-style phototaxis experiment.

    Creates a SimulatorBackendHOMEO (unless one is provided), initializes
    a Braitenberg 2 positive homeostat, then randomizes parameters and
    activates uniselectors.

    Parameters:
        topology:           'fixed' preserves Braitenberg wiring,
                            'random' enables all connections randomly.
        backendSimulator:   optional SimulatorBackendHOMEO instance.
                            If None, one is created with default settings.
        mass_range:         (low, high) for random mass on real units.
        max_speed_fraction: fraction of motor speed range to use.
        switching_rate:     logistic sigmoid steepness for motor output.
        light_intensity:    intensity of the light source (negative for
                            a "darkness source").
        uniselector_type:   'ashby' (default discrete stepping switch),
                            'random' (uniform random), or
                            'continuous' (Ornstein-Uhlenbeck weight drift).
        continuous_params:  dict of HomeoUniselectorContinuous parameters
                            (tau_a, theta, sigma_base, sigma_crit,
                            stress_exponent).  Only used when
                            uniselector_type='continuous'.  None = defaults.

    Returns:
        (hom, backend) - the configured Homeostat and the backend simulator
    '''
    from Simulator.SimulatorBackend import SimulatorBackendHOMEO
    from Simulator.HomeoExperiments import initializeBraiten2_2Pos

    if backendSimulator is None:
        lock = threading.Lock()
        backendSimulator = SimulatorBackendHOMEO(lock=lock, robotName='Khepera')

    # Set log directory and experiment name before world setup
    sims_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'SimulationsData')
    log_dir = os.path.join(sims_root, 'SimsData-' + time.strftime("%Y-%m-%d"))
    os.makedirs(log_dir, exist_ok=True)
    backendSimulator.kheperaSimulation.dataDir = log_dir

    if topology == 'random':
        exp_name = 'phototaxis_braitenberg2_Ashby_random'
    else:
        exp_name = 'phototaxis_braitenberg2_Ashby_fixed'
    if light_intensity < 0:
        exp_name += '_dark'
    if uniselector_type == 'continuous':
        exp_name += '_continuous'
    backendSimulator.kheperaSimulation.experimentName = exp_name

    hom = initializeBraiten2_2Pos(backendSimulator=backendSimulator)

    # Override light intensity on the already-created light body
    if light_intensity != 100:
        sim = backendSimulator.kheperaSimulation
        target_body = sim.allBodies['TARGET']
        target_body.userData['intensity'] = light_intensity
        target_body.userData['lightIntensity'] = light_intensity

    kwargs = dict(mass_range=mass_range,
                  max_speed_fraction=max_speed_fraction,
                  switching_rate=switching_rate,
                  uniselector_type=uniselector_type,
                  continuous_params=continuous_params)
    if topology == 'random':
        _ashby_random_topology(hom, **kwargs)
    else:
        _ashby_fixed_topology(hom, **kwargs)

    return hom, backendSimulator


def _set_uniselector_type(unit, uniselector_type, continuous_params=None):
    '''Set the uniselector on a unit according to the requested type.

    Parameters:
        unit:              HomeoUnit instance
        uniselector_type:  'ashby', 'random', or 'continuous'
        continuous_params: dict of HomeoUniselectorContinuous overrides
    '''
    from Core.HomeoUniselectorContinuous import HomeoUniselectorContinuous
    from Core.HomeoUniselectorAshby import HomeoUniselectorAshby
    from Core.HomeoUniselectorUniformRandom import HomeoUniselectorUniformRandom

    if uniselector_type == 'continuous':
        unis = HomeoUniselectorContinuous()
        if continuous_params:
            for key, val in continuous_params.items():
                setattr(unis, key, val)
        unit.uniselector = unis
    elif uniselector_type == 'random':
        unit.uniselector = HomeoUniselectorUniformRandom()
    else:
        # Default: Ashby stepping switch (already the default on new units)
        pass


def _ashby_fixed_topology(hom, mass_range=(1, 10),
                          max_speed_fraction=0.8, switching_rate=0.5,
                          uniselector_type='ashby', continuous_params=None):
    '''Randomize unit parameters and connection weights, keeping the
    Braitenberg cross-wiring topology intact.

    The topology set up by initializeBraiten2_2 is preserved: only
    connections that were already active get random weights.  Disabled
    connections stay disabled.  Self-connections are protected from the
    uniselector (state='manual').  Cross-connections are placed under
    uniselector control (state='uniselector').

    Motors and eyes have their uniselectors activated so the system
    can self-organize.  Sensor-only units are left as pure inputs.

    Parameters:
        mass_range:         (low, high) for random mass on real units.
                            Default (1, 10) — light enough for responsive
                            dynamics.  setRandomValues() leaves mass at
                            the sluggish default of 100; we override it.
        max_speed_fraction: fraction of motor speed range to use.
                            Default 0.8.  The actuator default is 0.2
                            which compresses speeds to a tiny band.
        switching_rate:     logistic sigmoid steepness for motor output.
                            Default 0.5.  The actuator default is 0.1
                            which makes moderate deviations produce
                            almost no speed.
        uniselector_type:   'ashby', 'random', or 'continuous'.
        continuous_params:  dict of HomeoUniselectorContinuous parameters.
    '''

    for u in hom.homeoUnits:
        if 'Sensor' in u.name and 'Eye' not in u.name:
            # Sensor-only units: pure input, no self-organization
            continue

        # Randomize unit parameters
        u.setRandomValues()

        # Override mass to a responsive range (setRandomValues doesn't touch it)
        u.mass = np.random.uniform(*mass_range)

        # Activate uniselector and set type
        u.uniselectorActive = True
        _set_uniselector_type(u, uniselector_type, continuous_params)

        # Motor-specific overrides
        if 'Motor' in u.name:
            u._maxSpeedFraction = max_speed_fraction
            u._switchingRate = switching_rate
            u._maxSpeed = None  # force recalculation from new fraction

        for conn in u.inputConnections:
            if conn.incomingUnit == u:
                # Self-connection: random weight but protected from uniselector
                conn.newWeight(np.random.uniform(-1, 1))
                conn.noise = np.random.uniform(0, 0.05)
                conn.state = 'manual'
                conn.status = True
            elif conn.status:
                # Active cross-connection: randomize weight, put under uniselector
                conn.newWeight(np.random.uniform(-1, 1))
                conn.noise = np.random.uniform(0, 0.1)
                conn.state = 'uniselector'


def _ashby_random_topology(hom, mass_range=(1, 10),
                           max_speed_fraction=0.8, switching_rate=0.5,
                           uniselector_type='ashby', continuous_params=None):
    '''Fully randomize all connections between the 4 real units.

    Every connection on motors and eyes gets a random weight and is
    placed under uniselector control.  The system must discover both
    useful topology (which connections matter) and weights.

    Sensor-only units remain input-only with all connections disabled.

    Parameters:
        mass_range:         (low, high) for random mass on real units.
                            Default (1, 10).  See _ashby_fixed_topology.
        max_speed_fraction: fraction of motor speed range to use.
                            Default 0.8.
        switching_rate:     logistic sigmoid steepness for motor output.
                            Default 0.5.
        uniselector_type:   'ashby', 'random', or 'continuous'.
        continuous_params:  dict of HomeoUniselectorContinuous parameters.
    '''

    for u in hom.homeoUnits:
        if 'Sensor' in u.name and 'Eye' not in u.name:
            # Sensor-only units: keep as pure inputs, all connections off
            u.uniselectorActive = False
            for conn in u.inputConnections:
                conn.status = False
            continue

        # Randomize unit parameters
        u.setRandomValues()

        # Override mass to a responsive range (setRandomValues doesn't touch it)
        u.mass = np.random.uniform(*mass_range)

        # Randomize all connections (sets all active with random weights,
        # noise, and state='uniselector')
        u.randomizeAllConnectionValues()

        # Activate uniselector and set type
        u.uniselectorActive = True
        _set_uniselector_type(u, uniselector_type, continuous_params)

        # Protect self-connection from uniselector
        u.inputConnections[0].state = 'manual'

        # Motor-specific overrides
        if 'Motor' in u.name:
            u._maxSpeedFraction = max_speed_fraction
            u._switchingRate = switching_rate
            u._maxSpeed = None  # force recalculation from new fraction


def run_headless(topology='fixed', total_steps=10000, report_interval=500,
                 light_intensity=100, early_stop_distance=None, quiet=False,
                 uniselector_type='ashby', continuous_params=None):
    '''Run the Ashby phototaxis experiment headless and print the trajectory.

    Parameters:
        topology:             'fixed' or 'random'
        total_steps:          number of simulation steps to run
        report_interval:      print robot state every this many steps
        light_intensity:      intensity of the light source (negative for
                              a "darkness source")
        early_stop_distance:  if set, stop when the robot gets closer than
                              this distance to the target
        quiet:                if True, suppress per-tick output (for batch mode)
        uniselector_type:     'ashby', 'random', or 'continuous'
        continuous_params:    dict of HomeoUniselectorContinuous overrides

    Returns:
        dict with keys: hom, backend, final_dist, min_dist, min_t,
                        steps_run, final_x, final_y, early_stopped,
                        log_path, json_path
    '''
    from Helpers.HomeostatConditionLogger import (
        log_homeostat_conditions, log_homeostat_conditions_json)

    hom, backend = setup_phototaxis(topology=topology,
                                    light_intensity=light_intensity,
                                    uniselector_type=uniselector_type,
                                    continuous_params=continuous_params)

    # Headless optimizations: disable the per-tick sleep and in-memory data
    # collection (initial/final state is logged separately to file)
    hom.slowingFactor = 0
    hom.collectsData = False
    hom._headless = True
    for u in hom.homeoUnits:
        u._headless = True

    sim = backend.kheperaSimulation
    robot = sim.allBodies['Khepera']
    target_pos = (7, 7)
    exp_name = sim.experimentName

    # Log initial conditions
    timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")
    log_dir = sim.dataDir
    log_path = os.path.join(log_dir, exp_name + '-' + timestamp + '.log')
    json_path = os.path.join(log_dir, exp_name + '-' + timestamp + '.json')
    log_homeostat_conditions(hom, log_path, 'INITIAL CONDITIONS', exp_name)
    log_homeostat_conditions_json(hom, json_path, 'INITIAL CONDITIONS', exp_name)

    def dist_to_target():
        rx, ry = robot.body.position[0], robot.body.position[1]
        return sqrt((rx - target_pos[0])**2 + (ry - target_pos[1])**2)

    mode_label = 'fixed topology' if topology == 'fixed' else 'random topology'
    if not quiet:
        print(f'=== Phototaxis: Braitenberg 2 — Ashby ({mode_label}) ===')
        print(f'Robot start: ({robot.body.position[0]:.3f}, {robot.body.position[1]:.3f})')
        print(f'Light target: {target_pos}')
        print(f'Initial distance: {dist_to_target():.3f}')
        print()
        print(f'{"Step":>6}  {"Robot X":>8}  {"Robot Y":>8}  {"Angle":>7}  {"Dist":>7}  {"L Sens":>7}  {"R Sens":>7}')
        print('-' * 65)

    min_dist = dist_to_target()
    min_t = 0
    early_stopped = False

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

        if not quiet:
            print(f'{target_tick:>6}  {rx:>8.3f}  {ry:>8.3f}  {a:>7.1f}  {d:>7.3f}  {lsensor:>7.2f}  {rsensor:>7.2f}')

        if early_stop_distance is not None and d < early_stop_distance:
            if not quiet:
                print(f'\n  *** Early stop: distance {d:.3f} < {early_stop_distance}')
            early_stopped = True
            break

    final_dist = dist_to_target()
    final_x, final_y = robot.body.position[0], robot.body.position[1]
    steps_run = target_tick

    if not quiet:
        print()
        print(f'Closest approach: {min_dist:.3f} at t={min_t}')
        print(f'Final distance:   {final_dist:.3f}')

    sim.saveTrajectory()

    # Log final conditions
    log_homeostat_conditions(hom, log_path, 'FINAL CONDITIONS')
    log_homeostat_conditions_json(hom, json_path, 'FINAL CONDITIONS')

    return dict(hom=hom, backend=backend,
                final_dist=final_dist, min_dist=min_dist, min_t=min_t,
                steps_run=steps_run, final_x=final_x, final_y=final_y,
                early_stopped=early_stopped,
                log_path=log_path, json_path=json_path)


def run_batch(n_runs=10, topology='fixed', total_steps=2000000,
              report_interval=500, light_intensity=100,
              early_stop_distance=None,
              uniselector_type='ashby', continuous_params=None):
    '''Run a batch of experiments and print a summary table.

    Parameters:
        n_runs:               number of independent runs
        topology:             'fixed' or 'random'
        total_steps:          step budget per run
        report_interval:      ticks between position checks
        light_intensity:      intensity (negative for darkness)
        early_stop_distance:  stop run early if robot gets this close
        uniselector_type:     'ashby', 'random', or 'continuous'
        continuous_params:    dict of HomeoUniselectorContinuous overrides

    Returns:
        list of result dicts (one per run, without hom/backend)
    '''
    import csv as _csv

    mode = 'dark' if light_intensity < 0 else 'light'
    print(f'=== Batch: {n_runs} runs, {mode}, {total_steps} ticks budget ===')
    print()

    results = []
    for i in range(n_runs):
        t0 = time.time()
        print(f'--- Run {i+1}/{n_runs} ---', flush=True)
        r = run_headless(topology=topology, total_steps=total_steps,
                         report_interval=report_interval,
                         light_intensity=light_intensity,
                         early_stop_distance=early_stop_distance,
                         quiet=True,
                         uniselector_type=uniselector_type,
                         continuous_params=continuous_params)
        elapsed = time.time() - t0
        # Drop non-serialisable objects before storing
        r.pop('hom'); r.pop('backend')
        r['run'] = i + 1
        r['wall_time'] = elapsed
        results.append(r)
        print(f'  final_dist={r["final_dist"]:.3f}  min_dist={r["min_dist"]:.3f}  '
              f'steps={r["steps_run"]}  early_stop={r["early_stopped"]}  '
              f'wall={elapsed:.1f}s', flush=True)

    # Summary table
    print()
    print(f'{"Run":>4}  {"Final Dist":>10}  {"Min Dist":>10}  {"Min@t":>8}  '
          f'{"Steps":>8}  {"EarlyStop":>9}  {"Wall(s)":>7}')
    print('-' * 68)
    for r in results:
        print(f'{r["run"]:>4}  {r["final_dist"]:>10.3f}  {r["min_dist"]:>10.3f}  '
              f'{r["min_t"]:>8}  {r["steps_run"]:>8}  '
              f'{"Yes" if r["early_stopped"] else "No":>9}  '
              f'{r["wall_time"]:>7.1f}')

    dists = [r['final_dist'] for r in results]
    mins = [r['min_dist'] for r in results]
    stops = sum(1 for r in results if r['early_stopped'])
    print('-' * 68)
    print(f'Mean final dist: {np.mean(dists):.3f}  (std {np.std(dists):.3f})')
    print(f'Mean min dist:   {np.mean(mins):.3f}  (std {np.std(mins):.3f})')
    print(f'Early stops:     {stops}/{n_runs}')

    # Save summary CSV next to the individual log files
    if results:
        log_dir = os.path.dirname(results[0]['log_path'])
        csv_name = f'batch_{mode}_{time.strftime("%Y-%m-%d-%H-%M-%S")}.csv'
        csv_path = os.path.join(log_dir, csv_name)
        fields = ['run', 'final_dist', 'min_dist', 'min_t', 'steps_run',
                  'early_stopped', 'final_x', 'final_y', 'wall_time',
                  'log_path', 'json_path']
        with open(csv_path, 'w', newline='') as f:
            w = _csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(results)
        print(f'\nSummary saved to: {csv_path}')

    return results


def run_visualized(topology='fixed'):
    '''Run the Ashby phototaxis experiment with the pyglet visualizer.

    Press Q or Escape to close the window.
    Up/Down arrows adjust simulation speed (steps per frame).
    '''
    import pyglet
    from pyglet.gl import (glEnable, glBlendFunc, glHint, glClearColor, glClear,
                           GL_BLEND, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
                           GL_LINE_SMOOTH, GL_LINE_SMOOTH_HINT, GL_NICEST,
                           GL_COLOR_BUFFER_BIT)
    from KheperaSimulator.KheperaSimulator import KheperaCamera

    mode_label = 'fixed' if topology == 'fixed' else 'random'
    window = pyglet.window.Window(width=800, height=600, resizable=True,
                                  caption=f'Phototaxis Ashby ({mode_label})')

    glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glClearColor(0.55, 0.95, 1.0, 1.0)

    from Helpers.HomeostatConditionLogger import (
        log_homeostat_conditions, log_homeostat_conditions_json)

    hom, backend = setup_phototaxis(topology=topology)
    sim = backend.kheperaSimulation
    robot = sim.allBodies['Khepera']
    target_pos = sim.allBodies['TARGET'].position
    exp_name = sim.experimentName

    # Log initial conditions
    timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")
    log_dir = sim.dataDir
    log_path = os.path.join(log_dir, exp_name + '-' + timestamp + '.log')
    json_path = os.path.join(log_dir, exp_name + '-' + timestamp + '.json')
    log_homeostat_conditions(hom, log_path, 'INITIAL CONDITIONS', exp_name)
    log_homeostat_conditions_json(hom, json_path, 'INITIAL CONDITIONS', exp_name)

    from KheperaSimulator.KheperaSimulator import _get_shape_program, _make_vlist
    from pyglet.gl import GL_LINES

    camera = KheperaCamera(position=(5.5, 5.5), zoom=8.0)
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
            f'Phototaxis Ashby ({mode_label}) - t={state[0]}  speed={state[1]}  '
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

    topology = 'random' if '--random-topology' in sys.argv else 'fixed'

    # Parse --steps N (default 10000)
    total_steps = 10000
    if '--steps' in sys.argv:
        idx = sys.argv.index('--steps')
        if idx + 1 < len(sys.argv):
            total_steps = int(sys.argv[idx + 1])

    # Parse --dark (negative light intensity) and --early-stop DIST
    light_intensity = -100 if '--dark' in sys.argv else 100
    early_stop_distance = None
    if '--early-stop' in sys.argv:
        idx = sys.argv.index('--early-stop')
        if idx + 1 < len(sys.argv):
            early_stop_distance = float(sys.argv[idx + 1])
    elif '--dark' in sys.argv:
        early_stop_distance = 1.5  # default: TrajectoryGrapher's gray circle

    # Parse --batch N
    n_batch = None
    if '--batch' in sys.argv:
        idx = sys.argv.index('--batch')
        if idx + 1 < len(sys.argv):
            n_batch = int(sys.argv[idx + 1])

    # Parse --continuous (use Ornstein-Uhlenbeck weight drift)
    uniselector_type = 'continuous' if '--continuous' in sys.argv else 'ashby'

    if '--visualize' in sys.argv:
        run_visualized(topology=topology)
    elif n_batch is not None:
        run_batch(n_runs=n_batch, topology=topology,
                  total_steps=total_steps,
                  light_intensity=light_intensity,
                  early_stop_distance=early_stop_distance,
                  uniselector_type=uniselector_type)
    else:
        run_headless(topology=topology, total_steps=total_steps,
                     light_intensity=light_intensity,
                     early_stop_distance=early_stop_distance,
                     uniselector_type=uniselector_type)
