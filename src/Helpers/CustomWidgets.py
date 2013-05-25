
from PyQt4.QtGui import QSpinBox, QDoubleSpinBox
from PyQt4.QtCore import SIGNAL, pyqtSignal
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