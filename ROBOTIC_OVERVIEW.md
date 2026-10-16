# Homeo -- Robotic Integration Overview

Ashby conceived the Homeostat as a model of adaptive behaviour: a system that, without being told what to do, finds and maintains stable configurations in the face of disturbance. The robotic component of Homeo applies this idea to mobile robot control. Instead of hand-coding a controller that maps sensor readings to motor commands, a homeostat network is placed between the robot's sensors and its wheels. The units treat sensor input as a perturbation to be absorbed and motor output as the means to do so. Because the uniselector mechanism randomly reassigns connection weights whenever a unit's essential variable leaves its viable range, the network explores the space of possible sensorimotor couplings until it discovers one that keeps every unit within bounds -- which, given the right wiring, corresponds to a robot that tracks a light source or avoids obstacles without any explicit goal representation.

The simulators sit behind a uniform backend interface, so the same homeostat configuration can drive a robot in either of them: KheperaSimulator, a lightweight Box2D simulator in the same process (the GA and the batch arrays), and Webots, run by Homeo as its robot's extern controller (re-testing selected results, figures).  Both model the same robot, an e-puck2.  The V-REP backend and the old Webots TCP bridge were deleted on 14 Oct 2026.

## Architecture

The robotic integration is organised in three layers:

1. **Transducers** (`RobotSimulator/Transducer.py`) provide a uniform read/write interface to individual sensors and actuators, hiding the details of how each backend communicates with its hardware or simulation.

2. **Simulator backends** (`Simulator/SimulatorBackend.py`) manage the lifecycle of the external simulator -- launching it, resetting it, querying it -- and act as factories that return the right transducer objects for a given backend.

3. **Transducer-equipped HomeoUnits** (`RobotSimulator/HomeoUnitNewtonianTransduc.py`) extend the standard `HomeoUnit` hierarchy with units that read from a sensor or write to an actuator each time they update. These are plugged into the homeostat alongside regular units, forming a mixed network where some units face inward (connected only to other units) and some face outward (coupled to the robot).

Data flows in a closed loop. On every tick the sensor-input units read from their transducers, propagate their output through the homeostat network, and the actuator units translate their critical deviation into motor commands that they send back through their transducers to the robot. The robot moves, the sensors see a new scene, and the cycle repeats. Within a tick the units advance together, each reading the outputs the others had at the start of the tick, so a sensor's reading reaches the units it feeds one tick after it is taken.

## Transducers

A transducer wraps a single sensor or actuator and exposes three methods:

- `read()` returns the current sensor value as a float.
- `act()` sends the current command (stored in the `funcParameters` property) to the actuator.
- `range()` returns a `(min, max)` tuple describing the transducer's value range, used for scaling.

The concrete transducers (in `RobotSimulator/Transducer.py`) call the robot directly in Python, in both simulators: `HOMEO_DiffMotor` sets a wheel's speed (`setRightSpeed`/`setLeftSpeed`, in rad/s; its range is +/- the robot's top wheel speed); `HOMEO_LightSensor` reads an eye's response to the lights (`getSensorRead`), in [0, 1], or in [-1, 0] for a darkness source; `HOMEO_QualitySensor` reads an eye's response to the sources of one quality only (`getSensorReadByQuality`: light, temperature, oxygen, organic matter), for Vehicle 3c. The motor finds its robot by name each time it acts, the sensors keep the robot object they were made with: after a backend reset, which builds a new robot, make the sensors again (every experiment does).

Because all transducers share the same three-method interface, the homeostat has no knowledge of which backend it is talking to.

## Transducer-equipped units

Two specialised HomeoUnit subclasses bridge the homeostat to the robot.

`HomeoUnitInput` (in `RobotSimulator/HomeoUnitNewtonianTransduc.py`) is a read-only unit that acts as a sensor bridge. Its `selfUpdate()` does not run the normal homeostat dynamics; instead it reads a value from its transducer, scales it into the unit's deviation range, computes the corresponding output, and stops. Downstream units see it as an ordinary unit whose output tracks the external sensor. The `always_pos` flag controls whether the scaled value occupies the range [0, maxDeviation] or is centred at zero.

