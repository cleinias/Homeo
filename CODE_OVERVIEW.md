# Homeo -- Code Overview

Homeo is a Python simulation of W. Ross Ashby's Homeostat, the adaptive electromechanical device described in *Design for a Brain* (1952, 2nd ed. 1960) and *An Introduction to Cybernetics* (1956). The original Homeostat consisted of four identical units, each with a needle free to move in a trough of water, interconnected so that any disturbance would propagate through the system. When a unit's needle strayed too far from equilibrium for too long, a stepping switch (the *uniselector*) would randomly reset the connection weights until the whole system settled into a stable configuration. Ashby used the device to study ultrastability and adaptive behaviour.

This software reproduces all the components of Ashby's machine -- units, connections, uniselectors -- and extends the model to an arbitrary number of units, Newtonian needle dynamics, configurable noise and viscosity, and a continuous (stochastic) uniselector besides Ashby's stepping switch. It provides a programmatic API for scripted and batch experiments, a PyQt5 GUI for interactive exploration, a genetic algorithm, and homeostats as the controllers of simulated robots (see [ROBOTIC_OVERVIEW.md](ROBOTIC_OVERVIEW.md)).

## Project layout

All source code lives under `src/`:

- **`Core/`** -- The simulation engine: `Homeostat`, the units (`HomeoUnit`, `HomeoUnitNewtonian`, `HomeoUnitAristotelian`, with their `HomeoNeedleUnit`), `HomeoConnection`, the uniselectors (`HomeoUniselectorAshby`, `HomeoUniselectorUniformRandom`, `HomeoUniselectorContinuous`), the data-collection classes, and `HomeoJIT`, the numba-compiled kernels of headless runs.
- **`Simulator/`** -- `HomeoQtSimulation` (the simulation runner of the GUIs and the GA, which also works without PyQt5), the GUI windows (`HomeoGeneralGUI`, `AshbyExperimentGui`, `HomeoGenAlgGui`), the GUI-free genetic-algorithm engine (`HomeoGenAlg`), Ashby's seven experiments (`AshbyOriginalExperiments`), the experiment setups (`HomeoExperiments`), and the robot-simulator backends (`SimulatorBackend`).
- **`Helpers/`** -- Noise (`HomeoNoise`), PyQt signal proxying (`QObjectProxyEmitter`, with a null fallback when PyQt5 is absent), loggers (`HomeostatStateLogger`, `HomeostatConditionLogger`, `RobotTrajectoryWriter`), and the analysis tools (`TrajectoryGrapher`, `StripchartGrapher`, `StatelogAnalyzer`, `StatsAnalyzer`, `HomeostatDiagramTikz`, `GenomeDecoder`).
- **`HomeoExperiments/KheperaExperiments/`** -- The phototaxis experiments (`phototaxis_braitenberg2_direct`, `phototaxis_braitenberg2_Ashby`, and what they share, `phototaxis_common`).
- **`KheperaSimulator/`**, **`WebotsSimulator/`**, **`Webots/`**, **`RobotSimulator/`** -- The robot simulators (Box2D and Webots), the Webots project, and the transducers that connect units to a robot.
- **`Unit_Tests/`** -- The pytest suite.

The scripts `src/run_*.py` and `src/replay_best_with_statelog.py` are the batch and GA entry points; `hpc/` holds the SLURM and workstation array scripts.

## Core concepts

### The Homeostat

`Homeostat` (in `Core/Homeostat.py`) is the top-level container. It holds a list of `HomeoUnit` instances and a `HomeoDataCollector` that records system state at every tick. Creating a simulation amounts to creating a `Homeostat`, populating it with units, and telling it to run.

To add units, call `addUnit(unit)` (no inter-unit connections are created) or, more commonly, `addFullyConnectedUnit(unit)`, which connects the new unit to every existing unit and vice versa with random weights and polarities. Individual connections can be managed with `addConnectionWithRandomValuesFromUnit1toUnit2(u1, u2)` and `removeConnectionFromUnit1ToUnit2(u1, u2)`. The method `unitWithName(name)` retrieves a unit by its unique name.

