""" 
Defines the XQueryEdit widget that allows users to visually build queries into
an ORB database. 
"""

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

from projexui.widgets.xorbrecordsetedit.xorbrecordsetedit import \
                                        XOrbRecordSetEdit

__designer_plugins__ = [XOrbRecordSetEdit]