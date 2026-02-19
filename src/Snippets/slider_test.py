from PyQt5.QtCore import *
from PyQt5.QtWidgets import *; from PyQt5.QtGui import *
from SliderTest_UI import *     
import sys
from math import floor
    
class SliderTest(QDialog, Ui_SliderTestUI):
    """Testing sliders with float/integer connections
    - verticalSlider is used to connect to Floats
    - verticalSlider_2 is connected to integers"""
    def __init__(self, parent = None):
        super(SliderTest, self).__init__(parent)
        self.prec = 10**5
        self.setupUi(self)
#        self.setupFloatSlider()
        self.setupIntSlider()
#        self.setGeometry

    def setupFloatSlider(self):
        '''Set up the critical deviation sliders. 
           As Qt sliders only accept integer values, we convert floats to integers using a precision parameter'''
         
        "the precision value to use for the float <--> integer conversion is stored in a class variable of HomeoUnit" 
                            
        self.SliderFloat.setMaximum(100)
        self.SliderFloat.setMinimum(0)
        self.doubleSpinBox.valueChanged.connect(self.emitConverted)
        # NOTE: valueConvertedChanged is a custom signal -- needs manual wiring if used
        self.SliderFloat.valueChanged.connect(self.doubleSpinBox.setValue)
#        self.connect(self.doubleSpinBox, SIGNAL("valueChanged(double)"), self.SliderInt, SLOT("setValue(int)"))
        
    def setupIntSlider(self):
        self.SliderInt.setMaximum(100)
        self.SliderInt.setMinimum(0)
#        QObject.connect(self.spinBox, SIGNAL("valueChanged"), self.SliderInt, SLOT("setValue(int)"))
        self.spinBox.valueChanged.connect(self.SliderInt.setValue)
        self.SliderInt.valueChanged.connect(self.spinBox.setValue)

    def emitConverted(self,aFloat):
        print("I'm emitting valueConvertedChanged(int)")
        # NOTE: old-style emit needs manual updating to use a custom pyqtSignal
        # self.doubleSpinBox.emit(SIGNAL("valueConvertedChanged(int)"), int(floor(aFloat * self.prec)))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    simul = SliderTest()
    simul.show()
    app.exec_()
    
