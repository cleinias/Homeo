'''
@author: stefano

The phototaxis scripts in the chemotaxis world (--world chemotaxis): the
vehicle's sensors are its chemical eyes, its files are named chemotaxis_...,
and its records give the field (the run's JSON settings, the .traj and
.statelog headers) and the chemical eyes.
'''
import glob
import json
import os
import tempfile
import unittest

from KheperaSimulator.KheperaSimulator import CHEMOTAXIS_FIELD, fieldContourRadius
from HomeoExperiments.KheperaExperiments import phototaxis_common as common
from HomeoExperiments.KheperaExperiments import phototaxis_braitenberg2_direct as direct
from HomeoExperiments.KheperaExperiments import phototaxis_braitenberg2_Ashby as ashby
from HomeoExperiments.KheperaExperiments import hunger_phototaxis as hunger


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

    def testTheWorldOption(self):
        self.assertEqual(common.parse_common_args(['x'])['world'], 'braitenberg2')
        o = common.parse_common_args(['x', '--world', 'chemotaxis', '--field-length', '1'])
        self.assertEqual((o['world'], o['field_length']), ('chemotaxis', 1.0))
        for argv in (['x', '--world', 'sea'], ['x', '--field-length', '1']):
            with self.assertRaises(SystemExit, msg=argv):
                common.parse_common_args(argv)

    def testNames(self):
        self.assertEqual(common.world_experiment('hunger_phototaxis', 'chemotaxis'),
                         'hunger_chemotaxis')
        self.assertEqual(common.world_experiment('phototaxis_braitenberg2_direct'),
                         'phototaxis_braitenberg2_direct')
        self.assertEqual(common.batch_kind('control_crossed_pp', world='chemotaxis'),
                         'control_crossed_pp_chemotaxis')

    def testTheContours(self):
        from KheperaSimulator.KheperaSimulator import _fieldShape
        for fraction in (0.5, 0.1, 0.01):
            r = fieldContourRadius(CHEMOTAXIS_FIELD, fraction)
            self.assertAlmostEqual(_fieldShape(CHEMOTAXIS_FIELD, r), fraction, places=9)
        self.assertIsNone(fieldContourRadius({'law': 'cone', 'radius': 500.0}, 0.01))


class ChemotaxisRunTest(_DataDirTest):

    def testADirectVehicleSteersByItsChemicalEyes(self):
        hom, backend, _ = direct.setup_phototaxis(fixed_weights=True, world='chemotaxis', seed=1)
        self.addCleanup(backend.kheperaSimulation.saveTrajectory)
        units = {u.name: u for u in hom.homeoUnits}
        self.assertEqual(units['Left Sensor'].transducer._eye, 'leftOrgEye')
        self.assertEqual(units['Left Sensor'].transducer._quality, 'organic')

    def testTheAshbyVehicleToo(self):
        hom, backend, _ = ashby.setup_phototaxis(world='chemotaxis', seed=1)
        self.addCleanup(backend.kheperaSimulation.saveTrajectory)
        self.assertIn('rightOrgEye', [getattr(u.transducer, '_eye', None) for u in hom.homeoUnits
                                      if hasattr(u, 'transducer')])

    def testTheRunsRecords(self):
        r = direct.run_headless(fixed_weights=True, world='chemotaxis', total_steps=200,
                                quiet=True, seed=1, state_log=True)
        self.assertTrue(os.path.basename(r['json_path']).startswith(
            'chemotaxis_braitenberg2_direct_control_crossed_pp'))
        self.assertTrue(r['start_sees_light'])          # the field reaches everywhere
        with open(r['json_path']) as f:
            settings = json.load(f)['settings']
        self.assertEqual(settings['world'], 'chemotaxis')
        self.assertEqual(settings['fields'], {'FOOD': CHEMOTAXIS_FIELD})
        self.assertEqual(settings['eye_response'], 'log')
        [traj] = self.files('chemotaxis_*.traj')
        with open(traj) as f:
            header = f.read().splitlines()
        self.assertIn('# Field\tFOOD\tlaw\tk0\tlength\t2.0\tradius\t0.06', header)
        [org] = [l for l in header if l.startswith('# Eye\tleftOrgEye\t')]
        self.assertTrue(org.endswith('\tresponse\tlog\tdirection-free'))
        with open(r['state_log_path']) as f:
            lines = f.read().splitlines()
        self.assertIn('# field_FOOD\tlaw=k0,length=2.0,radius=0.06', lines)
        columns = [l for l in lines if not l.startswith('#')][0].split('\t')
        first = dict(zip(columns, lines[[i for i, l in enumerate(lines)
                                         if not l.startswith('#')][1]].split('\t')))
        self.assertGreater(float(first['left_sensor']), 0)

    def testAnotherFieldLength(self):
        r = direct.run_headless(fixed_weights=True, world='chemotaxis', field_length=1.0,
                                total_steps=50, quiet=True, seed=1)
        self.assertIn('_len1', os.path.basename(r['json_path']))
        with open(r['json_path']) as f:
            self.assertEqual(json.load(f)['settings']['fields']['FOOD']['length'], 1.0)

    def testTheEyeSaturationIsADistanceInTheField(self):
        from KheperaSimulator.KheperaSimulator import KheperaRobot
        hom, backend, _ = direct.setup_phototaxis(fixed_weights=True, world='chemotaxis', seed=1,
                                                  eye_saturation=0.5)
        sim = backend.kheperaSimulation
        self.addCleanup(sim.saveTrajectory)
        _, saturation, response = sim.allBodies['Khepera'].eyeSettings()['rightOrgEye']
        self.assertAlmostEqual(saturation, KheperaRobot.sourceValue(sim.allBodies['FOOD'], 0.5))
        self.assertEqual(response, 'log')

    def testHungerChemotaxis(self):
        hunger.main(['hunger_phototaxis', '--fixed-weights', '--world', 'chemotaxis',
                     '--steps', '100'])
        [path] = self.files('hunger_chemotaxis_control_crossed_pp_death-*.json')
        with open(path) as f:
            settings = json.load(f)['settings']
        self.assertEqual(settings['food_quality'], 'organic')


if __name__ == '__main__':
    unittest.main()
