'''
What the phototaxis experiments share: seeding, the world and its light, the
eyes, the uniselectors, the random unit parameters, the start pose, the
baseline spin, and the runners (headless, batch, visualizer) with their
records and command-line options.

phototaxis_braitenberg2_direct (the 2+2 vehicle) and
phototaxis_braitenberg2_Ashby (the 6-unit vehicle) only build their
homeostats; everything else is here, so that a fix reaches both.  Until 13
Oct 2026 each script had its own copy, and fixes reached only the direct one
(review finding RE-06): the Ashby runs had no seed in batches, no run tag in
their file names, no stepping or stability options, and tagged nothing in
their batch files.

The command-line options both experiments take are listed in
COMMON_OPTIONS_HELP.

@author: stefano
'''

from Helpers.General_Helper_Functions import (unique_stem, run_tag, RUN_LOG_EXTENSIONS,
                                              report_ticks)
import os
import random
import time
import threading
from math import sqrt, degrees, atan2

import numpy as np

# The light's position in kheperaBraitenberg2_HOMEO_World
TARGET_POS = (7, 7)

# A vehicle has "acquired" the source once it comes this close to it.
ACQUISITION_RADIUS = 1.0

DEFAULT_START_RANGE = (2.0, 6.0)

UNISELECTOR_TYPES = ('ashby', 'random', 'continuous')


# --- Seeding and the world ----------------------------------------------------

def seed_run(seed=None):
    '''Seed numpy's, Python's and numba's generators; draw a seed from
    os.urandom if none is given.  Numba keeps a separate random state that
    np.random.seed() does not reach: without seeding it the trajectory is not
    reproducible from the seed (SH-03, RE-05).  Returns the seed.'''
    from Core.HomeoJIT import seed_jit_rng
    if seed is None:
        seed = int.from_bytes(os.urandom(4), 'big')
    np.random.seed(seed)
    random.seed(seed)
    seed_jit_rng(seed)
    return seed


def prepare_backend(backendSimulator, experiment_name, synchronous_stepping=True):
    '''The run's backend (a new SimulatorBackendHOMEO if None), stepping as
    asked, writing to today's SimsData directory under experiment_name.
    synchronous_stepping: advance the world once per tick, after all units
    have updated (default), or, if False, once per motor command, as runs
    before 13 Oct 2026 did (see KheperaSimulation).'''
    from Simulator.SimulatorBackend import SimulatorBackendHOMEO
    from Helpers.General_Helper_Functions import simulations_data_dir

    if backendSimulator is None:
        backendSimulator = SimulatorBackendHOMEO(lock=threading.Lock(), robotName='Khepera',
                                                 synchronousStepping=synchronous_stepping)
    else:
        backendSimulator.kheperaSimulation.synchronousStepping = synchronous_stepping

    log_dir = os.path.join(simulations_data_dir(), 'SimsData-' + time.strftime("%Y-%m-%d"))
    os.makedirs(log_dir, exist_ok=True)
    backendSimulator.kheperaSimulation.dataDir = log_dir
    backendSimulator.kheperaSimulation.experimentName = experiment_name
    return backendSimulator


def experiment_suffix(light_intensity=100, uniselector_type='ashby', adaptive=True,
                      spin=0.0, eye_saturation=None, eye_threshold=None, eye_response=None):
    "The experiment name's tags: '_dark', the uniselector if not Ashby's, spin, eyes."
    suffix = '_dark' if light_intensity < 0 else ''
    if adaptive and uniselector_type != 'ashby':
        suffix += '_' + uniselector_tag(uniselector_type)
    return suffix + spin_tag(spin) + eye_tag(eye_saturation, eye_threshold, eye_response)


def set_light(backend, light_intensity, eye_saturation=None, eye_threshold=None,
              eye_response=None):
    '''Set the light's intensity, then the eyes, whose saturation is computed
    from it (RE-11), and keep the eyes as configured, (I0, Isat, response), in
    the simulation's eyeConfig for the run's records.  Call once the world
    exists.'''
    if light_intensity != 100:
        target_body = backend.kheperaSimulation.allBodies['TARGET']
        target_body.userData['intensity'] = light_intensity
        target_body.userData['lightIntensity'] = light_intensity
    backend.kheperaSimulation.eyeConfig = configure_eyes(
        backend, eye_saturation, eye_threshold, eye_response)


# --- The eyes -------------------------------------------------------------------

