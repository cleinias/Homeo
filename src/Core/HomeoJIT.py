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
def _jit_seed(seed):
    """Seed the RNG that the JIT functions in this module actually draw from."""
    np.random.seed(seed)


def seed_jit_rng(seed):
    """Make the noise drawn inside this module's JIT functions reproducible.

    Numba's nopython mode keeps its OWN random state, entirely separate from the
    one np.random.seed() touches at Python level.  Seeding only at Python level
    therefore left every draw in _jit_unit_noise(), _jit_needle_position_base()
    and HomeoUniselectorContinuous.evolve_weights_jit() running off an unseeded
    stream: initial conditions were reproducible (they are drawn in Python,
    before any JIT call), but trajectories were not.  Three runs of one seed gave
    three different trajectories, which is how this was found.

    The seed must be set from inside nopython mode to reach that state, which is
    what _jit_seed does.  With numba absent, njit degrades to a no-op and the
    call simply re-seeds NumPy, which is already correct.

    Note: numba's random state is per-thread, so this seeds the thread that calls
    it.  Headless batch runs update the units on the calling thread, so one call
    per run is enough; a threaded run loop would need one call per worker.
    """
    _jit_seed(seed)


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
def _jit_spring_step(p, q, f, v0, t):
    """Exact step of u'' + p u' + q u = f from u = 0, u' = v0, over time t.

    Returns (u, u').  It is the exponential of the augmented system
    [[A, g], [0, 0]] t, A = [[0, 1], [-q, -p]], g = [0, f], computed on
    scalars by scaling and squaring a Taylor series: the 2x2 block E = e^(At)
    and the vector h = (integral of e^(As) ds) g, which square as
    (E, h) -> (E E, E h + h).  The scaled matrix has norm <= 0.5, where 14
    terms give double precision; the number of squarings grows only with the
    log of p t and q t, so stiff (Ashby-like) units cost little more."""
    norm = abs(t) * max(1.0, abs(q) + abs(p))
    squarings = 0
    while norm > 0.5:
        norm *= 0.5
        squarings += 1
    h = t / (2.0 ** squarings)
    a10 = -q * h
    a11 = -p * h
    g1 = f * h
    # Taylor series of e^(Ah) = sum A^n/n!, and of its integral times g,
    # sum A^(n-1) g / n!  (vector x = A^(n-1) g / (n-1)! carried along)
    e00, e01, e10, e11 = 1.0, 0.0, 0.0, 1.0
    t00, t01, t10, t11 = 1.0, 0.0, 0.0, 1.0      # A^n / n!
    x0, x1 = 0.0, g1                             # A^(n-1) g / (n-1)!
    h0, h1 = 0.0, g1                             # running sum, n = 1
    for n in range(1, 15):
        # t <- t A / n
        n00 = (t00 * 0.0 + t01 * a10) / n
        n01 = (t00 * h + t01 * a11) / n
        n10 = (t10 * 0.0 + t11 * a10) / n
        n11 = (t10 * h + t11 * a11) / n
        t00, t01, t10, t11 = n00, n01, n10, n11
        e00 += t00
        e01 += t01
        e10 += t10
        e11 += t11
        # x <- A x / n, added as the next term of the integral (divided by n + 1)
        y0 = (0.0 * x0 + h * x1) / n
        y1 = (a10 * x0 + a11 * x1) / n
        x0, x1 = y0, y1
        h0 += x0 / (n + 1)
        h1 += x1 / (n + 1)
    for _ in range(squarings):
        nh0 = e00 * h0 + e01 * h1 + h0
        nh1 = e10 * h0 + e11 * h1 + h1
        n00 = e00 * e00 + e01 * e10
        n01 = e00 * e01 + e01 * e11
        n10 = e10 * e00 + e11 * e10
        n11 = e10 * e01 + e11 * e11
        e00, e01, e10, e11 = n00, n01, n10, n11
        h0, h1 = nh0, nh1
    return e01 * v0 + h0, e11 * v0 + h1


