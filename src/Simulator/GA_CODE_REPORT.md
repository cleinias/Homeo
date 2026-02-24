# Genetic Algorithm for Homeostat Parameter Optimisation

## Overview

The GA module evolves the parameters of an Ashby-style Homeostat controlling
a simulated Khepera robot in a Braitenberg vehicle type-2 phototaxis task.
The fitness function measures how close the robot ends up to a light target
after a fixed number of simulation steps. The GA minimises this distance.

The implementation uses the **DEAP** framework (Distributed Evolutionary
Algorithms in Python) and supports three robotic simulation back-ends:
an internal Python simulator (HOMEO), Webots, and V-REP/CoppeliaSim.

**Key files:**

| File | Role |
|------|------|
| `Simulator/HomeoGenAlgGui.py` | GA simulation class and (stub) GUI |
| `Simulator/HomeoExperiments.py` | Experiment initialisation functions |
| `Simulator/SimulatorBackend.py` | Abstraction over robotic simulators |
| `Helpers/GenomeDecoder.py` | Genome decoding and pretty-printing |
| `Helpers/StatsAnalyzer.py` | Post-hoc analysis of GA run logbooks |
| `Core/HomeoUnit.py` | Weight-to-parameter mapping functions |
| `Core/HomeoConnection.py` | Weight-to-connection mapping |

---

## 1. The Homeostat Architecture Under Evolution

The experiment (`initializeBraiten2_2_Full_GA`) builds a 6-unit,
fully-connected homeostat wired to a Khepera-like robot:

```
                  +-----------+        +-----------+
 Light  --------> | Left      | -----> | Left      | ------> Left Wheel
 (sensor input)   | Sensor    |        | Eye       |
                  | (Input)   |        | (Newtonian|
                  +-----------+        +-----------+
                       |                    |    \
                       |                    |     \  cross-connections
                       |                    |      \
                  +-----------+        +-----------+
 Light  --------> | Right     | -----> | Right     | ------> Right Wheel
 (sensor input)   | Sensor    |        | Eye       |
                  | (Input)   |        | (Newtonian|
                  +-----------+        +-----------+
                                            |
                                       +-----------+    +-----------+
                                       | Left      |    | Right     |
                                       | Motor     |    | Motor     |
                                       | (Actuator)|    | (Actuator)|
                                       +-----------+    +-----------+
                                            |                |
                                        Left Wheel     Right Wheel
```

The six units are:

| # | Unit Name | Type | Role |
|---|-----------|------|------|
| 1 | Left Motor | `HomeoUnitNewtonianActuator` | Drives left wheel |
| 2 | Right Motor | `HomeoUnitNewtonianActuator` | Drives right wheel |
| 3 | Left Eye | `HomeoUnitNewtonian` | Internal processing |
| 4 | Right Eye | `HomeoUnitNewtonian` | Internal processing |
| 5 | Left Sensor | `HomeoUnitInput` | Reads left light sensor |
| 6 | Right Sensor | `HomeoUnitInput` | Reads right light sensor |

Units 1--4 are "real" homeostatic units with full dynamics (mass, viscosity,
deviation, uniselector). Units 5--6 are input-only: they inject sensor
readings into the network but have no dynamics of their own.

All 6 units are fully interconnected (36 connections), but the
connections *into* the two sensor-only units are disabled. Effectively,
only 24 connections are active.

---

## 2. The Genome

### 2.1 Structure

The genome is a flat list of floats, all in the **[0, 1]** range.
Its length depends on the number of evolved units (`noEvolvedUnits`) and
the total number of units (`noUnits`):

```
genomeSize = (noEvolvedUnits x essentParams) + (noEvolvedUnits x noUnits)
           = (4 x 4) + (4 x 6)
           = 40
```

Only the 4 units with full dynamics (motors and eyes) have genes in the
genome. The 2 sensor-only `HomeoUnitInput` units have fixed parameters
and are not evolved. Each experiment function declares its own
`noEvolvedUnits` attribute, which is queried by the GA at initialisation.

The genome is laid out in two sections:

**Section A — Unit essential parameters** (indices 0--15, 4 genes per evolved unit):

| Genes | Unit | Param 0 | Param 1 | Param 2 | Param 3 |
|-------|------|---------|---------|---------|---------|
| 0--3 | Left Motor | mass | viscosity | unisel. timing | max deviation |
| 4--7 | Right Motor | mass | viscosity | unisel. timing | max deviation |
| 8--11 | Left Eye | mass | viscosity | unisel. timing | max deviation |
| 12--15 | Right Eye | mass | viscosity | unisel. timing | max deviation |

