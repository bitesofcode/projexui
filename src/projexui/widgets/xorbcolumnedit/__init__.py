""" Defines a widget for generically editing orb column instances. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2012, Projex Software'
__license__         = 'LGPL'

# maintenance information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'


#------------------------------------------------------------------------------

from projexui.widgets.xorbcolumnedit.xorbcolumnedit import XOrbColumnEdit, \
                                                           IGNORED

__designer_plugins__ = [XOrbColumnEdit]