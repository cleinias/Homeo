# Combined Report: Homeostat-Driven Braitenberg Vehicle Under Positive and Negative Irradiance

## Summary

Two experiments were conducted with a 6-unit homeostat controlling a
Braitenberg type-2 (crossed) vehicle, using the Ashby fixed-topology
mode with active uniselectors. The experiments were identical except for
the sign of the light intensity:

| | Experiment 1: Positive light | Experiment 2: Negative light |
|-|------------------------------|------------------------------|
| Date | 2026-02-21 | 2026-02-22 |
| Light intensity | +100 | -100 |
| Ticks run | 2,000,000 | 60,000 (early stop) |
| Start position | (4, 4) | (4, 4) |
| Target position | (7, 7) | (7, 7) |
| Start distance | 4.243 | 4.243 |
| **Final distance** | **9.197 (farther)** | **1.458 (closer)** |
| Saturated units | 2 | 1 |
| Connection changes | 2 | 3 |
| Behaviour | Curved away from light | Spiralled toward target |

Both outcomes are consistent with the homeostat's core principle:
**ultrastability**. The system reorganises its parameters (via the
uniselector) until it finds a configuration where all essential variables
remain within their viable bounds. This is not goal-directed behaviour
in the conventional sense --- the homeostat does not "know" about the
light or the robot's position. It simply searches for internal stability,
and the resulting motor commands happen to produce coherent spatial
behaviour.

## Detailed reports

The full analysis of each experiment is in:

- [Experiment 1: Positive light (Feb 21)](2026-02-21-positive-light/phototaxis_braitenberg2_Ashby_fixed-2026-02-21-report.md)
- [Experiment 2: Negative light (Feb 22)](2026-02-22-negative-light/phototaxis_braitenberg2_Ashby_fixed_dark-2026-02-22-report.md)


## Trajectories

### Experiment 1: Positive light --- robot moves away

![Positive-light trajectory](2026-02-21-positive-light/trajectory.pdf)

The vehicle spirals outward, increasing its distance from the light
source from 4.243 to 9.197 over 2 million ticks.

### Experiment 2: Negative light --- robot approaches

![Negative-light trajectory](2026-02-22-negative-light/trajectory_dark.pdf)

The vehicle spirals inward, decreasing its distance from 4.243 to 1.458
in only 60,000 ticks, entering the target zone and triggering an early
stop.


## Network topology comparison

### Experiment 1: Positive light

Initial state (all units within bounds):

![Positive initial topology](2026-02-21-positive-light/topology_initial.pdf)

Final state (Right Motor and Left Eye saturated):

![Positive final topology](2026-02-21-positive-light/topology_final.pdf)

### Experiment 2: Negative light

Initial state (all units within bounds):

![Negative initial topology](2026-02-22-negative-light/topology_dark_initial.pdf)

Final state (Left Motor saturated):

![Negative final topology](2026-02-22-negative-light/topology_dark_final.pdf)


## Discussion

### The homeostat as an environment-coupled dynamical system

The two experiments demonstrate that the homeostat, despite having no
explicit representation of the external world, produces coherent spatial
behaviour through its coupling with the environment. The signal path is:

```
Environment (light/darkness)
    |
Sensors (irradiance -> critDev)
    |
Eyes (Newtonian dynamics)
    |
Motors (sigmoid -> wheel speed)
    |
Robot motion (changes sensor readings)
```

This closed loop means that the homeostat's internal dynamics and the
robot's spatial dynamics are coupled. When the homeostat finds a stable
internal configuration, the motor commands it produces are necessarily
consistent with the environmental input it receives --- and therefore
with the robot's position relative to the light.

### Why opposite light signs produce opposite behaviours

With **positive** light, approaching the source increases irradiance,
which increases the magnitude of sensor inputs, which increases the
torque on internal units, pushing them toward their critical thresholds.
The homeostat responds by finding configurations that reduce this
disturbance --- which, through the sensorimotor loop, means moving away.

With **negative** light, approaching the source increases the magnitude
of *negative* irradiance. But the critical threshold test is symmetric
(`|critDev| >= 0.9 * maxDev`), so large negative deviations are just as
destabilising as large positive ones. In principle, the same avoidance
logic should apply. However, the negative sign reverses the polarity of
all sensor-driven torques, and the uniselector explores a different
region of parameter space. In this particular run, the system found a
stable configuration that happened to produce approach behaviour. The
growing negative sensor signal was attenuated by reduced connection
weights (the uniselector cut the sensor-to-eye weights to 1/3 and 1/2
of their initial values), keeping the non-saturated units within bounds
even at close range.

### Convergence speed

The negative-light experiment converged in 60,000 ticks --- 33x faster
than the positive-light experiment's 2,000,000 ticks. This difference is
most likely due to the particular random initial conditions (masses,
viscosities, initial weights) rather than a fundamental asymmetry between
the two scenarios. The initial random weights may have happened to be
closer to a stable configuration for the negative-light case. A
systematic study with many random seeds would be needed to determine
whether there is a true asymmetry in convergence difficulty.
