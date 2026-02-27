# Details of the Ornstein-Uhlenbeck Uniselector

## Overview

The continuous uniselector replaces Ashby's discrete stepping switch
with an Ornstein-Uhlenbeck (OU) stochastic differential equation that
evolves connection weights at every simulation timestep.  The
implementation has four main pieces: the uniselector class itself, the
stress metric, the integration into the unit update loop, and the JIT
path for GA/headless mode.

See also:
- `Addendum_to_the_CTRNN_Ashby_Discussion.md`, Section 6
  ("Metadynamics / slow-fast systems")
- `CTRNN_Ashby_Discussion.md`, Sections 7-9 (timescales, OU
  mathematics, genome design)


## 1. Theoretical background

### 1.1 Three timescales

The slow-fast formulation reveals that the full system implicitly has
**three timescales**:

- **Instantaneous**: the needle's inertial response ($m\ddot{x}_i$)
  -- the physics of the unit itself
- **Fast**: relaxation toward equilibrium within a given $a_{ij}$
  configuration -- the ODE dynamics
- **Slow**: stochastic drift of the $a_{ij}$ themselves, intensifying
  when essential variables are far from zero -- the adaptive search

This three-level structure is arguably more faithful to Ashby's
original intuition than the uniselector was.  His switching was always
meant to be slow relative to the unit dynamics -- the uniselector only
fires after the system has demonstrably failed to find equilibrium.
The SDE formulation makes this timescale separation explicit and
continuous rather than implicit and discrete.

It also connects naturally to biological interpretations: the fast
dynamics are neural, the slow dynamics are something like
neuromodulation or synaptic consolidation -- a distinction the
neuroscience literature has independently found useful.

This is directly analogous to DiPaolo's CTRNN implementation, where
each unit has its own $\tau_i$ controlling its effective update rate.


### 1.2 The Ornstein-Uhlenbeck process

The OU process combines a deterministic pull back toward zero with
continuous random noise:

$$da_{ij} = -\theta \, a_{ij} \, dt + \sigma \, dW_t$$

where $dW_t$ is a Wiener process (continuous random noise).  The
$-\theta \, a_{ij} \, dt$ term acts like a leash -- the further a
weight drifts from zero, the stronger it is pulled back.  The
$\sigma \, dW_t$ term provides the random search.  The result is a
bounded, jittery process that explores a neighborhood of zero
indefinitely without drifting to infinity.

The long-run behavior is a Gaussian stationary distribution centered
at zero with variance $\sigma^2 / 2\theta$.  The relaxation time --
how long it takes to forget its initial condition -- is $1/\theta$.


### 1.3 Making noise proportional to displacement

For a single unit, the most natural and parsimonious choice is to make
$\sigma$ proportional to the essential variable:

$$\sigma(x_i) = \alpha |x_i|$$

Which gives:

$$da_{ij} = -\theta \, a_{ij} \, dt + \alpha |x_i| \, dW_t$$

This means:
- When $x_i = 0$ (unit at equilibrium) -- noise vanishes, weights
  stop drifting, the system stays where it is
- As $x_i$ grows (unit displaced) -- noise grows proportionally,
  search intensifies

This is a strictly stronger formalization than Ashby's binary
threshold: instead of a yes/no switch, search intensity is
continuously proportional to displacement.  Note that because $\sigma$
now depends on the state variable, this is **multiplicative noise** --
the Ito/Stratonovich distinction becomes relevant, unlike in the
simple constant-$\sigma$ case.


### 1.4 Discretization

The continuous OU equation discretizes to:

$$a_{ij} \leftarrow a_{ij} - \theta \, a_{ij} \, \Delta t + \sigma(x_i) \, \sqrt{\Delta t} \, \eta$$

where $\eta \sim \mathcal{N}(0,1)$ is a fresh standard normal random
draw at each step.  The $\sqrt{\Delta t}$ factor is essential: it
comes from the statistics of Brownian motion, where variance grows
linearly with time, so standard deviation grows as $\sqrt{\Delta t}$.

This is integrated via the Euler-Maruyama method -- the standard
first-order scheme for SDEs.


### 1.5 The roles of theta and sigma

The two parameters do distinct jobs:

- $\theta$ controls **how strongly weights are pulled back toward
  zero** -- the size of the leash.  Larger $\theta$ means weights stay
  close to zero even under sustained displacement.
- $\sigma$ (or $\alpha$, the scaling factor) controls **how vigorously
  weights respond to displacement** -- closer to what intuitively
  feels like "leap size into parameter space."  The actual step size
  per iteration is roughly $\sigma \, \sqrt{\Delta t}$, so both
  $\sigma$ and the timestep jointly determine leap magnitude.


---

## 2. Implementation: `HomeoUniselectorContinuous`

