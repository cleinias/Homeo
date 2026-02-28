# RNG Seeding and Initial State Logging

*Implemented: 2026-02-28.*

---

## Problem

Phototaxis experiments use stochastic initialization (random masses,
weights, noise, viscosity, etc.) but never seed the RNG.  This makes
runs unreproducible: even with the `.json` condition files logging
initial/final snapshots, there is no way to re-create the exact same
initial state for a new run.  Two independent RNG sources are involved:
`numpy.random` (unit/connection initialization, OU noise, Ashby
uniselector) and Python's `random` (HomeoNoise, DEAP operators).

Additionally, the first row logged in `.statelog` files was tick 1
(after the first `selfUpdate()`), so the pure initialization state
was never captured.

## Changes

1. **`setup_phototaxis()`** gains a `seed` parameter (default `None`).
   When `None`, a seed is generated from `os.urandom(4)`.  Both
   `np.random.seed()` and `random.seed()` are called before any
   stochastic initialization.  The function now returns
   `(hom, backend, seed)`.

2. **`run_ga_replay()`** seeds both RNGs with the same pattern, since
   GA replay does not go through `setup_phototaxis()`.

3. The seed is recorded in two places:
   - `.statelog` metadata header: `# seed\t{seed}`
   - `.json` condition file: top-level `"seed"` field

4. State loggers now call `log_tick(0)` immediately after creation,
   capturing the initialization state before any dynamics run.

## Files modified

- `src/HomeoExperiments/KheperaExperiments/phototaxis_braitenberg2_Ashby.py`
- `src/Helpers/HomeostatStateLogger.py`
- `src/Helpers/HomeostatConditionLogger.py`
- `src/run_validation_300k.py`

## Verification

All 182 unit tests pass.  To verify reproducibility:

```python
from HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_Ashby import run_headless
r1 = run_headless(state_log=True, seed=12345, total_steps=1000, quiet=True)
r2 = run_headless(state_log=True, seed=12345, total_steps=1000, quiet=True)
# r1 and r2 .statelog files should be identical
```
