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


if __name__ == '__main__':
    unittest.main()
