# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '../Simulator/UI_Files/SliderTest_UI.ui'
#
# Created: Wed May 15 20:39:46 2013
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
        self.widget = QtWidgets.QWidget(SliderTestUI)
        self.widget.setGeometry(QtCore.QRect(20, 10, 351, 261))
        self.widget.setObjectName(_fromUtf8("widget"))
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.widget)
        self.horizontalLayout.setMargin(0)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.doubleSpinBox = QtWidgets.QDoubleSpinBox(self.widget)
        self.doubleSpinBox.setObjectName(_fromUtf8("doubleSpinBox"))
        self.verticalLayout.addWidget(self.doubleSpinBox)
        self.SliderFloat = QtWidgets.QSlider(self.widget)
        self.SliderFloat.setOrientation(QtCore.Qt.Vertical)
        self.SliderFloat.setObjectName(_fromUtf8("SliderFloat"))
        self.verticalLayout.addWidget(self.SliderFloat)
        self.label = QtWidgets.QLabel(self.widget)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.spinBox = QtWidgets.QSpinBox(self.widget)
        self.spinBox.setObjectName(_fromUtf8("spinBox"))
        self.verticalLayout_2.addWidget(self.spinBox)
        self.SliderInt = QtWidgets.QSlider(self.widget)
        self.SliderInt.setOrientation(QtCore.Qt.Vertical)
        self.SliderInt.setObjectName(_fromUtf8("SliderInt"))
        self.verticalLayout_2.addWidget(self.SliderInt)
        self.label_2 = QtWidgets.QLabel(self.widget)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout_2.addWidget(self.label_2)
        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.retranslateUi(SliderTestUI)
        QtCore.QMetaObject.connectSlotsByName(SliderTestUI)

    def retranslateUi(self, SliderTestUI):
        SliderTestUI.setWindowTitle(_translate("SliderTestUI", "Dialog", None))
        self.label.setText(_translate("SliderTestUI", "Slider to Float", None))
        self.label_2.setText(_translate("SliderTestUI", "Slider to Int", None))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    SliderTestUI = QtWidgets.QDialog()
    ui = Ui_SliderTestUI()
    ui.setupUi(SliderTestUI)
    SliderTestUI.show()
    sys.exit(app.exec_())

