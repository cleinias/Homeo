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

from PyQt5.QtWidgets import QSpinBox, QDoubleSpinBox
from PyQt5.QtCore import pyqtSignal
import sys

class SFSpinBox(QSpinBox):
    '''
    A custom QSpinBox that adds a custom signal to send its value
    only when editing is finished
    '''
    editingValueFinished = pyqtSignal(int)       # emitted by the modified spinbox

    def __init__(self, parent = None):
        super(SFSpinBox, self).__init__(parent)
        self.editingFinished.connect( self.__handleEditingFinished)
        self.valueChanged.connect(self.__handleValueChanged)
        self.__before = 0

    def setValue(self, val):
        super(SFSpinBox, self).setValue(int(val))
        
    def __handleValueChanged(self, aValue):
        if not self.hasFocus():
            self.__before = aValue

    
    def __handleEditingFinished(self):
        before, after = self.__before, self.value()
        if before != after:
            self.__before = after
            sys.stderr.write("A SFDoubleWidget is about to emit a signal editingValueFinished with value: %f\n" % after)           
            self.editingValueFinished.emit(after)
        
        
class SFDoubleSpinBox(QDoubleSpinBox):
    '''
    A custom QDoubleSpinBox that adds a custom signal to send its value
    only when editing is finished
    '''
    editingValueFinished = pyqtSignal(float) # emitted by the modified doublespinbox

    def __init__(self, parent = None):
        super(SFDoubleSpinBox, self).__init__(parent)
        self.editingFinished.connect( self.__handleEditingFinished)
        self.valueChanged.connect(self.__handleValueChanged)
        self.__before = 0

    def setValue(self, val):
        super(SFDoubleSpinBox, self).setValue(float(val))
    
    def __handleValueChanged(self, aValue):
        if not self.hasFocus():
            self.__before = aValue
                    
    def __handleEditingFinished(self):
        
        before, after = self.__before, self.value()
        if before != after:
            self.__before = after
            sys.stderr.write("A SFDoubleWidget is about to emit a signal editingValueFinished with value: %f\n" % after)           
            self.editingValueFinished.emit(after)
        
        
#
#class SFLineEdit(QLineEdit):
#    '''
#    Modified LineEdit Widget that emits a textModified signal passing the new text
#    only after the editing has finished. Basically, it combines 
#    the  editingFinished and textEdited signals of QLineEdit'''
#     
#    textModified = pyqtSignal(str) # (after)
#
#    def __init__(self,  parent=None):
#        super(SFLineEdit, self).__init__(parent)
#        self.editingFinished.connect(self.__handleEditingFinished)
#        self.textChanged.connect(self.__handleTextChanged)
#        self._before = ''
#
#    def __handleTextChanged(self, text):
#        if not self.hasFocus():
#            self._before = text
#
#    def __handleEditingFinished(self):
#        before, after = self._before, self.text()
#        if before != after:
#            self._before = after
#            self.textModified.emit(after)        