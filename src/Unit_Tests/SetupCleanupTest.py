'''
@author: stefano

The experiment setups' corner cases: the agent-environment setups built
twice and their environment's mass, and the GA setups without a backend.
'''
import unittest

import Simulator.HomeoExperiments as HomeoExperiments


class LegacySetupsTwiceTest(unittest.TestCase):
    '''The two agent-environment setups give their units fixed names: a
    second call while the first homeostat is alive (the GUI's New) builds
    again, without "The name ... exists already".'''

    def testEachCanBeBuiltAgain(self):
        for name, units in (('initialize_1minus_2xExperiment',
                             ['H1_Agent', 'H1_Env', 'H2_Agent', 'H2_Env']),
                            ('initialize_1minus_2_minus_3xExperiment',
                             ['1_Agent', '2_Agent', 'Env', 'UNUSED'])):
            setup = getattr(HomeoExperiments, name)
            first = setup()
            second = setup()
            self.assertEqual([u.name for u in first.homeoUnits], units, name)
            self.assertEqual([u.name for u in second.homeoUnits], units, name)


class LegacyEnvironmentMassTest(unittest.TestCase):
    '''The environment units get env_mass (100), which is also the default
    mass: with another default the setups must still give env_mass.'''

    def testTheEnvironmentHasItsMass(self):
        from unittest import mock
        from Core.HomeoUnit import HomeoUnit
        with mock.patch.dict(HomeoUnit.DefaultParameters, {'mass': 7}):
            for name, envs in (('initialize_1minus_2xExperiment', ['H1_Env', 'H2_Env']),
                               ('initialize_1minus_2_minus_3xExperiment', ['Env'])):
                hom = getattr(HomeoExperiments, name)()
                masses = {u.name: u.mass for u in hom.homeoUnits}
                for env in envs:
                    self.assertEqual(masses[env], 100, (name, env))


class SetupsWithoutABackendTest(unittest.TestCase):
    '''The GA setups called without a backend, or with one they cannot use,
    say what is missing.'''

    def testEachGASetupAsksForABackend(self):
        import numpy as np
        names = ['initializeBraiten2_2_Full_GA'] + [
            n for n in dir(HomeoExperiments)
            if n.startswith('initialize') and hasattr(getattr(HomeoExperiments, n), 'genomeSize')]
        self.assertEqual(len(names), 7)                 # the classic setup and the six _v2 ones
        for name in names:
            setup = getattr(HomeoExperiments, name)
            genome = np.full(getattr(setup, 'genomeSize', 40), 0.5)
            with self.assertRaisesRegex(ValueError, 'needs a backendSimulator', msg=name):
                setup(genome, backendSimulator=None)

    def testAnUnknownBackendIsRefused(self):
        class Other(object):
            name = 'VREP'
        with self.assertRaisesRegex(Exception, 'cannot use backend simulator VREP'):
            HomeoExperiments.initializeBraiten2_2_Full_GA([0.5] * 40, backendSimulator=Other())


if __name__ == '__main__':
    unittest.main()
