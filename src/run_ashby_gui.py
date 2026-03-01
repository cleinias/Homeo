#!/usr/bin/env python3
'''Launch the interactive Ashby experiment GUI.

Usage:
    python run_ashby_gui.py             # show experiment selector
    python run_ashby_gui.py --exp 2     # jump directly to experiment 2
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
    args = parser.parse_args()

    app = QApplication(sys.argv)
    gui = AshbyExperimentGui(exp_num=args.exp)
    gui.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
