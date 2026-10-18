# Copyright (C) 2026 Stefano Franchi
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

'''
The GA's logbook: one run summary, the latest, and
generation 0's statistics whether or not a progress callback is given.
'''
import contextlib
import glob
import io
import os
import pickle
import tempfile
import unittest

from Simulator.HomeoGenAlg import HomeoGASimulation


class GALogbookTest(unittest.TestCase):

    def testOneSummaryAndEveryGeneration(self):
        '''Saves replace the run summary (a run of G generations has one,
        not G+1), and generation 0 is recorded with or without a progress
        callback.'''
        with tempfile.TemporaryDirectory() as tmp:
            root = HomeoGASimulation.dataDirRoot
            HomeoGASimulation.dataDirRoot = tmp
            self.addCleanup(setattr, HomeoGASimulation, 'dataDirRoot', root)
            with contextlib.redirect_stdout(io.StringIO()):
                ga = HomeoGASimulation(postEvalTop=0, stepsSize=20, popSize=4, generSize=3,
                                       exp='initializeBraiten2_direct_GA_continuous_weightfree_fixed_v2',
                                       simulatorBackend='HOMEO')
                ga.runGaSimulation(ga.generateRandomPop(randomSeed=1))
            [path] = glob.glob(os.path.join(ga.dataDir, 'Logbook-*.lgb'))
            with open(path, 'rb') as f:
                saved = pickle.load(f)
        for logbook in (ga.logbook, saved):
            self.assertEqual([r['gen'] for r in logbook if 'gen' in r], [0, 1, 2, 3])
            summaries = [r for r in logbook if 'finalIndivs' in r]
            self.assertEqual(len(summaries), 1)
            self.assertEqual(summaries[0]['finalPop'], 4)
            # how the genes decode (a layout's size does not identify it)
            self.assertEqual(summaries[0]['genomeLayout'], 'weightfree_v2')
            self.assertEqual(summaries[0]['lightIntensity'], 100)    # a light
            # what ran: the code, the simulator and the robot
            from Helpers.General_Helper_Functions import homeo_version
            self.assertEqual((summaries[0]['homeo'], summaries[0]['simulator'],
                              summaries[0]['robot']), (homeo_version(), 'box2d', 'epuck2'))


if __name__ == '__main__':
    unittest.main()
