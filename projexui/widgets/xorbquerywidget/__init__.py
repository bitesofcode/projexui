""" [desc] """

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

from .xorbqueryplugin import XOrbQueryPlugin, XOrbQueryPluginFactory

from .xorbquerywidget import XOrbQueryWidget
from .xorbquickfilterwidget import XOrbQuickFilterWidget

__designer_plugins__ = [XOrbQueryWidget, XOrbQuickFilterWidget]