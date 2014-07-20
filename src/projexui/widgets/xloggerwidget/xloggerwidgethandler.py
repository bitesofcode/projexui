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
from projexui.xlogginghandler import XLoggingHandler

class XLoggerWidgetHandler(XLoggingHandler):
    """ Custom class for handling error exceptions via the logging system,
        based on the logging level. """
    
    def __init__(self, parent):
        super(XLoggerWidgetHandler, self).__init__(parent)
        
        # define custom properties
        self._loggerLevels  = {}
        self._activeLevels = []
        self._recordQueue = []
        
        # process all notifications, this will handle
        # per logger vs. per handler
        self.setLevel(logging.DEBUG)
    
    def activeLevels(self):
        """
        Returns the active levels that should be displayed for this handler.
        
        :return     [<int>, ..]
        """
        return self._activeLevels
    
    def emit(self, record):
        """ 
        Throws an error based on the information that the logger reported,
        given the logging level.
        
        :param      record | <logging.LogRecord>
        """
        # if we've already processed this record, ignore it
        if record in self._recordQueue:
            return
        
        if self._activeLevels and not record.levelno in self._activeLevels:
            return
        
        name = record.name
        lvl = self.loggerLevel(name)
        
        # don't process this log
        if lvl > record.levelno:
            return
        
        self._recordQueue.insert(0, record)
        self._recordQueue = self._recordQueue[:10]
        
        # emit the change
        super(XLoggerWidgetHandler, self).emit(record)
    
    def loggerLevel(self, logger):
        """
        Returns the level for the inputed logger.
        
        :param      logger | <str>
        
        :return     <int>
        """
        try:
            return self._loggerLevels[logger]
        except KeyError:
            items = sorted(self._loggerLevels.items())
            for key, lvl in items:
                if logger.startswith(key):
                    return lvl
            return logging.NOTSET
    
    def loggerLevels(self):
        """
        Returns the logger levels for this handler.
        
        :return     {<str> logger: <int> level, ..}
        """
        return self._loggerLevels
    
    def setActiveLevels(self, levels):
        """
        Sets the active levels that will be emitted for this handler.
        
        :param      levels | [<int>, ..]
        """
        self._activeLevels = levels
    
    def setLoggerLevel(self, logger, level):
        """
        Sets the level to log the inputed logger at.
        
        :param      logger | <str>
                    level  | <int>
        """
        if logger == 'root':
            _log = logging.getLogger()
        else:
            _log = logging.getLogger(logger)
        
        _log.setLevel(level)
        
        if level == logging.NOTSET:
            self._loggerLevels.pop(logger, None)
        else:
            self._loggerLevels[logger] = level