`HomeoUnitNewtonianActuator` extends `HomeoUnitNewtonian` with motor output. After running the standard `selfUpdate()` cycle -- torque computation, deviation update, uniselector check -- it converts its critical deviation into a wheel speed using a logistic sigmoid:

    speed = -maxSpeed + 2 * maxSpeed / (1 + exp(-switchingRate * criticalDeviation))

where `maxSpeed` is a fraction (`_maxSpeedFraction`, default 20 %) of the actuator's top speed, and `switchingRate` (default 0.1) sets the slope. The resulting speed, rounded to 0.001, is sent to the transducer via `act()`. The sigmoid never reaches `maxSpeed`: the deviation stops at +/-`maxDeviation`, and with the defaults (10 and 0.1) the speed there is tanh(0.5) = 0.462 of `maxSpeed`, about 9 % of the wheel's top speed. Small deviations give a speed nearly proportional to the deviation, 0.05 x `maxSpeed` per unit of deviation. An optional `_speedBias` adds a constant fraction of `maxSpeed` to one wheel (a baseline spin, `--spin` in the phototaxis scripts), clipped at +/-`maxSpeed`.

A simpler variant, `HomeoUnitAristotelianActuator` (an Aristotelian needle, `--motor aristotelian`), maps the deviation linearly onto the actuator's range (times `_maxSpeedFraction`, default 1: the whole range), with the same optional bias.

## Simulator backends

`SimulatorBackendAbstract` (in `Simulator/SimulatorBackend.py`) defines the interface that every backend must implement:

- `start(world)` -- launch the simulator with a given world or scene file.
- `reset()` / `resetPhysics()` -- restore the simulation to its initial state.
- `connect()` / `close()` / `quit()` -- manage the connection lifecycle.
- `getWheel(name)` -- return an actuator transducer for the named wheel (`'right'` or `'left'`).
- `getSensor(name)` -- return a sensor transducer for the named eye (`'right'` or `'left'`); `getQualitySensor(name, quality)` one that reads a single quality.
- `finalDisFromTarget()` -- query the current distance between the robot and the target, used as a fitness measure in genetic-algorithm experiments.
- `setRobotModel(name)` -- label the robot with an identifier (used for trajectory logging).
- `setDataDir(path)` -- set the directory for trajectory files.

The concrete backends:

**`SimulatorBackendHOMEO`** wraps the internal `KheperaSimulation` class. Since the simulator runs in the same process, transducers call Python methods directly -- `HOMEO_DiffMotor.act()` calls `robot.setRightSpeed(speed)` and `HOMEO_LightSensor.read()` calls `robot.getSensorRead(eye)` -- making it the fastest backend and the natural choice for batch experiments and genetic-algorithm optimisation.

**`SimulatorBackendWEBOTS`** runs Webots (`WebotsSimulator/WebotsSimulation.py`, the project in `src/Webots`). Homeo launches Webots with the Webots twin of the Box2D world (`homeo_braitenberg2.wbt`, `homeo_braitenberg3c.wbt`) and is its robot's *extern* controller, in Homeo's own process, and a supervisor. Webots advances only when Homeo steps it, once per homeostat tick, as the Box2D world does. Its `kheperaSimulation` is a `WebotsSimulation`, with KheperaSimulation's interface, so the same transducers and experiment setups work unchanged. The robot is `HomeoEpuck.proto`, Webots' e-puck with its light sensors reading plain irradiance; an eye's irradiance is the mean of its two LightSensors', its response Homeo's. The Vehicle 3c qualities other than light have no Webots physics: Homeo computes them from the Webots poses with the Box2D formula ("virtual sensors"). The light is a PointLight of the same intensity and attenuation as the Box2D one, at the sensors' height, so the two simulators' eyes read the same irradiance (checked by `Unit_Tests/WebotsBackendTest.py`); what differs is the physics of motion. Darkness sources and the K-Junior are Box2D only. One process runs one Webots. In the phototaxis scripts: `--simulator webots`, and `--render` to watch.

