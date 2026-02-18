'''
Created on May 5, 2013

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
        """
        \brief Constructor.
        \param args tuple: [finish me]
        \param kwargs dict: Property keyword arguments
        """
        if len(args) == 2:
            assert(isinstance(args[0], Qt.Orientation))
            assert(isinstance(args[1], QObject))
            orient = args[0]
            parent = args[1]
        elif len(args) == 1:
            assert(isinstance(args[1], QObject))
            parent = args[1]
            orient = kwargs.pop('orientation', Qt.Horizontal)
        else:
            parent = kwargs.pop('parent', None)
            orient = kwargs.pop('orientation', Qt.Horizontal)
            super(Separator,self).__init__(parent, **kwargs)
        
        self.__orient = None
        self.orientation = orient
    
    def paintEvent(self, ev):
        """
        Reimplemented from parent class.
        \protected
        """
        p = QPainter(self)
        opt = QStyleOption()
        opt.initFrom(self)
        self.style().drawPrimitive(QStyle.PE_IndicatorToolBarSeparator,
        opt, p, self)
    
    def getOrientation(self):
        """
        \brief Returns the orientation property.
        \returns \var Qt.Orientation
        \getter orientation
        """
        return self.__orient
    
    def setOrientation(self, orient):
        """
        \brief Sets the orientation property.
        \param orient Qt.Orientation
        \setter orientation
        """
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