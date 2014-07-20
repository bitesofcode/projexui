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

from projex.text import nativestring

from orb import ColumnType
from projexui.widgets.xorbcolumnedit import plugins
from projexui.qt.QtGui import QCheckBox,\
                              QSpinBox,\
                              QDoubleSpinBox

class BoolEdit(QCheckBox):
    def label( self ):
        return nativestring(self.text())
    
    def setValue( self, value ):
        self.setChecked(value == True)
    
    def setLabel( self, text ):
        self.setText(text)
    
    def value( self ):
        return self.isChecked()

#------------------------------------------------------------------------------

class IntegerEdit(QSpinBox):
    def __init__( self, parent ):
        super(IntegerEdit, self).__init__(parent)
        
        self.setMinimum(-100000)
        self.setMaximum( 100000)
    
    def setValue( self, value ):
        try:
            value = int(value)
        except TypeError:
            value = 0
        
        super(IntegerEdit, self).setValue(value)

#------------------------------------------------------------------------------

class DoubleEdit(QDoubleSpinBox):
    def __init__( self, parent ):
        super(DoubleEdit, self).__init__(parent)
        
        self.setMinimum(-100000)
        self.setMaximum( 100000)
    
    def setValue( self, value ):
        try:
            value = float(value)
        except TypeError:
            value = 0.0
        
        super(DoubleEdit, self).setValue(value)

#------------------------------------------------------------------------------

plugins.widgets[ColumnType.Bool]    = BoolEdit
plugins.widgets[ColumnType.Integer] = IntegerEdit
plugins.widgets[ColumnType.Double]  = DoubleEdit
plugins.widgets[ColumnType.Decimal] = DoubleEdit