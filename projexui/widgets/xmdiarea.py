#!/usr/bin/python

""" Creates reusable Qt widgets for various applications. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

from projexui import resources
from projexui.qt import QtCore, QtGui
from projexui.widgets.xtoolbutton import XToolButton
from projexui.xpainter import XPainter

class XMdiSubWindow(QtGui.QMdiSubWindow):
    def __init__(self, parent, windowFlags=0):
        windowFlags = QtCore.Qt.WindowFlags(windowFlags)
        super(XMdiSubWindow, self).__init__(parent, windowFlags)
        
        # define custom properties
        palette = self.palette()
        
        font = self.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 2)
        
        self._titleBarFont = font
        self._titleBarBackground = palette.color(palette.Button)
        self._titleBarForeground = palette.color(palette.ButtonText)
        self._titleBarBorder = QtGui.QColor('black')
        
        # create the drop shadow effect
        eff = QtGui.QGraphicsDropShadowEffect(self)
        eff.setOffset(0, 0)
        eff.setBlurRadius(40)
        eff.setColor(palette.color(palette.Shadow))
        self.setGraphicsEffect(eff)
        
        # create the control buttons
        self._sysmenuBtn = XToolButton(self)
        self._sysmenuBtn.setIcon(self.windowIcon())
        self._sysmenuBtn.setPalette(palette)
        self._sysmenuBtn.setAutoRaise(True)
        self._sysmenuBtn.setFixedSize(QtCore.QSize(22, 22))
        self._sysmenuBtn.move(4, 4)
        self._sysmenuBtn.show()
        
        palette.setColor(palette.Shadow, QtGui.QColor('yellow'))
        
        self._minimizeBtn = XToolButton(self)
        self._minimizeBtn.setIcon(QtGui.QIcon(resources.find('img/mdiarea/minimize.png')))
        self._minimizeBtn.setPalette(palette)
        self._minimizeBtn.setShadowed(True)
        self._minimizeBtn.setShadowRadius(10)
        self._minimizeBtn.setFixedSize(QtCore.QSize(22, 22))
        self._minimizeBtn.show()
        
        palette.setColor(palette.Shadow, QtGui.QColor('orange'))
        
        self._maximizeBtn = XToolButton(self)
        self._maximizeBtn.setIcon(QtGui.QIcon(resources.find('img/mdiarea/maximize.png')))
        self._maximizeBtn.setPalette(palette)
        self._maximizeBtn.setShadowed(True)
        self._maximizeBtn.setShadowRadius(10)
        self._maximizeBtn.setFixedSize(QtCore.QSize(22, 22))
        self._maximizeBtn.show()
        
        palette.setColor(palette.Shadow, QtGui.QColor('red'))
        
        self._closeBtn = XToolButton(self)
        self._closeBtn.setIcon(QtGui.QIcon(resources.find('img/mdiarea/close.png')))
        self._closeBtn.setPalette(palette)
        self._closeBtn.setShadowed(True)
        self._closeBtn.setShadowRadius(10)
        self._closeBtn.setFixedSize(QtCore.QSize(22, 22))
        self._closeBtn.show()
        
        # create connections
        self._sysmenuBtn.clicked.connect(self.showSystemMenu)
        self._minimizeBtn.clicked.connect(self.toggleMinimized)
        self._maximizeBtn.clicked.connect(self.toggleMaximized)
        self._closeBtn.clicked.connect(self.close)

    def paintEvent(self, event):
        super(XMdiSubWindow, self).paintEvent(event)
        
        palette = self.palette()
        
        # draw the title
        with XPainter(self) as painter:
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setPen(self.titleBarBorder())
            painter.setBrush(self.titleBarBackground())
            painter.drawRect(0, 0, self.width(), 29)
            
            grad = QtGui.QLinearGradient()
            grad.setColorAt(0, QtGui.QColor(255, 255, 255, 30))
            grad.setColorAt(1, QtGui.QColor(0, 0, 0, 28))
            grad.setStart(0, 0)
            grad.setFinalStop(0, 30)
            
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(grad)
            painter.drawRect(0, 0, self.width(), 30)
            
            # draw the text
            painter.setFont(self.titleBarFont())
            
            bg = self.titleBarBackground()
            painter.setPen(bg.lighter(110))
            painter.drawText(45, 1, self.width(), 30,
                             QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                             self.windowTitle())
            
            painter.setPen(self.titleBarForeground())
            painter.drawText(45, 0, self.width(), 30,
                             QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                             self.windowTitle())

    def resizeEvent(self, event):
        super(XMdiSubWindow, self).resizeEvent(event)
        
        self._minimizeBtn.move(event.size().width() - 70, 4)
        self._maximizeBtn.move(event.size().width() - 50, 4)
        self._closeBtn.move(event.size().width() - 30, 4)

    def setTitleBarBackground(self, background):
        """
        Sets the background color for this titlebar.
        
        :param      background | <QtGui.QColor> || <QtGui.QBrush>
        """
        self._titleBarBackground = background

    def setTitleBarBorder(self, border):
        """
        Sets the border color for this titlebar.
        
        :param      border | <QtGui.QColor>
        """
        self._titleBarBorder = border

    def setTitleBarForeground(self, foreground):
        """
        Sets the foreground color for this titlebar.
        
        :param      foreground | <QtGui.QColor> || <QtGui.QPen>
        """
        self._titleBarForeground = foreground

    def setTitleBarFont(self, font):
        """
        Sets the font color for this titlebar.
        
        :param      font | <QtGui.QFont>
        """
        self._titleBarFont = font

    def setWindowIcon(self, icon):
        super(XMdiSubWindow, self).setWindowIcon(icon)
        
        self._sysmenuBtn.setIcon(icon)

    def toggleMinimized(self):
        if self.isMinimized() or self.isMaximized():
            self.showNormal()
        else:
            self.showMinimized()

    def toggleMaximized(self):
        if self.isMinimized() or self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def titleBarBackground(self):
        """
        Returns the background color for this titlebar.
        
        :return     <QtGui.QColor> || <QtGui.QBrush>
        """
        return self._titleBarBackground

    def titleBarBorder(self):
        """
        Returns the border color for this titlebar.
        
        :return     <QtGui.QColor>
        """
        return self._titleBarBorder

    def titleBarForeground(self):
        """
        Returns the foreground color for this titlebar.
        
        :return     <QtGui.QColor> || <QtGui.QPen>
        """
        return self._titleBarForeground

    def titleBarFont(self):
        """
        Returns the font color for this titlebar.
        
        :return     <QtGui.QFont>
        """
        return self._titleBarFont

#----------------------------------------------------------------------

class XMdiArea(QtGui.QMdiArea):
    def addSubWindow(self, widget, windowFlags=0):
        """
        Creates a new sub window for this widget, specifically
        creating an XMdiSubWindow class.
        
        :param      widget      | <QtGui.QWidget>
                    windowFlags | <QtCore.Qt.WindowFlags>
        
        :return     <XMdiSubWindow>
        """
        if not widget:
            return 0
        
        childFocus = widget.focusWidget()
        
        # child is already a sub window
        if not isinstance(widget, QtGui.QMdiSubWindow):
            child = XMdiSubWindow(self.viewport(), windowFlags)
            child.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            child.setWidget(widget)
        else:
            child = widget
        
        if childFocus:
            childFocus.setFocus()
        
        return super(XMdiArea, self).addSubWindow(child)

__designer_plugins__ = [XMdiArea]