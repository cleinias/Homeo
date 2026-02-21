# Homeo -- Robotic Integration Overview

Ashby conceived the Homeostat as a model of adaptive behaviour: a system that, without being told what to do, finds and maintains stable configurations in the face of disturbance. The robotic component of Homeo applies this idea to mobile robot control. Instead of hand-coding a controller that maps sensor readings to motor commands, a homeostat network is placed between the robot's sensors and its wheels. The units treat sensor input as a perturbation to be absorbed and motor output as the means to do so. Because the uniselector mechanism randomly reassigns connection weights whenever a unit's essential variable leaves its viable range, the network explores the space of possible sensorimotor couplings until it discovers one that keeps every unit within bounds -- which, given the right wiring, corresponds to a robot that tracks a light source or avoids obstacles without any explicit goal representation.

The system supports three simulator backends -- Webots, V-REP, and a custom lightweight simulator called KheperaSimulator -- behind a uniform interface, so the same homeostat configuration can drive a robot in any of them.

## Architecture

The robotic integration is organised in three layers:

1. **Transducers** (`RobotSimulator/Transducer.py`) provide a uniform read/write interface to individual sensors and actuators, hiding the details of how each backend communicates with its hardware or simulation.

2. **Simulator backends** (`Simulator/SimulatorBackend.py`) manage the lifecycle of the external simulator -- launching it, resetting it, querying it -- and act as factories that return the right transducer objects for a given backend.

3. **Transducer-equipped HomeoUnits** (`RobotSimulator/HomeoUnitNewtonianTransduc.py`) extend the standard `HomeoUnit` hierarchy with units that read from a sensor or write to an actuator each time they update. These are plugged into the homeostat alongside regular units, forming a mixed network where some units face inward (connected only to other units) and some face outward (coupled to the robot).

Data flows in a closed loop. On every tick the sensor-input units read from their transducers, propagate their output through the homeostat network, and the actuator units translate their critical deviation into motor commands that they send back through their transducers to the robot. The robot moves, the sensors see a new scene, and the cycle repeats.

## Transducers

A transducer wraps a single sensor or actuator and exposes three methods:

- `read()` returns the current sensor value as a float.
- `act()` sends the current command (stored in the `funcParameters` property) to the actuator.
- `range()` returns a `(min, max)` tuple describing the transducer's value range, used for scaling.

Every supported backend provides its own concrete transducer classes. For Webots, `WebotsLightSensorTCP` sends the ASCII command `O` over a TCP socket and parses the comma-separated response to extract a specific sensor channel; `WebotsDiffMotorTCP` sends a command like `R,10.5` to set a wheel speed. For V-REP, the transducers use the V-REP remote API to get and set signal values. For the internal KheperaSimulator, `HOMEO_LightSensor` calls `robot.getSensorRead(eye)` directly in Python, with no network overhead.

Because all transducers share the same three-method interface, the homeostat has no knowledge of which backend it is talking to.

## Transducer-equipped units

Two specialised HomeoUnit subclasses bridge the homeostat to the robot.

`HomeoUnitInput` (in `RobotSimulator/HomeoUnitNewtonianTransduc.py`) is a read-only unit that acts as a sensor bridge. Its `selfUpdate()` does not run the normal homeostat dynamics; instead it reads a value from its transducer, scales it into the unit's deviation range, computes the corresponding output, and stops. Downstream units see it as an ordinary unit whose output tracks the external sensor. The `always_pos` flag controls whether the scaled value occupies the range [0, maxDeviation] or is centred at zero.

`HomeoUnitNewtonianActuator` extends `HomeoUnitNewtonian` with motor output. After running the standard `selfUpdate()` cycle -- torque computation, deviation update, uniselector check -- it converts its critical deviation into a wheel speed using a logistic sigmoid:

    speed = -maxSpeed + 2 * maxSpeed / (1 + exp(-switchingRate * criticalDeviation))

where `maxSpeed` is a fraction (default 20 %) of the actuator's physical maximum, and `switchingRate` (default 0.1) controls how sharply the function transitions. The resulting speed is sent to the transducer via `act()`. This sigmoid mapping means that small deviations produce gentle corrections and large deviations saturate the motor at its limits.

A simpler variant, `HomeoUnitAristotelianActuator`, uses linear scaling instead of a sigmoid: the deviation is mapped proportionally onto the actuator's range.

## Simulator backends

`SimulatorBackendAbstract` (in `Simulator/SimulatorBackend.py`) defines the interface that every backend must implement:

