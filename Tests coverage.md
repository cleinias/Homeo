# Test Coverage Report

Measured for release v0.1.0, with Python 3.14.7, numba 0.68.0 and Webots R2025a.

**659 tests pass, none fail or are skipped** (17,216 subtests; about 7 minutes). The Webots
tests (`WebotsBackendTest`) run only where Webots can start, and are skipped elsewhere.

Overall line coverage of `src/` (tests excluded): **84%** (11,212 statements, 1,783 not run).

## How it was measured

```bash
cd src
COVERAGE_RCFILE=covrc QT_QPA_PLATFORM=offscreen python -m coverage run -m pytest -q Unit_Tests
python -m coverage combine && python -m coverage report --sort=cover
```

with `covrc`:

```ini
[run]
source = <checkout>/src
omit = */Unit_Tests/*
parallel = true
patch = subprocess
```

`patch = subprocess` also measures the scripts the tests run in subprocesses (the phototaxis
CLIs, the Webots runs, the replay, the Ashby experiments' runner). The GUI tests run offscreen.

## Coverage by module

| Module | Statements | Coverage |
|--------|-----------:|---------:|
| **Core** | | |
| `Core/HomeoNeedleUnit.py` | 23 | 100% |
| `Core/HomeoUniselectorAshby.py` | 84 | 100% |
| `Core/HomeoUniselectorContinuous.py` | 104 | 100% |
| `Core/HomeoUniselectorUniformRandom.py` | 26 | 100% |
| `Core/HomeoUnitAristotelian.py` | 18 | 100% |
| `Core/HomeoDataUnit.py` | 70 | 99% |
| `Core/HomeoDataCollector.py` | 107 | 97% |
| `Core/HomeoUniselector.py` | 39 | 97% |
| `Core/Homeostat.py` | 196 | 95% |
| `Core/HomeoUnit.py` | 748 | 94% |
| `Core/HomeoUnitNewtonian.py` | 133 | 85% |
| `Core/HomeoConnection.py` | 171 | 74% |
| `Core/HomeoJIT.py` | 129 | 60% |
| **Simulator** | | |
| `Simulator/AshbyOriginalExperiments.py` | 566 | 98% |
| `Simulator/HomeoExperiments.py` | 879 | 96% |
| `Simulator/HomeoGenAlg.py` | 507 | 95% |
| `Simulator/HomeoQtSimulation.py` | 262 | 95% |
| `Simulator/HomeoGeneralGUI.py` | 868 | 93% |
| `Simulator/SimulatorBackend.py` | 124 | 81% |
| `Simulator/HomeoGenAlgGui.py` | 269 | 79% |
| `Simulator/AshbyExperimentGui.py` | 316 | 61% |
| **Robots and experiments** | | |
| `HomeoExperiments/KheperaExperiments/phototaxis_braitenberg2_direct.py` | 239 | 99% |
| `HomeoExperiments/KheperaExperiments/phototaxis_common.py` | 499 | 94% |
| `HomeoExperiments/KheperaExperiments/phototaxis_braitenberg2_Ashby.py` | 81 | 93% |
| `RobotSimulator/HomeoUnitNewtonianTransduc.py` | 87 | 90% |
| `WebotsSimulator/WebotsSimulation.py` | 317 | 90% |
| `KheperaSimulator/KheperaSimulator.py` | 894 | 82% |
| `RobotSimulator/Transducer.py` | 105 | 80% |
| **Helpers** | | |
| `Helpers/ExceptionAndDebugClasses.py` | 21 | 100% |
| `Helpers/ExperimentOrchestrator.py` | 39 | 100% |
| `Helpers/HomeoNoise.py` | 23 | 100% |
| `Helpers/QObjectProxyEmitter.py` | 76 | 100% |
| `Helpers/HomeostatStateLogger.py` | 125 | 98% |
| `Helpers/HomeostatConditionLogger.py` | 181 | 93% |
| `Helpers/RobotTrajectoryWriter.py` | 151 | 92% |
| `Helpers/StripchartGrapher.py` | 286 | 89% |
| `Helpers/HomeostatDiagramTikz.py` | 212 | 86% |
| `Helpers/SimulationThread.py` | 13 | 85% |
| `Helpers/GenomeDecoder.py` | 158 | 80% |
| `Helpers/SFLineEdit.py` | 17 | 76% |
| `Helpers/TrajectoryGrapher.py` | 403 | 75% |
| `Helpers/CustomWidgets.py` | 39 | 74% |
| `Helpers/General_Helper_Functions.py` | 74 | 73% |
| `Helpers/TrajectoriesViewer.py` | 294 | 73% |
| `Helpers/StatsAnalyzer.py` | 225 | 62% |
| `Helpers/StatelogAnalyzer.py` | 411 | 28% |
| **Entry-point scripts** | | |
| `replay_best_with_statelog.py` | 235 | 63% |
| `run_ashby_original_experiments.py` | 217 | 54% |
| `run_direct_vehicle_ga.py` | 73 | 45% |
| `run_phototaxis_comparison.py` | 61 | 28% |
| `run_ashby_gui.py` | 17 | 0% |

## Notes on the low numbers

- **`Core/HomeoJIT.py` (60%)** is mostly numba-compiled functions. Coverage cannot trace code
  that runs compiled, so their bodies count as not run although every headless test runs
  them; `HomeostatHeadlessTest` checks them tick for tick against the Python path, with the
  continuous and the discrete uniselectors.
- **`Core/HomeoConnection.py` (74%)**: the unmeasured lines are two alternative constructors
  nothing calls, and the GUI's switch and state toggles.
- **The `run_*.py` entry points** are command-line wrappers. Their options are tested
  (`ExperimentOrchestratorTest`, `AshbyRunnerTest`, which also runs one experiment through
  `run_ashby_original_experiments.py`), and what they run is tested (the Ashby experiments,
  the GA, the orchestration loop); the long runs they launch are not. `run_ashby_gui.py` only
  opens the GUI.
- **`Helpers/StatelogAnalyzer.py` (28%)** and **`Helpers/StatsAnalyzer.py` (62%)**: the parsing,
  enrichment, logbook decoding and hall-of-fame ranking are tested; the plotting functions
  (`plot_*`), the printed summary and the command line are not.
- **`Simulator/AshbyExperimentGui.py` (61%)**: the setups, the run (equal to the headless run
  of the same seed) and the resets are tested; much of the window's interactive handling
  (dialogs, live charts) is not.
- **`replay_best_with_statelog.py` (63%)**: the replay of every GA vehicle and of k-run
  evaluations is tested; the visualizer is not.
- **`KheperaSimulator/KheperaSimulator.py` (82%)**: the unmeasured lines are mostly the pyglet
  drawing and the visualizer window (`KheperaSimulationVisualizer`), and demo worlds
  (`braiten2a`, `braiten2b`, `sensorTesting`); the motion, eyes, sensors and worlds are tested.
