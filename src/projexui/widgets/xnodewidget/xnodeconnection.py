#!/usr/bin/python

"""
Defines the most basic Connection class type for creating
nodes within the projex node scene system.
"""

# define authorship information
__authors__ = ['Eric Hulser']
__author__ = ','.join(__authors__)
__credits__ = []
__copyright__ = 'Copyright (c) 2011, Projex Software'
__license__ = 'LGPL'

# maintanence information
__maintainer__ = 'Projex Software'
__email__ = 'team@projexsoftware.com'

# ------------------------------------------------------------------------------

from projex.text import nativestring

from projexui.qt.QtCore import Qt, \
    QPointF, \
    QRectF

from projexui.qt.QtGui import QGraphicsPathItem, \
    QPainterPath, \
    QPen, \
    QPolygonF, \
    QTransform, \
    QApplication, \
    QGraphicsTextItem, \
    QFontMetrics

from projex.enum import enum

from projexui.widgets.xnodewidget.xnodelayer import XNodeLayer

# create the common enumerated types needed
XConnectionStyle = enum('Linear',
                        'Block',
                        'Smooth')

XConnectionLocation = enum('Top',
                           'Bottom',
                           'Left',
                           'Right')


class XNodeConnection(QGraphicsPathItem):
    """ 
    Defines the base graphics item class that is used to draw a connection
    between two nodes.
    """
    Style = XConnectionStyle
    Location = XConnectionLocation
    ArrowStyle = enum('Filled', 'Inverted')

    def __init__(self, scene):
        self._visible = True

        super(XNodeConnection, self).__init__()

        palette = scene.palette()

        # define custom properties
        self._textItem = None
        self._polygons = []
        self._style = XConnectionStyle.Linear
        self._padding = 20
        self._squashThreshold = 10
        self._showDirectionArrow = False
        self._highlightPen = QPen(palette.color(palette.ConnectionHighlight))
        self._disabledPen = QPen(palette.color(palette.Disabled, palette.Connection))
        self._disableWithLayer = False
        self._enabled = True
        self._dirty = True
        self._customData = {}
        self._layer = None
        self._font = QApplication.instance().font()
        self._text = ''

        self._inputNode = None
        self._inputFixedY = None
        self._inputFixedX = None
        self._inputHotspot = None
        self._inputPoint = QPointF()
        self._inputLocation = XConnectionLocation.Left
        self._autoCalculateInputLocation = False
        self._showInputArrow = False
        self._inputArrowStyle = self.ArrowStyle.Filled

        self._outputNode = None
        self._outputFixedX = None
        self._outputFixedY = None
        self._outputHotspot = None
        self._outputPoint = QPointF()
        self._outputLocation = XConnectionLocation.Right
        self._autoCalculateOutputLocation = False
        self._showOutputArrow = False
        self._outputArrowStyle = self.ArrowStyle.Filled

        # set standard properties
        self.setFlags(self.ItemIsSelectable)
        self.setZValue(-1)
        self.setPen(palette.color(palette.Connection))
        self.setLayer(scene.currentLayer())

    def autoCalculateInputLocation(self):
        """
        :remarks    Returns whether or not to auto calculate the input
                    location based on the proximity to the output node
                    or point.
        
        :deprecated This method is no longer needed, it will be determined
                    based on possible input locations
        
        :return     <bool>
        """
        return self._autoCalculateInputLocation

    def autoCalculateOutputLocation(self):
        """
        :remarks    Returns whether or not to auto calculate the input
                    location based on the proximity to the output node
                    or point.
        
        :deprecated This method is no longer needed, it will be determined
                    based on possible output locations
        
        :return     <bool>
        """
        return self._autoCalculateOutputLocation

    def connectSignals(self, node):
        """
        :remarks    Connects to signals of the inputed node, if the node
                    is a valid XNode type.
        
        :param      node    <XNode> || None
        
        :return     <bool> success
        """
        from projexui.widgets.xnodewidget.xnode import XNode

        # make sure we're connecting to a valid node
        if not isinstance(node, XNode):
            return False

        node.dispatch.geometryChanged.connect(self.setDirty)
        node.dispatch.visibilityChanged.connect(self.setDirty)
        node.dispatch.removed.connect(self.forceRemove)
        return True

    def controlPoints(self):
        """
        :remarks    Generates the control points for this path
        
        :return     <list> [ <tuple> ( <float> x, <float> y), .. ]
        """
        # define input variables
        in_point = self.inputPoint()
        in_rect = self.inputRect()

        in_x = in_point.x()
        in_y = in_point.y()

        in_cx = in_rect.center().x()
        in_cy = in_rect.center().y()
        in_left = in_rect.left()
        in_right = in_rect.right()
        in_top = in_rect.top()
        in_bot = in_rect.bottom()
        in_loc = self.inputLocation()

        # define output variables
        out_point = self.outputPoint()
        out_rect = self.outputRect()

        out_x = out_point.x()
        out_y = out_point.y()

        out_cx = out_rect.center().x()
        out_cy = out_rect.center().y()
        out_left = out_rect.left()
        out_right = out_rect.right()
        out_top = out_rect.top()
        out_bot = out_rect.bottom()
        out_loc = self.outputLocation()

        # define global variables
        pad = self.squashThreshold()
        loc_left = XConnectionLocation.Left
        loc_right = XConnectionLocation.Right
        loc_top = XConnectionLocation.Top
        loc_bot = XConnectionLocation.Bottom

        # calculate deltas
        delta_x = abs(in_x - out_x)
        delta_y = abs(in_y - out_y)
        buffer = 2

        # calculate point scenarios

        # right -> left
        if (out_loc & loc_right) and (in_loc & loc_left) and out_right < in_left:
            # no y change, bounding rects don't overlap
            if delta_y < buffer:
                return [(out_x, out_y), (in_x, in_y)]

            # y change, padding deltas don't overlap
            elif out_right + pad < in_left - pad:
                return [(out_x, out_y),
                        (out_x + delta_x / 2.0, out_y),
                        (out_x + delta_x / 2.0, in_y),
                        (in_x, in_y)]

        # left -> right
        if (out_loc & loc_left) and (in_loc & loc_right) and in_right < out_left:
            # no y change, bounding rects don't overlap
            if delta_y < buffer and in_x < out_x:
                return [(out_x, out_y), (in_x, in_y)]

            # y change, padding deltas don't overlap
            elif in_left + pad < out_right - pad:
                return [(out_x, out_y),
                        (out_x - delta_x / 2.0, out_y),
                        (out_x - delta_x / 2.0, in_y),
                        (in_x, in_y)]

        # bottom -> top
        if (out_loc & loc_bot) and (in_loc & loc_top) and out_bot < in_top:
            # no x change, bounding rects don't overlap
            if delta_x < buffer and out_y < in_y:
                return [(out_x, out_y), (in_x, in_y)]

            # x change, pading delta's don't overlap
            elif out_bot + pad < in_top - pad:
                return [(out_x, out_y),
                        (out_x, out_y + delta_y / 2.0),
                        (in_x, out_y + delta_y / 2.0),
                        (in_x, in_y)]

        # top -> bottom
        if (out_loc & loc_top) and (in_loc & loc_bot) and in_bot < out_top:
            # no x change, bounding rects don't overlap
            if delta_x < buffer and in_y < out_y:
                return [(out_x, out_y), (in_x, in_y)]

            # y change, padding deltas don't overlap
            elif in_bot + pad < out_top - pad:
                return [(out_x, out_y),
                        (out_x, out_y - delta_y / 2.0),
                        (in_x, out_y - delta_y / 2.0),
                        (in_x, in_y)]

        # bottom -> left
        if (out_loc & loc_bot) and (in_loc & loc_left):
            if out_y + pad < in_y and out_x + pad < in_x:
                return [(out_x, out_y),
                        (out_x, in_y),
                        (in_x, in_y)]

        # bottom -> right
        if (out_loc & loc_bot) and (in_loc & loc_right):
            if out_y + pad < in_y and out_x - pad > in_x:
                return [(out_x, out_y),
                        (out_x, in_y),
                        (in_x, in_y)]

        # top -> left
        if (out_loc & loc_top) and (in_loc & loc_left):
            if in_y + pad < out_y and out_x + pad < in_x:
                return [(out_x, out_y),
                        (out_x, in_y),
                        (in_x, in_y)]

        # top -> right
        if (out_loc & loc_top) and (in_loc & loc_right):
            if in_y + pad < out_y and out_x - pad > in_x:
                return [(out_x, out_y),
                        (out_x, in_y),
                        (in_x, in_y)]

        # right -> top
        if (out_loc & loc_right) and (in_loc & loc_top):
            if out_x + pad < in_x and out_y - pad < in_y:
                return [(out_x, out_y),
                        (in_x, out_y),
                        (in_x, in_y)]

        # right -> bottom
        if (out_loc & loc_right) and (in_loc & loc_bot):
            if out_x + pad < in_x and out_y + pad > in_y:
                return [(out_x, out_y),
                        (in_x, out_y),
                        (in_x, in_y)]

        # left -> top
        if (out_loc & loc_left) and (in_loc & loc_top):
            if in_x + pad < out_x and out_y - pad < in_y:
                return [(out_x, out_y),
                        (in_x, out_y),
                        (in_x, in_y)]

        # left -> bottom
        if (out_loc & loc_left) and (in_loc & loc_bot):
            if in_x + pad < out_x and out_y + pad > in_y:
                return [(out_x, out_y),
                        (in_x, out_y),
                        (in_x, in_y)]

        # right -> right
        if (out_loc & loc_right) and (in_loc & loc_right):
            max_x = max(out_right + 2 * pad, in_right + 2 * pad)
            if out_cx <= in_cx or not (out_loc & loc_left and in_loc & loc_left):
                return [(out_x, out_y),
                        (max_x, out_y),
                        (max_x, in_y),
                        (in_x, in_y)]

        # left -> left
        if (out_loc & loc_left) and (in_loc & loc_left):
            min_x = min(out_left - 2 * pad, in_left - 2 * pad)
            return [(out_x, out_y),
                    (min_x, out_y),
                    (min_x, in_y),
                    (in_x, in_y)]

        # top -> top
        if (out_loc & loc_top) and (in_loc & loc_top):
            if out_cy <= in_cy or not (out_loc & loc_bot and in_loc & loc_bot):
                min_y = min(out_top - 2 * pad, in_top - 2 * pad)
                return [(out_x, out_y),
                        (out_x, min_y),
                        (in_x, min_y),
                        (in_x, in_y)]

        # bottom -> bottom
        if (out_loc & loc_bot) and (in_loc & loc_bot):
            max_y = max(out_y + 2 * pad, out_y + 2 * pad)
            return [(out_x, out_y),
                    (out_x, max_y),
                    (in_x, max_y),
                    (in_x, in_y)]

        # right -> left with center squash
        if (out_loc & loc_right) and (in_loc & loc_left):
            if out_bot < in_top:
                mid_y = out_bot + (in_top - out_bot) / 2.0
            elif in_bot < out_top:
                mid_y = in_bot + (out_top - in_bot) / 2.0
            else:
                mid_y = None

            if mid_y:
                return [(out_x, out_y),
                        (out_x + 2 * pad, out_y),
                        (out_x + 2 * pad, mid_y),
                        (in_x - 2 * pad, mid_y),
                        (in_x - 2 * pad, in_y),
                        (in_x, in_y)]

        # left -> right with center squash
        if (out_loc & loc_left) and (in_loc & loc_right):
            if out_bot < in_top:
                mid_y = in_top + (in_top - out_bot) / 2.0
            elif in_bot < out_top:
                mid_y = out_top - (out_top - in_bot) / 2.0
            else:
                mid_y = None

            if mid_y:
                return [(out_x, out_y),
                        (out_x - 2 * pad, out_y),
                        (out_x - 2 * pad, mid_y),
                        (in_x + 2 * pad, mid_y),
                        (in_x + 2 * pad, in_y),
                        (in_x, in_y)]

        # bottom -> top with center squash
        if (out_loc & loc_bot) and (in_loc & loc_top):
            if out_right < in_left:
                mid_x = out_right + (in_left - out_right) / 2.0
            elif in_right < out_left:
                mid_x = in_right + (out_left - in_right) / 2.0
            else:
                mid_x = None

            if mid_x:
                return [(out_x, out_y),
                        (out_x, out_y + 2 * pad),
                        (mid_x, out_y + 2 * pad),
                        (mid_x, in_y - 2 * pad),
                        (in_x, in_y - 2 * pad),
                        (in_x, in_y)]

        # top -> bottom with center squash
        if (out_loc & loc_top) and (in_loc & loc_bot):
            if out_right < in_left:
                mid_x = in_left + (in_left - out_right) / 2.0
            elif in_right < out_left:
                mid_x = out_left - (out_left - in_right) / 2.0
            else:
                mid_x = None

            if mid_x:
                return [(out_x, out_y),
                        (out_x, out_y - 2 * pad),
                        (mid_x, out_y - 2 * pad),
                        (mid_x, in_y + 2 * pad),
                        (in_x, in_y + 2 * pad),
                        (in_x, in_y)]

        # right -> left with looping
        if (out_loc & loc_right) and (in_loc & loc_left):
            max_y = max(out_bot + 2 * pad, in_bot + 2 * pad)
            return [(out_x, out_y),
                    (out_x + 2 * pad, out_y),
                    (out_x + 2 * pad, max_y),
                    (in_x - 2 * pad, max_y),
                    (in_x - 2 * pad, in_y),
                    (in_x, in_y)]

        # left -> right with looping
        if (out_loc & loc_left) and (in_loc & loc_right):
            max_y = max(out_bot + 2 * pad, in_bot + 2 * pad)
            return [(out_x, out_y),
                    (out_x - 2 * pad, out_y),
                    (out_x - 2 * pad, max_y),
                    (in_x + 2 * pad, max_y),
                    (in_x + 2 * pad, in_y),
                    (in_x, in_y)]

        # bottom -> top with looping
        if (out_loc & loc_bot) and (in_loc & loc_top):
            max_x = max(out_right + 2 * pad, in_right + 2 * pad)
            return [(out_x, out_y),
                    (out_x, out_y + 2 * pad),
                    (max_x, out_y + 2 * pad),
                    (max_x, in_y - 2 * pad),
                    (in_x, in_y - 2 * pad),
                    (in_x, in_y)]

        # top -> bottom with looping
        if (out_loc & loc_top) and (in_loc & loc_bot):
            max_x = max(out_right + 2 * pad, in_right + 2 * pad)
            return [(out_x, out_y),
                    (out_x, out_y - 2 * pad),
                    (max_x, out_y - 2 * pad),
                    (max_x, in_y + 2 * pad),
                    (in_x, in_y + 2 * pad),
                    (in_x, in_y)]

        # right -> right with looping
        if (out_loc & loc_right) and (in_loc & loc_right):
            max_y = max(out_bot + 2 * pad, in_bot + 2 * pad)
            mid_x = out_left - abs(out_left - in_right) / 2.0
            return [(out_x, out_y),
                    (out_x + 2 * pad, out_y),
                    (out_x + 2 * pad, max_y),
                    (mid_x, max_y),
                    (mid_x, in_y),
                    (in_x, in_y)]

        # left -> left with looping
        if (out_loc & loc_left) and (in_loc & loc_left):
            max_y = max(out_bot + 2 * pad, in_bot + 2 * pad)
            mid_x = in_left - abs(in_left - out_right) / 2.0
            return [(out_x, out_y),
                    (out_x - 2 * pad, out_y),
                    (out_x - 2 * pad, max_y),
                    (mid_x, max_y),
                    (mid_x, in_y),
                    (in_x, in_y)]

        # unknown, return a direct route
        return [(out_x, out_y), (in_x, in_y)]

    def customData(self, key, default=None):
        """
        Returns custom defined data that can be tracked per connection.
        
        :param      key         <str>
        :param      default     <variant>
        
        :return     <variant>
        """
        return self._customData.get(nativestring(key), default)

    def direction(self):
        """
        Returns the output-to-input direction as a tuple of the output \
        and input locations.
        
        :return     (<XConnectionLocation> output, <XConnectionLocation> input)
        """
        return self.outputLocation(), self.inputLocation()

    def disabledPen(self):
        """
        Returns the pen that should be used when rendering a disabled \
        connection.
        
        :return     <QPen>
        """
        return self._disabledPen

    def disableWithLayer(self):
        """
        Returns whether or not this connection's enabled state should be \
        affected by its layer.
        
        :return     <bool>
        """
        return self._disableWithLayer

    def disconnectSignals(self, node):
        """
        Disconnects from signals of the inputed node, if the node is a \
        valid XNode type.
        
        :param      node    <XNode> || None
        
        :return     <bool> success
        """
        from projexui.widgets.xnodewidget.xnode import XNode

        # make sure we're disconnecting from a valid node
        if not isinstance(node, XNode):
            return False

        node.dispatch.geometryChanged.disconnect(self.setDirty)
        node.dispatch.removed.disconnect(self.forceRemove)
        return True

    def forceRemove(self):
        """
        Removes the object from the scene by queuing it up for removal.
        """
        scene = self.scene()
        if scene:
            scene.forceRemove(self)

    def font(self):
        """
        Returns the font for this connection.
        
        :return     <QFont>
        """
        return self._font

    def hasCustomData(self, key):
        """
        Returns whether or not there is the given key in the custom data.
        
        :param      key | <str>
        
        :return     <bool>
        """
        return nativestring(key) in self._customData

    def highlightPen(self):
        """
        Return the highlight pen for this connection.
        
        :return     <QPen>
        """
        return self._highlightPen

    def inputArrowStyle(self):
        """
        Returns the arrow style for this connection.

        :return     <XNodeConnection.ArrowStyle>
        """
        return self._inputArrowStyle

    def inputHotspot(self):
        """
        Returns the input hotspot associated with this connection.
        
        :return     <XNodeHotspot> || None
        """
        return self._inputHotspot

    def inputLocation(self):
        """
        Returns the input location for this connection.
        
        :return     <XConnectionLocation>
        """
        return self._inputLocation

    def inputNode(self):
        """
        Returns the input node that is connected to this connection.
        
        :return     <XNode>
        """
        return self._inputNode

    def inputRect(self):
        """
        Returns the bounding rectangle for the input node associated with this
        connection.  If only a point is provided, then a 0 width rect will be
        used.
        
        :return     <QRectF>
        """
        try:
            return self._inputNode.sceneRect()
        except AttributeError:
            point = self.inputPoint()
            return QRectF(point.x(), point.y(), 0, 0)

    def inputFixedX(self):
        """
        Returns the fixed X value for the input option
        
        :return     <float> || None
        """
        return self._inputFixedX

    def inputFixedY(self):
        """
        Returns the fixed Y value for the input option.
        
        :return     <float> || None
        """
        return self._inputFixedY

    def inputPoint(self):
        """
        Returns a scene space point that the connection \
        will draw to as its input target.  If the connection \
        has a node defined, then it will calculate the input \
        point based on the position of the node, factoring in \
        preference for input location and fixed information. \
        If there is no node connected, then the point defined \
        using the setInputPoint method will be used.
        
        :return     <QPointF>
        """
        node = self.inputNode()

        # return the set point
        if not node:
            return self._inputPoint

        # test for the hotspot
        hotspot = self.inputHotspot()

        # otherwise, calculate the point based on location and fixed info
        ilocation = self.inputLocation()
        ifixedx = self.inputFixedX()
        ifixedy = self.inputFixedY()

        loc_left = XNodeConnection.Location.Left
        loc_right = XNodeConnection.Location.Right
        loc_top = XNodeConnection.Location.Top
        loc_bot = XNodeConnection.Location.Bottom

        irect = self.inputRect()
        orect = self.outputRect()

        # return the left location
        if ilocation & loc_left and orect.right() < irect.left():
            if hotspot:
                return node.mapToScene(QPointF(hotspot.rect().left(),
                                               hotspot.rect().center().y()))
            else:
                return node.positionAt(loc_left, ifixedx, ifixedy)

        # return the right location
        elif ilocation & loc_right and irect.left() < orect.right():
            if hotspot:
                return node.mapToScene(QPointF(hotspot.rect().right(),
                                               hotspot.rect().center().y()))
            else:
                return node.positionAt(loc_right, ifixedx, ifixedy)

        # return the top location
        elif ilocation & loc_top and orect.bottom() < irect.top():
            if hotspot:
                return node.mapToScene(QPointF(hotspot.rect().center().x(),
                                               hotspot.rect().top()))
            else:
                return node.positionAt(loc_top, ifixedx, ifixedy)

        # return the bottom location
        elif ilocation & loc_bot and irect.bottom() < orect.top():
            if hotspot:
                return node.mapToScene(QPointF(hotspot.rect().center().x(),
                                               hotspot.rect().bottom()))
            else:
                return node.positionAt(loc_bot, ifixedx, ifixedy)

        # return the center location
        else:
            if hotspot:
                return node.mapToScene(hotspot.rect().center())
            else:
                return node.positionAt(ilocation, ifixedx, ifixedy)

    def isDirection(self, outputLocation, inputLocation):
        """
        Checks to see if the output and input locations match the settings \
        for this item.
        
        :param      outputLocation      | <XConnectionLocation>
        :param      inputLocation       | <XConnectionLocation>
        
        :return     <bool>
        """
        return (self.isOutputLocation(outputLocation) and
                self.isInputLocation(inputLocation))

    def isDirty(self):
        """
        Returns whether or not this path object is dirty and needs to \
        be rebuilt.
        
        :return     <bool>
        """
        return self._dirty

    def isEnabled(self):
        """
        Returns whether or not this connection is enabled.
        
        :sa     disableWithLayer
        
        :return     <bool>
        """
        if self._disableWithLayer and self._layer:
            lenabled = self._layer.isEnabled()
        elif self._inputNode and self._outputNode:
            lenabled = self._inputNode.isEnabled() and self._outputNode.isEnabled()
        else:
            lenabled = True

        return self._enabled and lenabled

    def isInputLocation(self, location):
        """
        Returns whether or not the inputed location value matches the \
        given input location.
        
        :param      location    | <XConnectionLocation>
        
        :return     <bool>
        """
        return (self.inputLocation() & location) != 0

    def isOutputLocation(self, location):
        """
        Returns whether or not the inputed location value matches the \
        given output location.
        
        :param      location    | <XConnectionLocation>
        
        :return     <bool>
        """
        return (self.outputLocation() & location) != 0

    def isStyle(self, style):
        """
        Return whether or not the connection is set to a particular style.
        
        :param      style       | <XConnectionStyle>
        
        :return     <bool>
        """
        return (self._style & style) != 0

    def isVisible(self):
        """
        Returns whether or not this connection is visible.  If either node it is
        connected to is hidden, then it should be as well.
        
        :return     <bool>
        """
        in_node = self.inputNode()
        out_node = self.outputNode()

        if in_node and not in_node.isVisible():
            return False

        if out_node and not out_node.isVisible():
            return False

        return self._visible

    def layer(self):
        """
        Returns the layer that this node is assigned to.
        
        :return     <XNodeLayer> || None
        """
        return self._layer

    def mappedPolygon(self, polygon, path=None, percent=0.5):
        """
        Maps the inputed polygon to the inputed path \
        used when drawing items along the path.  If no \
        specific path is supplied, then this object's own \
        path will be used.  It will rotate and move the \
        polygon according to the inputed percentage.
        
        :param      polygon     <QPolygonF>
        :param      path        <QPainterPath>
        :param      percent     <float>
        
        :return     <QPolygonF> mapped_poly
        """
        translatePerc = percent
        anglePerc = percent

        # we don't want to allow the angle percentage greater than 0.85
        # or less than 0.05 or we won't get a good rotation angle
        if 0.95 <= anglePerc:
            anglePerc = 0.98
        elif anglePerc <= 0.05:
            anglePerc = 0.05

        if not path:
            path = self.path()
        if not (path and path.length()):
            return QPolygonF()

        # transform the polygon to the path
        point = path.pointAtPercent(translatePerc)
        angle = path.angleAtPercent(anglePerc)

        # rotate about the 0 axis
        transform = QTransform().rotate(-angle)
        polygon = transform.map(polygon)

        # move to the translation point
        transform = QTransform().translate(point.x(), point.y())

        # create the rotated polygon
        mapped_poly = transform.map(polygon)
        self._polygons.append(mapped_poly)

        return mapped_poly

    def mousePressEvent(self, event):
        """
        Overloads the mouse press event to handle special cases and \
        bypass when the scene is in view mode.
        
        :param      event   <QMousePressEvent>
        """
        # ignore events when the scene is in view mode
        scene = self.scene()
        if scene and scene.inViewMode():
            event.ignore()
            return

        # block the selection signals
        if scene:
            scene.blockSelectionSignals(True)

            # clear the selection
            if ( not (self.isSelected() or
                              event.modifiers() == Qt.ControlModifier) ):
                for item in scene.selectedItems():
                    if item != self:
                        item.setSelected(False)

        # try to start the connection
        super(XNodeConnection, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """
        Overloads the mouse move event to ignore the event when \
        the scene is in view mode.
        
        :param      event   <QMouseMoveEvent>
        """
        # ignore events when the scene is in view mode
        scene = self.scene()
        if scene and (scene.inViewMode() or scene.isConnecting()):
            event.ignore()
            return

        # call the base method
        super(XNodeConnection, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        Overloads the mouse release event to ignore the event when the \
        scene is in view mode, and release the selection block signal.
         
         :param     event   <QMouseReleaseEvent>
        """
        # ignore events when the scene is in view mode
        scene = self.scene()
        if scene and (scene.inViewMode() or scene.isConnecting()):
            event.ignore()
            return

        # emit the scene's connection menu requested signal if
        # the button was a right mouse button
        if event.button() == Qt.RightButton and scene:
            scene.emitConnectionMenuRequested(self)
            event.accept()
        else:
            super(XNodeConnection, self).mouseReleaseEvent(event)

        # unblock the selection signals
        if scene:
            scene.blockSelectionSignals(False)

    def opacity(self):
        """
        Returns the opacity amount for this connection.
        
        :return     <float>
        """
        in_node = self.inputNode()
        out_node = self.outputNode()

        if ( in_node and out_node and \
                     (in_node.isIsolateHidden() or out_node.isIsolateHidden()) ):
            return 0.1

        opacity = super(XNodeConnection, self).opacity()
        layer = self.layer()
        if layer:
            return layer.opacity() * opacity

        return opacity

    def outputArrowStyle(self):
        """
        Returns the arrow style for this connection.

        :return     <XNodeConnection.ArrowStyle>
        """
        return self._outputArrowStyle

    def outputHotspot(self):
        """
        Returns the output hotspot associated with this connection.
        
        :return     <XNodeHotspot> || None
        """
        return self._outputHotspot

    def outputLocation(self):
        """
        Returns the location for the output source position.
        
        :return     <XConnectionLocation>
        """
        return self._outputLocation

    def outputNode(self):
        """
        Returns the output source node that this connection is currently \
        connected to.
        
        :return     <XNode> || None
        """
        return self._outputNode

    def outputFixedX(self):
        """
        Returns the fixed X position for the output component of this \
        connection.
                    
        :return     <float> || None
        """
        return self._outputFixedX

    def outputFixedY(self):
        """
        Returns the fixed Y position for the output component of this \
        connection.
                    
        :return     <float> || None
        """
        return self._outputFixedY

    def outputPoint(self):
        """
        Returns a scene space point that the connection \
        will draw to as its output source.  If the connection \
        has a node defined, then it will calculate the output \
        point based on the position of the node, factoring in \
        preference for output location and fixed positions.  If \ 
        there is no node connected, then the point defined using \
        the setOutputPoint method will be used.
        
        :return     <QPointF>
        """
        node = self.outputNode()

        # return the set point
        if not node:
            return self._outputPoint

        # test for the hotspot
        hotspot = self.outputHotspot()

        # otherwise, calculate the point based on location and fixed positions
        olocation = self.outputLocation()
        ofixedx = self.outputFixedX()
        ofixedy = self.outputFixedY()

        loc_left = XNodeConnection.Location.Left
        loc_right = XNodeConnection.Location.Right
        loc_top = XNodeConnection.Location.Top
        loc_bot = XNodeConnection.Location.Bottom

        irect = self.inputRect()
        orect = self.outputRect()

        # return the right location
        if olocation & loc_right and orect.right() < irect.left():
            if hotspot:
                return node.mapToScene(QPointF(hotspot.rect().right(),
                                               hotspot.rect().center().y()))
            else:
                return node.positionAt(loc_right, ofixedx, ofixedy)

        # return the left location
        elif olocation & loc_left and irect.right() < orect.left():
            if hotspot:
                return node.mapToScene(QPointF(hotspot.rect().left(),
                                               hotspot.rect().center().y()))
            else:
                return node.positionAt(loc_left, ofixedx, ofixedy)

        # return the bottom location
        elif olocation & loc_bot and orect.bottom() < irect.top():
            if hotspot:
                return node.mapToScene(QPointF(hotspot.rect().center().x(),
                                               hotspot.rect().bottom()))
            else:
                return node.positionAt(loc_bot, ofixedx, ofixedy)

        # return the top location
        elif olocation & loc_top and irect.bottom() < orect.top():
            if hotspot:
                return node.mapToScene(QPointF(hotspot.rect().center().x(),
                                               hotspot.rect().top()))
            else:
                return node.positionAt(loc_top, ofixedx, ofixedy)

        # return the center point
        else:
            if hotspot:
                return node.mapToScene(hotspot.rect().center())
            else:
                return node.positionAt(olocation, ofixedx, ofixedy)

    def outputRect(self):
        """
        Returns the bounding rectangle for the output node associated with this
        connection.  If only a point is provided, then a 0 width rect will be
        used.
        
        :return     <QRectF>
        """
        try:
            return self._outputNode.sceneRect()
        except AttributeError:
            point = self.outputPoint()
            return QRectF(point.x(), point.y(), 0, 0)

    def padding(self):
        """
        Returns the amount of padding to be used when drawing a connection \
        that will be drawn backwards.
        
        :return     <float>
        """
        return self._padding

    def paint(self, painter, option, widget):
        """
        Overloads the paint method from QGraphicsPathItem to \
        handle custom drawing of the path using this items \
        pens and polygons.
        
        :param      painter     <QPainter>
        :param      option      <QGraphicsItemStyleOption>
        :param      widget      <QWidget>
        """
        # following the arguments required by Qt
        # pylint: disable-msg=W0613

        painter.setOpacity(self.opacity())

        # show the connection selected
        if not self.isEnabled():
            pen = QPen(self.disabledPen())
        elif self.isSelected():
            pen = QPen(self.highlightPen())
        else:
            pen = QPen(self.pen())

        if self._textItem:
            self._textItem.setOpacity(self.opacity())
            self._textItem.setDefaultTextColor(pen.color().darker(110))

        # rebuild first if necessary
        if self.isDirty():
            self.setPath(self.rebuild())

        # store the initial hint
        hint = painter.renderHints()
        painter.setRenderHint(painter.Antialiasing)

        pen.setWidthF(1.25)
        painter.setPen(pen)
        painter.drawPath(self.path())

        # redraw the polys to force-fill them
        for poly in self._polygons:
            if not poly.isClosed():
                continue

            painter.setBrush(pen.color())
            painter.drawPolygon(poly)

        # restore the render hints
        painter.setRenderHints(hint)

    def prepareToRemove(self):
        """
        Handles any code that needs to run to cleanup the connection \
        before it gets removed from the scene.
        
        :return     <bool> success
        """
        # disconnect the signals from the input and output nodes
        for node in (self._outputNode, self._inputNode):
            self.disconnectSignals(node)

        # clear the pointers to the nodes
        self._inputNode = None
        self._outputNode = None

        return True

    def rebuild(self):
        """
        Rebuilds the path for this connection based on the given connection \
        style parameters that have been set.
        
        :return     <QPainterPath>
        """
        # create the path
        path = self.rebuildPath()
        self._polygons = self.rebuildPolygons(path)

        if self._textItem:
            point = path.pointAtPercent(0.5)
            metrics = QFontMetrics(self._textItem.font())

            point.setY(point.y() - metrics.height() / 2.0)

            self._textItem.setPos(point)

        # create the path for the item
        for poly in self._polygons:
            path.addPolygon(poly)

        # unmark as dirty
        self.setDirty(False)

        return path

    def rebuildPath(self):
        """
        Rebuilds the path for the given style options based on the currently \
        set parameters.
        
        :return     <QPainterPath>
        """
        # rebuild linear style
        if self.isStyle(XConnectionStyle.Linear):
            return self.rebuildLinear()

        # rebuild block style
        elif self.isStyle(XConnectionStyle.Block):
            return self.rebuildBlock()

        # rebuild smooth style
        elif self.isStyle(XConnectionStyle.Smooth):
            return self.rebuildSmooth()

        # otherwise, we have an invalid style, or a style
        # defined by a subclass
        else:
            return QPainterPath()

    def rebuildPolygons(self, path):
        """
        Rebuilds the polygons that will be used on this path.
        
        :param      path    | <QPainterPath>
        
        :return     <list> [ <QPolygonF>, .. ]
        """
        output = []

        # create the input arrow
        if self.showInputArrow():
            if self.inputArrowStyle() & self.ArrowStyle.Inverted:
                a = QPointF(0, -4)
                b = QPointF(-10, 0)
                c = QPointF(0, 4)
            else:
                a = QPointF(-10, -4)
                b = QPointF(0, 0)
                c = QPointF(-10, 4)

            if self.inputArrowStyle() & self.ArrowStyle.Filled:
                poly = QPolygonF([a, b, c, a])
            else:
                poly = QPolygonF([a, b, c])

            mpoly = self.mappedPolygon(poly, path, 1.0)
            output.append(mpoly)

        # create the direction arrow
        if self.showDirectionArrow():
            a = QPointF(-5, -4)
            b = QPointF(5, 0)
            c = QPointF(-5, 4)

            mpoly = self.mappedPolygon(QPolygonF([a, b, c, a]), path, 0.5)
            output.append(mpoly)

        # create the output arrow
        if self.showOutputArrow():
            if self.outputArrowStyle() & self.ArrowStyle.Inverted:
                a = QPointF(0, -4)
                b = QPointF(10, 0)
                c = QPointF(0, 4)
            else:
                a = QPointF(10, -4)
                b = QPointF(0, 0)
                c = QPointF(10, 4)

            if self.outputArrowStyle() & self.ArrowStyle.Filled:
                poly = QPolygonF([a, b, c, a])
            else:
                poly = QPolygonF([a, b, c])

            mpoly = self.mappedPolygon(poly, path, 0)
            output.append(mpoly)

        return output

    def rebuildLinear(self):
        """ 
        Rebuilds a linear path from the output to input points.
        
        :return     <QPainterPath>
        """

        points = self.controlPoints()

        # create a simple line between the output and input points
        path = QPainterPath()
        path.moveTo(*points[0])
        path.lineTo(*points[-1])

        return path

    def rebuildBlock(self):
        """
        Rebuilds a blocked path from the output to input points.
        
        :return     <QPainterPath>
        """
        # collect the control points
        points = self.controlPoints()

        curve = 12

        path = QPainterPath()
        if len(points) == 2:
            path.moveTo(*points[0])
            path.lineTo(*points[1])
        else:
            for i in range(len(points) - 2):
                a = points[i]
                b = points[i + 1]
                c = points[i + 2]

                delta_ab_x = b[0] - a[0]
                delta_ab_y = b[1] - a[1]

                delta_bc_x = b[0] - c[0]
                delta_bc_y = b[1] - c[1]

                # calculate ctrl_ab
                if delta_ab_y == 0:
                    mult = delta_ab_x / max(abs(delta_ab_x), 1)
                    off_x = min(curve, abs(delta_ab_x * 0.5))
                    ctrl_ab = (b[0] - (off_x * mult), b[1])
                else:
                    mult = delta_ab_y / max(abs(delta_ab_y), 1)
                    off_y = min(curve, abs(delta_ab_y * 0.5))
                    ctrl_ab = (b[0], b[1] - (off_y * mult))

                # calculate ctrl_bc
                if delta_bc_y == 0:
                    mult = delta_bc_x / max(abs(delta_bc_x), 1)
                    off_x = min(curve, abs(delta_bc_x * 0.5))
                    ctrl_bc = (b[0] - (off_x * mult), b[1])
                else:
                    mult = delta_bc_y / max(abs(delta_bc_y), 1)
                    off_y = min(curve, abs(delta_bc_y * 0.5))
                    ctrl_bc = (b[0], b[1] - (off_y * mult))

                if not i:
                    path.moveTo(*a)

                path.lineTo(*ctrl_ab)
                path.quadTo(*(list(b) + list(ctrl_bc)))

            path.lineTo(*points[-1])

        return path

    def rebuildSmooth(self):
        """
        Rebuilds a smooth path based on the inputed points and set \
        parameters for this item.
        
        :return     <QPainterPath>
        """
        # collect the control points
        points = self.controlPoints()

        # create the path
        path = QPainterPath()

        if len(points) == 3:
            x0, y0 = points[0]
            x1, y1 = points[1]
            xN, yN = points[2]

            path.moveTo(x0, y0)
            path.quadTo(x1, y1, xN, yN)

        elif len(points) == 4:
            x0, y0 = points[0]
            x1, y1 = points[1]
            x2, y2 = points[2]
            xN, yN = points[3]

            path.moveTo(x0, y0)
            path.cubicTo(x1, y1, x2, y2, xN, yN)

        elif len(points) == 6:
            x0, y0 = points[0]
            x1, y1 = points[1]
            x2, y2 = points[2]
            x3, y3 = points[3]
            x4, y4 = points[4]
            xN, yN = points[5]

            xC = (x2 + x3) / 2.0
            yC = (y2 + y3) / 2.0

            path.moveTo(x0, y0)
            path.cubicTo(x1, y1, x2, y2, xC, yC)
            path.cubicTo(x3, y3, x4, y4, xN, yN)

        else:
            x0, y0 = points[0]
            xN, yN = points[-1]

            path.moveTo(x0, y0)
            path.lineTo(xN, yN)

        return path

    def refreshVisible(self):
        """
        Refreshes whether or not this node should be visible based on its
        current visible state.
        """
        super(XNodeConnection, self).setVisible(self.isVisible())

    def setAutoCalculateInputLocation(self, state=True):
        """
        Sets whether or not to auto calculate the input location based on \
        the proximity to the output node or point.
        
        :param     state       | <bool>
        """
        self._autoCalculateInputLocation = state
        self.setDirty()

    def setAutoCalculateOutputLocation(self, state=True):
        """
        Sets whether or not to auto calculate the input location based on \
        the proximity to the output node or point.
        
        :param     state       | <bool>
        """
        self._autoCalculateOutputLocation = state
        self.setDirty()

    def setCustomData(self, key, value):
        """
        Stores the inputed value as custom data on this connection for \
        the given key.
        
        :param      key     | <str>
        :param      value   | <variant>
        """
        self._customData[nativestring(key)] = value

    def setDirection(self, outputLocation, inputLocation):
        """
        Sets the output-to-input direction by setting both the locations \
        at the same time.
        
        :param      outputLocation      | <XConnectionLocation>
        :param      inputLocation       | <XConnectionLocation>
        """
        self.setOutputLocation(outputLocation)
        self.setInputLocation(inputLocation)

    def setDirty(self, state=True):
        """
        Flags the connection as being dirty and needing a rebuild.
        
        :param      state   | <bool>
        """
        self._dirty = state

        # set if this connection should be visible
        if self._inputNode and self._outputNode:
            vis = self._inputNode.isVisible() and self._outputNode.isVisible()
            self.setVisible(vis)

    def setDisabledPen(self, pen):
        """
        Sets the disabled pen that will be used when rendering a connection \
        in a disabled state.
        
        :param      pen | <QPen>
        """
        self._disabledPen = QPen(pen)

    def setDisableWithLayer(self, state):
        """
        Sets whether or not this connection's layer's current state should \
        affect its enabled state.
        
        :param      state | <bool>
        """
        self._disableWithLayer = state
        self.setDirty()

    def setEnabled(self, state):
        """
        Sets whether or not this connection is enabled or not.
        
        :param      state | <bool>
        """
        self._enabled = state

    def setFont(self, font):
        """
        Sets the font for this connection to the inputed font.
        
        :param      font | <QFont>
        """
        self._font = font

    def setHighlightPen(self, pen):
        """
        Sets the pen to be used when highlighting a selected connection.
        
        :param      pen     | <QPen> || <QColor>
        """
        self._highlightPen = QPen(pen)

    def setInputLocation(self, location):
        """
        Sets the input location for where this connection should point to.
        
        :param      location       | <XConnectionLocation>
        """
        self._inputLocation = location
        self.setDirty()

    def setInputArrowStyle(self, style):
        """
        Sets the input arrow style for this connection to the inputed style.

        :param      style | <XNodeConnection.ArrowStyle>
        """
        self._inputArrowStyle = style

    def setInputNode(self, node):
        """
        Sets the node that will be recieving this connection as an input.
        
        :param      node    | <XNode>
        """
        # if the node already matches the current input node, ignore
        if self._inputNode == node:
            return

        # disconnect from the existing node
        self.disconnectSignals(self._inputNode)

        # store the node
        self._inputNode = node

        # connect to the new node
        self.connectSignals(self._inputNode)

        # force the rebuilding of the path
        self.setPath(self.rebuild())

    def setInputFixedX(self, x):
        """
        Sets the fixed x position for the input component of this connection.
        
        :param      x       | <float> || None
        """
        self._inputFixedX = x
        self.setDirty()

    def setInputFixedY(self, y):
        """
        Sets the fixed y position for the input component of this connection.
        
        :param      y       | <float> || None
        """
        self._inputFixedY = y
        self.setDirty()

    def setInputHotspot(self, hotspot):
        """
        Sets the hotspot associated with this connection's input.
        
        :param      hotspot | <XNodeHotspot> || None
        """
        self._inputHotspot = hotspot
        self.setDirty()

    def setInputPoint(self, point):
        """
        Sets the scene level input point position to draw the connection to. \
        This is used mainly by the scene when drawing a user connection - \
        it will only be used when there is no connected input node.
        
        :param      point       | <QPointF>
        """
        self._inputPoint = point
        self.setPath(self.rebuild())

    def setLayer(self, layer):
        """
        Sets the layer that this node is associated with to the given layer.
        
        :param      layer       | <XNodeLayer> || None
        
        :return     <bool> changed
        """
        if layer == self._layer:
            return False

        self._layer = layer
        self.syncLayerData()

        return True

    def setOutputArrowStyle(self, style):
        """
        Sets the input arrow style for this connection to the outputed style.

        :param      style | <XNodeConnection.ArrowStyle>
        """
        self._outputArrowStyle = style

    def setOutputLocation(self, location):
        """
        Sets the location for the output part of the connection to generate \
        from.
        
        :param      location      | <XConnectionLocation>
        """
        self._outputLocation = location
        self.setDirty()

    def setOutputNode(self, node):
        """
        Sets the node that will be generating the output information for \
        this connection.
        
        :param      node         | <XNode>
        """
        # if the output node matches the current, ignore
        if node == self._outputNode:
            return

        # disconnect from an existing node
        self.disconnectSignals(self._outputNode)

        # set the current node
        self._outputNode = node
        self.connectSignals(self._outputNode)

        # force the rebuilding of the path
        self.setPath(self.rebuild())

    def setOutputFixedX(self, x):
        """
        Sets the fixed x position for the output component of this connection.
        
        :param      x       | <float> || None
        """
        self._outputFixedX = x
        self.setDirty()

    def setOutputFixedY(self, y):
        """
        Sets the fixed y position for the output component of this connection.
        
        :param      y       | <float> || None
        """
        self._outputFixedY = y
        self.setDirty()

    def setOutputHotspot(self, hotspot):
        """
        Sets the hotspot associated with this connection's output.
        
        :param      hotspot | <XNodeHotspot> || None
        """
        self._outputHotspot = hotspot
        self.setDirty()

    def setOutputPoint(self, point):
        """
        Sets the scene space point for where this connection should draw \
        its output from.  This value will only be used if no output \
        node is defined.
        
        :param      point      | <QPointF>
        """
        self._outputPoint = point
        self.setPath(self.rebuild())

    def setPadding(self, padding):
        """
        Sets the padding amount that will be used when drawing a connection \
        whose points will overlap.
        
        :param      padding    | <float>
        """
        self._padding = padding
        self.setDirty()

    def setShowDirectionArrow(self, state=True):
        """
        Marks whether or not an arrow in the center of the path should be \
        drawn, showing the direction that the connection is flowing in.
        
        :param      state      | <bool>
        """
        self._showDirectionArrow = state
        self.setDirty()

    def setShowInputArrow(self, state=True):
        """
        :remarks    Marks whether or not an arrow should be shown pointing
                    at the input node.
        
        :param      state       <bool>
        """
        self._showInputArrow = state
        self.setDirty()

    def setShowOutputArrow(self, state=True):
        """
        :remarks    Marks whether or not an arrow should be shown pointing at
                    the output node.
        
        :param      state       <bool>
        """
        self._showOutputArrow = state
        self.setDirty()

    def setSquashThreshold(self, amount):
        """
        :remarks    Sets the threshold limit of when the connection should
                    start 'squashing', calculated based on the distance between
                    the input and output points when rebuilding.
        
        :param      amount      <float>
        """
        self._squashThreshold = amount
        self.setDirty()

    def setStyle(self, style):
        """
        :remarks    Sets the style of the connection that will be used.
        
        :param      style       <XConnectionStyle>
        """
        self._style = style
        self.setDirty()
        self.update()

    def setVisible(self, state):
        """
        Sets whether or not this connection's local visibility should be on.
        
        :param      state | ,bool>
        """
        self._visible = state

        super(XNodeConnection, self).setVisible(self.isVisible())

    def setZValue(self, value):
        """
        Sets the z value for this connection, also updating the text item to 
        match the value if one is defined.
        
        :param      value | <int>
        """
        super(XNodeConnection, self).setZValue(value)

        if self._textItem:
            self._textItem.setZValue(value)

    def showDirectionArrow(self):
        """
        :remarks    Return whether or not the direction arrow is visible
                    for this connection.
        
        :return     <bool>
        """
        return self._showDirectionArrow

    def showInputArrow(self):
        """
        :remarks    Return whether or not the input arrow is visible
                    for this connection.
        
        :return     <bool>
        """
        return self._showInputArrow

    def showOutputArrow(self):
        """
        :remarks    Return whether or not the output arrow is visible
                    for this connection.
        
        :return     <bool>
        """
        return self._showOutputArrow

    def squashThreshold(self):
        """
        :remarks    Returns the sqash threshold for when the line
                    should be squashed based on the input and output
                    points becoming too close together.
        
        :return     <float>
        """
        return self._squashThreshold

    def setText(self, text):
        """
        Sets the text for this connection to the inputed text.
        
        :param      text | <str>
        """
        self._text = text

        if text:
            if self._textItem is None:
                self._textItem = QGraphicsTextItem()
                self._textItem.setParentItem(self)

            self._textItem.setPlainText(text)

        elif self._textItem:
            self.scene().removeItem(self._textItem)
            self._textItem = None

    def style(self):
        """
        :remarks    Returns the style of the connection that is being drawn.
        
        :return     style       <XConnectionStyle>
        """
        return self._style

    def syncLayerData(self, layerData=None):
        """
        Syncs the layer information for this item from the given layer data.
        
        :param      layerData | <dict>
        """
        if not self._layer:
            return

        if not layerData:
            layerData = self._layer.layerData()

        self.setVisible(layerData.get('visible', True))

        if layerData.get('current'):
            # set the default parameters
            self.setFlags(self.ItemIsSelectable)
            self.setAcceptHoverEvents(True)
            self.setZValue(99)

        else:
            # set the default parameters
            self.setFlags(self.GraphicsItemFlags(0))
            self.setAcceptHoverEvents(True)
            self.setZValue(layerData.get('zValue', 0) - 1)

    def text(self):
        """
        Returns the text for this connection.
        
        :return     <str>
        """
        return self._text