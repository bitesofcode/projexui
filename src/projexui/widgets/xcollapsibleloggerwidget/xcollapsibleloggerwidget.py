#!/usr/bin/python

""" Defines a view for the XViewWidget based on the XConsoleEdit. """

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

from xqt import QtCore, QtGui, unwrapVariant

import projexui

class XCollapsibleLoggerWidget(QtGui.QWidget):
    """ """
    def __init__(self, parent=None):
        super(XCollapsibleLoggerWidget, self).__init__(parent)
        
        # load the user interface
        projexui.loadUi(__file__, self)
        
        # define custom properties
        self._collapsed = False
        self._animated = True
        self._expandedHeight = 250
        
        # animation properties
        self._startHeight = 0
        self._targetHeight = 0
        self._targetPercent = 0
        
        self.uiFeedbackLBL.setFont(self.uiLoggerWGT.font())
        
        # set default properties
        self.setCollapsed(True)
        
        # create connections
        self.uiShowBTN.clicked.connect(self.expand)
        self.uiHideBTN.clicked.connect(self.collapse)
        self.uiLoggerWGT.messageLogged.connect(self.updateFeedback)

    @QtCore.Slot()
    def clear(self):
        self.uiLoggerWGT.clear()
        self.uiFeedbackLBL.setText('')

    @QtCore.Slot()
    def collapse(self):
        self.setCollapsed(True)

    def critical(self, msg):
        """
        Logs a critical message to the console.
        
        :param      msg | <unicode>
        """
        self.uiLoggerWGT.critical(msg)
    
    def debug(self, msg):
        """
        Inserts a debug message to the current system.
        
        :param      msg | <unicode>
        """
        self.uiLoggerWGT.debug(msg)
    
    def error(self, msg):
        """
        Inserts an error message to the current system.
        
        :param      msg | <unicode>
        """
        self.uiLoggerWGT.error(msg)
    
    @QtCore.Slot()
    def expand(self):
        self.setCollapsed(False)

    def expandedHeight(self):
        return self._expandedHeight

    def fatal(self, msg):
        """
        Logs a fatal message to the system.
        
        :param      msg | <unicode>
        """
        self.uiLoggerWGT.fatal(msg)
    
    def formatText(self):
        return self.uiLoggerWGT.formatText()
    
    def information(self, msg):
        """
        Inserts an information message to the current system.
        
        :param      msg | <unicode>
        """
        self.uiLoggerWGT.information(msg)
    
    def isAnimated(self):
        return self._animated

    def isCollapsed(self):
        """
        Returns whether or not this logger widget is in the collapsed
        state.
        
        :return     <bool>
        """
        return self._collapsed

    def isConfigurable(self):
        """
        Returns whether or not this widget can be configured by the user.
        
        :return     <bool>
        """
        return self.uiLoggerWGT.isConfigurable()

    def log(self, level, msg):
        """
        Logs the inputed message with the given level.
        
        :param      level | <int> | logging level value
                    msg   | <unicode>
        
        :return     <bool> success
        """
        return self.uiLoggerWGT.log(level, msg)

    def logger(self):
        """
        Returns the logger associated with this widget.
        
        :return     <logging.Logger>
        """
        return self.uiLoggerWGT.logger()

    def loggerLevel(self, logger):
        return self.uiLoggerWGT.loggerLevel(logger)

    def loggerWidget(self):
        return self.uiLoggerWGT

    def setAnimated(self, state):
        self._animated = state

    @QtCore.Slot(bool)
    def setExpanded(self, state):
        self.setCollapsed(not state)

    def setExpandedHeight(self, height):
        self._expandedHeight = height

    @QtCore.Slot(bool)
    def setCollapsed(self, state):
        if self._collapsed == state:
            return
        
        self._collapsed = state
        
        # update the sizing constraints
        palette = self.palette()
        if state:
            height = 24
        else:
            height = self.expandedHeight()
        
        if self.isVisible() and self.parent() and self.isAnimated():
            # show the uncollapsed items collapsing
            if not state:
                # update the visible children based on the state
                for widget in self.children():
                    prop = unwrapVariant(widget.property('showCollapsed'))
                    if prop is not None:
                        widget.setVisible(bool(prop) == state)
            
            self._startHeight = self.height()
            self._targetHeight = height
            self._targetPercent = 0.0
            self.startTimer(10)
        else:
            # update the visible children based on the state
            for widget in self.children():
                prop = unwrapVariant(widget.property('showCollapsed'))
                if prop is not None:
                    widget.setVisible(bool(prop) == state)
            
            self.setFixedHeight(height)

    def setConfigurable(self, state):
        """
        Sets whether or not this logger widget can be configured by the user.
        
        :param      state | <bool>
        """
        self.uiLoggerWGT.setConfigurable(state)

    def setLoggerLevel(self, logger, level):
        self.uiLoggerWGT.setLoggerLevel(logger, level)

    def setFormatText(self, text):
        self.uiLoggerWGT.setFormatText(text)

    def setLogger(self, logger):
        """
        Sets the logger associated with this widget.
        
        :param     logger | <logging.Logger>
        """
        self.uiLoggerWGT.setLogger(logger)

    def timerEvent(self, event):
        self._targetPercent += 0.05
        if self._targetPercent >= 1:
            self.killTimer(event.timerId())
            self.setFixedHeight(self._targetHeight)
            
            # always show the logger widget
            if self.isCollapsed():
                # update the visible children based on the state
                for widget in self.children():
                    prop = unwrapVariant(widget.property('showCollapsed'))
                    if prop is not None:
                        widget.setVisible(bool(prop) == self.isCollapsed())
            
        else:
            delta = (self._startHeight - self._targetHeight) * self._targetPercent
            self.setFixedHeight(self._startHeight - delta)

    def updateFeedback(self, level, message):
        clr = self.uiLoggerWGT.color(level)
        palette = self.uiFeedbackLBL.palette()
        palette.setColor(palette.WindowText, clr)
        self.uiFeedbackLBL.setPalette(palette)
        self.uiFeedbackLBL.setText(message)

    def warning(self, msg):
        """
        Logs a warning message to the system.
        
        :param      msg | <unicode>
        """
        self.uiLoggerWGT.warning(msg)

    x_animated = QtCore.Property(bool, isAnimated, setAnimated)
    x_collapsed = QtCore.Property(bool, isCollapsed, setCollapsed)
    x_configurable = QtCore.Property(bool, isConfigurable, setConfigurable)
    x_expandedHeight = QtCore.Property(int, expandedHeight, setExpandedHeight)
    x_formatText = QtCore.Property(str, formatText, setFormatText)

__designer_plugins__ = [XCollapsibleLoggerWidget]