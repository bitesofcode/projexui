#!/usr/bin python

"""
Defines base classes that can be used with stylesheets for custom
styling. """

# define authorship information
__authors__     = ['Eric Hulser']
__author__      = ','.join(__authors__)
__credits__     = []
__copyright__   = 'Copyright (c) 2011, Projex Software'

from projexui.qt import QtGui
from projexui.xpainter import XPainter

class XStyleableMixin(object):
    StyleOptionClass = QtGui.QStyleOption
    
    def drawStyle(self, style, painter, option):
        raise NotImplementedError

    def paintEvent(self, event):
        with XPainter(self) as painter:
            self.drawStyle(self.style(), painter, self.styleOption())

    def styleOption(self):
        opt = self.StyleOptionClass()
        opt.initFrom(self)
        return opt


# P
#----------------------------------------------------------------------

class XStyleablePushButton(QtGui.QPushButton, XStyleableMixin):
    StyleOptionClass = QtGui.QStyleOptionButton
    
    def drawStyle(self, style, painter, option):
        style.drawControl(QtGui.QStyle.CE_PushButton, option, painter, self)

    def styleOption(self):
        opt = super(XStyleablePushButton, self).styleOption()
        
        # setup additional options
        opt.icon = self.icon()
        opt.iconSize = self.iconSize()
        opt.text = self.text()
        return opt

# W
#----------------------------------------------------------------------

class XStyleableWidget(QtGui.QWidget, XStyleableMixin):
    def drawStyle(self, style, painter, option):
        style.drawPrimitive(QtGui.QStyle.PE_Widget, option, painter, self)


