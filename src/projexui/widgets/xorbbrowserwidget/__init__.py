""" [desc] """

# define authorship information
__authors__         = ['']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

__maintainer__      = ''
__email__           = ''


#------------------------------------------------------------------------------

from projexui.widgets.xorbbrowserwidget.xorbbrowserwidget import XOrbBrowserWidget
from projexui.widgets.xorbbrowserwidget.xorbbrowserfactory import XOrbBrowserFactory
from projexui.widgets.xorbbrowserwidget.xcardwidget import XAbstractCardWidget,\
                                                           XBasicCardWidget

__designer_plugins__ = [XOrbBrowserWidget]