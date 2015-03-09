""" Defines the XUrlWidget class """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software, LLC'
__license__         = 'LGPL'

__maintainer__      = 'Projex Software, LLC'
__email__           = 'team@projexsoftware.com'

import webbrowser

from projex.text import nativestring

from projexui.qt import Signal,\
                        Slot,\
                        Property

from projexui.qt.QtCore import Qt
from projexui.qt.QtGui import QWidget,\
                              QHBoxLayout,\
                              QIcon,\
                              QToolButton

from projexui.widgets.xlineedit import XLineEdit
from projexui import resources

class XUrlWidget(QWidget):
    urlChanged = Signal(str)
    urlEdited  = Signal()
    
    def __init__( self, parent ):
        super(XUrlWidget, self).__init__(parent)
        
        # define the interface
        self._urlEdit      = XLineEdit(self)
        self._urlButton    = QToolButton(self)
        
        self._urlButton.setAutoRaise(True)
        self._urlButton.setIcon(QIcon(resources.find('img/web.png')))
        self._urlButton.setToolTip('Browse Link')
        self._urlButton.setFocusPolicy(Qt.NoFocus)
        
        self._urlEdit.setHint('http://')
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._urlEdit)
        layout.addWidget(self._urlButton)
        
        self.setLayout(layout)
        self.setFocusPolicy(Qt.StrongFocus)
        
        # create connections
        self._urlEdit.textChanged.connect(self.urlChanged)
        self._urlEdit.textEdited.connect(self.urlEdited)
        self._urlButton.clicked.connect(self.browse)
    
    def blockSignals( self, state ):
        """
        Blocks the signals for this widget and its sub-parts.
        
        :param      state | <bool>
        """
        super(XUrlWidget, self).blockSignals(state)
        self._urlEdit.blockSignals(state)
        self._urlButton.blockSignals(state)
    
    def browse( self ):
        """
        Brings up a web browser with the address in a Google map.
        """
        webbrowser.open(self.url())
    
    def hint( self ):
        """
        Returns the hint associated with this widget.
        
        :return     <str>
        """
        return self._urlEdit.hint()
    
    def lineEdit( self ):
        """
        Returns the line edit linked with this widget.
        
        :return     <XLineEdit>
        """
        return self._urlEdit
    
    def setFocus(self):
        """
        Sets the focus for this widget on its line edit.
        """
        self._urlEdit.setFocus()
    
    @Slot(str)
    def setHint( self, hint ):
        """
        Sets the hint associated with this widget.
        
        :param      hint | <str>
        """
        self._urlEdit.setHint(hint)
    
    @Slot(str)
    def setUrl( self, url ):
        """
        Sets the url for this widget to the inputed url.
        
        :param      url | <str>
        """
        self._urlEdit.setText(nativestring(url))
    
    def url( self ):
        """
        Returns the current url from the edit.
        
        :return     <str>
        """
        return nativestring(self._urlEdit.text())
    
    x_hint   = Property(str, hint, setHint)
    x_url    = Property(str, url, setUrl)

__designer_plugins__ = [XUrlWidget]