'''
Created on Apr 24, 2013

@author: Tom Dossis
From http://code.activestate.com/recipes/361527-emit-qt-signals-from-a-non-qobject-type/

In PyQt applications it is often desirable to connect objects from the model domain to Qt widgets. 
Qt requires objects which emit signals to inherit QObject. This may sometimes be too restrictive or cumbersome. 
For example, objects which inherit QObject are not pickleable. Also classes can't derive from both object 
and QObject. This function provides a non invasive way to allow model objects to participate in Qt signalling.

This simple solution associates a QObject instance for each object passed to the emitter function. 
When the object is no longer referenced the assocation is removed, thereby freeing the QObject 
which will subsequently be removed from the Qt signalling system.

Sample usage:

     class A(object):
         def notify(self, *args):
          QObject.emit(emitter(self), PYSIGNAL('test'), args)
      
      ob = A()
      def myhandler(*args): print 'got', args
      ...
      QObject.connect(emitter(ob), PYSIGNAL('test'), myhandler)
    True
      ob.notify('hello')
    got ('hello',)

      QObject.emit(emitter(ob), PYSIGNAL('test'), (42, 'abc',))
    got (42, 'abc')

'''
from PyQt4.QtCore import QObject
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
