'''
@author: stefano

A unit's own noise cannot push its needle past the stops, headless or not.
The Python path adds the noise through the criticalDeviation setter, which
clips, and the headless path clips it too.  Without the clip a needle at a
stop would be pushed past it each tick, and clipped back with its velocity
zeroed: held at the stop by an outward kick that the Python path lets an
inward torque overcome.
'''
import Core.HomeoUnit as HomeoUnitModule
from Core.Homeostat import Homeostat
from Core.HomeoUnit import HomeoUnit
from Core.HomeoUnitNewtonian import HomeoUnitNewtonian

import unittest
from unittest import mock

KICK = 0.05


def _trajectory(unitClass, headless, ticks=6):
    '''A unit at its upper stop, pulled inwards by its self-connection,
    kicked outwards by a constant noise.'''
    HomeoUnit.clearNames()
    unit = unitClass()
    unit.uniselectorActive = False
    unit.noise = KICK                   # the patched noise functions return it
    hom = Homeostat()
    hom.addFullyConnectedUnit(unit)
    hom.slowingFactor = 0
    hom.collectsData = False
    hom._headless = headless
    unit._headless = headless
    selfConnection = unit.inputConnections[0]
    selfConnection.newWeight(-0.5)
    selfConnection.noise = 0
    selfConnection.state = 'manual'
    unit.criticalDeviation = unit.maxDeviation
    unit.computeOutput()
    positions = []
    with mock.patch.object(HomeoUnitModule, '_jit_unit_noise', lambda noise: noise), \
            mock.patch.object(HomeoUnitModule.HomeoNoise, 'unitNoise',
                              staticmethod(lambda noise: noise)):
        for _ in range(ticks):
            hom.runOnce()
            positions.append(unit.criticalDeviation)
    return positions


class HeadlessNoiseClipTest(unittest.TestCase):

    def testHeadlessAndPythonPathsAgreeAtTheStops(self):
        for unitClass in (HomeoUnitNewtonian, HomeoUnit):
            with self.subTest(unitClass.__name__):
                python = _trajectory(unitClass, headless=False)
                headless = _trajectory(unitClass, headless=True)
                for p, h in zip(python, headless):
                    self.assertAlmostEqual(p, h, places=9)

    def testTheNeedleLeavesTheStop(self):
        positions = _trajectory(HomeoUnitNewtonian, headless=True)
        self.assertLess(positions[-1], positions[0])
        self.assertLess(positions[-1], HomeoUnitNewtonian().maxDeviation)


if __name__ == '__main__':
    unittest.main()
