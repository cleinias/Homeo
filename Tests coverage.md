# Test Coverage Report

Measured on 14 Oct 2026 at commit `29a3839` (branch `phase-h-cleanup`: the fixes of the
7 Oct 2026 code review, Phases A–H), with Python 3.14.7, numba 0.68.0 and Webots R2025a.

**581 tests pass, none fail or are skipped** (17,155 subtests; about 4 minutes). The Webots
tests (`WebotsBackendTest`) run only where Webots can start, and are skipped elsewhere.

Overall line coverage of `src/` (tests excluded): **79%** (11,279 statements, 2,366 not run).

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
CLIs, the Webots runs, the replay). The GUI tests run offscreen.

## Coverage by module

| Module | Statements | Coverage |
|--------|-----------:|---------:|
| **Core** | | |
| `Core/HomeoNeedleUnit.py` | 23 | 100% |
| `Core/HomeoUniselectorAshby.py` | 82 | 100% |
| `Core/HomeoUniselectorContinuous.py` | 116 | 100% |
| `Core/HomeoUniselectorUniformRandom.py` | 24 | 100% |
| `Core/HomeoUnitAristotelian.py` | 18 | 100% |
| `Core/HomeoDataUnit.py` | 70 | 99% |
| `Core/HomeoDataCollector.py` | 107 | 97% |
| `Core/HomeoUniselector.py` | 39 | 97% |
| `Core/Homeostat.py` | 196 | 95% |
| `Core/HomeoUnit.py` | 735 | 93% |
| `Core/HomeoUnitNewtonian.py` | 121 | 86% |
| `Core/HomeoConnection.py` | 164 | 69% |
| `Core/HomeoJIT.py` | 129 | 26% (see below) |
| **Simulator** | | |
| `Simulator/HomeoExperiments.py` | 887 | 97% |
| `Simulator/HomeoGenAlg.py` | 456 | 95% |
| `Simulator/HomeoQtSimulation.py` | 262 | 95% |
| `Simulator/HomeoGeneralGUI.py` | 845 | 92% |
| `Simulator/AshbyOriginalExperiments.py` | 557 | 89% |
| `Simulator/HomeoGenAlgGui.py` | 268 | 80% |
| `Simulator/SimulatorBackend.py` | 126 | 79% |
| `Simulator/AshbyExperimentGui.py` | 312 | 60% |
| **Robots and experiments** | | |
| `HomeoExperiments/KheperaExperiments/phototaxis_braitenberg2_direct.py` | 239 | 99% |
| `HomeoExperiments/KheperaExperiments/phototaxis_braitenberg2_Ashby.py` | 81 | 93% |
| `HomeoExperiments/KheperaExperiments/phototaxis_common.py` | 531 | 82% |
| `RobotSimulator/HomeoUnitNewtonianTransduc.py` | 87 | 90% |
| `RobotSimulator/Transducer.py` | 107 | 80% |
| `WebotsSimulator/WebotsSimulation.py` | 304 | 87% |
| `KheperaSimulator/KheperaSimulator.py` | 847 | 72% |
| **Helpers** | | |
| `Helpers/ExceptionAndDebugClasses.py` | 21 | 100% |
| `Helpers/ExperimentOrchestrator.py` | 39 | 100% |
| `Helpers/HomeoNoise.py` | 23 | 100% |
| `Helpers/QObjectProxyEmitter.py` | 75 | 100% |
| `Helpers/HomeostatStateLogger.py` | 124 | 99% |
| `Helpers/HomeostatConditionLogger.py` | 183 | 92% |
| `Helpers/RobotTrajectoryWriter.py` | 146 | 92% |
| `Helpers/StripchartGrapher.py` | 286 | 89% |
| `Helpers/General_Helper_Functions.py` | 65 | 88% |
| `Helpers/HomeostatDiagramTikz.py` | 212 | 86% |
| `Helpers/SimulationThread.py` | 13 | 85% |
| `Helpers/QtSeparator.py` | 35 | 83% |
| `Helpers/GenomeDecoder.py` | 152 | 80% |
| `Helpers/SFLineEdit.py` | 17 | 76% |
| `Helpers/TrajectoryGrapher.py` | 395 | 75% |
| `Helpers/CustomWidgets.py` | 39 | 74% |
| `Helpers/TrajectoriesViewer.py` | 294 | 73% |
| `Helpers/StatsAnalyzer.py` | 206 | 52% |
| `Helpers/StatelogAnalyzer.py` | 411 | 28% |
| **Entry-point scripts** | | |
| `replay_best_with_statelog.py` | 257 | 62% |
| `run_ashby_gui.py` | 17 | 0% |
| `run_ashby_original_experiments.py` | 200 | 0% |
| `run_direct_vehicle_ga.py` | 76 | 0% |
| `run_phototaxis_comparison.py` | 60 | 0% |

## Notes on the low numbers

- **`Core/HomeoJIT.py` (26%)** is mostly numba-compiled functions. Coverage cannot trace code
  that runs compiled, so their bodies count as not run although every headless test runs
  them; `HomeostatHeadlessTest` checks them tick for tick against the Python path.
- **`Core/HomeoConnection.py` (69%)**: the unmeasured lines are two alternative constructors
  nothing calls, and the GUI's switch and state toggles.
- **The `run_*.py` entry points** are thin command-line wrappers. What they run is tested
  (the Ashby experiments in `AshbyExperimentsTest`, the GA in the GA tests, the orchestration
  loop in `ExperimentOrchestratorTest`); the scripts themselves, which launch long runs, are
  not.
- **`Helpers/StatelogAnalyzer.py` (28%)** and **`Helpers/StatsAnalyzer.py` (52%)**: the parsing,
  enrichment and logbook decoding are tested; the plotting functions (`plot_*`), the printed
  summary and the command line are not.
- **`Simulator/AshbyExperimentGui.py` (60%)**: the setups and the run are tested; much of the
  window's interactive handling (dialogs, live charts) is not.
- **`KheperaSimulator/KheperaSimulator.py` (72%)**: the unmeasured lines are mostly the pyglet
  drawing and the visualizer window (`KheperaSimulationVisualizer`), and old demo worlds
  (`braiten2a`, `braiten2b`, `sensorTesting`); the physics, eyes, sensors and worlds are tested.

## Changes since the previous report

The previous report (commit `2a728f1`) counted 135 tests and 14% overall coverage, with
the robot setups, backends, GUIs, analysis tools and the Aristotelian unit at 0%. Since then:
- the test suite was rebuilt during the review fixes (Phases A–H, Oct 2026): 581 tests;
- the code that could not run was deleted: V-REP and the old Webots bridge, the generated
  UI module, `HomeoMinimalGui`, `HomeoSimulation`, the broken data exporters, the unused
  `getNoise*` noise algorithms and the legacy setups;
- the stochastic KS-test failure the old report described no longer occurs: every test
  runs on a fixed random stream (`conftest.py`).
