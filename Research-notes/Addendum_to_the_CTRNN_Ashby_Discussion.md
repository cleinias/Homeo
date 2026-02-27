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

*Models discussed: Beer & Gallagher (1992) CTRNN; W.R. Ashby, Design for a Brain (1960)*