Swapping backends is transparent. The experiment-setup functions in `HomeoExperiments.py` take a backend instance (`backendSimulator`), call `basicBraiten2Tranducers(backend, world)` to obtain a dictionary of four transducers (two wheels, two eyes), and wire them into the same homeostat structure regardless of which backend produced them. The phototaxis scripts choose the backend with `--simulator` (`phototaxis_common.prepare_backend`).

## KheperaSimulator

KheperaSimulator (in `KheperaSimulator/KheperaSimulator.py`) is a lightweight 2D physics simulator built on pyBox2D and pyglet, designed for fast headless execution during genetic-algorithm runs. Its step is 0.032 s (`timeStep`), Webots' `basicTimeStep` in the twin worlds.

**`KheperaRobot`** models a differential-drive robot as a Box2D circular body. Since 14 Oct 2026 it is an **e-puck2** (`model='epuck2'`, the default), built to the dimensions of Webots' `E-puck.proto` so that the Box2D and the Webots vehicles are one robot: a body 74 mm across, wheels of 20 mm radius, 52 mm apart. Its motion is kinematic: with wheel speeds vR and vL (set in rad/s, times the wheel radius) and wheel separation L, the body moves forward at (vR + vL)/2 and turns at (vR - vL)/L, integrated exactly over each simulation step; the two `KheperaWheel` bodies only follow the chassis, for rendering. The top wheel speed, `maxWheelSpeed`, is in rad/s, the unit of `setRightSpeed`/`setLeftSpeed` and of the motor transducers' range. It is capped at the old vehicle's top speed, 24.3 mm/s (1.2166 rad/s), not the e-puck2's 151 mm/s, so that the homeostat's timescales keep their relation to the motion.

Each eye is a pair of the e-puck's light sensors at their real positions and facing their real directions: ls0 and ls1 (facing -17.2 and -45.9 degrees) on the right, ls7 and ls6 (17.1 and 45.8 degrees) on the left. An eye's irradiance is the mean of its two sensors', and each sensor has a Webots `LightSensor`'s field: the cosine law, nothing from behind (180 degrees, no hoods). Together the eyes see the front 146 degrees; an 88-degree sector straight behind is unseen.

The robot of every run before 14 Oct 2026 is kept as `model='kjunior'` (`KheperaSimulation(robotModel='kjunior')`, `--robot kjunior` in the phototaxis scripts): a K-Junior, 126 mm across, inherited from V-REP's model in 2015, with one 90-degree eye each side at +/- 22 degrees, half way in along its radius (`eyeRadiusRatio` 0.5) or on the rim (1.0, `--robot kjunior-rim` or `--rim-eyes`), as before 13 Oct 2026, when the rim eyes left a blind wedge straight ahead.

Each sensor computes irradiance from every detectable light source according to the formula

    irrad = (intensity * (1 - ambientRatio) * cos(angle) + intensity * ambientRatio) / (a + b * distance + c * distance^2)

where the attenuation vector (a, b, c) defaults to (0, 0, 1) for pure inverse-square decay. A sensor ignores lights outside its field (180 degrees for the e-puck2, 90 for the K-Junior); it has no maximum distance. Its reading is the eye's response to that irradiance: 0 up to a threshold, 1 from a saturation value, linear or logarithmic in between (`eyeResponse`). This is Webots' model of a light, so that results are comparable with the Webots backend.

**`KheperaSimulation`** manages the Box2D world, the bodies in it, and a `RobotTrajectoryWriter` that logs the robot's position at every step. The method `setupWorld(HomeoWorld)` calls a named setup function (e.g. `kheperaBraitenberg2_HOMEO_World`) that creates the world, places the robot and one or more lights, and initialises the trajectory writer. The simulation is advanced one step at a time by `advanceSim()`, which updates all bodies and steps the physics engine. The motors only set their wheel speeds; once every unit has updated, `Homeostat.runFor` calls `tickAdvance()`, which advances the world by two steps (a tick is 2 x 0.032 s). Runs before 13 Oct 2026 advanced the world one step per motor command instead (`synchronousStepping=False`, `--async-stepping` in the direct phototaxis experiment), so the left wheel's command acted one step before the right one's. `resetWorld()` tears down and rebuilds the world, opening a new trajectory file.

