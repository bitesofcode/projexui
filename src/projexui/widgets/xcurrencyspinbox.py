""" Defines a spinner to control money values. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software, LLC'
__license__         = 'LGPL'

__maintainer__      = 'Projex Software, LLC'
__email__           = 'team@projexsoftware.com'

from projexui.qt import Slot, Property
from projexui.qt.QtGui import QDoubleSpinBox

import projex.money

class XCurrencySpinBox(QDoubleSpinBox):
    def __init__( self, parent ):
        super(XCurrencySpinBox, self).__init__(parent)
        
        # define custom properties
        self._currency = 'USD'
        
        # set default values
        self.setSingleStep(10)
    
    def currency( self ):
        """
        Returns the currency for this widget.
        
        :return     <str>
        """
        return self._currency
    
    @Slot(str)
    def setCurrency( self, currency ):
        """
        Sets the currency for this widget.
        
        :param      currency | <str>
        """
        self._currency = currency
        self.setValue(self.value())
    
    def textFromValue( self, value ):
        """
        Returns the text for this widgets value.
        
        :param      value | <float>
        
        :return     <str>
        """
        return projex.money.toString(value, self.currency())
    
    def valueFromText( self, text ):
        """
        Returns the value for this widgets text.
        
        :param      text | <str>
        
        :return     <float>
        """
        value, currency = projex.money.fromString(text)
        
        return value
    
    x_currency = Property(str, currency, setCurrency)

__designer_plugins__ = [XCurrencySpinBox]