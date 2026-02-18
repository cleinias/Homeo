'''
Created on Apr 24, 2013
Updated for PyQt5: Feb 2026

@author: Tom Dossis (original), Stefano Franchi (PyQt5 port)

Provides a SignalHub QObject that declares all signals used by non-QObject
Core classes (HomeoUnit, HomeoConnection, Homeostat, HomeoUniselector).
The emitter() function returns a SignalHub instance instead of a bare QObject,
preserving picklability of the Core classes.

Sample usage (PyQt5):

     class A(object):
         def notify(self):
             emitter(self).nameChanged.emit('hello')

     ob = A()
     emitter(ob).nameChanged.connect(some_slot)
     ob.notify()

'''
from PyQt5.QtCore import QObject, pyqtSignal
import weakref


class SignalHub(QObject):
    """QObject surrogate that declares all signals used by Core classes."""

    # HomeoUnit signals
    nameChanged = pyqtSignal(object)
    nameChangedLineEdit = pyqtSignal(object)
    currentOutputChanged = pyqtSignal(object)
    currentOutputChangedLineEdit = pyqtSignal(object)
    inputTorqueChanged = pyqtSignal(object)
    inputTorqueChangedLineEdit = pyqtSignal(object)
    unitActiveIndexchanged = pyqtSignal(object)
    massChanged = pyqtSignal(object)
    massChangedLineEdit = pyqtSignal(object)
    switchChanged = pyqtSignal(object)
    switchChangedLineEdit = pyqtSignal(object)
    potentiometerDeviationChanged = pyqtSignal(object)
    potentiometerChanged = pyqtSignal(object)
    potentiometerChangedLineEdit = pyqtSignal(object)
    viscosityChanged = pyqtSignal(object)
    viscosityChangedLineEdit = pyqtSignal(object)
    noiseChanged = pyqtSignal(object)
    noiseChangedLineEdit = pyqtSignal(object)
    criticalDeviationChanged = pyqtSignal(object)
    criticalDeviationChangedLineEdit = pyqtSignal(object)
    criticalDeviationScaledChanged = pyqtSignal(int)
    minDeviationChanged = pyqtSignal(object)
    minDeviationChangedLineEdit = pyqtSignal(object)
    minDeviationScaledChanged = pyqtSignal(int)
    maxDeviationChanged = pyqtSignal(object)
    maxDeviationChangedLineEdit = pyqtSignal(object)
    maxDeviationScaledChanged = pyqtSignal(int)
    deviationRangeChanged = pyqtSignal(object, object)
    uniselectorTimeIntervalChanged = pyqtSignal(object)
    uniselectorTimeIntervalChangedLineEdit = pyqtSignal(object)
    unitUniselOnChanged = pyqtSignal(object)

    # HomeoConnection signals
    weightChanged = pyqtSignal(object)

    # Homeostat signals
    homeostatTimeChanged = pyqtSignal(int)

    # HomeoUniselector signals
    uniselSoundChanged = pyqtSignal(object)
    unitUniselSoundChanged = pyqtSignal(object)


_emitterCache = weakref.WeakKeyDictionary()

def emitter(ob):
    """Returns a SignalHub surrogate for *ob*, to use in Qt signaling.

    This function enables you to connect to and emit signals from (almost)
    any python object without having to subclass QObject.
    """

    if ob not in _emitterCache:
        _emitterCache[ob] = SignalHub()
    return _emitterCache[ob]
