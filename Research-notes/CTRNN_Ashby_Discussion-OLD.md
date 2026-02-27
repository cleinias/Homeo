# CTRNN, Ashby's Homeostat, and Equilibrium-Seeking Dynamics

*Conversation excerpt on neural models and cybernetic theory*

---

## 1. CTRNN Model: Source of Nonlinearity

The standard differential equation model of a CTRNN unit (Beer & Gallagher, 1992) consists of two equations.

**Equation 1** — the ODE for each neuron *i*:

$$\tau_i \dot{y}_i = -y_i + \sum_{j=1}^N w_{ji} z_j + I_i$$

This is **linear** in all its terms — a weighted sum of inputs plus an external current $I_i$, minus a decay term. If this were the whole story, the network would be a linear dynamical system.

**Equation 2** — where the nonlinearity enters:

$$z_j = \frac{1}{1 + e^{b_j - y_j}}$$

This is the **sigmoid (logistic) function** applied to the internal state $y_j$, shifted by a bias $b_j$. The nonlinearity is the exponential in the denominator.

What feeds into Equation 1 is not $y_j$ directly, but $z_j$ — the output of neuron *j* after passing through the sigmoid. This breaks linearity and gives the network its computational power: a purely linear network can only compute linear functions of its inputs, regardless of depth or width.

The sigmoid models the **firing rate** of a biological neuron — below threshold it is nearly silent, above threshold it saturates. The bias $b_j$ shifts where that threshold sits for each neuron.

---

## 2. Ashby's Homeostat: A Linear ODE in Service of a Nonlinear Hypothesis

Ashby's homeostat unit equation (*Design for a Brain*, 1960):

$$m\ddot{x}_i = -k\dot{x}_i + l(p-q)\sum_{j=1}^N a_{ij} x_j$$

Where $x_i$ is the needle's angle of deviation, $m$ is moment of inertia, $k$ represents frictional forces, $l$ is a gain parameter (depends on the valve), and $p$, $q$ are potentials at the opposite ends of the fluid-filled trough.

This is a **second order linear ODE** — every term is linear: constant coefficient times second derivative ($m\ddot{x}_i$), constant coefficient times first derivative ($-k\dot{x}_i$), and a weighted sum of state variables all to the first power. No exponentials, no products of state variables, no squared terms.

The linearity of Ashby's ODE is not incidental — it is **in service of the design hypothesis**. The homeostat is designed so that each unit naturally seeks a fixed point ($x_i = 0$). The random resampling of the $a_{ij}$ weights is a search strategy over the space of linear systems until one is found whose fixed point is stable and within the essential variables' range. Equilibrium-seeking is the *meaning* of the device, not just a property of it.

---

## 3. Is Equilibrium Present in a CTRNN?

A CTRNN certainly has fixed points — states $y^*$ where $\dot{y}_i = 0$ for all *i*. The network may converge to them depending on the weights. But there is a crucial difference:

**In Ashby's homeostat**, convergence to equilibrium is the *goal* — the whole point of the device. The weights are resampled until equilibrium is guaranteed.

**In a CTRNN**, fixed points are just one possible behavior among many. Depending on weights, the system can exhibit stable fixed points, but also limit cycles, multistability, and chaos. Beer and others have exploited precisely these non-equilibrium behaviors to model locomotion rhythms and neural oscillators. The *interesting* cases are often the ones that do *not* settle.

The notion of equilibrium is mathematically present in CTRNNs but theoretically **neutral** — it carries none of the normative weight it has in Ashby. The CTRNN is a neutral dynamical substrate: a sufficiently general continuous-time nonlinear dynamical system that can approximate many behaviors.

---

## 4. Ashby's Philosophical Hypothesis: Conservative Systems and Dynamic Environments

The deeper question is whether an essentially conservative system like Ashby's can produce non-stable behaviors given an essentially dynamic environment.

