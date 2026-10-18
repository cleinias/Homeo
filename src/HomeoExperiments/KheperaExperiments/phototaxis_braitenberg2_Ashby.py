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
Ashby-style phototaxis experiment using a Braitenberg type-2 vehicle
with the internal HOMEO Khepera simulator backend.

All unit parameters (mass, viscosity,
noise, potentiometer, switch) and connection weights start at random values.
The uniselectors are active on the four real units (motors and eyes), so
that when a unit's essential variable stays critical for too long
(deviation >= critThreshold * maxDeviation for uniselectorTimeInterval ticks),
the uniselector fires and randomly reassigns the weights of that unit's
incoming connections.  This is Ashby's core idea: the system searches
through parameter space by random trial until it finds a configuration
where all units remain within their viable range.

The experiment uses the 6-unit Braitenberg topology of initializeBraiten2_2:
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


Options
-------
   Those of phototaxis_common.COMMON_OPTIONS_HELP, which both phototaxis
   experiments share.


Usage
-----
    # Headless, fixed topology (default)
    python -m HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_Ashby

    # Headless, random topology
    python -m HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_Ashby --random-topology

    # With visualizer
    python -m HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_Ashby --visualize

    # A seeded batch in the dark, continuous uniselector
    python -m HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_Ashby --dark --continuous --batch 10 --seed 1
'''

from HomeoExperiments.KheperaExperiments import phototaxis_common as common
from HomeoExperiments.KheperaExperiments.phototaxis_common import (
    DEFAULT_START_RANGE, DEFAULT_ROBOT, seed_run, prepare_backend, experiment_suffix, set_light,
    apply_spin, set_uniselector_type, uniselector_tag, randomize_unit,
    set_motor_response)

import numpy as np


def setup_phototaxis(topology='fixed', backendSimulator=None,
                     mass_range=(1, 10), max_speed_fraction=0.8,
                     switching_rate=0.5, light_intensity=100,
                     uniselector_type='ashby', continuous_params=None,
                     seed=None, stable_draws=False, start_at_rest=False,
                     spin=0.0, eye_saturation=None, eye_threshold=None,
                     eye_response=None, robot=DEFAULT_ROBOT, simulator='box2d', rendering=False):
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
                            (model, tau_a, sigma_base, sigma_crit,
                            stress_exponent).  Only used when
                            uniselector_type='continuous'.  None = defaults.
        seed:               RNG seed for reproducibility.  If None, a
                            random seed is generated from os.urandom().
        stable_draws, start_at_rest: see phototaxis_common.randomize_unit.
        spin:               baseline spin, fraction of the motors' max speed,
                            > 0 clockwise (see phototaxis_common.apply_spin).
        eye_saturation, eye_threshold, eye_response: the eyes' sensitivity
                            (see phototaxis_common.configure_eyes).
        robot:              the robot, a name in phototaxis_common.ROBOTS
                            (default the e-puck2).
        simulator, rendering: 'box2d' (default) or 'webots', and for Webots
                            whether to show its window (see
                            phototaxis_common.prepare_backend).

    Returns:
        (hom, backend, seed) - the configured Homeostat, the backend
                               simulator, and the RNG seed used
    '''
    from Simulator.HomeoExperiments import initializeBraiten2_2Pos

    # Seed every generator before any stochastic initialization
    seed = seed_run(seed)

    exp_name = ('phototaxis_braitenberg2_Ashby_random' if topology == 'random'
                else 'phototaxis_braitenberg2_Ashby_fixed')
    exp_name += experiment_suffix(light_intensity, uniselector_type, True, spin,
                                  eye_saturation, eye_threshold, eye_response,
                                  robot, simulator, continuous_params)
    backendSimulator = prepare_backend(backendSimulator, exp_name, robot, simulator,
                                       rendering)

    hom = initializeBraiten2_2Pos(backendSimulator=backendSimulator)
    set_light(backendSimulator, light_intensity, eye_saturation, eye_threshold, eye_response)

    kwargs = dict(mass_range=mass_range,
                  max_speed_fraction=max_speed_fraction,
                  switching_rate=switching_rate,
                  uniselector_type=uniselector_type,
                  continuous_params=continuous_params,
                  stable_draws=stable_draws,
                  start_at_rest=start_at_rest)
    if topology == 'random':
        _ashby_random_topology(hom, **kwargs)
    else:
        _ashby_fixed_topology(hom, **kwargs)
    apply_spin(hom, spin)

    return hom, backendSimulator, seed


