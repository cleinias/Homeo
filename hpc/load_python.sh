# Sourced by the Homeo Grace scripts.  Loads Python 3.14.2 (matching the 3.14.7
# used in development) together with whatever toolchain Lmod requires for it.
#
# Lmod hides modules behind their compiler toolchain, so `module load
# Python/3.14.2` alone usually fails with "these module(s) are known but cannot
# be loaded".  `module spider Python/3.14.2` then prints the prerequisite line.
# Rather than hardcode a GCCcore version that may change, discover it.

HOMEO_PY_VERSION="${HOMEO_PY_VERSION:-Python/3.14.2}"

homeo_load_python() {
    module purge 2>/dev/null || true

    # 1. the simple case: no prerequisite needed
    if module load "$HOMEO_PY_VERSION" 2>/dev/null; then
        echo "loaded $HOMEO_PY_VERSION"
        return 0
    fi

    # 2. ask spider which toolchain unlocks it, and load that first
    local prereq
    prereq=$(module --redirect spider "$HOMEO_PY_VERSION" 2>&1 \
             | grep -oE '(GCCcore|GCC|foss|intel)/[0-9][0-9.]*' \
             | head -1)
    if [ -n "$prereq" ]; then
        echo "loading prerequisite $prereq"
        module load "$prereq" && module load "$HOMEO_PY_VERSION" && {
            echo "loaded $prereq + $HOMEO_PY_VERSION"; return 0; }
    fi

    echo "!! could not load $HOMEO_PY_VERSION." >&2
    echo "   Run: module spider $HOMEO_PY_VERSION" >&2
    echo "   then set HOMEO_PY_VERSION / load the prerequisite by hand." >&2
    return 1
}
