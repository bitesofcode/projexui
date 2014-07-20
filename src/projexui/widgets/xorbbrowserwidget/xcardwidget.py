""" Defines the base card widget that will be used when generating cards
    for the browser system through the factory.
"""

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software, LLC'
__license__         = 'LGPL'

__maintainer__      = 'Projex Software, LLC'
__email__           = 'team@projexsoftware.com'

from projexui.qt.QtCore import QSize

from projexui.qt.QtGui import QWidget,\
                              QIcon,\
                              QLabel,\
                              QHBoxLayout

from projexui.widgets.xiconbutton import XIconButton

import projexui

class XAbstractCardWidget(QWidget):
    def __init__( self, parent ):
        super(XAbstractCardWidget, self).__init__(parent)
        
        # define custom properties
        self._record = None
    
    def browserWidget( self ):
        """
        Returns the browser widget this card is linked to.
        
        :return     <XOrbBrowserWidget> || None
        """
        from projexui.widgets.xorbbrowserwidget import XOrbBrowserWidget
        return projexui.ancestor(self, XOrbBrowserWidget)
    
    def record( self ):
        """
        Returns the record linked with this widget.
        
        :return     <orb.Table>
        """
        return self._record
    
    def setRecord( self, record ):
        """
        Sets the record linked with this widget.
        
        :param      record | <orb.Table>
        """
        self._record = record
    
#------------------------------------------------------------------------------

class XBasicCardWidget(XAbstractCardWidget):
    def __init__( self, parent ):
        super(XBasicCardWidget, self).__init__(parent)
        
        # define the interface
        self._thumbnailButton = XIconButton(self)
        self._thumbnailButton.setIconSize(QSize(64, 64))
        
        self._titleLabel      = QLabel(self)
        
        layout = QHBoxLayout()
        layout.addWidget(self._thumbnailButton)
        layout.addWidget(self._titleLabel)
        self.setLayout(layout)
    
    def setRecord( self, record ):
        """
        Sets the record that is linked with this widget.
        
        :param      record | <orb.Table>
        """
        super(XBasicCardWidget, self).setRecord(record)
        
        browser = self.browserWidget()
        if ( not browser ):
            return
        
        factory = browser.factory()
        if ( not factory ):
            return
        
        self._thumbnailButton.setIcon(factory.thumbnail(record))
        self._titleLabel.setText(factory.thumbnailText(record))