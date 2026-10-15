'''
Created on Oct 14, 2026

@author: stefano

The experiment setups' small defects (review findings SE-06, SE-10, SE-11,
SE-13; Phase H of the 7 Oct 2026 review plan).
'''
import unittest

import Simulator.HomeoExperiments as HomeoExperiments


class LegacySetupsTwiceTest(unittest.TestCase):
    '''SE-10: the two legacy agent-environment setups give their units fixed
    names, and a second call while the first homeostat was alive (the GUI's
    New) raised "The name ... exists already".'''

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


class SetupsWithoutABackendTest(unittest.TestCase):
    '''SE-06: the GA setups called without a backend failed with an
    AttributeError raised from inside a bare except; they say what is
    missing.'''

    def testEachGASetupAsksForABackend(self):
        import numpy as np
        names = ['initializeBraiten2_2_Full_GA'] + [
            n for n in dir(HomeoExperiments)
            if n.startswith('initialize') and hasattr(getattr(HomeoExperiments, n), 'genomeSize')]
        self.assertGreater(len(names), 8)
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