**File:** `src/Core/HomeoUniselectorContinuous.py`

The core SDE integrated at each tick via Euler-Maruyama is:

    dw = -(theta / tau_a) * w * dt  +  sigma(stress) * sqrt(dt) * N(0,1)

It has two terms:

- **Drift** (line 151): `-(theta / tau_a) * w * dt` -- a deterministic
  pull toward zero.  This is the mean-reversion term.  With the
  defaults (`theta = 0.01`, `tau_a = 1000`), the coefficient is tiny:
  `-0.00001 * w` per tick.  Over thousands of ticks, weights that are
  not being perturbed will slowly decay toward zero.  This is analogous
  to Ashby's idea that unused connections should weaken.

- **Diffusion** (line 152): `sigma * sqrt(dt) * randn()` -- Gaussian
  noise whose intensity depends on stress.  This is where the
  "searching" happens.  When the unit is comfortable (stress ~ 0),
  sigma is nearly zero (`sigma_base = 0.001`) and weights barely
  jitter.  When the essential variable is near its limits (stress -> 1),
  sigma ramps up to `sigma_crit = 0.1`, producing vigorous exploration
  -- the continuous analogue of the uniselector firing.

### The sigma function

The **sigma function** (lines 123-133) interpolates between baseline
and critical noise with nonlinear shaping:

```python
shaped = s ** stress_exponent     # default exponent = 2.0
return sigma_base + (sigma_crit - sigma_base) * shaped
```

With exponent 2, the noise stays very low until stress exceeds ~0.5,
then ramps up quadratically.  This keeps weights stable when the unit
is well within bounds, but triggers increasingly aggressive exploration
as it approaches criticality -- a smoother version of the binary
threshold in the discrete uniselector.

Note: the implementation uses `stressLevel()` (a normalized measure of
|critDev| / maxDev) rather than the raw essential variable $x_i$ as
the noise modulator.  This is a design choice: it normalizes across
units with different maxDeviation values, making the sigma parameters
unit-independent.  The theoretical treatment in section 1.3 uses
$\alpha |x_i|$ directly; the implementation's `sigma(stress)` is
functionally equivalent but parameterized differently.

### Default parameters

| Parameter        | Default | Role                                        |
|------------------|---------|---------------------------------------------|
| `tau_a`          | 1000.0  | Weight relaxation timescale (>> 1 for slow drift) |
| `theta`          | 0.01    | Mean-reversion rate (pulls weights toward 0) |
| `sigma_base`     | 0.001   | Baseline noise (exploration when stable)     |
| `sigma_crit`     | 0.1     | Noise when essential variable is critical    |
| `dt`             | 1.0     | Integration timestep (matches fast dynamics) |
| `stress_exponent`| 2.0     | Nonlinear shaping (1 = linear, 2 = quadratic) |


## 3. The stress metric -- `HomeoUnit.stressLevel()`

**File:** `src/Core/HomeoUnit.py`

The continuous uniselector needs a graded stress signal rather than a
binary "critical or not" check.  The `stressLevel()` method provides
this:

```python
def stressLevel(self):
    if self.maxDeviation == 0:
        return 0.0
    return min(abs(self.criticalDeviation) / self.maxDeviation, 1.0)
```

This maps `|critDev|` linearly into [0, 1], where 0 = needle at
centre, 1 = needle at the rail.  It is the continuous replacement for
`essentialVariableIsCritical()`, which returns a binary True/False
based on whether `|critDev| >= criticalThreshold * maxDev`.


## 4. Integration into the update loop -- `selfUpdate()`

**File:** `src/Core/HomeoUnitNewtonian.py`, lines 200-247

The `selfUpdate()` method branches on uniselector type at step 3
(weight adaptation):

```python
if isinstance(self.uniselector, HomeoUniselectorContinuous):
    # Continuous: evolve weights EVERY tick
    stress = self.stressLevel()
    self.uniselector.evolve_weights(self.inputConnections, stress)
else:
    # Discrete: original periodic check + random resampling
    self.updateUniselectorTime()
    if self.uniselectorTime >= self.uniselectorTimeInterval:
        if self.essentialVariableIsCritical():
            self.operateUniselector()
        ...
```

The key architectural difference: the discrete uniselector only fires
every `uniselectorTimeInterval` ticks (default 100) and only if the
essential variable is critical at that moment.  The continuous
uniselector touches weights on **every single tick**, but with noise
intensity proportional to stress.  The timescale separation
(`tau_a = 1000 >> 1`) ensures that even at maximum noise, weights
change slowly compared to the fast needle dynamics.

This preserves Ashby's core constraint from the Addendum: adaptation
operates on the *parameters* (connection weights), not within the
dynamics (the Newtonian needle ODE is untouched).

The same branching logic exists in the base class `HomeoUnit.selfUpdate()`
for the Aristotelian physics variant.


