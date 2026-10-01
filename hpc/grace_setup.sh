#!/bin/bash
# One-time environment setup for Homeo on TAMU HPRC Grace.
#
# Bootstraps from nothing but a Grace login shell:
#     cd $SCRATCH
#     git clone --depth 1 https://github.com/cleinias/Homeo.git
#     bash Homeo/hpc/grace_setup.sh
#
# It fetches the code (grace_sync_code.sh), builds the venv, then verifies both
# headless operation and the test suite.  Run it once; afterwards
# grace_sync_code.sh alone refreshes the code without rebuilding the venv.
set -euo pipefail

HOMEO_SRC="${HOMEO_SRC:-$SCRATCH/Homeo}"
VENV="${VENV:-$SCRATCH/homeo-venv}"
_hpc_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bash "$_hpc_dir/grace_sync_code.sh"
echo

source "$_hpc_dir/load_python.sh"
homeo_load_python || exit 1
echo

# Reuse an existing venv rather than recreating it.  `python -m venv` on a
# populated venv rewrites bin/activate, which fails outright if that file is not
# writable ("Errno 13 Permission denied: .../bin/activate") even though the venv
# itself is perfectly usable.  Re-running this script must be safe.
if [ -x "$VENV/bin/python" ]; then
    echo "== reusing existing venv at $VENV"
    echo "   (delete it and re-run if you want a clean one)"
else
    echo "== creating venv at $VENV"
    python -m venv "$VENV"
fi
source "$VENV/bin/activate"
python -m pip install --upgrade pip setuptools wheel

# ---------------------------------------------------------------------------
# box2d-py has NO wheel on PyPI for any current CPython (checked 2026-10-01:
# none for cp311/312/313/314), so pip always builds it from source, and the
# build runs swig.  Without swig it dies with
#     error: command 'swig' failed: No such file or directory
#
# The PyPI `swig` package provides the binary without needing a cluster module,
# but it is a Python shim that imports its own package -- so inside pip's
# isolated build environment it fails with "No module named 'swig'".  Hence
# --no-build-isolation for this one install, which lets the shim see the venv
# it was installed into.  Verified building box2d-py 2.3.8 on Python 3.14.
#
# A real swig binary works too (`module load SWIG`) and needs no special flag,
# but the module is toolchain-gated on Grace like Python is, so the pip route
# is the one that always works.
# ---------------------------------------------------------------------------
python -m pip install swig
python -m pip install --no-build-isolation box2d-py

# PyQt5 is needed even for headless batch runs, which is not obvious: the Core
# classes emit their signals through Helpers/QObjectProxyEmitter, whose SignalHub
# is a QObject, so run_headless() ends up importing PyQt5.QtCore.  Only QtCore is
# touched -- no QApplication, no display -- and the PyQt5 wheels are cp38-abi3,
# so they install on Python 3.14 and work with DISPLAY unset (verified).
#
# The cleaner fix would be for QObjectProxyEmitter to degrade to a no-op emitter
# when PyQt5 is absent, the way HomeoJIT degrades without numba. Until then the
# simulation core has a hard dependency on a GUI toolkit.
python -m pip install \
    numpy scipy pandas matplotlib \
    deap dill tabulate \
    pyglet PyQt5 \
    pytest

# numba is optional (HomeoJIT degrades silently to a no-op decorator) but gives
# a real speedup on the inner loops, and is NOT in requirements.txt.
python -m pip install numba || echo "!! numba unavailable for this Python; continuing without JIT"

python -c "import Box2D; print('box2d-py OK:', Box2D.__version__)"

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
# Do not let a failing test abort setup: with `set -o pipefail` a non-zero pytest
# exit kills the pipeline and the script dies before saying it finished, which
# reads as a broken environment when it is not.  Expect 184 passed / 1 failed --
# HomeoUnitTest::testUnitNameUnique is order-dependent (it counts units created
# earlier in the session) and fails in the full suite while passing alone.
if python -m pytest -q Unit_Tests 2>&1 | tail -2; then
    :
else
    echo "   (pytest reported failures -- see the tally above)"
fi
echo
echo "Setup complete.  venv: $VENV"
