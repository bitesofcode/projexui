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

import time

from projex.decorators import abstractmethod
from projex.plugin import Plugin
from projexui.qt.QtCore import Qt, QPointF, QRectF
from projexui.qt.QtGui import QApplication
from projexui.widgets.xnodewidget.xnode import XNodeAnimation, XNode

class XNodeLayout(Plugin):
    def __init__(self, *args, **kwds):
        super(XNodeLayout, self).__init__(*args, **kwds)
        
        self._testing = False
        
    def connectionMap(self, scene, nodes):
        """
        Generates a mapping for the nodes to each other based on their
        connections.
        
        :param      nodes | [<XNode>, ..]
        
        :return     {<XNode>: ([<XNode> input, ..], [<XNode> output, ..]), ..}
        """
        output = {}
        connections = scene.connections()
        
        for node in nodes:
            inputs = []
            outputs = []
            
            for connection in connections:
                in_node = connection.inputNode()
                out_node = connection.outputNode()
                
                if node == in_node:
                    inputs.append(out_node)
                elif node == out_node:
                    outputs.append(in_node)
                
            output[node] = (inputs, outputs)
        
        return output
    
    @abstractmethod('XNodeLayout')
    def layout(self,
               scene,
               nodes,
               center=None,
               padX=None,
               padY=None,
               direction=None,
               animationGroup=None):
        """
        Lays out the nodes in the scene for this plugin.  The root node layout
        class defines no implementation for this, and needs to be 
        re-implemented.
        
        If the animationGroup parameter is specified, then this layout should
        generate the node animations that will be required for each node as
        they move during the animation.
        
        :param      scene          | <XNodeScene>
                    nodes          | [<XNode>, ..]
                    center         | <QPointF> || None
                    padX           | <int> || None
                    padY           | <int> || None
                    direction      | <Qt.Direction>
                    animationGroup | <QAnimationGroup> || None
        
        :return     {<XNode>: <QRectF>, ..} | new rects per affected node
        """
        return {}
    
    def runTest(self, 
                scene, 
                padX=None, 
                padY=None, 
                direction=Qt.Horizontal):
        """
        Sets up a test for the node layout.
        """
        nodes = {}
        for letter in 'abcdefghi':
            node = scene.addNode(point='center')
            node.setDisplayName(letter)
            nodes[letter] = node
        
        for con in ('ea', 'eb', 'bf', 'cf', 'gc', 'gd', 'di', 'hi', 'ec', 'ia'):
            o_node = nodes[con[0]]
            i_node = nodes[con[1]]
            
            connection = scene.addConnection()
            connection.setInputNode(i_node)
            connection.setOutputNode(o_node)
        
        self._testing = True
        self.layout(scene, nodes.values(), padX, padY, direction)
        self._testing = False
    
    def setTesting(self, state=True):
        self._testing = state

#----------------------------------------------------------

