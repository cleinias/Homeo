# Homeo's Webots project

Webots twins of Homeo's Box2D worlds, run by Homeo itself as its robot's
*extern* controller (`src/WebotsSimulator/WebotsSimulation.py`,
`SimulatorBackendWEBOTS` in `src/Simulator/SimulatorBackend.py`).  Nothing here
runs on its own: Homeo launches Webots with a world, steps it once per
homeostat tick, and reads the robot's pose as a supervisor.

- `protos/HomeoEpuck.proto`: Webots' `E-puck.proto` (R2025a), unchanged but
  for its light sensors' lookup table, which is a field and by default the
  plain irradiance (the original table reads a constant 4095 in these arenas).
  Homeo's robot is the e-puck2 (`version "2"`), in Box2D too.
- `worlds/homeo_braitenberg2.wbt`: the twin of `kheperaBraitenberg2_HOMEO_World`.
- `worlds/homeo_braitenberg3c.wbt`: the twin of `kheperaBraitenberg3c_HOMEO_World`;
  temperature, oxygen and organic matter are markers, their fields computed by
  Homeo ("virtual sensors").

Run an experiment on Webots with `--simulator webots` (add `--render` to watch it):

    python -m HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct \
        --fixed-weights --simulator webots --render

Webots must be installed (`WEBOTS_HOME`, or `webots` on the `PATH`).  Without a
display, Homeo runs it under `xvfb-run` with software OpenGL.
