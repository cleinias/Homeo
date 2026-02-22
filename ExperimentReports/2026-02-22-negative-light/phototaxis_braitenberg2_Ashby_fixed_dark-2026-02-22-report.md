# Report on a "Darkness Source" Experiment: Braitenberg Type-2 Vehicle Driven by a Homeostat, February 22nd, 2026

## Overview

A Braitenberg type-2 vehicle controlled by a 6-unit homeostat was run in
Ashby fixed-topology mode with a **negated light intensity** (-100),
effectively turning the light source into a "darkness source": the closer
the robot gets, the more negative the irradiance at its sensors. The
robot started at position (4, 4), facing north, at a distance of 4.243
units from the target at (7, 7). The experiment was configured for up to
4,000,000 ticks but with an early-stop condition: halt if the robot
enters within 1.5 units of the target (the grey circle drawn by
TrajectoryGrapher).

**The robot reached the target zone in only 60,000 ticks**, arriving at
position (5.968, 5.970) with a final distance of **1.458** from the
target. This is in stark contrast to the positive-light experiment of
February 21st, where the robot moved *away* from the light over
2,000,000 ticks.

![Vehicle trajectory](trajectory_dark.pdf)

### Experiment parameters

| Parameter | Value |
|-----------|-------|
| Experiment | `phototaxis_braitenberg2_Ashby_fixed_dark` |
| Date | 2026-02-22 10:28:47 |
| Total steps (actual) | 60,000 (early stop) |
| Total steps (budget) | 4,000,000 |
| Topology | Ashby fixed (Braitenberg cross-wiring preserved) |
| Light intensity | **-100** (negated) |
| Early stop distance | 1.5 |
| Mass range | [1, 10] (randomised) |
| Motor max speed fraction | 0.8 |
| Motor switching rate | 0.5 |
| Uniselector time interval | 100 ticks |
| Critical threshold | 0.9 |
| Light attenuation vector | (0, 0, 1) --- pure quadratic decay |
| Light ambient ratio | 0 |

### Data files

- `phototaxis_braitenberg2_Ashby_fixed_dark-2026-02-22-10-28-47.traj` --- trajectory
- `phototaxis_braitenberg2_Ashby_fixed_dark-2026-02-22-10-28-47.log` --- initial and final conditions
- `phototaxis_braitenberg2_Ashby_fixed_dark-2026-02-22-10-28-47.json` --- experiment metadata


## Network topology

![Initial topology](topology_dark_initial.pdf)

![Final topology](topology_dark_final.pdf)

In the diagrams above, **green** nodes are within normal bounds, **red**
nodes are saturated at their deviation limits. Blue arcs are manual
(protected) connections; orange arcs are uniselector-controlled. Labels
show the effective weight (switch x weight).

The vehicle uses the same 6-unit Braitenberg type-2 (crossed) topology
as the positive-light experiment:

- **2 Sensor units** (HomeoUnitInput): Left Sensor, Right Sensor ---
  pure input transducers, no uniselector, `always_pos = True`
- **2 Eye units** (HomeoUnitNewtonian): Left Eye, Right Eye ---
  intermediate processing, uniselector active
- **2 Motor units** (HomeoUnitNewtonianActuator): Left Motor, Right Motor ---
  drive the wheels via a sigmoid mapping, uniselector active

Active connections (Braitenberg cross-wiring):

```
Left Sensor  -->  Left Eye   -->  Right Motor   -->  Right Wheel
Right Sensor -->  Right Eye  -->  Left Motor    -->  Left Wheel
```


## 1. The effect of negative irradiance

With `light_intensity = -100`, the irradiance formula becomes:

```
irradiance = -100 * cos(incidentAngle) / distance^2
```

This produces **negative** sensor readings that grow in magnitude as the
robot approaches the target. At the starting distance of 4.243, each
sensor reads approximately -5.6; at the final distance of 1.458, readings
exceeded -30.

Since the `HomeoUnitInput` sensors use `always_pos = True` with
`scaleTo([0, maxRange], [0, maxDev], irradiance)`, negative irradiance
maps directly to negative `critDev` and negative `output`. This means
the sensor units push negative values into the downstream eye and motor
units --- the opposite polarity from the positive-light experiment.


## 2. Internal variable values at start and end

### Unit parameters (unchanged during the run)

| Unit | Mass | Viscosity | Noise | Potentiometer | Switch | Uniselector |
|------|------|-----------|-------|---------------|--------|-------------|
| Right Motor | 8.348 | 2.305 | 0.017 | 0.696 | -1 | Active |
| Left Motor | 7.726 | 3.242 | 0.003 | 0.636 | +1 | Active |
| Left Eye | 9.694 | 6.954 | 0.072 | 0.644 | -1 | Active |
| Right Eye | 9.731 | 4.253 | 0.075 | 0.265 | +1 | Active |

### Essential variables: initial vs final

