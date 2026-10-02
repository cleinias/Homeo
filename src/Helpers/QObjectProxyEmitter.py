'''
Created on Apr 24, 2013
Updated for PyQt5: Feb 2026
Headless fallback without PyQt5: Oct 2026

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

Without PyQt5 (a headless batch run on a machine that has no Qt), emitter()
returns a shared null hub instead.  Its signals accept .emit() and do nothing,
which is what a Qt signal with no connected receiver does: nothing headless
ever connects, and in a headless run every emit happens while the network is
being built, before any GUI could exist.  Calling .connect() on it raises,
since it would mean someone expects signals in a process that cannot deliver
them.  The choice is made once, when this module is first imported, by trying
to import PyQt5: there is nothing to configure.

'''
import weakref

# Every signal a Core class emits.  SignalHub declares one pyqtSignal per name;
# the null hub accepts exactly these, so a misspelt signal fails the same way
# with or without Qt.  Unit_Tests/EmitterTest.py keeps the two lists in step.
SIGNAL_NAMES = (
    'nameChanged',
    'nameChangedLineEdit',
    'currentOutputChanged',
    'currentOutputChangedLineEdit',
    'inputTorqueChanged',
    'inputTorqueChangedLineEdit',
    'unitActiveIndexchanged',
    'massChanged',
    'massChangedLineEdit',
    'switchChanged',
    'switchChangedLineEdit',
    'potentiometerDeviationChanged',
    'potentiometerChanged',
    'potentiometerChangedLineEdit',
    'viscosityChanged',
    'viscosityChangedLineEdit',
    'noiseChanged',
    'noiseChangedLineEdit',
    'criticalDeviationChanged',
    'criticalDeviationChangedLineEdit',
    'criticalDeviationScaledChanged',
    'minDeviationChanged',
    'minDeviationChangedLineEdit',
    'minDeviationScaledChanged',
    'maxDeviationChanged',
    'maxDeviationChangedLineEdit',
    'maxDeviationScaledChanged',
    'deviationRangeChanged',
    'uniselectorTimeIntervalChanged',
    'uniselectorTimeIntervalChangedLineEdit',
    'unitUniselOnChanged',
    'weightChanged',
    'homeostatTimeChanged',
    'uniselSoundChanged',
    'unitUniselSoundChanged',
)

try:
    from PyQt5.QtCore import QObject, pyqtSignal
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False


if QT_AVAILABLE:

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

else:

    class _NullSignal(object):
        """Stands in for a pyqtSignal when PyQt5 is absent."""
        __slots__ = ('_name',)

        def __init__(self, name):
            self._name = name

        def emit(self, *args):
            pass

        def connect(self, *args, **kwargs):
            raise RuntimeError(
                "cannot connect to signal %r: PyQt5 is not installed, so Homeo "
                "signals are disabled in this process" % self._name)

    class _NullHub(object):
        """Stands in for SignalHub when PyQt5 is absent."""
        __slots__ = ()

        def __getattr__(self, name):
            try:
                return _NULL_SIGNALS[name]
            except KeyError:
                raise AttributeError(
                    "'SignalHub' object has no attribute %r" % name) from None

    _NULL_SIGNALS = {name: _NullSignal(name) for name in SIGNAL_NAMES}
    _NULL_HUB = _NullHub()

    def emitter(ob):
        """Returns the shared null hub: PyQt5 is not available."""
        return _NULL_HUB