Ashby's hypothesis is subtler than simply "systems seek equilibrium." He claims that what *looks like* rich, adaptive, non-equilibrium behavior from the outside can be **fully explained** as a sequence of equilibrium-seeking episodes in a system whose parameters are being continuously perturbed by the environment. The behavior is in the *interaction*, not in the system alone.

This is a genuinely radical inversion of the standard engineering assumption: if you want complex dynamic behavior, build complexity into the system. Beer does this — rich CTRNN dynamics produce rich behavior directly. Ashby says: you do not need that. A fundamentally simple, conservative system plus a sufficiently rich environment *generates* apparent complexity for free. **The complexity is not in the system — it is in the system-environment coupling.**

This connects directly to Ashby's concept of **ultrastability** — a system can be stable at a higher level (survives, maintains essential variables) precisely because it is unstable at a lower level (keeps resetting its own parameters). The nonlinearity in the homeostat is discrete and external to the differential equation itself, triggered by threshold crossings. The ODE between resets is linear.

---

## 5. The Honest Tension

Ashby's hypothesis works beautifully for explaining *adaptation* and *robustness*. It is less convincing for **rhythmic, anticipatory, or coordinated behaviors** — things like locomotion, where the non-equilibrium dynamics seem to be the point, not a byproduct of environmental perturbation. A walking animal is not being knocked out of equilibrium by the ground — it is actively generating a structured dynamic pattern.

This is precisely where Beer's CTRNN approach has an advantage — and Beer was deeply aware of Ashby, consciously positioning his work in that tradition while departing from it.

The open question remains: **is Ashby's conservative hypothesis sufficient, or does biology require something more** — a system that does not just tolerate non-equilibrium but actively *produces* and *exploits* it?

---

## 6. Modernizing the Uniselector While Preserving Ashby's Bet

The question arises whether Ashby's crude switching mechanism — introduced largely due to the technical limitations of 1950 — could be replaced by something more formally elegant without abandoning his core philosophical hypothesis.

The key constraint is this: **the adaptive mechanism must operate on the parameters, not within the dynamics**. That is what keeps Ashby's bet intact. Replacing the uniselector with a sigmoid coupling between units — while superficially attractive — would quietly abandon the hypothesis, since it would build adaptive competence into the continuous dynamics themselves rather than leaving it to blind search at the parameter level.

Three directions are worth considering:

**Stochastic differential equations for parameter drift.** Instead of discrete random resampling, let the $a_{ij}$ weights evolve continuously according to a noise-driven process — for instance a mean-reverting Ornstein-Uhlenbeck process:

$$d a_{ij} = -\theta a_{ij} \, dt + \sigma \, dW_t$$

Where $dW_t$ is a Wiener process. The trigger condition (essential variable out of range) modulates $\sigma$ — noise is amplified when the system is far from equilibrium, suppressed when stable. This replaces discrete resampling with continuous drift under noise, preserving randomness and parameter-level operation.

**Hebbian or anti-Hebbian learning rules.** Let weights adapt according to correlations between unit states. This is parameter-level and continuous, but directed rather than random — potentially too competent for Ashby's purposes. An anti-Hebbian or decorrelating variant could recover some of Ashby's flavor by actively destabilizing current configurations when the system is off-target.

**Metadynamics / slow-fast systems.** The most formally elegant option. The system is written as two coupled equations operating on different timescales:

