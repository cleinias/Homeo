# Copyright (C) 2006-2026 Stefano Franchi
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

from   Core.HomeoUnit import *
from   Core.Homeostat import *
import unittest, string, random
from copy import copy

class HomeoConnectionTest(unittest.TestCase):


    def setUp(self):
        """
        Set up a unit connected to itself
        """
        self.unit = HomeoUnit()
        self.unit.setRandomValues()
        self.unit.selfUpdate()              #allows the unit to have some values in its slots"
        self.connection = HomeoConnection()
        self.connection.incomingUnit = self.unit

    def tearDown(self):
        pass

    def testOutgoingUnitIsAProperty(self):
        '''outgoingUnit is a property, not shadowed by a method, and does
           not send assignments to the instance dictionary: it reads the
           unit set, None before one is set, and a change of weight marks the
           holding unit's headless arrays stale.'''
        self.assertIsInstance(HomeoConnection.__dict__['outgoingUnit'], property)
        self.assertIsNone(self.connection.outgoingUnit)
        holder = HomeoUnit()
        self.connection.outgoingUnit = holder
        self.assertIs(self.connection.outgoingUnit, holder)
        self.assertIs(self.connection._outgoingUnit, holder)
        self.assertNotIn('outgoingUnit', self.connection.__dict__)
        holder._jit_dirty = False
        self.connection.newWeight(0.3)
        self.assertTrue(holder._jit_dirty)

    def testConnectionsPickledWithOutgoingUnitInTheirDictLoad(self):
        '''A connection pickle that keeps its outgoing unit under
           'outgoingUnit' in its dictionary loads with the unit in place.'''
        import pickle
        holder = HomeoUnit()
        self.connection.outgoingUnit = holder
        state = dict(self.connection.__dict__)
        state['outgoingUnit'] = state.pop('_outgoingUnit')
        old = HomeoConnection.__new__(HomeoConnection)
        old.__dict__.update(state)
        loaded = pickle.loads(pickle.dumps(old))
        self.assertEqual(loaded.outgoingUnit.name, holder.name)
        self.assertNotIn('outgoingUnit', loaded.__dict__)


    def testAddConnection(self):
        "Test the unit we setup is properly connected to itself"
        self.assertTrue(self.connection.incomingUnit == self.unit)

    def testDefaults(self):
        "Test default values for a connection "
        self.assertTrue(self.connection.weight >  0 and
                        self.connection.weight < 1)
        self.assertTrue(self.connection.noise > 0 and
                        self.connection.noise < 0.1)
        self.assertTrue(self.connection.switch is not None)
        
    def testSameAs(self):
        "Test if two connections are the same"

        self.unit = HomeoUnit()
        self.unit.setRandomValues()
        unit2 = HomeoUnit()
        unit2.setRandomValues()

        self.connection.randomizeConnectionValues()
        self.connection.incomingUnit = self.unit

        connection2 = copy(self.connection)
        self.assertTrue(self.connection.sameAs(connection2))

        self.connection.incomingUnit = unit2
        self.assertFalse(self.connection.sameAs(connection2))
        
    def testState(self):
        "Test default state of the connection units" 
        self.assertTrue(self.connection.state == 'uniselector') 

        "switching from uniselector to manual and back"
        self.connection.switchToManual()
        self.assertTrue(self.connection.state == 'manual')
        self.connection.switchToUniselector()
        self.assertTrue(self.connection.state == 'uniselector')

        self.connection.switchToManual()
        self.assertTrue(self.connection.state == 'manual')
            
    def testValueOfState(self):
        "Test connections are always in either 'uniselector' or 'manual' state"

        self.assertTrue(self.connection.state == 'manual' or self.connection.state =='uniselector')
            
        self.connection.state = 'manual'
        self.assertTrue(self.connection.state == 'manual' or
                        self.connection.state == 'uniselector')

        self.connection.state = 'uniselector'
        self.assertTrue(self.connection.state == 'manual' or
                        self.connection.state == 'uniselector')

        for testTry in range(10):
            randomString = ''.join(random.choice(string.ascii_lowercase) for x in range(10))
            self.assertRaises(ConnectionError, setattr, self.connection, 'state', randomString)
                
    def testWeight(self):
        """"Test basic algorithm of a connection.
        Output is equal to the originating unit's output * weight * switch - noise 
        We don't test for the influence of noise, as it is a normally distributed value around
        connection.noise and therefore difficult to test reliably. We trust the noise tests carried
        out in HomeNoiseTests 
        
        """
        errorTolerance = pow(10,-7)
        inputUnit = self.connection.incomingUnit
        tests = 100
        
        for i in range(tests):
            self.connection.noise = 0                  # eliminate noise"
            outputWeighed = self.connection.output()
            self.assertTrue(abs(outputWeighed - 
                                ((inputUnit.currentOutput * self.connection.weight * self.connection.switch) - self.connection.noise)) 
                                < errorTolerance)
            inputUnit.selfUpdate()
            
if __name__ == "__main__":
    unittest.main()