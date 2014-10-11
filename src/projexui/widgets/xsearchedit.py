""" Defines a search edit for the line edit. """

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

from projexui import resources
from xqt import QtCore, QtGui
from .xlineedit import XLineEdit
from .xtoolbutton import XToolButton

class XSearchEdit(XLineEdit):
    def __init__(self, parent=None):
        super(XSearchEdit, self).__init__(parent)
        
        # setup default properties
        self.setHint('enter search')
        self.setIcon(QtGui.QIcon(resources.find('img/search.png')))
        self.setCornerRadius(8)
        
        # setup custom properties
        self._cancelButton = XToolButton(self)
        self._cancelButton.setIcon(QtGui.QIcon(resources.find('img/remove_dark.png')))
        self._cancelButton.setToolTip('Clear Search Text')
        self._cancelButton.setShadowed(True)
        self._cancelButton.hide()
        self.addButton(self._cancelButton, QtCore.Qt.AlignRight)
        
        # create connections
        self._cancelButton.clicked.connect(self.clear)
        self.textChanged.connect(self.toggleCancelButton)
    
    def cancelButton(self):
        """
        Returns the cancel button associated with this edit.
        
        :return     <QToolButton>
        """
        return self.cancelButton()
    
    def toggleCancelButton(self):
        """
        Toggles the visibility for the cancel button based on the current
        text.
        """
        self._cancelButton.setVisible(self.text() != '')

__designer_plugins__ = [XSearchEdit]