class XLayeredNodeLayout(XNodeLayout):
    def __init__(self):
        super(XLayeredNodeLayout, self).__init__('Layered')
        
        # register plugin information
        self.setAuthor('Projex Software')
        self.setEmail('team@projexsoftware.com')
        self.setUrl('dev.projexsoftware.com')
        
        # caches the connection map information for comparisons
        self._connectionMap = {}
    
    def calculateDepth(self, node, connections, recurse=None):
        if recurse is None:
            recurse = []
        
        if node in recurse:
            return 0

        recurse.append(node)
        inputs = connections[node][0]
        if len(inputs) == 0:
            return 0
        
        in_depths = [self.calculateDepth(input, connections, recurse) \
                     for input in inputs]
        
        return 1 + max(in_depths)
    
    def collectLayer(self, node, connections, layerset, level=0, recurse=None):
        if recurse is None:
            recurse = []
        
        if node in recurse:
            return
        
        recurse.append(node)
        layerset.setdefault(level, [])
        layerset[level].append(node)
        
        for output in connections[node][1]:
            self.collectLayer(output, connections, layerset,
                              level+1, recurse)

    def generateLayers(self, scene, nodes, connections):
        """
        Breaks the nodes into layers by grouping the nodes together based on
        their connection scheme.
        
        :param      nodes | [<XNode>, ..]
        """
        depth = {}
        for node in nodes:
            depth[node] = (self.calculateDepth(node, connections),
                           len(connections[node][0]))
        
        ordered = depth.keys()
        ordered.sort(key=lambda x: depth[x])
        
        layers = {}
        processed = []
        for node in ordered:
            self.collectLayer(node, connections, layers, recurse=processed)
        
        return [v for _, v in sorted(layers.items())]

    def layout(self,
               scene,
               nodes,
               center=None,
               padX=None,
               padY=None,
               direction=None,
               animationGroup=None):
        """
        Lays out the nodes for this scene based on a block layering algorithm.
        
        :param      scene          | <XNodeScene>
                    nodes          | [<XNode>, ..]
                    center         | <QPointF> || None
                    padX           | <int> || None
                    padY           | <int> || None
                    direction      | <Qt.Direction>
                    animationGroup | <QAnimationGroup> || None
        
        :return     {<XNode>: <QRectF>, ..} | new rects per affected node
        """
        nodes = filter(lambda x: x is not None and x.isVisible(), nodes)
        
        # make sure we have at least 1 node, otherwise, it is already laid out
        if not nodes or len(nodes) == 1:
            return {}
        
        # calculate the default padding based on the scene
        if padX == None:
            if direction == Qt.Vertical:
                padX = 2 * scene.cellWidth()
            else:
                padX = 4 * scene.cellWidth()
            
        if padY == None:
            if direction == Qt.Vertical:
                padY = 4 * scene.cellHeight()
            else:
                padY = 2 * scene.cellWidth()
        
        # step 1: create a mapping of the connections
        connection_map = self.connectionMap(scene, nodes)
        
        # step 2: organize the nodes into layers based on their connection chain
        layers = self.generateLayers(scene, nodes, connection_map)
        
        # step 3: calculate the total dimensions for the layout
        bounds = QRectF()
        
        # step 3.1: compare the nodes together that have common connections
        layer_widths = []
        layer_heights = []
        node_heights = {}
        node_widths = {}
        
        for layer_index, layer in enumerate(layers):
            layer_w = 0
            layer_h = 0
            
            layer_node_w = []
            layer_node_h = []
            
            for node in layer:
                rect = node.rect()
                
                layer_node_w.append(rect.width())
                layer_node_h.append(rect.height())
                
                if direction == Qt.Vertical:
                    layer_w += rect.width()
                    layer_h = max(rect.height(), layer_h)
                else:
                    layer_w = max(rect.width(), layer_w)
                    layer_h += rect.height()
            
            # update the bounding area
            if direction == Qt.Vertical:
                layer_w += padX * 1 - len(layer)
                bounds.setWidth(max(layer_w, bounds.width()))
                bounds.setHeight(bounds.height() + layer_h)
            else:
                layer_h += padY * 1 - len(layer)
                bounds.setWidth(bounds.width() + layer_w)
                bounds.setHeight(max(layer_h, bounds.height()))
            
            node_widths[layer_index] = layer_node_w
            node_heights[layer_index] = layer_node_h
            
            layer_widths.append(layer_w)
            layer_heights.append(layer_h)
            
        if not center:
            center = scene.sceneRect().center()
        
        w = bounds.width()
        h = bounds.height()
        bounds.setX(center.x() - bounds.width() / 2.0)
        bounds.setY(center.y() - bounds.height() / 2.0)
        bounds.setWidth(w)
        bounds.setHeight(h)
        
        # step 4: assign positions for each node by layer
        processed_nodes = {}
        layer_grps = [(i, layer) for i, layer in enumerate(layers)]
        layer_grps.sort(key=lambda x: len(x[1]))
        
        used_rects = [n.sceneRect() for n in scene.nodes() if not n in nodes]
        
        for layer_index, layer in reversed(layer_grps):
            layer_width  = layer_widths[layer_index]
            layer_height = layer_heights[layer_index]
            
            # determine the starting point for this layer
            if direction == Qt.Vertical:
                offset = layer_index * padY + sum(layer_heights[:layer_index])
                point = QPointF(bounds.x(), offset + bounds.y())
            else:
                offset = layer_index * padX + sum(layer_widths[:layer_index])
                point = QPointF(offset + bounds.x(), bounds.y())
            
            # assign node positions based on existing connections
            for node_index, node in enumerate(layer):
                max_, min_ = (None, None)
                inputs, outputs = connection_map[node]
                for connected_node in inputs + outputs:
                    if not connected_node in processed_nodes:
                        continue
                    
                    npos  = processed_nodes[connected_node]
                    nrect = connected_node.rect()
                    rect  = QRectF(npos.x(), 
                                   npos.y(), 
                                   nrect.width(), 
                                   nrect.height())
                    
                    if direction == Qt.Vertical:
                        if min_ is None:
                            min_ = rect.left()
                        min_ = min(rect.left(), min_)
                        max_ = max(rect.right(), max_)
                    else:
                        if min_ is None:
                            min_ = rect.top()
                        min_ = min(rect.top(), min_)
                        max_ = max(rect.bottom(), max_)
                
                if direction == Qt.Vertical:
                    off_x = 0
                    off_y = (layer_height - node.rect().height()) / 2.0
                    start_x = (bounds.width() - layer_width)
                    start_y = 0
                else:
                    off_x = (layer_width - node.rect().width()) / 2.0
                    off_y = 0
                    start_x = 0
                    start_y = (bounds.height() - layer_height)
                
                # align against existing nodes
                point_x = -1
                point_y = -1
                offset = 0
                before = True
                found_point = True
                new_rect = QRectF()
                
                while found_point:
                    if not None in (min_, max_):
                        if direction == Qt.Vertical:
                            off_x = (max_ - min_)/2.0 - node.rect().width()/2.0
                            
                            if before:
                                off_x -= offset
                                offset += node.rect().width() + padX
                            else:
                                off_x += offset
                            
                            point_x = min_ + off_x
                            point_y = point.y() + off_y
                        else:
                            off_y = (max_ - min_)/2.0 - node.rect().height()/2.0
                            
                            if before:
                                off_y -= offset
                                offset += node.rect().height() + padY
                            else:
                                off_y += offset
                            
                            point_x = point.x() + off_x
                            point_y = min_ + off_y
                        
                    # otherwise, align based on its position in the layer
                    else:
                        if direction == Qt.Vertical:
                            off_x  = sum(node_widths[layer_index][:node_index])
                            off_x += node_index * padX
                            off_x += start_x
                            
                            if before:
                                off_x -= offset
                                offset += node.rect().width() + padX
                            else:
                                off_x += offset
                            
                            point_x = point.x() + off_x
                            point_y = point.y() + off_y
                        else:
                            off_y  = sum(node_heights[layer_index][:node_index])
                            off_y += node_index * padY
                            off_y += start_y
                            
                            if before:
                                off_y -= offset
                                offset += node.rect().height() + padY
                            else:
                                off_y += offset
                            
                            point_x = point.x() + off_x
                            point_y = point.y() + off_y
                    
                    # determine if we've already used this point before
                    before = not before
                    found_point = False
                    orect = node.rect()
                    new_rect = QRectF(point_x, point_y,
                                      orect.width(), orect.height())
                    for used_rect in used_rects:
                        if used_rect.intersects(new_rect):
                            found_point = True
                            break
                
                used_rects.append(new_rect)
                
                if not animationGroup:
                    node.setPos(point_x, point_y)
                else:
                    anim = XNodeAnimation(node, 'setPos')
                    anim.setStartValue(node.pos())
                    anim.setEndValue(QPointF(point_x, point_y))
                    animationGroup.addAnimation(anim)
                    
                processed_nodes[node] = QPointF(point_x, point_y)
                
                if self._testing:
                    QApplication.processEvents()
                    time.sleep(0.5)
        
        return processed_nodes

XNodeLayout.register(XLayeredNodeLayout())
