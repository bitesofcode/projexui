#!/usr/bin/python

""" Creates a splash screen that is linked to the python logging system. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

#------------------------------------------------------------------------------

import logging
import weakref

from projexui.qt.QtCore import Qt
from projexui.qt.QtGui  import QSplashScreen, QColor

logger = logging.getLogger()

class XSplashHandler(logging.Handler):
    """ Custom class for handling error exceptions via the logging system,
        based on the logging level. """
    
    def __init__( self, splash ):
        logging.Handler.__init__(self)
        
        self._splash = splash
        self._formatter = logging.Formatter()
        
    def emit( self, record ):
        """ 
        Throws an error based on the information that the logger reported,
        given the logging level.
        
        :param      record | <logging.LogRecord>
        """
        msg   = self._formatter.format(record)
        align = self._splash.textAlignment()
        fg    = self._splash.textColor()
        
        self._splash.showMessage(msg, align, fg)

class XLoggerSplashScreen(QSplashScreen):
    """
    Creates a simple loading screen that will display the logger information \
    during startup.
    """
    def __init__(self, *args):
        super(XLoggerSplashScreen, self).__init__(*args)
        
        # update the font info
        font = self.font()
        font.setPointSize(10)
        font.setBold(True)
        self.setFont(font)
        
        # define custom properties
        self._handler       = XSplashHandler(self)
        self._textAlignment = Qt.AlignLeft | Qt.AlignBottom
        self._textColor     = QColor('black')
        
        logger.addHandler(self._handler)
    
    def closeEvent(self, event):
        logger.removeHandler(self._handler)
        
        super(XLoggerSplashScreen, self).closeEvent(event)
    
    def setTextColor( self, textColor ):
        self._textColor = textColor
    
    def setTextAlignment( self, alignment ):
        self._textAlignment = alignment
    
    def textAlignment( self ):
        return self._textAlignment
    
    def textColor( self ):
        return self._textColor

