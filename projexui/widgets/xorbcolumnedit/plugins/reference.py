""" Defines the different plugins that will be used for this widget. """

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

from orb import ColumnType
from projexui.widgets.xorbcolumnedit import plugins
from projexui.widgets.xorbrecordbox  import XOrbRecordBox

class ForeignKeyEdit(XOrbRecordBox):
    def setValue( self, value ):
        self.setCurrentRecord(value)
    
    def value( self ):
        return self.currentRecord()

#------------------------------------------------------------------------------

plugins.widgets[ColumnType.ForeignKey]    = ForeignKeyEdit