**`KheperaSimulationVisualizer`** is an optional pyglet window that renders the world in real time. It draws the robot, its sensor arcs, and the light sources over a reference grid, and supports pan, zoom, and tilt via mouse and keyboard. The visualiser is useful for debugging but is normally bypassed in batch mode.

**`KheperaRobotView`** is what the phototaxis experiments' `--visualize` window and the GA replay show. The robot is drawn at true size: a filled body with a radius along its heading, the wheels, and each light receptor as a small circle with a tick along its facing (left eye blue, right eye orange). The window opens on the whole arena, with a ring around the robot to find it by; C switches to a close-up that follows the robot, F follows or stops, V shows each eye's field of view (the outer boundary of its receptors' fields combined, out to 0.15 m, rendering only), the mouse wheel zooms and dragging pans.

The top-level function `runKheperaSimulator(headless=True/False, ...)` provides a convenient entry point: in headless mode it returns a `KheperaSimulation` ready for programmatic control; otherwise it launches the visualiser window.

## Experiment setup

The module `Simulator/HomeoExperiments.py` contains functions that return a fully wired homeostat for specific robotic experiments. The standard configuration for a Braitenberg-type light-seeking vehicle uses six units:

- Two **sensor-input units** (`HomeoUnitInput`) that read the left and right light sensors.
- Two **eye units** (regular `HomeoUnitNewtonian`) that receive input from the sensor units and participate in the internal homeostat dynamics.
- Two **motor units** (`HomeoUnitNewtonianActuator`) that drive the left and right wheels.

In the fixed topology (the default) only the Braitenberg wiring is active: each sensor feeds its eye, and each eye the motor on the other side (crossed, Vehicle 2b); the self-connections are manual, the cross-connections under uniselector control. In the random topology every connection between the four adaptive units is active. The sensor-input units are passive bridges; the four adaptive units maintain their essential variables through mutual interaction and, when necessary, changes of weights. The direct vehicle drops the eye units: two sensor-input units feed two motor units, the motors with negative self-connections.

The experiments, in `HomeoExperiments/KheperaExperiments/`:

- `phototaxis_braitenberg2_Ashby` -- the six-unit vehicle (`initializeBraiten2_2`), parameters and weights random, the uniselectors on the eyes and motors.
- `phototaxis_braitenberg2_direct` -- the direct vehicle; with `--fixed-weights` a non-adaptive Braitenberg vehicle (wiring crossed or `--uncrossed`, `--signs`, Newtonian or Aristotelian `--motor`), the baseline of the adaptive runs.

Both take the options listed in `phototaxis_common`'s docstring: the run length, seeds (`--seed` for the homeostat, `--env-seed` for the start pose), batches, the uniselector (Ashby's, or the continuous one with `--continuous`), the topology (`--random-topology`), the start pose, the eyes' response, a darkness source (`--dark`), the robot (`--robot`) and the simulator (`--simulator`). Each run records its settings in a JSON file, and a batch writes a summary CSV.

For the genetic algorithm (`Simulator/HomeoGenAlg.py`), each setup builds a homeostat from a genome of values in [0, 1]:

