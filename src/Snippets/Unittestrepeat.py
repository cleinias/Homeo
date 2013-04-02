import unittest
import random

SETUP_COUNTER = 0

class MyTestCase(unittest.TestCase):

    def setUp(self):
        global SETUP_COUNTER
        SETUP_COUNTER += 1

    def test_one(self):
        self.assertTrue(random.random() > 0.3)

    def test_two(self):
        # We just want to make sure this isn't run
        self.assertTrue(False, "This should not have been run")


def suite():
    tests = []
    for _ in range(100):
        tests.append('test_one')

    return unittest.TestSuite(map(MyTestCase, tests))

unittest.TextTestRunner().run(suite())
print 'setUp was run', SETUP_COUNTER, 'times'
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()