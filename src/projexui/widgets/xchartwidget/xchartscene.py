""" 
Defines the QGraphicsScene class that is at the heart managing the different
objects.
"""

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2012, Projex Software'
__license__         = 'LGPL'

# maintenance information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

#------------------------------------------------------------------------------

import weakref

from projexui.qt import Signal
from projexui.qt.QtCore import QLineF,\
                               Qt,\
                               QRectF,\
                               QPointF

from projexui.qt.QtGui import QGraphicsScene,\
                              QFontMetrics,\
                              QApplication,\
                              QPen,\
                              QColor,\
                              QPainterPath,\
                              QCursor

from projex.enum import enum

from projexui.widgets.xchartwidget.xchartruler       import XChartRuler
from projexui.widgets.xchartwidget.xcharttrackeritem import XChartTrackerItem

XChartWidgetItem = None

class XChartScene( QGraphicsScene ):
    Type             = enum('Bar', 'Pie', 'Line')
    
    chartTypeChanged = Signal()
    
    def __init__( self, chartWidget ):
        super(XChartScene, self).__init__(chartWidget)
        
        # create custom properties
        self._chartWidget       = chartWidget
        self._minimumWidth      = -1
        self._minimumHeight     = -1
        self._maximumWidth      = -1
        self._maximumHeight     = -1
        self._horizontalPadding = 6
        self._verticalPadding   = 6
        self._showGrid          = True
        self._showRows          = True
        self._showColumns       = True
        self._trackingEnabled   = True
        self._chartType         = XChartScene.Type.Line
        self._trackerItem       = None
        
        # used with pie charts
        self._pieAxis           = Qt.YAxis
        self._pieAlignment      = Qt.AlignCenter
        
        self._horizontalRuler   = XChartRuler(XChartRuler.Type.Number)
        self._verticalRuler     = XChartRuler(XChartRuler.Type.Number)
        self._font              = QApplication.font()
        
        self._alternatingColumnColors = False
        self._alternatingRowColors    = True
        
        self._dirty             = False
        self._buildData         = {}
        
        palette                 = QApplication.palette()
        
        self._axisColor         = palette.color(palette.Mid).darker(125)
        self._baseColor         = palette.color(palette.Base)
        self._alternateColor    = palette.color(palette.Base).darker(104)
        self._borderColor       = palette.color(palette.Mid)
        
        # create custom properties
        chartWidget.installEventFilter(self)
        self.chartTypeChanged.connect(self.update)
    
    def alternateColor( self ):
        """
        Returns the color to be used for the alternate background.
        
        :return     <QColor>
        """
        return self._alternateColor
    
    def alternatingColumnColors( self ):
        """
        Returns whether or not to display alternating column colors.
        
        :return     <bool>
        """
        return self._alternatingColumnColors
    
    def alternatingRowColors( self ):
        """
        Returns whehter or not to display alternating row colors.
        
        :return     <bool>
        """
        return self._alternatingRowColors
    
    def axisColor( self ):
        """
        Returns the axis color for this chart.
        
        :return     <QColor>
        """
        return self._axisColor
    
    def baseColor( self ):
        """
        Returns the color to be used for the primary background.
        
        :return     <QColor>
        """
        return self._baseColor
    
    def borderColor( self ):
        """
        Returns the color to be used for the chart borders.
        
        :return     <QColor>
        """
        return self._borderColor
    
    def chartWidget( self ):
        """
        Returns the chart widget this scene is linked to.
        
        :return     <XChartWidget>
        """
        return self._chartWidget
    
    def chartItems(self):
        """
        Returns the chart items that are found within this scene.
        
        :return     [<XChartWidgetItem>, ..]
        """
        from projexui.widgets.xchartwidget import XChartWidgetItem
        return filter(lambda x: isinstance(x, XChartWidgetItem), self.items())
    
    def chartType( self ):
        """
        Returns the chart type for this scene.
        
        :return     <XChartScene.Type>
        """
        return self._chartType
    
    def drawBackground( self, painter, rect ):
        """
        Draws the backgrounds for the different chart types.
        
        :param      painter | <QPainter>
                    rect    | <QRect>
        """
        if ( self._dirty ):
            self.rebuild()
        
        if ( self.showGrid() ):
            self.drawGrid(painter)
    
    def drawForeground( self, painter, rect ):
        """
        Draws the foreground for the different chart types.
        
        :param      painter | <QPainter>
                    rect    | <QRect>
        """
        if ( self.showGrid() ):
            self.drawAxis(painter)
    
    def drawGrid( self, painter ):
        """
        Draws the rulers for this scene.
        
        :param      painter | <QPainter>
        """
        # draw the minor grid lines
        pen = QPen(self.borderColor())
        painter.setPen(pen)
        painter.setBrush(self.baseColor())
        
        # draw the grid data
        painter.drawRect(self._buildData['grid_rect'])
        
        painter.setBrush(self.alternateColor())
        painter.setPen(Qt.NoPen)
        
        if ( self.alternatingRowColors() ):
            for alt_rect in self._buildData['grid_h_alt']:
                painter.drawRect(alt_rect)
        
        if ( self.alternatingColumnColors() ):
            for alt_rect in self._buildData['grid_v_alt']:
                painter.drawRect(alt_rect)
        
        if ( self.showGrid() ):
            painter.setPen(pen)
            
            grid = []
            if ( self.showRows() ):
                grid += self._buildData['grid_h_lines']
            
            if ( self.showColumns() ):
                grid += self._buildData['grid_v_lines']
            
            painter.drawLines(grid)
    
    def drawAxis( self, painter ):
        """
        Draws the axis for this system.
        """
        # draw the axis lines
        pen = QPen(self.axisColor())
        pen.setWidth(4)
        painter.setPen(pen)
        painter.drawLines(self._buildData['axis_lines'])
        
        # draw the notches
        for rect, text in self._buildData['grid_h_notches']:
            painter.drawText(rect, Qt.AlignTop | Qt.AlignRight, text)
        
        for rect, text in self._buildData['grid_v_notches']:
            painter.drawText(rect, Qt.AlignCenter, text)
    
    def enterEvent( self, event ):
        """
        Toggles the display for the tracker item.
        """
        item = self.trackerItem()
        if ( item ):
            item.setVisible(True)
    
    def eventFilter( self, object, event ):
        """
        Filters the chart widget for the resize event to modify this scenes
        rect.
        
        :param      object | <QObject>
                    event | <QEvent>
        """
        if ( event.type() != event.Resize ):
            return False
        
        size     = event.size()
        w        = size.width()
        h        = size.height()
        hpolicy  = Qt.ScrollBarAlwaysOff
        vpolicy  = Qt.ScrollBarAlwaysOff
        
        if ( self._minimumHeight != -1 and h < self._minimumHeight ):
            h      = self._minimumHeight
            vpolicy = Qt.ScrollBarAsNeeded
            
        if ( self._maximumHeight != -1 and self._maximumHeight < h ):
            h      = self._maximumHeight
            vpolicy = Qt.ScrollBarAsNeeded
        
        if ( self._minimumWidth != -1 and w < self._minimumWidth ):
            w      = self._minimumWidth
            hpolicy = Qt.ScrollBarAsNeeded
            
        if ( self._maximumWidth != -1 and self._maximumWidth < w ):
            w      = self._maximumWidth
            hpolicy = Qt.ScrollBarAsNeeded
        
        hruler = self.horizontalRuler()
        vruler = self.verticalRuler()
        
        hlen = hruler.minLength(Qt.Horizontal)
        vlen = hruler.minLength(Qt.Vertical)
        
        offset_w = 0
        offset_h = 0
        
