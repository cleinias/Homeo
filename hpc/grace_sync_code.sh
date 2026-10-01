#!/bin/bash
# Put the Homeo source on Grace (or refresh it), and print the exact commit so
# every job's log says which code produced its results.
#
#     bash hpc/grace_sync_code.sh            # clone or fast-forward $SCRATCH/Homeo
#     HOMEO_REF=some-branch bash hpc/grace_sync_code.sh
#
# Clone over HTTPS, not SSH: the repo is public, so this needs no key on Grace.
# The clone is shallow -- the history is 22 MB and compute jobs never need it.
#
# If you are running uncommitted code, do NOT use this; rsync from the laptop
# instead (see "Getting the code there" in the HPC deployment plan) and the
# script will leave a non-git directory alone.
set -euo pipefail

HOMEO_SRC="${HOMEO_SRC:-$SCRATCH/Homeo}"
HOMEO_REPO="${HOMEO_REPO:-https://github.com/cleinias/Homeo.git}"
HOMEO_REF="${HOMEO_REF:-master}"

if [ -d "$HOMEO_SRC/.git" ]; then
    echo "== refreshing $HOMEO_SRC to origin/$HOMEO_REF"
    git -C "$HOMEO_SRC" fetch --depth 1 origin "$HOMEO_REF"
    git -C "$HOMEO_SRC" checkout -q -B "$HOMEO_REF" FETCH_HEAD
elif [ -d "$HOMEO_SRC" ]; then
    echo "== $HOMEO_SRC exists but is not a git checkout; leaving it as it is"
    echo "   (rsync'ed working copy?  Re-rsync it yourself.)"
else
    echo "== cloning $HOMEO_REPO ($HOMEO_REF) into $HOMEO_SRC"
    git clone --depth 1 --branch "$HOMEO_REF" "$HOMEO_REPO" "$HOMEO_SRC"
fi

echo
echo "code at $HOMEO_SRC:"
git -C "$HOMEO_SRC" log --oneline -1 2>/dev/null | sed 's/^/   /' \
    || echo "   (not a git checkout -- provenance unrecorded)"