The simulation is advanced by `runFor(t)`, which runs until the homeostat's time reaches `t` -- from time 0, `t` ticks; a later call carries on from where the previous one stopped to the new target -- or by `runOnce()` for a single tick. Each tick (`Homeostat.updateUnits`) records every unit's state if data collection is enabled (the `collectsData` property, `True` by default), then updates every active unit. The units advance together: each reads the outputs the others had at the start of the tick, so the order of the units does not matter. (Runs before 13 Oct 2026 updated the units one after another, each committing its output at once, so a unit read the current tick's outputs of the units before it in `homeoUnits` and the previous tick's of those after it.) After the units, the robot's world advances once (see ROBOTIC_OVERVIEW).

The entire homeostat can be serialised to disk with `saveTo(filename)` (pickle) and restored with the class method `Homeostat.readFrom(filename)`. A full reset of all units and the clock is available via `fullReset()`; `randomizeValuesforAllUnits()` randomises every unit's parameters without resetting the topology.

### Units

`HomeoUnit` (in `Core/HomeoUnit.py`) represents a single unit of the homeostat. Its central state variable is `criticalDeviation`, the displacement of the needle from equilibrium, between -`maxDeviation` and +`maxDeviation` (default 10). Each tick, `selfUpdate()`:

1. Adds the unit's internal noise to the deviation (`updateDeviationWithNoise`).
2. Computes the *torque* on the needle, the sum over the active incoming connections, the self-connection included, of weight x switch x the incoming unit's output, plus each connection's noise (`computeTorque()`).
3. Computes the *next deviation* from the torque (`newNeedlePosition`, below).
4. Lets the uniselector act on the next deviation, before it is clipped:
   - a discrete uniselector (Ashby's, or uniform random) fires when the next deviation is critical, beyond `critThreshold` x `maxDeviation` (default 0.9) on either side, and resets the weights of the unit's incoming connections in state `'uniselector'`. Like the relay of Ashby's homeostat it fires as soon as the deviation is critical, then at most once every `uniselectorTimeInterval` ticks (default 100) while it stays critical (`operateUniselectorIfCritical`). (Before 13 Oct 2026 the unit looked once per interval, at one tick, and fired only if the deviation was critical at that tick.)
   - a continuous uniselector moves those weights a little, by an amount set by the unit's stress, |deviation| / `maxDeviation` (`stressLevel`).
5. Clips the next deviation to [-`maxDeviation`, +`maxDeviation`] and maps it linearly to the output current in `outputRange` (default [-1, 1]; `computeOutput()`).

The base unit's needle has no momentum (an *Aristotelian* needle: the force sets the velocity). With `needleCompMethod` `'linear'` (the default) the deviation moves by torque x (1 - viscosity/`maxViscosity`) / mass in a tick; with `'proportional'` the torque is first divided by 2 x `maxDeviation`, so the potential displacement does not grow with the number of connections. Viscosity runs from 0 (no effect) to `maxViscosity` (10; the needle cannot move). `HomeoUnitAristotelian` is the same model for the `'linear'` method, the viscosity subtracted as a drag force (`dragOn`).

Internal noise is "distorting normal" noise: each tick a Gaussian draw with standard deviation `noise`/3, clipped to +/-`noise`, is added to the deviation (`HomeoNoise.unitNoise`). A connection adds its own noise to what it carries, a Gaussian with standard deviation `noise` x |current| / 3, clipped to +/-`noise` x |current|, so none on a connection carrying no current (`HomeoNoise.connNoise`).

Units are created with `HomeoUnit()` and can be randomised with `setRandomValues()`, which draws the viscosity, noise, self-connection and needle deviation (uniform over the whole range, +/-`maxDeviation`) and sets the output that deviation gives. (Before 13 Oct 2026 the deviation came from (-1, 1), the central tenth of the range, and the output was a separate draw from (0, 1).) Connections are added with `addConnectionWithRandomValues(otherUnit)`. Each unit always has a self-connection as its first input connection; the self-connection weight is the `potentiometer` property and its polarity is the `switch` property. The homeostat's resets (`Homeostat.timeReset`, which also sets the outputs from the deviations and restarts the uniselectors, and `fullReset`) keep the self-connection manual and in step with the potentiometer.

`HomeoUnitNewtonian` (in `Core/HomeoUnitNewtonian.py`) gives the needle mass and velocity: m x'' = F - c x' - k (x - x0), with F the torque of the other connections, c the viscosity (Stokes drag, -viscosity x velocity) and the self-connection acting as a spring of stiffness k (a negative spring under positive feedback; `selfSpring`). Each tick advances the needle by `dt_fast` (default 1) with the exact solution of that equation, F held over the step (`HomeoJIT._jit_needle_position_newtonian`, a matrix exponential, with no case split between under-, over- and critically damped motion): the step adds no growth or damping of its own at any mass, viscosity, stiffness or `dt_fast`. At a stop the needle halts (velocity 0). (Before 13 Oct 2026 the step was explicit: it held the whole torque over the step and moved the position with the old velocity, which added energy every tick.) `dragEquationDrag()` (a high-Reynolds drag) is kept for comparison; the step does not use it. `dt_fast` changes only the needle's step: noise, connections, both uniselectors and the world stay per tick. It is a rescaling of the needle, not a time step: (mass m, viscosity c, `dt_fast` dt) moves exactly as (m/dt², c/dt, 1); it stays only to replay genomes that evolved it (review finding CU-11). A Newtonian unit's viscosity is a drag coefficient with no ceiling; `HomeoUnit`'s `maxViscosity` (10) bounds only the base unit's own viscosity. The phototaxis experiments and the GA use `HomeoUnitNewtonian` motors.

### Headless runs

A homeostat whose `_headless` flag is set (the phototaxis experiments, the GA) runs the units' arithmetic through the numba-compiled kernels in `Core/HomeoJIT.py`, on arrays of weights and outputs that the units keep in step with their connection objects. Without numba the same functions run as plain Python. Numba draws its noise from its own generator: a seed gives the same run on two machines only if both have numba, or both lack it; the experiments seed both generators.

### Connections

`HomeoConnection` (in `Core/HomeoConnection.py`) represents a directed, weighted link from one unit to another. Its key attributes are:

- **`weight`** -- magnitude of the connection (0 to 1).
- **`switch`** -- polarity (+1 or -1).
- **`noise`** -- connection-level noise (0 to 1), proportional to the current carried (above).
- **`state`** -- `'manual'` or `'uniselector'`, indicating whether the weight is under direct control or can be reset by the uniselector.

The signed output of a connection is computed by `output()`, which returns weight * switch * incomingUnit.currentOutput, plus a noise term. The weight and polarity can be set together with `newWeight(w)`, which accepts a value in [-1, 1] and stores its absolute value in `weight` and its sign in `switch`.

### Uniselectors

`HomeoUniselector` (in `Core/HomeoUniselector.py`) is the abstract base class for Ashby's stepping switch. `HomeoUniselectorUniformRandom` draws each new weight uniformly from its bounds.

`HomeoUniselectorAshby` (in `Core/HomeoUniselectorAshby.py`) pre-computes a matrix of weight values and steps through it one row at a time whenever `advance()` is called. Three matrix-generation strategies are available, selected by calling the corresponding method on the uniselector instance:

- `equallySpaced()` -- 25 values (12 positive, 0, 12 negative) uniformly spaced in [-1, 1].
- `randomized()` -- 25 random values, shared across all controlled connections but shuffled independently for each.
- `independentlyRandomized()` -- each connection gets its own 25 independently drawn random values.

At each step, `produceNewValue()` returns the next weight from the matrix. The default number of steps is 12 (yielding 25 positions: 12 negative, zero, 12 positive), matching Ashby's original design. The matrix has one row per position and one column per connection the uniselector controls, every column shuffled; it starts with 10 columns and grows in steps of 10 as units are added. A firing gives each controlled connection its weight from the current row, then steps to the next row; a fresh uniselector's first firing reads row 0, and after the last row the switch returns to the first. (Before 13 Oct 2026 the switch had 26 positions over the 25 rows, so every 26th firing repeated the previous weights, the first firing read the last row, the first column was the unshuffled ramp, and more than 10 or 11 connections crashed.)

`HomeoUniselectorContinuous` (in `Core/HomeoUniselectorContinuous.py`) replaces the stepping switch with a continuous random search on the weights: every tick each weight in state `'uniselector'` moves by a random amount whose size sigma(stress) = `sigma_base` + (`sigma_crit` - `sigma_base`) x stress^`stress_exponent` grows with the unit's stress. Its `model` is `'diffusion'` (the default: dw = sigma(stress) sqrt(2 dt / `tau_a`) N(0,1), no drift, so a unit without stress keeps its weights), `'ou'` (an Ornstein-Uhlenbeck process relaxing towards 0 over `tau_a` ticks), or `'legacy'` (the process before 12 Oct 2026, to reproduce earlier runs). The first two reflect the weights at +/-1.

### Data collection

`HomeoDataCollector` (in `Core/HomeoDataCollector.py`) records a snapshot of every unit's state at each tick. Each snapshot is a `HomeoDataUnit` (in `Core/HomeoDataUnit.py`) holding the unit's name, critical deviation, output, uniselector state, and a dictionary of all incoming connection parameters. In headless runs the weights recorded are those the run is using (the units' JIT arrays, flushed before each record).

The collector's exports: `saveCompleteDataOnFile(filename)` writes all data as formatted text, `saveEssentialDataOnFile(filename)` writes a CSV of critical deviations and uniselector activations, and `criticalDevAsNPArrayForAllUnits()` returns the deviation history as a NumPy array for direct analysis: one row per tick, one column per unit, in the homeostat's unit order. Collection may start at a tick other than 0. For long runs, `Helpers/HomeostatStateLogger` writes a per-tick (or every N ticks) `.statelog` of deviations, outputs, weights and stress instead, and `HomeostatConditionLogger` records a run's initial and final conditions (and can restore them).

## Running a simulation

### Headless (scripted)

A `Homeostat` runs by itself: build it, run it with `runFor`, and read or save what it collected.  Set `slowingFactor` to 0 for headless runs: it is a per-tick pause in milliseconds (10 by default), there for the GUI.  `Simulator/AshbyOriginalExperiments.py` (driven by `run_ashby_original_experiments.py`) and the phototaxis scripts in `HomeoExperiments/KheperaExperiments/` are the headless experiment runners.  (`HomeoSimulation`, an older wrapper with filenames and save flags, and `Homeostat.start()`/`stop()`, which ran a homeostat in a thread, were deleted on 14 Oct 2026; `HomeoQtSimulation` does that bookkeeping and runs without PyQt5.)

A four-unit homeostat of Newtonian units:

```python
from Core.Homeostat import Homeostat
from Core.HomeoUnitNewtonian import HomeoUnitNewtonian

hom = Homeostat()
for _ in range(4):
    unit = HomeoUnitNewtonian()
    unit.setRandomValues()
    hom.addFullyConnectedUnit(unit)

hom.slowingFactor = 0
hom.runFor(500)

hom.saveTo('run.pickled')                                  # the homeostat
hom.dataCollector.saveCompleteDataOnFile('run-data.txt')   # every unit at every tick
# extract deviation history as a NumPy array: data[t, j] is unit j's deviation at tick t
data = hom.dataCollector.criticalDevAsNPArrayForAllUnits()
```

Seed numpy's generator first (and numba's, `HomeoJIT._jit_seed`, for a headless run) to make a run repeatable; the experiment scripts take `--seed`, record it, and the phototaxis scripts seed the environment (the robot's start pose) separately with `--env-seed`.

### With the GUI

`HomeoQtSimulation` (in `Simulator/HomeoQtSimulation.py`) integrates the simulation into the PyQt5 event loop, providing live charting and signal-based updates; it runs the homeostat in a worker thread (`go`, `pause`, `resume`, `step`). Its per-tick hooks are the contract of the headless runner (`AshbyOriginalExperiments.run_with_events`), so that an experiment runs the same in the GUI and headless: `tick_callbacks`, called with (homeostat, tick) before each tick's update -- the experiment's operator (trainer, constraint) acting on what it sees -- and `tick_observers`, called with (homeostat, time) after it -- record keepers such as the stability tracker. It is not normally instantiated directly; instead, one of the GUI entry points creates it.

Three GUIs are available, launched as modules (`python -m`) or, for Ashby's experiments, as a script.  With Homeo installed editable (`pip install -e .`, see the README) this works from any directory; without it, only from `src/`:

- **`python -m Simulator.HomeoGeneralGUI`** -- Full-featured interface: unit and connection configuration, real-time deviation charts, save/load, experiment selection.
- **`python src/run_ashby_gui.py`** -- Ashby's seven experiments from _Design for a Brain_ (`AshbyExperimentGui`, a `HomeoGeneralGUI` with an experiment selector and each experiment's controls); `--exp N` skips the selector, `--seed S` builds the homeostat of seed S, the same one a headless run of that seed builds.
- **`python -m Simulator.HomeoGenAlgGui`** -- Genetic-algorithm interface for evolutionary parameter optimisation (requires the DEAP library).  The engine behind it, `Simulator/HomeoGenAlg.py`, runs without the GUI and without PyQt5, e.g. from `run_direct_vehicle_ga.py`.

### Predefined experiments

`Simulator/AshbyOriginalExperiments.py` builds Ashby's seven experiments from *Design for a Brain* (`setup_exp1_basic_ultrastability` ... `setup_exp7_multistable`) and runs them with their events (`run_with_events`); the GUI's experiments are the same setups. The module `Simulator/HomeoExperiments.py` provides functions that return a fully configured `Homeostat` ready to run. Notable ones include:

- `initializeAshbySimulation()` -- Four fully connected units with random values (Ashby's standard setup).
- `initializeAshbyNoNoiseSimulation()` -- Same topology with all noise zeroed, useful for deterministic testing.
- `initializeAshbyExp1BasicUltrastability()` ... `initializeAshbyExp7Multistable()` -- Ashby's seven experiments, for the GUI.
- `initializeBraiten2_2...`, `initializeBraiten2_direct_...`, `initializeBraiten3c_...` -- Braitenberg vehicles controlled by a homeostat, for the phototaxis experiments and the GA (see ROBOTIC_OVERVIEW).

## Dependencies

- **Python 3** (3.11 or later)
- **PyQt5** -- GUI and signal/slot infrastructure.  Not needed for headless batch runs or the GA: without it, `QObjectProxyEmitter` hands the Core a null emitter and `HomeoQtSimulation` becomes a plain object
- **NumPy** -- numerical computation throughout
- **SciPy** -- statistical tests in the test suite
- **Matplotlib** -- static plotting and data export
- **pandas**, **tabulate** -- the analysis tools and the condition logger
- **pyqtgraph** -- real-time charting in the GUI
- **Box2D**, **pyglet** -- the Box2D robot simulator and its window
- **numba** -- optional: compiles the headless kernels (the HPC runs use it)
- **DEAP**, **dill** -- genetic-algorithm experiments (optional)
- **Webots** R2025a -- optional, for the Webots robot simulator
