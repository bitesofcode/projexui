#!/usr/bin/python

""" Defines commonly used config settings for different apps. """

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

from projexui.dialogs.xconfigdialog                     import XConfigPlugin
from projexui.configs.xshortcutconfig.xshortcutwidget   import XShortcutWidget

class XShortcutConfig(XConfigPlugin):
    def __init__( self, 
                  configGroup = 'User Interface', 
                  title       = 'Shortcuts',
                  dataSet     = None,
                  uifile      = '',
                  iconfile    = '' ):
        
        if ( not iconfile ):
            iconfile = resources.find('img/shortcuts.png')
        
        super(XShortcutConfig, self).__init__(
            configGroup,
            title,
            dataSet,
            uifile,
            iconfile)
        
        self.setWidgetClass(XShortcutWidget)