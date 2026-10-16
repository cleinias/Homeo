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
   Ignores --random-topology/--continuous.  Two kinds of motor:

   --motor newtonian (default): the homeostat's own motor units with frozen
      weights.  Motor dynamics: mass 1, viscosity 0, -0.9 self-connection, and
      a sigmoid from deviation to wheel speed.  NOT a Braitenberg vehicle: each motor is a second-order
      system, and the self-connection acts as a spring, not as damping, so
      with zero viscosity the motor is an undamped oscillator -- under a
      constant light the wheel speed swings every ~18 ticks.

   --motor aristotelian: a true Braitenberg vehicle, with no dynamics.
      Aristotelian units are first-order, x(t+1) = x(t) + torque / mass,
      and with mass ARIST_MASS = 0.1 and self-weight -1 the self-connection
      cancels x(t) exactly, so each motor's output equals its sensor's
      reading on the previous tick (times the connection's sign).  The
      wheel speed is linear in that output -- no sigmoid -- and its max is
      the same as the Newtonian vehicle's (max_speed_fraction of the range).
      Two constant units, Drive and Spin (output 1, no inputs), give it a
      resting drive and the spin as ordinary weighted inputs: a motor driven
      by an inhibitory connection also receives Drive with weight 1, so its
      output is 1 - s -- it races in the dark and comes to rest at full
      intensity, Braitenberg's Vehicle 3 (p. 10) -- and the spin is Spin's
      +-spin weights to the two motors.  6 units in all.


Options
-------
   The options both phototaxis experiments take (run length, batches, seed,
   --dark, uniselector, start pose, spin, eyes, stepping, stable draws...) are
   described in phototaxis_common.COMMON_OPTIONS_HELP.  This experiment's own:
   --fixed-weights      the non-adaptive vehicle (mode 3); ignores
                        --random-topology/--continuous
   --signs XY           its connections' signs, left eye first (default ++)
   --uncrossed          each eye drives its own side's motor (2a) instead of
                        the contra-lateral one (2b)
   --motor newtonian|aristotelian   its motors (default newtonian)

Usage
-----
    # Fixed-weight baseline, 20 runs from random start poses
    # (+ --motor aristotelian for the true Braitenberg vehicle)
    python -m HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct --fixed-weights --random-start --batch 20

    # The same with a slow clockwise baseline spin ("exploratory" mode)
    python -m HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct --fixed-weights --random-start --spin 0.05 --batch 20

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

from HomeoExperiments.KheperaExperiments import phototaxis_common as common
# Some of these only for the callers that import them from here
from HomeoExperiments.KheperaExperiments.phototaxis_common import (
    ACQUISITION_RADIUS, DEFAULT_START_RANGE, DEFAULT_ROBOT, STABILITY_MARGIN, TARGET_POS,
    seed_run, prepare_backend, experiment_suffix, set_light, configure_eyes,
    eye_tag, spin_tag, apply_spin, set_constant_input, set_start_pose,
    set_uniselector_type, uniselector_tag, randomize_unit, set_motor_response)
import random

import numpy as np


def setup_phototaxis(topology='fixed', backendSimulator=None,
                     mass_range=(1, 10), max_speed_fraction=0.8,
                     switching_rate=0.5, light_intensity=100,
                     uniselector_type='ashby', continuous_params=None,
                     seed=None, fixed_weights=False,
                     stable_draws=False, start_at_rest=False,
                     wiring='crossed', signs='++', spin=0.0, motor='newtonian',
                     eye_saturation=None, eye_threshold=None, eye_response=None,
                     robot=DEFAULT_ROBOT, simulator='box2d', rendering=False):
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
        wiring, signs:      with fixed_weights, which fixed-weight vehicle:
                            'crossed' (2b) or 'uncrossed' (2a), and the sign
                            of each sensor->motor connection, left eye first
                            ('++', '+-', '-+', '--').
        spin:               baseline spin, as a fraction of the motors' max
                            speed; > 0 clockwise (see apply_spin).
        eye_saturation, eye_threshold, eye_response: the eyes' sensitivity
                            (see configure_eyes); None keeps the default.
        robot:              the robot, a name in phototaxis_common.ROBOTS
                            (default the e-puck2).
        simulator, rendering: 'box2d' (default) or 'webots', and for Webots
                            whether to show its window (see
                            phototaxis_common.prepare_backend).
        motor:              with fixed_weights, 'newtonian' (default) or
                            'aristotelian' (the true Braitenberg vehicle; see
                            _direct_fixed_weights).
        stable_draws:       redraw each motor's (mass, viscosity) while
                            viscosity*dt/mass >= STABILITY_MARGIN; default
                            False, the full distribution (see phototaxis_common.randomize_unit).

    Returns:
        (hom, backend, seed)
    '''
    from Core.Homeostat import Homeostat
    from Core.HomeoUnit import HomeoUnit
    from RobotSimulator.HomeoUnitNewtonianTransduc import HomeoUnitNewtonianActuator
    from RobotSimulator.HomeoUnitNewtonianTransduc import HomeoUnitAristotelianActuator
    from RobotSimulator.HomeoUnitNewtonianTransduc import HomeoUnitInput
    from Simulator.HomeoExperiments import basicBraiten2Tranducers

    # Seed every generator before any stochastic initialization
    seed = seed_run(seed)

    if motor not in CONTROL_MOTORS:
        raise ValueError("motor must be one of %s, got %r" % (CONTROL_MOTORS, motor))
    if motor != 'newtonian' and not fixed_weights:
        raise ValueError("motor=%r applies only with fixed_weights" % motor)
    if fixed_weights:
        exp_name = ('phototaxis_braitenberg2_direct_control_'
                    + control_variant_name(wiring, signs, motor))
    elif topology == 'random':
        exp_name = 'phototaxis_braitenberg2_direct_random'
    else:
        exp_name = 'phototaxis_braitenberg2_direct_fixed'
    exp_name += experiment_suffix(light_intensity, uniselector_type, not fixed_weights,
                                  spin, eye_saturation, eye_threshold, eye_response,
                                  robot, simulator)
    backendSimulator = prepare_backend(backendSimulator, exp_name, robot, simulator,
                                       rendering)

    # --- Build the 4-unit homeostat ---
    world = 'kheperaBraitenberg2_HOMEO_World'
    transducers = basicBraiten2Tranducers(backendSimulator, world)
    set_light(backendSimulator, light_intensity, eye_saturation, eye_threshold, eye_response)

    hom = Homeostat()
    hom._host = backendSimulator.host
    hom._port = backendSimulator.port
    HomeoUnit.clearNames()

    rightWheel = transducers["rightWheelTransd"]
    leftWheel = transducers["leftWheelTransd"]
    leftSensorTransd = transducers["leftEyeTransd"]
    rightSensorTransd = transducers["rightEyeTransd"]

    # 2 motors + 2 sensor inputs (no eye intermediaries)
    motorClass = (HomeoUnitAristotelianActuator if motor == 'aristotelian'
                  else HomeoUnitNewtonianActuator)
    leftMotor = motorClass(transducer=leftWheel)
    rightMotor = motorClass(transducer=rightWheel)
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

    # The Aristotelian vehicle's two constant units (see add_constant_units).
    if fixed_weights and motor == 'aristotelian':
        add_constant_units(hom)

    # Disable all sensor connections (pure input transducers)
    leftSensor.uniselectorActive = False
    rightSensor.uniselectorActive = False
    for conn in leftSensor.inputConnections:
        conn.status = False
    for conn in rightSensor.inputConnections:
        conn.status = False

    # Apply topology-specific wiring
    kwargs = dict(mass_range=mass_range,
                  max_speed_fraction=max_speed_fraction,
                  switching_rate=switching_rate,
                  uniselector_type=uniselector_type,
                  continuous_params=continuous_params,
                  stable_draws=stable_draws,
                  start_at_rest=start_at_rest)
    if fixed_weights:
        _direct_fixed_weights(hom, max_speed_fraction=max_speed_fraction,
                              switching_rate=switching_rate,
                              wiring=wiring, signs=signs, motor=motor)
    elif topology == 'random':
        _direct_random_topology(hom, **kwargs)
    else:
        _direct_fixed_topology(hom, **kwargs)
    apply_spin(hom, spin)

    return hom, backendSimulator, seed


def _direct_fixed_topology(hom, mass_range=(1, 10),
                           max_speed_fraction=0.8, switching_rate=0.5,
                           uniselector_type='ashby', continuous_params=None,
                           stable_draws=False, start_at_rest=False):
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

        # Randomize unit parameters (see phototaxis_common.randomize_unit)
        randomize_unit(u, mass_range, stable_draws, start_at_rest)
        set_motor_response(u, max_speed_fraction, switching_rate)

        # Activate uniselector
        u.uniselectorActive = True
        set_uniselector_type(u, uniselector_type, continuous_params)

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



def _direct_random_topology(hom, mass_range=(1, 10),
                            max_speed_fraction=0.8, switching_rate=0.5,
                            uniselector_type='ashby', continuous_params=None,
                            stable_draws=False, start_at_rest=False):
    '''Random topology: all connections between the 2 motors are active
    (including inter-motor and from sensors).  The system must discover
    useful weights.

    Self-connections are still negative and manual-protected.
    '''
    for u in hom.homeoUnits:
        if 'Sensor' in u.name:
            continue

        randomize_unit(u, mass_range, stable_draws, start_at_rest)
        set_motor_response(u, max_speed_fraction, switching_rate)

        # Set all non-self connections active with random weights
        for conn in u.inputConnections[1:]:
            conn.newWeight(np.random.uniform(-0.1, 0.1))
            conn.noise = np.random.uniform(0, 0.1)
            conn.state = 'uniselector'
            conn.status = True

        # Activate uniselector
        u.uniselectorActive = True
        set_uniselector_type(u, uniselector_type, continuous_params)

        # Self-connection: negative (pass negative value to newWeight),
        # protected from uniselector
        u.inputConnections[0].newWeight(-np.random.uniform(0.01, 0.1))
        u.inputConnections[0].noise = np.random.uniform(0, 0.05)
        u.inputConnections[0].state = 'manual'
        u.inputConnections[0].status = True



# Fixed-weight vehicle parameters (the Newtonian motor; see _direct_fixed_weights)
CONTROL_CROSS_WEIGHT = 1.0    # sensor -> motor, magnitude (sign set by `signs`)
# Motor self-connection: with no viscosity a spring, not a damper -- the motor
# oscillates about its balance point at constant amplitude (the step is exact)
CONTROL_SELF_WEIGHT = -0.9
CONTROL_MASS = 1.0
CONTROL_VISCOSITY = 0.0


CONTROL_WIRINGS = ('crossed', 'uncrossed')
CONTROL_SIGNS = ('++', '+-', '-+', '--')
CONTROL_MOTORS = ('newtonian', 'aristotelian')

# The Aristotelian (Braitenberg) motor.  Its update is
#     x(t+1) = x(t) + (w s(t) + c out(t)) / m,   out = x / maxDeviation,
# so x(t) survives into x(t+1) with the factor 1 + c / (m maxDeviation).  The
# self-weight c is DERIVED from the mass and the deviation range to make that
# factor exactly 0 -- the unit then keeps no state, and x(t+1) = w s(t) / m,
# i.e. out(t+1) = w s(t).  Change the mass or the range and c follows; set c
# by hand and the memory silently comes back.  A connection weight must lie in
# [-1, 1], so with maxDeviation 10 the mass can be at most 0.1.
ARIST_MASS = 0.1


def aristotelian_self_weight(unit):
    "The self-weight that leaves an Aristotelian motor with no memory (see ARIST_MASS)."
    return -unit.mass * unit.maxDeviation


def _control_sensor_motor_pairs(wiring):
    '''(sensor, motor) pairs of the non-adaptive vehicle, LEFT EYE FIRST: the
    first character of `signs` applies to the left eye's connection, the second
    to the right eye's.  'crossed' is Braitenberg's 2b layout (each eye drives
    the contra-lateral motor), 'uncrossed' his 2a (each eye drives the motor on
    its own side).'''
    if wiring == 'crossed':
        return (('Left Sensor', 'Right Motor'), ('Right Sensor', 'Left Motor'))
    if wiring == 'uncrossed':
        return (('Left Sensor', 'Left Motor'), ('Right Sensor', 'Right Motor'))
    raise ValueError("wiring must be one of %s, got %r" % (CONTROL_WIRINGS, wiring))


def control_variant_name(wiring, signs, motor='newtonian'):
    '''Filename-safe tag for a non-adaptive variant, e.g. 'crossed_pm' for
    crossed +-, 'arist_crossed_pm' for the same with Aristotelian motors.  The
    Newtonian vehicle's names carry no motor tag.'''
    tag = '%s_%s' % (wiring, signs.replace('+', 'p').replace('-', 'm'))
    return 'arist_' + tag if motor == 'aristotelian' else tag


def _direct_fixed_weights(hom, max_speed_fraction=0.8, switching_rate=0.5,
                          wiring='crossed', signs='++', motor='newtonian'):
    '''Non-adaptive baseline: a fixed-weight Braitenberg 2 vehicle.

    Each sensor drives one motor with a fixed weight of magnitude
    CONTROL_CROSS_WEIGHT; inter-motor connections are off.  `wiring` chooses
    which motor ('crossed', 2b, the default; or 'uncrossed', 2a) and `signs`
    the sign of each connection, left eye first (see
    _control_sensor_motor_pairs): the default, crossed '++', is Braitenberg's
    2b ("aggression").  No uniselector, no noise and no random parameters, so
    a run depends only on the start pose.

    motor='newtonian': the homeostat's motor units, with mass 1, zero
    viscosity, a -0.9 self-connection and a sigmoid to wheel speed.  The self-connection acts as
    a spring, not as damping, so each motor is an undamped second-order
    oscillator (see the module docstring).

    motor='aristotelian': Aristotelian motor units with mass ARIST_MASS and the
    self-weight that cancels their state (aristotelian_self_weight), so each
    motor's output is its sensor's previous reading times the connection's
    sign, and the wheel speed is linear in it.  This is Braitenberg's vehicle.

    Either way motors start at zero deviation (zero wheel speed), so the robot
    does not move until an eye sees the light (or a spin turns it).
    '''
    for u in hom.homeoUnits:
        if 'Sensor' in u.name:
            u.noise = 0
            continue
        if u.name in CONSTANT_UNITS:
            continue                    # set up by add_constant_units

        u.mass = ARIST_MASS if motor == 'aristotelian' else CONTROL_MASS
        u.viscosity = CONTROL_VISCOSITY
        u.noise = 0
        u.uniselectorActive = False
        u.criticalDeviation = 0.0
        u._maxSpeedFraction = max_speed_fraction
        if motor == 'newtonian':
            u._switchingRate = switching_rate
            u._maxSpeed = None  # force recalculation from new fraction

        for conn in u.inputConnections[1:]:
            conn.status = False
        u.inputConnections[0].newWeight(aristotelian_self_weight(u) if motor == 'aristotelian'
                                        else CONTROL_SELF_WEIGHT)
        u.inputConnections[0].noise = 0
        u.inputConnections[0].state = 'manual'
        u.inputConnections[0].status = True

    if signs not in CONTROL_SIGNS:
        raise ValueError("signs must be one of %s, got %r" % (CONTROL_SIGNS, signs))
    units = {u.name: u for u in hom.homeoUnits}
    for (sensor, motorName), sign in zip(_control_sensor_motor_pairs(wiring), signs):
        weight = CONTROL_CROSS_WEIGHT if sign == '+' else -CONTROL_CROSS_WEIGHT
        matches = [c for c in units[motorName].inputConnections
                   if c.incomingUnit.name == sensor]
        if len(matches) != 1:
            raise RuntimeError('expected one %s -> %s connection, found %d'
                               % (sensor, motorName, len(matches)))
        conn = matches[0]
        conn.newWeight(weight)
        conn.noise = 0
        conn.state = 'manual'
        conn.status = True
        # Braitenberg's inhibition slows a motor down from a resting drive
        # (Vehicle 3, p. 10): the Drive unit supplies it, so that the motor's
        # output is DRIVE_WEIGHT - s, and it comes to rest at full intensity.
        # An excitatory motor has no drive: output s, at rest in the dark.
        if motor == 'aristotelian' and sign == '-':
            set_constant_input(units[motorName], 'Drive', DRIVE_WEIGHT)


# The Aristotelian vehicle's constant units: no inputs, deviation held at the
# maximum, so output 1 for the whole run (an Aristotelian unit with zero torque
# keeps its deviation: x(t+1) = x(t)).  Drive gives an inhibited motor its
# resting speed, Spin the baseline spin.  Two units, not one, because a motor
# that is both inhibited and spun would need a single weight of 1 + spin, and
# weights must lie in [-1, 1].  With DRIVE_WEIGHT 1 such a motor's output in
# the dark, 1 + spin, is clipped at the deviation limit, so for an inhibited
# vehicle in the dark the spin is half as strong (only the other wheel slows).
CONSTANT_UNITS = ('Drive', 'Spin')
DRIVE_WEIGHT = 1.0


def add_constant_units(hom):
    '''Add the Drive and Spin units, both with output 1 and every connection
    into or out of them off.  Creating units and connections draws from
    np.random, so its state is saved and restored: the draws a seed makes
    afterwards do not depend on whether these units exist.  (The start pose
    is not among them: it comes from the environment's own stream.)'''
    from Core.HomeoUnitAristotelian import HomeoUnitAristotelian
    np_state, py_state = np.random.get_state(), random.getstate()
    try:
        for name in CONSTANT_UNITS:
            unit = HomeoUnitAristotelian()
            hom.addFullyConnectedUnit(unit)
            unit.name = name
            unit.uniselectorActive = False
            unit.noise = 0
            for conn in unit.inputConnections:
                conn.status = False
                conn.noise = 0
            unit.criticalDeviation = unit.maxDeviation
            unit.computeOutput()
        for u in hom.homeoUnits:
            for conn in u.inputConnections:
                if conn.incomingUnit.name in CONSTANT_UNITS:
                    conn.status = False
    finally:
        np.random.set_state(np_state)
        random.setstate(py_state)



def _setup(fixed_weights=False, wiring='crossed', signs='++', motor='newtonian', **kwargs):
    "setup_phototaxis bound to its arguments, and the run's title and extra record fields."
    def setup():
        return setup_phototaxis(fixed_weights=fixed_weights, wiring=wiring, signs=signs,
                                motor=motor, **kwargs)
    if fixed_weights:
        label = 'fixed weights, no uniselector, %s motors, %s %s' % (motor, wiring, signs)
    else:
        label = '%s topology, %s uniselector' % (kwargs.get('topology', 'fixed'),
                                                 kwargs.get('uniselector_type', 'ashby'))
    extra = dict(wiring=wiring if fixed_weights else '',
                 signs=signs if fixed_weights else '',
                 motor=motor if fixed_weights else '')
    return setup, 'Braitenberg 2 Direct 2+2 (%s)' % label, extra


def run_headless(topology='fixed', total_steps=60000, report_interval=500,
                 light_intensity=100, early_stop_distance=None, quiet=False,
                 uniselector_type='ashby', continuous_params=None,
                 state_log=False, state_log_interval=1, seed=None, env_seed=None, heading=None,
                 fixed_weights=False, random_heading=False, random_start=False,
                 stable_draws=False, start_at_rest=False,
                 wiring='crossed', signs='++', start_range=DEFAULT_START_RANGE,
                 spin=0.0, motor='newtonian', eye_saturation=None, eye_threshold=None,
                 eye_response=None, robot=DEFAULT_ROBOT, simulator='box2d', rendering=False):
    '''Run the simplified 2+2 phototaxis experiment headless
    (phototaxis_common.run_headless, which describes the result).

    The setup's parameters are setup_phototaxis's; the others:
        total_steps, report_interval: run length, and ticks between reports.
        early_stop_distance: stop once this close to the light.
        quiet:          no per-report output (batch mode).
        state_log, state_log_interval: a per-tick .statelog, every N ticks.
        random_heading: start with a random heading, drawn from the
                        environment's stream.
        random_start:   random heading and position start_range units from
                        the light (default 2-6).
        heading:        a FIXED start heading in degrees, used when neither
                        random_heading nor random_start is set.
        env_seed:       the environment's seed (default: seed).  No pose draws
                        from the homeostat's stream, so a seed yields the same
                        homeostat, noise included, whatever the start pose --
                        which is what lets two batches differing only in
                        geometry be compared pairwise.
    The result also has wiring, signs and motor ('' unless fixed_weights).
    '''
    setup, title, extra = _setup(
        topology=topology, light_intensity=light_intensity,
        uniselector_type=uniselector_type, continuous_params=continuous_params,
        seed=seed, fixed_weights=fixed_weights, stable_draws=stable_draws,
        start_at_rest=start_at_rest, wiring=wiring, signs=signs, spin=spin,
        motor=motor, eye_saturation=eye_saturation, eye_threshold=eye_threshold,
        eye_response=eye_response, robot=robot, simulator=simulator, rendering=rendering)
    return common.run_headless(
        setup, title, total_steps=total_steps, report_interval=report_interval,
        light_intensity=light_intensity, early_stop_distance=early_stop_distance,
        quiet=quiet, state_log=state_log, state_log_interval=state_log_interval,
        heading=heading, random_heading=random_heading, random_start=random_start,
        start_range=start_range, stable_draws=stable_draws,
        eye_saturation=eye_saturation, spin=spin, env_seed=env_seed, extra=extra)


def run_batch(n_runs=10, topology='fixed', total_steps=2000000,
              report_interval=500, light_intensity=100,
              early_stop_distance=None,
              uniselector_type='ashby', continuous_params=None,
              fixed_weights=False, random_heading=False, random_start=False,
              stable_draws=False, start_at_rest=False, seed=None, env_seed=None,
              batch_vary='both',
              state_log=False, state_log_interval=1, heading=None,
              wiring='crossed', signs='++', start_range=DEFAULT_START_RANGE,
              spin=0.0, motor='newtonian', eye_saturation=None, eye_threshold=None,
              eye_response=None, robot=DEFAULT_ROBOT, simulator='box2d', rendering=False):
    '''Run a batch of experiments and print a summary table
    (phototaxis_common.run_batch).

    With seed given, run i uses seed+i, so the batch is reproducible and an
    array job can pin exactly one run per task with --batch 1 --seed N;
    env_seed and batch_vary: see phototaxis_common.batch_seeds.'''
    if fixed_weights:
        variant = 'control_' + control_variant_name(wiring, signs, motor)
    else:
        variant = uniselector_tag(uniselector_type)
    kind = common.batch_kind(variant, spin, eye_saturation, eye_threshold, eye_response,
                             stable_draws and not fixed_weights, robot, simulator)

    def run_one(run_seed, run_env_seed):
        return run_headless(topology=topology, total_steps=total_steps,
                            report_interval=report_interval,
                            light_intensity=light_intensity,
                            early_stop_distance=early_stop_distance,
                            quiet=True,
                            uniselector_type=uniselector_type,
                            continuous_params=continuous_params,
                            fixed_weights=fixed_weights,
                            random_heading=random_heading,
                            random_start=random_start,
                            stable_draws=stable_draws,
                            start_at_rest=start_at_rest,
                            state_log=state_log,
                            state_log_interval=state_log_interval,
                            heading=heading,
                            wiring=wiring, signs=signs, start_range=start_range,
                            spin=spin, motor=motor, eye_saturation=eye_saturation,
                            eye_threshold=eye_threshold, eye_response=eye_response,
                            robot=robot, simulator=simulator, rendering=rendering,
                            seed=run_seed, env_seed=run_env_seed)
    return common.run_batch(run_one, n_runs, 'direct', kind,
                            light_intensity=light_intensity, total_steps=total_steps,
                            seed=seed, env_seed=env_seed,
                            vary=batch_vary)


def run_visualized(topology='fixed', fixed_weights=False, random_heading=False,
                   random_start=False, seed=None, env_seed=None, uniselector_type='ashby',
                   spin=0.0, motor='newtonian', light_intensity=100, heading=None,
                   start_range=DEFAULT_START_RANGE, stable_draws=False,
                   start_at_rest=False, wiring='crossed', signs='++',
                   eye_saturation=None, eye_threshold=None, eye_response=None,
                   robot=DEFAULT_ROBOT, simulator='box2d', rendering=False, continuous_params=None):
    '''Run the simplified 2+2 phototaxis experiment with the pyglet
    visualizer, with the same options as run_headless.'''
    setup, title, _ = _setup(
        topology=topology, light_intensity=light_intensity,
        uniselector_type=uniselector_type, continuous_params=continuous_params,
        seed=seed, fixed_weights=fixed_weights, stable_draws=stable_draws,
        start_at_rest=start_at_rest, wiring=wiring, signs=signs, spin=spin,
        motor=motor, eye_saturation=eye_saturation, eye_threshold=eye_threshold,
        eye_response=eye_response, robot=robot, simulator=simulator, rendering=rendering)
    common.run_visualized(setup, 'Phototaxis ' + title, light_intensity=light_intensity,
                          stable_draws=stable_draws, random_heading=random_heading,
                          random_start=random_start, heading=heading,
                          start_range=start_range, env_seed=env_seed)


def main(argv):
    o = common.parse_common_args(argv, flags=('--fixed-weights', '--uncrossed'),
                                 valued={'--signs': 1, '--motor': 1})
    fixed_weights = '--fixed-weights' in argv
    if fixed_weights and ('--continuous' in argv or '--random-topology' in argv):
        print('Note: --fixed-weights ignores --continuous and --random-topology')
    # --signs XY / --uncrossed: which fixed-weight vehicle (only with
    # --fixed-weights).  X is the sign of the left eye's connection, Y the right
    # eye's; --uncrossed wires each eye to its own side's motor (2a) instead of
    # the contra-lateral one (2b).
    signs = '++'
    if '--signs' in argv:
        idx = argv.index('--signs')
        signs = argv[idx + 1] if idx + 1 < len(argv) else ''
        if signs not in CONTROL_SIGNS:
            raise SystemExit('--signs must be one of %s, got %r'
                             % (' '.join(CONTROL_SIGNS), signs))
    wiring = 'uncrossed' if '--uncrossed' in argv else 'crossed'
    if not fixed_weights and ('--signs' in argv or '--uncrossed' in argv):
        raise SystemExit('--signs and --uncrossed apply only with --fixed-weights')
    # --motor newtonian|aristotelian: the fixed-weight vehicle's motors.
    motor = 'newtonian'
    if '--motor' in argv:
        idx = argv.index('--motor')
        motor = argv[idx + 1] if idx + 1 < len(argv) else ''
        if motor not in CONTROL_MOTORS:
            raise SystemExit('--motor must be one of %s, got %r'
                             % (' '.join(CONTROL_MOTORS), motor))
        if not fixed_weights:
            raise SystemExit('--motor applies only with --fixed-weights')

    vehicle = dict(fixed_weights=fixed_weights, wiring=wiring, signs=signs, motor=motor)
    setup_options = common.pick(o, common.SETUP_OPTIONS)
    if o['visualize']:
        run_visualized(**setup_options, **common.pick(o, common.POSE_OPTIONS), **vehicle)
    else:
        run_options = dict(setup_options, **common.pick(o, common.RUN_OPTIONS))
        if o['n_batch'] is not None:
            run_batch(n_runs=o['n_batch'], batch_vary=o['batch_vary'], **run_options, **vehicle)
        else:
            run_headless(**run_options, **vehicle)


if __name__ == '__main__':
    import sys
    main(sys.argv)
