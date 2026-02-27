# Phototaxis Experiment Comparison: Four Adaptive Mechanisms

## Purpose

Compare four progressively richer adaptive mechanisms on the same
phototaxis task (negative irradiance, Braitenberg-2 cross-wired
topology) to determine whether:

1. The Ornstein-Uhlenbeck continuous uniselector matches or exceeds
   Ashby's discrete stepping switch on the same task (Exp 1 vs 2).
2. Evolving per-unit body parameters via a GA provides additional
   benefit beyond continuous weight drift alone (Exp 2 vs 3).
3. Evolving per-unit timescale parameters (tau_a, dt_fast) via a GA
   provides further benefit beyond fixed-timestep GA evolution (Exp 3
   vs 4).

All four experiments use negative light intensity (phototaxis: robot
seeks the light source).  Fitness = Euclidean distance from target,
minimised.

---

## Parameters Held Constant Across All Four Experiments

The following asymmetries from the original plan have been resolved:
all four experiments now share the same motor responsiveness, mass
range, initial connection weight range, and run length.

| Parameter               | Value                        |
|-------------------------|------------------------------|
| Topology                | Braitenberg-2 cross-wiring   |
| Light intensity         | -100 (phototaxis)            |
| Backend simulator       | HOMEO                        |
| Physics model           | Newtonian (2nd order ODE)    |
| Self-connection state   | `manual` (protected)         |
| Sensor-only units       | Passive input, no uniselector|
| Headless mode           | True                         |
| mass                    | U(1, 10)                     |
| max_speed_fraction      | 0.8                          |
| switching_rate          | 0.5                          |
| Initial conn weights    | U(-0.1, 0.1)                |
| Run length              | 60,000 simulated seconds     |

---

## Experiment 1: Standalone Ashby (Discrete Uniselector)

**Script:** `phototaxis_braitenberg2_Ashby.py --fixed-topology --dark`

The baseline.  Ashby's original design: a linear second-order ODE
with discrete random resampling of connection weights when essential
variables exceed a threshold.  No GA — a single run.

### Unit parameters

| Parameter         | Value / Range           | Notes                              |
|-------------------|-------------------------|------------------------------------|
| mass              | U(1, 10)                | Override of default 100            |
| viscosity         | U(0.8, 10)              | From `setRandomValues()`           |
| maxDeviation      | 10 (default)            | Not randomised                     |
| noise (unit)      | U(0, 0.1)               | From `setRandomValues()`           |
| potentiometer     | U(0, 1)                 | From `setRandomValues()`           |
| switch            | random +1 / -1          | From `setRandomValues()`           |
| critThreshold     | 0.9                     | Ratio of deviation to maxDeviation |
| uniselectorTimeInterval | 100 (default)     | Ticks between uniselector checks   |
| dt_fast           | 1.0 (implicit)          | Standard Verlet timestep           |

### Uniselector

- **Type:** Ashby stepping switch (`HomeoUniselectorAshby`)
- **Mechanism:** Every `uniselectorTimeInterval` ticks, if essential
  variable is critical (deviation/maxDeviation > critThreshold), a new
  random weight is drawn from an equally-spaced grid in [-1, 1].
- **Self-connections:** `state='manual'` (protected from uniselector)
- **Cross-connections:** `state='uniselector'`

### Connection parameters

| Parameter         | Self-connection     | Cross-connection       |
|-------------------|---------------------|------------------------|
| weight            | U(-0.1, 0.1)       | U(-0.1, 0.1)          |
| noise             | U(0, 0.05)          | U(0, 0.1)             |
| state             | `manual`            | `uniselector`          |
| status            | True                | True (cross-wired only)|

### Motor parameters

| Parameter           | Value | Notes                             |
|---------------------|-------|-----------------------------------|
| max_speed_fraction  | 0.8   | Overrides actuator default 0.2    |
| switching_rate      | 0.5   | Overrides actuator default 0.1    |

### Run parameters

| Parameter         | Value       |
|-------------------|-------------|
| light_intensity   | -100        |
| total_steps       | 60,000      |
| report_interval   | 500         |
| headless          | True        |

---

## Experiment 2: Standalone Continuous OU (Fixed Timestep)

