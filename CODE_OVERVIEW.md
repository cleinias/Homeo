# Homeo -- Code Overview

Homeo is a Python simulation of W. Ross Ashby's Homeostat, the adaptive electromechanical device described in *Design for a Brain* (1952, 2nd ed. 1960) and *An Introduction to Cybernetics* (1956). The original Homeostat consisted of four identical units, each with a needle free to move in a trough of water, interconnected so that any disturbance would propagate through the system. When a unit's needle strayed too far from equilibrium for too long, a stepping switch (the *uniselector*) would randomly reset the connection weights until the whole system settled into a stable configuration. Ashby used the device to study ultrastability and adaptive behaviour.

This software reproduces all the components of Ashby's machine -- units, connections, uniselectors -- and extends the model to an arbitrary number of units, optional Newtonian needle dynamics, configurable noise and viscosity, and several modes of uniselector operation. It provides both a programmatic API for scripted and batch experiments and a PyQt5 GUI for interactive exploration.

## Project layout

All source code lives under `src/`. The four main directories are:

- **`Core/`** -- The simulation engine: `Homeostat`, `HomeoUnit`, `HomeoConnection`, `HomeoUniselector`, and data-collection classes.
- **`Simulator/`** -- Simulation runners (`HomeoSimulation` for headless runs, `HomeoQtSimulation` for the Qt event loop), GUI windows (`HomeoGeneralGUI`, `HomeoMinimalGui`, `HomeoGenAlgGui`), and predefined experiment setups (`HomeoExperiments`).
- **`Helpers/`** -- Noise generation (`HomeoNoise`), PyQt signal proxying (`QObjectProxyEmitter`), trajectory and statistics utilities.
- **`Unit_Tests/`** -- Pytest test suite covering every core class.

Additional directories (`RobotSimulator/`, `VREP/`, `Webots/`, `KheperaSimulator/`) contain integration code for controlling virtual robots with a homeostat; they are not required for the basic simulation.

## Core concepts

### The Homeostat

`Homeostat` (in `Core/Homeostat.py`) is the top-level container. It holds a list of `HomeoUnit` instances and a `HomeoDataCollector` that records system state at every tick. Creating a simulation amounts to creating a `Homeostat`, populating it with units, and telling it to run.

To add units, call `addUnit(unit)` (no inter-unit connections are created) or, more commonly, `addFullyConnectedUnit(unit)`, which connects the new unit to every existing unit and vice versa with random weights and polarities. Individual connections can be managed with `addConnectionWithRandomValuesFromUnit1toUnit2(u1, u2)` and `removeConnectionFromUnit1ToUnit2(u1, u2)`. The method `unitWithName(name)` retrieves a unit by its unique name.

The simulation is advanced by calling `runFor(ticks)`, which iterates the system for the given number of steps, or `runOnce()` for a single tick. For continuous execution there are `start()` and `stop()`. At each tick every unit updates its needle deviation and output, checks whether its uniselector should fire, and records its state if data collection is enabled (the `collectsData` property, `True` by default).

The entire homeostat can be serialised to disk with `saveTo(filename)` (pickle) and restored with the class method `Homeostat.readFrom(filename)`. A full reset of all units and the clock is available via `fullReset()`; `randomizeValuesforAllUnits()` randomises every unit's parameters without resetting the topology.

### Units

`HomeoUnit` (in `Core/HomeoUnit.py`) represents a single unit of the homeostat. Its central state variable is `criticalDeviation`, the displacement of the needle from equilibrium. At each tick the unit:

1. Computes the *torque* acting on the needle by summing the weighted, switched outputs of all active incoming connections (`computeTorque()`).
2. Computes the *next deviation* from the torque, the current deviation, optional viscosity damping, and internal noise (`computeNextDeviation()`).
3. Clips the deviation to the interval [-`maxDeviation`, +`maxDeviation`].
4. Maps the deviation to an output current in `outputRange` (default [-1, 1]) via `computeOutput()`.
5. If the uniselector is active and the deviation has remained above the critical threshold (`critThreshold`, default 0.9 of `maxDeviation`) for longer than `uniselectorTimeInterval` ticks, the uniselector fires and resets the weights of the unit's incoming connections.

The method that drives this cycle is `selfUpdate()`.

Two methods of computing the needle displacement are available, selected by setting `needleCompMethod` to `'linear'` (deviation += torque) or `'proportional'` (deviation += torque / (2 * maxDeviation)). Viscosity attenuates the incoming torque: the effective force is multiplied by (1 - viscosity/maxViscosity), where `maxViscosity` defaults to 10. Internal noise is a normally distributed perturbation whose standard deviation is proportional to the `noise` property.

Units are created with `HomeoUnit()` and can be randomised with `setRandomValues()`. Connections are added with `addConnectionWithRandomValues(otherUnit)`. Each unit always has a self-connection as its first input connection; the self-connection weight is the `potentiometer` property and its polarity is the `switch` property.

`HomeoUnitNewtonian` (in `Core/HomeoUnitNewtonian.py`) extends `HomeoUnit` with simplified Newtonian dynamics: the needle has mass and velocity, and position changes follow s = s0 + v + a/2, with acceleration = torque / mass. A drag force opposes motion; two drag models are provided -- Stokes-law drag (`stokesLawDrag()`, default) and a simplified high-Reynolds drag (`dragEquationDrag()`). All predefined experiments use `HomeoUnitNewtonian`.

