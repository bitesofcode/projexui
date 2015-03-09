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

#------------------------------------------------------------------------------

import logging

from projex.text import nativestring
from projex.decorators import deprecatedmethod

from xqt import QtCore, QtGui, wrapVariant, unwrapVariant

import projex.text
from projexui import resources
from projexui.widgets.xpopupbutton import XPopupButton

from .xloggercolorset import XLoggerColorSet
from .xloggercontrols import XLoggerControls
from .xloggerwidgethandler import XLoggerWidgetHandler

#------------------------------------------------------------------------------

class XLoggerWidget(QtGui.QTextEdit):
    __designer_icon__ = resources.find('img/log/info.png')
    
    LoggingMap = {
        logging.DEBUG:    ('debug',    resources.find('img/log/bug.png')),
        logging.INFO:     ('info',     resources.find('img/log/info.png')),
        logging.SUCCESS:  ('success',  resources.find('img/log/success.png')),
        logging.WARN:     ('warning',  resources.find('img/log/warning.png')),
        logging.ERROR:    ('error',    resources.find('img/log/error.png')),
        logging.CRITICAL: ('critical', resources.find('img/log/critical.png')),
    }
    
    messageLogged       = QtCore.Signal(int, unicode)
    
    """ Defines the main logger widget class. """
    def __init__(self, parent):
        super(XLoggerWidget, self).__init__(parent)
        
        # set standard properties
        self.setReadOnly(True)
        self.setLineWrapMode(XLoggerWidget.NoWrap)
        
        # define custom properties
        self._clearOnClose  = True
        self._handler       = XLoggerWidgetHandler(self)
        self._currentMode   = 'standard'
        self._blankCache    = ''
        self._mutex         = QtCore.QMutex()
        self._loggers       = set()
        self._configurable  = True
        self._destroyed     = False
        
        # define the popup button for congfiguration
        self._configButton  = XPopupButton(self)
        self._configButton.setIcon(QtGui.QIcon(resources.find('img/config.png')))
        self._configButton.setShadowed(True)
        
        popup = self._configButton.popupWidget()
        popup.setShowTitleBar(False)
        popup.setResizable(False)
        
        bbox = popup.buttonBox()
        bbox.clear()
        bbox.addButton(QtGui.QDialogButtonBox.Ok)
        
        # set to a monospace font
        font = QtGui.QFont('Courier New')
        font.setPointSize(9)
        self.setFont(font)
        metrics = QtGui.QFontMetrics(font)
        self.setTabStopWidth(4 * metrics.width(' '))
        self.setAcceptRichText(False)
        
        # determine whether or not to use the light or dark configuration
        palette = self.palette()
        base    = palette.color(palette.Base)
        avg     = (base.red() + base.green() + base.blue()) / 3.0
        
        if avg < 160:
            colorSet = XLoggerColorSet.darkScheme()
        else:
            colorSet = XLoggerColorSet.lightScheme()
        
        self._colorSet = colorSet
        palette.setColor(palette.Text, colorSet.color('Standard'))
        palette.setColor(palette.Base, colorSet.color('Background'))
        self.setPalette(palette)
        
        # create the logger tree widget
        controls = XLoggerControls(self)
        self._configButton.setCentralWidget(controls)
        self._configButton.setDefaultAnchor(popup.Anchor.TopRight)
        
        # create connections
        self._handler.dispatch().messageLogged.connect(self.log)
        self.destroyed.connect(self.markDestroyed)
    
    def activeLevels(self):
        """
        Returns the active levels that will be displayed for this widget.
        
        :return     [<int>, ..]
        """
        return self._handler.activeLevels()
    
    def addLogger(self, logger, level=logging.INFO):
        """
        Adds the inputed logger to the list of loggers that are being tracked
        with this widget.
        
        :param      logger | <logging.Logger> || <str>
                    level  | <logging.LEVEL>
        """
        if isinstance(logger, logging.Logger):
            logger = logger.name
        
        if logger in self._loggers:
            return
        
        # allow the handler to determine the level for this logger
        if logger == 'root':
            _log = logging.getLogger()
        else:
            _log = logging.getLogger(logger)
        
        _log.addHandler(self.handler())
        
        self._loggers.add(logger)
        self.handler().setLoggerLevel(logger, level)
    
    def cleanup(self):
        self._destroyed = True
        
        try:
            self._handler.dispatch().messageLogged.disconnect(self.log)
            self.destroyed.disconnect(self.markDestroyed)
        except StandardError:
            pass
        
        self.markDestroyed()
    
    def clear(self):
        super(XLoggerWidget, self).clear()
        
        self._currentMode = 'standard'
    
    def clearLoggers(self, logger):
        """
        Removes the inputed logger from the set for this widget.
        
        :param      logger | <str> || <logging.Logger>
        """
        for logger in self._loggers:
            if logger == 'root':
                logger = logging.getLogger()
            else:
                logger = logging.getLogger(logger)
            logger.removeHandler(self.handler())
        
        self._loggers = set()
    
    def clearOnClose(self):
        """
        Returns whether or not this widget should clear the link to its \
        logger when it closes.
        
        :return     <bool>
        """
        return self._clearOnClose
    
    def color(self, key):
        """
        Returns the color value for the given key for this console.
        
        :param      key | <unicode>
        
        :return     <QtGui.QColor>
        """
        if type(key) == int:
            key = self.LoggingMap.get(key, ('NotSet', ''))[0]
        name = nativestring(key).capitalize()
        return self._colorSet.color(name)
    
    def colorSet(self):
        """
        Returns the colors used for this console.
        
        :return     <XLoggerColorSet>
        """
        return self._colorSet
    
    def critical(self, msg):
        """
        Logs a critical message to the console.
        
        :param      msg | <unicode>
        """
        self.log(logging.CRITICAL, msg)
    
    def currentMode(self):
        """
        Returns the current mode that the console is in for coloring.
        
        :return     <unicode>
        """
        return self._currentMode
    
    def debug(self, msg):
        """
        Inserts a debug message to the current system.
        
        :param      msg | <unicode>
        """
        self.log(logging.DEBUG, msg)
    
    def error(self, msg):
        """
        Inserts an error message to the current system.
        
        :param      msg | <unicode>
        """
        self.log(logging.ERROR, msg)
    
    @deprecatedmethod('2.1', 'Use critical instead (same level as FATAL)')
    def fatal(self, msg):
        """
        Logs a fatal message to the system.
        
        :param      msg | <unicode>
        """
        self.log(logging.FATAL, msg)
    
    def formatText(self):
        """
        Returns the text that is used to format entries that are logged
        to this handler.
        
        :return     <str>
        """
        return self.handler().formatText()
    
    def handler(self):
        """
        Returns the logging handler that is linked to this widget.
        
        :return     <XLoggerWidgetHandler>
        """
        return self._handler
    
    def hasLogger(self, logger):
        """
        Returns whether or not the inputed logger is tracked by this widget.
        
        :param      logger | <str> || <logging.Logger>
        """
        if isinstance(logger, logging.Logger):
            logger = logging.name
        
        return logger in self._loggers
    
    def information(self, msg):
        """
        Inserts an information message to the current system.
        
        :param      msg | <unicode>
        """
        self.log(logging.INFO, msg)
    
    def isConfigurable(self):
        """
        Returns whether or not the user can configure the loggers associated
        with this widget.
        
        :return     <bool>
        """
        return self._configurable
    
    def isDestroyed(self):
        return self._destroyed
    
    @deprecatedmethod('2.1', 'Use the loggerLevel now.')
    def isLoggingEnabled(self, level):
        """
        Returns whether or not logging is enabled for the given level.
        
        :param      level | <int>
        """
        return False
    
    def log(self, level, msg):
        """
        Logs the inputed message with the given level.
        
        :param      level | <int> | logging level value
                    msg   | <unicode>
        
        :return     <bool> success
        """
        if self.isDestroyed():
            return
        
        locker = QtCore.QMutexLocker(self._mutex)
        try:
            msg = projex.text.nativestring(msg)
            self.moveCursor(QtGui.QTextCursor.End)
            self.setCurrentMode(level)
            if self.textCursor().block().text():
                self.insertPlainText('\n')
            self.insertPlainText(msg.lstrip('\n\r'))
            self.scrollToEnd()
        except RuntimeError:
            return
        
        if not self.signalsBlocked():
            self.messageLogged.emit(level, msg)
        
        return True
    
    @deprecatedmethod('2.1', 'Loggers will not be explicitly set anymore.  Use loggerLevel instead.')
    def logger(self):
        """
        Returns the logger instance that this widget will monitor.
        
        :return     <logging.Logger> || None
        """
        return None
    
    def loggerLevel(self, logger='root'):
        """
        Returns the logging level for the inputed logger.
        
        :param      logger | <str> || <logging.Logger>
        """
        if isinstance(logger, logging.Logger):
            logger = logger.name
        
        return self.handler().loggerLevel(logger)
    
    def loggerLevels(self):
        """
        Returns a dictionary of the set logger levels for this widget.
        
        :return     {<str> logger: <int> level, ..}
        """
        return self._handler.loggerLevels()
    
    def markDestroyed(self):
        self._destroyed = True
    
    def resizeEvent(self, event):
        super(XLoggerWidget, self).resizeEvent(event)
        
        size = event.size()
        self._configButton.move(size.width() - 22, 3)
    
    def removeLogger(self, logger):
        """
        Removes the inputed logger from the set for this widget.
        
        :param      logger | <str> || <logging.Logger>
        """
        if isinstance(logger, logging.Logger):
            logger = logger.name
        
        if logger in self._loggers:
            self._loggers.remove(logger)
            if logger == 'root':
                logger = logging.getLogger()
            else:
                logger = logging.getLogger(logger)
            
            logger.removeHandler(self.handler())
    
    def restoreSettings(self, settings):
        """
        Restores the settings for this logger from the inputed settings.
        
        :param      <QtCore.QSettings>
        """
        val = unwrapVariant(settings.value('format'))
        if val:
            self.setFormatText(val)
        
        levels = unwrapVariant(settings.value('levels'))
        if levels:
            self.setActiveLevels(map(int, levels.split(',')))
        
        logger_levels = unwrapVariant(settings.value('loggerLevels'))
        if logger_levels:
            for key in logger_levels.split(','):
                logger, lvl = key.split(':')
                lvl = int(lvl)
                self.setLoggerLevel(logger, lvl)

    def saveSettings(self, settings):
        """
        Saves the logging settings for this widget to the inputed settings.
        
        :param      <QtCore.QSettings>
        """
        lvls = []
        for logger, level in self.loggerLevels().items():
            lvls.append('{0}:{1}'.format(logger, level))
        
        settings.setValue('format', wrapVariant(self.formatText()))
        settings.setValue('levels', ','.join(map(str, self.activeLevels())))
        settings.setValue('loggerLevels', ','.join(lvls))
    
    def scrollToEnd(self):
        """
        Scrolls to the end for this console edit.
        """
        vsbar = self.verticalScrollBar()
        vsbar.setValue(vsbar.maximum())
        
        hbar = self.horizontalScrollBar()
        hbar.setValue(0)
    
    def setActiveLevels(self, levels):
        """
        Defines the levels for this widgets visible/processed levels.
        
        :param      levels | [<int>, ..]
        """
        self._handler.setActiveLevels(levels)
    
    def setClearOnClose(self, state):
        """
        Sets whether or not this widget should clear the logger link on close.
        
        :param      state | <bool>
        """
        self._clearOnClose = state
    
    def setColor(self, key, value):
        """
        Sets the color value for the inputed color.
        
        :param      key     | <unicode>
                    value   | <QtGui.QColor>
        """
        key = nativestring(key).capitalize()
        self._colorSet.setColor(key, value)
        
        # update the palette information
        if ( key == 'Background' ):
            palette = self.palette()
            palette.setColor( palette.Base, value )
            self.setPalette(palette)
    
    def setColorSet(self, colorSet):
        """
        Sets the colors for this console to the inputed collection.
        
        :param      colors | <XLoggerColorSet>
        """
        self._colorSet = colorSet
        
        # update the palette information
        palette = self.palette()
        palette.setColor( palette.Text, colorSet.color('Standard') )
        palette.setColor( palette.Base, colorSet.color('Background') )
        self.setPalette(palette)
    
    def setConfigurable(self, state):
        """
        Sets whether or not this logger widget is configurable.
        
        :param      state | <bool>
        """
        self._configurable = state
        self._configButton.setVisible(state)
    
    def setCurrentMode(self, mode):
        """
        Sets the current color mode for this console to the inputed value.
        
        :param      mode | <unicode>
        """
        if type(mode) == int:
            mode = self.LoggingMap.get(mode, ('standard', ''))[0]
            
        if mode == self._currentMode:
            return
            
        self._currentMode = mode
        color = self.color(mode)
        if not color.isValid():
            return
            
        format = QtGui.QTextCharFormat()
        format.setForeground(color)
        self.setCurrentCharFormat(format)
    
    def setFormatText(self, text):
        """
        Sets the format text for this logger to the inputed text.
        
        :param      text | <str>
        """
        self.handler().setFormatText(text)
    
    @deprecatedmethod('2.1', 'Use the setLoggerLevel method now')
    def setLoggingEnabled(self, level, state):
        """
        Sets whether or not this widget should log the inputed level amount.
        
        :param      level | <int>
                    state | <bool>
        """
        pass
    
    def setLoggerLevel(self, logger, level):
        """
        Returns the logging level for the inputed logger.
        
        :param      logger | <logging.Logger> || <str>
                    level  | <logging.LEVEL>
        """
        if level == logging.NOTSET:
            self.removeLogger(logger)
            return
            
        if isinstance(logger, logging.Logger):
            logger = logger.name
        
        if not logger in self._loggers:
            self.addLogger(logger, level)
        else:
            self.handler().setLoggerLevel(logger, level)
    
    @deprecatedmethod('2.1', 'You should now use the addLogger method.')
    def setLogger(self, logger):
        """
        Sets the logger instance that this widget will monitor.
        
        :param      logger  | <logging.Logger>
        """
        pass
    
    @deprecatedmethod('2.1', 'You should now use the setFormatText method.')
    def setShowDetails(self, state):
        pass
    
    @deprecatedmethod('2.1', 'You should now use the setFormatText method.')
    def setShowLevel(self, state):
        pass

    @deprecatedmethod('2.1', 'You should now use the formatText method.')
    def showDetails(self):
        pass
    
    @deprecatedmethod('2.1', 'You should now use the formatText method.')
    def showLevel(self):
        pass
    
    def success(self, msg):
        """
        Logs the message for this widget.
        
        :param      msg | <str>
        """
        self.log(logging.SUCCESS, msg)
    
    def warning(self, msg):
        """
        Logs a warning message to the system.
        
        :param      msg | <unicode>
        """
        self.log(logging.WARNING, msg)
    
    x_configurable = QtCore.Property(bool, isConfigurable, setConfigurable)
    x_formatText = QtCore.Property(str, formatText, setFormatText)

