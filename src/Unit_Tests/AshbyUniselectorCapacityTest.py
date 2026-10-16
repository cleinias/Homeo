'''
@author: stefano

How many connections Ashby's uniselector can control.  It holds weights
for 10 connections and grows in steps of 10, as setUnitsControlled and
Homeostat.addFullyConnectedUnit (which calls the existing units'
maxConnectedUnits method) ask it to, so fully connected homeostats of 12 or
more units can fire.
'''
from Core.Homeostat import Homeostat
from Core.HomeoUnit import HomeoUnit
from Core.HomeoUniselector import HomeoUniselectorError
from Core.HomeoUniselectorAshby import HomeoUniselectorAshby

import unittest

import numpy as np

KINDS = ('randomized', 'equallySpaced', 'independentlyRandomized')


class AshbyUniselectorCapacityTest(unittest.TestCase):

    def testCapacityGrowsInStepsOfTen(self):
        for kind in KINDS:
            with self.subTest(kind):
                uniselector = HomeoUniselectorAshby()
                getattr(uniselector, kind)()
                uniselector.unitsControlled = 15
                self.assertEqual(uniselector.unitsControlled, 20)
                self.assertGreaterEqual(uniselector.matrix().shape[1], 20)
                for _ in range(3):
                    values = [uniselector.produceNewValue() for _ in range(20)]
                    uniselector.advance()
                    self.assertEqual(len(values), 20)

    def testCapacityNeverShrinks(self):
        uniselector = HomeoUniselectorAshby()
        uniselector.unitsControlled = 25
        uniselector.unitsControlled = 4
        self.assertEqual(uniselector.unitsControlled, 30)

    def testOneConnectionTooManyIsAnError(self):
        for kind in KINDS:
            with self.subTest(kind):
                uniselector = HomeoUniselectorAshby()
                getattr(uniselector, kind)()
                for _ in range(uniselector.matrix().shape[1]):
                    uniselector.produceNewValue()
                with self.assertRaises(HomeoUniselectorError):
                    uniselector.produceNewValue()

    def testLargeFullyConnectedHomeostatsCanFire(self):
        for n in (12, 13, 25):
            with self.subTest(units=n):
                np.random.seed(n)
                HomeoUnit.clearNames()
                hom = Homeostat()
                for _ in range(n):
                    hom.addFullyConnectedUnit(HomeoUnit())
                for unit in hom.homeoUnits:
                    self.assertTrue(callable(unit.maxConnectedUnits))
                    for conn in unit.inputConnections:
                        conn.state = 'uniselector'      # the self-connection too
                    self.assertGreaterEqual(unit.uniselector.unitsControlled, n)
                    unit.operateUniselector()


if __name__ == '__main__':
    unittest.main()
