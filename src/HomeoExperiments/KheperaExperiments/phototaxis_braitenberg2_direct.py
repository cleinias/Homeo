'''
Simplified 2+2 Braitenberg type-2 phototaxis experiment.

Same phototaxis task as phototaxis_braitenberg2_Ashby.py, but with a
simplified vehicle: the two intermediate "eye" units are eliminated.
The two passive sensor inputs (HomeoUnitInput) connect directly to the
two motor outputs (HomeoUnitNewtonianActuator).

Architecture
------------
    Left Sensor  ──►  Right Motor   (Braitenberg cross-wiring)
    Right Sensor ──►  Left Motor

Total: 4 units (2 HomeoUnitInput + 2 HomeoUnitNewtonianActuator)
compared to 6 units in the standard version (2 input + 2 eyes + 2 motors).

This is closer to Steven Battle's setup: the sensor transducers feed
directly into the motor units, with no intermediate processing layer.
The motor units have negative self-connections (per stability analysis
of the 2-unit homeostat, a negative self-connection guarantees
stability regardless of the cross-connection values).


Initialization modes
--------------------

1. Fixed topology (default, --fixed-topology):
   Only the Braitenberg cross-wiring is active (Left Sensor -> Right Motor,
   Right Sensor -> Left Motor).  Motor-to-motor connections are disabled.
   Self-connections are negative and protected from the uniselector.

2. Random topology (--random-topology):
   All connections between the 2 motors are active (including inter-motor).
   Sensor-only units remain input-only.

3. Fixed weights (--fixed-weights): the non-adaptive baseline.
   Braitenberg's vehicle 2b ("aggression"): each sensor excites the
   contra-lateral motor with a fixed weight of +1.0.  No uniselector, no
   noise, no random parameters, so a run depends only on the start pose.
   Motor dynamics as in phototaxis_braitenberg2_control (mass 1, viscosity
   0, -0.9 damping self-connection).  Ignores --random-topology/--continuous.

Start pose (any mode)
---------------------
   Default: robot at (4, 4), heading 0; the light at (7, 7) is in view.
   --random-heading   random heading, default position
   --random-start     random heading and a random position 2-6 units from
                      the light
   Both are drawn from the run's seed, and the batch CSV records the start
   pose and whether either eye could see the light at the start.


Usage
-----
    # Fixed-weight baseline, 20 runs from random start poses
    python -m HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct --fixed-weights --random-start --batch 20

    # Headless, fixed topology (default)
    python -m HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct

    # Headless, random topology
    python -m HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct --random-topology

    # With visualizer
    python -m HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct --visualize

    # Batch mode
    python -m HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct --batch 10

@author: stefano
'''

import os
import random
import time
import threading
from math import sqrt, degrees

import numpy as np


