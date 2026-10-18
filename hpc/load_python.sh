# Copyright (C) 2026 Stefano Franchi
#
# This file is part of Homeo, a simulation of Ashby's homeostat and of
# homeostat-controlled robots.
#
# Homeo is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# Homeo is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with Homeo.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
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
