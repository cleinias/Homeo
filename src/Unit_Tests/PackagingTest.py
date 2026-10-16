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
