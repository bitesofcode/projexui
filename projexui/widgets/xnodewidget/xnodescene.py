#!/usr/bin/python

""" Defines the root QGraphicsScene class for the node system. """

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

import re

from projex.text import nativestring

from projexui.qt import Signal
from projexui.qt.QtCore       import  QLine,\
                                      QRectF,\
                                      Qt,\
                                      QParallelAnimationGroup
                                
from projexui.qt.QtGui        import  QColor, \
                                      QCursor, \
                                      QBrush, \
                                      QGraphicsItem, \
                                      QGraphicsScene, \
                                      QTransform,\
                                      QPen

from projexui.xanimation                            import XObjectAnimation
from projexui.widgets.xnodewidget.xnode             import XNode
from projexui.widgets.xnodewidget.xnodeconnection   import XNodeConnection
from projexui.widgets.xnodewidget.xnodelayer        import XNodeLayer
from projexui.widgets.xnodewidget.xnodelayout       import XNodeLayout

from .xnodepalette import XNodePalette

class XNodeScene(QGraphicsScene):
    """ 
    Defines the base node scene class that will manage all of the node \
    and connection objects for a node graph widget.
    """
    
    # define node signals
    nodeClicked             = Signal( QGraphicsItem )
    nodeDoubleClicked       = Signal( QGraphicsItem )
    nodeMenuRequested       = Signal( QGraphicsItem )
    
    # define connection signals
    connectionDoubleClicked = Signal( QGraphicsItem )
    connectionMenuRequested = Signal( QGraphicsItem )
    connectionRequested     = Signal( QGraphicsItem )
    
    # define scene signals
    menuRequested           = Signal()
    modifiedStateChanged    = Signal()
    selectionFinished       = Signal()
    viewModeChanged         = Signal()
    
    itemDoubleClicked       = Signal( QGraphicsItem )
    itemsRemoved            = Signal()
    
    # members
    def __init__(self, view, cellWidth=20, cellHeight=18):
        """
        Constructor for the XNodeScene class \
        the inputed view will be treated as the main \
        view" that will be affected when the scene \
        modifications occur.  Other views can be \
        associated with the scene (such as an overview \
        view) that will not be affected.

        :param      view        <QGraphicsView>
        :param      cellWidth   <float> || <int>
        :param      cellHeight  <float> || <int>
        """
        super(XNodeScene, self).__init__(view)
        
        # set base QGraphicsScene properties
        w = 1170 * cellWidth
        h = 594 * cellWidth
        
        self.setSceneRect(-w/2.0, -h/2.0, w, h) # center on 0, 0
        self.setObjectName('XNodeScene')
        
        # initialize the main view
        view.setDragMode(view.RubberBandDrag)
        view.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        view.setScene(self)
        
        # create custom parameters
        self._cache                     = set() # caches python pointers or
                                                # memory leaks...
        self._mainView                  = view
        self._minorLines                = []
        self._majorLines                = []
        self._centerLines               = []
        self._cellWidth                 = cellWidth
        self._cellHeight                = cellHeight
        self._minZoomAmount             = 20
        self._maxZoomAmount             = 100
        self._modified                  = False
        self._dirty                     = True
        self._viewMode                  = False
        self._selectionSignalsBlocked   = False
        self._showGrid                  = True
        self._removalQueue              = []
        self._layers                    = []
        self._loading                   = False
        self._isolationMode             = False
        self._activeConnection          = None
        self._currentLayer              = None
        self._palette                   = XNodePalette()
        
        self._defaultNodeClass          = XNode
        self._defaultConnectionClass    = XNodeConnection
        self._defaultLayerClass         = XNodeLayer
        
        # create connections
        self.selectionChanged.connect(self.updateIsolated)
        self.setBackgroundBrush(self._palette.color(XNodePalette.GridBackground))
    
    def __layoutNodes( self, 
                       nodes, 
                       connection_map, 
                       padX,
                       padY,
                       direction,
                       startX = None,
                       startY = None,
                       processed = None ):
        
        # clear out any blank nodes
        while ( None in nodes ):
            nodes.remove(None)
        
        # if no nodes, then exit
        if ( not nodes ):
            return
        
        # phase 01: break nodes into layers
        
        
#        if ( processed is None ):
#            processed = []
        
#        nodes = list(set(nodes).difference(processed))
        
        if ( not nodes ):
            return
        
