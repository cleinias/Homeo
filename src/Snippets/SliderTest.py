# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '../Simulator/UI_Files/SliderTest_UI.ui'
#
# Created: Wed May 15 20:27:32 2013
#      by: PyQt4 UI code generator 4.9.6
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_SliderTestUI(object):
    def setupUi(self, SliderTestUI):
        SliderTestUI.setObjectName(_fromUtf8("SliderTestUI"))
        SliderTestUI.resize(400, 300)
        self.verticalSlider = QtGui.QSlider(SliderTestUI)
        self.verticalSlider.setGeometry(QtCore.QRect(350, 50, 16, 160))
        self.verticalSlider.setOrientation(QtCore.Qt.Vertical)
        self.verticalSlider.setObjectName(_fromUtf8("verticalSlider"))
        self.verticalSlider_2 = QtGui.QSlider(SliderTestUI)
        self.verticalSlider_2.setGeometry(QtCore.QRect(40, 50, 16, 160))
        self.verticalSlider_2.setOrientation(QtCore.Qt.Vertical)
        self.verticalSlider_2.setObjectName(_fromUtf8("verticalSlider_2"))
        self.lineEdit = QtGui.QLineEdit(SliderTestUI)
        self.lineEdit.setGeometry(QtCore.QRect(130, 110, 113, 23))
        self.lineEdit.setObjectName(_fromUtf8("lineEdit"))

        self.retranslateUi(SliderTestUI)
        QtCore.QMetaObject.connectSlotsByName(SliderTestUI)

    def retranslateUi(self, SliderTestUI):
        SliderTestUI.setWindowTitle(_translate("SliderTestUI", "Dialog", None))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    SliderTestUI = QtGui.QDialog()
    ui = Ui_SliderTestUI()
    ui.setupUi(SliderTestUI)
    SliderTestUI.show()
    sys.exit(app.exec_())