- `start(world)` -- launch the simulator with a given world or scene file.
- `reset()` / `resetPhysics()` -- restore the simulation to its initial state.
- `connect()` / `close()` / `quit()` -- manage the connection lifecycle.
- `getWheel(name)` -- return an actuator transducer for the named wheel (`'right'` or `'left'`).
- `getSensor(name)` -- return a sensor transducer for the named eye.
- `finalDisFromTarget()` -- query the current distance between the robot and the target, used as a fitness measure in genetic-algorithm experiments.
- `setRobotModel(name)` -- label the robot with an identifier (used for trajectory logging).
- `setDataDir(path)` -- set the directory for trajectory files.

Three concrete backends implement this interface:

**`SimulatorBackendWEBOTS`** communicates with Webots over two TCP connections. One connects to the robot controller (default port 10020) for motor commands and sensor queries. The other connects to a supervisor controller (default port 10021) that can reset the simulation, reset physics, set the robot's model name, query the distance to the target, or quit Webots. Connection management is handled by `WebotsTCPClient` (in `RobotSimulator/WebotsTCPClient.py`), which wraps a socket with automatic retry logic.

**`SimulatorBackendVREP`** uses the V-REP Python remote API. It communicates through named signals (`HOMEO_SIGNAL_rightWheel_MAX_SPEED`, `HOMEO_SIGNAL_leftEye_LIGHT_READING`, etc.) in synchronous operation mode.

**`SimulatorBackendHOMEO`** wraps the internal `KheperaSimulation` class. Since the simulator runs in the same process, transducers call Python methods directly -- `HOMEO_DiffMotor.act()` calls `robot.setRightSpeed(speed)` and `HOMEO_LightSensor.read()` calls `robot.getSensorRead(eye)` -- making it the fastest backend and the natural choice for batch experiments and genetic-algorithm optimisation.

Swapping backends is transparent. The experiment-setup functions in `HomeoExperiments.py` accept a `simulator` parameter; depending on its value, they instantiate the appropriate backend, call `basicBraiten2Transducers(backend, worldFile)` to obtain a dictionary of four transducers (two wheels, two eyes), and wire them into the same homeostat structure regardless of which backend produced them.

## Webots integration

The Webots side of the integration consists of two controller scripts that run inside the Webots process, each listening on a TCP socket.