def eye_tag(saturation=None, threshold=None, response=None):
    "Filename tag for non-default eyes, e.g. '_log_sat0.5'; '' for the default eyes."
    tag = '_log' if response == 'log' else ''
    if saturation is not None:
        tag += '_sat%g' % saturation
    if threshold is not None:
        tag += '_thr%g' % threshold
    return tag


def configure_eyes(backend, saturation=None, threshold=None, response=None):
    """Set both eyes' sensitivity (KheperaRobot.setEyeSensitivity).

    saturation: a DISTANCE -- the eye saturates at `saturation` units from the
                light, on its axis: Isat = intensity / saturation^2 (the light
                has no ambient part and purely quadratic attenuation,
                KheperaWorldLightDef's defaults, which is checked).
    threshold:  an irradiance, I0.  A log eye needs one > 0 and gets 1 if none
                is given, so that it stops seeing an intensity-100 light 10
                units away -- as far as the old eyes' distance cut-off.
    response:   'linear' or 'log'.
    None leaves a setting at the eye's default (linear, I0 = 0, Isat = 100).
    Returns the eyes' (threshold, saturation irradiance, response)."""
    sim = backend.kheperaSimulation
    robot = sim.allBodies['Khepera']
    target = sim.allBodies['TARGET']
    Isat = None
    if saturation is not None:
        if not saturation > 0:
            raise ValueError('eye saturation distance must be > 0, got %r' % saturation)
        if tuple(target.userData['attenVec']) != (0, 0, 1) or target.userData['ambRatio'] != 0:
            raise ValueError('configure_eyes assumes purely quadratic attenuation and no ambient light')
        Isat = abs(target.userData['intensity']) / saturation ** 2
    if response == 'log' and threshold is None:
        threshold = 1.0
    for eye in ('leftEye', 'rightEye'):
        robot.setEyeSensitivity(eye, threshold=threshold, saturation=Isat, response=response)
    ud = robot.sensors['leftEye'].userData
    return ud['leftEyeThreshold'], ud['leftEyeSaturation'], ud['leftEyeResponse']


# --- Uniselectors and random unit parameters ---------------------------------

def set_uniselector_type(unit, uniselector_type, continuous_params=None):
    '''Set the uniselector on a unit: 'ashby' (the stepping switch, already
    every new unit's), 'random' (uniform random) or 'continuous' (the OU
    process; continuous_params overrides its parameters).  Any other type is
    an error: it used to leave the Ashby uniselector in place silently.'''
    from Core.HomeoUniselectorContinuous import HomeoUniselectorContinuous
    from Core.HomeoUniselectorUniformRandom import HomeoUniselectorUniformRandom

    if uniselector_type == 'continuous':
        unis = HomeoUniselectorContinuous()
        if continuous_params:
            for key, val in continuous_params.items():
                setattr(unis, key, val)
        unit.uniselector = unis
    elif uniselector_type == 'random':
        unit.uniselector = HomeoUniselectorUniformRandom()
    elif uniselector_type != 'ashby':
        raise ValueError("uniselector_type must be one of %s, got %r"
                         % (UNISELECTOR_TYPES, uniselector_type))


def uniselector_tag(uniselector_type):
    "The uniselector's tag in file names: its type (batch files called 'random' 'ashby')."
    if uniselector_type not in UNISELECTOR_TYPES:
        raise ValueError("uniselector_type must be one of %s, got %r"
                         % (UNISELECTOR_TYPES, uniselector_type))
    return uniselector_type


# --- Numerical-integration stability -----------------------------------------
#
# The Newtonian needle used to be integrated explicitly: with zero torque the
# velocity recursion was
#       v <- v * (1 - viscosity * dt_fast / mass)
# so the step was stable only while  viscosity * dt_fast / mass < 2.  Outside
# that bound the needle diverged to its limit within a few dozen ticks with no
# sensory input at all, which looked like -- but was not -- a saturated unit.
# Random (mass, viscosity) draws violated this in 9 of the 20 runs of
# 2026-09-30; see "Bimodal acquisition in OU chemotaxis".
# HomeoJIT._jit_needle_position_newtonian now takes the exact step, stable for
# any ratio (Homeo 1257d58), so the guard is no longer needed for the
# numerics, and since 13 Oct 2026 it is off: (mass, viscosity) come from
# their full distribution, the one the Ashby experiment always used.
# --stable-draws (stable_draws=True) restores it, to reproduce earlier runs of
# the direct experiment; runs and batch files record which was used.
STABILITY_MARGIN = 1.8          # with stable_draws, keep viscosity*dt/mass below this