**Section B — Connection weights** (indices 16--39, 6 genes per evolved unit):

Each evolved unit has 6 incoming connections (one from each unit in the
fully-connected network). The 6 weights for each unit's incoming
connections are stored contiguously:

| Genes | Unit receiving input | Connections from all 6 units |
|-------|---------------------|------------------------------|
| 16--21 | Left Motor | 6 incoming connection weights |
| 22--27 | Right Motor | 6 incoming connection weights |
| 28--33 | Left Eye | 6 incoming connection weights |
| 34--39 | Right Eye | 6 incoming connection weights |

### 2.2 Genome size

All 40 genes have a phenotypic effect. The genome contains only genes for
the evolved units:
- 16 unit parameters (4 evolved units x 4 params)
- 24 connection weights (4 evolved units x 6 connections)

The `GenomeDecoder` and `StatsAnalyzer` functions accept a `noEvolvedUnits`
parameter (defaulting to `noUnits`) for backward compatibility when
decoding old 60-gene logbooks from earlier runs.

---

## 3. Gene-to-Parameter Mapping

All genes are stored as weights *w* in [0, 1] and decoded to actual
parameter values via linear scaling.

### 3.1 Unit parameters

| Parameter | Formula | Min (w=0) | Max (w=1) | Units |
|-----------|---------|-----------|-----------|-------|
| Mass | 9990 *w* + 10 | 10 | 10,000 | (dimensionless) |
| Viscosity | 10 *w* | 0 | 10 | (dimensionless) |
| Uniselector timing | 1000 *w* | 0 | 1,000 | ticks between uniselector activations |
| Max deviation | 999.9 *w* + 0.1 | 0.1 | 1,000 | critical deviation threshold |

These mappings are implemented as class methods on `HomeoUnit`:

```python
massFromWeight(w)                       = (maxMass - minMass) * w + minMass
viscosityfromWeight(w)                  = maxViscosity * w
uniselectorTimeIntervalFromWeight(w)    = maxUniselectorTimeInterval * w
maxDeviationFromWeight(w)               = (maxTheoreticalDev - minTheoreticalDev) * w + minTheoreticalDev
```

### 3.2 Connection weights

| Parameter | Formula | Min (w=0) | Max (w=1) |
|-----------|---------|-----------|-----------|
| Signed weight | −1 + 2*w* | −1 | +1 |

The signed weight is then decomposed into:
- **Absolute weight** = |−1 + 2*w*| (connection strength, [0, 1])
- **Switch** = sign(−1 + 2*w*) (polarity: −1 = inhibitory, +1 = excitatory)

At *w* = 0.5 the connection has zero weight. Below 0.5 the connection is
inhibitory; above 0.5 it is excitatory.

---

## 4. GA Strategy

### 4.1 Algorithm type

Generational GA with **elitist replacement**: each generation, the
population is replaced by selected-and-varied offspring, with the best
individual from the previous generation guaranteed to survive (k=1
elitism).

### 4.2 Default parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| Population size | 150 | Individuals per generation |
| Generations | 1 | Number of generational cycles (beyond gen 0) |
| Steps per evaluation | 1,000 | Simulation ticks per fitness evaluation |
| Crossover probability | 0.5 | Per-pair probability of mating |
| Mutation probability | 0.2 | Per-individual probability of mutation |
| Per-gene mutation rate | 0.05 | `indpb` for Gaussian mutation |
| Tournament size | 3 | Individuals per tournament |

### 4.3 Operators

| Operator | DEAP function | Details |
|----------|---------------|---------|
| **Selection** | `selTournament(tournsize=3)` | Tournament selection; selects `len(pop)` individuals |
| **Crossover** | `cxTwoPoint` | Two-point crossover on genome lists |
| **Mutation** | `mutGaussian(mu=0, sigma=0.2, indpb=0.05)` | Gaussian noise added to each gene with 5% probability |
| **Bounds** | `checkBounds(0, 1)` | Decorator clamping all genes to [0, 1] after crossover and mutation |

The Gaussian mutation sigma of 0.2 produces perturbations that typically
stay within the [0, 1] gene range (~95% of draws fall within ±0.4 of the
current value). The bounds decorator clips occasional out-of-range values.

### 4.4 Fitness function

```
fitness(genome) = fitnessSign × Euclidean distance from robot to TARGET at end of simulation
```

