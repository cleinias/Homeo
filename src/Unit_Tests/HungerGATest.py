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
The hunger GA setups and the fitness a setup names: the GA minimises the
setup's fitness measure (final distance by default; minus the battery's
mean level, or minus the fraction of the run survived, for the hunger
setups), the logbook records it, and the replay recomputes it.
'''
import contextlib
import io
import tempfile
import threading
import unittest

import numpy as np

import Simulator.HomeoExperiments as HE
from Simulator import HomeoGenAlg
from Simulator.HomeoGenAlg import (HomeoGASimulation, fitness_measure, measured_fitness,
                                   evaluate_genome, FITNESS_MEASURES)
from Simulator.SimulatorBackend import SimulatorBackendHOMEO

HUNGER_SETUPS = ('initializeHungerPhototaxis_GA_continuous_weightfree_fixed_v2',
                 'initializeHunger3c_GA_continuous_weightfree_fixed_v2',
                 'initializeHungerChemotaxis_GA_continuous_weightfree_fixed_v2')


class Genome(list):
    def __init__(self, genes, ID='000-001'):
        super().__init__(genes)
        self.ID = ID


class HungerSetupsTest(unittest.TestCase):

    def backend(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        backend = SimulatorBackendHOMEO(lock=threading.Lock(), robotName='Khepera')
        backend.kheperaSimulation.dataDir = tmp.name
        self.addCleanup(backend.quit)
        return backend

    def testTheSetupsHaveABatteryThatDies(self):
        for name, quality in zip(HUNGER_SETUPS, ('light', 'organic', 'organic')):
            with self.subTest(name):
                f = getattr(HE, name)
                backend = self.backend()
                hom = f(np.full(f.genomeSize, 0.5), backendSimulator=backend)
                robot = backend.kheperaSimulation.allBodies['Khepera']
                self.assertEqual(robot.battery.depletion, 'death')
                self.assertEqual(robot.foodQuality, quality)
                self.assertEqual(len(hom.homeoUnits), f.noUnits)
                self.assertIn('Battery', [u.name for u in hom.homeoUnits])
                self.assertEqual(f.fitness, 'battery_mean')
                self.assertEqual(fitness_measure(name), 'battery_mean')

    def testTheChemotaxisSetupSteersByTheChemicalEyes(self):
        name = HUNGER_SETUPS[2]
        f = getattr(HE, name)
        backend = self.backend()
        hom = f(np.full(f.genomeSize, 0.5), backendSimulator=backend)
        sim = backend.kheperaSimulation
        self.assertIs(sim.allBodies['TARGET'], sim.allBodies['FOOD'])
        sensors = {u.name: u for u in hom.homeoUnits}
        self.assertEqual(sensors['Left Sensor'].transducer._eye, 'leftOrgEye')
        self.assertEqual(sensors['Right Sensor'].transducer._quality, 'organic')

    def testTheDefaultMeasureIsTheFinalDistance(self):
        self.assertEqual(fitness_measure('initializeBraiten2_direct_GA_continuous_weightfree_fixed_v2'),
                         'final_distance')

    def testTheMeasures(self):
        from KheperaSimulator.Battery import Battery
        backend = self.backend()
        backend.start('kheperaBraitenberg2_HOMEO_World')
        robot = backend.kheperaSimulation.allBodies['Khepera']
        with self.assertRaises(ValueError):
            measured_fitness(backend, 'battery_mean', 10)
        robot.battery = Battery(discharge_rate=0.25, recharge_factor=0.0, depletion='death')
        for _ in range(10):
            robot.battery.tick()
        # levels 0.75, 0.5, 0.25, 0 (dead at tick 4): mean over 10 ticks 0.15
        self.assertAlmostEqual(measured_fitness(backend, 'battery_mean', 10), -0.15)
        self.assertAlmostEqual(measured_fitness(backend, 'survival', 10), -0.4)
        self.assertAlmostEqual(measured_fitness(backend, 'final_distance', 10),
                               backend.finalDisFromTarget())
        backend.kheperaSimulation.saveTrajectory()

    def testAnEvaluationIsTheBatterysMean(self):
        name = HUNGER_SETUPS[0]
        f = getattr(HE, name)
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            (fitness,) = evaluate_genome(Genome(np.full(f.genomeSize, 0.5)), name,
                                         {'dataDir': tmp}, 20, tmp)
        # 20 ticks far from the light: the battery barely drains
        self.assertTrue(-1.0 <= fitness < -0.99, fitness)

    def testTheLogbookRecordsTheMeasure(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = HomeoGASimulation.dataDirRoot
        HomeoGASimulation.dataDirRoot = tmp.name
        self.addCleanup(setattr, HomeoGASimulation, 'dataDirRoot', root)
        with contextlib.redirect_stdout(io.StringIO()):
            ga = HomeoGASimulation(postEvalTop=0, stepsSize=5, popSize=2, exp=HUNGER_SETUPS[0],
                                   simulatorBackend=None)
        self.assertEqual(ga.fitnessMeasure, 'battery_mean')
        self.assertEqual(ga.noUnits, 5)
        self.assertIn('battery_mean', FITNESS_MEASURES)

    def testTheReplayKnowsTheHungerSetups(self):
        import replay_best_with_statelog as replay
        for name in HUNGER_SETUPS:
            self.assertEqual(replay._EXP_FUNC_MAP[name], name)


if __name__ == '__main__':
    unittest.main()
