from PyQt4.QtGui import QLineEdit
from PyQt4.QtCore import pyqtSignal

class SFLineEdit(QLineEdit):
    '''
    Modified LineEdit Widget that emits a textModified signal passing the new text
    only after the editing has finished. Basically, it combines 
    the  editingFinished and textEdited signale of QLineEdit'''
     
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