#!/usr/bin/python

""" Simple widget for managing boolean values in a drop-down. """

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

from projexui.qt import Property
from projexui.widgets.xcombobox import XComboBox

class XBoolComboBox(XComboBox):
    def __init__(self, parent=None):
        super(XBoolComboBox, self).__init__(parent)
        
        # setup properties
        self.addItem('True')
        self.addItem('False')
    
    def falseText(self):
        """
        Returns the text that will be shown for a false state.
        
        :return     <str>
        """
        return self.itemText(0)
    
    def isChecked(self):
        """
        Returns whether or not this combo box is in a checked (True) state.
        
        :return     <bool>
        """
        return self.currentIndex() == 0
    
    def setChecked(self, state):
        """
        Sets whether or not this combo box is in a checked (True) state.
        
        :param      state | <bool>
        """
        if state:
            index = 0
        else:
            index = 1
        
        self.setCurrentIndex(index)
    
    def setFalseText(self, text):
        """
        Sets the text that will be shown for a false state.
        
        :param      text | <str>
        """
        self.setItemText(1, text)
    
    def setTrueText(self, text):
        """
        Sets the text that will be shown for a true state.
        
        :param      text | <str>
        """
        self.setItemText(0, text)
    
    def trueText(self):
        """
        Returns the text that will be shown for a true state.
        
        :return     <str>
        """
        return self.itemText(0)
    
    x_checked = Property(bool, isChecked, setChecked)
    x_falseText = Property(str, falseText, setFalseText)
    x_trueText = Property(str, trueText, setTrueText)

__designer_plugins__ = [XBoolComboBox]