def integration_ratio(unit):
    "viscosity * dt_fast / mass (the old explicit step needed it below 2)."
    dt = getattr(unit, '_dt_fast', 1.0)
    return unit.viscosity * dt / unit.mass if unit.mass else float('inf')


def randomize_unit(u, mass_range, stable_draws=False, start_at_rest=False, max_tries=200):
    """setRandomValues() + a mass uniform in mass_range (setRandomValues leaves
    it at the sluggish default of 100).

    With stable_draws (the default of the direct experiment's runs before 13
    Oct 2026) the (mass, viscosity) pair is resampled until
    viscosity*dt_fast/mass < STABILITY_MARGIN, the bound the old explicit
    integrator needed: the original joint distribution conditioned on that
    bound.  With start_at_rest the needle starts centred and motionless, so
    the vehicle begins stationary instead of mid-manoeuvre.
    """
    for _ in range(max_tries):
        u.setRandomValues()
        u.mass = np.random.uniform(*mass_range)
        if not stable_draws or integration_ratio(u) < STABILITY_MARGIN:
            break
    else:
        u.viscosity = STABILITY_MARGIN * u.mass / getattr(u, '_dt_fast', 1.0)
    if start_at_rest:
        u.criticalDeviation = 0.0
        u.currentOutput = 0.0
        u._currentVelocity = 0.0
        u._lastAcceleration = 0.0


def set_motor_response(u, max_speed_fraction, switching_rate):
    '''A motor's fraction of the wheel speed range and the steepness of its
    sigmoid.  The actuator's defaults, 0.2 and 0.1, left a robot with random
    parameters nearly immobile: speeds in a tiny band, and almost none for a
    moderate deviation.'''
    u._maxSpeedFraction = max_speed_fraction
    u._switchingRate = switching_rate
    u._maxSpeed = None  # force recalculation from new fraction


# --- Baseline spin ------------------------------------------------------------

def spin_tag(spin):
    "Filename tag for a baseline spin: '' for none, else e.g. '_cw0.05'."
    if not spin:
        return ''
    return '_%s%g' % ('cw' if spin > 0 else 'ccw', abs(spin))


def set_constant_input(motor, source, weight):
    "Connect a constant unit to a motor with a fixed, noiseless weight."
    conn = [c for c in motor.inputConnections if c.incomingUnit.name == source][0]
    conn.newWeight(weight)
    conn.noise = 0
    conn.state = 'manual'
    conn.status = True


def apply_spin(hom, spin):
    '''Give the vehicle a baseline spin in place: a constant offset of
    +spin x max speed on the left wheel and -spin x max speed on the right,
    added to the speed each motor commands (HomeoUnitNewtonianActuator's
    _speedBias).  spin > 0 turns the vehicle clockwise -- its heading
    decreases -- and spin < 0 counter-clockwise.  The offset is independent
    of the network, so with no light in view the vehicle turns at a constant
    rate, and with the light in view the offset adds to the light-driven
    steering.

    A vehicle with a Spin unit (the direct experiment's Aristotelian one)
    gets the same offset as a network input instead: Spin (output 1) feeds the
    motors with weights +spin and -spin, which for its memoryless, linear
    motors is the same wheel speed.'''
    units = {u.name: u for u in hom.homeoUnits}
    if 'Spin' in units:
        if spin:
            set_constant_input(units['Left Motor'], 'Spin', spin)
            set_constant_input(units['Right Motor'], 'Spin', -spin)
        return
    units['Left Motor']._speedBias = spin
    units['Right Motor']._speedBias = -spin


# --- The start pose -----------------------------------------------------------

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


def random_start_pose(target_pos, random_position, start_range=DEFAULT_START_RANGE):
    '''Draw a start pose from np.random (so it follows the run's seed):
    a uniform heading, and if random_position, a position at a uniform
    distance within start_range (default 2-6 units) and uniform bearing
    from the light.
    Returns (x, y, heading); x and y are None when not randomised.'''
    heading = np.random.uniform(0, 360)
    if not random_position:
        return None, None, heading
    d = np.random.uniform(*start_range)
    bearing = np.random.uniform(0, 2 * np.pi)
    return (target_pos[0] + d * np.cos(bearing),
            target_pos[1] + d * np.sin(bearing), heading)


