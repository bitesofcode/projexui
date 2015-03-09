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
from projexui.widgets.xlogrecordwidget import XLogRecordWidget

class XLogRecordView(XView):
    def __init__(self, parent):
        super(XLogRecordView, self).__init__(parent)
        
        # define custom properties
        self._logger = XLogRecordWidget(self)
        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._logger)
        self.setLayout(layout)

    def closeEvent(self, event):
        self._logger.cleanup()
        
        super(XLogRecordView, self).closeEvent(event)

    def logger(self):
        """
        Returns the logger for this view.
        
        :return     <projexui.widgets.xlogrecordwidget.XLogRecordWidget>
        """
        return self._logger
    
    def restoreXml(self, xml):
        self._logger.restoreXml(xml)
    
    def saveXml(self, xml):
        self._logger.saveXml(xml)

XLogRecordView.setViewName('Logger')