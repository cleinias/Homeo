# Copyright (C) 2013-2026 Stefano Franchi
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

from PyQt5.QtCore import QThread

class SimulationThread(QThread):
    
    def __init__(self):
        super(SimulationThread,self).__init__()
        self.exiting = False
 
    def __del__(self):
        self.exiting = True
        try:
            self.exit()
        except RuntimeError:
            pass
    
    def run(self):
        self.exec_()
        
