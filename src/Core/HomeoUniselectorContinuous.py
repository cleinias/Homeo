'''
@author: stefano

Continuous stochastic uniselector: replaces Ashby's discrete stepping switch
with a continuous random search on the connection weights.

Instead of periodically checking whether the essential variable is critical
and then randomly resampling all weights at once, this uniselector moves
each weight a little at every timestep, by an amount that grows with the
unit's stress (0 at equilibrium, 1 at the limit of its range).  tau_a is the
search's timescale: the weights move slowly relative to the fast needle
dynamics when tau_a is large compared with them, the slow-fast separation of
an adaptive parameter a whose rate is set by the fast state x,
tau_a da/dt = f(x).  Two models (attribute `model`):

'diffusion' (default): a stress-gated random walk with no drift,

    dw = sigma(stress) * sqrt(2 dt / tau_a) * N(0,1)

  Under full stress a weight roams the whole range [-1, 1] in about
  tau_a / (2 sigma_crit^2) ticks (its stationary distribution is uniform);
  without stress (sigma_base = 0) it does not move at all, so a unit that
  has found a stable field keeps its weights, as Ashby's uniselector does.

'ou': an Ornstein-Uhlenbeck process with the whole equation on the slow
  timescale,

    dw = -(w / tau_a) dt + sigma(stress) * sqrt(2 dt / tau_a) * N(0,1)

  tau_a is the autocorrelation time and sigma the stationary standard
  deviation (before the bounds).  The weights also relax towards 0, over
  tau_a ticks, when the unit is stable.

Both reflect the weights at +-1, so no mass piles up at the bounds.

This preserves Ashby's core hypothesis: adaptation operates on the
parameters (weights), not within the dynamics.  The fast ODE is untouched.
'''

from Core.HomeoUniselector import HomeoUniselector, HomeoUniselectorError
import numpy


def reflect(w, low=-1.0, high=1.0):
    '''Fold w back into [low, high], reflecting at the bounds (any number of
    times).  Works on scalars and arrays.'''
    w = numpy.asarray(w, dtype=float)
    span = high - low
    y = numpy.mod(w - low, 2 * span)
    folded = low + numpy.where(y > span, 2 * span - y, y)
    return numpy.where((w >= low) & (w <= high), w, folded)    # exact inside