#        processed += nodes
        
        # start at the first node's location
        if ( startX is None ):
            startX = nodes[0].x()
            
        if ( startY is None ):
            startY = nodes[0].y()
        
        next_x     = startX
        next_y     = startY
        next_level = []
        
        if ( direction == Qt.Horizontal ):
            total_height = sum(map(lambda x: x.rect().height(), nodes))
            total_height += padY * (len(nodes) - 1)
            startY -= (total_height / 2.0)
            
            widths = []
            for node in nodes:
                if ( not node ):
                    continue
                    
                node.setPos(startX, startY)
                startY += node.rect().height() + padY
                widths.append(node.rect().width())
                next_level += connection_map.get(node, [])
            
            next_x = startX + max(widths) + padX
            
        else:
            total_width = sum(map(lambda x: x.rect().width(), nodes))
            total_width += padX * (len(nodes) - 1)
            startX -= (total_width / 2.0)
            
            heights = []
            
            for node in nodes:
                if ( not node ):
                    continue
                
                node.setPos(startX, startY)
                startX += node.rect().width() + padX
                heights.append(node.rect().height())
                next_level += connection_map.get(node, [])
            
            next_y = startY + max(heights) + padY
        
        # layout the next level of nodes
        self.__layoutNodes(list(set(next_level)), 
                           connection_map, 
                           padX, 
                           padY, 
                           direction, 
                           next_x, 
                           next_y,
                           processed)
    
    def activeConnection( self ):
        """
        Returns the active connection instance.  This method is provided \
        for a developer to modify the look and action of the active \
        connection, however is not used internally,  so any refactoring \
        of it will not be used.
      
        :return     <XNodeConnection>
        """
        return self._activeConnection
    
    def addConnection( self, cls = None ):
        """
        Creates a new connection instance in the scene.  If the optional cls \
        parameter is not supplied, then the default connection class will \
        be used when creating the connection.
        
        :param      cls     subclass of <XNodeConnection>
        
        :return     <XNodeConnection> || None
        """
        # make sure we have a valid class
        if ( not cls ):
            cls = self.defaultConnectionClass()
        if ( not cls ):
            return None
        
        # create the new connection
        connection = cls(self)
        connection.setLayer(self.currentLayer())
        self.addItem(connection)
        return connection
    
    def addLayer(self, cls=None):
        """
        Creates a new layer instance for this scene.  If the optional cls \
        parameter is not supplied, then the default layer class will be \
        used when creating the layer.
        
        :param      cls     <subclass of XNodeLayer>
        
        :return     <XNodeLayer> || None
        """
        if ( not cls ):
            cls = self.defaultLayerClass()
            
        if ( not cls ):
            return None
        
        # create the new layer
        layer = cls(self)
        self._layers.append(layer)
        self.setCurrentLayer(layer)
        self.setModified()
        
        return layer
    
    def addItem( self, item ):
        """
        Overloaded from the base QGraphicsScene class to set the modified \
        state for this scene to being modified.
                    
        :param      item        <QGraphicsItem>
        
        :return     <bool> success
        """
        result = super(XNodeScene, self).addItem(item)
        self.setModified()
        self._cache.add(item)
        
        return result
    
    def addNode(self, cls=None, point=None):
        """
        Creates a new node instance in the scene.  If the optional \
        cls parameter is not supplied, then the default node class \
        will be used when creating the node.  If a point is \
        supplied, then the node will be created at that position, \
        otherwise the node will be created under the cursor.
        
        :param      node    subclass of <XNode>
        :param      point   <QPointF>
        
        :return     <XNode> || None
        """
        # make sure we have a valid class
        if not cls:
            cls = self.defaultNodeClass()
            
        if not cls:
            return None
        
        # create the new node
        node = cls(self)
        node.setLayer(self.currentLayer())
        node.rebuild()
        self.addItem(node)
        
        if point == 'center':
            x = self.sceneRect().width() / 2.0
            y = self.sceneRect().height() / 2.0
            
            x -= (node.rect().width() / 2.0)
            y -= (node.rect().height() / 2.0)
            
            node.setPos(x, y)
            
        elif not point:
            pos    = self._mainView.mapFromGlobal(QCursor.pos())
            point  = self._mainView.mapToScene(pos)
            if ( point ):
                x = point.x() - node.rect().width() / 2.0
                y = point.y() - node.rect().height() / 2.0
                node.setPos(x, y)
        else:
            x = float(point.x())
            y = float(point.y())
            node.setPos(x, y)
        
        return node
    
    def alternateGridColor(self):
        """
        Returns the alternate color for the smaller grid lines.
        
        :return     <QColor>
        """
        palette = self.palette()
        return palette.color(palette.GridAlternateForeground)
    
    def autoLayout( self, 
                    padX = None, 
                    padY = None,
                    direction = Qt.Horizontal,
                    layout = 'Layered',
                    animate = 0,
                    centerOn = None,
                    center = None,
                    debug=False ):
        """
        Automatically lays out all the nodes in the scene using the \
        autoLayoutNodes method.
        
        :param      padX | <int> || None | default is 2 * cell width
                    padY | <int> || None | default is 2 * cell height
                    direction | <Qt.Direction>
                    layout | <str> | name of the layout plugin to use
                    animate | <int> | number of seconds to animate over
        
        :return     {<XNode>: <QRectF>, ..} | new rects per affected node
        """
        return self.autoLayoutNodes(self.nodes(), 
                                    padX, 
                                    padY, 
                                    direction, 
                                    layout,
                                    animate,
                                    centerOn,
                                    center,
                                    debug)
    
    def autoLayoutNodes( self, 
                         nodes, 
                         padX = None, 
                         padY = None, 
                         direction = Qt.Horizontal,
                         layout = 'Layered',
                         animate = 0,
                         centerOn = None,
                         center = None,
                         debug=False):
        """
        Automatically lays out all the nodes in the scene using the private \
        autoLayoutNodes method.
        
        :param      nodes | [<XNode>, ..]
                    padX | <int> || None | default is 2 * cell width
                    padY | <int> || None | default is 2 * cell height
                    direction | <Qt.Direction>
                    layout | <str> | name of the layout plugin to use
                    animate | <int> | number of seconds to animate over
        
        :return     {<XNode>: <QRectF>, ..} | new rects per affected node
        """
        plugin = XNodeLayout.plugin(layout)
        if not plugin:
            return 0
        
        if not animate:
            plugin.setTesting(debug)
            results = plugin.layout(self, nodes, center, padX, padY, direction)
            if centerOn:
                self.mainView().centerOn(centerOn)
            return results
        else:
            anim_group = QParallelAnimationGroup(self)
            plugin.setTesting(debug)
            results = plugin.layout(self,
                                   nodes,
                                   center,
                                   padX,
                                   padY,
                                   direction,
                                   anim_group)
            
            if isinstance(centerOn, XNode):
                if centerOn in results:
                    end_center = results[centerOn] + centerOn.rect().center()
                else:
                    end_center = centerOn.sceneRect().center()
                
                anim = XObjectAnimation(self.mainView(), 'centerOn')
                anim.setStartValue(self.mainView().viewportRect().center())
                anim.setEndValue(end_center)
                anim_group.addAnimation(anim)
            
            for i in range(anim_group.animationCount()):
                anim = anim_group.animationAt(i)
                anim.setDuration(1000 * animate)
            
            anim_group.finished.connect(anim_group.deleteLater)
            anim_group.start()
            return results

    def autoLayoutSelected( self, 
                             padX = None,
                             padY = None,
                             direction = Qt.Horizontal,
                             layout = 'Layered',
                             animate = 0,
                             centerOn = None,
                             center = None):
        """
        Automatically lays out all the selected nodes in the scene using the \
        autoLayoutNodes method.
        
        :param      padX | <int> || None | default is 2 * cell width
                    padY | <int> || None | default is 2 * cell height
                    direction | <Qt.Direction>
                    layout | <str> | name of the layout plugin to use
                    animate | <int> | number of seconds to animate over
        
        :return     {<XNode>: <QRectF>, ..} | new rects per node
        """
        nodes = self.selectedNodes()
        return self.autoLayoutNodes(nodes, 
                                    padX, 
                                    padY, 
                                    direction, 
                                    layout, 
                                    animate,
                                    centerOn,
                                    center)
    
    def blockSelectionSignals( self, state ):
        """
        Sets the state for the seleciton finished signal.  When it \
        is set to True, it will emit the signal.  This is used \
        internally to control selection signal propogation, so  \
        should not really be called unless you know why you are \
        calling it.
                    
        :param      state   <bool>
        """
        if ( self._selectionSignalsBlocked == state ):
            return
        
        self._selectionSignalsBlocked = state
        if ( not state ):
            self.emitSelectionFinished()
    
    def calculateBoundingRect(self, nodes):
        """
        Returns the bounding rectangle for the inputed nodes.
        
        :param      nodes | [<XNode>, ..]
        """
        out = QRectF()
        for node in nodes:
            rect = node.rect()
            pos = node.pos()
            
            bounding = QRectF(pos.x(), pos.y(), rect.width(), rect.height())
            out = out.united(bounding)
        
        return out
    
    def cellHeight( self ):
        """
        Returns the cell height parameter for the graph.
        
        :return     <int>
        """
        return self._cellHeight
    
    def cellWidth( self ):
        """
        Returns the cell width parameter for the graph.
        
        :return     <int>
        """
        return self._cellWidth
    
    def centerLineColor(self):
        """
        Returns the color for the center line.
        
        :return     <QColor>
        """
        palette = self.palette()
        return palette.color(palette.GridForeground)
    
    def cleanup( self ):
        """
        Cleans up the scene prior to deletion (called by XNodeWidget)
        """
        self.selectionChanged.disconnect(self.updateIsolated)
        self._mainView = None
    
    def clear( self ):
        """
        Clears the current scene of all the items and layers.
        """
        self.setCurrentLayer(None)
        
        self._layers = []
        self._cache.clear()
        
        super(XNodeScene, self).clear()
    
    def connectSelection( self, cls = None ):
        """
        Creates a connection between the currently selected \
        nodes, provided there are only 2 nodes selected.  If \
        the cls parameter is supplied then that will be the \
        class instance used when creating the connection. \
        Otherwise, the default connection class will be used.
        
        :param      cls         subclass of <XNodeConnection>
        
        :return     <XNodeConnection> || None
        """
        # collect the selected nodes
        nodes = self.selectedNodes()
        if ( len(nodes) != 2 ):
            return None
        
        # create the connection
        con = self.addConnection(cls)
        con.setOutputNode(nodes[0])
        con.setInputNode(nodes[1])
        con.rebuild()
        
        return con
    
    def connections(self, hotspot=None):
        """
        Returns a list of all the connection instances that are in this scene.
                    
        :return     <list>  [ <XNodeConnection>, .. ]
        """
        cons = self.findItems(XNodeConnection)
        if hotspot is not None:
            filt = lambda x: hotspot in (x.inputHotspot(), x.outputHotspot())
            return filter(filt, cons)
        return cons
    
    def currentConnection(self):
        """
        Returns the currently selected connection in the scene. \
        If multiple connections are selected, then the last one \
        selected will be considered the current one.
        
        :return     <XNodeConnection> || None
        """
        connections = self.selectedConnections()
        if ( connections ):
            return connections[-1]
        return None
    
    def currentLayer(self):
        """
        Returns the currently active layer for this scene.
        
        :return     <XNodeLayer> || None
        """
        return self._currentLayer
    
    def currentNode(self):
        """
        Returns the currently selected node in the scene.  If \
        multiple nodes are selected, then the last one selected \ 
        will be considered the current one.
        
        :return     <XNode> || None
        """
        nodes = self.selectedNodes()
        if ( nodes and len(nodes) == 1 ):
            return nodes[0]
        return None
    
    def defaultConnectionClass( self ):
        """
        Returns the default class used when creating connections in the scene.
        
        :return     subclass of <XNodeConnection>
        """
        return self._defaultConnectionClass
    
    def defaultLayerClass( self ):
        """
        Returns the default layer class associated with this scene.
        
        :return     <subclass of XNodeLayer>
        """
        return self._defaultLayerClass
    
    def defaultNodeClass( self ):
        """
        Returns the default class used when creating nodes in the scene.
        
        :return     subclass of <XNode>
        """
        return self._defaultNodeClass
    
    def drawBackground(self, painter, rect):
        """
        Overloads the base QGraphicsScene method to handle \
        drawing the grid for the node scene.  This method should \
        not be called manually but is called internally as part \
        of the painting mechanism for the QGraphicsScene object.
        
        :param      painter     <QPainter>
        :param      rect        <QRect>
        """
        painter.save()
        
        palette = self.palette()
        if not (self._mainView and self._mainView.isEnabled()):
            state = palette.Disabled
        else:
            state = palette.Active
        
        bg          = palette.color(state, palette.GridBackground)
        grid        = palette.color(state, palette.GridForeground)
        agrid       = palette.color(state, palette.GridAlternateForeground)
        lineColor   = palette.color(state, palette.GridCenterline)
        
        brush = self.backgroundBrush()
        brush.setColor(bg)
        
        painter.setBrush(brush)
        painter.drawRect(rect.x() - 1,
                         rect.y() - 1,
                         rect.width() + 2,
                         rect.height() + 2)
        
        # draw the grid if it is currently enabled
        if not self.showGrid():
            painter.restore()
            return
        
        # rebuild the grid if the scene is dirty
        if self.isDirty():
            self.rebuild()
        
        # if we're zoomed in above 50%, then draw the minor grid lines
        if self.zoomAmount() > 50:
            # draw the minor lines
            painter.setPen(agrid)
            painter.drawLines( self._minorLines )
        
        # draw the major grid lines
        painter.setPen(grid)
        painter.drawLines(self._majorLines)
        
        # draw the center lines
        painter.setPen(lineColor)
        painter.drawLines(self._centerLines)
        
        painter.restore()
    
    def emitConnectionRequested( self, connection ):
        """
        Emits the connection requested signal for the inputed connection \
        instance, provided the signals are not currently being blocked.
        
        :param      connection      <XNodeConnection>
        """
        if ( not self.signalsBlocked() ):
            self.connectionRequested.emit(connection)
    
    def emitConnectionMenuRequested( self, connection ):
        """
        Emits the connection menu request signal for the inputed connection \
        instance, provided the signals are not currently being blocked.
        
        :param      connection      <XNodeConnection>
        """
        if ( not self.signalsBlocked() ):
            self.connectionMenuRequested.emit(connection)
    
    def emitNodeMenuRequested( self, node ):
        """
        Emits the node menu requested signal for the inputed node instance, \
        provided the signals are not currently being  blocked.
        
        :param      node            <XNode>
        """
        if ( not self.signalsBlocked() ):
            self.nodeMenuRequested.emit(node)
    
    def emitMenuRequested( self ):
        """
        Emits the menu requested signal for this scene, provided \
        the signals are not currently being blocked.
        """
        if ( not self.signalsBlocked() ):
            self.menuRequested.emit()
    
    def emitModifiedStateChanged( self ):
        """
        Emits that the modified state for this scene has changed, provided \
        the signals are not currently being blocked.
        """
        if ( not self.signalsBlocked() ):
            self.modifiedStateChanged.emit()
    
    def emitSelectionFinished( self ):
        """
        Emits the selection finished signal, provided the signals and \
        selectionSignals are not currently being blocked.
        """
        if ( not (self.signalsBlocked() or self.selectionSignalsBlocked()) ):
            self.selectionFinished.emit()
    
    def emitViewModeChanged( self ):
        """
        Emits the view mode state change signal, provided the signals are \
        not currently being blocked.
        """
        if ( not self.signalsBlocked() ):
            self.viewModeChanged.emit()
    
    def findItems( self, cls ):
        """
        Looks up the items in the scene that inherit from the inputed class.
        
        :param      cls | <type>
        """
        return filter(lambda x: isinstance(x, cls), self.items())
    
    def findLayer( self, layerName ):
        """
        Looks up the layer for this node based on the inputed layer name.
        
        :param      layerName   | <str>
        
        :return     <XNodeLayer>
        """
        for layer in self._layers:
            if ( layer.name() == layerName ):
                return layer
        return None
    
    def findNode( self, objectName ):
        """
        Looks up the node based on the inputed node name.
        
        :param      objectName     | <str>
        """
        for item in self.items():
            if ( isinstance(item, XNode) and 
                 item.objectName() == objectName ):
                return item
        return None
    
    def findNodeByRegex( self, objectRegex ):
        """
        Looks up the first instance of the node who matches the inputed regex
        expression.
        
        :param      objectRegex | <str>
        
        :return     <XNode> || None
        """
        expr = re.compile(nativestring(objectRegex))
        for item in self.items():
            if ( isinstance(item, XNode) and
                 expr.match(item.displayName()) ):
                return item
        return None
    
    def findNodeById( self, objectId ):
        """
        Looks up the node based on the unique node identifier.
        
        :param      nodeId
        """
        for item in self.items():
            if ( isinstance(item, XNode) and item.objectId() == objectId):
                return item
        return None
    
    def forceRemove( self, item ):
        """
        Adds the inputed item to the removal queue that is used when making \
        sure connections are removed along with nodes
                    
        :param      item    <QGraphicsItem>
        """
        if ( not item in self._removalQueue ):
            self.removeItem(item)
    
    def finishConnection(self, accept=True):
        """
        Finishes the active connection.  If the accept value is \
        true, then the connection requested signal will be emited, \
        otherwise, it will simply clear the active connection \
        data.
        
        :param      accept      <bool>
        """
        if not self._activeConnection:
            return
        
        # when accepting, emit the connection requested signal
        if accept:
            self.emitConnectionRequested(self._activeConnection)
            
            # emit the slot for the given node dropzone
            if self._activeConnection.customData('__output__'):
                target = self._activeConnection.inputPoint()
                node   = self.nodeAt(target)
            else:
                target = self._activeConnection.outputPoint()
                node   = self.nodeAt(target)
            
            if node:
                npos = node.mapFromScene(target)
                node.triggerDropzoneAt(npos, self._activeConnection)
        
        # remove the connection
        self.removeItem(self._activeConnection)
        self._activeConnection = None
    
    def gridColor(self):
        """
        Returns the grid color for this instance.
        
        :return     <QColor>
        """
        palette = self.palette()
        return palette.color(palette.GridForeground)
    
    def inViewMode( self ):
        """
        Returns whether or not the scene is currently \
        in view mode.  When in view mode, all interactions \
        will be disabled except for panning and zooming.  A \
        user will be able to enter zoom mode by hitting the \
        spacebar key.
        
        :return     <bool>
        """
        return self._viewMode
    
    def isConnecting( self ):
        """
        Returns whether or not there is an active connection \
        going on in the scene.
                    
        :return     <bool>
        """
        return self._activeConnection != None
    
    def isDirty( self ):
        """
        Returns whether or not the scene is dirty and thus needs a rebuild.
                    
        :return     <bool>
        """
        return self._dirty
    
    def isLoading( self ):
        """
        Used by a loading system to alter the default behavior based on if \
        a file is being loaded or not.
        
        :return     <bool>
        """
        return self._loading
    
    def isModified( self ):
        """
        Returns whehter or not this scene is currently in a modified state.
                    
        :return     <bool>
        """
        return self._modified
    
    def isolationMode( self ):
        """
        Returns whether or not the isolation mode is enabled.  When in 
        isolation mode, only the selected node and its direct connections will
        be displayed.
        
        :return     <bool>
        """
        return self._isolationMode
    
    def keyPressEvent( self, event ):
        """
        Overloads the base QGraphicsScene method to handle individual \
        key overrides.
                    
        :param      event       <QKeyPressEvent>
        """
        # otherwise, eat all other key press events until the 
        # view mode is released
        if ( self.inViewMode() ):
            event.accept()
        
        # when the user presses the space bar, put
        # the scene into view editing mode
        elif ( event.key() == Qt.Key_Space ):
            self.setViewMode(True)
            event.accept()
        
        # cancel the connection if escape is pressed
        elif ( event.key() == Qt.Key_Escape ):
            self.finishConnection(False)
            event.accept()
        
        # otherwise, run the standard key press event
        else:
            super(XNodeScene, self).keyPressEvent(event)
    
    def keyReleaseEvent( self, event ):
        """
        Intercepts the Qt key released event to look for built-in overrides.
        
        :param      event       <QKeyReleaseEvent>
        """
        # when the user releases the space bar, remove
        # the scene view edit override
        if ( event.key() == Qt.Key_Space ):
            self.setViewMode(False)
            event.accept()
        
        # otherwise, eat all other key press events until the 
        # view mode is released
        elif ( self.inViewMode() ):
            event.accept()
        
        # otherwise, handle the event like normal
        else:
            super(XNodeScene, self).keyPressEvent(event)
    
    def layers( self ):
        """
        Returns a list of all the layers associated with this scene.
        
        :return     [<XNodeLayer>, ..]
        """
        return self._layers[:]
    
    def mainView( self ):
        """
        Return the main view that is linked to this scene.
        
        :return     <QGraphicsView>
        """
        return self._mainView
    
    def maxZoomAmount( self ):
        """
        Returns the maximum amount that a user can zoom into to.
        
        :return     <int>
        """
        return self._maxZoomAmount
    
    def minZoomAmount( self ):
        """
        Returns the minimum amount that a user can zoom into to.
        
        :return     <int>
        """
        return self._minZoomAmount
    
    def mouseDoubleClickEvent(self, event):
        """
        Emits the node double clicked event when a node is double clicked.
        
        :param      event | <QMouseDoubleClickEvent>
        """
        super(XNodeScene, self).mouseDoubleClickEvent(event)
        
        # emit the node double clicked signal
        if event.button() == Qt.LeftButton:
            item = self.itemAt(event.scenePos())
            
            if not item:
                self.clearSelection()
            else:
                blocked = self.signalsBlocked()
                self.blockSignals(True)
                self.clearSelection()
                item.setSelected(True)
                self.blockSignals(blocked)
            
                if isinstance(item, XNode) and not blocked:
                    self.nodeDoubleClicked.emit(item)
                elif isinstance(item, XNodeConnection) and not blocked:
                    self.connectionDoubleClicked.emit(item)
                
                if not blocked:
                    self.itemDoubleClicked.emit(item)
    
    def mousePressEvent( self, event ):
        """
        Overloads the base QGraphicsScene method to block the \
        selection signals, otherwise, each time an object is \
        bulk selected the selection changed signal will be \
        emitted.
                    
        :param      event   <QMousePressEvent>
        """
        if event.button() == Qt.MidButton:
            self.setViewMode(True)
            event.accept()
        elif event.button() == Qt.RightButton:
            event.accept()
        else:
            super(XNodeScene, self).mousePressEvent(event)
            self.blockSelectionSignals(True)
    
    def mouseMoveEvent( self, event ):
        """
        Overloads the base QGraphicsScene method to update the active \
        connection if there is one going on.
                    
        :param      event   <QMouseMoveEvent>
        """
        if ( self._activeConnection ):
            if self._activeConnection.customData('__output__'):
                self._activeConnection.setInputPoint(event.scenePos())
            else:
                self._activeConnection.setOutputPoint(event.scenePos())
        
        super(XNodeScene, self).mouseMoveEvent(event)
    
    def mouseReleaseEvent( self, event ):
        """
        Overloads the base QGraphicsScene method to reset the selection \
        signals and finish the connection.
                    
        :param      event   <QMouseReleaseEvent>
        """
        if event.button() == Qt.MidButton:
            self.setViewMode(False)
            event.accept()
            return
        
        super(XNodeScene, self).mouseReleaseEvent(event)
        
        # reset the selection blocked signals
        self.blockSelectionSignals(False)
        
        # finish the connection
        if ( self.isConnecting() ):
            self.finishConnection()
        
        # emit a menu request signal if necessary
        elif ( not event.isAccepted() and event.button() == Qt.RightButton ):
            item = self.itemAt(event.scenePos())
            if isinstance(item, XNode):
                self.emitNodeMenuRequested(item)
            else:
                self.emitMenuRequested()
            event.accept()
    
    def nodes( self ):
        """
        Returns a list of the nodes in this scene.
        
        :return     <list> [ <XNode>, .. ]
        """
        return self.findItems(XNode)
    
    def nodeAt( self, point ):
        """
        Returns the node at the inputed positions.
        
        :return     <XNode>
        """
        items = self.items(point)
        for item in items:
            if ( isinstance(item, XNode) ):
                return item
        return None
    
    def palette(self):
        """
        Returns the palette coloring for this instance.
        
        :return     <XNodePalette>
        """
        return self._palette
    
    def rebuild( self ):
        """
        Rebuilds the grid lines based on the current settings and \
        scene width.  This method is triggered automatically, and \
        shouldn't need to be manually called.
        """
        rect    = self.sceneRect()
        x       = rect.left()
        y       = rect.top()
        w       = rect.width()
        h       = rect.height()
        
        # calculate background gridlines
        cx      = x + (w / 2)
        cy      = y + (h / 2)
        
        self._centerLines = [QLine(cx, rect.top(), cx, rect.bottom()),
                             QLine(rect.left(), cy, rect.right(), cy) ]
        
        # create the horizontal grid lines
        delta           = self.cellHeight()
        minor_lines     = []
        major_lines     = []
        count           = 1
        while delta < (h / 2):
            pos_line = QLine(x, cy + delta, x + w, cy + delta)
            neg_line = QLine(x, cy - delta, x + w, cy - delta)
            
            # every 10th line will be a major line
            if count == 10:
                major_lines.append(pos_line)
                major_lines.append(neg_line)
                count = 1
            else:
                minor_lines.append(pos_line)
                minor_lines.append(neg_line)
            
            # update the current y location
            delta += self.cellHeight()
            count += 1
        
        # create the vertical grid lines
        delta = self.cellWidth()
        count = 1
        while delta < (w / 2):
            pos_line = QLine(cx + delta, y, cx + delta, y + h)
            neg_line = QLine(cx - delta, y, cx - delta, y + h)
            
            # every 10th line will be a major line
            if count == 10:
                major_lines.append(pos_line)
                major_lines.append(neg_line)
                count = 1
            else:
                minor_lines.append(pos_line)
                minor_lines.append(neg_line)
            
            # update the current y location
            delta += self.cellWidth()
            count += 1
        
        # set the line cache
        self._majorLines = major_lines
        self._minorLines = minor_lines
        
        # unmark the scene as being dirty
        self.setDirty(False)
    
    def removeItem( self, item ):
        """
        Overloads the default QGraphicsScene method to handle cleanup and \
        additional removal options for nodes.
        
        :param      item        <QGraphicsItem>
        
        :return     <bool>
        """
        # for nodes and connections, call the prepareToRemove method before 
        # removing
        if ( isinstance( item, XNode ) or 
             isinstance( item, XNodeConnection ) ):
            # make sure this item is ok to remove
            if ( not item.prepareToRemove() ):
                return False
        
        # remove the item using the base class method
        try:
            self._cache.remove(item)
        except KeyError:
            pass
        
        # mark the scene as modified
        self.setModified(True)
        super(XNodeScene, self).removeItem(item)
        
        if not self.signalsBlocked():
            self.itemsRemoved.emit()
        
        return True
    
    def removeItems(self, items):
        """
        Removes all the inputed items from the scene at once.  The \
        list of items will be stored in an internal cache.  When \
        updating a node or connection's prepareToRemove method, \
        any additional items that need to be removed as a result \
        of that object being removed, should use the \
        scene.forceRemove method which will keep track of all the \
        items queued up to remove, so it won't be removed twice.
        
        :sa         forceRemove
        
        :param      items       <list> [ <QGraphicsItem>, .. ]
        
        :return     <int> number removed
        """
        count = 0
        self._removalQueue = items
        blocked = self.signalsBlocked()
        self.blockSignals(True)
        update = set()
        for item in items:
            if isinstance(item, XNodeConnection):
                update.add(item.inputNode())
                update.add(item.outputNode())
            
            if self.removeItem(item):
                count += 1
        
        self.blockSignals(blocked)
        self._removalQueue = []
        
        # update any existing nodes once the connections have been removed
        for node in update.difference(items):
            node.setDirty(True)
        
        if not self.signalsBlocked():
            self.itemsRemoved.emit()
        
        return count
    
    def removeSelection( self ):
        """
        Removes the current selected items by calling the removeItems method.
        
        :sa         removeItems
        
        :return     <int> number removed
        """
        results = self.removeItems( self.selectedItems() )
        self.emitSelectionFinished()
        return results
    
    def selectAll( self ):
        """
        Selects all the items in the scene.
        """
        currLayer = self._currentLayer
        for item in self.items():
            layer = item.layer()
            if ( layer == currLayer or not layer ):
                item.setSelected(True)
    
    def selectInvert( self ):
        """
        Inverts the currently selected items in the scene.
        """
        currLayer = self._currentLayer
        for item in self.items():
            layer = item.layer()
            if ( layer == currLayer or not layer ):
                item.setSelected(not item.isSelected())
    
    def selectNone( self ):
        """
        Deselects all the items in the scene.
        """
        currLayer = self._currentLayer
        for item in self.items():
            layer = item.layer()
            if ( layer == currLayer or not layer ):
                item.setSelected(False)
    
    def selectedConnections( self ):
        """
        Returns a list of the selected connections in a scene.
        
        :return     <list> [ <XNodeConnection>, .. ]
        """
        output = []
        for item in self.selectedItems():
            if ( isinstance(item, XNodeConnection) ):
                output.append(item)
        return output
    
    def selectedNodes( self ):
        """
        Returns a list of the selected nodes in a scene.
        
        :return     <list> [ <XNode>, .. ]
        """
        output = []
        for item in self.selectedItems():
            if ( isinstance(item, XNode) ):
                output.append(item)
        return output
    
    def selectionSignalsBlocked( self ):
        """
        Returns whether or not the selection signals are \
        currently being blocked.
        
        :return     <bool>
        """
        return self._selectionSignalsBlocked
    
    def setAlternateGridColor(self, color):
        """
        Sets the alternate color for the smaller grid lines.
        
        :param     color | <QColor>
        """
        palette = self.palette()
        palette.setColor(palette.GridAlternateForeground, QColor(color))
    
    def setBackgroundBrush(self, brush):
        """
        Sets the background brush for this node scene.  This will
        replace the default method as a convenience wrapper around the
        XNodePalette associated with this scene.
        
        :param     color | <str> || <QColor> || <QBrush>
        """
        if type(brush) == str:
            brush = QBrush(QColor(brush))
        elif type(brush) == QColor:
            brush = QBrush(brush)
        elif type(brush) != QBrush:
            return
        
        # update the palette color
        palette = self.palette()
        palette.setColor(palette.GridBackground, brush.color())
        
        super(XNodeScene, self).setBackgroundBrush(brush)
    
    def setCenterLineColor(self, color):
        """
        Sets the color for the center line.
        
        :return     <QColor>
        """
        palette = self.palette()
        palette.setColor(palette.GridCenterline, QColor(color))
    
    def setCurrentLayer(self, layer):
        """
        Sets the current layer for this scene to the inputed layer.
        
        :param      layer | <XNodeLayer> || None
        """
        if self._currentLayer == layer:
            return False
        
        old = self._currentLayer
        self._currentLayer = layer
        
        if old is not None:
            old.sync()
        if layer is not None:
            layer.sync()
        
        self.selectionFinished.emit()
        self.invalidate()
        
        return True
    
    def setCurrentNode(self, node):
        """
        Sets the currently selected node in the scene.  If \
        multiple nodes are selected, then the last one selected \ 
        will be considered the current one.
        
        :param      node | <XNode> || None
        """
        self.blockSignals(True)
        self.clearSelection()
        if node:
            node.setSelected(True)
        self.blockSignals(False)
    
    def setDirty( self, state = True ):
        """
        Flags the scene as being dirty based on the inputed \
        state value if the scene is dirty, then a rebuild will \
        be triggered on the next paint event.
        
        :param      state   <bool>
        """
        self._dirty = state
    
    def setLoading( self, state = True ):
        """
        Sets whether or not the scene is in a loading state.
        
        :param      state | <bool>
        """
        self._loading = state
    
    def setModified( self, state = True ):
        """
        Flags the scene as being modified based on the inputed value.
        
        :param      state   <bool>
        """
        if ( state == self._modified ):
            return
            
        self._modified = state
        self.emitModifiedStateChanged()
    
    def setCellHeight( self, height ):
        """
        Sets the current height of the grid's cells.
        
        :param      height      <float>
        """
        self._cellHeight = height
        self.setDirty()
    
    def setCellWidth( self, width ):
        """
        Sets the current width of the grid's cells.
        
        :param      width       <float>
        """
        self._cellWidth = width
        self.setDirty()
    
    def setDefaultConnectionClass( self, cls ):
        """
        Defines the connection class that will be \
        used when the addConnection method is called, \
        and for the activeConnection method when a user \
        creates a connection through the interface.
        
        :param      cls     subclass of <XNodeConnection>
        """
        self._defaultConnectionClass = cls
    
    def setDefaultLayerClass( self, cls ):
        """
        Defines the default class that will be used when the addLayer \
        method is called.
        
        :param      cls | <subclass of XNodeLayer>
        """
        self._defaultLayerClass = cls
    
    def setDefaultNodeClass( self, cls ):
        """
        Defines the node class that will be used when the addNode \
        method is called.
        
        :param      cls     subclass of <XNode>
        """
        self._defaultNodeClass = cls
    
    def setGridColor(self, color):
        """
        Sets the color for the grid for this instance to the given color.
        
        :param      color | <QColor>
        """
        palette = self.palette()
        palette.setColor(palette.GridForeground, QColor(color))
    
    def setIsolationMode( self, state ):
        """
        Sets whether or not this widget is in isolation mode.  When in 
        isolation, only the selected node and its direct connections will be
        displayed.
        
        :param      state | <bool>
        """
        self._isolationMode = state
        self.updateIsolated(force = True)
        self.update()
    
    def setMaxZoomAmount( self, amount ):
        """
        Sets the maximum amount that a user can zoom into to.  Default is 100.
        
        :param      amount | <int>
        """
        self._maxZoomAmount = amount
        view = self.mainView()
        if view:
            view.maxZoomAmountChanged.emit(amount)
    
    def setMinZoomAmount( self, amount ):
        """
        Sets the minimum amount that a user can zoom into to.  Default is 100.
        
        :param      amount | <int>
        """
        self._minZoomAmount = amount
        view = self.mainView()
        if view:
            view.minZoomAmountChanged.emit(amount)
    
    def setPalette(self, palette):
        """
        Sets the palette for this instance to the inputed palette.
        
        :param      palette | <XNodePalette>
        """
        self._palette = XNodePalette(palette)
    
    def setSceneRect(self, *args):
        """
        Overloads the base QGraphicsScene method to set the scene as \
        dirty to trigger a rebuild on draw.
        
        :param      *args | <QRectF> || <int> x, <int> y, <int> w, <int> h
        """
        super(XNodeScene, self).setSceneRect(*args)
        self.setDirty()
    
    def setShowGrid( self, state = True ):
        """
        Flags whether or not the grid should be drawn in the scene.
        
        :param      state   <bool>
        """
        self._showGrid = state
    
    def setViewMode( self, state = True ):
        """
        Starts the view mode for moving around the scene.
        """
        if self._viewMode == state:
            return
            
        self._viewMode = state
        if state:
            self._mainView.setDragMode( self._mainView.ScrollHandDrag )
        else:
            self._mainView.setDragMode( self._mainView.RubberBandDrag )
            
        self.emitViewModeChanged()
    
    def setZoomAmount(self, amount):
        """
        Sets the zoom level for the current scene, updating all the \
        views that it is connected to.
        
        :param      amount      <int>  (100 based %)
        """
        amount = max(self._minZoomAmount, amount)
        amount = min(self._maxZoomAmount, amount)
        
        # only update when necessary
        if amount == self.zoomAmount():
            return
        
        # calculate the scalar value
        scale = (amount / 100.0)
        
        # assign the new transform to all of the views
        view = self.mainView()
        view.setTransform(QTransform.fromScale(scale, scale))
        
        # emit the value changed signal for the scene
        if not (self.signalsBlocked() or view.signalsBlocked()):
            view.zoomAmountChanged.emit(amount)
    
    def showGrid( self ):
        """
        Returns whether or not the grid will be displayed when the \
        scene is drawn.
        
        :return     <bool>
        """
        return self._showGrid
    
    def startConnection( self, point, cls=None, output=True ):
        """
        Starts creating a new connection from the given output point.  \
        If a connection class is not provided, then the \
        defaultConnectionClass will be used.
        
        :param      point           <QPointF>
                    cls             subclass of <XNodeConnection>
                    output          <bool>
        """
        # clear the last connection
        self.finishConnection(False)
        
        # create a new connection
        self._activeConnection = self.addConnection(cls)
        if self._activeConnection:
            self._activeConnection.setOutputPoint(point)
            self._activeConnection.setInputPoint(point)
            self._activeConnection.setCustomData('__output__', output)
        
        return self._activeConnection
    
    def toggleViewMode( self ):
        """
        Toggles the current view control state.
        """
        self.setViewMode( not self.inViewMode() )
    
    def uniqueNodeName( self, name ):
        """
        Looks up the next available name for the inputed node name.
        
        :param      name    <str>
        """
        nodenames   = []
        for node in self.items():
            if ( isinstance(node, XNode) ):
                nodenames.append( node.objectName() )
        
        basename    = nativestring(name)
        index       = 1
        name        = basename
        
        while ( name in nodenames ):
            name = '%s%02i' % (basename, index)
            index += 1
        
        return name
    
    def updateIsolated( self, force = False ):
        """
        Updates the visible state of nodes based on whether or not they are
        isolated.
        """
        if ( not (self.isolationMode() or force) ):
            return
        
        # make sure all nodes are not being hidden because of isolation
        if ( not self.isolationMode() ):
            for node in self.nodes():
                node.setIsolateHidden(False)
            return
        
        # make sure all the nodes are visible or hidden based on the selection
        selected_nodes  = self.selectedNodes()
        isolated_nodes  = set(selected_nodes)
        connections     = self.connections()
        for connection in connections:
            in_node  = connection.inputNode()
            out_node = connection.outputNode()
            
            if ( in_node in selected_nodes or out_node in selected_nodes ):
                isolated_nodes.add(in_node)
                isolated_nodes.add(out_node)
        
        for node in self.nodes():
            node.setIsolateHidden(not node in isolated_nodes)
    
    def visibleItemsBoundingRect(self):
        """
        Returns the bounding rect for the visible items in the scene.
        
        :return     <QRectF>
        """
        return self.calculateBoundingRect(self.visibleNodes())
    
    def visibleNodes(self):
        """
        Returns a list of the visible nodes in the scene.
        
        :return     [<XNode>, ..]
        """
        return filter(lambda x: isinstance(x, XNode) and x.isVisible(),
                      self.items())
    
    def wheelEvent( self, event ):
        """
        Overloads the base QGraphicsScene wheelEvent method to \
        use scrolling as a zooming mechanism, if the system \
        is currently in the view mode.
        
        :param      event   <QWheelEvent>
        """
        # check to see if the system is
        # currently in view mode
        if ( self.inViewMode() ):
            if ( event.delta() < 0 ):
                self.zoomOut()
            else:
                self.zoomIn()
            
            event.accept()
            self.mainView().setFocus()
        
        else:
            super(XNodeScene, self).wheelEvent(event)
    
    def zoomAmount( self ):
        """
        Returns the current zoom level.
        
        :return     <int>
        """
        return self._mainView.transform().m11() * 100
    
    def zoomIn( self ):
        """
        Zooms in by 20%.
        """
        self.setZoomAmount(self.zoomAmount() + 20)
    
    def zoomOut( self ):
        """
        Zooms out by 20%.
        """
        self.setZoomAmount(self.zoomAmount() - 20)