def setup_phototaxis(topology='fixed', backendSimulator=None,
                     mass_range=(1, 10), max_speed_fraction=0.8,
                     switching_rate=0.5, light_intensity=100,
                     uniselector_type='ashby', continuous_params=None,
                     seed=None, fixed_weights=False,
                     stable_integration=True, start_at_rest=False):
    '''Set up a simplified 2+2 phototaxis experiment.

    Creates a SimulatorBackendHOMEO (unless one is provided), initializes
    a 4-unit Braitenberg-2 homeostat (2 sensors + 2 motors, no eyes),
    then randomizes parameters and activates uniselectors on the motors.

    Parameters:
        topology:           'fixed' — only Braitenberg cross-wiring active
                            'random' — all motor connections active
        backendSimulator:   optional SimulatorBackendHOMEO instance.
        mass_range:         (low, high) for random mass on motor units.
        max_speed_fraction: fraction of motor speed range to use.
        switching_rate:     logistic sigmoid steepness for motor output.
        light_intensity:    intensity of the light source (negative for
                            a "darkness source").
        uniselector_type:   'ashby' (default), 'random', or 'continuous'.
        continuous_params:  dict of HomeoUniselectorContinuous overrides.
        seed:               RNG seed for reproducibility.
        fixed_weights:      if True, build the non-adaptive Braitenberg 2b
                            baseline (see _direct_fixed_weights); topology,
                            mass_range, uniselector_type and
                            continuous_params are then ignored.

    Returns:
        (hom, backend, seed)
    '''
    from Simulator.SimulatorBackend import SimulatorBackendHOMEO
    from Core.Homeostat import Homeostat
    from Core.HomeoUnit import HomeoUnit
    from RobotSimulator.HomeoUnitNewtonianTransduc import HomeoUnitNewtonianActuator
    from RobotSimulator.HomeoUnitNewtonianTransduc import HomeoUnitInput
    from Simulator.HomeoExperiments import basicBraiten2Tranducers

    # Seed both RNGs before any stochastic initialization
    if seed is None:
        seed = int.from_bytes(os.urandom(4), 'big')
    np.random.seed(seed)
    random.seed(seed)

    if backendSimulator is None:
        lock = threading.Lock()
        backendSimulator = SimulatorBackendHOMEO(lock=lock, robotName='Khepera')

    # Set log directory and experiment name before world setup
    from Helpers.General_Helper_Functions import simulations_data_dir
    sims_root = simulations_data_dir()
    log_dir = os.path.join(sims_root, 'SimsData-' + time.strftime("%Y-%m-%d"))
    os.makedirs(log_dir, exist_ok=True)
    backendSimulator.kheperaSimulation.dataDir = log_dir

    if fixed_weights:
        exp_name = 'phototaxis_braitenberg2_direct_control'
    elif topology == 'random':
        exp_name = 'phototaxis_braitenberg2_direct_random'
    else:
        exp_name = 'phototaxis_braitenberg2_direct_fixed'
    if light_intensity < 0:
        exp_name += '_dark'
    if uniselector_type == 'continuous' and not fixed_weights:
        exp_name += '_continuous'
    backendSimulator.kheperaSimulation.experimentName = exp_name

    # --- Build the 4-unit homeostat ---
    world = 'kheperaBraitenberg2_HOMEO_World'
    transducers = basicBraiten2Tranducers(backendSimulator, world)

    hom = Homeostat()
    hom._host = backendSimulator.host
    hom._port = backendSimulator.port
    HomeoUnit.clearNames()

    rightWheel = transducers["rightWheelTransd"]
    leftWheel = transducers["leftWheelTransd"]
    leftSensorTransd = transducers["leftEyeTransd"]
    rightSensorTransd = transducers["rightEyeTransd"]

    # 2 motors + 2 sensor inputs (no eye intermediaries)
    leftMotor = HomeoUnitNewtonianActuator(transducer=leftWheel)
    rightMotor = HomeoUnitNewtonianActuator(transducer=rightWheel)
    leftSensor = HomeoUnitInput(transducer=leftSensorTransd)
    rightSensor = HomeoUnitInput(transducer=rightSensorTransd)

    hom.addFullyConnectedUnit(leftMotor)
    hom.addFullyConnectedUnit(rightMotor)
    hom.addFullyConnectedUnit(leftSensor)
    hom.addFullyConnectedUnit(rightSensor)

    # Name units
    leftMotor.name = 'Left Motor'
    rightMotor.name = 'Right Motor'
    leftSensor.name = 'Left Sensor'
    rightSensor.name = 'Right Sensor'

    # Disable all sensor connections (pure input transducers)
    leftSensor.uniselectorActive = False
    rightSensor.uniselectorActive = False
    for conn in leftSensor.inputConnections:
        conn.status = False
    for conn in rightSensor.inputConnections:
        conn.status = False

    # Override light intensity
    if light_intensity != 100:
        sim = backendSimulator.kheperaSimulation
        target_body = sim.allBodies['TARGET']
        target_body.userData['intensity'] = light_intensity
        target_body.userData['lightIntensity'] = light_intensity

    # Apply topology-specific wiring
    kwargs = dict(mass_range=mass_range,
                  max_speed_fraction=max_speed_fraction,
                  switching_rate=switching_rate,
                  uniselector_type=uniselector_type,
                  continuous_params=continuous_params,
                  stable_integration=stable_integration,
                  start_at_rest=start_at_rest)
    if fixed_weights:
        _direct_fixed_weights(hom, max_speed_fraction=max_speed_fraction,
                              switching_rate=switching_rate)
    elif topology == 'random':
        _direct_random_topology(hom, **kwargs)
    else:
        _direct_fixed_topology(hom, **kwargs)

    return hom, backendSimulator, seed


