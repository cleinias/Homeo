# Batch Phototaxis Experiment Report

**Date:** 2026-02-22 / 2026-02-23
**Experiment:** Braitenberg type-2 vehicle with Ashby fixed-topology uniselectors
**Configuration:** 6-unit homeostat, randomly selected initial weights per run
**Starting position:** (4, 4), Target: (7, 7), Initial distance: 4.243

---

## Light-Avoiding (positive light, intensity = 100)

10 runs, 2,000K ticks each. The robot's sensors detect irradiance from a
light source at (7,7). With positive intensity, higher sensor readings drive
stronger motor output on the ipsilateral side, causing the vehicle to turn
away from the light (Braitenberg type-2 avoidance).

| Run | Final dist | Min dist | Min dist at | Early stop | Wall time |
|-----|-----------|----------|-------------|------------|-----------|
|  1  |    18.634 |    0.978 |      42.5K  |     No     |   44.5 min |
|  2  |     4.780 |    4.241 |       0.5K  |     No     |   40.6 min |
|  3  |     9.765 |    3.416 |     783.0K  |     No     |   41.1 min |
|  4  |     3.655 |    3.501 |   1,994.5K  |     No     |   38.3 min |
|  5  |    67.393 |    0.132 |      31.0K  |     No     |   37.5 min |
|  6  |     0.088 |    0.001 |      48.0K  |     No     |   39.9 min |
|  7  |     0.127 |    0.078 |   1,910.5K  |     No     |   38.2 min |
|  8  |    11.777 |    4.243 |       0.0K  |     No     |   38.1 min |
|  9  |     3.527 |    3.360 |   1,832.5K  |     No     |   38.4 min |
| 10  |     4.242 |    4.241 |       0.5K  |     No     |   38.3 min |

**Summary:**
- Mean final distance: **12.4** (std: 19.1)
- Median final distance: **4.5**
- Runs converging close to target (final dist < 1): **2** (runs 6, 7)
- Runs diverging far from target (final dist > 10): **3** (runs 1, 5, 8)
- No early stops (none configured for this batch)
- Total wall time: ~6.6 hours

### Trajectories

| | | |
|---|---|---|
| ![Run 1](light_run_01.pdf) | ![Run 2](light_run_02.pdf) | ![Run 3](light_run_03.pdf) |
| ![Run 4](light_run_04.pdf) | ![Run 5](light_run_05.pdf) | ![Run 6](light_run_06.pdf) |
| ![Run 7](light_run_07.pdf) | ![Run 8](light_run_08.pdf) | ![Run 9](light_run_09.pdf) |
| ![Run 10](light_run_10.pdf) | | |

---

## Darkness-Seeking (negative light, intensity = -100)

10 runs, 4,000K ticks each (with early stop at distance < 1.5).
With negative intensity, the sensor readings are inverted: proximity to the
source produces lower readings, causing the vehicle to steer toward the
darkness source (seeking behaviour).

| Run | Final dist | Min dist | Min dist at | Early stop | Wall time |
|-----|-----------|----------|-------------|------------|-----------|
|  1  |     6.754 |    2.392 |     425.0K  |     No     |   86.5 min |
|  2  |    10.266 |    4.243 |       0.0K  |     No     |   80.2 min |
|  3  |    10.079 |    4.243 |       0.0K  |     No     |   78.9 min |
|  4  |     5.059 |    4.056 |       9.5K  |     No     |   77.0 min |
|  5  |    70.824 |    4.243 |       0.0K  |     No     |   77.4 min |
|  6  |    10.237 |    4.231 |       4.0K  |     No     |   72.0 min |
|  7  |    24.797 |    2.367 |      10.5K  |     No     |   72.9 min |
|  8  |    10.544 |    4.114 |       3.5K  |     No     |   73.2 min |
|  9  |     1.467 |    1.467 |     229.0K  |    Yes     |    4.3 min |
| 10  |    52.589 |    3.657 |       6.5K  |     No     |   73.8 min |

**Summary:**
- Mean final distance: **20.3** (std: 21.9)
- Median final distance: **10.2**
- Runs converging close to target (final dist < 5): **1** (run 9, early-stopped)
- Runs diverging far from target (final dist > 10): **5** (runs 2, 3, 5, 7, 10)
- Early stops: **1** (run 9 at 229K ticks, final distance 1.467)
- Total wall time: ~11.3 hours

### Trajectories

| | | |
|---|---|---|
| ![Run 1](dark_run_01.pdf) | ![Run 2](dark_run_02.pdf) | ![Run 3](dark_run_03.pdf) |
| ![Run 4](dark_run_04.pdf) | ![Run 5](dark_run_05.pdf) | ![Run 6](dark_run_06.pdf) |
| ![Run 7](dark_run_07.pdf) | ![Run 8](dark_run_08.pdf) | ![Run 9](dark_run_09.pdf) |
| ![Run 10](dark_run_10.pdf) | | |

---

## Comparison

|                          | Light-Avoiding | Darkness-Seeking |
|--------------------------|---------------|------------------|
| Ticks per run            |     2,000K    |       4,000K     |
| Mean final distance      |      12.4     |        20.3      |
| Median final distance    |       4.5     |        10.2      |
| Std dev                  |      19.1     |        21.9      |
| Converged (< 1.0)        |     2 / 10    |       0 / 10     |
| Close (< 5.0)            |     5 / 10    |       1 / 10     |
| Diverged (> 10.0)        |     3 / 10    |       5 / 10     |
| Early stops              |     0 / 10    |       1 / 10     |

**Observations:**

1. **Light-avoiding outperforms darkness-seeking.** Despite running for
   half the ticks, the light-avoiding condition produces lower median
   final distances (4.5 vs 10.2) and more runs that converge close to
   the target.

2. **High variance in both conditions.** Both distributions are heavy-
   tailed, with some runs converging tightly (runs 6-7 in light, run 9
   in dark) while others diverge dramatically (run 5 in light at 67.4,
   run 5 in dark at 70.8).

3. **Random weights dominate outcomes.** The initial random weight
   selection appears to be the primary factor determining whether the
   homeostat finds a viable configuration. The Ashby fixed-topology
   uniselector can recover from bad initial weights (as seen in runs
   where min_dist is reached late), but often does not within the
   allotted time.

4. **Darkness-seeking is harder.** The inverted sensor signal makes it
   more difficult for the homeostat to find stable configurations that
   drive the vehicle toward the target. Only 1 of 10 dark runs got
   within 5 units of the target.
