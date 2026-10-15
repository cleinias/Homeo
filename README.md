# Homeo

A software simulation of W. Ross Ashby's Homeostat, as described in
*Design for a Brain* (1952) and *Introduction to Cybernetics* (1956), and a
platform for research with it: Ashby's own experiments, and homeostats as
the controllers of simulated robots (Braitenberg vehicles).

## Features

- Full simulation of all components of Ashby's original Homeostat (units,
  uniselectors, connections), extensible to any number of units
- Ashby's seven experiments from *Design for a Brain*, interactive or in batch
- Generalized models of a homeostatic unit: Ashby's (Aristotelian: the
  needle's velocity follows the force) and Newtonian (a needle with mass,
  stepped exactly), with discrete (Ashby's) or continuous
  (Ornstein-Uhlenbeck) uniselectors
- Seeded, reproducible runs: a run's seed rebuilds the same homeostat and
  its noise, and is recorded with its results
- Interactive GUI (PyQt5) for building, running and manipulating homeostats,
  with real-time charts
- Robotic component: a homeostat as the controller of a simulated e-puck2,
  in a built-in Box2D simulator (fast, in-process: batch runs and the GA) or
  in Webots (Homeo as the robot's extern controller: re-testing results,
  figures).  Braitenberg vehicles 2 and 3c, phototaxis with light, darkness,
  temperature, oxygen and organic-matter sources
- Genetic algorithms (DEAP) that evolve homeostat-controlled vehicles
- Batch arrays on a SLURM cluster or on a workstation (`hpc/`)
- Analysis tools: trajectories, strip charts, state logs, TikZ diagrams of a
  homeostat's topology

## Getting started

```bash
pip install -r requirements.txt
pip install -e .                        # Homeo itself, editable
```

The editable install (`pyproject.toml`) puts `src/` on Python's path, so the
modules, which import each other as top-level packages (`from Helpers.X import
...`), work from any directory instead of only from `src/`.  It must be
editable: SimulationsData is located relative to the checkout.  On a
distribution's system Python (e.g. Arch), whose packages already provide the
dependencies:

```bash
pip install --user --break-system-packages --no-deps -e .
```

Webots is optional: only the `--simulator webots` runs need it (Webots
R2025a, found through `WEBOTS_HOME` or `webots` on the `PATH`; without a
display, Homeo runs it under `xvfb-run`).  See [src/Webots/README.md](src/Webots/README.md).

## Interactive runs

The `python -m` commands work from any directory:

```bash
python src/run_ashby_gui.py             # Ashby's 7 experiments (--exp N skips the selector,
                                        # --seed S builds the homeostat of seed S)
python -m Simulator.HomeoGeneralGUI     # general homeostat GUI
python -m Simulator.HomeoGenAlgGui      # genetic-algorithm GUI (needs DEAP)

# Braitenberg vehicles on the Box2D simulator, in a pyglet window
python -m HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct --visualize
python -m HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_Ashby --visualize

# the same vehicle in Webots, in its own window
python -m HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct \
    --fixed-weights --simulator webots --render
```

`Simulator.HomeoQtSimulation` is the simulation engine behind the Qt GUIs;
it has no window of its own.

## Batch runs

```bash
# Ashby's experiments: a .statelog per run, and a .json of its conditions
python src/run_ashby_original_experiments.py --exp 6 --seed 42

# phototaxis: a homeostat drives the vehicle toward a light.  _direct: 2 sensors
# feed 2 motor units; _Ashby: 6 units (sensors, eyes, motors).  --batch N runs N
# seeds and writes a summary CSV.  The options (robot, eyes, start pose, seeds,
# uniselector, simulator, ...) are listed in
# HomeoExperiments/KheperaExperiments/phototaxis_common.py
python -m HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct \
    --batch 20 --seed 1 --random-start --steps 300000

# genetic algorithms
python src/run_direct_vehicle_ga.py           # GA + OU on the direct vehicle
python src/run_phototaxis_comparison.py       # Ashby, OU, and two GA + OU runs side by side
python src/replay_best_with_statelog.py --logbook path.lgb   # replay an individual

# arrays: SLURM (hpc/grace_*.slurm) or a workstation
bash hpc/run_array_local.sh --dry-run
```

Results go to a `SimulationsData` directory: `$HOMEO_DATA_DIR` if set, else
next to the checkout (see `simulations_data_dir` in
`Helpers/General_Helper_Functions.py`).

The robot is an e-puck2 (both simulators; the dimensions of Webots'
`E-puck.proto`, each eye a pair of its light sensors).  The K-Junior of the
runs made before 14 Oct 2026 is kept as `--robot kjunior` to reproduce them.
See [ROBOTIC_OVERVIEW.md](ROBOTIC_OVERVIEW.md).

## Analysis

The install puts the analysis helpers on the path as commands (in
`~/.local/bin` for a `--user` install):

```bash
homeo-traj SimsData-*/run*.traj -o runs.pdf    # Helpers.TrajectoryGrapher
homeo-strip run.statelog --value weight        # Helpers.StripchartGrapher
homeo-statelog run.statelog                    # Helpers.StatelogAnalyzer
homeo-tikz run.log -o topology.tex             # Helpers.HomeostatDiagramTikz
```

## Running tests

```bash
cd src                        # pytest.ini lives here
python -m pytest Unit_Tests/ -x -q
```

The Webots tests are skipped where Webots cannot run.

## Project structure

```
src/
  Core/              # Homeostat core classes (units, connections, uniselectors)
  Helpers/           # Loggers, noise, analysis and graphing tools
  Simulator/         # Simulation engine, GUIs, Ashby's experiments, GA, simulator backends
  HomeoExperiments/  # Experiment setups (KheperaExperiments: the phototaxis scripts)
  KheperaSimulator/  # The Box2D robot simulator (an e-puck2; the K-Junior of older runs)
  WebotsSimulator/   # Webots as the robot simulator (Homeo as extern controller)
  Webots/            # The Webots project: HomeoEpuck.proto and the worlds
  RobotSimulator/    # Transducers and transducer-equipped units
  Unit_Tests/        # Pytest test suite
  run_*.py           # Batch and GA entry points
hpc/                 # SLURM arrays, workstation arrays, aggregation
Docs/                # Figures (e.g. the e-puck's fields of view)
resources/           # GUI resources (icons, images)
```

See [CODE_OVERVIEW.md](CODE_OVERVIEW.md) for a detailed walkthrough of the
codebase, and [ROBOTIC_OVERVIEW.md](ROBOTIC_OVERVIEW.md) for the robotic
integration.

## License

See [license.txt](license.txt) for details.
