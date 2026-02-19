# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '../Simulator/UI_Files/SliderTest_UI.ui'
#
# Created: Wed May 15 20:27:32 2013
#      by: PyQt4 UI code generator 4.9.6 (ported to PyQt5)
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

def _fromUtf8(s):
    return s

def _translate(context, text, disambig):
    return QtCore.QCoreApplication.translate(context, text, disambig)

class Ui_SliderTestUI(object):
    def setupUi(self, SliderTestUI):
        SliderTestUI.setObjectName(_fromUtf8("SliderTestUI"))
        SliderTestUI.resize(400, 300)
        self.verticalSlider = QtWidgets.QSlider(SliderTestUI)
        self.verticalSlider.setGeometry(QtCore.QRect(350, 50, 16, 160))
        self.verticalSlider.setOrientation(QtCore.Qt.Vertical)
        self.verticalSlider.setObjectName(_fromUtf8("verticalSlider"))
        self.verticalSlider_2 = QtWidgets.QSlider(SliderTestUI)
        self.verticalSlider_2.setGeometry(QtCore.QRect(40, 50, 16, 160))
        self.verticalSlider_2.setOrientation(QtCore.Qt.Vertical)
        self.verticalSlider_2.setObjectName(_fromUtf8("verticalSlider_2"))
        self.lineEdit = QtWidgets.QLineEdit(SliderTestUI)
        self.lineEdit.setGeometry(QtCore.QRect(130, 110, 113, 23))
        self.lineEdit.setObjectName(_fromUtf8("lineEdit"))

        self.retranslateUi(SliderTestUI)
        QtCore.QMetaObject.connectSlotsByName(SliderTestUI)

    def retranslateUi(self, SliderTestUI):
        SliderTestUI.setWindowTitle(_translate("SliderTestUI", "Dialog", None))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    SliderTestUI = QtWidgets.QDialog()
    ui = Ui_SliderTestUI()
    ui.setupUi(SliderTestUI)
    SliderTestUI.show()
    sys.exit(app.exec_())

