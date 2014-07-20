#!/usr/bin/python

""" Defines a dialog used by a view system to break out views into floating
    windows. """

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

from projexui.qt.QtCore import Qt
from projexui.qt.QtGui import QDialog,\
                              QVBoxLayout
                        
from projexui.widgets.xviewwidget import XViewWidget

class XViewDialog(QDialog):
    def __init__( self, parent=None, viewTypes=None):
        super(XViewDialog, self).__init__(parent)
        
        # create a new view widget for this dialog
        self._viewWidget = XViewWidget(self)
        if viewTypes != None:
            self._viewWidget.setViewTypes(viewTypes)
        
        # create the layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._viewWidget)
        
        self.setLayout(layout)
        self.setWindowTitle('Detached Views')
        self.setAttribute(Qt.WA_DeleteOnClose)
    
    def closeEvent(self, event):
        """
        Checks to make sure that the view widget can be properly closed.
        
        :param      event | <QCloseEvent>
        """
        if not self.viewWidget().canClose():
            event.ignore()
        else:
            super(XViewDialog, self).closeEvent(event)
    
    def setVisible( self, state ):
        """
        Updates the view widget when the dialog is set to visible.
        
        :param      state | <bool>
        """
        super(XViewDialog, self).setVisible(state)
        
        if ( state ):
            self.viewWidget().currentPanel().adjustButtons()
    
    def viewWidget( self ):
        """
        Returns the view widget linked to this dialog.
        
        :return     <XViewWidget>
        """
        return self._viewWidget