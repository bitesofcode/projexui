#!/usr/bin/python

""" Embeds the XConsoleView as a widget into a status bar that can be used \
    in QMainWindows.  """

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

from projexui.qt.QtGui import QStatusBar, QHBoxLayout, QSizeGrip

from projex.lazymodule import LazyModule
import projexui.resources
console = LazyModule('projexui.views.xconsoleview')

class XConsoleStatusBar(QStatusBar):
    """ """
    __designer_icon__ = projexui.resources.find('img/ui/console.png')
    
    def __init__(self, parent=None):
        super(XConsoleStatusBar, self).__init__( parent )
        
        # define custom properties
        self._console = console.XConsoleView(self)
        self.insertPermanentWidget(0, self._console, 1)
        
        widget = self.findChildren(QSizeGrip)[0]
        widget.setFixedWidth(0)
        
        # set default properties
        self.setFixedHeight(28)
        self.layout().setContentsMargins(2, 2, 2, 2)
        
        # create connections
        #self._console.lockToggled.connect( self.adjustConsoleSize )
    
    def adjustConsoleSize( self ):
        """
        Updates the status bar's height to match the console.
        """
        if ( self._console.isLocked() ):
            self.setFixedHeight(28)
        else:
            self.setFixedHeight( 300 )
    
    def showMessage( self, msg ):
        """
        Shows the message in the console window.
        
        :param      msg | <str>
        """
        self._console.console().information(msg)

__designer_plugins__ = [XConsoleStatusBar]