This is a **minimisation** objective (DEAP weight = −1.0). Each experiment
function declares a `fitnessSign` attribute that controls the optimisation
direction:

| Experiment | `fitnessSign` | Light intensity | Behaviour | Effect |
|------------|---------------|-----------------|-----------|--------|
| `initializeBraiten2_2_Full_GA_phototaxis` | +1 | −100 (negative) | Robot seeks light source | Minimise distance directly |
| `initializeBraiten2_2_Full_GA_scototaxis` | −1 | +100 (positive, default) | Robot avoids light source | Negate distance: minimising = maximising distance |
| `initializeBraiten2_2_Full_GA` | +1 | +100 (positive, default) | Original experiment | Minimise distance directly |

For **phototaxis** (negative light intensity), the robot should approach the
light source, so `fitnessSign = 1` and DEAP minimises the raw distance.

For **scototaxis** (positive light intensity), the robot should flee the
light source, so `fitnessSign = -1` negates the distance before DEAP
minimises it — effectively maximising the distance from the target.

The `fitnessSign` is read from the experiment function at GA initialisation
and propagated through the worker configuration for parallel evaluation.

### 4.5 Evolution loop

```
1. Generate initial population (random or cloned)
2. Assign IDs: "000-001", "000-002", ...
3. Evaluate all individuals (parallel via multiprocessing.Pool)
4. Update Hall of Fame and History
5. FOR each generation g = 1..G:
   a. SELECT offspring via tournament (with replacement)
   b. CLONE selected individuals
   c. CROSSOVER pairs with probability cxProb
      → invalidate fitness of crossed-over children
   d. MUTATE individuals with probability mutationProb
      → invalidate fitness of mutants
   e. Assign new IDs to invalidated individuals
   f. RE-EVALUATE only individuals with invalid fitness
   g. REPLACE population entirely with offspring
   h. ELITISM: re-insert best individual if lost (k=1)
   i. Compute and record generation statistics
   j. Update Hall of Fame
   k. Save logbook and history (checkpoint after each generation)
6. Clean up trajectory files
7. Save final logbook and history
8. Quit simulator backend
```

---

## 5. Fitness Evaluation in Detail

Each call to `evaluateGenomeFitness(genome)` performs:

1. Store the genome in `experimentParams` dict
2. Call `initializeExperSetup(**experimentParams)`, which dynamically dispatches
   to `initializeBraiten2_2_Full_GA(homeoGenome=..., backendSimulator=..., ...)`
3. This function:
   - Creates a fresh 6-unit Homeostat
   - Sets essential parameters of units 1--4 from the genome
   - Creates all 36 connections and sets active weights from the genome
   - Disables connections into sensor-only units
   - Wires transducers (wheels and sensors) to the appropriate units
4. Connect to the simulator backend and reset the world
5. Set the robot model name (for trajectory file naming)
6. Run exactly `stepsSize` simulation steps:
   ```python
   for i in range(stepsSize):
       simulation.step()
   ```
7. After the simulation, query the backend for the robot-to-target distance
8. Return the distance as a single-element tuple `(distance,)`

---

## 6. Population Initialisation

### Random population

```python
generateRandomPop(randomSeed=64)
```

Uses `np.random.seed(64)` for reproducibility. Each individual's genome is
generated as `genomeSize` values from `np.random.uniform(0, 1)`.

### Cloned population

```python
generatePopOfClones(cloneName='018-006')
```

All individuals in the population start with the same genome, extracted
from a previous GA run's logbook via `extractGenomeOfIndID()`. This
allows re-evolving from a known good starting point.

Note: cloned individuals do *not* have pre-filled fitness values (marked
as FIXME in the code), so they are all evaluated fresh in generation 0.

---

## 7. Record Keeping

### Logbook (`.lgb` files)

Pickled DEAP `Logbook` containing two types of records:

1. **Per-individual:** `{indivId, fitness, genome}` — recorded each time
   an individual is evaluated
2. **Per-generation:** `{gen, evaluations, avg, std, min, max}` — population
   statistics
3. **Summary record** (appended at save time): date, experiment name,
   population size, generations, genome size, steps, operator probabilities,
   elapsed time, final population with fitnesses

### History (`.hist` files)

Pickled DEAP `History` object tracking parent-child relationships across
all generations. Can be visualised as a genealogy tree via
`showGenealogyTree()` using networkx.

### Hall of Fame

Top 10 individuals across all generations, using genome equality for
deduplication.

### Statistics

Per-generation: mean, standard deviation, minimum, and maximum fitness.

