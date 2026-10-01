#!/bin/bash
# One-time environment setup for Homeo on TAMU HPRC Grace.
#
# Run this ONCE on a Grace login node, from your scratch space:
#     cd $SCRATCH && bash /path/to/Homeo/hpc/grace_setup.sh
#
# It clones nothing: point HOMEO_SRC at the code you want to run.
set -euo pipefail

HOMEO_SRC="${HOMEO_SRC:-$SCRATCH/Homeo}"
VENV="${VENV:-$SCRATCH/homeo-venv}"

source "$(dirname "${BASH_SOURCE[0]}")/load_python.sh"
homeo_load_python || exit 1
echo

python -m venv "$VENV"
source "$VENV/bin/activate"
python -m pip install --upgrade pip wheel

# numba is optional (HomeoJIT degrades silently to a no-op decorator) but gives
# a real speedup on the inner loops, and is NOT in requirements.txt.  box2d-py
# needs swig to build; if the wheel is unavailable, `module load SWIG` first.
#
# Python 3.14 is recent enough that some wheels may not exist yet -- if numba or
# box2d-py fails here, drop numba (the code runs without it) and report the
# box2d failure, which IS fatal.
python -m pip install \
    numpy scipy pandas matplotlib \
    deap dill tabulate \
    box2d-py pyglet \
    pytest
python -m pip install numba || echo "!! numba unavailable for this Python; continuing without JIT"

echo
echo "== verifying headless operation (no DISPLAY on compute nodes):"
cd "$HOMEO_SRC/src"
env -u DISPLAY -u WAYLAND_DISPLAY python -c "
import sys; sys.path.insert(0,'.')
import pyglet; pyglet.options['shadow_window'] = False   # no GL context on compute nodes
import HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct as D
r = D.run_headless(total_steps=500, quiet=True, seed=1, start_at_rest=True)
print('  headless OK, final_dist %.3f' % r['final_dist'])
"
echo
echo "== running the test suite:"
python -m pytest -q Unit_Tests 2>&1 | tail -2
echo
echo "Setup complete.  venv: $VENV"