## 5. The JIT path -- `evolve_weights_jit()`

**File:** `src/Core/HomeoUniselectorContinuous.py`, lines 171-196

In headless/GA mode, units store weights and switches as bare numpy
arrays (`_jit_weights`, `_jit_switches`) rather than `HomeoConnection`
objects, bypassing the PyQt signal machinery.  The `evolve_weights_jit()`
method operates on these arrays in place:

```python
for i in range(n):
    w = jit_weights[i] * jit_switches[i]   # reconstruct signed weight
    w_new = w + drift_coeff * w + diffusion_scale * noise[i]
    w_new = numpy.clip(w_new, -1.0, 1.0)
    jit_weights[i] = abs(w_new)             # magnitude back to array
    jit_switches[i] = 1.0 if w_new >= 0 else -1.0  # sign back to array
```

The simulator stores weights as (magnitude, sign) pairs because that
is how Ashby's original hardware worked -- the switch is a physical
polarity reverser, and the potentiometer sets magnitude.  The OU
process works on the *signed* product, then decomposes back.  If the
noise drives a weight through zero, the switch flips -- the continuous
analogue of the discrete uniselector changing a connection's polarity.

After evolving, `_jit_dirty = True` is set so that `computeTorque()`
re-syncs on the next tick.


## 6. What is *not* changed (current implementation)

The fast dynamics -- the Newtonian needle ODE in
`newLinearNeedlePosition()` -- are completely untouched.  The
integration scheme (velocity Verlet with dt = 1), the Stokes drag,
the mass/viscosity parameters, the input torque computation -- all
identical.  The continuous uniselector is a pure parameter-level
intervention, exactly as the Addendum's section 6 prescribes.

### Timescale separation in the current implementation

The three timescales identified in section 1.1 map onto the code as
follows:

1. **Instantaneous** -- inertial response (mass, acceleration)
2. **Fast** -- needle dynamics (criticalDeviation, currentVelocity),
   O(1) ticks
3. **Slow** -- weight drift (OU process), O(tau_a) = O(1000) ticks

This separation ensures that the fast dynamics have time to settle
(or fail to settle) before the weights change appreciably, preserving
the logical structure of Ashby's step function: the system either
finds equilibrium with the current weights, or the weights drift until
it does.


---

## 7. Planned revision: evolvable timescales and weight-free genome

The initial implementation (sections 2-6) uses fixed OU parameters
and evolves connection weights via the GA alongside the unit physics.
This section describes a planned revision that makes both timescales
explicit and evolvable, and removes connection weights from the genome
entirely.


### 7.1 Making tau_a per-unit and evolvable

In the current implementation, `tau_a` is a fixed default (1000) on
the `HomeoUniselectorContinuous` object.  The existing GA genome
includes a `uniselector_timing` gene (index 2 per unit) that controls
the discrete uniselector's check interval -- a parameter that is
**completely ignored** in continuous mode.

We repurpose this gene: in continuous mode, gene index 2 maps to
`tau_a` instead of `uniselectorTimeInterval`.  The conversion maps
[0, 1) to a logarithmic range, e.g. [100, 10000]:

    tau_a = tau_a_min * (tau_a_max / tau_a_min) ^ gene_value

This costs zero extra genes -- the slot is already there, just
reinterpreted.  Each unit's OU uniselector gets its own `tau_a`,
allowing the GA to evolve different adaptation speeds for different
functional roles (sensors vs eyes vs motors).

Whether heterogeneous `tau_a` values across units turn out to be
functionally significant -- as heterogeneous $\tau_i$ values are in
evolved CTRNNs (cf. DiPaolo 2000) -- is itself an interesting
experimental question the model is now positioned to ask.


### 7.2 Introducing dt_fast -- an explicit fast-dynamics timescale

Currently the Verlet integrator in `newLinearNeedlePosition()` uses an
implicit dt = 1.  We introduce an explicit `dt_fast` parameter per
unit that scales the integration step:

```python
# Current (dt = 1 implicit):
displacement = self.currentVelocity + (1/2. * acceleration)

# With explicit dt_fast:
displacement = self.currentVelocity * self.dt_fast + (1/2. * acceleration * self.dt_fast**2)
```

And the velocity update in `selfUpdate()`:

```python
# Current:
self.currentVelocity = 2 * (newDeviation - self.criticalDeviation) - self.currentVelocity

# With explicit dt_fast:
self.currentVelocity = self.currentVelocity + acceleration * self.dt_fast
```

The gene maps [0, 1) to a bounded range, e.g. [0.2, 2.0]:

- **dt_fast < 1**: the needle is sluggish, taking more ticks to
  settle.  Timescale separation with the OU is *reduced*.
