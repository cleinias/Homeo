'''
@author: stefano

The hunger layer of the experiment setups (add_battery_to_homeostat): the
battery it gives the robot, the Battery unit that senses it, and the
optional Hunger unit between the Battery unit and the motors.
'''
import unittest

from KheperaSimulator.Battery import BREAK_EVEN_DISTANCE
from Core.HomeoUniselectorContinuous import HomeoUniselectorContinuous
from HomeoExperiments.KheperaExperiments import phototaxis_braitenberg2_direct as direct
from HomeoExperiments.KheperaExperiments.phototaxis_common import set_start_pose
from Simulator.HomeoExperiments import add_battery_to_homeostat, FOOD_SOURCE_RADIUS


def connection(unit, source):
    return [c for c in unit.inputConnections if c.incomingUnit.name == source][0]


class HungerSetupTest(unittest.TestCase):

    def vehicle(self, uniselector_type='continuous', **kwargs):
        hom, backend, _ = direct.setup_phototaxis(uniselector_type=uniselector_type, seed=1)
        self.addCleanup(backend.kheperaSimulation.saveTrajectory)
        battery_unit = add_battery_to_homeostat(hom, backend, **kwargs)
        return hom, backend, battery_unit, {u.name: u for u in hom.homeoUnits}

    def testTheBatteryUnitSensesHunger(self):
        hom, backend, unit, _ = self.vehicle()
        battery = backend.kheperaSimulation.allBodies['Khepera'].battery
        self.assertEqual(unit.transducer.read(), 0.0)          # full: not hungry
        battery.level = 0.25
        self.assertEqual(unit.transducer.read(), 0.75)
        self.assertEqual(unit.transducer.range(), (0.0, 1.0))
        hom2, backend2, unit2, _ = self.vehicle(signal='level')
        self.assertEqual(unit2.transducer.read(), 1.0)

    def testTheBatteryFeedsTheMotorsThroughSmallAdaptiveWeights(self):
        _, _, battery, units = self.vehicle()
        self.assertFalse(battery.uniselectorActive)
        self.assertFalse(any(c.status for c in battery.inputConnections))
        for name, unit in units.items():
            conn = connection(unit, 'Battery') if name != 'Battery' else None
            if name.endswith('Motor'):
                self.assertTrue(conn.status)
                self.assertLess(abs(conn.weight), 0.1)
                self.assertEqual(conn.state, 'uniselector')
            elif conn is not None:
                self.assertFalse(conn.status, name)

    def testAFixedWeightVehiclesBatteryWeightsAreFixed(self):
        hom, backend, _ = direct.setup_phototaxis(fixed_weights=True, seed=1)
        self.addCleanup(backend.kheperaSimulation.saveTrajectory)
        add_battery_to_homeostat(hom, backend)
        units = {u.name: u for u in hom.homeoUnits}
        self.assertEqual(connection(units['Left Motor'], 'Battery').state, 'manual')

    def testARecordedOnlyBattery(self):
        _, _, _, units = self.vehicle(to_motors=False)
        self.assertFalse(connection(units['Left Motor'], 'Battery').status)
        self.assertFalse(connection(units['Right Motor'], 'Battery').status)

    def testDefaultRechargeBreaksEvenAtOneUnitFromTheLight(self):
        _, backend, _, _ = self.vehicle()
        sim = backend.kheperaSimulation
        robot, battery = sim.allBodies['Khepera'], sim.allBodies['Khepera'].battery
        self.assertAlmostEqual(battery.recharge_factor * 100 / BREAK_EVEN_DISTANCE ** 2,
                               battery.discharge_rate)
        self.assertAlmostEqual(battery.saturation, 100 / FOOD_SOURCE_RADIUS ** 2)
        battery.level = 0.5
        set_start_pose(robot, 7 - BREAK_EVEN_DISTANCE, 7, 0)
        sim.tickAdvance()
        self.assertAlmostEqual(battery.level, 0.5, places=9)
        set_start_pose(robot, 7 - 0.5, 7, 0)                    # closer: it gains
        sim.tickAdvance()
        self.assertGreater(battery.level, 0.5)

    def testBatteryParametersReachTheBattery(self):
        _, backend, _, _ = self.vehicle(capacity=2.0, discharge_rate=1e-3, recharge_factor=1e-5,
                                        saturation=50, critical_level=0.2, depletion='death',
                                        min_efficiency=0.0)
        b = backend.kheperaSimulation.allBodies['Khepera'].battery
        self.assertEqual((b.capacity, b.discharge_rate, b.recharge_factor, b.saturation,
                          b.critical_level, b.depletion, b.min_efficiency),
                         (2.0, 1e-3, 1e-5, 50.0, 0.2, 'death', 0.0))

    def testNoFoodSourceIsAnError(self):
        with self.assertRaises(ValueError):
            self.vehicle(food_quality='organic')

    def testTheHungerUnitStandsBetweenTheBatteryAndTheMotors(self):
        _, _, _, units = self.vehicle(hunger_unit=True)
        hunger = units['Hunger']
        self.assertTrue(hunger.uniselectorActive)
        self.assertIsInstance(hunger.uniselector, HomeoUniselectorContinuous)
        active = {c.incomingUnit.name for c in hunger.inputConnections if c.status}
        self.assertEqual(active, {'Hunger', 'Battery'})
        self.assertEqual(connection(hunger, 'Battery').state, 'uniselector')
        self.assertEqual(connection(hunger, 'Hunger').state, 'manual')
        self.assertLess(connection(hunger, 'Hunger').weight * connection(hunger, 'Hunger').switch, 0)
        for name in ('Left Motor', 'Right Motor'):
            self.assertTrue(connection(units[name], 'Hunger').status)
            self.assertFalse(connection(units[name], 'Battery').status)
        for name in ('Left Sensor', 'Right Sensor'):
            self.assertFalse(connection(units[name], 'Hunger').status)

    def testAHungerUnitWithEveryInput(self):
        _, _, _, units = self.vehicle(hunger_unit=True, hunger_inputs='all')
        active = {c.incomingUnit.name for c in units['Hunger'].inputConnections if c.status}
        self.assertEqual(active, set(units))

    def testAnAshbyVehiclesHungerUnitHasAshbysUniselector(self):
        _, _, _, units = self.vehicle(uniselector_type='ashby', hunger_unit=True)
        self.assertNotIsInstance(units['Hunger'].uniselector, HomeoUniselectorContinuous)


if __name__ == '__main__':
    unittest.main()
