'''
Created on Feb 26, 2026

@author: stefano

Continuous stochastic uniselector: replaces Ashby's discrete stepping switch
with an Ornstein-Uhlenbeck process on the connection weights.

Instead of periodically checking whether the essential variable is critical
and then randomly resampling all weights at once, this uniselector evolves
each weight continuously at every timestep via Euler-Maruyama integration:

    dw = (-theta * w / tau_a) * dt  +  sigma(stress) * sqrt(dt) * N(0,1)

where sigma(stress) interpolates between a small baseline noise (when the
unit is near equilibrium) and a large noise (when the essential variable
is critical).  The timescale separation tau_a >> 1 ensures that weights
drift slowly relative to the fast needle dynamics.

This preserves Ashby's core hypothesis: adaptation operates on the
parameters (weights), not within the dynamics.  The fast ODE is untouched.

See: Research-notes/Addendum_to_the_CTRNN_Ashby_Discussion.md, Section 6.
'''

from Core.HomeoUniselector import HomeoUniselector
import numpy


class HomeoUniselectorContinuous(HomeoUniselector):
    '''
    A continuous stochastic uniselector that evolves connection weights
    via an Ornstein-Uhlenbeck process at every simulation timestep.

    The noise intensity is modulated by a stress level in [0, 1], where
    0 means the essential variable is at equilibrium and 1 means it is
    at the boundary of the acceptable range.

    Instance variables (beyond superclass):
        tau_a        -- weight relaxation timescale (>> 1 for slow drift)
        theta        -- mean-reversion rate (pulls weights toward 0)
        sigma_base   -- baseline noise intensity (exploration when stable)
        sigma_crit   -- noise intensity when essential variable is critical
        dt           -- integration timestep (matches the fast dynamics)
        stress_exponent -- nonlinear shaping of stress level (1 = linear,
                          2 = quadratic, etc.)
    '''

    DefaultParameters = {
        'tau_a': 1000.0,
        'theta': 0.01,
        'sigma_base': 0.001,
        'sigma_crit': 0.1,
        'dt': 1.0,
        'stress_exponent': 2.0,
    }

    def __init__(self):
        super(HomeoUniselectorContinuous, self).__init__()
        self._lowerBound = -1
        self._upperBound = 1
        self._tau_a = self.DefaultParameters['tau_a']
        self._theta = self.DefaultParameters['theta']
        self._sigma_base = self.DefaultParameters['sigma_base']
        self._sigma_crit = self.DefaultParameters['sigma_crit']
        self._dt = self.DefaultParameters['dt']
        self._stress_exponent = self.DefaultParameters['stress_exponent']

    # --- Properties ---

    def getTauA(self):
        return self._tau_a

    def setTauA(self, value):
        if value > 0:
            self._tau_a = float(value)

    tau_a = property(fget=lambda self: self.getTauA(),
                     fset=lambda self, value: self.setTauA(value))

    def getTheta(self):
        return self._theta

    def setTheta(self, value):
        if value >= 0:
            self._theta = float(value)

    theta = property(fget=lambda self: self.getTheta(),
                     fset=lambda self, value: self.setTheta(value))

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

    def evolve_weight(self, current_signed_weight, stress_level):
        '''Integrate one Euler-Maruyama step for a single weight.

        Parameters:
            current_signed_weight -- the current effective weight in [-1, 1]
            stress_level          -- float in [0, 1]

        Returns the new signed weight, clipped to [-1, 1].
        '''

        w = current_signed_weight
        sig = self.sigma(stress_level)
        dt = self._dt

        # Ornstein-Uhlenbeck step:
        #   dw = -(theta / tau_a) * w * dt  +  sigma * sqrt(dt) * N(0,1)
        drift = -(self._theta / self._tau_a) * w * dt
        diffusion = sig * numpy.sqrt(dt) * numpy.random.randn()
        w_new = w + drift + diffusion

        return numpy.clip(w_new, -1.0, 1.0)

    def evolve_weights(self, connections, stress_level):
        '''Evolve all uniselector-controlled connection weights by one timestep.

        Parameters:
            connections  -- list of HomeoConnection objects (the unit's inputConnections)
            stress_level -- float in [0, 1]
        '''

        for conn in connections:
            if conn.state == 'uniselector' and conn.isActive():
                w = conn.weight * conn.switch   # current signed weight in [-1, 1]
                w_new = self.evolve_weight(w, stress_level)
                conn.newWeight(w_new)

    def evolve_weights_jit(self, jit_weights, jit_switches, stress_level):
        '''Evolve weights in-place on the JIT arrays (headless/GA mode).

        Parameters:
            jit_weights  -- numpy float64 array of absolute weight values
            jit_switches -- numpy float64 array of signs (+1/-1)
            stress_level -- float in [0, 1]

        Modifies jit_weights and jit_switches in place.
        '''

        n = jit_weights.shape[0]
        sig = self.sigma(stress_level)
        dt = self._dt
        drift_coeff = -(self._theta / self._tau_a) * dt
        diffusion_scale = sig * numpy.sqrt(dt)

        # Vectorised: one randn per connection
        noise = numpy.random.randn(n)

        for i in range(n):
            w = jit_weights[i] * jit_switches[i]  # signed weight
            w_new = w + drift_coeff * w + diffusion_scale * noise[i]
            w_new = numpy.clip(w_new, -1.0, 1.0)
            jit_weights[i] = abs(w_new)
            jit_switches[i] = 1.0 if w_new >= 0 else -1.0

    # --- Superclass interface (unused in continuous mode, but kept for compatibility) ---

    def advance(self):
        '''No-op: the continuous uniselector has no stepping index.'''
        pass

    def produceNewValue(self):
        '''Not used in continuous mode.  Returns a random value for
        compatibility with code that expects the discrete interface.'''
        return numpy.random.uniform(self._lowerBound, self._upperBound)
