#!/usr/bin/python

""" Defines a reusable widget for the XConsoleEdit. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

#------------------------------------------------------------------------------

import logging
from xqt import QtCore, QtGui, wrapVariant, unwrapVariant

#from projexui.widgets.xlogrecordwidget import XLogRecordWidget
#from projexui.widgets.xconsoleedit import XConsoleEdit
#from projexui.widgets.xcodeedit import XCodeEdit

import projexui

from projexui.widgets.xviewwidget import XViewWidget
from projexui.views.xconsoleview import XConsoleView
from projexui.views.xscriptview import XScriptView
from projexui.views.xlogrecordview import XLogRecordView

class XDevToolsWidget(XViewWidget):
    def __init__(self, parent=None):
        super(XDevToolsWidget, self).__init__(parent)
        
        # register the views for the development
        self.setViewTypes([XConsoleView,
                           XLogRecordView,
                           XScriptView])
