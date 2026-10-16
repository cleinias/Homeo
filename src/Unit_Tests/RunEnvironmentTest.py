'''
The suite leaves the run environment as it found it: a test or a test class
that points HOMEO_DATA_DIR (or HOMEO_RUN_TAG) elsewhere and pops it after
does not change it for the tests that follow (conftest.py); and the data
directory the tests start with is the suite's own temporary one, not the one
HOMEO_DATA_DIR names when pytest starts.  Run as pytest runs the suite, on two
small test files beside a copy of conftest.py.
'''
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)

POPPING = """
import os, unittest

class PopsInTheClass(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ['HOMEO_DATA_DIR'] = '/elsewhere'
    @classmethod
    def tearDownClass(cls):
        os.environ.pop('HOMEO_DATA_DIR', None)
    def test(self):
        pass

class PopsInTheTest(unittest.TestCase):
    def test(self):
        os.environ['HOMEO_DATA_DIR'] = '/elsewhere'
        os.environ['HOMEO_RUN_TAG'] = '07'
        os.environ.pop('HOMEO_DATA_DIR')
"""

PROBE = """
import os

def test_the_environment_is_as_it_was():
    data = os.environ['HOMEO_DATA_DIR']
    assert os.path.basename(data).startswith('homeo-suite-data-'), data
    assert data != os.environ['CALLERS_DATA_DIR']
    assert 'HOMEO_RUN_TAG' not in os.environ
"""


class RunEnvironmentTest(unittest.TestCase):

    def testTestsLeaveTheDataDirectoryAsItWas(self):
        "the run environment is restored, and the data directory is the suite's own"
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copy(os.path.join(HERE, 'conftest.py'), tmp)
            for name, text in (('test_a_pops.py', POPPING), ('test_b_probe.py', PROBE)):
                with open(os.path.join(tmp, name), 'w') as f:
                    f.write(text)
            callers = os.path.join(tmp, 'data')
            env = dict(os.environ, HOMEO_DATA_DIR=callers, CALLERS_DATA_DIR=callers,
                       PYTHONPATH=SRC + os.pathsep + os.environ.get('PYTHONPATH', ''))
            env.pop('HOMEO_RUN_TAG', None)
            r = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
                                'test_a_pops.py', 'test_b_probe.py'],
                               cwd=tmp, env=env, capture_output=True, text=True, timeout=300)
            self.assertEqual(r.returncode, 0, r.stdout[-2000:] + r.stderr[-2000:])
            self.assertIn('3 passed', r.stdout)
            self.assertFalse(os.path.exists(callers))


if __name__ == '__main__':
    unittest.main()
