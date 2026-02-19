from PyQt5.QtCore import *
from PyQt5.QtWidgets import *; from PyQt5.QtGui import *


class Dialog(QDialog):
    def __init__(self, parent = None):
        super(Dialog, self).__init__(parent)
        self.otherDialog = QDialog(parent=self)

        self.otherDialog.show()


if __name__ == "__main__":
    app = QApplication([])
    dialog = Dialog()
    dialog.show()
    app.exec_()
    