- `initializeBraiten2_2_Full_GA()` -- the six-unit vehicle, the genome (40 genes) encoding the four adaptive units' parameters and their connection weights; `_phototaxis` and `_scototaxis` variants set the fitness's sign.
- `initializeBraiten2_2_Full_GA_continuous_weightfree...`, `initializeBraiten2_direct_GA_continuous_weightfree...`, `initializeBraiten3c_GA_continuous_weightfree...` -- "weight-free" setups: the genome holds only the evolved units' parameters (mass, viscosity, the continuous uniselector's `tau_a`, `maxDeviation`), the weights start small and random and adapt during the run through the continuous uniselector. New runs use the `_v2` setups (since 15 Oct 2026): mass and viscosity log-uniform in [0.25, 250] and [0.05, 50]. The others are kept to replay old genomes: mass in [1, 10] and viscosity in [0, 10], linear, and, except the `_fixed_dt` ones, a `dt_fast` gene, which rescales mass and viscosity (review finding CU-11; the GA logbooks record each genome's layout, and GenomeDecoder adds the effective mass and viscosity).

Each function takes the backend instance (`backendSimulator`), plus optional flags like `noNoise` and `noUnisel` for ablation studies.

## Trajectory logging

Every simulation run produces a `.traj` file that records the robot's pose at every simulator step (two per homeostat tick), or every N-th step with `--traj-interval N`; the last row is always the final pose. The file is written by `RobotTrajectoryWriter` (in `Helpers/RobotTrajectoryWriter.py`), which is created automatically when a simulation world is set up.

Each `.traj` file starts with a header of comment lines and values, written at the run's first step: the sampling ("Sampled every N simulator steps, M steps per homeostat tick"), each light source's position, intensity (negative for a darkness source) and state, the robot model, the eyes as configured (threshold, saturation, response), and the robot's start position and heading. One tab-separated row per sample follows, with these columns:

| Column | Description |
|--------|-------------|
| `robot_x` | Robot x position |
| `robot_y` | Robot y position |
| `heading` | Robot heading in degrees (0-360) |
| `light_x` | Light source x position |
| `light_y` | Light source y position |
| `distance` | Euclidean distance from robot to light |

If multiple lights are present, a light_x, light_y, distance triplet follows for each further source, named after it.

Trajectory files are saved under the `SimulationsData` directory (`$HOMEO_DATA_DIR` if set, else Cybernetics-research/SimulationsData or Homeo/SimulationsData: `simulations_data_dir` in `Helpers/General_Helper_Functions.py`), the experiment scripts' in a dated subdirectory, `SimsData-YYYY-MM-DD`. When an experiment sets `kheperaSimulation.experimentName`, the filename is `experimentName-YYYY-MM-DD-HH-MM-SS<tag>.traj` (e.g. `phototaxis_braitenberg2_direct-2026-02-21-14-30-00.traj`), `<tag>` being `-NN` for a run with `--run-tag NN` (the HPC arrays' task serial); without one, `trajData-ID-modelName-YYYY-MM-DD-HH-MM-SS<tag>.traj`. A name already taken gets `-2`, `-3`, ..., so runs started in the same second do not overwrite each other. A run's `.log`, `.json` and `.statelog` share its stem.

The GA (`HomeoGenAlg.py`, run from its GUI `HomeoGenAlgGui.py` or from a script) creates timestamped subdirectories under `SimulationsData/` (`SimsData-YYYY-MM-DD-HH-MM-SS`) containing `.traj`, `.lgb` logbook, and `.hist` history files. Note that `.lgb` logbook files are only produced by GA optimisation runs, not by standalone experiments.

## Visualising experiment data

Two tools are provided for inspecting trajectory data:

**`TrajectoryGrapher`** (`Helpers/TrajectoryGrapher.py`, the command `homeo-traj`) plots one or more trajectories with matplotlib. It reads each `.traj` file, draws the robot's (x, y) path, marks the start position in green and the end position in red, overlays each light source, the ring beyond which the eyes see nothing (from the eyes in the file's header, or `--sensor-range`), and annotates the final distance to the target and the run's length in ticks. Several files are drawn on one chart; `-o` saves it (PDF, PNG, ...) instead of showing it.

    homeo-traj path/to/file.traj
    homeo-traj SimsData-*/run*.traj -o runs.pdf

**`TrajectoriesViewer`** (`Helpers/TrajectoriesViewer.py`) is a PyQt5 GUI for browsing and visualising multiple experiment runs. It lists all `.traj` files in a directory, supports changing directories, and auto-refreshes every second to pick up new files as they are written. Single-click a trajectory to select it; double-click or press "Visualize" to plot it via `TrajectoryGrapher`. If DEAP genetic-algorithm logbook files (`.lgb`) are present in the same directory, the viewer also provides buttons for inspecting GA statistics: hall of fame, full individual genomes, average fitness charts, and genealogy trees.

    python -m Helpers.TrajectoriesViewer
