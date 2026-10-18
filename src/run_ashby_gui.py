#!/usr/bin/env python3
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

'''Launch the interactive Ashby experiment GUI.

Usage:
    python run_ashby_gui.py             # show experiment selector
    python run_ashby_gui.py --exp 2     # jump directly to experiment 2
    python run_ashby_gui.py --exp 3 --seed 2   # the homeostat of seed 2

The panel shows the seed of the homeostat; the headless setup_expN(seed=...)
of Simulator.AshbyOriginalExperiments builds the same one.
'''

import argparse
import sys
import os

# Ensure src/ is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from Simulator.AshbyExperimentGui import AshbyExperimentGui


def main():
    parser = argparse.ArgumentParser(
        description="Interactive GUI for Ashby's 7 original Homeostat experiments")
    parser.add_argument('--exp', type=int, default=None, choices=range(1, 8),
                        help='Experiment number (1-7). If omitted, shows selector.')
    parser.add_argument('--seed', type=int, default=None,
                        help='Seed of the homeostat (default: drawn, and shown)')
    args = parser.parse_args()

    app = QApplication(sys.argv)
    gui = AshbyExperimentGui(exp_num=args.exp, seed=args.seed)
    gui.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
