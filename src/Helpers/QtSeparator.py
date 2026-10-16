'''
@author: mnijph
from http://code.google.com/p/kyui/source/browse/trunk/src/Widgets/separator.pyw?r=182
'''

from PyQt5.QtCore import Qt, QObject, pyqtProperty
from PyQt5.QtWidgets import QFrame, QStyle, QStyleOption
from PyQt5.QtGui import QPainter
    
class Separator(QFrame):
    """
    Acts as a horizontal or vertical divider in a layout.
    This class is functionally identical to the Horizontal Line and Vertical
    Line objects provided in QtDesigner.
    """
    def __init__(self, *args, **kwargs):
        """Separator(), Separator(parent), Separator(orientation, parent), or
        the keywords orientation and parent; other keywords go to QFrame."""
        orient = kwargs.pop('orientation', Qt.Horizontal)
        parent = kwargs.pop('parent', None)
        if len(args) == 2:
            orient, parent = args
        elif len(args) == 1:
            parent = args[0]
        elif args:
            raise TypeError('Separator takes at most 2 positional arguments')
        assert isinstance(orient, Qt.Orientation)
        assert parent is None or isinstance(parent, QObject)
        super(Separator, self).__init__(parent, **kwargs)

        self.__orient = None
        self.orientation = orient

    def paintEvent(self, ev):
        "Reimplemented from QFrame: draws a toolbar separator."
        p = QPainter(self)
        opt = QStyleOption()
        opt.initFrom(self)
        self.style().drawPrimitive(QStyle.PE_IndicatorToolBarSeparator,
        opt, p, self)
    
    def getOrientation(self):
        "The orientation property: a Qt.Orientation."
        return self.__orient
    
    def setOrientation(self, orient):
        "Set the orientation property (a Qt.Orientation)."
        assert(isinstance(orient, Qt.Orientation))
        if orient == self.__orient:
            return
        self.__orient = orient
        
        extant = self.style().pixelMetric(QStyle.PM_ToolBarSeparatorExtent)
        if orient == Qt.Horizontal:
            self.setFixedSize(16777215, extant)
        else:
            self.setFixedSize(extant, 16777215)
        ##\name Properties
        ##\{
        
    orientation = pyqtProperty(Qt.Orientation,
                               fset=setOrientation,
                               fget=getOrientation)
         ##\}