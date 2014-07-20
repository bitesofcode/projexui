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

import logging
import projex.text
import sys

from xqt import QtCore, QtGui, wrapVariant, unwrapVariant
from projexui.widgets.xloggerwidget import XLoggerWidget
from projexui.widgets.xtreewidget import XTreeWidget, \
                                         XTreeWidgetDelegate, \
                                         XTreeWidgetItem

class XLoggerTreeWidgetItem(XTreeWidgetItem):
    def __init__(self, logger, parent=None):
        super(XLoggerTreeWidgetItem, self).__init__(parent)
        
        # define the properties
        self._logger = logger
        
        # setup the text
        self.setText(0, logger.split('.')[-1])
        self.setCheckState(0, QtCore.Qt.Unchecked)
        self.setFixedHeight(22)
        self.updateUi()

    def logger(self):
        return self._logger

    def updateUi(self):
        if self.logger() == 'root':
            log = logging.getLogger()
        else:
            log = logging.getLogger(self.logger())
        
        level = log.level
        if self.treeWidget().loggerWidget().hasLogger(self.logger()):
            checked = QtCore.Qt.Checked
            fg = QtGui.QColor('black')
        else:
            checked = QtCore.Qt.Unchecked
            fg = QtGui.QColor('gray')
        
        self.setCheckState(0, checked)
        self.setForeground(0, fg)
        self.setForeground(1, fg)
        
        text = XLoggerTreeWidget.LoggingMap.get(level, ('', ''))[0]
        self.setText(1, projex.text.pretty(text))

#----------------------------------------------------------------------

class XLoggerDelegate(XTreeWidgetDelegate):
    def createEditor(self, parent, option, index):
        """
        Creates a new editor for the given index parented to the inputed widget.
        
        :param      parent | <QtGui.QWidget>
                    option | <QtGui.QStyleOption>
                    index  | <QtGui.QModelIndex>
        
        :return     <QWidget> || None
        """
        if index.column() != 1:
            return None
        
        editor = QtGui.QComboBox(parent)
        
        # load the levels
        items = sorted(XLoggerWidget.LoggingMap.items())
        for i, (level, data) in enumerate(items):
            editor.addItem(projex.text.pretty(data[0]))
            editor.setItemData(i, wrapVariant(level))
        
        return editor

    def setEditorData(self, editor, index):
        """
        Updates the editor with the model data.
        
        :param      editor | <QtGui.QWidget>
                    index  | <QtGui.QModelIndex>
        """
        data = unwrapVariant(index.data())
        editor.setCurrentIndex(editor.findText(data))

    def setModelData(self, editor, model, index):
        """
        Updates the item with the new data value.
        
        :param      editor  | <QtGui.QWidget>
                    model   | <QtGui.QModel>
                    index   | <QtGui.QModelIndex>
        """
        value = editor.currentText()
        model.setData(index, wrapVariant(value))

#----------------------------------------------------------------------

class XLoggerTreeWidget(XTreeWidget):
    LoggingMap = XLoggerWidget.LoggingMap
    
    def __init__(self, parent=None):
        super(XLoggerTreeWidget, self).__init__(parent, XLoggerDelegate)
        
        # define custom properties
        self._loggerWidget = None
        
        # setup the look for the loggers
        self.setShowGrid(False)
        self.setArrowStyle(True)
        self.setColumns(['Logger', 'Level'])
        
        header = self.header()
        header.setResizeMode(0, header.Stretch)
        header.setResizeMode(1, header.Fixed)
        header.setStretchLastSection(False)
        
        self.setColumnWidth(1, 120)
        
        # create connections
        self.itemChanged.connect(self.updateLoggerState)

    def loggerWidget(self):
        return self._loggerWidget

    def reloadLoggers(self):
        # do NOT save loggers in designer
        if 'designer' in sys.executable:
            return
        
        self.blockSignals(True)
        self.clear()
        root = XLoggerTreeWidgetItem('root', parent=self)
        all_loggers = sorted(logging.root.manager.loggerDict.keys())
        mapped = {}
        
        for logger in all_loggers:
            parent_name, _, name = logger.rpartition('.')
            parent = mapped.get(parent_name, root)
            
            item = XLoggerTreeWidgetItem(logger, parent)
            if item.checkState(0) == QtCore.Qt.Checked:
                item.ensureVisible()
            mapped[logger] = item
        self.blockSignals(False)

    def showEvent(self, event):
        super(XLoggerTreeWidget, self).showEvent(event)
        
        self.reloadLoggers()

    def setLoggerWidget(self, widget):
        self._loggerWidget = widget

    def updateLoggerState(self, item, column):
        self.blockSignals(True)
        if column == 0 and item.checkState(0) == QtCore.Qt.Unchecked:
            level = logging.NOTSET
        else:
            level = getattr(logging, str(item.text(1)).upper(), logging.INFO)
        
        self._loggerWidget.setLoggerLevel(item.logger(), level)
        item.updateUi()
        self.blockSignals(False)
