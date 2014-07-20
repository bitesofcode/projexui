#!/usr/bin python

""" Defines a full rich text edit to handle WYSIWYG editing. """

# define authorship information
__authors__     = ['Eric Hulser']
__author__      = ','.join(__authors__)
__credits__     = []
__copyright__   = 'Copyright (c) 2011, Projex Software'

# maintanence information
__maintainer__  = 'Projex Software'
__email__       = 'team@projexsoftware.com'

#------------------------------------------------------------------------------

from projexui.qt import Signal
from projexui.qt.QtGui import QWidget,\
                              QFontDatabase,\
                              QFont,\
                              QTreeWidgetItem

import projexui

class XFontPickerWidget(QWidget):
    """ """
    accepted = Signal()
    
    def __init__( self, parent = None ):
        super(XFontPickerWidget, self).__init__( parent )
        
        # load the user interface
        projexui.loadUi(__file__, self)
        
        # define custom properties
        database = QFontDatabase()
        for family in sorted(database.families()):
            item = QTreeWidgetItem(self.uiFontTREE, [family])
            item.setFont(0, QFont(family))
        
        # set default properties
        
        # create connections
        self.uiSizeSPN.valueChanged.connect(self.setPointSize)
        self.uiFontTREE.itemDoubleClicked.connect(self.accepted)
    
    def currentFamily(self):
        """
        Returns the currently selected font family.
        
        :return     <str>
        """
        item = self.uiFontTREE.currentItem()
        if item:
            return item.text(0)
        return ''
    
    def pointSize(self):
        """
        Returns the point size for the current font.
        
        :return     <int>
        """
        return self.uiSizeSPN.value()
    
    def setCurrentFamily(self, family):
        """
        Sets the current font family to the inputed family.
        
        :param      family | <str>
        """
        for i in range(self.uiFontTREE.topLevelItemCount()):
            item = self.uiFontTREE.topLevelItem(i)
            if item.text(0) == family:
                self.uiFontTREE.setCurrentItem(item)
                return
        
        self.uiFontTREE.setCurrentItem(None)
    
    def setPointSize(self, pointSize):
        """
        Sets the point size for this widget to the inputed size.
        
        :param      pointSize | <int>
        """
        self.uiSizeSPN.blockSignals(True)
        self.uiSizeSPN.setValue(pointSize)
        self.uiSizeSPN.blockSignals(False)
        
        for i in range(self.uiFontTREE.topLevelItemCount()):
            item = self.uiFontTREE.topLevelItem(i)
            font = item.font(0)
            font.setPointSize(pointSize)
            item.setFont(0, font)