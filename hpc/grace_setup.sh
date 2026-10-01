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

echo "== available Python modules (pick the newest 3.11+):"
module spider Python 2>&1 | grep -iE "Python/3\.(1[1-9])" | head || true
echo

# Load a Python module.  Adjust the exact name to whatever `module spider`
# above reports; GCCcore-suffixed names are the usual form on Grace.
module purge
module load GCCcore/13.2.0 Python/3.11.5 || {
    echo "!! Adjust the module load line to a version listed above." >&2
    exit 1
}

python -m venv "$VENV"
source "$VENV/bin/activate"
python -m pip install --upgrade pip wheel

# numba is optional (HomeoJIT degrades to a no-op) but gives a real speedup on
# the inner loops, and is NOT in requirements.txt.
python -m pip install \
    numpy scipy pandas matplotlib \
    deap dill tabulate \
    box2d-py pyglet \
    numba pytest

echo
echo "== verifying headless operation (no DISPLAY on compute nodes):"
cd "$HOMEO_SRC/src"
env -u DISPLAY -u WAYLAND_DISPLAY python -c "
import sys; sys.path.insert(0,'.')
import pyglet; pyglet.options['shadow_window'] = False
import HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct as D
r = D.run_headless(total_steps=500, quiet=True, seed=1, start_at_rest=True)
print('  headless OK, final_dist %.3f' % r['final_dist'])
"
echo
echo "== running the test suite:"
python -m pytest -q Unit_Tests 2>&1 | tail -2
echo
echo "Setup complete.  venv: $VENV"
