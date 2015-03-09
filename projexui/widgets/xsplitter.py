#!/usr/bin/python

""" 
Extends the base QTableWidget class with additional methods.
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

from projex.enum import enum

from projexui.qt.QtCore   import Qt, QLine

from projexui.qt.QtGui import QSplitter,\
                              QSplitterHandle,\
                              QToolButton,\
                              QBoxLayout,\
                              QLabel

import projexui.resources
from projexui.xpainter import XPainter

class XSplitterHandle(QSplitterHandle):
    CollapseDirection = enum('After', 'Before')
    
    def __init__( self, orientation, parent ):
        super(XSplitterHandle, self).__init__( orientation, parent )
        
        # create a layout for the different buttons
        self._collapsed      = False
        self._storedSizes    = None
        
        self._collapseBefore = QToolButton(self)
        self._resizeGrip     = QLabel(self)
        self._collapseAfter  = QToolButton(self)
        
        self._collapseBefore.setAutoRaise(True)
        self._collapseAfter.setAutoRaise(True)
        
        self._collapseBefore.setCursor(Qt.ArrowCursor)
        self._collapseAfter.setCursor(Qt.ArrowCursor)
        
        # define the layout
        layout = QBoxLayout(QBoxLayout.LeftToRight, self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(1)
        layout.addWidget(self._collapseBefore)
        layout.addWidget(self._resizeGrip)
        layout.addWidget(self._collapseAfter)
        layout.addStretch(1)
        self.setLayout(layout)
        
        # set the orientation to start with
        self.setOrientation(orientation)
        
        # create connections
        self._collapseAfter.clicked.connect(  self.toggleCollapseAfter )
        self._collapseBefore.clicked.connect( self.toggleCollapseBefore )
    
    def collapse( self, direction ):
        """
        Collapses this splitter handle before or after other widgets based on \
        the inputed CollapseDirection.
        
        :param      direction | <XSplitterHandle.CollapseDirection>
        
        :return     <bool> | success
        """
        if ( self.isCollapsed() ):
            return False
        
        splitter = self.parent()
        if ( not splitter ):
            return False
        
        sizes   = splitter.sizes()
        handles = [splitter.handle(i) for i in range(len(sizes))]
        index   = handles.index(self)
        
        self.markCollapsed(direction, sizes)
        
        # determine the sizes to use based on the direction
        if ( direction == XSplitterHandle.CollapseDirection.Before ):
            sizes = [0 for i in range(i)] + sizes[i+1:]
        else:
            sizes = sizes[:i] + [0 for i in range(i, len(sizes))]
        
        splitter.setSizes(sizes)
        return True
        
    def collapseAfter( self, handle ):
        """
        Collapses the splitter after the inputed handle.
        
        :param      handle | <XSplitterHandle>
        """
        self.setUpdatesEnabled(False)
        
        # collapse all items after the current handle
        if ( handle.isCollapsed() ):
            self.setSizes(handle.restoreSizes())
            
        found = False
        sizes = self.sizes()
        
        handle.storeSizes(sizes)
        
        for c in range(self.count()):
            if ( self.handle(c) == handle ):
                found = True
            
            if ( found ):
                sizes[c] = 0
        
        self.setSizes(sizes)
        self.update()
        
        self.setUpdatesEnabled(True)
    
    def collapseBefore( self, handle ):
        """
        Collapses the splitter before the inputed handle.
        
        :param      handle | <XSplitterHandle>
        """
        self.setUpdatesEnabled(False)
        
        # collapse all items after the current handle
        if ( handle.isCollapsed() ):
            self.setSizes(handle.restoreSizes())
            
        # collapse all items before the current handle
        found = False
        sizes = self.sizes()
        
        handle.storeSizes(sizes)
        
        for c in range(self.count()):
            if ( self.handle(c) == handle ):
                break
            
            sizes[c] = 0
        
        self.setSizes(sizes)
        self.setUpdatesEnabled(True)
    
    def isCollapsed( self ):
        """
        Returns whether or not this widget is collapsed.
        
        :return     <bool>
        """
        return self._collapsed
    
    def markCollapsed( self, direction, sizes ):
        """
        Updates the interface to reflect that the splitter is collapsed.
        
        :param      direction | <XSplitterHandle.CollapseDirection>
                    sizes     | [<int>, ..]
        """
        self._collapsed = True
        self._storedSizes = sizes[:]
        
        if ( direction == XSplitterHandle.CollapseDirection.Before ):
            if ( self.orientation() == Qt.Horizontal ):
                self._collapseAfter.setArrowType( Qt.RightArrow )
                self._collapseBefore.setArrowType( Qt.RightArrow )
            else:
                self._collapseAfter.setArrowType( Qt.DownArrow )
                self._collapseBefore.setArrowType( Qt.DownArrow )
        else:
            if ( self.orientation() == Qt.Horizontal ):
                self._collapseAfter.setArrowType( Qt.LeftArrow )
                self._collapseBefore.setArrowType( Qt.LeftArrow )
            else:
                self._collapseAfter.setArrowType( Qt.UpArrow )
                self._collapseAfter.setArrowType( Qt.UpArrow )
        
    def paintEvent( self, event ):
        """
        Overloads the paint event to handle drawing the splitter lines.
        
        :param      event | <QPaintEvent>
        """
        lines = []
        count = 20
        
        # calculate the lines
        if ( self.orientation() == Qt.Vertical ):
            x = self._resizeGrip.pos().x()
            h = self.height()
            spacing = int(float(self._resizeGrip.width()) / count)
            
            for i in range(count):
                lines.append(QLine(x, 0, x, h))
                x += spacing
        else:
            y = self._resizeGrip.pos().y()
            w = self.width()
            spacing = int(float(self._resizeGrip.height()) / count)
            
            for i in range(count):
                lines.append(QLine(0, y, w, y))
                y += spacing
            
        # draw the lines
        with XPainter(self) as painter:
            pal = self.palette()
            painter.setPen(pal.color(pal.Window).darker(120))
            painter.drawLines(lines)
    
    def setOrientation( self, orientation ):
        """
        Sets the orientation for this handle and updates the widgets linked \
        with it.
        
        :param      orientation | <Qt.Orientation>
        """
        super(XSplitterHandle, self).setOrientation(orientation)
        
        if ( orientation == Qt.Vertical ):
            self.layout().setDirection( QBoxLayout.LeftToRight )
            
            # update the widgets
            self._collapseBefore.setFixedSize(30, 10)
            self._collapseAfter.setFixedSize(30, 10)
            self._resizeGrip.setFixedSize(60, 10)
            
            self._collapseBefore.setArrowType(Qt.UpArrow)
            self._collapseAfter.setArrowType(Qt.DownArrow)
            
        elif ( orientation == Qt.Horizontal ):
            self.layout().setDirection( QBoxLayout.TopToBottom )
            
            # update the widgets
            self._collapseBefore.setFixedSize(10, 30)
            self._collapseAfter.setFixedSize(10, 30)
            self._resizeGrip.setFixedSize(10, 60)
            
            self._collapseBefore.setArrowType(Qt.LeftArrow)
            self._collapseAfter.setArrowType(Qt.RightArrow)
    
    def uncollapse( self ):
        """
        Uncollapses the splitter this handle is associated with by restoring \
        its sizes from before the collapse occurred.
        
        :return     <bool> | changed
        """
        if ( not self.isCollapsed() ):
            return False
        
        self.parent().setSizes(self._storedSizes)
        self.unmarkCollapsed()
        
        return True
    
    def unmarkCollapsed( self ):
        """
        Unmarks this splitter as being in a collapsed state, clearing any \
        collapsed information.
        """
        if ( not self.isCollapsed() ):
            return
        
        self._collapsed     = False
        self._storedSizes   = None
        
        if ( self.orientation() == Qt.Vertical ):
            self._collapseBefore.setArrowType( Qt.UpArrow )
            self._collapseAfter.setArrowType(  Qt.DownArrow )
        else:
            self._collapseBefore.setArrowType( Qt.LeftArrow )
            self._collapseAfter.setArrowType(  Qt.RightArrow )
    
    def toggleCollapseAfter( self ):
        """
        Collapses the splitter after this handle.
        """
        if ( self.isCollapsed() ):
            self.uncollapse()
        else:
            self.collapse( XSplitterHandle.CollapseDirection.After )
    
    def toggleCollapseBefore( self ):
        """
        Collapses the splitter before this handle.
        """
        if ( self.isCollapsed() ):
            self.uncollapse()
        else:
            self.collapse( XSplitterHandle.CollapseDirection.Before )
        
#-------------------------------------------------------------------------------

class XSplitter(QSplitter):
    """ """
    __designer_icon__ = projexui.resources.find('img/ui/splitter.png')
    
    def __init__( self, *args ):
        super(XSplitter, self).__init__( *args )
        
        # define custom properties
        
        # set default properties
        self.setHandleWidth(10)
        
        # create connections
        self.splitterMoved.connect(self.clearCollapseState)
    
    def clearCollapseState( self, pos, index ):
        """
        Clears the collapsed state when a user moves the splitter handle.
        
        :param      pos     | <int>
                    index   | <int>
        """
        self.handle(index).unmarkCollapsed()
    
    def createHandle( self ):
        """
        Creates a new splitter handle for this class using the XSplitterHandle \
        subclass.  This will allow for additional features like collapsing and \
        expanding of pages, etc.
        
        :return     <XSplitterHandle>
        """
        return XSplitterHandle(self.orientation(), self)
    
    def restoreState( self, state ):
        super(XSplitter, self).restoreState(state)
        
        # force the handle with to remain the same
        self.setHandleWidth(10)

__designer_plugins__ = [XSplitter]