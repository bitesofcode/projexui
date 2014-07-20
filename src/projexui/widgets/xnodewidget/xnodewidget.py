#!/usr/bin/python

"""
Defines a node widget class that can be reused for generating 
various node systems.
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

from projexui.qt import Property, Slot, Signal
from projexui.qt.QtCore   import Qt, QSize, QPoint, QRectF, QPointF
from projexui.qt.QtGui    import QGraphicsView,\
                                 QApplication

from projexui.xanimation import XObjectAnimation
from projexui.widgets.xnodewidget.xnode import XNode
from projexui.widgets.xnodewidget.xnodescene import XNodeScene
from projexui.widgets.xnodewidget.xnodelayout import XNodeLayout

import projexui.resources

class XNodeWidget(QGraphicsView):
    """ Defines the main widget for creating node graph views. """
    __designer_icon__ = projexui.resources.find('img/ui/node.png')
    
    maxZoomAmountChanged = Signal(int)
    minZoomAmountChanged = Signal(int)
    zoomAmountChanged = Signal(int)
    
    def __init__(self, parent, sceneClass=None):
        # initialize the super class
        super(XNodeWidget, self).__init__( parent )
        
        # set the scene
        if not sceneClass:
            sceneClass = XNodeScene
        
        self._cleanupOnClose = True
        self._initialized = False
        
        self.setScene(sceneClass(self))
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
    
    def __dir__(self):
        out = set(self.__dict__.keys())
        out.update(dir(self.scene()))
        return list(out)
        
    def __getattr__( self, key ):
        return getattr(self.scene(), key)
    
    def _runLayoutTest(self, layoutName):
        """
        Runs a layout test for this widget for the inputed layout plugin
        name.
        
        :param      layoutName | <str>
        
        :return     <bool> | success
        """
        layout = XNodeLayout.plugin(layoutName)
        if not layout:
            return False
        
        layout.runTest(self.scene())
        return True
    
    @Slot()
    def autoLayout(self):
        """
        Auto-lays out the whole scene.
        """
        self.scene().autoLayout()
    
    @Slot()
    def autoLayoutSelected( self ):
        """
        Auto-lays out the selected items.
        """
        self.scene().autoLayoutSelected()
    
    def centerOn(self, *args):
        """
        Updates the center on method to ensure the viewport is updated.
        
        :param      *args | <variant>
        """
        super(XNodeWidget, self).centerOn(*args)
        
        for con in self.connections():
            con.setPath(con.rebuild())
            con.update()
    
    def centerOnAnimated(self, centerOn, animate=0):
        """
        Animates the centering options over a given number of seconds.
        
        :param      centerOn | <QRectF> | <QPointF> | <XNode>
                    animate  | <float> | seconds
        """
        if isinstance(centerOn, XNode):
            center = centerOn.sceneRect().center()
        elif isinstance(centerOn, QRectF):
            center = centerOn.center()
        elif isinstance(centerOn, QPointF):
            center = centerOn
        else:
            return
        
        anim = XObjectAnimation(self, 'centerOn', self)
        anim.setStartValue(self.viewportRect().center())
        anim.setEndValue(center)
        anim.setDuration(1000 * animate)
        anim.start()
        anim.finished.connect(anim.deleteLater)
    
    def centerOnItems(self, items = None):
        """
        Centers on the given items, if no items are supplied, then all
        items will be centered on.
        
        :param      items | [<QGraphicsItem>, ..]
        """
        if not items:
            rect = self.scene().visibleItemsBoundingRect()
            if not rect.width():
                rect = self.scene().sceneRect()
            
            self.centerOn(rect.center())
        else:
            self.centerOn(self.scene().calculateBoundingRect(items).center())
    
    def centerOnSelection(self):
        """
        Centers on the selected items.
        
        :sa     centerOnItems
        """
        self.centerOnItems(self.scene().selectedItems())
    
    def cleanupOnClose( self ):
        """
        Sets whether or not this widget should clean up its scene before
        closing.
        
        :return     <bool>
        """
        return self._cleanupOnClose
    
    def closeEvent( self, event ):
        """
        Cleans up the scene before closing.
        
        :param      event | <QEvent>
        """
        if ( self.cleanupOnClose() ):
            scene = self.scene()
            scene.cleanup()
            self.setScene(None)
        
        super(XNodeWidget, self).closeEvent(event)
    
    @Slot()
    def disableViewMode(self):
        """
        Sets the node widget into selection mode which allows the user to select
        vs. pan and zoom.
        """
        self.scene().setViewMode(False)
    
    @Slot()
    def enableViewMode(self):
        """
        Sets the node widget into view mode which allows the user to pan
        and zoom vs. select.
        """
        self.scene().setViewMode(True)
    
    def findNodeByRegex( self, nodeRegex ):
        """
        Returns the first node that matches the inputed regular expression.
        
        :param      nodeRegex | <str>
        
        :return     <XNode> || None
        """
        return self.scene().findNodeByRegex(nodeRegex)
    
    def findNode( self, nodeName ):
        """
        Returns the node for the given node name.
        
        :param     nodeName | <str>
        
        :return     <XNode> || None
        """
        return self.scene().findNode(nodeName)
    
    def isolationMode( self ):
        """
        Returns whether or not this widget is in isolation mode.
        
        :return     <bool>
        """
        return self.scene().isolationMode()
    
    def setCleanupOnClose( self, state ):
        """
        Sets whether or not the scene should be cleaned up before closing.
        
        :param      state | <bool>
        """
        self._cleanupOnClose = state
    
    @Slot(bool)
    def setIsolationMode( self, state ):
        """
        Sets whether or not the widget is in isolation mode.
        
        :param      state | <bool>
        """
        self.scene().setIsolationMode(state)
    
    @Slot(int)
    def setZoomAmount(self, amount):
        """
        Sets the zoom amount for this widget to the inputed amount.
        
        :param      amount | <int>
        """
        self.scene().setZoomAmount(amount)
    
    def showEvent(self, event):
        super(XNodeWidget, self).showEvent(event)
        
        if not self._initialized:
            self._initialized = True
            self.centerOnItems()
    
    def viewportRect(self):
        """
        Returns the QRectF that represents the visible viewport rect for the
        current view.
        
        :return     <QRectF>
        """
        w = self.width()
        h = self.height()
        
        vbar = self.verticalScrollBar()
        hbar = self.horizontalScrollBar()
        
        if vbar.isVisible():
            w -= vbar.width()
        if hbar.isVisible():
            h -= hbar.height()
        
        top_l = self.mapToScene(QPoint(0, 0))
        bot_r = self.mapToScene(QPoint(w, h))
        
        return QRectF(top_l.x(), 
                      top_l.y(), 
                      bot_r.x() - top_l.x(), 
                      bot_r.y() - top_l.y())
    
    def zoomAmount(self):
        """
        Returns the zoom amount for this widget to the inputed amount.
        
        :param      amount | <int>
        """
        return self.scene().zoomAmount()
    
    @Slot()
    def zoomExtents(self):
        """
        Fits all the nodes in the view.
        """
        rect = self.scene().visibleItemsBoundingRect()
        vrect = self.viewportRect()
        
        if rect.width():
            changed = False
            scene_rect = self.scene().sceneRect()
            
            if scene_rect.width() < rect.width():
                scene_rect.setWidth(rect.width() + 150)
                scene_rect.setX(-scene_rect.width() / 2.0)
                changed = True
            
            if scene_rect.height() < rect.height():
                scene_rect.setHeight(rect.height() + 150)
                scene_rect.setY(-scene_rect.height() / 2.0)
                changed = True
            
            if changed:
                self.scene().setSceneRect(scene_rect)
            
            self.fitInView(rect, Qt.KeepAspectRatio)
        
        if not self.signalsBlocked():
            self.zoomAmountChanged.emit(self.zoomAmount())
        
    @Slot()
    def zoomIn(self):
        """
        Zooms in for this widget by the scene's zoom step amount.
        """
        self.scene().zoomIn()
    
    @Slot()
    def zoomOut(self):
        """
        Zooms out for this widget by the scene's zoom step amount.
        """
        self.scene().zoomOut()
    
    x_isolationMode  = Property(bool, isolationMode, setIsolationMode)
    x_cleanupOnClose = Property(bool, cleanupOnClose, setCleanupOnClose)