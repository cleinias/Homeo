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

from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtCore import pyqtSignal

class SFLineEdit(QLineEdit):
    '''
    Modified LineEdit Widget that emits a textModified signal passing the new text
    only after the editing has finished. Basically, it combines 
    the  editingFinished and textEdited signals of QLineEdit'''
     
    textModified = pyqtSignal(str) # (after)

    def __init__(self,  parent=None):
        super(SFLineEdit, self).__init__(parent)
        self.editingFinished.connect(self.__handleEditingFinished)
        self.textChanged.connect(self.__handleTextChanged)
        self._before = ''

    def __handleTextChanged(self, text):
        if not self.hasFocus():
            self._before = text

    def __handleEditingFinished(self):
        before, after = self._before, self.text()
        if before != after:
            self._before = after
            self.textModified.emit(after)