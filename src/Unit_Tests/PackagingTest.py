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

'''
What the install files ask for: requirements.txt asks only for what pip can
install (Box2D, which has no wheel under either of its names, is installed
first, as the README says), and numba, whose generator draws the headless
runs' noise, has one pinned version in requirements.txt, pyproject.toml and
hpc/grace_setup.sh, the one the suite runs with when it has numba.
'''
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def read(*path):
    with open(os.path.join(ROOT, *path)) as f:
        return f.read()


def requirements():
    return [line.split('#')[0].strip() for line in read('requirements.txt').splitlines()
            if line.split('#')[0].strip()]


class PackagingTest(unittest.TestCase):

    def testBox2DIsNotARequirement(self):
        self.assertFalse([r for r in requirements() if r.lower().startswith(('box2d', 'box2d-py'))])
        self.assertIn('pip install --no-build-isolation box2d-py', read('README.md'))

    def testNumbaIsPinnedOnce(self):
        [numba] = [r for r in requirements() if r.startswith('numba')]
        self.assertEqual(numba, 'numba==0.68.*')
        self.assertIn('"numba==0.68.*"', read('pyproject.toml'))
        self.assertIn('pip install "numba==0.68.*"', read('hpc', 'grace_setup.sh'))
        try:
            import numba
        except ImportError:
            return
        self.assertTrue(re.match(r'0\.68\.', numba.__version__), numba.__version__)


if __name__ == '__main__':
    unittest.main()
