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
StatelogAnalyzer's drift/diffusion split: on a noise-free weight trajectory
the diffusion residual is zero.  The drift uses the uniselector's own dt,
not the unit's dt_fast, spans the log_interval ticks between two records,
is evaluated at the earlier record's weight, and follows the formula of the
model the statelog records ('ou', or the theta model, 'legacy').
'''
import os
import tempfile
import unittest

import numpy as np

from Helpers import StatelogAnalyzer as SLA


def _write_statelog(path, model, w, ticks, tau_a=100.0, theta=0.5, ou_dt=1.0, dt_fast=0.2):
    with open(path, 'w') as f:
        f.write('# HomeostatStateLog v1\n')
        f.write('# log_interval\t%d\n' % (ticks[1] - ticks[0]))
        for name in ('Left Motor', 'Right Motor'):
            prefix = '# unit_%s' % name
            f.write('%s_dt_fast\t%f\n' % (prefix, dt_fast))
            if model is not None:
                f.write('%s_ou_model\t%s\n' % (prefix, model))
            f.write('%s_tau_a\t%f\n%s_theta\t%f\n%s_ou_dt\t%f\n'
                    % (prefix, tau_a, prefix, theta, prefix, ou_dt))
        f.write('tick\tw_Left Motor<-Right Motor\n')
        for t, v in zip(ticks, w):
            f.write('%d\t%.15f\n' % (t, v))


class DriftDiffusionTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def residual(self, model, k, interval, ou_dt=1.0):
        "Median |diffusion|/|drift| on the noise-free trajectory w_n = 0.8 (1 - k ou_dt)^n."
        ticks = np.arange(0, 2000, interval)
        w = 0.8 * (1.0 - k * ou_dt) ** ticks
        path = os.path.join(self.tmp.name, 'run.statelog')
        _write_statelog(path, model, w, ticks, ou_dt=ou_dt)
        data = SLA.parse_statelog(path)
        SLA.enrich(data)
        col = 'w_Left Motor<-Right Motor'
        df = data.df.iloc[1:]
        return (df['diffusion_' + col].abs() / df['drift_' + col].abs()).median()

    def testNoiseFreeTrajectoriesHaveNoDiffusion(self):
        for model, k in (('legacy', 0.5 / 100), ('ou', 1 / 100), (None, 0.5 / 100)):
            for interval in (1, 100):
                with self.subTest(model=model, interval=interval):
                    self.assertLess(self.residual(model, k, interval), 1e-6)
        with self.subTest('ou_dt'):
            self.assertLess(self.residual('ou', 1 / 100, 10, ou_dt=0.5), 1e-6)

    def testTheDiffusionModelHasNoDrift(self):
        self.assertEqual(SLA.ou_drift_rate({'ou_model': 'diffusion', 'tau_a': 100.0}), 0.0)
        self.assertIsNone(SLA.ou_drift_rate({'dt_fast': 1.0}))


if __name__ == '__main__':
    unittest.main()