def place_robot(robot, random_heading=False, random_start=False, heading=None,
                start_range=DEFAULT_START_RANGE):
    '''The start pose: random (heading, or heading and position, drawn from
    the run's seed), a fixed heading (draws nothing, so a seed yields the same
    homeostat whatever the heading), or as the world placed it.'''
    if random_heading or random_start:
        set_start_pose(robot, *random_start_pose(TARGET_POS, random_start, start_range))
    elif heading is not None:
        set_start_pose(robot, heading=heading)


# --- Runners ------------------------------------------------------------------

def _start_logs(hom, backend, seed, settings):
    "Log the initial conditions; returns (log_path, json_path, stem)."
    from Helpers.HomeostatConditionLogger import (
        log_homeostat_conditions, log_homeostat_conditions_json)
    sim = backend.kheperaSimulation
    exp_name = sim.experimentName
    timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")
    stem = unique_stem(sim.dataDir, exp_name + '-' + timestamp + run_tag(),
                       RUN_LOG_EXTENSIONS)
    log_path = os.path.join(sim.dataDir, stem + '.log')
    json_path = os.path.join(sim.dataDir, stem + '.json')
    log_homeostat_conditions(hom, log_path, 'INITIAL CONDITIONS', exp_name)
    log_homeostat_conditions_json(hom, json_path, 'INITIAL CONDITIONS', exp_name,
                                  seed=seed, settings=settings)
    return log_path, json_path, stem


def _end_logs(hom, log_path, json_path):
    from Helpers.HomeostatConditionLogger import (
        log_homeostat_conditions, log_homeostat_conditions_json)
    log_homeostat_conditions(hom, log_path, 'FINAL CONDITIONS')
    log_homeostat_conditions_json(hom, json_path, 'FINAL CONDITIONS')


def run_settings(backend, light_intensity, stable_draws):
    "The settings every run records in its JSON."
    eye_config = backend.kheperaSimulation.eyeConfig
    return dict(stable_draws=stable_draws,
                synchronous_stepping=backend.kheperaSimulation.synchronousStepping,
                light_intensity=light_intensity,
                eye_threshold=eye_config[0],
                eye_saturation_irradiance=eye_config[1],
                eye_response=eye_config[2])


