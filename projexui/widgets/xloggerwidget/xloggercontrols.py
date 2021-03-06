#!/usr/bin/python

""" Creates a widget for monitoring logger information. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

import projex.text
import projexui
import sys
import webbrowser

from projexui.widgets.xtreewidget import XTreeWidgetItem
from xqt import QtCore, QtGui, wrapVariant, unwrapVariant

class XLoggerControls(QtGui.QWidget):
    activeLevelsChanged = QtCore.Signal(list)
    
    def __init__(self, loggerWidget):
        super(XLoggerControls, self).__init__(loggerWidget)
        
        # load the user interface
        projexui.loadUi(__file__, self)
        
        self._url = 'https://docs.python.org/2/library/logging.html#logrecord-attributes'
        self._loggerWidget = loggerWidget
        self.uiLoggerTREE.setLoggerWidget(loggerWidget)
        self.uiFormatTXT.setText(loggerWidget.formatText())
        
        # load the levels
        if 'designer' not in sys.executable:
            tree = self.uiLevelTREE
            from projexui.widgets.xloggerwidget import XLoggerWidget
            items = sorted(XLoggerWidget.LoggingMap.items())
            for i, (level, data) in enumerate(items):
                item = XTreeWidgetItem(tree, [projex.text.pretty(data[0])])
                item.setFixedHeight(22)
                item.setData(0, QtCore.Qt.UserRole, wrapVariant(level))
                item.setCheckState(0, QtCore.Qt.Unchecked)
        
        # create connections
        self.uiFormatTXT.textChanged.connect(loggerWidget.setFormatText)
        self.uiLevelTREE.itemChanged.connect(self.updateLevels)
        self.uiHelpBTN.clicked.connect(self.showHelp)

    def showEvent(self, event):
        super(XLoggerControls, self).showEvent(event)
        
        # update the format text
        widget = self._loggerWidget
        self.uiFormatTXT.setText(widget.formatText())
        
        # update the active levels
        lvls = widget.activeLevels()
        tree = self.uiLevelTREE
        tree.blockSignals(True)
        for item in tree.topLevelItems():
            if unwrapVariant(item.data(0, QtCore.Qt.UserRole)) in lvls:
                item.setCheckState(0, QtCore.Qt.Checked)
            else:
                item.setCheckState(0, QtCore.Qt.Unchecked)
        tree.blockSignals(False)

    def showHelp(self):
        webbrowser.open(self._url)

    def updateLevels(self):
        levels = []
        tree = self.uiLevelTREE
        tree.blockSignals(True)
        for item in tree.checkedItems():
            level = unwrapVariant(item.data(0, QtCore.Qt.UserRole))
            if level is not None:
                levels.append(level)
        tree.blockSignals(False)
        self._loggerWidget.setActiveLevels(levels)


