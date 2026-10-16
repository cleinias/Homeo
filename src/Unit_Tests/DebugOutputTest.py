'''
@author: stefano

The units' debug output (debugMode) and uniselector report
(showUniselectorAction), both GUI toggles, print without crashing on their
format strings.  Each unit kind runs a few ticks with both on.
'''
import contextlib
import io
import unittest

from Core.Homeostat import Homeostat
from Core.HomeoUnit import HomeoUnit
from Core.HomeoUnitAristotelian import HomeoUnitAristotelian
from Core.HomeoUnitNewtonian import HomeoUnitNewtonian


class DebugOutputTest(unittest.TestCase):

    def runWithBothToggles(self, unitClass):
        hom = Homeostat()
        hom.slowingFactor = 0
        units = [unitClass() for i in range(3)]
        for unit in units:
            unit.setRandomValues()
            hom.addFullyConnectedUnit(unit)
            unit.toggleDebugMode()
            unit.toggleShowUniselectorAction()
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            hom.runFor(3)
            units[0].operateUniselector()
        self.assertEqual(hom.time, 3)
        return err.getvalue()

    def testHomeoUnit(self):
        text = self.runWithBothToggles(HomeoUnit)
        self.assertIn('Current Deviat. at time: 0 for unit', text)
        self.assertIn('new position at time: 1 for unit', text)
        self.assertIn('activated uniselector for unit', text)

    def testAristotelianUnit(self):
        text = self.runWithBothToggles(HomeoUnitAristotelian)
        self.assertIn('New position at time: 1 for unit', text)
        self.assertIn('activated uniselector for unit', text)

    def testNewtonianUnit(self):
        text = self.runWithBothToggles(HomeoUnitNewtonian)
        self.assertIn('activated uniselector for unit', text)


if __name__ == '__main__':
    unittest.main()
