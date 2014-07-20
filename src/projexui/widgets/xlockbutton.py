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

from xqt import QtGui

from projexui.widgets.xtoolbutton import XToolButton
from projexui import resources

class XLockButton(XToolButton):
    __designer_icon__ = resources.find('img/ui/lock.png')
    
    def __init__(self, parent=None):
        super(XLockButton, self).__init__(parent)
        
        # define custom properties
        self._lockIcon = None
        self._unlockIcon = None
        
        # set properties
        palette = self.palette()
        palette.setColor(palette.Shadow, QtGui.QColor('orange'))
        self.setPalette(palette)
        
        self.setLockIcon(resources.find('img/ui/lock.png'))
        self.setUnlockIcon(resources.find('img/ui/unlock.png'))
        self.setCheckable(True)
        self.setChecked(False)
        self.setShadowed(True)
        
        # update the icon based on the lock state
        self.toggled.connect(self.updateState)

    def lockIcon(self):
        """
        Returns the lock icon for this button.
        
        :return     <QtGui.QIcon>
        """
        return self._lockIcon

    def setChecked(self, state):
        """
        Sets whether or not this button is in its locked state.
        
        :param      state | <bool>
        """
        super(XLockButton, self).setChecked(state)
        self.updateState()

    def setLockIcon(self, icon):
        """
        Sets the lock icon for this button.
        
        :param      icon | <str> || <QtGui.QIcon>
        """
        self._lockIcon = QtGui.QIcon(icon)

    def setUnlockIcon(self, icon):
        """
        Sets the unlock icon for this button.
        
        :param      icon | <str> || <QtGui.QIcon>
        """
        self._unlockIcon = QtGui.QIcon(icon)

    def updateState(self):
        """
        Updates the icon for this lock button based on its check state.
        """
        if self.isChecked():
            self.setIcon(self.lockIcon())
            self.setToolTip('Click to unlock')
        else:
            self.setIcon(self.unlockIcon())
            self.setToolTip('Click to lock')

    def unlockIcon(self):
        """
        Returns the unlock icon for this button.
        
        :return     <QtGui.QIcon>
        """
        return self._unlockIcon

__designer_plugins__ = [XLockButton]