def _set_uniselector_type(unit, uniselector_type, continuous_params=None):
    '''Set the uniselector on a unit according to the requested type.'''
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
        pass  # default Ashby stepping switch


def _direct_fixed_topology(hom, mass_range=(1, 10),
                           max_speed_fraction=0.8, switching_rate=0.5,
                           uniselector_type='ashby', continuous_params=None,
                           stable_integration=True, start_at_rest=False):
    '''Fixed Braitenberg cross-wiring: sensors connect directly to
    contra-lateral motors.  Inter-motor connections are disabled.

    Connection scheme:
        Left Sensor  -> Right Motor  (cross-wired, under uniselector)
        Right Sensor -> Left Motor   (cross-wired, under uniselector)
        Left Motor   -> Left Motor   (negative self-connection, manual)
        Right Motor  -> Right Motor  (negative self-connection, manual)
    '''
    for u in hom.homeoUnits:
        if 'Sensor' in u.name:
            continue

        # Randomize unit parameters (rejecting numerically unstable draws)
        _randomize_unit_stably(u, mass_range, stable_integration, start_at_rest)

        # Motor-specific overrides
        u._maxSpeedFraction = max_speed_fraction
        u._switchingRate = switching_rate
        u._maxSpeed = None  # force recalculation from new fraction

        # Activate uniselector
        u.uniselectorActive = True
        _set_uniselector_type(u, uniselector_type, continuous_params)

        # Disable all non-self connections first
        for conn in u.inputConnections[1:]:
            conn.status = False

        # Self-connection: negative (pass negative value to newWeight),
        # protected from uniselector
        u.inputConnections[0].newWeight(-np.random.uniform(0.01, 0.1))
        u.inputConnections[0].noise = np.random.uniform(0, 0.05)
        u.inputConnections[0].state = 'manual'
        u.inputConnections[0].status = True

    # Activate Braitenberg cross-wiring: Left Sensor -> Right Motor,
    # Right Sensor -> Left Motor
    cross_wiring = {
        'Left Motor': 'Right Sensor',
        'Right Motor': 'Left Sensor',
    }
    for u in hom.homeoUnits:
        if u.name not in cross_wiring:
            continue
        source_name = cross_wiring[u.name]
        for conn in u.inputConnections:
            if conn.incomingUnit.name == source_name:
                conn.newWeight(np.random.uniform(-0.1, 0.1))
                conn.noise = np.random.uniform(0, 0.1)
                conn.state = 'uniselector'
                conn.status = True



# --- Numerical-integration stability -----------------------------------------
#
# The Newtonian needle is integrated explicitly (HomeoJIT._jit_needle_position_
# newtonian): with zero torque the velocity recursion is
#       v <- v * (1 - viscosity * dt_fast / mass)
# so the step is stable only while  viscosity * dt_fast / mass < 2.  Outside
# that bound the needle diverges to its limit within a few dozen ticks with no
# sensory input at all, which looks like -- but is not -- a saturated unit.
# Random (mass, viscosity) draws violated this in 9 of the 20 runs of
# 2026-09-30; see "Bimodal acquisition in OU chemotaxis".
STABILITY_MARGIN = 1.8          # keep viscosity*dt/mass below this


def _integration_ratio(unit):
    "viscosity * dt_fast / mass -- must stay below 2 for the explicit step."
    dt = getattr(unit, '_dt_fast', 1.0)
    return unit.viscosity * dt / unit.mass if unit.mass else float('inf')