The **robot controller** (a C program, compiled and loaded by Webots as the robot's controller) opens a TCP server on port 10020 and accepts single-character commands followed by optional parameters:

| Command | Description | Response |
|---------|-------------|----------|
| `O` | Read all light sensors | `o,v0,v1,...,v7` (eight sensor values) |
| `R,speed` | Set right wheel speed (rad/s) | `r` |
| `L,speed` | Set left wheel speed (rad/s) | `l` |
| `D,rSpeed,lSpeed` | Set both wheels at once | `d` |
| `M` | Query max wheel speed | `m,maxSpeed` |

The **supervisor controller** (`tcpip-supervisor-python.py`) opens a TCP server on port 10021 and handles simulation-level commands:

| Command | Description | Response |
|---------|-------------|----------|
| `R` | Revert simulation | `r` |
| `P` | Reset physics | `p` |
| `Q` | Quit Webots | `q` |
| `D` | Distance robot-to-target | distance as float string |
| `M,name` | Set robot model name | `m` |

The Webots world files used by Homeo are stored in `Webots/Homeo-experiments/` and define a flat arena with a Khepera-like robot and one or more light sources. Orthodox Braitenberg controller scripts (`Type-2a`, `Type-2b`, `Type-3a`, `Type-3b`) are also included for comparison with the homeostatic controller.

## KheperaSimulator

KheperaSimulator (in `KheperaSimulator/KheperaSimulator.py`) is a lightweight 2D physics simulator built on pyBox2D and pyglet, designed for fast headless execution during genetic-algorithm runs.

**`KheperaRobot`** models a differential-drive robot as a Box2D circular body (default diameter 126 mm, matching a real Khepera Junior) with two `KheperaWheel` bodies attached via angle-locked revolute joints. The wheels implement tire physics: lateral velocity is killed at every step to prevent skidding, and forward speed is set directly to achieve near-instantaneous response. The robot carries two directional light sensors at approximately +/- 22 degrees from its forward axis. Each sensor computes irradiance from every detectable light source according to the formula

    irrad = (intensity * (1 - ambientRatio) * cos(angle) + intensity * ambientRatio) / (a + b * distance + c * distance^2)

where the attenuation vector (a, b, c) defaults to (0, 0, 1) for pure inverse-square decay. The sensor clips its output at a configurable maximum value (default 100) and ignores lights outside its angular range (default 90 degrees) or beyond its maximum distance (default 10 metres). This model matches the one used by Webots and V-REP, so that results are comparable across backends.

**`KheperaSimulation`** manages the Box2D world, the bodies in it, and a `RobotTrajectoryWriter` that logs the robot's position at every step. The method `setupWorld(HomeoWorld)` calls a named setup function (e.g. `kheperaBraitenberg2_HOMEO_World`) that creates the world, places the robot and one or more lights, and initialises the trajectory writer. The simulation is advanced one step at a time by `advanceSim()`, which updates all bodies and steps the physics engine. `resetWorld()` tears down and rebuilds the world, opening a new trajectory file.

**`KheperaSimulationVisualizer`** is an optional pyglet window that renders the world in real time. It draws the robot, its sensor arcs, and the light sources over a reference grid, and supports pan, zoom, and tilt via mouse and keyboard. The visualiser is useful for debugging but is normally bypassed in batch mode.

The top-level function `runKheperaSimulator(headless=True/False, ...)` provides a convenient entry point: in headless mode it returns a `KheperaSimulation` ready for programmatic control; otherwise it launches the visualiser window.

## Experiment setup

The module `Simulator/HomeoExperiments.py` contains functions that return a fully wired homeostat for specific robotic experiments. The standard configuration for a Braitenberg-type light-seeking vehicle uses six units:

- Two **sensor-input units** (`HomeoUnitInput`) that read the left and right light sensors.
- Two **sensory units** (regular `HomeoUnitNewtonian`) that receive input from the sensor units and participate in the internal homeostat dynamics.
- Two **motor units** (`HomeoUnitNewtonianActuator`) that drive the left and right wheels.

All six units are interconnected, forming a network whose internal feedback connections are subject to uniselector adaptation. The sensor-input units are passive bridges; the four active units maintain their essential variables through mutual interaction and, when necessary, randomised weight changes. The emergent motor patterns that keep every unit's deviation within bounds correspond -- by construction of the sensor/motor wiring -- to the robot approaching or orbiting a light source.

Several experiment functions are provided:

- `initializeBraiten1_1Arist()` -- minimal reactive vehicle: one sensor, one Aristotelian motor, linear proportional control.
- `initializeBraiten2_2()` -- full adaptive vehicle with the six-unit architecture described above.
- `initializeBraiten2_2_Full_GA()` -- same structure, but initialised from a 60-element genome encoding unit parameters and connection weights, for use with the DEAP genetic-algorithm framework.

Each function accepts a `simulator` parameter (`'WEBOTS'`, `'VREP'`, or `'HOMEO'`) to select the backend, plus optional flags like `noNoise` and `noUnisel` for ablation studies.

## Trajectory logging

Every simulation run produces a `.traj` file that records the robot's state at every tick. The file is written by `RobotTrajectoryWriter` (in `Helpers/RobotTrajectoryWriter.py`), which is created automatically when a simulation world is set up.

Each `.traj` file contains a header with light positions and the robot's initial position, followed by one tab-separated row per tick with these columns:

| Column | Description |
|--------|-------------|
| `robot_x` | Robot x position |
| `robot_y` | Robot y position |
| `heading` | Robot heading in degrees (0-360) |
| `light_x` | Light source x position |
| `light_y` | Light source y position |
| `distance` | Euclidean distance from robot to light |

If multiple lights are present, the light columns are repeated for each light source.

By default, `.traj` files are saved to the current working directory. Experiment scripts can redirect them by setting `kheperaSimulation.dataDir` before the world is created. The phototaxis experiment in `HomeoExperiments/KheperaExperiments/` saves its logs to `SimulationsData/`. The GA GUI (`HomeoGenAlgGui.py`) creates timestamped subdirectories there (`SimsData-YYYY-MM-DD-HH-MM-SS`) containing `.traj`, `.lgb` logbook, and `.hist` history files. Note that `.lgb` logbook files are only produced by GA optimisation runs, not by standalone experiments.

## Visualising experiment data

Two tools are provided for inspecting trajectory data:

**`TrajectoryGrapher`** (`Helpers/TrajectoryGrapher.py`) is a command-line script that plots a single trajectory with matplotlib. It reads the `.traj` file, draws the robot's (x, y) path, marks the start position in green and the end position in red, overlays circles for each light source (sized by intensity), and annotates the final distance to the target.

    python -m Helpers.TrajectoryGrapher path/to/file.traj

**`TrajectoriesViewer`** (`Helpers/TrajectoriesViewer.py`) is a PyQt5 GUI for browsing and visualising multiple experiment runs. It lists all `.traj` files in a directory, supports changing directories, and auto-refreshes every second to pick up new files as they are written. Single-click a trajectory to select it; double-click or press "Visualize" to plot it via `TrajectoryGrapher`. If DEAP genetic-algorithm logbook files (`.lgb`) are present in the same directory, the viewer also provides buttons for inspecting GA statistics: hall of fame, full individual genomes, average fitness charts, and genealogy trees.

    python -m Helpers.TrajectoriesViewer