@njit(cache=True)
def _jit_needle_position_newtonian(torque, viscosity, current_velocity, mass, crit_dev,
                                   dt_fast, stiffness=0.0):
    """Replacement for HomeoUnitNewtonian.newLinearNeedlePosition() arithmetic.

    The exact solution over one step of

        m x'' = torque - stiffness (x - x0) - viscosity x'

    from x0 = crit_dev, v0 = current_velocity: a needle with Stokes drag
    whose force is torque at the start and changes by -stiffness per unit of
    displacement during the step.  The stiffness is the unit's own
    self-connection, which acts on the needle as a spring (or, with positive
    feedback, a negative spring); the other connections' torque is held over
    the step.  Being exact, the step adds nothing of its own: no growth the
    equation does not have (an explicit step blew up beyond viscosity * dt /
    mass = 2, and made an undamped spring's swing grow), no damping it does
    not have.

    Without stiffness the solution is, with b = viscosity * dt_fast / mass,

        v_new = v e^-b + (torque dt / m) phi1(b)
        x_new = x + v dt phi1(b) + (torque dt^2 / m) phi2(b)

    phi1(b) = (1 - e^-b) / b and phi2(b) = (b - 1 + e^-b) / b^2, which tend to
    1 and 1/2 as b -> 0.  With stiffness see _jit_spring_step (u = x - x0).

    Returns (new_pos, acceleration), the acceleration being the step's mean,
    (v_new - v) / dt_fast, so that v_new = v + acceleration * dt_fast.
    """
    if dt_fast <= 0.0:
        return crit_dev, 0.0
    if stiffness == 0.0:
        b = viscosity * dt_fast / mass
        if abs(b) < 1e-4:
            phi1 = 1.0 - b / 2.0 + b * b / 6.0
            phi2 = 0.5 - b / 6.0 + b * b / 24.0
        else:
            em1 = np.expm1(-b)                  # e^-b - 1
            phi1 = -em1 / b
            phi2 = (b + em1) / (b * b)
        impulse = torque * dt_fast / mass
        new_velocity = current_velocity * (1.0 - b * phi1) + impulse * phi1
        new_pos = crit_dev + current_velocity * dt_fast * phi1 + impulse * dt_fast * phi2
        return new_pos, (new_velocity - current_velocity) / dt_fast
    u, new_velocity = _jit_spring_step(viscosity / mass, stiffness / mass, torque / mass,
                                       current_velocity, dt_fast)
    return crit_dev + u, (new_velocity - current_velocity) / dt_fast


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


_warmed_up = False


def warmup_jit():
    """Call each JIT function once with dummy data to trigger Numba compilation.
    This is a one-time cost (~1s) at simulation start, so it runs once per
    process.  The dummy calls use zero noise, so they draw no random numbers:
    numba compiles a function on its first call whatever branch it takes, and
    drawing here (as this did on every Homeostat.runFor() call) shifted the
    random stream, so one seed gave a different run depending on how the run
    was split into runFor() calls."""
    global _warmed_up
    if _warmed_up:
        return
    _jit_unit_noise(0.0)
    _jit_conn_noise(0.5, 0.0)
    dummy = np.array([0.5], dtype=np.float64)
    _jit_compute_torque(dummy, dummy, dummy, np.zeros(1, dtype=np.float64))
    _jit_needle_position_base(1.0, 0.5, 10.0, 100.0, 0.0)
    _jit_needle_position_newtonian(1.0, 0.5, 0.1, 100.0, 0.0, 1.0, 0.0)
    _jit_needle_position_newtonian(1.0, 0.5, 0.1, 100.0, 0.0, 1.0, 0.1)
    _jit_compute_output(0.0, -10.0, 10.0, -1.0, 1.0)
    _warmed_up = True
