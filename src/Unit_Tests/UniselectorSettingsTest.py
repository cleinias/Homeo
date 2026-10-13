'''
Created on Oct 13, 2026

@author: stefano

The uniselectors' settings do what they say (review finding CD-16).  They
used to be traps for scripts: setting beeps raised, the sound signal the GUI
listens for was never sent, setting an Ashby uniselector's steps left its
matrix at 25 rows, setting its kind was ignored, and the continuous
uniselector took any bounds, (-1, 5) for upperBound = 5.
'''
from Core.HomeoUniselector import HomeoUniselector, HomeoUniselectorError
from Core.HomeoUniselectorAshby import HomeoUniselectorAshby
from Core.HomeoUniselectorContinuous import HomeoUniselectorContinuous
from Helpers.QObjectProxyEmitter import emitter

import unittest

import numpy as np


class UniselectorSettingsTest(unittest.TestCase):

    def testBeepsCanBeSetAndSignalTheGui(self):
        uniselector = HomeoUniselectorAshby()
        heard = []
        emitter(uniselector).uniselSoundChanged.connect(heard.append)
        uniselector.beeps = True
        self.assertTrue(uniselector.beeps)
        uniselector.toggleBeeping()
        self.assertFalse(uniselector.beeps)
        self.assertEqual(heard, [True, False])

    def testStepsRebuildTheMatrix(self):
        uniselector = HomeoUniselectorAshby()
        uniselector.steps = 3
        self.assertEqual(uniselector.matrix().shape, (7, uniselector.unitsControlled))
        for _ in range(10):
            values = [uniselector.produceNewValue() for _ in range(3)]
            uniselector.advance()
            self.assertEqual(len(values), 3)

    def testFewerStepsKeepThePositionOnTheSwitch(self):
        uniselector = HomeoUniselectorAshby()
        for _ in range(20):
            uniselector.advance()
        uniselector.steps = 3
        uniselector.produceNewValue()

    def testTheKindCanBeSetByName(self):
        uniselector = HomeoUniselectorAshby()
        uniselector.ashbyKind = 'EquallySpacedValues'
        self.assertEqual(uniselector.ashbyKind, 'EquallySpacedValues')
        self.assertTrue(np.array_equal(np.sort(uniselector.matrix()[:, 0]), np.linspace(-1, 1, 25)))
        uniselector.ashbyKind = 'IndependentlyRandomizedValues'
        self.assertEqual(uniselector.ashbyKind, 'IndependentlyRandomizedValues')
        with self.assertRaises(HomeoUniselectorError):
            uniselector.ashbyKind = 'Shuffled'

    def testContinuousBoundsAreSymmetric(self):
        uniselector = HomeoUniselectorContinuous()
        uniselector.upperBound = 5
        self.assertEqual((uniselector.lowerBound, uniselector.upperBound), (-5, 5))
        uniselector.lowerBound = -2
        self.assertEqual((uniselector.lowerBound, uniselector.upperBound), (-2, 2))
        for bad in (('upperBound', -1), ('upperBound', 0), ('lowerBound', 3), ('lowerBound', 0)):
            with self.subTest(bad):
                with self.assertRaises(HomeoUniselectorError):
                    setattr(uniselector, *bad)
        self.assertEqual((uniselector.lowerBound, uniselector.upperBound), (-2, 2))

    def testContinuousDtCanBeSet(self):
        uniselector = HomeoUniselectorContinuous()
        uniselector.dt = 0.5
        self.assertEqual(uniselector.dt, 0.5)
        self.assertEqual(uniselector._dt, 0.5)
        with self.assertRaises(HomeoUniselectorError):
            uniselector.dt = 0


if __name__ == '__main__':
    unittest.main()
