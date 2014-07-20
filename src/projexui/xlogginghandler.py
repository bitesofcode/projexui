#!/usr/bin/python

"""
Defines a QObject that allows for signal emission for loggers.
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

import logging
from xqt import QtCore

class XLoggingDispatch(QtCore.QObject):
    # define signals
    criticalLogged = QtCore.Signal(str)
    errorLogged = QtCore.Signal(str)
    debugLogged = QtCore.Signal(str)
    messageLogged = QtCore.Signal(int, str)
    infoLogged = QtCore.Signal(str)
    warningLogged = QtCore.Signal(str)
    recordLogged = QtCore.Signal(logging.LogRecord)

#----------------------------------------------------------------------

class XLoggingHandler(logging.Handler):
    def __init__(self, parent):
        logging.Handler.__init__(self)
        
        # create the dispatcher
        self._dispatch = XLoggingDispatch(parent)
        self._formatter = logging.Formatter()
        self._formatter._fmt = '[%(levelname)s] %(name)s: %(message)s'
        
        # create connections
        self._dispatch.destroyed.connect(self.close)

    def close(self):
        """
        Closes down this handler.
        """
        self._dispatch = None
        
        super(XLoggingHandler, self).close()

    def dispatch(self):
        """
        Returns the dispatcher object for this handler.
        
        :return     <projexui.xlogginghandler.XLoggingDispatch>
        """
        return self._dispatch

    def emit(self, record):
        """
        Emits the signal for this record through the dispatch
        element.
        
        :param      record | <logging.LogRecord>
        """
        disp = self.dispatch()
        if disp is None:
            return
        
        msg = self.format(record)
        
        # emit the dispatch signals
        disp.recordLogged.emit(record)
        disp.messageLogged.emit(record.levelno, msg)
        
        if record.levelno == logging.DEBUG:
            disp.debugLogged.emit(msg)
        elif record.levelno == logging.INFO:
            disp.infoLogged.emit(msg)
        elif record.levelno == logging.WARN:
            disp.warningLogged.emit(msg)
        elif record.levelno == logging.ERROR:
            disp.errorLogged.emit(msg)
        elif record.levelno == logging.CRITICAL:
            disp.criticalLogged.emit(msg)

    def format(self, record):
        """
        Formats the inputed log record to the return string.
        
        :param      record | <logging.LogRecord>
        """
        return self._formatter.format(record)

    def formatText(self):
        """
        Returns the formatter text for this handler.
        
        :return     <str>
        """
        return self._formatter._fmt
    
    def setFormatText(self, text):
        """
        Sets the format string to be used with this handler.
        
        :param      text | <str>
        """
        self._formatter._fmt = text

