"""
Numba JIT-compiled functions for hot-path arithmetic in headless/GA mode.

Replaces the scalar Python loops in computeTorque, noise generation,
needle position computation, and output scaling with compiled native code.

Falls back gracefully to pure Python when numba is not installed.
"""

try:
    from numba import njit
except ImportError:
    def njit(func=None, **kwargs):
        if func is not None:
            return func
        return lambda f: f

import numpy as np


@njit(cache=True)
def _jit_unit_noise(noise):
    """Replacement for HomeoNoise.unitNoise().
    Distorting-normal-linear noise: Gaussian(0, noise/3) clipped to [-noise, noise].
    Uses np.random.normal instead of random.gauss (identical distribution)."""
    if noise == 0.0:
        return 0.0
    val = np.random.normal(0.0, noise / 3.0)
    if val < -noise:
        return -noise
    if val > noise:
        return noise
    return val


@njit(cache=True)
def _jit_conn_noise(current, noise):
    """Replacement for HomeoNoise.connNoise().
    Distorting-normal-proportional noise for connections."""
    if noise == 0.0:
        return 0.0
    if current != 0.0:
        bound = noise * abs(current)
    else:
        bound = noise
    val = np.random.normal(0.0, bound / 3.0)
    if val < -bound:
        return -bound
    if val > bound:
        return bound
    return val


@njit(cache=True)
def _jit_compute_torque(outputs, switches, weights, noises):
    """Replacement for the computeTorque list comprehension + conn.output() chain.

    Parameters
    ----------
    outputs : float64 array — currentOutput of each incoming unit
    switches : float64 array — connection switch (+1/-1)
    weights : float64 array — connection weight (absolute)
    noises : float64 array — connection noise parameter

    Returns the sum of (output * switch * weight + connNoise) for each connection.
    """
    total = 0.0
    n = outputs.shape[0]
    for i in range(n):
        cn = _jit_conn_noise(outputs[i], noises[i])
        total += outputs[i] * switches[i] * weights[i] + cn
    return total


@njit(cache=True)
def _jit_needle_position_base(torque, viscosity, max_viscosity, mass, crit_dev):
    """Replacement for HomeoUnit.newLinearNeedlePosition() arithmetic.

    Aristotelian model: v = F/m, new_pos = crit_dev + v
    where F = torque * (1 - viscosity/max_viscosity).
    """
    normalizedViscosity = viscosity / max_viscosity
    totalForce = torque * (1.0 - normalizedViscosity)
    newVelocity = totalForce / mass
    return crit_dev + newVelocity


@njit(cache=True)
def _jit_needle_position_newtonian(torque, viscosity, current_velocity, mass, crit_dev, dt_fast):
    """Replacement for HomeoUnitNewtonian.newLinearNeedlePosition() arithmetic.

    Newtonian model with Stokes drag inline:
    drag = -viscosity * current_velocity
    totalForce = torque + drag
    acceleration = totalForce / mass
    displacement = current_velocity * dt_fast + 0.5 * acceleration * dt_fast * dt_fast
    new_pos = crit_dev + displacement

    Returns (new_pos, acceleration).
    """
    drag = -viscosity * current_velocity
    totalForce = torque + drag
    acceleration = totalForce / mass
    displacement = current_velocity * dt_fast + 0.5 * acceleration * dt_fast * dt_fast
    return crit_dev + displacement, acceleration


@njit(cache=True)
def _jit_compute_output(crit_dev, min_dev, max_dev, out_low, out_high):
    """Replacement for HomeoUnit.computeOutput() scaling + clipping.

    Linearly maps crit_dev from [min_dev, max_dev] to [out_low, out_high],
    then clips to [out_low, out_high].
    """
    out_range = out_high - out_low
    dev_range = max_dev - min_dev
    out = (crit_dev - min_dev) * (out_range / dev_range) + out_low
    if out < out_low:
        return out_low
    if out > out_high:
        return out_high
    return out


def warmup_jit():
    """Call each JIT function once with dummy data to trigger Numba compilation.
    This is a one-time cost (~1s) at simulation start."""
    _jit_unit_noise(0.1)
    _jit_conn_noise(0.5, 0.1)
    dummy = np.array([0.5], dtype=np.float64)
    _jit_compute_torque(dummy, dummy, dummy, dummy)
    _jit_needle_position_base(1.0, 0.5, 10.0, 100.0, 0.0)
    _jit_needle_position_newtonian(1.0, 0.5, 0.1, 100.0, 0.0, 1.0)
    _jit_compute_output(0.0, -10.0, 10.0, -1.0, 1.0)