**Script:** `phototaxis_braitenberg2_Ashby.py --fixed-topology --continuous --dark`

Same topology, same unit randomisation, but the discrete stepping
switch is replaced by a continuous Ornstein-Uhlenbeck process on the
connection weights.  All timescale parameters are fixed at defaults.
No GA — a single run.

### Unit parameters

Identical to Experiment 1 (same `setRandomValues()` + mass override).

### Uniselector

- **Type:** Continuous OU (`HomeoUniselectorContinuous`)
- **Mechanism:** Every timestep, each active connection weight drifts:
  `dw = -(theta/tau_a) * w * dt + sigma(stress) * sqrt(dt) * N(0,1)`
- **sigma(s) =** `sigma_base + (sigma_crit - sigma_base) * s^stress_exponent`

| Parameter        | Value   | Meaning                                  |
|------------------|---------|------------------------------------------|
| tau_a            | 1000.0  | OU slow timescale (fixed)                |
| theta            | 0.01    | Mean-reversion rate (leash strength)     |
| sigma_base       | 0.001   | Noise at equilibrium (exploration floor) |
| sigma_crit       | 0.1     | Noise at full stress (search intensity)  |
| stress_exponent  | 2.0     | Nonlinear shaping of stress -> noise     |
| dt               | 1.0     | OU integration timestep                  |

### Connection parameters

Identical to Experiment 1.

### Motor parameters

Identical to Experiment 1.

### Run parameters

| Parameter         | Value       |
|-------------------|-------------|
| light_intensity   | -100        |
| total_steps       | 60,000      |
| report_interval   | 500         |
| headless          | True        |

### Key difference from Experiment 1

The only change is the uniselector type.  Instead of periodic
threshold-check + random resampling, weights drift continuously with
noise proportional to the essential variable's displacement.

---

## Experiment 3: Weight-Free GA with Fixed Timestep

**Experiment function:** `initializeBraiten2_2_Full_GA_continuous_weightfree_fixed_dt`

A genetic algorithm evolves the physical parameters of each unit,
while the OU process handles connection weights online.  The
integration timestep `dt_fast` is fixed at 1.0, matching Experiments
1 and 2.  This isolates the contribution of GA-evolved body parameters
from any timescale effects.

### Genome

16 genes = 4 evolved units x 4 genes per unit.

| Gene index | Parameter     | Mapping             | Range            |
|------------|---------------|---------------------|------------------|
| 0          | mass          | linear              | [1, 10]          |
| 1          | viscosity     | linear              | [0, 10]          |
| 2          | tau_a         | logarithmic         | [100, 10000]     |
| 3          | maxDeviation  | linear              | [0.1, 1000]      |

Gene-to-parameter conversion:
- `mass = 1.0 + param * 9.0` &mdash; same responsive range as Exp 1-2
- `viscosity = param * 10`
- `tau_a = 100 * (100 ^ param)` &mdash; 0 &rarr; 100, 0.5 &rarr; 1000, 1 &rarr; 10000
- `maxDeviation = 0.1 + param * 999.9`
- `dt_fast = 1.0` (fixed, not in genome)

### Uniselector

- **Type:** Continuous OU (`HomeoUniselectorContinuous`)
- **tau_a:** Evolved per unit (gene 2)
- **theta, sigma_base, sigma_crit, stress_exponent:** Defaults
  (same as Experiment 2)

### Connection parameters

| Parameter         | Self-connection     | Cross-connection       |
|-------------------|---------------------|------------------------|
| weight            | U(-0.1, 0.1)       | U(-0.1, 0.1)          |
| noise             | 0.05                | 0.05                   |
| state             | `manual`            | `uniselector`          |
| status            | True                | True (cross-wired only)|

### Motor parameters

| Parameter           | Value | Notes                             |
|---------------------|-------|-----------------------------------|
| max_speed_fraction  | 0.8   | Same as Exp 1-2                   |
| switching_rate      | 0.5   | Same as Exp 1-2                   |

### GA parameters