def _randomize_unit_stably(u, mass_range, stable_integration=True,
                           start_at_rest=False, max_tries=200):
    """setRandomValues() + random mass, rejecting numerically unstable draws.

    With stable_integration the (mass, viscosity) pair is resampled until
    viscosity*dt_fast/mass < STABILITY_MARGIN, so the joint distribution is the
    original one conditioned on the integrator being stable.  With
    start_at_rest the needle starts centred and motionless, so the vehicle
    begins stationary instead of mid-manoeuvre.
    """
    for _ in range(max_tries):
        u.setRandomValues()
        u.mass = np.random.uniform(*mass_range)
        if not stable_integration or _integration_ratio(u) < STABILITY_MARGIN:
            break
    else:
        u.viscosity = STABILITY_MARGIN * u.mass / getattr(u, '_dt_fast', 1.0)
    if start_at_rest:
        u.criticalDeviation = 0.0
        u.currentOutput = 0.0
        u._currentVelocity = 0.0
        u._lastAcceleration = 0.0


# Fixed-weight baseline (Braitenberg 2b) parameters
CONTROL_CROSS_WEIGHT = 1.0    # sensor -> contra-lateral motor, excitatory
CONTROL_SELF_WEIGHT = -0.9    # motor self-connection (damping)
CONTROL_MASS = 1.0
CONTROL_VISCOSITY = 0.0


def _direct_fixed_weights(hom, max_speed_fraction=0.8, switching_rate=0.5):
    '''Non-adaptive baseline: Braitenberg's vehicle 2b ("aggression").

    Each sensor excites the contra-lateral motor with a fixed weight
    (CONTROL_CROSS_WEIGHT); inter-motor connections are off.  No uniselector,
    no noise and no random parameters, so a run depends only on the start pose.

    Motor dynamics follow phototaxis_braitenberg2_control: mass 1 and zero
    viscosity, so each tick's input acts immediately, and a damping
    self-connection, so a motor slows down when its input fades.  Motors start
    at zero deviation (zero wheel speed), so, as in Braitenberg's vehicle,
    the robot does not move until an eye sees the light.
    '''
    for u in hom.homeoUnits:
        if 'Sensor' in u.name:
            u.noise = 0
            continue

        u.mass = CONTROL_MASS
        u.viscosity = CONTROL_VISCOSITY
        u.noise = 0
        u.uniselectorActive = False
        u.criticalDeviation = 0.0
        u._maxSpeedFraction = max_speed_fraction
        u._switchingRate = switching_rate
        u._maxSpeed = None  # force recalculation from new fraction

        for conn in u.inputConnections[1:]:
            conn.status = False
        u.inputConnections[0].newWeight(CONTROL_SELF_WEIGHT)
        u.inputConnections[0].noise = 0
        u.inputConnections[0].state = 'manual'
        u.inputConnections[0].status = True

    cross_wiring = {
        'Left Motor': 'Right Sensor',
        'Right Motor': 'Left Sensor',
    }
    for u in hom.homeoUnits:
        if u.name not in cross_wiring:
            continue
        for conn in u.inputConnections:
            if conn.incomingUnit.name == cross_wiring[u.name]:
                conn.newWeight(CONTROL_CROSS_WEIGHT)
                conn.noise = 0
                conn.state = 'manual'
                conn.status = True


def set_start_pose(robot, x=None, y=None, heading=None):
    '''Place the robot at (x, y) with the given heading (degrees, same
    convention as the .traj "heading" column); None keeps the current value.

    Moves the wheel bodies with the chassis, rotating them about its centre,
    so the wheel joints stay intact (KheperaRobot.rotateTo/moveTo do not).
    Call before the first simulation step.
    '''
    from math import radians, cos, sin
    from Box2D import b2Vec2

    body = robot.body
    ox, oy = body.position[0], body.position[1]
    nx = ox if x is None else x
    ny = oy if y is None else y
    delta = 0.0 if heading is None else radians(heading) - body.angle
    c, s = cos(delta), sin(delta)
    for wheel in robot.wheels.values():
        rx, ry = wheel.body.position[0] - ox, wheel.body.position[1] - oy
        wheel.body.position = b2Vec2(nx + c * rx - s * ry, ny + s * rx + c * ry)
        wheel.body.angle += delta
    body.position = b2Vec2(nx, ny)
    body.angle += delta