def run_headless(setup, title, total_steps=60000, report_interval=500,
                 light_intensity=100, early_stop_distance=None, quiet=False,
                 state_log=False, state_log_interval=1, heading=None,
                 random_heading=False, random_start=False,
                 start_range=DEFAULT_START_RANGE, stable_draws=False,
                 eye_saturation=None, spin=0.0, extra=None):
    '''Run a phototaxis experiment headless.

    setup:   a function of no arguments that builds the experiment and returns
             (hom, backend, seed) -- an experiment's setup_phototaxis with its
             arguments bound.
    title:   the run's description, printed in the header.
    extra:   experiment-specific fields of the result (e.g. the fixed-weight
             vehicle's wiring).
    The other arguments are described in COMMON_OPTIONS_HELP; light_intensity,
    stable_draws, eye_saturation and spin must be the ones setup uses, since
    they are recorded.

    Returns a dict: hom, backend, final_dist, min_dist, min_t, steps_run,
    final_x, final_y, early_stopped, log_path, json_path, state_log_path,
    seed, start_x, start_y, start_heading, start_dist, start_sees_light (did
    either eye see the light at the start), first_acq (the first report tick
    within ACQUISITION_RADIUS of the light, or None), acquired, final_speed,
    final_bearing, the eyes as configured, spin, synchronous_stepping,
    stable_draws, and the extra fields.
    '''
    hom, backend, seed = setup()
    sim = backend.kheperaSimulation
    robot = sim.allBodies['Khepera']
    target_pos = TARGET_POS
    place_robot(robot, random_heading, random_start, heading, start_range)
    start_x, start_y = robot.body.position[0], robot.body.position[1]
    start_heading = degrees(robot.body.angle) % 360
    start_dist = sqrt((start_x - target_pos[0])**2 + (start_y - target_pos[1])**2)
    start_sees_light = (robot.getSensorRead('leftEye') != 0 or
                        robot.getSensorRead('rightEye') != 0)

    # Headless: no per-tick sleep, no in-memory data (the initial and final
    # states go to the log files)
    hom.slowingFactor = 0
    hom.collectsData = False
    hom._headless = True
    for u in hom.homeoUnits:
        u._headless = True

    eye_config = sim.eyeConfig
    log_path, json_path, stem = _start_logs(
        hom, backend, seed, run_settings(backend, light_intensity, stable_draws))

    # Optional per-tick state logger
    state_log_path = None
    if state_log:
        from Helpers.HomeostatStateLogger import HomeostatStateLogger
        state_log_path = os.path.join(sim.dataDir, stem + '.statelog')
        state_logger = HomeostatStateLogger(
            hom, sim, state_log_path, log_interval=state_log_interval, seed=seed)
        state_logger.log_tick(0)
        hom._state_logger = state_logger

    def dist_to_target():
        rx, ry = robot.body.position[0], robot.body.position[1]
        return sqrt((rx - target_pos[0])**2 + (ry - target_pos[1])**2)

    if spin:
        title += ', spin %g %s' % (abs(spin), 'CW' if spin > 0 else 'CCW')
    if not quiet:
        print(f'=== Phototaxis: {title} ===')
        print(f'Seed: {seed}')
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
    '''Time of first acquisition: the tick at which the vehicle first comes
       within ACQUISITION_RADIUS of the target.  Recorded here rather than
       reconstructed from the .traj afterwards, which is what the 2026-09-30
       analysis had to do.  None if it never acquires.'''
    first_acq = None
    rx, ry = robot.body.position[0], robot.body.position[1]
    prev_x, prev_y, prev_tick = rx, ry, 0

    target_tick = 0
    for target_tick in report_ticks(report_interval, total_steps):
        prev_x, prev_y = rx, ry
        prev_tick = hom.time
        hom.runFor(target_tick)
        rx, ry = robot.body.position[0], robot.body.position[1]
        d = dist_to_target()
        a = degrees(robot.body.angle) % 360
        lsensor = robot.getSensorRead('leftEye')
        rsensor = robot.getSensorRead('rightEye')

        if d < min_dist:
            min_dist = d
            min_t = target_tick
        if first_acq is None and d < ACQUISITION_RADIUS:
            first_acq = target_tick

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
    '''How the run ends, which "acquired" alone cannot tell: Braitenberg's
       Aggressor hits the source at speed, his Love vehicle comes to rest near
       it facing it, his Explorer comes to rest facing away.
       final_speed: distance covered over the last report interval (the
       last stretch, if shorter), per tick.
       final_bearing: where the light is relative to the heading, in degrees,
       0 = straight ahead, +-180 = straight behind, > 0 to the left.'''
    final_speed = (sqrt((final_x - prev_x)**2 + (final_y - prev_y)**2)
                   / max(1, target_tick - prev_tick))
    final_bearing = (degrees(atan2(target_pos[1] - final_y, target_pos[0] - final_x)
                             - robot.body.angle) + 180) % 360 - 180

    if not quiet:
        print()
        print(f'Closest approach: {min_dist:.3f} at t={min_t}')
        print(f'Final distance:   {final_dist:.3f}')

    sim.saveTrajectory()

    if state_log and hom._state_logger is not None:
        hom._state_logger.close()
        hom._state_logger = None

    _end_logs(hom, log_path, json_path)

    result = dict(hom=hom, backend=backend,
                  final_dist=final_dist, min_dist=min_dist, min_t=min_t,
                  steps_run=steps_run, final_x=final_x, final_y=final_y,
                  early_stopped=early_stopped,
                  log_path=log_path, json_path=json_path,
                  state_log_path=state_log_path, seed=seed,
                  start_x=start_x, start_y=start_y, start_heading=start_heading,
                  start_dist=start_dist, start_sees_light=start_sees_light,
                  first_acq=first_acq, acquired=first_acq is not None,
                  # The eyes as configured, not as asked: a log eye's default
                  # threshold is 1, not 0 (RE-11)
                  eye_response=eye_config[2],
                  eye_threshold=eye_config[0],
                  eye_saturation='' if eye_saturation is None else eye_saturation,
                  eye_saturation_irradiance=eye_config[1],
                  final_speed=final_speed, final_bearing=final_bearing,
                  spin=spin, synchronous_stepping=sim.synchronousStepping,
                  stable_draws=stable_draws)
    result.update(extra or {})
    return result


BATCH_FIELDS = ['run', 'seed', 'motor', 'wiring', 'signs', 'spin', 'eye_response',
                'eye_threshold', 'eye_saturation', 'eye_saturation_irradiance',
                'start_x', 'start_y', 'start_heading', 'start_dist',
                'start_sees_light', 'acquired', 'first_acq',
                'final_dist', 'min_dist', 'min_t', 'steps_run',
                'final_speed', 'final_bearing',
                'early_stopped', 'final_x', 'final_y', 'wall_time', 'synchronous_stepping',
                'stable_draws',
                'log_path', 'json_path', 'state_log_path']


