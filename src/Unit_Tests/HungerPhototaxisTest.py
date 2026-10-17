'''
@author: stefano

The hunger_phototaxis experiment: its options, its files, and its runs --
a vehicle with a battery that dies when the battery empties, and one that
feeds at the light.
'''
import glob
import os
import tempfile
import unittest

from HomeoExperiments.KheperaExperiments import hunger_phototaxis as hunger
from HomeoExperiments.KheperaExperiments import phototaxis_braitenberg2_direct as direct
from HomeoExperiments.KheperaExperiments import phototaxis_common as common


class _DataDirTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        saved = os.environ.get('HOMEO_DATA_DIR')
        os.environ['HOMEO_DATA_DIR'] = self.tmp.name
        self.addCleanup(lambda: os.environ.__setitem__('HOMEO_DATA_DIR', saved)
                        if saved is not None else os.environ.pop('HOMEO_DATA_DIR', None))

    def files(self, pattern):
        return glob.glob(os.path.join(self.tmp.name, '*', pattern))


class OptionsTest(unittest.TestCase):

    def testTheDefaults(self):
        self.assertEqual(hunger.parse_battery(['x']),
                         dict(depletion='death', signal='hunger', hunger_unit=False,
                              to_motors=True))

    def testEveryOption(self):
        argv = ['x', '--depletion', 'graded', '--capacity', '2', '--discharge', '0.001',
                '--recharge', '1e-5', '--food-saturation', '50', '--critical-level', '0.2',
                '--min-efficiency', '0', '--battery-signal', 'level', '--hunger-unit',
                '--hunger-inputs', 'all', '--battery-recorded']
        common.check_options(argv, hunger.BATTERY_FLAGS, hunger.BATTERY_VALUED)
        self.assertEqual(hunger.parse_battery(argv, {'stress_source': 'battery'}),
                         dict(depletion='graded', signal='level', hunger_unit=True,
                              to_motors=False, capacity=2.0, discharge_rate=0.001,
                              recharge_factor=1e-5, saturation=50.0, critical_level=0.2,
                              min_efficiency=0.0, hunger_inputs='all', stress_source='battery'))

    def testBadOptions(self):
        for argv in (['x', '--depletion', 'coma'], ['x', '--battery-signal', 'mood'],
                     ['x', '--hunger-inputs', 'all'], ['x', '--discharge', 'fast']):
            with self.assertRaises(SystemExit, msg=argv):
                hunger.parse_battery(argv)

    def testTheStressSourceNeedsTheContinuousUniselector(self):
        with self.assertRaises(SystemExit):
            common.parse_common_args(['x', '--stress-source', 'battery'])
        o = common.parse_common_args(['x', '--continuous', '--stress-source', 'battery'])
        self.assertEqual(o['continuous_params'], {'stress_source': 'battery'})


class HungerRunTest(_DataDirTest):

    def testARobotFarFromTheLightStarves(self):
        '''Started 4.2 from the light and facing away, the fixed-weight
        vehicle never feeds: with depletion death it dies when its battery
        empties (1 / 0.01 = 100 ticks, less the little food 4.2 away), and
        the run ends there.'''
        r = direct.run_headless(fixed_weights=True, total_steps=1000, report_interval=50,
                                quiet=True, heading=225, seed=1, experiment=hunger.EXPERIMENT,
                                battery=hunger.parse_battery(['x', '--discharge', '0.01']))
        self.assertFalse(r['alive'])
        self.assertTrue(95 <= r['death_tick'] <= 110, r['death_tick'])
        self.assertEqual(r['steps_run'], r['death_tick'])
        self.assertTrue(os.path.basename(r['json_path']).startswith(
            'hunger_phototaxis_control_crossed_pp_death'))

    def testAVehicleThatReachesTheLightFeeds(self):
        '''The fixed-weight crossed ++ vehicle started 1.4 from the light and
        facing it reaches it and stays alive, its battery full again at the
        light.'''
        def setup():
            hom, backend, seed = direct.setup_phototaxis(
                fixed_weights=True, seed=1, experiment=hunger.EXPERIMENT,
                battery=hunger.parse_battery(['x', '--battery-recorded', '--discharge', '1e-3']))
            common.set_start_pose(backend.kheperaSimulation.allBodies['Khepera'], 6, 6, 45)
            return hom, backend, seed
        r = common.run_headless(setup, 'hunger', total_steps=4000, report_interval=500,
                                quiet=True)
        self.assertTrue(r['acquired'])
        self.assertTrue(r['alive'])
        self.assertLess(r['battery_min'], 1.0)
        self.assertAlmostEqual(r['battery_final'], 1.0)

    def testTheScriptsBatch(self):
        hunger.main(['hunger_phototaxis', '--continuous', '--stress-source', 'battery',
                     '--hunger-unit', '--steps', '50', '--batch', '2', '--seed', '3',
                     '--random-start'])
        [batch] = self.files('batch_hunger_continuous_stbattery_death_hungerunit_stbattery_*.csv')
        self.assertTrue(self.files('hunger_phototaxis_fixed_continuous_stbattery_death_hungerunit_*.json'))


if __name__ == '__main__':
    unittest.main()
