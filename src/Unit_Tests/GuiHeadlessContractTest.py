'''
Created on Oct 14, 2026

@author: stefano

An Ashby experiment runs the same in the GUI's simulation loop as in the
headless runner (review finding SR-06): the experiment's per-tick callbacks
run before each tick's update, with the time about to run, and the record
keepers after it.  Until 14 Oct 2026 the GUI called its callbacks after the
update, one tick later than run_with_events.
'''
import os
import tempfile
import unittest

from Simulator import AshbyOriginalExperiments as AOE
from Simulator.HomeoQtSimulation import HomeoQtSimulation


class GuiHeadlessContractTest(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        os.environ['HOMEO_DATA_DIR'] = tmp.name
        self.addCleanup(os.environ.pop, 'HOMEO_DATA_DIR', None)

    def guiRun(self, hom, ticks, callbacks, observers=()):
        sim = HomeoQtSimulation()
        sim.homeostat = hom
        hom.slowingFactor = 0
        sim.setSimulDelay(0)
        sim.maxRuns = ticks
        sim.tick_callbacks = list(callbacks)
        sim.tick_observers = list(observers)
        sim.go()
        return hom

    def testTheTrainerPunishesOnTheSameTicks(self):
        ticks = 8000                    # seed 2: punished in tests 1, 2 and 4
        hom, _, _ = AOE.setup_exp3_training(seed=2)
        trainer, headless_log = AOE.make_trainer_callback()
        AOE.run_with_events(hom, ticks, tick_callback=trainer)
        headless = [u.criticalDeviation for u in hom.homeoUnits]

        hom, _, _ = AOE.setup_exp3_training(seed=2)
        trainer, gui_log = AOE.make_trainer_callback()
        self.guiRun(hom, ticks, [trainer])
        self.assertTrue(headless_log)
        self.assertEqual(gui_log, headless_log)
        self.assertEqual([u.criticalDeviation for u in hom.homeoUnits], headless)

    def testCallbacksBeforeObserversAfter(self):
        hom, _, _ = AOE.setup_exp1_basic_ultrastability(seed=1)
        seen = []
        before = lambda h, t: seen.append(('before', t, h.time))
        after = lambda h, t: seen.append(('after', t, h.time))
        self.guiRun(hom, 2, [before], [after])
        self.assertEqual(seen, [('before', 0, 0), ('after', 1, 1),
                                ('before', 1, 1), ('after', 2, 2)])


if __name__ == '__main__':
    unittest.main()