$$m\ddot{x}_i = -k\dot{x}_i + l(p-q)\sum_j a_{ij} x_j \quad \text{(fast: Ashby's original dynamics, intact)}$$

$$\tau_a \dot{a}_{ij} = f(x_1, \ldots, x_N) \quad \text{(slow: stochastic parameter adaptation)}$$

With $\tau_a \gg \tau / m$, so the $a_{ij}$ look nearly constant to the fast system at any given moment. Crucially, **Ashby's second order ODE is preserved in full** — inertia, friction, coupling — while the slow equation operates on its parameters. The function $f$ encodes noise-driven drift that intensifies under failure, replacing the binary threshold switch with a continuous modulation of search intensity.

---

## 7. Three Timescales

The slow-fast formulation (options 1+3 combined) reveals that the full system implicitly has **three timescales**:

- **Instantaneous**: the needle's inertial response ($m\ddot{x}_i$) — the physics of the unit itself
- **Fast**: relaxation toward equilibrium within a given $a_{ij}$ configuration — the ODE dynamics
- **Slow**: stochastic drift of the $a_{ij}$ themselves, intensifying when essential variables are far from zero — the adaptive search

This three-level structure is arguably more faithful to Ashby's original intuition than the uniselector was. His switching was always meant to be slow relative to the unit dynamics — the uniselector only fires after the system has demonstrably failed to find equilibrium. The SDE formulation makes this timescale separation explicit and continuous rather than implicit and discrete.

It also connects naturally to biological interpretations: the fast dynamics are neural, the slow dynamics are something like neuromodulation or synaptic consolidation — a distinction the neuroscience literature has independently found useful.

---

## 8. Implementation: The OU Process in Practice

### The Ornstein-Uhlenbeck Process

The OU process provides a mathematically clean replacement for the uniselector. It combines a deterministic pull back toward zero with continuous random noise:

$$da_{ij} = -\theta \, a_{ij} \, dt + \sigma \, dW_t$$

Where $dW_t$ is a Wiener process (continuous random noise). The $-\theta \, a_{ij} \, dt$ term acts like a leash — the further a weight drifts from zero, the stronger it is pulled back. The $\sigma \, dW_t$ term provides the random search. The result is a bounded, jittery process that explores a neighborhood of zero indefinitely without drifting to infinity.

The long-run behavior is a Gaussian stationary distribution centered at zero with variance $\sigma^2 / 2\theta$. The relaxation time — how long it takes to forget its initial condition — is $1/\theta$.

### Making Noise Proportional to Displacement

For a single unit, the most natural and parsimonious choice is to make $\sigma$ proportional to the essential variable:

$$\sigma(x_i) = \alpha |x_i|$$

Which gives:

$$da_{ij} = -\theta \, a_{ij} \, dt + \alpha |x_i| \, dW_t$$

This means:
- When $x_i = 0$ (unit at equilibrium) — noise vanishes, weights stop drifting, the system stays where it is
- As $x_i$ grows (unit displaced) — noise grows proportionally, search intensifies

This is a strictly stronger formalization than Ashby's binary threshold: instead of a yes/no switch, search intensity is continuously proportional to displacement. Note that because $\sigma$ now depends on the state variable, this is **multiplicative noise** — the Itô/Stratonovich distinction becomes relevant, unlike in the simple constant-$\sigma$ case.

### Discretized Implementation

The continuous OU equation discretizes to:

$$a_{ij} \leftarrow a_{ij} - \theta \, a_{ij} \, \Delta t + \alpha \, |x_i| \, \sqrt{\Delta t} \, \eta$$

Where $\eta \sim \mathcal{N}(0,1)$ is a fresh standard normal random draw at each step. The $\sqrt{\Delta t}$ factor is essential: it comes from the statistics of Brownian motion, where variance grows linearly with time, so standard deviation grows as $\sqrt{\Delta t}$.

### The Unit's State and Per-Timestep Logic

```
HomeoUnit state:
  x            # essential variable (needle position)
  x_dot        # velocity
  m            # mass (fixed)
  k            # friction (fixed)
  l            # gain (fixed)
  p, q         # potentials (fixed or externally driven)
  a[]          # weight vector (dynamic)
  theta        # OU mean-reversion rate
  alpha        # noise scaling factor
  tau_a        # timescale of weight adaptation
  accumulator  # tracks time since last weight update
```

Each timestep executes two steps in order:

**Step 1 — fast dynamics** (runs every timestep):

```python
x_ddot = (1/m) * (
    -k * x_dot
    + l * (p - q) * sum(a[j] * neighbors[j].x for j in range(N))
)
x_dot += x_ddot * dt
x     += x_dot * dt        # or use Verlet
```

**Step 2 — slow dynamics** (runs at reduced rate governed by $\tau_a$):

```python
accumulator += dt
if accumulator >= tau_a:
    effective_dt = accumulator
    for j in range(N):
        eta = random.gauss(0, 1)
        a[j] += (
            - theta * a[j] * effective_dt
            + alpha * abs(x) * sqrt(effective_dt) * eta
        )
    accumulator = 0.0
```

The accumulator pattern handles fractional multiples of $\Delta t$ cleanly — the weight update fires whenever enough fast-timestep time has elapsed, with no requirement that $\tau_a$ be an integer multiple of $\Delta t$.

### The Role of $\theta$ and $\alpha$

The two parameters do distinct jobs:

- $\theta$ controls **how strongly weights are pulled back toward zero** — the size of the leash. Larger $\theta$ means weights stay close to zero even under sustained displacement.
- $\alpha$ controls **how vigorously weights respond to displacement** — closer to what intuitively feels like "leap size into parameter space." The actual step size per iteration is roughly $\alpha \, |x_i| \, \sqrt{\Delta t}$, so both $\alpha$ and the timestep jointly determine leap magnitude.

---

## 9. Explicit Timescale Separation and the Genome

### Making $\tau_a$ Explicit

The accumulator approach above makes the timescale separation a first-class parameter of the model rather than something implicit in the choice of $\alpha$ or $\Delta t$. This is good modeling practice: the three levels of the system — inertial response, ODE relaxation, weight adaptation — remain cleanly separated and independently adjustable, making the model's behavior easier to interpret and debug.

This is directly analogous to DiPaolo's CTRNN implementation, where each unit has its own $\tau_i$ controlling its effective update rate. Running the update cycle 5 times per unit is equivalent to setting $\tau_i = 5\Delta t$ — both are valid discretizations of the same underlying timescale separation.

### What Goes in the Genome

When the model is run under a genetic algorithm, the genome encodes **how each unit adapts**, not **what it has learned**. The weight values $a_{ij}$ are dynamic variables that change during the lifetime of the individual through the OU process — they are ontogenetic, not phylogenetic.

Per unit, the genome encodes:

```
tau_a      # timescale of weight adaptation
theta      # OU mean-reversion rate
alpha      # noise scaling factor
```

The mechanical parameters $m$, $k$, $l$ are fixed physics, not evolved. The weights $a_{ij}$ are dynamic state, not genome.

### A Clean Conceptual Hierarchy

This gives the model three well-separated levels:

- **Phylogenetic** (genome, fixed for lifetime): $\tau_a$, $\theta$, $\alpha$ — the search strategy
- **Ontogenetic** (changes during lifetime): $a_{ij}$ — the result of search
- **Dynamic** (changes every timestep): $x_i$, $\dot{x}_i$ — moment-to-moment behavior

This is not just computationally tidy — it maps onto a genuine biological distinction between what is inherited, what is learned, and what is currently happening. Ashby himself was deeply interested in this distinction, and the formalization makes it explicit in a way his original hardware could not.

### Design Choice: How Much to Evolve

A more constrained alternative is to fix $\theta$ globally and only evolve $\alpha$ and $\tau_a$ per unit. This says the *shape* of the leash is universal but the *sensitivity to failure* and the *timescale of adaptation* are individually tuned. Reducing the genome in this way shrinks the search space for the genetic algorithm and may be a sensible starting point before opening up all three parameters to evolution.

Whether heterogeneous $\tau_a$ values across units turn out to be functionally significant — as heterogeneous $\tau_i$ values are in evolved CTRNNs — is itself an interesting experimental question the model is now positioned to ask.

---

*Models discussed: Beer & Gallagher (1992) CTRNN; W.R. Ashby, Design for a Brain (1960)*