def _random_start_pose(target_pos, random_position):
    '''Draw a start pose from np.random (so it follows the run's seed):
    a uniform heading, and if random_position, a position at a uniform
    distance of 2-6 units and uniform bearing from the light.
    Returns (x, y, heading); x and y are None when not randomised.'''
    heading = np.random.uniform(0, 360)
    if not random_position:
        return None, None, heading
    d = np.random.uniform(2.0, 6.0)
    bearing = np.random.uniform(0, 2 * np.pi)
    return (target_pos[0] + d * np.cos(bearing),
            target_pos[1] + d * np.sin(bearing), heading)


def _direct_random_topology(hom, mass_range=(1, 10),
                            max_speed_fraction=0.8, switching_rate=0.5,
                            uniselector_type='ashby', continuous_params=None,
                            stable_integration=True, start_at_rest=False):
    '''Random topology: all connections between the 2 motors are active
    (including inter-motor and from sensors).  The system must discover
    useful weights.

    Self-connections are still negative and manual-protected.
    '''
    for u in hom.homeoUnits:
        if 'Sensor' in u.name:
            continue

        _randomize_unit_stably(u, mass_range, stable_integration, start_at_rest)

        u._maxSpeedFraction = max_speed_fraction
        u._switchingRate = switching_rate
        u._maxSpeed = None

        # Set all non-self connections active with random weights
        for conn in u.inputConnections[1:]:
            conn.newWeight(np.random.uniform(-0.1, 0.1))
            conn.noise = np.random.uniform(0, 0.1)
            conn.state = 'uniselector'
            conn.status = True

        # Activate uniselector
        u.uniselectorActive = True
        _set_uniselector_type(u, uniselector_type, continuous_params)

        # Self-connection: negative (pass negative value to newWeight),
        # protected from uniselector
        u.inputConnections[0].newWeight(-np.random.uniform(0.01, 0.1))
        u.inputConnections[0].noise = np.random.uniform(0, 0.05)
        u.inputConnections[0].state = 'manual'
        u.inputConnections[0].status = True


def run_headless(topology='fixed', total_steps=60000, report_interval=500,
                 light_intensity=100, early_stop_distance=None, quiet=False,
                 uniselector_type='ashby', continuous_params=None,
                 state_log=False, state_log_interval=1, seed=None,
                 fixed_weights=False, random_heading=False, random_start=False,
                 stable_integration=True, start_at_rest=False):
    '''Run the simplified 2+2 phototaxis experiment headless.

    Parameters and return value are the same as in
    phototaxis_braitenberg2_Ashby.run_headless(), plus:
        fixed_weights:  run the non-adaptive Braitenberg 2b baseline.
        random_heading: start with a random heading (seeded).
        random_start:   random heading and position 2-6 units from the light.
    The returned dict also has start_x, start_y, start_heading, start_dist
    and start_sees_light (whether either eye saw the light at the start).
    '''
    from Helpers.HomeostatConditionLogger import (
        log_homeostat_conditions, log_homeostat_conditions_json)

    hom, backend, seed = setup_phototaxis(topology=topology,
                                          light_intensity=light_intensity,
                                          uniselector_type=uniselector_type,
                                          continuous_params=continuous_params,
                                          seed=seed,
                                          fixed_weights=fixed_weights,
                                          stable_integration=stable_integration,
                                          start_at_rest=start_at_rest)
    robot = backend.kheperaSimulation.allBodies['Khepera']
    target_pos = (7, 7)
    if random_heading or random_start:
        set_start_pose(robot, *_random_start_pose(target_pos, random_start))
    start_x, start_y = robot.body.position[0], robot.body.position[1]
    start_heading = degrees(robot.body.angle) % 360
    start_dist = sqrt((start_x - target_pos[0])**2 + (start_y - target_pos[1])**2)
    start_sees_light = (robot.getSensorRead('leftEye') != 0 or
                        robot.getSensorRead('rightEye') != 0)

    hom.slowingFactor = 0
    hom.collectsData = False
    hom._headless = True
    for u in hom.homeoUnits:
        u._headless = True

    sim = backend.kheperaSimulation
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

    def dist_to_target():
        rx, ry = robot.body.position[0], robot.body.position[1]
        return sqrt((rx - target_pos[0])**2 + (ry - target_pos[1])**2)

    if fixed_weights:
        mode_label = 'fixed weights, no uniselector'
    else:
        mode_label = 'fixed topology' if topology == 'fixed' else 'random topology'
    if not quiet:
        print(f'=== Phototaxis: Braitenberg 2 Direct 2+2 ({mode_label}) ===')
        print(f'Robot start: ({start_x:.3f}, {start_y:.3f})  heading {start_heading:.1f}  '
              f'light {"in view" if start_sees_light else "NOT in view"}')
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

    if state_log and hom._state_logger is not None:
        hom._state_logger.close()
        hom._state_logger = None

    # Log final conditions
    log_homeostat_conditions(hom, log_path, 'FINAL CONDITIONS')
    log_homeostat_conditions_json(hom, json_path, 'FINAL CONDITIONS')

    return dict(hom=hom, backend=backend,
                final_dist=final_dist, min_dist=min_dist, min_t=min_t,
                steps_run=steps_run, final_x=final_x, final_y=final_y,
                early_stopped=early_stopped,
                log_path=log_path, json_path=json_path,
                state_log_path=state_log_path, seed=seed,
                start_x=start_x, start_y=start_y, start_heading=start_heading,
                start_dist=start_dist, start_sees_light=start_sees_light)