def batch_kind(variant, spin=0.0, eye_saturation=None, eye_threshold=None,
               eye_response=None, synchronous_stepping=True, stable_draws=False):
    '''The batch file's tag: the variant (the uniselector, or the fixed-weight
    vehicle), then spin, eyes, '_async' and '_stabledraws'.'''
    kind = variant + spin_tag(spin) + eye_tag(eye_saturation, eye_threshold, eye_response)
    if not synchronous_stepping:
        kind += '_async'
    if stable_draws:
        kind += '_stabledraws'
    return kind


def run_batch(run_one, n_runs, experiment, kind, light_intensity=100, total_steps=60000,
              seed=None):
    '''Run a batch, print a summary table and save it as
    batch_<experiment>_<kind>_<light|dark>_<timestamp><run tag>.csv next to
    the runs' logs.

    run_one(seed) runs one experiment quietly and returns run_headless's
    dict.  With seed given, run i uses seed+i, so the batch is reproducible
    and an array job can pin exactly one run per task with --batch 1
    --seed N.'''
    import csv as _csv

    mode = 'dark' if light_intensity < 0 else 'light'
    print(f'=== Batch ({experiment}): {n_runs} runs, {mode}, {total_steps} ticks budget ===')
    print()

    results = []
    _base_tag = os.environ.get('HOMEO_RUN_TAG')
    for i in range(n_runs):
        t0 = time.time()
        print(f'--- Run {i+1}/{n_runs} ---', flush=True)
        # Every output file is named from a whole-second timestamp plus the run
        # tag, so several runs in ONE process overwrite each other unless the tag
        # distinguishes them.  With --batch 1 (how the HPC arrays invoke this)
        # there is nothing to disambiguate, so the tag is left exactly as the
        # array set it.
        if n_runs > 1:
            os.environ['HOMEO_RUN_TAG'] = (
                '%s-r%02d' % (_base_tag, i + 1) if _base_tag else 'r%02d' % (i + 1))
        r = run_one(None if seed is None else seed + i)
        elapsed = time.time() - t0
        r.pop('hom'); r.pop('backend')
        r['run'] = i + 1
        r['wall_time'] = elapsed
        results.append(r)
        if n_runs > 1:
            if _base_tag is None:
                os.environ.pop('HOMEO_RUN_TAG', None)
            else:
                os.environ['HOMEO_RUN_TAG'] = _base_tag
        print(f'  seed={r["seed"]}  '
              f'start=({r["start_x"]:.2f},{r["start_y"]:.2f}) hdg={r["start_heading"]:.0f} '
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
        csv_name = unique_stem(log_dir, f'batch_{experiment}_{kind}_{mode}_'
                               f'{time.strftime("%Y-%m-%d-%H-%M-%S")}{run_tag()}',
                               ('.csv',)) + '.csv'
        csv_path = os.path.join(log_dir, csv_name)
        with open(csv_path, 'w', newline='') as f:
            w = _csv.DictWriter(f, fieldnames=BATCH_FIELDS, extrasaction='ignore')
            w.writeheader()
            w.writerows(results)
        print(f'\nSummary saved to: {csv_path}')

    return results


def run_visualized(setup, caption, light_intensity=100, stable_draws=False,
                   random_heading=False, random_start=False, heading=None,
                   start_range=DEFAULT_START_RANGE):
    '''Run a phototaxis experiment with the pyglet visualizer.  setup and the
    other arguments as for run_headless.

    Press Q or Escape to close the window.
    Up/Down arrows adjust simulation speed (steps per frame).
    '''
    import pyglet
    from pyglet.gl import (glEnable, glBlendFunc, glHint, glClearColor, glClear,
                           GL_BLEND, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
                           GL_LINE_SMOOTH, GL_LINE_SMOOTH_HINT, GL_NICEST,
                           GL_COLOR_BUFFER_BIT)
    from KheperaSimulator.KheperaSimulator import KheperaCamera

    window = pyglet.window.Window(width=800, height=600, resizable=True, caption=caption)

    glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glClearColor(0.55, 0.95, 1.0, 1.0)

    hom, backend, seed = setup()
    sim = backend.kheperaSimulation
    robot = sim.allBodies['Khepera']
    target_pos = sim.allBodies['TARGET'].position
    place_robot(robot, random_heading, random_start, heading, start_range)
    print(f'{caption}: seed {seed}')

    log_path, json_path, _ = _start_logs(
        hom, backend, seed, run_settings(backend, light_intensity, stable_draws))

    from KheperaSimulator.KheperaSimulator import _get_shape_program
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
            f'{caption} - seed {seed}  t={state[0]}  speed={state[1]}  '
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
        _end_logs(hom, log_path, json_path)

    pyglet.clock.schedule(update)
    pyglet.app.run()


# --- Command line ---------------------------------------------------------------

COMMON_OPTIONS_HELP = '''
Options both experiments take
-----------------------------
   --steps N            run length in ticks (default 60000)
   --batch N            N runs and a summary CSV; with --seed S, run i uses S+i
   --seed S             the run's seed (default: drawn, printed and recorded)
   --run-tag NN         a serial appended to every output file name
   --visualize          the pyglet visualizer, with the same options
   --random-topology    every connection between the adaptive units on
   --continuous         the continuous (OU) uniselector instead of Ashby's
   --dark               light intensity -100 (a "darkness source"); with it,
                        --early-stop defaults to 1.5
   --early-stop D       stop a run once the robot is within D of the light
   --state-log          a per-tick .statelog (--log-interval N: every N ticks)
   --stable-draws       redraw each unit's (mass, viscosity) while viscosity x
                        dt / mass >= 1.8, as the direct experiment's runs
                        before 13 Oct 2026 did, to reproduce them; batch files
                        get "_stabledraws"
   --start-at-rest      the adaptive units start centred and motionless
   --async-stepping     one world step per motor command instead of one per
                        tick, as runs before 13 Oct 2026 did; batch files get
                        "_async"

   Start pose: default (4, 4), heading 0, the light at (7, 7) in view.
   --random-heading     random heading, default position
   --random-start       random heading, and a position --start-range MIN MAX
                        units from the light (default 2 6)
   --heading DEG        a fixed heading (draws nothing from the seed)

   --spin RATE          a baseline spin: +RATE x max speed on the left wheel and
                        -RATE on the right; > 0 clockwise.  0.05 is about 0.074
                        deg/tick.

   The eyes report their response, in [0, 1], to the irradiance on them: 0 up
   to their threshold I0, 1 from their saturation Isat on (default: linear, I0
   = 0, Isat = 100, saturating 1 unit from a light of intensity 100).
   --eye-saturation D   saturate at distance D: Isat = intensity / D^2
   --eye-threshold I0   the threshold, an irradiance (1 for a log eye)
   --eye-response log   logarithmic response (default linear)

   --traj-interval N    record every N-th trajectory point (the final pose is
                        always kept); --no-traj records none
'''


def _value(argv, flag, convert, message):
    "The value after flag in argv, converted; SystemExit(message) if missing or bad."
    idx = argv.index(flag)
    try:
        return convert(argv[idx + 1])
    except (IndexError, ValueError):
        raise SystemExit(message)


def parse_common_args(argv):
    '''Parse the options in COMMON_OPTIONS_HELP from argv; returns a dict.
    Also sets HOMEO_RUN_TAG from --run-tag (exported rather than threaded
    through: the file names are built where argv is not seen) and the
    trajectory recording.'''
    if '--run-tag' in argv:
        idx = argv.index('--run-tag')
        if idx + 1 < len(argv):
            os.environ['HOMEO_RUN_TAG'] = argv[idx + 1]

    o = {}
    o['topology'] = 'random' if '--random-topology' in argv else 'fixed'
    o['uniselector_type'] = 'continuous' if '--continuous' in argv else 'ashby'
    o['total_steps'] = (_value(argv, '--steps', int, '--steps needs a number of ticks')
                        if '--steps' in argv else 60000)
    o['light_intensity'] = -100 if '--dark' in argv else 100
    o['early_stop_distance'] = None
    if '--early-stop' in argv:
        o['early_stop_distance'] = _value(argv, '--early-stop', float,
                                          '--early-stop needs a distance')
    elif '--dark' in argv:
        o['early_stop_distance'] = 1.5   # TrajectoryGrapher's gray circle
    o['n_batch'] = (_value(argv, '--batch', int, '--batch needs a number of runs')
                    if '--batch' in argv else None)
    o['state_log'] = '--state-log' in argv
    o['state_log_interval'] = (_value(argv, '--log-interval', int, '--log-interval needs a number')
                               if '--log-interval' in argv else 1)
    o['seed'] = _value(argv, '--seed', int, '--seed needs an integer') if '--seed' in argv else None
    o['stable_draws'] = '--stable-draws' in argv     # off by default since 13 Oct 2026
    o['start_at_rest'] = '--start-at-rest' in argv
    o['random_start'] = '--random-start' in argv
    o['random_heading'] = '--random-heading' in argv
    o['synchronous_stepping'] = '--async-stepping' not in argv
    o['visualize'] = '--visualize' in argv

    o['heading'] = None
    if '--heading' in argv:
        o['heading'] = _value(argv, '--heading', float, '--heading needs degrees')
        if o['random_heading'] or o['random_start']:
            raise SystemExit('--heading cannot be combined with --random-heading/--random-start')

    o['start_range'] = DEFAULT_START_RANGE
    if '--start-range' in argv:
        idx = argv.index('--start-range')
        try:
            o['start_range'] = (float(argv[idx + 1]), float(argv[idx + 2]))
        except (IndexError, ValueError):
            raise SystemExit('--start-range needs two numbers, MIN MAX')
        if not 0 < o['start_range'][0] <= o['start_range'][1]:
            raise SystemExit('--start-range needs 0 < MIN <= MAX, got %g %g' % o['start_range'])
        if not o['random_start']:
            raise SystemExit('--start-range applies only with --random-start')

    o['spin'] = 0.0
    if '--spin' in argv:
        o['spin'] = _value(argv, '--spin', float, '--spin needs a number, e.g. 0.05 (> 0 clockwise)')
        if not -1 < o['spin'] < 1:
            raise SystemExit('--spin is a fraction of max speed, |RATE| < 1, got %g' % o['spin'])

    o['eye_response'] = None
    if '--eye-response' in argv:
        idx = argv.index('--eye-response')
        o['eye_response'] = argv[idx + 1] if idx + 1 < len(argv) else ''
        if o['eye_response'] not in ('linear', 'log'):
            raise SystemExit('--eye-response must be linear or log, got %r' % o['eye_response'])
    o['eye_threshold'] = None
    if '--eye-threshold' in argv:
        o['eye_threshold'] = _value(argv, '--eye-threshold', float,
                                    '--eye-threshold needs an irradiance, e.g. 1')
        if o['eye_threshold'] < 0 or (o['eye_response'] == 'log' and o['eye_threshold'] == 0):
            raise SystemExit('--eye-threshold must be >= 0 (> 0 for a log eye), got %g'
                             % o['eye_threshold'])
    o['eye_saturation'] = None
    if '--eye-saturation' in argv:
        o['eye_saturation'] = _value(argv, '--eye-saturation', float,
                                     '--eye-saturation needs a distance, e.g. 0.5')
        if not o['eye_saturation'] > 0:
            raise SystemExit('--eye-saturation must be > 0, got %g' % o['eye_saturation'])

    '''Trajectory volume.  Two rows are recorded per homeostat tick at ~50 bytes
       each, so a 6M-step run writes ~600 MB and a batch of 20 wrote 11.5 GB on
       2026-09-30.  --traj-interval decimates at write time; the final pose is
       always kept, so final-distance analyses are unaffected.'''
    from Helpers.RobotTrajectoryWriter import configureTrajectoryDefaults
    traj_interval = 1
    if '--traj-interval' in argv:
        traj_interval = max(1, _value(argv, '--traj-interval', int, '--traj-interval needs a number'))
    traj_enabled = '--no-traj' not in argv
    configureTrajectoryDefaults(interval=traj_interval, enabled=traj_enabled)
    if traj_enabled:
        est_mb = o['total_steps'] * 2 * 50 / traj_interval / 1e6 * (o['n_batch'] or 1)
        if est_mb > 200:
            print('Warning: this will write about %.1f GB of trajectory data. '
                  'Consider --traj-interval %d (keeps ~%d points per run).'
                  % (est_mb / 1000, max(traj_interval, 200),
                     o['total_steps'] * 2 // max(traj_interval, 200)))
    return o


# The options of parse_common_args that setup_phototaxis takes, and those of
# the runners
SETUP_OPTIONS = ('topology', 'light_intensity', 'uniselector_type', 'seed', 'stable_draws',
                 'start_at_rest', 'spin', 'eye_saturation', 'eye_threshold', 'eye_response',
                 'synchronous_stepping')
RUN_OPTIONS = ('total_steps', 'light_intensity', 'early_stop_distance', 'state_log',
               'state_log_interval', 'heading', 'random_heading', 'random_start',
               'start_range', 'stable_draws', 'eye_saturation', 'spin')
POSE_OPTIONS = ('random_heading', 'random_start', 'heading', 'start_range')


def pick(options, names):
    "The entries of options named in names."
    return {k: options[k] for k in names if k in options}