| Parameter            | Value       |
|----------------------|-------------|
| population_size      | 150         |
| generations          | 100         |
| steps_per_evaluation | 60,000      |
| crossover_prob       | 0.5         |
| mutation_prob        | 0.2         |
| indiv_gene_mut_prob  | 0.05        |
| tournament_size      | 3           |
| workers              | 8           |
| fitness              | distance (minimised, sign = 1) |

### Run parameters

| Parameter         | Value       |
|-------------------|-------------|
| light_intensity   | -100        |
| total_steps       | 60,000 (per GA evaluation) |
| headless          | True        |

### Key difference from Experiment 2

The OU parameters (specifically tau_a) and unit body parameters (mass,
viscosity, maxDeviation) are now evolved by the GA rather than being
drawn randomly once.  dt_fast remains fixed at 1.0, so 60,000
simulated seconds = 60,000 ticks, exactly as in Experiments 1 and 2.

---

## Experiment 4: Weight-Free GA with Evolvable Timescales

**Experiment function:** `initializeBraiten2_2_Full_GA_continuous_weightfree_fixed`

Same as Experiment 3, but with an additional evolved parameter:
`dt_fast`, the Verlet integration timestep.  This allows the GA to
discover per-unit timescales that enable effective self-organisation.

### Genome

20 genes = 4 evolved units x 5 genes per unit.

| Gene index | Parameter     | Mapping             | Range            |
|------------|---------------|---------------------|------------------|
| 0          | mass          | linear              | [1, 10]          |
| 1          | viscosity     | linear              | [0, 10]          |
| 2          | tau_a         | logarithmic         | [100, 10000]     |
| 3          | maxDeviation  | linear              | [0.1, 1000]      |
| 4          | dt_fast       | linear              | [0.2, 2.0]       |

Gene-to-parameter conversion:
- `mass = 1.0 + param * 9.0` &mdash; same responsive range as Exp 1-3
- `viscosity = param * 10`
- `tau_a = 100 * (100 ^ param)` &mdash; 0 &rarr; 100, 0.5 &rarr; 1000, 1 &rarr; 10000
- `maxDeviation = 0.1 + param * 999.9`
- `dt_fast = 0.2 + param * 1.8` &mdash; 0 &rarr; 0.2, ~0.44 &rarr; 1.0, 1 &rarr; 2.0

### Uniselector

- **Type:** Continuous OU (`HomeoUniselectorContinuous`)
- **tau_a:** Evolved per unit (gene 2)
- **theta, sigma_base, sigma_crit, stress_exponent:** Defaults
  (same as Experiment 2)

### Connection parameters

| Parameter         | Self-connection     | Cross-connection       |
|-------------------|---------------------|------------------------|
| weight            | U(-0.1, 0.1)       | U(-0.1, 0.1)          |
| noise             | 0.05                | 0.05                   |
| state             | `manual`            | `uniselector`          |
| status            | True                | True (cross-wired only)|

### Motor parameters

| Parameter           | Value | Notes                             |
|---------------------|-------|-----------------------------------|
| max_speed_fraction  | 0.8   | Same as Exp 1-3                   |
| switching_rate      | 0.5   | Same as Exp 1-3                   |

### GA parameters

| Parameter            | Value       |
|----------------------|-------------|
| population_size      | 150         |
| generations          | 100         |
| steps_per_evaluation | 60,000      |
| crossover_prob       | 0.5         |
| mutation_prob        | 0.2         |
| indiv_gene_mut_prob  | 0.05        |
| tournament_size      | 3           |
| workers              | 8           |
| fitness              | distance (minimised, sign = 1) |

### Run parameters

| Parameter         | Value       |
|-------------------|-------------|
| light_intensity   | -100        |
| total_steps       | 60,000 simulated seconds (per GA evaluation) |
| headless          | True        |

---

## Note on simulated time, ticks, and dt_fast

Throughout all four experiments, **"steps" means simulated seconds**,
not computational ticks.  This is a unit of time, not a unit of
computation.

In Experiments 1, 2, and 3, `dt_fast = 1.0` (implicit or fixed), so
one tick equals one simulated second: 60,000 steps = 60,000 ticks.