- **dt_fast = 1**: current behaviour, unchanged.
- **dt_fast > 1**: the needle responds rapidly, settling quickly
  relative to the OU.  Greater timescale separation.

This adds one new gene per evolved unit.  Upper bound should be kept
moderate (~ 2.0) to avoid numerical instability in the Verlet scheme.

An alternative approach would be **sub-stepping**: running `n_substeps`
needle iterations per OU step, each at dt = 1.  This is numerically
safer (always dt = 1 internally) but costs proportionally more compute
and requires restructuring `selfUpdate()` into an inner fast loop and
an outer slow step.  The dt_fast scaling is simpler and cheaper for a
first implementation.


### 7.3 Eliminating connection weights from the genome

With the OU process governing connection weights at every timestep,
the GA-evolved initial weight values are redundant.  The OU's
mean-reversion and stress-driven noise will drift the weights away
from their initial values within O(tau_a) ticks.  The GA is
effectively optimising parameters that the system immediately
"forgets."

We therefore remove all 24 connection weight genes from the genome.
The OU process alone is responsible for finding good weights online --
which is exactly what ultrastability means.

**Initial weight values at tick 0:** small random values drawn from
uniform[-0.1, 0.1].  This is consistent with the OU's mean-reversion
target near zero and gives the process a low-energy starting point
from which stress-driven noise can explore outward.


### 7.4 Conceptual hierarchy: phylogenetic, ontogenetic, dynamic

The weight-free genome produces a clean three-level hierarchy:

- **Phylogenetic** (genome, fixed for lifetime): mass, viscosity,
  tau_a, maxDeviation, dt_fast -- the *search strategy* and physical
  structure.  These are the parameters the *engineer* would choose
  when building the hardware.

- **Ontogenetic** (changes during lifetime): $a_{ij}$ connection
  weights -- the *result of search*.  These are what the uniselector
  is for: online, autonomous adaptation that the designer does not
  control.

- **Dynamic** (changes every timestep): $x_i$, $\dot{x}_i$ --
  moment-to-moment behavior.

This is not just computationally tidy -- it maps onto a genuine
biological distinction between what is inherited, what is learned, and
what is currently happening.  Ashby himself was deeply interested in
this distinction, and the formalization makes it explicit in a way his
original hardware could not.

In the discrete uniselector regime, the GA had to evolve weights
because the uniselector's random resampling was too crude to reliably
find good configurations in the allotted simulation time.  The
continuous OU process, with its stress-modulated noise and
mean-reversion, is a far more competent searcher -- it does not need
the GA to give it a head start.


### 7.5 Revised genome layout

```
Per evolved unit (5 genes):
  [0] mass           -->  m_i         (inertia, part of tau_fast)
  [1] viscosity      -->  eta_i       (damping, part of tau_fast)
  [2] tau_a          -->  tau_a_i     (OU slow timescale, repurposed from uniselector_timing)
  [3] maxDeviation   -->  maxDev_i    (essential variable range)
  [4] dt_fast        -->  dt_fast_i   (explicit fast integration step)   <-- NEW

No connection weight genes.

Total: 4 evolved units x 5 genes = 20 genes
```

Down from 40 genes in the current discrete-uniselector genome (or 44
if we had kept weights alongside the new timescale genes).  The
20-gene search space should converge substantially faster.

### Design choice: how much to evolve

A more constrained alternative is to fix $\theta$ globally and only
evolve `tau_a` and `dt_fast` per unit.  This says the *shape* of the
leash is universal but the *sensitivity to failure* and the *timescale
of adaptation* are individually tuned.  Reducing the genome in this
way shrinks the search space for the genetic algorithm and may be a
sensible starting point before opening up all parameters to evolution.


### 7.6 Effective timescale separation

With both `tau_a` and `dt_fast` evolvable per unit, the effective
timescale separation ratio for each unit becomes:

    R_i = tau_a_i / tau_fast_i

where `tau_fast_i = m_i / (eta_i * dt_fast_i)` is the characteristic
damping time of the needle dynamics.  Expanding:

    R_i = tau_a_i * eta_i * dt_fast_i / m_i

The GA can independently tune:

- How quickly each unit's needle responds (mass, viscosity, dt_fast)
- How quickly each unit's weights adapt (tau_a)
- The ratio between them (R)

Different functional roles might evolve different strategies:

- **Motor units**: large R (stable weights, responsive needle) --
  "don't change what works"
- **Eye units**: small R (weights track the signal, needle sluggish) --
  "stay flexible"
- Or the reverse -- the GA decides what works for the task at hand.


---

*Sources: W.R. Ashby, Design for a Brain (1960); Beer & Gallagher
(1992) CTRNN; DiPaolo (2000) evolved CTRNNs.  See also
`CTRNN_Ashby_Discussion.md` for the full theoretical context.*