#        if ( hlen > w ):
#            w        = hlen
#            hpolicy  = Qt.ScrollBarAlwaysOn
#            offset_h = 25
#        
#        if ( vlen > h ):
#            h        = vlen
#            vpolicy  = Qt.ScrollBarAlwaysOn
#            offset_w = 25
        
        self.setSceneRect(0, 0, w - offset_w, h - offset_h)
        object.setVerticalScrollBarPolicy(vpolicy)
        object.setHorizontalScrollBarPolicy(hpolicy)
        
        return False
    
    def font( self ):
        """
        Returns the font for this scene.
        
        :return     <QFont>
        """
        return self._font
    
    def gridRect( self ):
        """
        Returns the grid rect for this chart.
        
        :return     <QRectF>
        """
        if ( self._dirty ):
            self.rebuild()
        
        return self._buildData['grid_rect']
    
    def horizontalPadding( self ):
        """
        Returns the horizontal padding for this scene.
        
        :return     <int>
        """
        return self._horizontalPadding
    
    def horizontalRuler( self ):
        """
        Returns the horizontal (x-axis) ruler for this scene.
        """
        return self._horizontalRuler
    
    def isTrackingEnabled( self ):
        """
        Returns whether or not tracking is enabled for this chart.
        
        :return     <bool>
        """
        return self._trackingEnabled
    
    def leaveEvent( self, event ):
        """
        Toggles the display for the tracker item.
        """
        item = self.trackerItem()
        if ( item ):
            item.setVisible(False)
    
    def mapFromChart( self, x, y ):
        """
        Maps a chart point to a pixel position within the grid based on the
        rulers.
        
        :param      x | <variant>
                    y | <variant>
        
        :return     <QPointF>
        """
        grid      = self.gridRect()
        hruler    = self.horizontalRuler()
        vruler    = self.verticalRuler()
        
        xperc     = hruler.percentAt(x)
        yperc     = vruler.percentAt(y)
        
        xoffset   = grid.width() * xperc
        yoffset   = grid.height() * yperc
        
        xpos      = grid.left() + xoffset
        ypos      = grid.bottom() - yoffset
        
        return QPointF(xpos, ypos)
    
    def mouseMoveEvent( self, event ):
        """
        Overloads the moving event to move the tracker item.
        
        :param      event | <QEvent>
        """
        super(XChartScene, self).mouseMoveEvent(event)
        
        self.updateTrackerItem(event.scenePos())
    
    def pieAxis( self ):
        """
        Returns the axis that will be used when calculating percentages for the
        pie chart.
        
        :return     <Qt.Axis>
        """
        return self._pieAxis
    
    def pieAlignment( self ):
        """
        Returns the alignment location to be used for the chart pie.
        
        :return     <Qt.Alignment>
        """
        return self._pieAlignment
    
    def rebuild( self ):
        """
        Rebuilds the data for this scene to draw with.
        """
        global XChartWidgetItem
        if ( XChartWidgetItem is None ):
            from projexui.widgets.xchartwidget.xchartwidgetitem \
            import XChartWidgetItem
        
        self._buildData = {}
        
        # build the grid location
        x      = 8
        y      = 8
        w      = self.sceneRect().width()
        h      = self.sceneRect().height()
        hpad   = self.horizontalPadding()
        vpad   = self.verticalPadding()
        hmax   = self.horizontalRuler().maxNotchSize(Qt.Horizontal)
        
        left_offset   = hpad + self.verticalRuler().maxNotchSize(Qt.Vertical)
        right_offset  = left_offset + hpad
        top_offset    = vpad
        bottom_offset = top_offset + vpad + hmax
        
        left    = x + left_offset
        right   = w - right_offset
        top     = y + top_offset
        bottom  = h - bottom_offset
        
        rect = QRectF()
        rect.setLeft(left)
        rect.setRight(right)
        rect.setBottom(bottom)
        rect.setTop(top)
        
        self._buildData['grid_rect'] = rect
        
        # rebuild the ruler data
        self.rebuildGrid()
        self._dirty = False
        
        # rebuild all the items
        padding  = self.horizontalPadding() + self.verticalPadding()
        grid     = self.sceneRect()
        filt     = lambda x: isinstance(x, XChartWidgetItem)
        items    = filter(filt, self.items())
        height   = float(grid.height())
        if height == 0:
            ratio = 1
        else:
            ratio = grid.width() / height
        count    = len(items)
        
        if ( not count ):
            return
        
        if ( ratio >= 1 ):
            radius   = (grid.height() - padding * 2) / 2.0
            x        = rect.center().x()
            y        = rect.center().y()
            dx       = radius * 2.5
            dy       = 0
        else:
            radius   = (grid.width() - padding * 2) / 2.0
            x        = rect.center().x()
            y        = rect.center().y()
            dx       = 0
            dy       = radius * 2.5
        
        for item in items:
            item.setPieCenter(QPointF(x, y))
            item.setRadius(radius)
            item.rebuild()
            
            x += dx
            y += dy
        
        if ( self._trackerItem and self._trackerItem() ):
            self._trackerItem().rebuild(self._buildData['grid_rect'])
    
    def rebuildGrid( self ):
        """
        Rebuilds the ruler data.
        """
        vruler = self.verticalRuler()
        hruler = self.horizontalRuler()
        
        rect   = self._buildData['grid_rect']
        
        # process the vertical ruler
        h_lines     = []
        h_alt       = []
        h_notches   = []
        
        vpstart  = vruler.padStart()
        vnotches = vruler.notches()
        vpend    = vruler.padEnd()
        vcount   = len(vnotches) + vpstart + vpend
        deltay   = rect.height() / max((vcount - 1), 1)
        y        = rect.bottom()
        alt      = False
        
        for i in range(vcount):
            h_lines.append(QLineF(rect.left(), y, rect.right(), y))
            
            # store alternate color
            if ( alt ):
                alt_rect = QRectF(rect.left(), y, rect.width(), deltay)
                h_alt.append(alt_rect)
            
            # store notch information
            nidx = i - vpstart
            if ( 0 <= nidx and nidx < len(vnotches) ):
                notch = vnotches[nidx]
                notch_rect = QRectF(0, y - 3, rect.left() - 3, deltay)
                h_notches.append((notch_rect, notch))
            
            y -= deltay
            alt = not alt
        
        self._buildData['grid_h_lines']     = h_lines
        self._buildData['grid_h_alt']       = h_alt
        self._buildData['grid_h_notches']   = h_notches
        
        # process the horizontal ruler
        v_lines     = []
        v_alt       = []
        v_notches   = []
        
        hpstart     = hruler.padStart()
        hnotches    = hruler.notches()
        hpend       = hruler.padEnd()
        hcount      = len(hnotches) + hpstart + hpend
        deltax      = rect.width() / max((hcount - 1), 1)
        x           = rect.left()
        alt         = False
        
        for i in range(hcount):
            v_lines.append(QLineF(x, rect.top(), x, rect.bottom()))
            
            # store alternate info
            if ( alt ):
                alt_rect = QRectF(x - deltax, rect.top(), deltax, rect.height())
                v_alt.append(alt_rect)
            
            # store notch information
            nidx = i - hpstart
            if ( 0 <= nidx and nidx < len(hnotches) ):
                notch = hnotches[nidx]
                notch_rect = QRectF(x - (deltax / 2.0), 
                                    rect.bottom() + 3, 
                                    deltax, 
                                    13)
                v_notches.append((notch_rect, notch))
            
            x += deltax
            alt = not alt
        
        self._buildData['grid_v_lines']     = v_lines
        self._buildData['grid_v_alt']       = v_alt
        self._buildData['grid_v_notches']   = v_notches
        
        # draw the axis lines
        axis_lines = []
        axis_lines.append(QLineF(rect.left(), 
                                 rect.top(), 
                                 rect.left(), 
                                 rect.bottom()))
                                 
        axis_lines.append(QLineF(rect.left(), 
                                 rect.bottom(), 
                                 rect.right(), 
                                 rect.bottom()))
        
        self._buildData['axis_lines'] = axis_lines
    
    def setBarType(self):
        self.setChartType(XChartScene.Type.Bar)
    
    def setDirty( self, state = True ):
        """
        Marks the scene as dirty and needing a rebuild.
        
        :param      state | <bool>
        """
        self._dirty = state
    
    def setChartType( self, chartType ):
        """
        Sets the chart type for this scene to the inputed type.
        
        :param      chartType | <XChartScene.Type>
        """
        self._chartType = chartType
        self.setDirty()
        
        # setup default options
        if ( chartType == XChartScene.Type.Pie ):
            self.setShowGrid(False)
            
            self.horizontalRuler().setPadStart(0)
            self.horizontalRuler().setPadEnd(0)
            
        elif ( chartType == XChartScene.Type.Bar ):
            self.setShowGrid(True)
            self.setShowColumns(False)
            self.setShowRows(True)
            
            self.horizontalRuler().setPadStart(1)
            self.horizontalRuler().setPadEnd(1)
            
        else:
            self.setShowGrid(True)
            self.setShowColumns(True)
            self.setShowRows(True)
            
            self.horizontalRuler().setPadStart(0)
            self.horizontalRuler().setPadEnd(0)
        
        if ( not self.signalsBlocked() ):
            self.chartTypeChanged.emit()
    
    def setFont( self, font ):
        """
        Sets the font for this scene.
        
        :param      font | <QFont>
        """
        self._font = font
    
    def setHorizontalPadding( self, padding ):
        """
        Sets the horizontal padding amount for this chart to the given value.
        
        :param      padding | <int>
        """
        self._horizontalPadding = padding
    
    def setHorizontalRuler( self, ruler ):
        """
        Sets the horizontal ruler for this chart to the inputed ruler.
        
        :param      ruler | <XChartRuler>
        """
        self._horizontalRuler = ruler
    
    def setLineType(self):
        self.setChartType(XChartScene.Type.Line)
    
    def setPieAlignment( self, alignment ):
        """
        Sets the alignment to be used when rendering a pie chart.
        
        :param      alignment | <Qt.Alignment>
        """
        self._alignment = alignment
    
    def setPieAxis( self, axis ):
        """
        Sets the axis to be used when calculating pie chart information.
        
        :param      axis | <Qt.Axis>
        """
        self._pieAxis = axis
    
    def setPieType(self):
        self.setChartType(XChartScene.Type.Pie)
    
    def setSceneRect( self, *args ):
        """
        Overloads the set scene rect to handle rebuild information.
        """
        super(XChartScene, self).setSceneRect(*args)
        self._dirty = True
    
    def setShowColumns( self, state ):
        """
        Sets whether or not to display the columns for this chart.
        
        :param      state | <bool>
        """
        self._showColumns = state
    
    def setShowGrid( self, state ):
        """
        Sets whether or not the grid should be visible.
        
        :param      state | <bool>
        """
        self._showGrid = state
    
    def setShowRows( self, state ):
        """
        Sets whether or not to display the rows for this chart.
        
        :param      state | <bool>
        """
        self._showRows = state
    
    def setTrackingEnabled( self, state ):
        """
        Sets whether or not information tracking is enabled for this chart.
        
        :param      state | <bool>
        """
        self._trackingEnabled = state
        self.updateTrackerItem()
    
    def setVerticalPadding( self, padding ):
        """
        Sets the vertical padding amount for this chart to the given value.
        
        :param      padding | <int>
        """
        self._verticalPadding = padding
    
    def setVerticalRuler( self, ruler ):
        """
        Sets the vertical ruler for this chart to the inputed ruler.
        
        :param      ruler | <XChartRuler>
        """
        self._verticalRuler = ruler
    
    def showColumns( self ):
        """
        Returns whether or not to show columns for this scene.
        
        :return     <bool>
        """
        return self._showColumns
    
    def showGrid( self ):
        """
        Sets whether or not the grid should be visible for this scene.
        
        :return     <bool>
        """
        return self._showGrid
    
    def showRows( self ):
        """
        Returns whether or not to show rows for this scene.
        
        :return     <bool>
        """
        return self._showRows
    
    def trackerItem( self ):
        """
        Returns the tracker item for this chart.
        
        :return     <XChartTrackerItem> || None
        """
        # check for the tracking enabled state
        if not self.isTrackingEnabled():
            return None
        
        # generate a new tracker item
        if not (self._trackerItem and self._trackerItem()):
            item = XChartTrackerItem()
            self.addItem(item)
            self._trackerItem = weakref.ref(item)
        
        return self._trackerItem()
    
    def updateTrackerItem( self, point = None ):
        """
        Updates the tracker item information.
        """
        item = self.trackerItem()
        if not item:
            return
        
        gridRect = self._buildData.get('grid_rect')
        
        if ( not (gridRect and gridRect.isValid()) ):
            item.setVisible(False)
            return
        
        if ( point is not None ):
            item.setPos(point.x(), gridRect.top())
        
        if ( not gridRect.contains(item.pos()) ):
            item.setVisible(False)
            return
        
        if ( self.chartType() != self.Type.Line ):
            item.setVisible(False)
            return
        
        if ( not self.isTrackingEnabled() ):
            item.setVisible(False)
            return
        
        item.rebuild(gridRect)
    
    def valueAt( self, point ):
        """
        Returns the X, Y value for the given point.
        
        :param      point | <QPoint>
        
        :return     (<variant> x, <variant> y)
        """
        x = point.x()
        y = point.y()
        
        hruler = self.horizontalRuler()
        vruler = self.verticalRuler()
        
        grid   = self._buildData.get('grid_rect')
        if ( not grid ):
            return (None, None)
        
        x_perc = 1 - ((grid.right() - x) / grid.width())
        y_perc = ((grid.bottom() - y) / grid.height())
        
        return (hruler.valueAt(x_perc), vruler.valueAt(y_perc))
    
    def verticalPadding( self ):
        """
        Returns the vertical padding amount for this chart.
        
        :return     <int>
        """
        return self._verticalPadding
    
    def verticalRuler( self ):
        """
        Returns the vertical (y-axis) ruler for this chart.
        
        :return     <XChartRuler>
        """
        return self._verticalRuler