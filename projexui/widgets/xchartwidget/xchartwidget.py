#!/usr/bin/python

""" Defines a chart widget for use in displaying data. """

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

from projexui.qt.QtCore import Qt
from projexui.qt.QtGui import QGraphicsView

from projexui.widgets.xchartwidget.xchartscene import XChartScene

class XChartWidget(QGraphicsView):
    """ """
    Type = XChartScene.Type
    
    def __getattr__( self, key ):
        """
        Passes along access to the scene properties for this widget.
        
        :param      key | <str>
        """
        return getattr(self.scene(), key)
        
    def __init__( self, parent = None ):
        super(XChartWidget, self).__init__( parent )
        
        # define custom properties
        
        # set default properties
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setScene(XChartScene(self))
        
        # create connections