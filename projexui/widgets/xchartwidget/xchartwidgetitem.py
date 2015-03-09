""" Defines the generic chart widget item class for adding items to charts. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2012, Projex Software'
__license__         = 'LGPL'

# maintenance information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

import random

from projex.text import nativestring

from projexui.qt.QtCore import QPointF,\
                               QRectF,\
                               Qt

from projexui.qt.QtGui import QGraphicsPathItem,\
                              QColor,\
                              QPainterPath,\
                              QPen,\
                              QLinearGradient,\
                              QRadialGradient,\
                              QCursor,\
                              QApplication,\
                              QToolTip,\
                              QDrag

from projexui.widgets.xchartwidget.xchartscene import XChartScene
from projexui.widgets.xpopupwidget             import XPopupWidget

class XChartWidgetItem(QGraphicsPathItem):
    def __init__( self ):
        super(XChartWidgetItem, self).__init__()
        
        self.setAcceptHoverEvents(True)
        
        # set default information
        self._chartType         = None
        self._pieCenter         = QPointF(0, 0)
        self._subpaths          = []
        self._keyColors         = {}
        self._ellipses          = []
        self._keyToolTips       = {}
        self._showPointsInLine  = True
        self._shaded            = True
        self._dragData          = {}
        self._radius            = 6
        
        self._title             = ''
        self._color             = self.randomColor()
        self._alternateColor    = self._color.lighter(140)
        self._points            = []
        self._barSize           = 30
        self._orientation       = Qt.Horizontal
        self._pieAxis           = Qt.YAxis
        
        self._pointRadius       = 6
        self._horizontalOffset  = 0
        self._verticalOffset    = 0
        
        self._hoveredPath       = None
        self._dirty             = False
        self._buildData         = {}
    
    def addPoint( self, x, y ):
        """
        Adds a new chart point to this item.
        
        :param      x | <variant>
                    y | <variant>
        """
        self._points.append((x, y))
        self._dirty = True
    
    def alternateColor( self ):
        """
        Returns the alternate color for this item.
        
        :return     <QColor>
        """
        return QColor(self._alternateColor)
    
    def barSize( self ):
        """
        Returns the size that the bar chart should be rendered with.
        
        :return     <int>
        """
        return self._barSize
    
    def chartType( self ):
        """
        Returns the chart type for this item.  If no type is explicitely set,
        then the scenes chart type will be utilized.
        
        :return     <XChartScene.Type>
        """
        if ( self._chartType ):
            return self._chartType
        
        scene = self.scene()
        if ( not scene ):
            return 0
        
        return scene.chartType()
    
    def clear( self ):
        """
        Clears the chart points from this item.
        """
        self._points = []
        self._dirty = True
    
    def color( self ):
        """
        Returns the primary color for this item.
        
        :return     <QColor>
        """
        return QColor(self._color)
    
    def dragData(self, x=None, y=None):
        """
        Returns any drag information that will be used from this chart item.
        
        :return     <QMimeData> || None
        """
        # look for specific drag information for this item
        first  = (x, y)
        second = (x, None)
        third  = (None, y)
        fourth = (None, None)
        
        for key in (first, second, third, fourth):
            data = self._dragData.get(key)
            if data:
                return data
        
        return None
    
    def hasCustomType( self ):
        """
        Returns true if this item defines its own chart type.
        
        :return     <bool>
        """
        return self._chartType != None
    
    def horizontalRuler( self ):
        """
        Returns the horizontal ruler for this widget item.
        
        :return     <projexui.widgets.xchartwidget.XChartRuler> || None
        """
        if ( not self.scene() ):
            return None
        return self.scene().horizontalRuler()
    
    def horizontalOffset( self ):
        """
        Returns the horizontal offset for this item.
        
        :return     <int>
        """
        return self._horizontalOffset
    
    def hoverMoveEvent( self, event ):
        """
        Tracks whether or not this item is being hovered.
        
        :param      event | <QEvent>
        """
        point = event.pos()
        
        found_key = ''
        found = None
        for key, value, subpath in self._subpaths:
            if subpath.contains(point):
                found = subpath
                found_key = key
                break
        
        if found:
            # update the tooltip
            tip    = self.keyToolTip(found_key)
            if ( tip ):
                widget = self.scene().chartWidget()
                anchor = XPopupWidget.Anchor.RightCenter
                
                # show the popup widget
                XPopupWidget.showToolTip(tip, 
                                         anchor = anchor,
                                         parent = widget,
                                         foreground = self.color().darker(120),
                                         background = self.alternateColor())
            
            if ( found != self._hoveredPath ):
                self._hoveredPath = found
                self.update()
    
    def hoverLeaveEvent( self, event ):
        """
        Tracks whether or not this item is being hovered.
        
        :param      event | <QEvent>
        """
        super(XChartWidgetItem, self).hoverEnterEvent(event)
        
        self._hoveredPath = None
        self.update()
    
    def isShaded( self ):
        """
        Returns the shaded state for this item.
        
        :return     <bool>
        """
        return self._shaded
    
    def keyColor( self, key ):
        """
        Returns a color for the inputed key (used in pie charts).
        
        :param      key | <str>
        
        :return     <QColor>
        """
        self._keyColors.setdefault(nativestring(key), self.color())
        return self._keyColors[nativestring(key)]
    
    def keyToolTip( self, key ):
        """
        Returns the tool tip for this key.
        
        :param      key | <str>
        
        :return     <str>
        """
        return self._keyToolTips.get(nativestring(key), '')
    
    def mousePressEvent(self, event):
        """
        Creates the drag event for this item.
        
        :param      event | <QMousePressEvent>
        """
        near_x, near_y = self.nearestPoint(event.pos())
        
        data = self.dragData(x=near_x, y=near_y)
        self.startDrag(data)
        
        super(XChartWidgetItem, self).mousePressEvent(event)
    
    def nearestPoint(self, pos):
        """
        Returns the nearest graphing point for this item based on the
        inputed graph position.
        
        :param      pos | <QPoint>
        
        :return     (<variant> x, <variant> y)
        """
        # lookup subpaths
        for x, y, path in self._subpaths:
            if path.contains(pos):
                return (x, y)
        
        return (None, None)
    
    def orientation( self ):
        """
        Returns the orienatation for this item (used in bar charts).
        
        :return     <Qt.Orienation>
        """
        return self._orientation
    
    def paint( self, painter, option, widget ):
        """
        Draws this item with the inputed painter.
        
        :param      painter | <QPainter>
                    rect    | <QRect>
        """
        if self._dirty:
            self.rebuild()
        
        scene   = self.scene()
        if not scene:
            return
        
        grid    = scene.gridRect()
        typ     = self.chartType()
        
        # draw the line chart
        if typ == XChartScene.Type.Line:
            painter.setRenderHint(painter.Antialiasing)
            
            # draw the path area
            area = self._buildData.get('path_area')
            if area and self.isShaded():
                clr   = QColor(self.color())
                
                clr.setAlpha(120)
                painter.setPen(Qt.NoPen)
                painter.setBrush(clr)
                
                painter.drawPath(area)
            
            # draw the line data
            pen = QPen(self.color())
            pen.setWidth(2)
            
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            
            painter.drawPath(self.path())
            
            if ( self.showPointsInLine() ):
                palette = QApplication.palette()
                pen = QPen(palette.color(palette.Base))
                pen.setWidth(2)
                
                painter.setBrush(self.color())
                painter.setPen(pen)
                
                for point in self._ellipses:
                    painter.drawEllipse(point, 
                                        self.pointRadius(), 
                                        self.pointRadius())
        
        # draw a bar chart
        elif typ == XChartScene.Type.Bar:
            painter.setRenderHint(painter.Antialiasing)
            
            pen = QPen(self.color())
            pen.setWidth(1)
            painter.setPen(pen)
            
            for key, value, sub_path in self._subpaths:
                gradient = QLinearGradient()
                
                clr = QColor(self.color())
                
                if ( sub_path != self._hoveredPath ):
                    clr.setAlpha(130)
                
                gradient.setColorAt(0.0,  clr.lighter(140))
                gradient.setColorAt(0.1,  clr.lighter(120))
                gradient.setColorAt(0.25, clr.lighter(110))
                gradient.setColorAt(1.0,  clr.lighter(105))
                
                if ( self.orientation() == Qt.Horizontal ):
                    gradient.setStart(0, sub_path.boundingRect().top())
                    gradient.setFinalStop(0, sub_path.boundingRect().bottom())
                else:
                    gradient.setStart(sub_path.boundingRect().left(), 0)
                    gradient.setFinalStop(sub_path.boundingRect().right(), 0)
                
                painter.setBrush(gradient)
                painter.drawPath(sub_path)
        
        # draw a simple pie chart (calculated by scene)
        elif typ == XChartScene.Type.Pie:
            painter.setRenderHint(painter.Antialiasing)
            
            center   = self.pieCenter()
            radius   = self.radius()
            
            for key, value, sub_path in self._subpaths:
                clr = self.keyColor(key)
                
                gradient = QRadialGradient(QPointF(0, 0), radius)
                
                a = QColor(clr.lighter(140))
                b = QColor(clr.lighter(110))
                
                a.setAlpha(40)
                b.setAlpha(80)
                
                # look for mouse over
                if ( sub_path == self._hoveredPath ):
                    a.setAlpha(100)
                    b.setAlpha(200)
                
                gradient.setColorAt(0, a)
                gradient.setColorAt(1, b)
                
                pen = QPen(clr)
                pen.setWidth(1)
                
                painter.setBrush(gradient)
                painter.setPen(pen)
                
                painter.drawPath(sub_path)
    
    def pieAxis( self ):
        """
        Returns the axis that is used as the pie value for this item.
        
        :return     <Qt.Axis>
        """
        return self._pieAxis
    
    def pieCenter( self ):
        """
        Returns the center point for the pie for this item.
        
        :return     <QPointF>
        """
        return self._pieCenter
    
    def pointRadius(self):
        """
        Returns the radius for individual points on the line.
        
        :return     <int>
        """
        return self._pointRadius
    
    def randomColor( self ):
        """
        Generates a random color.
        
        :return     <QColor>
        """
        r = random.randint(120, 180)
        g = random.randint(120, 180)
        b = random.randint(120, 180)
        
        return QColor(r, g, b)
    
    def radius( self ):
        """
        Returns the radius for this item for the pie chart.
        
        :return     <float>
        """
        return self._radius
    
    def rebuild( self ):
        """
        Rebuilds the item based on the current points.
        """
        scene       = self.scene()
        if not scene:
            return
        
        self._subpaths = []
        
        grid        = scene.gridRect()
        typ         = self.chartType()
        
        hruler      = scene.horizontalRuler()
        vruler      = scene.verticalRuler()
        
        path        = QPainterPath()
        area        = QPainterPath()
        
        self._buildData.clear()
        self._buildData['path_area'] = area
        
        self.setPos(0, 0)
        
        # draw a line item
        if typ == XChartScene.Type.Line:
            first = True
            pos   = None
            home  = None
            self._ellipses = []
            
            points = self.points()
            if ( self.orientation() == Qt.Horizontal ):
                points.sort(hruler.compareValues, key = lambda x: x[0])
            else:
                points.sort(vruler.compareValues, key = lambda y: y[1])
                points.reverse()
            
            for x, y in self.points():
                pos = scene.mapFromChart(x, y)
                if first:
                    home = QPointF(pos.x(), grid.bottom())
                    area.moveTo(home)
                    area.lineTo(pos)
                    path.moveTo(pos)
                    
                    self._ellipses.append(pos)
                    
                    first = False
                else:
                    path.lineTo(pos)
                    area.lineTo(pos)
                    
                    self._ellipses.append(pos)
            
            if pos and home:
                area.lineTo(pos.x(), grid.bottom())
                area.lineTo(home)
        
        # draw a bar item
        elif typ == XChartScene.Type.Bar:
            barsize = self.barSize()
            horiz   = self.orientation() == Qt.Horizontal
            
            for x, y in self.points():
                pos = scene.mapFromChart(x, y)
                subpath = QPainterPath()
                if horiz:
                    r = min(grid.bottom() - pos.y(), 8)
                    
                    subpath.moveTo(pos.x() - barsize / 2.0, grid.bottom())
                    subpath.lineTo(pos.x() - barsize / 2.0, pos.y() + r)
                    subpath.quadTo(pos.x() - barsize / 2.0, pos.y(),
                                   pos.x() - barsize / 2.0 + r, pos.y())
                    
                    subpath.lineTo(pos.x() + barsize / 2.0 - r, pos.y())
                    subpath.quadTo(pos.x() + barsize / 2.0, pos.y(),
                                   pos.x() + barsize / 2.0, pos.y() + r)
                    
                    subpath.lineTo(pos.x() + barsize / 2.0, grid.bottom())
                    subpath.lineTo(pos.x() - barsize / 2.0, grid.bottom())
                else:
                    subpath.moveTo(grid.left(), pos.y() - barsize / 2.0)
                    subpath.lineTo(pos.x(),     pos.y() - barsize / 2.0)
                    subpath.lineTo(pos.x(),     pos.y() + barsize / 2.0)
                    subpath.lineTo(grid.left(), pos.y() + barsize / 2.0)
                    subpath.lineTo(grid.left(), pos.y() - barsize / 2.0)
                
                path.addPath(subpath)
                self._subpaths.append((x, y, subpath))
        
        # draw a pie chart
        elif typ == XChartScene.Type.Pie:
            if self.orientation() == Qt.Horizontal:
                key_index   = 0
                value_index = 1
                value_ruler = self.verticalRuler()
            else:
                key_index   = 1
                value_index = 0
                value_ruler = self.horizontalRuler()
        
            pie_values = {}
            
            for point in self.points():
                key     = point[key_index]
                value   = point[value_index]
                
                pie_values.setdefault(key, [])
                pie_values[key].append(value)
        
            for key, values in pie_values.items():
                pie_values[key] = value_ruler.calcTotal(values)
            
            total = max(1, value_ruler.calcTotal(pie_values.values()))
            
            # calculate drawing parameters
            center   = self.pieCenter()
            radius   = self.radius()
            diameter = radius * 2
            angle    = 0
            bound    = QRectF(-radius, -radius, diameter, diameter)
            
            for key, value in sorted(pie_values.items(), key = lambda x: x[1]):
                # calculate the percentage
                perc  = float(value) / total
                
                # calculate the angle as the perc * 360
                item_angle = perc * 360
                self.setPos(center)
                
                sub_path = QPainterPath()
                sub_path.arcTo(bound, angle, item_angle)
                sub_path.lineTo(0, 0)
                
                path.addPath(sub_path)
                self._subpaths.append((key, value, sub_path))
                
                angle += item_angle
                
        self.setPath(path)
        self._dirty = False
    
    def points( self ):
        """
        Returns a list of the points for this item.
        
        :return     [(<variant> x, <variant> y), ..]
        """
        return self._points
    
    def setAlternateColor( self, color ):
        """
        Sets the alternate color for this widget to the inputed color.
        
        :param      color | <QColor>
        """
        self._alternateColor = QColor(color)
    
    def setChartType( self, chartType ):
        """
        Sets the chart type for this item.  Setting the item to a None chart 
        type will signal it to use the default scenes chart type.
        
        :param      chartType | <XChartScene.Type>
        """
        self._chartType = chartType
        self._dirty = True
    
    def setColor( self, color ):
        """
        Sets the color for this widget to the inputed color.
        
        :param      color | <QColor>
        """
        self._color = QColor(color)
        self.setAlternateColor(self._color.lighter(140))
    
    def setDirty( self, state = True ):
        """
        Sets whether or not this item is dirty.
        
        :param      state | <bool>
        """
        self._dirty
    
    def setDragData(self, data, x=None, y=None):
        """
        Sets the drag data for this chart item to the inputed data.
        
        :param      data | <QMimeData> || None
        """
        self._dragData[(x, y)] = data
    
    def setKeyColor( self, key, color ):
        """
        Sets the color used when rendering pie charts.
        
        :param      key   | <str>
                    color | <QColor>
        """
        self._keyColors[nativestring(key)] = QColor(color)
    
    def setKeyToolTip( self, key, tip ):
        """
        Sets the tool tip for the specified key.
        
        :param      key | <str>
                    tip | <str>
        """
        self._keyToolTips[nativestring(key)] = tip
    
    def setHorizontalOffset( self, offset ):
        """
        Sets the horizontal offset for this item.
        
        :param     offset | <int>
        """
        self._horizontalOffset = offset
    
    def setPieCenter( self, center ):
        """
        Sets the center for the pie for the chart.
        
        :param      center | <QPointF>
        """
        self._pieCenter = center
    
    def setPointRadius(self, radius):
        """
        Sets the point radius for this line.
        
        :param      radius | <int>
        """
        self._pointRadius = radius
    
    def setPoints(self, points):
        """
        Sets the points values for this chart widget item.
        
        :param      points | [(<variant> x, <variant> y), ..]
        """
        self._points = points[:]
    
    def setPos( self, *args ):
        super(XChartWidgetItem, self).setPos(*args)
        
        if ( self._horizontalOffset or self._verticalOffset ):
            offset = QPointF(self._horizontalOffset, self._verticalOffset)
            super(XChartWidgetItem, self).setPos(self.pos() + offset)
    
    def setPieAxis( self, pieAxis ):
        """
        Sets the axis that will be used for the pie chart for this item.  This
        will only apply when the item itself defines itself as a pie chart, 
        otherwise, the scene will determine it when the scene is rendered as a
        pie chart.
        
        :param      pieAxis | <Qt.Axis>
        """
        self._pieAxis = pieAxis
    
    def setRadius( self, radius ):
        """
        Sets the radius size for this item.
        
        :param      radius | <float>
        """
        self._radius = radius
    
    def setShaded( self, state ):
        """
        Sets whether or not to shade line items in this graph.
        
        :param      state | <bool>
        """
        self._shaded = state
    
    def setShowPointsInLine( self, state ):
        """
        Sets whether or not to show points in line mode.
        
        :param      state | <bool>
        """
        self._showPointsInLine = state
    
    def setTitle( self, title ):
        """
        Sets the title text for this chart widget item.
        
        :param      title | <str>
        """
        self._title = title
    
    def startDrag(self, data):
        """
        Starts dragging information from this chart widget based on the
        dragData associated with this item.
        """
        if not data:
            return
        
        widget = self.scene().chartWidget()
        drag = QDrag(widget)
        drag.setMimeData(data)
        drag.exec_()
    
    def showPointsInLine( self ):
        """
        Returns whether or not to show points in the line.
        
        :return     <bool>
        """
        return self._showPointsInLine
    
    def title( self ):
        """
        Returns the title for this item.
        
        :return     <str>
        """
        return self._title
    
    def verticalRuler( self ):
        """
        Returns the vertical ruler for this widget item.
        
        :return     <projexui.widgets.xchartwidget.XChartRuler> || None
        """
        if ( not self.scene() ):
            return None
        return self.scene().verticalRuler()