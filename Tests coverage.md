# Test Coverage Report

Measured at commit `2a728f1` (Rename Snippets directory to Scratch), branch `python3`.

134 of 135 tests passing. The single failure is a stochastic KS-test
(`testIndependentlyRandomizedValuesMatrix`) that occasionally falls below
the p > 0.05 threshold by chance.

## Well-covered modules

| Module | Coverage |
|--------|----------|
| `Core/HomeoNeedleUnit.py` | 100% |
| `Helpers/QObjectProxyEmitter.py` | 100% |
| `Helpers/SimulationThread.py` | 100% |
| `Core/HomeoUniselectorUniformRandom.py` | 96% |
| `Core/HomeoDataUnit.py` | 95% |
| `Core/HomeoUniselectorAshby.py` | 95% |
| `Helpers/HomeoNoise.py` | 94% |
| `Core/HomeoUniselector.py` | 90% |
| `Core/HomeoUnit.py` | 78% |
| `Core/Homeostat.py` | 78% |
| `Simulator/HomeoSimulation.py` | 76% |
| `Core/HomeoUnitNewtonian.py` | 67% |
| `Core/HomeoConnection.py` | 64% |
| `Simulator/HomeoQtSimulation.py` | 64% |

## Low or zero coverage

| Module | Coverage | Notes |
|--------|----------|-------|
| `Core/HomeoDataCollector.py` | 25% | Many export methods untested |
| `Core/HomeoUnitAristotelian.py` | 0% | No tests |
| `Simulator/HomeoExperiments.py` | 1% | Robotic experiment setups; need external backends |
| `Simulator/SimulatorBackend.py` | 0% | Backend code; needs external simulators |
| `Simulator/HomeoGeneralGUI.py` | 0% | GUI code |
| `Simulator/HomeoMinimalGui.py` | 0% | GUI code |
| `Simulator/HomeoGenAlgGui.py` | 0% | GUI code |
| `Helpers/StatsAnalyzer.py` | 0% | |
| `Helpers/GenomeDecoder.py` | 0% | |
| `Helpers/TrajectoryGrapher.py` | 0% | |
| `Helpers/TrajectoriesViewer.py` | 0% | |

Overall reported coverage is 14%, but this is heavily skewed by the large
auto-generated UI file (`Four_units_Homeostat_Standard_UI.py`, 3881 lines)
and the robotic/backend modules that cannot run without external simulators.
The core simulation logic is reasonably well covered (64--100%).