---

## 8. Parallelisation

Fitness evaluation is parallelised using `multiprocessing.Pool`. Each
worker process creates an independent simulator instance and evaluates a
single genome. The number of workers is configurable via the `nWorkers`
parameter (defaults to 1 for serial evaluation).

| Strategy | Status | Notes |
|----------|--------|-------|
| Serial `map` | Available | `nWorkers=1`; evaluations run sequentially |
| `multiprocessing.Pool.map` | **Active** | `nWorkers>1`; parallel evaluation via process pool |

Additionally, Numba JIT compilation accelerates the hot-path arithmetic
(torque computation, needle position, noise, output scaling) when running
in headless mode, which is automatically enabled during GA evaluation.

### 8.1 Rationale for `multiprocessing.Pool`

Several parallelisation libraries were considered. `multiprocessing.Pool`
was chosen because it has no external dependencies, works when launched
from the PyQt GUI, and is well suited to the workload: each fitness
evaluation is CPU-bound and embarrassingly parallel, with each genome
getting an independent simulator instance and no shared state.

The alternatives were rejected for the following reasons:

- **`scoop`** (Scalable COncurrent Operations in Python) distributes work
  across multiple machines over a network, but requires launching the
  program with `python -m scoop` instead of `python`. This is incompatible
  with a normal GUI-launched application and adds a dependency for
  multi-machine cluster support that is not needed here.

- **`pathos.ProcessingPool`** works like `multiprocessing` but uses `dill`
  instead of `pickle` for serialisation, which can handle lambdas, closures,
  and nested functions. This was relevant when the fitness function used
  closures, but the current worker function (`_evaluate_genome_worker`) is
  a plain top-level function that serialises correctly with standard
  `pickle`. The extra dependency is unnecessary.

- **`playdoh`** is Python 2 only and unmaintained.

---

## 9. Analysis Tools

`Helpers/StatsAnalyzer.py` provides post-hoc analysis of completed GA runs:

| Function | Purpose |
|----------|---------|
| `extractGenomeOfIndID(id, logbook)` | Retrieve a specific individual's genome and fitness |
| `extractAllGenomes(logbook)` | Get the set of all unique genomes |
| `indivsDecodedFromLogbook(logbook)` | Decode all genomes to actual parameter values |
| `hallOfFame(logbook, n)` | Formatted table of top *n* individuals |
| `plotFitnessesFromLogBook(logbook)` | matplotlib chart of min/max/avg fitness over generations |
| `showGenealogyTree(history)` | networkx visualisation of parent-child relationships |
| `saveGenomeToCSV(genome, file)` | Export a genome to CSV |

`Helpers/GenomeDecoder.py` provides:

| Function | Purpose |
|----------|---------|
| `genomeDecoder(noUnits, genome, noEvolvedUnits=None)` | Convert [0,1] genome to actual parameter values |
| `genomePrettyPrinter(noUnits, decoded, noEvolvedUnits=None)` | Formatted string of all decoded parameters |
| `statFileDecoder(fileIn, fileOut, noUnits=6, rounding=2, noEvolvedUnits=None)` | Batch-decode a GA statistics file |

---

## 10. Known Limitations and Design Notes

1. ~~**Wasted genes:**~~ **Resolved.** The genome now contains only genes
   for evolved units (40 genes instead of 60). Each experiment function
   declares a `noEvolvedUnits` attribute; sensor-only units are excluded.

2. ~~**Large mutation sigma:**~~ **Resolved.** Sigma reduced from 2 to 0.2,
   keeping most mutations within the [0, 1] gene range for proper
   neighbourhood exploration.

3. ~~**Serial evaluation only:**~~ **Resolved.** Parallel evaluation via
   `multiprocessing.Pool` with configurable `nWorkers`. Numba JIT
   compilation accelerates headless simulation arithmetic.

4. ~~**No elitism:**~~ **Resolved.** The best individual from the Hall of
   Fame is re-inserted into the offspring (replacing the worst) when it
   would otherwise be lost (k=1 elitism).

5. ~~**Clone fitness not preserved:**~~ **Resolved.** Cloned individuals
   now carry the source individual's fitness via `ind.fitness.values`,
   avoiding redundant re-evaluation in generation 0.

6. **Fixed topology:** The GA evolves only unit parameters and connection
   weights. The network topology (which units exist, which connections are
   active) is fixed by the experiment function. This is a fundamental
   design choice — changing it would require a substantially different
   genome encoding (e.g. NEAT-style topology evolution).
