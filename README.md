# Homeo

A software simulation of W. Ross Ashby's Homeostat, as described in
*Design for a Brain* (1952) and *Introduction to Cybernetics* (1956).

## Features

- Full simulation of all components of Ashby's original Homeostat
  (units, uniselectors, connections)
- Interactive GUI (PyQt5) for running and manipulating the simulated device
- Data logging and graphing capabilities
- Extensible to an arbitrary number of homeostatic units
- Generalized and supplemented model of a homeostatic unit, including
  Newtonian physics and continuous (Ornstein-Uhlenbeck) uniselectors
- Robotic component: use a homeostat as the controller of virtual robots
  in simulation environments (Webots, V-REP/CoppeliaSim)

## Getting started

```bash
pip install -r requirements.txt
pip install -e .                        # Homeo itself, editable
python -m Simulator.HomeoQtSimulation   # launch the GUI, from any directory
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

It also installs the analysis helpers as commands (in `~/.local/bin` for a
`--user` install):

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

## Project structure

```
src/
  Core/           # Homeostat core classes (units, connections, uniselectors)
  Helpers/        # Utility modules (signals, general helpers)
  Simulator/      # Simulation runners (CLI and GUI), GA experiments
  Unit_Tests/     # Pytest test suite
  HomeoExperiments/  # Predefined experiment configurations
  KheperaSimulator/  # Khepera robot integration
  RobotSimulator/    # Generic robot simulator
  Webots/            # Webots robot controller
resources/        # GUI resources (icons, images)
```

See [CODE_OVERVIEW.md](CODE_OVERVIEW.md) for a detailed walkthrough of the
codebase, and [ROBOTIC_OVERVIEW.md](ROBOTIC_OVERVIEW.md) for the robotic
integration.

## License

See [license.txt](license.txt) for details.