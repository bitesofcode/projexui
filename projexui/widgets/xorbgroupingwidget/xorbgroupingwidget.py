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

from projexui.qt.QtGui import QWidget

import projexui

class XOrbGroupingWidget(QWidget):
    """ """
    def __init__( self, parent = None ):
        super(XOrbGroupingWidget, self).__init__( parent )
        
        # load the user interface
        projexui.loadUi(__file__, self)
        
        # define custom properties
        self._tableType = None
        
        # set default properties
        
        # create connections
    
    def setTableType(self, tableType):
        """
        Sets the table type for this widget to the inputed type.
        
        :param      tableType | <subclass of orb.Table>
        """
        self._tableType = tableType
        self.reset()
    
    def tableType(self):
        """
        Returns the table type for this widget.
        
        :return     <subclass of orb.TableType>
        """
        return self._tableType