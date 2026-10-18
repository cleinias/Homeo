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
A run lasts its whole step budget: the report loops run the remainder of
total_steps / report_interval too, and runs shorter than report_interval.
'''
import contextlib
import io
import os
import tempfile
import unittest

from Helpers.General_Helper_Functions import report_ticks


class StepBudgetTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ['HOMEO_DATA_DIR'] = self.tmp.name

    def tearDown(self):
        os.environ.pop('HOMEO_DATA_DIR', None)
        self.tmp.cleanup()

    def testReportTicks(self):
        self.assertEqual(report_ticks(500, 1250), [500, 1000, 1250])
        self.assertEqual(report_ticks(500, 1000), [500, 1000])
        self.assertEqual(report_ticks(500, 100), [100])
        self.assertEqual(report_ticks(500, 0), [])

    def check(self, run, steps):
        with contextlib.redirect_stdout(io.StringIO()):
            r = run(steps)
        hom = r['hom'] if isinstance(r, dict) else r[0]
        backend = r['backend'] if isinstance(r, dict) else r[1]
        backend.kheperaSimulation.saveTrajectory()
        self.assertEqual(hom.time, steps)
        if isinstance(r, dict):
            self.assertEqual(r['steps_run'], steps)

    def testEveryExperimentRunsItsBudget(self):
        import HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_direct as D
        import HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_Ashby as A
        runs = {
            'direct': lambda n: D.run_headless(total_steps=n, quiet=True, seed=1),
            'Ashby': lambda n: A.run_headless(total_steps=n, quiet=True, seed=1),
        }
        for name, run in runs.items():
            for steps in (1250, 100):
                with self.subTest(experiment=name, steps=steps):
                    self.check(run, steps)


if __name__ == '__main__':
    unittest.main()
