import time, sys
from PyQt5.QtCore  import *
from PyQt5.QtWidgets import *; from PyQt5.QtGui import *

class SimulRunner(QObject):
    'Object managing the simulation'

    stepIncreased = pyqtSignal(int, name = 'stepIncreased')
    def __init__(self):
        super(SimulRunner, self).__init__()
        self._step = 0
        self._isRunning = True
        self._maxSteps = 200
        
    def longRunning(self):
        while self._step  < self._maxSteps  and self._isRunning == True:
            self._step += 1
            self.stepIncreased.emit(self._step)
            time.sleep(0.1)
            
    def stop(self):
        self._isRunning = False

class SimulationUi(QDialog):
    'PyQt interface'
    
    def __init__(self):
        super(SimulationUi, self).__init__()
        
        self.goButton = QPushButton('Go')
        self.stopButton = QPushButton('Stop')
        self.currentStep = QSpinBox()
        
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.goButton)
        self.layout.addWidget(self.stopButton)
        self.layout.addWidget(self.currentStep)
        self.setLayout(self.layout)

        self.simulRunner = SimulRunner()
        self.simulThread = QThread()
        self.simulRunner.moveToThread(self.simulThread)
        self.simulThread.started.connect(self.simulRunner.longRunning)
        self.simulRunner.stepIncreased.connect(self.currentStep.setValue)


        self.stopButton.clicked.connect(self.simulRunner.stop)
        self.goButton.clicked.connect(self.simulThread.start)
        self.simulRunner.stepIncreased.connect(self.currentStep.setValue)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    simul = SimulationUi()
    simul.show()
    sys.exit(app.exec_())