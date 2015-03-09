#!/usr/bin/python

""" 
The rollout widget allows for multiple collapsible views to be open at once.
"""

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintenance information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'


#------------------------------------------------------------------------------

import datetime

from projex.text import nativestring

from projexui.xpainter import XPainter
from projexui.qt import Signal
from projexui.qt.QtCore import Qt
from projexui.qt.QtGui import QFrame,\
                              QHBoxLayout,\
                              QLabel,\
                              QPalette,\
                              QScrollArea,\
                              QSizePolicy,\
                              QToolButton,\
                              QVBoxLayout,\
                              QWidget,\
                              QPushButton,\
                              QIcon,\
                              QPen

from projexui.xpainter import XPainter
import projexui.resources

TITLE_STYLESHEET = """\
QPushButton {
    text-align: left;
    border: 1px solid palette(midlight);
    border-radius: 8px;
}
QPushButton:hover {
    background-color: palette(button);
}
"""

class XRolloutItem(QWidget):
    def __init__( self, rolloutWidget, widget, title = 'Rollout', expanded = False ):
        super(XRolloutItem, self).__init__(rolloutWidget)
        
        # initialize the interface
        self._rolloutWidget = rolloutWidget
        self._widget        = widget
        self._expanded      = expanded
        
        self._titleButton   = QPushButton(self)
        self._titleButton.setFlat(True)
        self._titleButton.setSizePolicy(QSizePolicy.Expanding, 
                                        QSizePolicy.Minimum)
        self._titleButton.setFixedHeight(20)
        self._titleButton.setText(title)
        self._titleButton.setStyleSheet(TITLE_STYLESHEET)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(6, 6, 6, 9)
        layout.setSpacing(2)
        layout.addWidget(self._titleButton)
        layout.addWidget(widget)
        
        self.setLayout(layout)
        
        # initialize the expanded state
        self.setExpanded(expanded)
        
        # create connections
        self._titleButton.clicked.connect( self.toggleExpanded )
    
    def collapse( self ):
        """
        Collapses this rollout item.
        """
        self.setExpanded(False)
    
    def expand( self ):
        """
        Expands this rollout item.
        """
        self.setExpanded(True)
    
    def isCollapsed( self ):
        """
        Returns whether or not this rollout is in the collapsed state.
        
        :return     <bool>
        """
        return not self._expanded
    
    def paintEvent( self, event ):
        """
        Overloads the paint event to draw rounded edges on this widget.
        
        :param      event | <QPaintEvent>
        """
        super(XRolloutItem, self).paintEvent(event)
        
        with XPainter(self) as painter:
            w = self.width() - 3
            h = self.height() - 3
            
            color = self.palette().color(QPalette.Midlight)
            color = color.darker(180)
            pen = QPen(color)
            pen.setWidthF(0.5)
            
            painter.setPen(pen)
            painter.setBrush(self.palette().color(QPalette.Midlight))
            painter.setRenderHint(XPainter.Antialiasing)
            painter.drawRoundedRect(1, 1, w, h, 10, 10)
    
    def isExpanded( self ):
        """
        Returns whether or not this rollout is in the expanded state.
        
        :return     <bool>
        """
        return self._expanded
    
    def rolloutWidget( self ):
        """
        Returns the rollout widget that this item is associated with.
        
        :return     <XRolloutWidget>
        """
        return self._rolloutWidget
    
    def setCollapsed( self, state ):
        """
        Sets whether or not this rollout is in the collapsed state.
        
        :param      state | <bool>
        """
        return self.setExpanded(not state)
    
    def setExpanded( self, state ):
        """
        Sets whether or not this rollout is in the expanded state.
        
        :param      state | <bool>
        """
        self._expanded = state
        self._widget.setVisible(state)
        
        if ( state ):
            ico = projexui.resources.find('img/treeview/triangle_down.png')
        else:
            ico = projexui.resources.find('img/treeview/triangle_right.png')
        
        self._titleButton.setIcon(QIcon(ico))
        
        # emit the signals for this widget
        rollout = self.rolloutWidget()
        if ( not rollout.signalsBlocked() ):
            index = rollout.widget().layout().indexOf(self)
            
            rollout.itemCollapsed.emit(index)
            rollout.itemExpanded.emit(index)
    
    def setTitle( self, title ):
        """
        Sets the title for this item to the inputed title text.
        
        :param      title | <str>
        """
        self._titleLabel.setText(title)
    
    def title( self ):
        """
        Returns the title for this rollout.
        
        :return     <str>
        """
        return nativestring(self._titleLabel.text())
    
    def toggleExpanded( self ):
        """
        Toggles whether or not this rollout is in the expanded state.
        """
        self.setExpanded(not self.isExpanded())
    
    def widget( self ):
        """
        Returns the widget that is associated with this rollout item.
        
        :return     <QWidget>
        """
        return self._widget

#------------------------------------------------------------------------------

class XRolloutWidget(QScrollArea):
    """ """
    itemCollapsed   = Signal(int)
    itemExpanded    = Signal(int)
    
    def __init__( self, parent = None ):
        super(XRolloutWidget, self).__init__( parent )
        
        # define custom properties
        self.setWidgetResizable(True)
        
        # set default properties
        widget = QWidget(self)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        layout.addStretch(1)
        widget.setLayout(layout)
        
        self.setWidget(widget)
    
    def clear( self ):
        """
        Clears out all of the rollout items from the widget.
        """
        self.blockSignals(True)
        self.setUpdatesEnabled(False)
        for child in self.findChildren(XRolloutItem):
            child.setParent(None)
            child.deleteLater()
        self.setUpdatesEnabled(True)
        self.blockSignals(False)
    
    def addRollout( self, widget, title, expanded = False ):
        """
        Adds a new widget to the rollout system.
        
        :param      widget      | <QWidget>
                    title       | <str>
                    expanded    | <bool>
        
        :return     <XRolloutItem>
        """
        layout = self.widget().layout()
        item = XRolloutItem(self, widget, title, expanded)
        layout.insertWidget(layout.count() - 1, item)
        return item
    
    def count( self ):
        """
        Returns the number of items that are associated with this rollout.
        
        :return     <int>
        """
        return self.widget().layout().count() - 1
    
    def itemAt( self, index ):
        """
        Returns the rollout item at the inputed index.
        
        :return     <XRolloutItem> || None
        """
        layout = self.widget().layout()
        if ( 0 <= index and index < (layout.count() - 1) ):
            return layout.itemAt(index).widget()
        return None
    
    def items( self ):
        """
        Returns all the rollout items for this widget.
        
        :return     [<XRolloutItem>, ..]
        """
        layout = self.widget().layout()
        return [layout.itemAt(i).widget() for i in range(layout.count()-1)]
    
    def takeAt( self, index ):
        """
        Removes the widget from the rollout at the inputed index.
        
        :param      index | <int>
        
        :return     <QWidget> || None
        """
        layout = self.widget().layout()
        item = layout.takeAt(index)
        if ( not item ):
            return None
        
        return item.widget().widget()

__designer_plugins__ = [XRolloutWidget]