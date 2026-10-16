# GA Parallelism & GPU Acceleration

How the GA's fitness evaluations run in parallel, and why they do not run on
a GPU.  The GA's design as a whole is in `GA_CODE_REPORT.md`; its section 8
covers the worker pool.

## 1. The Workload

Each GA fitness evaluation runs a homeostat simulation for N ticks inside a
Box2D physics world.  Within a homeostat tick, most of the work is in:

- **`HomeoUnit.computeTorque()`** — a sum over the unit's active connections
  of `HomeoConnection.output()`
- **`HomeoConnection.output()`** — 3 multiplications + 1 addition + 1 Gaussian
  noise sample per connection
- **`HomeoUnit.newNeedlePosition()`** — a handful of scalar divisions and
  multiplications

For 1 000 ticks with a 6-unit fully-connected homeostat (24 active
connections), this amounts to roughly 24 000 `output()` calls per evaluation:
each cheap, so that in pure Python the loop overhead dominates.  In headless
mode, which GA evaluations use, the hot-path arithmetic runs JIT-compiled
(`Core/HomeoJIT.py`, Numba).

---

## 2. What an Evaluation Must Not Share

Evaluations are embarrassingly parallel once they share no mutable state:

| Shared state | Location | Problem under parallelism |
|-------------|----------|---------------------------|
| A single simulation | `HomeoQtSimulation` | Workers calling `initializeExperSetup()` on the same object race |
| `HomeoUnit.allNames` | Class-level `set()` | Parallel unit creation causes name collisions |
| PyQt signal emissions | `emitter()` / `SignalHub` | Qt objects cannot be accessed from non-GUI threads/processes |
| Data collectors / file I/O | `HomeoDataCollector`, trajectory writers | Concurrent writes to one file corrupt data |

So each evaluation builds its own simulation and backend
(`prepare_genome_evaluation` in `HomeoGenAlg.py`: a fresh `HomeoQtSimulation`
and `SimulatorBackendHOMEO`), in its own worker process, and writes its own
trajectory file, named after the individual.

---

## 3. Process-level Parallelism

The evaluations run in a `forkserver` `multiprocessing.Pool`
(`HomeoGASimulation._startPool`, one per run), with `nWorkers` processes;
`nWorkers=1` evaluates serially.  The pool's worker function,
`_evaluate_genome_worker`, is a plain top-level function, so standard
`pickle` serialises it.  Multiprocessing and the JIT are orthogonal: the
pool spreads evaluations over cores, the JIT speeds up each one.

---

## 4. GPU Acceleration — Not Viable

The homeostat simulation is a poor fit for GPU:

- **Too small:** 4–6 units × ~6 FP ops each = 24–36 operations per step.
  A modern GPU needs millions of parallel operations to amortise launch and
  data-transfer overhead.
- **Irregular topology:** The network is sparse and cyclic, with conditional
  branches (active/inactive units). This maps poorly to SIMD execution.
- **Box2D is already native C++**, so accelerating it would gain little.

Even batch-evaluating the entire population on GPU (one homeostat per CUDA
thread) would be bottlenecked by data transfer latency: copying 150 genomes
to the GPU takes longer than computing them on CPU.

A full JAX or PyTorch rewrite — replacing both the homeostat dynamics and
Box2D with differentiable, vectorised equivalents — could in theory yield
100×+ speedup by evaluating thousands of homeostats simultaneously on GPU,
at the cost of physics fidelity and code maintainability.

---

## 5. Summary

- **GPU:** Not viable — the per-evaluation workload is too small and irregular.
- **Multiprocessing:** Each evaluation is isolated (its own simulation and
  backend, in its own process), so evaluations run in parallel on a process
  pool.
- **Numba JIT:** Compiles the inner loops of headless runs; compounds with
  multiprocessing.
