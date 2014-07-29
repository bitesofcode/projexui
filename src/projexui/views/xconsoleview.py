#!/usr/bin/python

""" Defines a reusable widget for the XConsoleEdit. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

from xqt import QtGui
from projexui.widgets.xviewwidget import XView
from projexui.widgets.xconsoleedit import XConsoleEdit

class XConsoleView(XView):
    def __init__(self, parent):
        super(XConsoleView, self).__init__(parent)
        
        # define custom properties
        self._console = XConsoleEdit(self)
        
        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._console)
        self.setLayout(layout)
        
        self.initialized.connect(self.setupConsole)

    def closeEvent(self, event):
        self._console.cleanup()
        
        super(XConsoleView, self).closeEvent(event)

    def setupConsole(self):
        self._console.setScope(self.viewWidget().codeScope())

    def console(self):
        """
        Returns the console for this view.
        
        :return     <projexui.widgets.xconsoleedit.XConsoleEdit>
        """
        return self._console

XConsoleView.setViewName('Console')