def _ashby_fixed_topology(hom, mass_range=(1, 10),
                          max_speed_fraction=0.8, switching_rate=0.5,
                          uniselector_type='ashby', continuous_params=None,
                          stable_draws=False, start_at_rest=False):
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
        stable_draws, start_at_rest: see phototaxis_common.randomize_unit.
    '''

    for u in hom.homeoUnits:
        if 'Sensor' in u.name and 'Eye' not in u.name:
            # Sensor-only units: pure input, no self-organization
            continue

        # Randomize unit parameters, mass in a responsive range
        randomize_unit(u, mass_range, stable_draws, start_at_rest)

        # Activate uniselector and set type
        u.uniselectorActive = True
        set_uniselector_type(u, uniselector_type, continuous_params)

        # Motor-specific overrides
        if 'Motor' in u.name:
            set_motor_response(u, max_speed_fraction, switching_rate)

        for conn in u.inputConnections:
            if conn.incomingUnit == u:
                # Self-connection: small random weight, protected from uniselector
                conn.newWeight(np.random.uniform(-0.1, 0.1))
                conn.noise = np.random.uniform(0, 0.05)
                conn.state = 'manual'
                conn.status = True
            elif conn.status:
                # Active cross-connection: small random weight, under uniselector
                conn.newWeight(np.random.uniform(-0.1, 0.1))
                conn.noise = np.random.uniform(0, 0.1)
                conn.state = 'uniselector'



def _ashby_random_topology(hom, mass_range=(1, 10),
                           max_speed_fraction=0.8, switching_rate=0.5,
                           uniselector_type='ashby', continuous_params=None,
                          stable_draws=False, start_at_rest=False):
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
        stable_draws, start_at_rest: see phototaxis_common.randomize_unit.
    '''

    for u in hom.homeoUnits:
        if 'Sensor' in u.name and 'Eye' not in u.name:
            # Sensor-only units: keep as pure inputs, all connections off
            u.uniselectorActive = False
            for conn in u.inputConnections:
                conn.status = False
            continue

        # Randomize unit parameters, mass in a responsive range
        randomize_unit(u, mass_range, stable_draws, start_at_rest)

        # Set all connections active with small random weights
        for conn in u.inputConnections:
            conn.newWeight(np.random.uniform(-0.1, 0.1))
            conn.noise = np.random.uniform(0, 0.1)
            conn.state = 'uniselector'
            conn.status = True

        # Activate uniselector and set type
        u.uniselectorActive = True
        set_uniselector_type(u, uniselector_type, continuous_params)

        # Protect self-connection from uniselector
        u.inputConnections[0].state = 'manual'

        # Motor-specific overrides
        if 'Motor' in u.name:
            set_motor_response(u, max_speed_fraction, switching_rate)


def _setup(**kwargs):
    "setup_phototaxis bound to its arguments, and the run's title."
    def setup():
        return setup_phototaxis(**kwargs)
    return setup, 'Braitenberg 2 — Ashby (%s topology, %s uniselector)' % (
        kwargs.get('topology', 'fixed'), kwargs.get('uniselector_type', 'ashby'))


def run_headless(topology='fixed', total_steps=60000, report_interval=500,
                 light_intensity=100, early_stop_distance=None, quiet=False,
                 uniselector_type='ashby', continuous_params=None,
                 state_log=False, state_log_interval=1, seed=None, env_seed=None, heading=None,
                 random_heading=False, random_start=False, start_range=DEFAULT_START_RANGE,
                 stable_draws=False, start_at_rest=False, spin=0.0,
                 eye_saturation=None, eye_threshold=None, eye_response=None,
                 robot=DEFAULT_ROBOT, simulator='box2d', rendering=False):
    '''Run the Ashby phototaxis experiment headless
    (phototaxis_common.run_headless, which describes the options and the
    result; the setup's are setup_phototaxis's).'''
    setup, title = _setup(topology=topology, light_intensity=light_intensity,
                          uniselector_type=uniselector_type,
                          continuous_params=continuous_params, seed=seed,
                          stable_draws=stable_draws, start_at_rest=start_at_rest,
                          spin=spin, eye_saturation=eye_saturation,
                          eye_threshold=eye_threshold, eye_response=eye_response,
                          robot=robot, simulator=simulator, rendering=rendering)
    return common.run_headless(
        setup, title, total_steps=total_steps, report_interval=report_interval,
        light_intensity=light_intensity, early_stop_distance=early_stop_distance,
        quiet=quiet, state_log=state_log, state_log_interval=state_log_interval,
        heading=heading, random_heading=random_heading, random_start=random_start,
        start_range=start_range, stable_draws=stable_draws,
        eye_saturation=eye_saturation, spin=spin, env_seed=env_seed)