In Experiment 4, `dt_fast` is evolved per unit and ranges from 0.2 to
2.0.  Each tick advances a unit's Verlet integrator by `dt_fast`
simulated seconds — a unit with `dt_fast = 0.5` covers 0.5 simulated
seconds per tick, while a unit with `dt_fast = 2.0` covers 2.0.
Different units within the same individual will generally have
different dt_fast values, so they advance at different rates per tick.

To ensure **all units experience at least 60,000 simulated seconds**,
the GA evaluation computes the actual tick count as:

```
actual_ticks = ceil(60000 / min(dt_fast across all units))
```

For example, if the smallest dt_fast in an individual is 0.2, the
evaluation runs for `ceil(60000 / 0.2) = 300,000 ticks`.  Units with
larger dt_fast values will experience proportionally more simulated
time (e.g., a unit with dt_fast = 1.0 will experience 300,000
simulated seconds in the same run).

This means **Experiment 4 evaluations will generally take longer than
Experiments 1-3** in wall-clock time, because more ticks are needed to
cover the same simulated time.  The per-tick computation cost is
unchanged regardless of dt_fast.

**Computation budget.** The worst case (all units at dt_fast = 0.2)
requires 300,000 ticks per evaluation.  At 150 population and 100
generations: ~150 x 100 x 300k = 4.5 billion ticks total, distributed
across 8 workers.  Typical cases (mixed dt_fast values around 1.0)
will be closer to the 900M tick baseline.  Consider reducing
population_size or generations if wall-clock time is prohibitive.

---

## What Varies Across Experiments

| Parameter               | Exp 1 (Ashby)    | Exp 2 (OU standalone) | Exp 3 (GA fixed dt)   | Exp 4 (GA variable dt) |
|-------------------------|-------------------|-----------------------|-----------------------|------------------------|
| **Adaptation type**     | Standalone        | Standalone            | GA                    | GA                     |
| **Uniselector type**    | Ashby stepping    | OU continuous         | OU continuous         | OU continuous          |
| **Weight adaptation**   | Periodic random   | Continuous drift      | Continuous drift      | Continuous drift       |
| **dt_fast**             | 1.0 (fixed)       | 1.0 (fixed)           | 1.0 (fixed)           | [0.2, 2.0] (evolved)  |
| **tau_a**               | N/A               | 1000 (fixed)          | [100, 10000] (evolved)| [100, 10000] (evolved) |
| **viscosity**           | U(0.8, 10)        | U(0.8, 10)            | [0, 10] (evolved)     | [0, 10] (evolved)      |
| **maxDeviation**        | 10 (default)      | 10 (default)          | [0.1, 1000] (evolved) | [0.1, 1000] (evolved)  |
| **mass**                | U(1, 10)          | U(1, 10)              | [1, 10] (evolved)     | [1, 10] (evolved)      |
| **Genome size**         | N/A               | N/A                   | 16 genes              | 20 genes               |
| **Ticks per evaluation**| 60,000            | 60,000                | 60,000                | ceil(60k / min dt_fast)|
| **Adaptation scope**    | Within-lifetime   | Within-lifetime       | GA + within-lifetime  | GA + within-lifetime   |

---

## Hypotheses

**H1:** The OU continuous uniselector (Exp 2) will match or exceed the
Ashby stepping switch (Exp 1) on convergence time and final distance,
because continuous drift explores the weight space more efficiently
than periodic random resampling.

**H2:** GA-evolved body parameters with fixed dt_fast (Exp 3) will
outperform standalone OU (Exp 2), because the GA can discover
per-unit tau_a, viscosity, and maxDeviation values that create
favourable conditions for the OU weight adaptation.

**H3:** Adding evolvable dt_fast (Exp 4) will further improve
performance over fixed dt_fast (Exp 3), because different units in
the circuit benefit from different integration timescales
(fast-adapting sensors, slow-adapting motors, or vice versa).

**H4:** Both weight-free genomes (Exp 3: 16 genes, Exp 4: 20 genes)
will converge faster than the 40-gene genome (previous GA run,
fitness 4.053) because the GA search space is halved and the GA is
no longer fighting the OU process for control of connection weights.

---

*Document created: 2026-02-26*
*Last updated: 2026-02-27*
*Related: Details_of_the_Ornstein-Uhlenbeck_uniselector.md, CTRNN_Ashby_Discussion.md*