| Unit | Initial CritDev | Final CritDev | Initial Output | Final Output |
|------|-----------------|---------------|----------------|--------------|
| Right Motor | -0.076 | -0.030 | 0.895 | -0.003 |
| Left Motor | -0.692 | **-9.999** (saturated) | 0.043 | **-1.000** |
| Left Eye | -0.208 | 0.056 | 0.197 | 0.006 |
| Right Eye | -0.278 | -4.941 | 0.966 | -0.494 |

One unit (Left Motor) saturated at its negative deviation limit. The
other three settled to moderate or near-zero values.

### Connection changes (initial vs final)

| Connection | Initial Weight | Initial Switch | Final Weight | Final Switch | Changed? |
|------------|---------------|----------------|-------------|-------------|----------|
| Right Motor <- Right Motor (self) | 0.910 | -1 | 0.910 | -1 | No (manual) |
| Right Motor <- Left Eye | 0.535 | -1 | 0.535 | -1 | No |
| Left Motor <- Left Motor (self) | 0.401 | +1 | 0.401 | +1 | No (manual) |
| Left Motor <- Right Eye | **0.570** | **+1** | **0.283** | **-1** | **Yes --- sign flipped, weight halved** |
| Left Eye <- Left Eye (self) | 0.986 | -1 | 0.986 | -1 | No (manual) |
| Left Eye <- Left Sensor | **0.976** | +1 | **0.342** | +1 | **Yes --- weight reduced to 1/3** |
| Right Eye <- Right Eye (self) | 0.029 | +1 | 0.029 | +1 | No (manual) |
| Right Eye <- Right Sensor | **0.293** | +1 | **0.144** | -1 | **Yes --- sign flipped, weight halved** |


## 3. Interpretation

### Why the robot approaches the target

The negative irradiance creates an incentive structure opposite to the
positive-light case. In the positive case, approaching the light
*increases* sensor output magnitude, creating larger disturbances that
push units toward their critical thresholds. The homeostat responded by
finding a configuration that moved the robot away, reducing the
disturbance.

With negative irradiance, the same logic works in reverse: the sensors
produce negative values whose magnitude grows with proximity. However,
the critical threshold test (`|critDev| >= 0.9 * maxDev`) is symmetric
--- it triggers on large deviations in either direction. The homeostat
must still keep its essential variables within bounds.

In this run, the system found a configuration where:

1. **Left Motor saturated** at -9.999 (output = -1.000), driving the
   left wheel in strong reverse.

2. **Right Motor near zero** (critDev = -0.030), producing essentially
   no wheel command.

3. This asymmetry (left wheel in reverse, right wheel near zero)
   produces a gentle **clockwise turn toward the target**.

4. As the robot approaches, the negative sensor readings grow in
   magnitude, but the connection weights were reduced by the uniselector
   (Left Eye <- Left Sensor dropped from 0.976 to 0.342, Right Eye <-
   Right Sensor from 0.293 to 0.144), attenuating the growing signal
   enough to keep the non-saturated units within bounds.

### The uniselector's actions

Three connections were modified during the 60,000-tick run:

- **Left Motor <- Right Eye**: sign flipped (+1 to -1) and weight halved
  (0.570 to 0.283). This reversed the effect of the Right Eye on the
  Left Motor, contributing to the Left Motor's negative saturation.

- **Left Eye <- Left Sensor**: weight reduced from 0.976 to 0.342.
  This attenuated the growing (negative) sensor signal, helping the Left
  Eye stay near zero despite increasing irradiance magnitude.

- **Right Eye <- Right Sensor**: sign flipped (+1 to -1) and weight
  halved (0.293 to 0.144). This both attenuated and reversed the sensor
  input to the Right Eye.

### Comparison with the positive-light experiment

| | Positive light (Feb 21) | Negative light (Feb 22) |
|-|------------------------|------------------------|
| Light intensity | +100 | -100 |
| Duration | 2,000,000 ticks | 60,000 ticks (early stop) |
| Starting distance | 4.243 | 4.243 |
| Final distance | 9.197 (farther) | 1.458 (closer) |
| Saturated units | 2 (Right Motor, Left Eye) | 1 (Left Motor) |
| Behaviour | Curved away from light | Spiralled toward target |
| Connection changes | 2 | 3 |

Both experiments demonstrate the homeostat's fundamental property:
**ultrastability**. The system reorganises its parameters until it finds
a configuration where the essential variables remain within acceptable
bounds. In the positive-light case, this meant moving away to reduce
sensor stimulation. In the negative-light case, the system found a
configuration that happened to spiral inward --- but importantly, this
was not "goal-seeking" in any intentional sense. The homeostat simply
found a parameter set where its internal variables were stable, and
the resulting motor commands happened to produce approach behaviour.

The much faster convergence (60k vs 2M ticks) likely reflects the
particular random initial conditions rather than a fundamental asymmetry
between approach and avoidance. Different random seeds would produce
different convergence times.
