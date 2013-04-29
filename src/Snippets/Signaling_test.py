import time, sys
from PyQt4.QtCore  import *
from PyQt4.QtGui import * 
from threading import Thread
 

import weakref

_emitterCache = weakref.WeakKeyDictionary()

def emitter(ob):
    """Returns a QObject surrogate for *ob*, to use in Qt signaling.

    This function enables you to connect to and emit signals from (almost)
    any python object without having to subclass QObject.

    """

    if ob not in _emitterCache:
        _emitterCache[ob] = QObject()
    return _emitterCache[ob]


class BigObject(object):
    '''The main object being simulated. Completely QT-Agnostic'''
    def __init__(self):
        self._time = 0
        
    def selfUpdate(self):
        self._time += 1
        QObject.emit(emitter(self), SIGNAL('stepIncreased'), self._time)
    
    def setStep(self,value):
        self._time = value
        print "I'm in self.setStep"
    def getStep(self):
        return self._time
        print "returning value %u" % self._time
    step = property(fget = lambda self: self.getStep(),
                    fset = lambda self, value: self.setStep(value))

        
class Simulation(object):
    'The class managing the simulation, QT-agnostic as well. Can be run from CLI' 
    def __init__(self):
        self.simulatedObject = BigObject()
        self._isRunning = False
        
    def runForever(self):
        'Must be run in a thread'
        while self._isRunning == True:
            self.simulatedObject.selfUpdate()
            time.sleep(0.0)
    
    def start(self):
        self._isRunning = True
        self.runForever()
    
    def stop(self):
        self._isRunning = False
        
        
class QSimulation(QObject):
    'QObject managing the simulation'

    stepIncreased = pyqtSignal(int, name = 'stepIncreased')
    
    def __init__(self):
        super(QSimulation, self).__init__()
        self._simulatedObject = BigObject()
        self._step = 0
        self._isRunning = True
        self._maxSteps = 200
        
    
    def startSimulation(self):
        self._simulatedObject.start()
    
    def go(self):
         self._isRunning = True
         print 'clicked go button and iVar self._iRunning = %d' % self._isRunning
         self.longRunning()
         print "and now iVar self._isRunning = %s" % self._isRunning

    def go2(self):
         self._isRunning = True
         print 'clicked go button and iVar self._iRunning = %d' % self._isRunning
         self.runForever()
         print "and now iVar self._isRunning = %s" % self._isRunning

    def runForever(self):
        'Must be run in a thread'
        while self._simulatedObject.step  < self._maxSteps  and self._isRunning == True:
            self._simulatedObject.selfUpdate()
            time.sleep(0.1)
            QApplication.processEvents() 

                
    def longRunning(self):
        while self._step  < self._maxSteps  and self._isRunning == True:
            self._step += 1
            self.stepIncreased.emit(self._step)
            time.sleep(0.01)
            QApplication.processEvents() 
            
    def stop(self):
        print "clicked stop button and iVar self._isRunning = %s" % self._isRunning
        self._isRunning = False
        print "and now iVar self._isRunning = %s" % self._isRunning

class MyThread(QThread):
    def run(self):
        self.exec_()
        
        
class SimulationUi(QDialog):
    'PyQt interface'
    
    def __init__(self):
        
        super(SimulationUi, self).__init__()

        
        self.goButton = QPushButton('Go')
        self.stopButton = QPushButton('Stop')
        self.resumeButton = QPushButton('Resume')
        self.currentStep = QSpinBox()
        self.currentStep.setRange(0,100000)
        
        
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.goButton)
        self.layout.addWidget(self.resumeButton)
        self.layout.addWidget(self.stopButton)
        self.layout.addWidget(self.currentStep)
        self.setLayout(self.layout)


        self.qsimulation = QSimulation()
#        self.simulThread = Thread(target = self.simulation.start)
#        self.simulRunner = SimulRunner(self.simulation)        
        self.simulThread = MyThread()
        self.qsimulation.moveToThread(self.simulThread)

#        self.stopButton.clicked.connect(self.stop)
        self.stopButton.clicked.connect(self.qsimulation.stop)
        self.goButton.clicked.connect(self.simulThread.start)
        self.resumeButton.clicked.connect(self.qsimulation.go2)
        self.simulThread.started.connect(self.qsimulation.go2)
#        emitter(self.qsimulation._simulatedObject).stepIncreased.connect(self.currentStep.setValue)
        QObject.connect(emitter(self.qsimulation._simulatedObject), SIGNAL("stepIncreased"), self.currentStep.setValue)
        self.currentStep.valueChanged.connect(self.qsimulation._simulatedObject.setStep)
    
    def stop(self):
        print "clicked stop button"
        print self.simulThread.isRunning()
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    simul = SimulationUi()
    simul.show()
    sys.exit(app.exec_())