def run_batch(n_runs=10, topology='fixed', total_steps=2000000,
              report_interval=500, light_intensity=100,
              early_stop_distance=None,
              uniselector_type='ashby', continuous_params=None, seed=None, env_seed=None,
              batch_vary='both',
              state_log=False, state_log_interval=1, heading=None,
              random_heading=False, random_start=False, start_range=DEFAULT_START_RANGE,
              stable_draws=False, start_at_rest=False, spin=0.0,
              eye_saturation=None, eye_threshold=None, eye_response=None,
              robot=DEFAULT_ROBOT, simulator='box2d', rendering=False):
    '''Run a batch of experiments and print a summary table
    (phototaxis_common.run_batch).  With seed given, run i uses seed+i;
    env_seed and batch_vary: see phototaxis_common.batch_seeds.'''
    kind = common.batch_kind(uniselector_tag(uniselector_type, continuous_params), spin, eye_saturation,
                             eye_threshold, eye_response, stable_draws, robot,
                             simulator)

    def run_one(run_seed, run_env_seed):
        return run_headless(topology=topology, total_steps=total_steps,
                            report_interval=report_interval,
                            light_intensity=light_intensity,
                            early_stop_distance=early_stop_distance, quiet=True,
                            uniselector_type=uniselector_type,
                            continuous_params=continuous_params,
                            seed=run_seed, env_seed=run_env_seed,
                            state_log=state_log, state_log_interval=state_log_interval,
                            heading=heading, random_heading=random_heading,
                            random_start=random_start, start_range=start_range,
                            stable_draws=stable_draws, start_at_rest=start_at_rest,
                            spin=spin, eye_saturation=eye_saturation,
                            eye_threshold=eye_threshold, eye_response=eye_response,
                            robot=robot, simulator=simulator, rendering=rendering)
    return common.run_batch(run_one, n_runs, 'ashby', kind,
                            light_intensity=light_intensity, total_steps=total_steps,
                            seed=seed, env_seed=env_seed,
                            vary=batch_vary)


def run_visualized(topology='fixed', light_intensity=100, uniselector_type='ashby',
                   continuous_params=None, seed=None, env_seed=None, heading=None,
                   random_heading=False, random_start=False, start_range=DEFAULT_START_RANGE,
                   stable_draws=False, start_at_rest=False, spin=0.0,
                   eye_saturation=None, eye_threshold=None, eye_response=None,
                   robot=DEFAULT_ROBOT, simulator='box2d', rendering=False):
    '''Run the Ashby phototaxis experiment with the pyglet visualizer, with
    the same options as run_headless.

    Press Q or Escape to close the window.
    Up/Down arrows adjust simulation speed (steps per frame).
    '''
    setup, title = _setup(topology=topology, light_intensity=light_intensity,
                          uniselector_type=uniselector_type,
                          continuous_params=continuous_params, seed=seed,
                          stable_draws=stable_draws, start_at_rest=start_at_rest,
                          spin=spin, eye_saturation=eye_saturation,
                          eye_threshold=eye_threshold, eye_response=eye_response,
                          robot=robot, simulator=simulator, rendering=rendering)
    common.run_visualized(setup, 'Phototaxis ' + title, light_intensity=light_intensity,
                          stable_draws=stable_draws, random_heading=random_heading,
                          random_start=random_start, heading=heading,
                          start_range=start_range, env_seed=env_seed)


def main(argv):
    o = common.parse_common_args(argv)
    setup_options = common.pick(o, common.SETUP_OPTIONS)
    if o['visualize']:
        run_visualized(**setup_options, **common.pick(o, common.POSE_OPTIONS))
    else:
        run_options = dict(setup_options, **common.pick(o, common.RUN_OPTIONS))
        if o['n_batch'] is not None:
            run_batch(n_runs=o['n_batch'], batch_vary=o['batch_vary'], **run_options)
        else:
            run_headless(**run_options)


if __name__ == '__main__':
    import sys
    main(sys.argv)
