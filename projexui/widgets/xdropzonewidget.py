""" Defines a widget for editing enumerated types """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2012, Projex Software'
__license__         = 'LGPL'

# maintenance information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

from projexui.qt import QtCore, QtGui
from projexui.xpainter import XPainter

class XDropZoneRegion(QtGui.QLabel):
    def __init__(self, parent):
        super(XDropZoneRegion, self).__init__(parent)
        
        palette = self.palette()
        self._hovered = False
        self._foreground = palette.color(palette.HighlightedText)
        self._background = palette.color(palette.Highlight)
        
        # define the attributes for this widget
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.setAutoFillBackground(True)
        self.setWordWrap(True)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setMinimumSize(80, 40)
    
    def background(self):
        """
        Returns the background associated with this drop zone.
        
        :return     <QtGui.QColor>
        """
        return self._background
    
    def isHovered(self):
        """
        Returns whether or not this widget is being hovered over.
        
        :return     <bool>
        """
        return self._hovered
    
    def foreground(self):
        """
        Returns the foreground associated with this drop zone.
        
        :return     <QtGui.QColor>
        """
        return self._foreground
    
    def paintEvent(self, event):
        with XPainter(self) as painter:
            if self.isHovered():
                alpha = 120
            else:
                alpha = 30
            
            x = 0
            y = 0
            w = self.width() - 1
            h = self.height() - 1
            
            clr = QtGui.QColor(self.background())
            clr.setAlpha(alpha)
            brush = QtGui.QBrush(clr)
            painter.setPen(self.foreground())
            painter.setBrush(brush)
            
            painter.drawRect(x, y, w, h)
            painter.drawText(x, y, w, h,
                             QtCore.Qt.AlignCenter | QtCore.Qt.TextWordWrap,
                             self.text())

    def setBackground(self, background):
        """
        Returns the background associated with this drop zone.
        
        :return     <QtGui.QColor>
        """
        self._background = background
    
    def setForeground(self, foreground):
        """
        Returns the foreground associated with this drop zone.
        
        :return     <QtGui.QColor>
        """
        self._foreground = foreground
    
    def testHovered(self, pos):
        self._hovered = self.geometry().contains(pos)
        self.repaint()
        return self._hovered
    
#----------------------------------------------------------------------

class XDropZoneWidget(QtGui.QWidget):
    def __init__(self, parent):
        super(XDropZoneWidget, self).__init__(parent)
        
        self._filter = None
        
        parent.installEventFilter(self)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.setLayout(QtGui.QGridLayout())
        self.lower()
        self.hide()

    def addRegion(self, name, text, row, column):
        """
        Adds a new region for this zone at the given row and column.
        
        :param      name   | <str>
                    text   | <str>
                    row    | <int>
                    column | <int>
        """
        region = XDropZoneRegion(self)
        region.setObjectName(name)
        region.setText(text)
        region.hide()
        self.layout().addWidget(region, row, column)
        return region

    def currentRegion(self):
        """
        Returns the current region based on the current cursor position.
        
        :return     <XDropZoneWidget>
        """
        pos = QtGui.QCursor.pos()
        pos = self.mapFromGlobal(pos)
        for region in self.regions():
            if region.testHovered(pos):
                return region
        return None

    def eventFilter(self, object, event):
        if event.type() == event.Resize:
            self.resize(self.parent().width(), self.parent().height())
        
        elif event.type() == event.DragEnter:
            if self._filter is None or self._filter(event):
                self.raise_()
                self.show()

                for region in self.regions():
                    region.show()
        
        elif event.type() == event.DragMove:
            if self._filter is None or self._filter(event):
                self.raise_()
                self.show()

                pos = QtGui.QCursor.pos()
                pos = self.mapFromGlobal(pos)
                for region in self.regions():
                    region.testHovered(pos)
        
        elif event.type() in (event.DragLeave, event.Drop, event.Leave):
            self.hide()
            self.lower()

            for region in self.regions():
                region.hide()
        
        return False

    def filter(self):
        """
        Returns the filter associated with this zone widget
        to determine whether or not to accept the drop event.
        
        :return     <callable> || None
        """
        return sel.f_filter

    def region(self, name):
        """
        Returns the region associated with the given name for this zone.
        
        :return     <XDropZoneRegion> || None
        """
        return self.findChild(XDropZoneRegion, name)

    def setColumnStretch(self, col, stretch):
        self.layout().setColumnStretch(col, stretch)

    def setRowStretch(self, row, stretch):
        self.layout().setRowStretch(row, stretch)

    def setFilter(self, filter):
        """
        Sets the filter callable that will determine
        if this widget should be shown for a given
        drag event.
        
        :param      filter | <callable>
        """
        self._filter = filter

    def regions(self):
        l = self.layout()
        widgets = [l.itemAt(i).widget() for i in range(l.count())]
        return filter(lambda x: x is not None, widgets)

