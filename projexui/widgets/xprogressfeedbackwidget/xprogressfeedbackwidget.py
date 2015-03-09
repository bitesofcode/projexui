#!/usr/bin/python

""" Creates reusable Qt widgets for various applications. """

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

from projexui.qt import QtGui, QtCore

import projexui

class XProgressFeedbackWidget(QtGui.QWidget):
    """ """
    def __init__( self, parent = None ):
        super(XProgressFeedbackWidget, self).__init__( parent )
        
        # load the user interface
        projexui.loadUi(__file__, self)
        
        # update the ui
        self._showSecondary = False
        
        self.uiLoggerEDIT.hide()
        self.setProgress(0)
        self.setSecondaryProgress(0)
        self.setShowSecondaryProgress(False)

    def progress(self):
        """
        Returns the progress value for this widget.
        
        :return     <int>
        """
        return self.uiProgressBAR.value()

    def reset(self):
        """
        Resets this widget before continuing.  This is also acheived by
        setting the progress to 0.
        """
        self.setProgress(0)

    def secondaryProgress(self):
        """
        Returns the secondary progress value for this widget.
        
        :return     <int>
        """
        return self.uiSecondaryProgressBAR.value()

    def setProgress(self, value):
        """
        Sets the progress value for this widget to the inputed value.
        
        :param      value | <int>
        """
        if value == 0:
            self.uiFeedbackLBL.setText('')
            self.uiLoggerEDIT.clear()
        
        self.uiProgressBAR.setValue(value)

    def setSecondaryProgress(self, value):
        """
        Sets the progress value for the secondary progress widget.
        
        :param      value | <int>
        """
        self.uiSecondaryProgressBAR.setValue(value)

    def setShowSecondaryProgress(self, state):
        """
        Sets whether or not to display the secondary progress widget.
        
        :param      state | <bool>
        """
        self._showSecondary = state
        self.uiSecondaryProgressBAR.setVisible(state)

    def showEvent(self, event):
        super(XProgressFeedbackWidget, self).showEvent(event)
        
        self.uiSecondaryProgressBAR.setVisible(self._showSecondary)

    def showMessage(self, level, message):
        """
        Logs the inputed message for the given level.  This will update
        both the feedback label and the details widget.
        
        :param      level   | <int>
                    message | <str>
        """
        self.uiFeedbackLBL.setText(message)
        self.uiLoggerEDIT.log(level, message)

    def showSecondaryProgress(self):
        """
        Sets whether or not to display the secondary progress widget.
        
        :param      state | <bool>
        """
        return self._showSecondary

    x_showSecondaryProgress = QtCore.Property(bool, showSecondaryProgress, setShowSecondaryProgress)

