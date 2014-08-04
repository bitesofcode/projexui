#!/usr/bin/python

"""
Defines the XPainter class, a simple wrapper over the <QtGui.QPainter> class
that supports python's notion of enter/exit contexts to begin and end painting
on a device.  This is more reliable than using Qt's scoping as the object
may linger in memory longer than in the C++ version.

:usage      |from xqt import QtGui
            |from projexui.xpainter import XPainter
            |class MyWidget(QtGui.QWidget):
            |   def paintEvent(self, event):
            |       with XPainter(self) as painter:
            |           # do some paint operations
"""

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'


from xqt import QtGui


class XPainter(QtGui.QPainter):
    def __init__(self, device):
        super(XPainter, self).__init__()
        
        # store a reference to the paint device
        self._device = device

    def __enter__(self):
        self.begin(self._device)
        return self

    def __exit__(self, *args):
        self.end()