def run_batch(n_runs=10, topology='fixed', total_steps=2000000,
              report_interval=500, light_intensity=100,
              early_stop_distance=None,
              uniselector_type='ashby', continuous_params=None,
              fixed_weights=False, random_heading=False, random_start=False,
              stable_integration=True, start_at_rest=False):
    '''Run a batch of experiments and print a summary table.'''
    import csv as _csv

    mode = 'dark' if light_intensity < 0 else 'light'
    if fixed_weights:
        kind = 'control'
    else:
        kind = 'continuous' if uniselector_type == 'continuous' else 'ashby'
    print(f'=== Batch (direct 2+2): {n_runs} runs, {mode}, {total_steps} ticks budget ===')
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
                         continuous_params=continuous_params,
                         fixed_weights=fixed_weights,
                         random_heading=random_heading,
                         random_start=random_start,
                         stable_integration=stable_integration,
                         start_at_rest=start_at_rest)
        elapsed = time.time() - t0
        r.pop('hom'); r.pop('backend')
        r['run'] = i + 1
        r['wall_time'] = elapsed
        results.append(r)
        print(f'  start=({r["start_x"]:.2f},{r["start_y"]:.2f}) hdg={r["start_heading"]:.0f} '
              f'sees_light={r["start_sees_light"]}  '
              f'final_dist={r["final_dist"]:.3f}  min_dist={r["min_dist"]:.3f}  '
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
    print(f'Light in view at start: {sum(1 for r in results if r["start_sees_light"])}/{n_runs}')

    if results:
        log_dir = os.path.dirname(results[0]['log_path'])
        csv_name = f'batch_direct_{kind}_{mode}_{time.strftime("%Y-%m-%d-%H-%M-%S")}.csv'
        csv_path = os.path.join(log_dir, csv_name)
        fields = ['run', 'seed', 'start_x', 'start_y', 'start_heading', 'start_dist',
                  'start_sees_light', 'final_dist', 'min_dist', 'min_t', 'steps_run',
                  'early_stopped', 'final_x', 'final_y', 'wall_time',
                  'log_path', 'json_path', 'state_log_path']
        with open(csv_path, 'w', newline='') as f:
            w = _csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(results)
        print(f'\nSummary saved to: {csv_path}')

    return results


def run_visualized(topology='fixed', fixed_weights=False, random_heading=False,
                   random_start=False, seed=None, uniselector_type='ashby'):
    '''Run the simplified 2+2 phototaxis experiment with the pyglet visualizer.'''
    import pyglet
    from pyglet.gl import (glEnable, glBlendFunc, glHint, glClearColor, glClear,
                           GL_BLEND, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
                           GL_LINE_SMOOTH, GL_LINE_SMOOTH_HINT, GL_NICEST,
                           GL_COLOR_BUFFER_BIT)
    from KheperaSimulator.KheperaSimulator import KheperaCamera

    if fixed_weights:
        mode_label = 'fixed weights'
    else:
        mode_label = 'fixed' if topology == 'fixed' else 'random'
    window = pyglet.window.Window(width=800, height=600, resizable=True,
                                  caption=f'Phototaxis Direct 2+2 ({mode_label})')

    glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glClearColor(0.55, 0.95, 1.0, 1.0)

    from Helpers.HomeostatConditionLogger import (
        log_homeostat_conditions, log_homeostat_conditions_json)

    hom, backend, seed = setup_phototaxis(topology=topology, seed=seed,
                                          uniselector_type=uniselector_type,
                                          fixed_weights=fixed_weights)
    sim = backend.kheperaSimulation
    robot = sim.allBodies['Khepera']
    target_pos = sim.allBodies['TARGET'].position
    if random_heading or random_start:
        set_start_pose(robot, *_random_start_pose(target_pos, random_start))
    exp_name = sim.experimentName

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
    trail_vlists = []
    trail_last = [None]
    TRAIL_MIN_DIST = 0.05

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

        dist = sqrt((rx - target_pos[0])**2 + (ry - target_pos[1])**2)
        window.set_caption(
            f'Phototaxis Direct 2+2 ({mode_label}) - t={state[0]}  speed={state[1]}  '
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

    total_steps = 60000
    if '--steps' in sys.argv:
        idx = sys.argv.index('--steps')
        if idx + 1 < len(sys.argv):
            total_steps = int(sys.argv[idx + 1])

    light_intensity = -100 if '--dark' in sys.argv else 100
    early_stop_distance = None
    if '--early-stop' in sys.argv:
        idx = sys.argv.index('--early-stop')
        if idx + 1 < len(sys.argv):
            early_stop_distance = float(sys.argv[idx + 1])
    elif '--dark' in sys.argv:
        early_stop_distance = 1.5

    n_batch = None
    if '--batch' in sys.argv:
        idx = sys.argv.index('--batch')
        if idx + 1 < len(sys.argv):
            n_batch = int(sys.argv[idx + 1])

    uniselector_type = 'continuous' if '--continuous' in sys.argv else 'ashby'

    state_log = '--state-log' in sys.argv
    state_log_interval = 1
    if '--log-interval' in sys.argv:
        idx = sys.argv.index('--log-interval')
        if idx + 1 < len(sys.argv):
            state_log_interval = int(sys.argv[idx + 1])

    seed = None
    if '--seed' in sys.argv:
        idx = sys.argv.index('--seed')
        if idx + 1 < len(sys.argv):
            seed = int(sys.argv[idx + 1])

    fixed_weights = '--fixed-weights' in sys.argv
    stable_integration = '--allow-unstable' not in sys.argv   # guard on by default
    start_at_rest = '--start-at-rest' in sys.argv
    random_start = '--random-start' in sys.argv
    random_heading = '--random-heading' in sys.argv
    if fixed_weights and ('--continuous' in sys.argv or '--random-topology' in sys.argv):
        print('Note: --fixed-weights ignores --continuous and --random-topology')

    if '--visualize' in sys.argv:
        run_visualized(topology=topology, fixed_weights=fixed_weights,
                       random_heading=random_heading, random_start=random_start,
                       seed=seed, uniselector_type=uniselector_type)
    elif n_batch is not None:
        run_batch(n_runs=n_batch, topology=topology,
                  total_steps=total_steps,
                  light_intensity=light_intensity,
                  early_stop_distance=early_stop_distance,
                  uniselector_type=uniselector_type,
                  fixed_weights=fixed_weights,
                  random_heading=random_heading, random_start=random_start,
                  stable_integration=stable_integration, start_at_rest=start_at_rest)
    else:
        run_headless(topology=topology, total_steps=total_steps,
                     light_intensity=light_intensity,
                     early_stop_distance=early_stop_distance,
                     uniselector_type=uniselector_type,
                     state_log=state_log,
                     state_log_interval=state_log_interval,
                     seed=seed, fixed_weights=fixed_weights,
                     random_heading=random_heading, random_start=random_start,
                     stable_integration=stable_integration, start_at_rest=start_at_rest)
