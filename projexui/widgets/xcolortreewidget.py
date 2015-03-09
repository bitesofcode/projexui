#!/usr/bin/python

""" Defines a tree widget designed to let users modify color information \
    easily."""

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

from projexui.qt.QtCore  import QSize
from projexui.qt.QtGui   import QColorDialog,\
                                QTreeWidgetItem,\
                                QPalette

import projex.text
import projexui.resources

from projexui.widgets.xtreewidget import XTreeWidget
from projexui.xcolorset           import XPaletteColorSet

class XColorTreeWidgetItem(QTreeWidgetItem):
    """ Defines a color item for use in the color tree """
    def __init__( self, name, colors ):
        super(XColorTreeWidgetItem, self).__init__()
        
        # set custom properties
        self._name   = name
        
        # set standard properties
        self.setSizeHint(0, QSize(0, 22))
        self.setName(name)
        
        # define colors
        for i, color in enumerate(colors):
            self.setBackground( i+1, color )
    
    def colorAt( self, index ):
        """
        Returns the color at the given index
        
        :return     <QColor>
        """
        return self.background(index+1).color()
    
    def colors( self ):
        """
        Returns a list of the colors linked to this item.
        
        :param      [<QColor>, ..]
        """
        return [self.colorAt(i-1) for i in range(1, self.columnCount())]
    
    def name( self ):
        """
        Returns the name of the current item.
        
        :return     <str>
        """
        return self._name
    
    def setColorAt( self, index, color ):
        """
        Sets the color at the inputed index to the given color.
        
        :param      index | <int>
                    color | <QColor>
        """
        self.setBackground(index+1, color)
    
    def setName( self, name ):
        """
        Sets the name for this color item to the inputed name.
        
        :param      name | <str>
        """
        self._name = projex.text.nativestring(name)
        self.setText(0, ' '.join(projex.text.words(self._name)))

#------------------------------------------------------------------------------

class XColorTreeWidget(XTreeWidget):
    """ Defines the color tree widget class for editing colors """
    __designer_icon__ = projexui.resources.find('img/ui/colorpicker.png')
    
    def __init__( self, parent ):
        super(XColorTreeWidget, self).__init__(parent)
        
        # define custom properties
        self._propogateRight = False
        
        # set properties
        self.header().setStretchLastSection(False)
        
        self.setSelectionMode(self.NoSelection)
        self.setRootIsDecorated(False)
        self.setAlternatingRowColors(True)
        self.setColorWidth(20)
        self.setColumnCount(2)
        self.setHeaderLabels(['Name', 'Color'])
        self.setPropagateRight( True )
        
        # create connections
        self.itemDoubleClicked.connect( self.editColor )
    
    def colorSet( self ):
        """
        Returns a color map for all the items in this tree.
        
        :return     { <str> name: (<QColor> color, ..), .. }
        """
        return self._colorSet
    
    def editColor( self, item, index ):
        """
        Prompts the user to pick a new color for the inputed item/column.
        
        :param      item  | <XColorTreeWidgetItem>
                    index | <int>
        """
        if ( not index ):
            return
            
        newcolor = QColorDialog.getColor(item.colorAt(index-1), self)
        
        if ( not newcolor.isValid() ):
            return
            
        endIndex = index + 1
        if ( self.propogateRight() ):
            endIndex = self.columnCount()
        
        for i in range(index, endIndex):
            item.setColorAt(i-1, newcolor)
    
    def propogateRight( self ):
        """
        Sets whether or not to automatically set the values to the right of \
        the currently edited color when a user modifies a parituclar color.
        
        :return     <bool>
        """
        return self._propogateRight
    
    def savedColorSet( self ):
        """
        Returns the current colors as a saved color set.
        
        :return     <XColorSet> || None
        """
        colorSet = self._colorSet
        if ( not colorSet ):
            return None
        
        labels = colorSet.colorGroups()
        for i in range( self.topLevelItemCount() ):
            item = self.topLevelItem(i)
            colorName = item.name()
            for i, color in enumerate(item.colors()):
                colorSet.setColor(colorName, color, labels[i])
        
        return colorSet
    
    def setColorSet( self, colorSet ):
        """
        Resets the tree to use the inputed color set information.
        
        :param      colorSet | <XColorSet>
        """
        self.blockSignals(True)
        self.setUpdatesEnabled(False)
        
        self.clear()
        
        self._colorSet = colorSet
        
        if ( colorSet ):
            labels = colorSet.colorGroups()
            self.setHeaderLabels( [colorSet.name()] + labels )
            self.setColumnCount( 1 + len(labels) )
            
            for colorName in colorSet.colorNames():
                item = XColorTreeWidgetItem(colorName, 
                                            colorSet.colors(colorName))
                                            
                self.addTopLevelItem(item)
            
        self.setUpdatesEnabled(True)
        self.blockSignals(False)
    
    def setColorWidth( self, amount ):
        """
        Defines the width to use for the color section of the tree.
        
        :param      amount | <int>
        """
        self.header().setMinimumSectionSize(amount)
    
    def setColumnCount( self, count ):
        """
        Sets the number of columns used for this tree widget, updating the \
        column resizing modes to stretch the first column.
        
        :param      count | <int>
        """
        super(XColorTreeWidget, self).setColumnCount(count)
        
        header = self.header()
        header.setResizeMode(0, header.Stretch)
        for i in range(1, count):
            header.setResizeMode(i, header.Fixed)
    
    def setPropagateRight( self, state ):
        """
        Sets whether or not to propogate user changes to the right as a color \
        is modified.
        
        :param      state   | <bool>
        """
        self._propogateRight = state
    
    def setQuickColor( self, color ):
        """
        Sets the quick color for the palette to the given color.
        
        :param      color | <QColor>
        """
        colorset = XPaletteColorSet()
        colorset.setPalette(QPalette(color))
        self.setColorSet(colorset)
    
__designer_plugins__ = [XColorTreeWidget]