class HomeoUniselectorContinuous(HomeoUniselector):
    '''
    A continuous stochastic uniselector that evolves connection weights
    at every simulation timestep (see the module docstring for the models).

    The noise intensity is modulated by a stress level in [0, 1], where
    0 means the essential variable is at equilibrium and 1 means it is
    at the boundary of the acceptable range.

    Instance variables (beyond superclass):
        model        -- 'diffusion' (default) or 'ou'
        tau_a        -- timescale of the search, in ticks (>> the needle's)
        sigma_base   -- amplitude at zero stress (0: weights kept when stable)
        sigma_crit   -- amplitude at full stress
        dt           -- integration timestep (matches the fast dynamics)
        stress_exponent -- nonlinear shaping of stress level (1 = linear,
                          2 = quadratic, etc.)
    '''

    MODELS = ('diffusion', 'ou')

    DefaultParameters = {
        'model': 'diffusion',
        'tau_a': 1000.0,
        'sigma_base': 0.0,
        'sigma_crit': 1.0,
        'dt': 1.0,
        'stress_exponent': 2.0,
    }

    def __init__(self):
        super(HomeoUniselectorContinuous, self).__init__()
        self.setDefaults()

    def setDefaults(self):
        "The default weights' range, [-1, 1], and the default parameters (DefaultParameters)"
        self._lowerBound = -1
        self._upperBound = 1
        self._model = self.DefaultParameters['model']
        self._tau_a = self.DefaultParameters['tau_a']
        self._sigma_base = self.DefaultParameters['sigma_base']
        self._sigma_crit = self.DefaultParameters['sigma_crit']
        self._dt = self.DefaultParameters['dt']
        self._stress_exponent = self.DefaultParameters['stress_exponent']

    # --- Properties ---

    def setLowerBound(self, value):
        '''The weights' range is symmetric about 0: a negative lower bound
           sets the upper one to its opposite.'''
        if not value < 0:
            raise HomeoUniselectorError('lowerBound must be negative, not %r' % value)
        self._lowerBound = value
        self._upperBound = -value

    def setUpperBound(self, value):
        "See setLowerBound."
        if not value > 0:
            raise HomeoUniselectorError('upperBound must be positive, not %r' % value)
        self._upperBound = value
        self._lowerBound = -value

    def getDt(self):
        return self._dt

    def setDt(self, value):
        "The uniselector's time step, in ticks."
        if not value > 0:
            raise HomeoUniselectorError('dt must be positive, not %r' % value)
        self._dt = float(value)

    dt = property(fget=lambda self: self.getDt(),
                  fset=lambda self, value: self.setDt(value))

    def getModel(self):
        return self._model

    def setModel(self, value):
        if value not in self.MODELS:
            raise ValueError('model must be one of %s, not %r' % (self.MODELS, value))
        self._model = value

    model = property(fget=lambda self: self.getModel(),
                     fset=lambda self, value: self.setModel(value))

    def getTauA(self):
        return self._tau_a

    def setTauA(self, value):
        if value > 0:
            self._tau_a = float(value)

    tau_a = property(fget=lambda self: self.getTauA(),
                     fset=lambda self, value: self.setTauA(value))

    def getSigmaBase(self):
        return self._sigma_base

    def setSigmaBase(self, value):
        if value >= 0:
            self._sigma_base = float(value)

    sigma_base = property(fget=lambda self: self.getSigmaBase(),
                          fset=lambda self, value: self.setSigmaBase(value))

    def getSigmaCrit(self):
        return self._sigma_crit

    def setSigmaCrit(self, value):
        if value >= 0:
            self._sigma_crit = float(value)

    sigma_crit = property(fget=lambda self: self.getSigmaCrit(),
                          fset=lambda self, value: self.setSigmaCrit(value))

    def getStressExponent(self):
        return self._stress_exponent

    def setStressExponent(self, value):
        if value > 0:
            self._stress_exponent = float(value)

    stress_exponent = property(fget=lambda self: self.getStressExponent(),
                               fset=lambda self, value: self.setStressExponent(value))

    # --- Core methods ---

    def sigma(self, stress_level):
        '''Compute noise intensity from the current stress level.

        stress_level is in [0, 1].  The stress_exponent controls the
        nonlinear shaping: exponent=1 gives linear interpolation,
        exponent=2 keeps noise very low until the variable is
        substantially displaced, then ramps up fast.'''

        s = min(max(stress_level, 0.0), 1.0)
        shaped = s ** self._stress_exponent
        return self._sigma_base + (self._sigma_crit - self._sigma_base) * shaped

    def step(self, w, stress_level, noise):
        '''One step of the current model for the signed weight(s) w, given
        standard normal noise of the same shape.  Returns the new weight(s)
        in [-1, 1].'''
        sig = self.sigma(stress_level)
        dt = self._dt
        diffusion = sig * numpy.sqrt(2.0 * dt / self._tau_a) * noise
        if self._model == 'ou':
            w_new = w - (w / self._tau_a) * dt + diffusion
        else:
            w_new = w + diffusion
        return reflect(w_new, self._lowerBound, self._upperBound)

    def evolve_weight(self, current_signed_weight, stress_level):
        '''Integrate one Euler-Maruyama step for a single weight.

        Parameters:
            current_signed_weight -- the current effective weight in [-1, 1]
            stress_level          -- float in [0, 1]

        Returns the new signed weight, in [-1, 1].
        '''
        return float(self.step(current_signed_weight, stress_level, numpy.random.randn()))

    def evolve_weights(self, connections, stress_level):
        '''Evolve all uniselector-controlled connection weights by one timestep.

        Parameters:
            connections  -- list of HomeoConnection objects (the unit's inputConnections)
            stress_level -- float in [0, 1]
        '''

        for conn in connections:
            # The connections the unit's dynamics use (active, from an active
            # unit), as in the headless arrays (HomeoUnit._sync_jit_arrays):
            # evolving one more here would also shift the noise draws.
            if (conn.state == 'uniselector' and conn.isActive()
                    and conn.incomingUnit.isActive()):
                w = conn.weight * conn.switch   # current signed weight in [-1, 1]
                w_new = self.evolve_weight(w, stress_level)
                conn.newWeight(w_new)

    def evolve_weights_jit(self, jit_weights, jit_switches, stress_level, evolvable=None):
        '''Evolve weights in-place on the JIT arrays (headless/GA mode).

        Parameters:
            jit_weights  -- numpy float64 array of absolute weight values
            jit_switches -- numpy float64 array of signs (+1/-1)
            stress_level -- float in [0, 1]
            evolvable    -- optional boolean array: which entries the
                            uniselector controls (state 'uniselector').  The
                            others, a 'manual' self-connection for instance,
                            are left alone, as evolve_weights() leaves them.
                            None evolves every entry.

        Modifies jit_weights and jit_switches in place.  Draws its noise in
        the same order as evolve_weights(), so both paths follow the same
        trajectory from the same random state.
        '''

        if evolvable is None:
            indices = numpy.arange(jit_weights.shape[0])
        else:
            indices = numpy.flatnonzero(evolvable)
        noise = numpy.random.randn(len(indices))
        w = jit_weights[indices] * jit_switches[indices]  # signed weights
        w_new = self.step(w, stress_level, noise)
        jit_weights[indices] = numpy.abs(w_new)
        jit_switches[indices] = numpy.where(w_new >= 0, 1.0, -1.0)

    # --- Superclass interface (unused in continuous mode, but kept for compatibility) ---

    def advance(self):
        '''No-op: the continuous uniselector has no stepping index.'''
        pass

    def produceNewValue(self):
        '''Not used in continuous mode.  Returns a random value for
        compatibility with code that expects the discrete interface.'''
        return numpy.random.uniform(self._lowerBound, self._upperBound)
