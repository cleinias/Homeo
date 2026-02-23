# GA Parallelism & GPU Acceleration — Feasibility Report

## 1. Current Performance Profile

Each GA fitness evaluation runs a homeostat simulation for N steps inside a
Box2D physics world. Profiling the hot path reveals:

| Component | Share of CPU | Implementation |
|-----------|-------------|----------------|
| Homeostat step loop | ~99% | Pure Python scalar arithmetic |
| Box2D physics step | ~1% | Compiled C++ (pybox2d) |

Within the homeostat step, most time is spent in:

- **`HomeoUnit.computeTorque()`** — Python `sum()` over a list comprehension
  calling `HomeoConnection.output()` for each active connection
- **`HomeoConnection.output()`** — 3 multiplications + 1 addition + 1 Gaussian
  noise sample per connection
- **`HomeoUnit.newNeedlePosition()`** — a handful of scalar divisions and
  multiplications

For 1 000 steps with a 6-unit fully-connected homeostat (24 active connections),
this amounts to roughly 24 000 `output()` calls per evaluation — individually
cheap, but the Python-loop overhead dominates.

---

## 2. Why Existing Parallelism Is Disabled

The code already imports `scoop`, `multiprocessing`, and `pathos`, with their
`map` registrations commented out. The reason is **shared mutable state**:

| Shared state | Location | Problem under parallelism |
|-------------|----------|---------------------------|
| `HomeoGASimulation._simulation` | Single `HomeoQtSimulation` instance | All workers call `initializeExperSetup()` on the same object — race condition |
| `HomeoUnit.allNames` | Class-level `set()` | Parallel unit creation causes name collisions |
| PyQt signal emissions | `emitter()` / `SignalHub` | Qt objects cannot be accessed from non-GUI threads/processes |
| Data collectors / file I/O | `HomeoDataCollector`, trajectory writers | Concurrent file writes corrupt data |

None of these are fundamental architectural barriers — they are fixable with
per-evaluation instance isolation.

---

## 3. GPU Acceleration — Not Viable

The homeostat simulation is a poor fit for GPU:

- **Too small:** 4–6 units × ~6 FP ops each = 24–36 operations per step.
  A modern GPU needs millions of parallel operations to amortise launch and
  data-transfer overhead.
- **Irregular topology:** The network is sparse and cyclic, with conditional
  branches (active/inactive units). This maps poorly to SIMD execution.
- **Box2D is already native C++** and accounts for only ~1% of runtime —
  accelerating it would be imperceptible.

Even batch-evaluating the entire population on GPU (one homeostat per CUDA
thread) would be bottlenecked by data transfer latency: copying 150 genomes
to the GPU takes longer than computing them on CPU.

A full JAX or PyTorch rewrite — replacing both the homeostat dynamics and
Box2D with differentiable, vectorised equivalents — could in theory yield
100×+ speedup by evaluating thousands of homeostats simultaneously on GPU.
However, this is a 6+ week rewrite that sacrifices physics fidelity and
code maintainability.

**Recommendation:** Do not pursue GPU acceleration.

---

## 4. Viable Parallelism Strategy

### 4.1 Process-level parallelism (multiprocessing)

Fitness evaluations are **embarrassingly parallel** once state is isolated.
The fix requires:

1. **Per-evaluation `HomeoQtSimulation` instances** — create a fresh simulation
   object inside `evaluateGenomeFitness()` instead of reusing `self._simulation`
2. **Clear `HomeoUnit.allNames`** at the start of each evaluation (or switch to
   instance-scoped name tracking)
3. **Suppress PyQt signal emissions** in worker processes (no GUI to update)
4. **Batch file I/O** — defer trajectory writes or use per-worker directories

With these fixes, `multiprocessing.Pool.map` or `pathos.ProcessingPool.map`
can replace the serial `map`. Expected speedup: **4–8×** on a typical 4–8 core
machine.

### 4.2 Numba JIT compilation

The innermost loops (`computeTorque`, `HomeoConnection.output`, noise
generation) are pure scalar Python arithmetic — ideal targets for Numba's
`@jit(nopython=True)`. This eliminates Python-loop overhead without
changing the algorithm.

Expected speedup: **2–4×** on the per-evaluation computation.

### 4.3 Combined

Multiprocessing + Numba JIT are orthogonal and compose multiplicatively:

| Approach | Estimated speedup | Effort |
|----------|-------------------|--------|
| Multiprocessing alone | 4–8× | 1–2 weeks |
| Numba JIT alone | 2–4× | 3 days |
| Both combined | 8–20× | 2 weeks |

---

## 5. Summary

- **GPU:** Not viable — the per-evaluation workload is too small and irregular.
- **Multiprocessing:** The most impactful single change. Requires fixing shared
  state (primarily `_simulation` instance isolation and `allNames`), after which
  evaluations are embarrassingly parallel.
- **Numba JIT:** Low-hanging fruit for the inner loops; compounds with
  multiprocessing.
- **Combined ceiling:** 8–20× speedup, turning a 24-hour GA run into 1–3 hours.