### Connections

`HomeoConnection` (in `Core/HomeoConnection.py`) represents a directed, weighted link from one unit to another. Its key attributes are:

- **`weight`** -- magnitude of the connection (0 to 1).
- **`switch`** -- polarity (+1 or -1).
- **`noise`** -- connection-level noise (0 to 1), added to the output independently of the unit's internal noise.
- **`state`** -- `'manual'` or `'uniselector'`, indicating whether the weight is under direct control or can be reset by the uniselector.

The signed output of a connection is computed by `output()`, which returns weight * switch * incomingUnit.currentOutput, plus a noise term. The weight and polarity can be set together with `newWeight(w)`, which accepts a value in [-1, 1] and stores its absolute value in `weight` and its sign in `switch`.

### Uniselectors

`HomeoUniselector` (in `Core/HomeoUniselector.py`) is the abstract base class for Ashby's stepping switch. The concrete implementation is `HomeoUniselectorAshby` (in `Core/HomeoUniselectorAshby.py`), which pre-computes a transition matrix of weight values and advances through it one row at a time whenever `advance()` is called. Three matrix-generation strategies are available, selected by calling the corresponding method on the uniselector instance:

- `equallySpaced()` -- 25 values (12 positive, 0, 12 negative) uniformly spaced in [-1, 1].
- `randomized()` -- 25 random values, shared across all controlled connections but shuffled independently for each.
- `independentlyRandomized()` -- each connection gets its own 25 independently drawn random values.

At each step, `produceNewValue()` returns the next weight from the matrix. The default number of steps is 12 (yielding 25 positions: 12 negative, zero, 12 positive), matching Ashby's original design.

### Data collection

`HomeoDataCollector` (in `Core/HomeoDataCollector.py`) records a snapshot of every unit's state at each tick. Each snapshot is a `HomeoDataUnit` (in `Core/HomeoDataUnit.py`) holding the unit's name, critical deviation, output, uniselector state, and a dictionary of all incoming connection parameters.

The collector offers several export methods: `saveCompleteDataOnFile(filename)` writes all data as formatted text, `saveEssentialDataOnFile(filename)` writes a CSV of critical deviations and uniselector activations, and `criticalDevAsNPArrayForAllUnits()` returns the deviation history as a NumPy array for direct analysis.

## Running a simulation

### Headless (scripted)

`HomeoSimulation` (in `Simulator/HomeoSimulation.py`) wraps a `Homeostat` with administrative bookkeeping -- filenames, save flags, a run counter. The simplest way to set up a standard four-unit homeostat is:

```python
from Simulator.HomeoSimulation import HomeoSimulation

sim = HomeoSimulation()
sim.initializeAshbySimulation()   # 4 fully connected HomeoUnitNewtonian units
sim.maxRuns = 1000
sim.start()                       # runs for maxRuns ticks

sim.saveCompleteRunOnFile()       # writes all data to a timestamped file
sim.save()                        # pickles the homeostat
```

For a custom topology:

```python
from Core.Homeostat import Homeostat
from Core.HomeoUnitNewtonian import HomeoUnitNewtonian

hom = Homeostat()
for _ in range(4):
    unit = HomeoUnitNewtonian()
    unit.setRandomValues()
    hom.addFullyConnectedUnit(unit)

hom.runFor(500)

# extract deviation history as a NumPy array
data = hom.dataCollector.criticalDevAsNPArrayForAllUnits()
```

### With the GUI

`HomeoQtSimulation` (in `Simulator/HomeoQtSimulation.py`) integrates the simulation into the PyQt5 event loop, providing live charting and signal-based updates. It is not normally instantiated directly; instead, one of the GUI entry points creates it.

Three GUIs are available, each launched as a script from the `src/` directory:

- **`python Simulator/HomeoGeneralGUI.py`** -- Full-featured interface: unit and connection configuration, real-time deviation charts, save/load, experiment selection.
- **`python Simulator/HomeoMinimalGui.py`** -- Stripped-down interface with start/pause, save, and basic graphing.
- **`python Simulator/HomeoGenAlgGui.py`** -- Genetic-algorithm interface for evolutionary parameter optimisation (requires the DEAP library).

### Predefined experiments

The module `Simulator/HomeoExperiments.py` provides functions that return a fully configured `Homeostat` ready to run. Notable ones include:

- `initializeAshbySimulation()` -- Four fully connected units with random values (Ashby's standard setup).
- `initializeAshbyNoNoiseSimulation()` -- Same topology with all noise zeroed, useful for deterministic testing.
- `initialize_Ashby_2nd_Experiment()` -- Three units connected in a circle, reproducing the experiment described in *Design for a Brain*, pp. 106--107.

## Dependencies

- **Python 3**
- **PyQt5** -- GUI and signal/slot infrastructure
- **NumPy** -- numerical computation throughout
- **SciPy** -- statistical tests in the test suite
- **Matplotlib** -- static plotting and data export
- **pyqtgraph** -- real-time charting in the GUI
- **DEAP** -- genetic-algorithm experiments (optional)