#!/usr/bin/python

"""
Extends the base QGroupBox class to support some additional features like
setting collapsing on toggle.
"""

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

import projexui.resources

from projexui.qt        import Property
from projexui.qt.QtGui  import QGroupBox, QWidget

MAX_INT = 10000

class XGroupBox( QGroupBox ):
    """
    Extends the base QGroupBox class to support some additional features like
    setting collapsing on toggle.
    """
    
    __designer_icon__ = projexui.resources.find('img/ui/groupbox.png')
    __designer_container__ = True
    
    def __init__( self, *args ):
        super(XGroupBox, self).__init__(*args)
        
        self._collapsible       = False
        self._collapsedHeight   = 18
        self._inverted          = False
        
        self.toggled.connect( self.matchCollapsedState )
    
    def collapsedHeight( self ):
        """
        Returns the collapsed height for this object.
        
        :return     <int>
        """
        return self._collapsedHeight
    
    def isCollapsed( self ):
        """
        Returns whether or not this group box is collapsed.
        
        :return     <bool>
        """
        if not self.isCollapsible():
            return False
        
        if self._inverted:
            return self.isChecked()
        return not self.isChecked()
    
    def isCollapsible( self ):
        """
        Returns whether or not this group box is collapsiible.
        
        :return     <bool>
        """
        return self._collapsible
    
    def isInverted(self):
        """
        Returns whether or not this widget is in an inverted state, by which
        unchecking the group box will force it collapsed.
        
        :return     <bool>
        """
        return self._inverted
    
    def paintEvent( self, event ):
        """
        Overloads the paint event for this group box if it is currently
        collpased.
        
        :param      event | <QPaintEvent>
        """
        if ( self.isCollapsed() ):
            self.setFlat(True)
        
        elif ( self.isCollapsible() ):
            self.setFlat(False)
            
        super(XGroupBox, self).paintEvent(event)
    
    def matchCollapsedState( self ):
        """
        Matches the collapsed state for this groupbox.
        """
        collapsed = not self.isChecked()
        if self._inverted:
            collapsed = not collapsed
        
        if ( not self.isCollapsible() or not collapsed ):
            for child in self.children():
                if ( not isinstance(child, QWidget) ):
                    continue
                
                child.show()
            
            self.setMaximumHeight(MAX_INT)
            self.adjustSize()
            
            if ( self.parent() ):
                self.parent().adjustSize()
        else:
            self.setMaximumHeight(self.collapsedHeight())
            
            for child in self.children():
                if ( not isinstance(child, QWidget) ):
                    continue
                
                child.hide()
    
    def setCollapsed( self, state ):
        """
        Sets whether or not this group box is collapsed.
        
        :param      state | <bool>
        """
        self.setCollapsible(True)
        if not self._inverted:
            self.setChecked(not state)
        else:
            self.setChecked(state)
    
    def setCollapsible( self, state ):
        """
        Sets whether or not this groupbox will be collapsible when toggled.
        
        :param      state | <bool>
        """
        self._collapsible = state
        self.matchCollapsedState()
    
    def setCollapsedHeight( self, height ):
        """
        Sets the height that will be used when this group box is collapsed.
        
        :param      height | <int>
        """
        self._collapsedHeight = height
        self.matchCollapsedState()
    
    def setInverted(self, state):
        """
        Sets whether or not to invert the check state for collapsing.
        
        :param      state | <bool>
        """
        collapsed = self.isCollapsed()
        self._inverted = state
        if self.isCollapsible():
            self.setCollapsed(collapsed)
    
    # create Qt properties
    x_collapsible       = Property(bool, isCollapsible, setCollapsible)
    x_collapsed         = Property(bool, isCollapsed, setCollapsed)
    x_collapsedHeight   = Property(int, collapsedHeight, setCollapsedHeight)
    x_inverted          = Property(bool, isInverted, setInverted)
    
__designer_plugins__ = [XGroupBox]