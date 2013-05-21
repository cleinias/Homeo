from PyQt4.QtCore import *
from PyQt4.QtGui import *
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
        self.connect(self.doubleSpinBox, SIGNAL("valueChanged"), self, SLOT("self.emitConverted"))
        self.connect(self.doubleSpinBox, SIGNAL("valueConvertedChanged(int)"), self.SliderFloat, SLOT("setValue(int)"))
        self.connect(self.SliderFloat, SIGNAL("valueChanged(int)"), self.doubleSpinBox, SLOT("setValue(int)"))
#        self.connect(self.doubleSpinBox, SIGNAL("valueChanged(double)"), self.SliderInt, SLOT("setValue(int)"))
        
    def setupIntSlider(self):
        self.SliderInt.setMaximum(100)
        self.SliderInt.setMinimum(0)
#        QObject.connect(self.spinBox, SIGNAL("valueChanged"), self.SliderInt, SLOT("setValue(int)"))
        self.connect(self.spinBox, SIGNAL("valueChanged(int)"), self.SliderInt, SLOT("setValue(int)"))
        self.connect(self.SliderInt, SIGNAL("valueChanged(int)"), self.spinBox, SLOT("setValue(int)"))

    def emitConverted(self,aFloat):
        print "I'm emitting valueConvertedChanged(int)"
        self.doubleSpinBox.emit(SIGNAL("valueConvertedChanged(int)"), int(floor(aFloat * self.prec)))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    simul = SliderTest()
    simul.show()
    app.exec_()
    
