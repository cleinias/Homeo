'''
Created on Oct 14, 2026

@author: stefano

The debug-message helper (review finding HN-16): 'all' enables every code
only as a code of its own, and a message's formatting is deferred until it
is printed, so the per-connection hot path pays nothing when debugging is off.
'''
import io
import unittest
from unittest import mock

from Helpers import ExceptionAndDebugClasses as debugModule
from Helpers.ExceptionAndDebugClasses import HomeoDebug, hDebug


class Unformattable(object):
    "A %-argument that fails the test if it is ever formatted"
    def __float__(self):
        raise AssertionError('formatted although debugging is off')


class HomeoDebugTest(unittest.TestCase):

    def setUp(self):
        self.saved = HomeoDebug.debugCodes
        HomeoDebug.debugCodes = set()

    def tearDown(self):
        HomeoDebug.debugCodes = self.saved

    def testAllOnlyAsAWholeCode(self):
        with mock.patch.object(debugModule, 'stderr', io.StringIO()):
            HomeoDebug.addDebugCodes('ball')         # not a code: nothing enabled
        self.assertEqual(HomeoDebug.debugCodes, set())
        HomeoDebug.addDebugCodes('all')
        self.assertEqual(HomeoDebug.debugCodes, set(HomeoDebug.allowableCodes))

    def testFormattingDeferred(self):
        hDebug('conn', 'The noise on the connection is %f', Unformattable())
        HomeoDebug.addDebugCodes('unit')
        hDebug('conn', 'The noise on the connection is %f', Unformattable())
        out = io.StringIO()
        HomeoDebug.addDebugCodes('conn')
        with mock.patch.object(debugModule, 'stderr', out):
            hDebug('conn', 'The noise on the connection is %f', 0.25)
            hDebug('conn', 'plain message')
        self.assertEqual(out.getvalue(), 'The noise on the connection is 0.250000\nplain message\n')


if __name__ == '__main__':
    unittest.main()
