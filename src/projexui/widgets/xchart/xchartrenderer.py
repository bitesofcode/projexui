#!/usr/bin/python

""" 
Defines the base chart renderer class that will be used to
render chart data for a given widget.  This class will be subclassed to
process all the data for a given chart and render it out to the graphics view.
"""

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2013, Projex Software'
__license__         = 'LGPL'

# maintenance information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

#------------------------------------------------------------------------------

from projex.text import nativestring

from projexui.qt.QtCore import Qt, QRectF, QLineF, QPointF
from projexui.qt.QtGui import QPen,\
                              QColor,\
                              QApplication,\
                              QFontMetrics

class XChartRenderer(object):
    _plugins = {}
    
    def __init__(self):
        # define custom properties
        palette = QApplication.palette()
        
        self._name = 'Default'
        self._axisColor = palette.color(palette.Mid).darker(125)
        self._alternateColor = palette.color(palette.Base).darker(104)
        self._baseColor = palette.color(palette.Base)
        self._borderColor = palette.color(palette.Mid)
        self._showGrid = True
        self._showRows = True
        self._showColumns = True
        self._showXAxis = True
        self._showYAxis = True
        self._verticalLabelPadding = 4
        self._horizontalLabelPadding = 4
        self._alternatingRowColors = True
        self._alternatingColumnColors = False
        self._buildData = {}
    
    def alternateColor(self):
        """
        Returns the alternate color for this renderer.
        
        :return     <QColor>
        """
        return self._alternateColor
    
    def alternatingColumnColors(self):
        """
        Returns whether or not the column colors will alternate for this
        widget.
        
        :return     <bool>
        """
        return self._alternatingColumnColors
    
    def alternatingRowColors(self):
        """
        Returns whether or not the row colors will alternate for this
        widget.
        
        :return     <bool>
        """
        return self._alternatingRowColors
    
    def axisColor(self):
        """
        Returns the color that will be used for the axis for this
        renderer.
        
        :return     <QColor>
        """
        return self._axisColor
    
    def baseColor(self):
        """
        Returns the color that will be used for the base for this
        renderer.
        
        :return     <QColor>
        """
        return self._baseColor
    
    def borderColor(self):
        """
        Returns the color that will be used for the border for this
        renderer.
        
        :return     <QColor>
        """
        return self._borderColor
    
    def buildData(self, key, default=None):
        """
        Returns the build information for the given key.
        
        :param      key     | <str>
                    default | <variant>
        
        :return     <variant>
        """
        return self._buildData.get(nativestring(key), default)
    
    def calculate(self, scene, xaxis, yaxis):
        """
        Calculates the grid data before rendering.
        
        :param      scene       | <XChartScene>
                    xaxis       | <XChartAxis>
                    yaxis       | <XChartAxis>
        """
        # build the grid location
        sceneRect = scene.sceneRect()
        
        # process axis information
        h_lines  = []
        h_alt    = []
        h_labels = []
        v_lines  = []
        v_alt    = []
        v_labels = []
        
        xlabels   = []
        xcount    = 1
        xsections = 1
        xdelta    = 0
        xdeltamin = 0
        
        ylabels   = []
        ycount    = 1
        ysections = 1
        ydeltamin = 0
        ydelta    = 0
        
        axis_lft  = 0
        axis_rht  = 0
        axis_bot  = 0
        axis_top  = 0
        
        # precalculate xaxis information for width changes
        if xaxis and self.showXAxis():
            size = sceneRect.width()
            xdeltamin = xaxis.minimumLabelWidth()
            result = self.calculateAxis(xaxis, size, xdeltamin)
            
            xlabels, xcount, xsections, newWidth, xdelta = result
            if newWidth != size:
                sceneRect.setWidth(newWidth)
        
        # precalculate yaxis information for height changes
        if yaxis and self.showYAxis():
            size = sceneRect.height()
            ydeltamin = yaxis.minimumLabelHeight()
            result = self.calculateAxis(yaxis, size, ydeltamin)
            
            ylabels, ycount, ysections, newHeight, ydelta = result
            if newHeight != size:
                sceneRect.setHeight(newHeight)
        
        # generate the xaxis
        if xaxis and self.showXAxis():
            x        = sceneRect.left() + xdeltamin / 2
            axis_lft = x
            axis_rht = x
            alt      = False
            
            for i in range(xcount):
                v_lines.append(QLineF(x, sceneRect.top(),
                                      x, sceneRect.bottom()))
                
                # store alternate info
                if alt:
                    alt_rect = QRectF(x - xdelta, sceneRect.top(),
                                      xdelta, sceneRect.height())
                    v_alt.append(alt_rect)
                
                # store label information
                v_labels.append((x, xdelta, xlabels[i]))
                axis_rht = x
                
                x += xdelta
                alt = not alt
        
        # generate the yaxis
        if yaxis and self.showYAxis():
            y        = sceneRect.bottom() - ydeltamin / 2
            axis_bot = y
            axis_top = y
            alt      = False
            
            for i in range(ycount):
                h_lines.append(QLineF(sceneRect.left(), y,
                                      sceneRect.right(), y))
                
                # store alternate color
                if alt:
                    alt_rect = QRectF(sceneRect.left(), y,
                                      sceneRect.width(), ydelta)
                    h_alt.append(alt_rect)
                
                # store the vertical information
                h_labels.append((y, ydelta, ylabels[i]))
                axis_top = y
                
                y -= ydelta
                alt = not alt
        
        # assign the build data
        self._buildData['grid_h_lines']  = h_lines
        self._buildData['grid_h_alt']    = h_alt
        self._buildData['grid_h_labels'] = h_labels
        self._buildData['grid_v_lines']  = v_lines
        self._buildData['grid_v_alt']    = v_alt
        self._buildData['grid_v_labels'] = v_labels
        self._buildData['grid_rect']     = sceneRect
        self._buildData['axis_rect']     = QRectF(axis_lft, axis_top,
                                                  axis_rht - axis_lft,
                                                  axis_bot - axis_top)
        
        scene.setSceneRect(sceneRect)
        return sceneRect
    
    def calculateAxis(self, axis, size, minDelta):
        """
        Calculates the rendering information for the given axis based on
        the current size and the minimum required delta.
        
        :param      axis     | <XChartAxis>
                    size     | <int>
                    minDelta | <int>
        
        :return     ([<str>, ..] labels, \
                     <int> count, \
                     <int> sections, \
                     <int> newSize, \
                     <int> delta)
        """
        labels   = axis.labels()
        count    = len(labels)
        sections = max((count - 1), 1)
        newSize  = size
        delta    = (size - minDelta) / sections
        
        # ensure the sizes fit within our specs
        if labels and delta < minDelta and axis.isDynamicScalingEnabled():
            orig = labels[:]
            total = count - count % 2 # make sure we at least get a 2
            step_range = range(2, total / 2 + 1)
            steps = [i for i in step_range if not (total / float(i)) % 1]
            
            for step in steps:
                labels = orig[::step]
                if not orig[-1] in labels:
                    labels.append(orig[-1])
                count = len(labels)
                sections = max((count - 1), 1)
                delta = (size - minDelta) / sections
                
                if minDelta < delta:
                    break
            
            if delta < minDelta:
                labels = [orig[0], orig[-1]]
                count = 2
                sections = 1
                delta = (size - minDelta) / sections
        
        if delta < minDelta:
            newSize = (minDelta * sections) + minDelta
            delta = minDelta
        
        return (labels, count, sections, newSize, delta)
    
    def calculateDatasets(self, scene, axes, datasets):
        """
        Builds the datasets for this renderer.  Each renderer will need to
        subclass and implemenent this method, otherwise, no data will be
        shown in the chart.
        
        :param      datasets | [<XChartDataset>, ..]
        """
        pass
    
    def calculateDatasetItems(self, scene, datasets):
        """
        Syncs the scene together with the given datasets to make sure we
        have the proper number of items, by removing non-existant datasets
        and adding new ones.
        
        :param      scene    | <XChartScene>
                    datasets | <XChartDataset>
        
        :return     {<XChartDataset>: <XChartDatasetItem>, ..}
        """
        dataitems = scene.datasetItems()
        olditems = set(dataitems.keys()).difference(datasets)
        newitems = set(datasets).difference(dataitems.keys())
        
        for dataset in olditems:
            scene.removeItem(dataitems[dataset])
        
        for dataset in newitems:
            dataitems[dataset] = scene.addDataset(dataset)
        
        return dataitems
    
    def drawAxis(self, painter, rect, axis):
        """
        Draws the axis for the given painter.
        
        :param      painter | <QPainter>
                    rect    | <QRect>
        """
        if not axis:
            return
        
        # draw the axis lines
        painter.save()
        pen = QPen(self.axisColor())
        pen.setWidth(3)
        painter.setPen(pen)
        
        # draw the vertical line
        if axis.orientation() == Qt.Vertical:
            line = QLineF(rect.right(), rect.top(),
                          rect.right(), rect.bottom())
            
            painter.drawLine(line)
            painter.setFont(axis.labelFont())
            for y, height, label in self._buildData.get('grid_h_labels', []):
                painter.drawText(0, y - height / 2.0, rect.width() - 3, height,
                                 Qt.AlignRight | Qt.AlignVCenter, label)
            
            painter.translate(0, rect.center().y())
            painter.rotate(-90)
            
            painter.setFont(axis.titleFont())
            painter.drawText(-rect.height()/2, 0, rect.height(), rect.width(),
                             Qt.AlignHCenter | Qt.AlignTop, axis.title())
            
        # draw the horizontal line
        else:
            line = QLineF(rect.left(), rect.top(),
                          rect.right(), rect.top())
            
            painter.setFont(axis.titleFont())
            painter.drawText(rect,
                             Qt.AlignHCenter | Qt.AlignBottom,
                             axis.title())
            
            painter.drawLine(line)
            painter.setFont(axis.labelFont())
            for x, width, label in self._buildData.get('grid_v_labels', []):
                painter.drawText(x - width / 2.0, 3, width, rect.height() - 6,
                                 Qt.AlignHCenter | Qt.AlignTop, label)
        painter.restore()
    
    def drawForeground(self, painter, rect, showGrid, showColumns, showRows):
        """
        Draws the grid on the inputed painter
        
        :param      painter     | <QPainter>
                    rect        | <QRect>
                    showGrid    | <bool>
                    showColumns | <bool>
                    showRows    | <bool>
        """
        pass
    
    def drawGrid(self, painter, rect, showGrid, showColumns, showRows):
        """
        Draws the grid on the inputed painter
        
        :param      painter     | <QPainter>
                    rect        | <QRect>
                    showGrid    | <bool>
                    showColumns | <bool>
                    showRows    | <bool>
        """
        if not (self.showGrid() and showGrid):
            return
        
        # saves the painter state before continuing
        painter.save()
        
        # draw the grid data
        painter.setBrush(self.alternateColor())
        painter.setPen(Qt.NoPen)
        
        # draw alternating rows
        if self.alternatingRowColors():
            painter.drawRects(self._buildData.get('grid_h_alt', []))
        
        # draw alternating columns
        if self.alternatingColumnColors():
            painter.drawRects(self._buildData.get('grid_v_alt', []))
        
        # draws the grid lines
        painter.setPen(QPen(self.axisColor()))
        grid = []
        if self.showRows() and showRows:
            grid += self._buildData.get('grid_h_lines', [])
        if self.showColumns() and showColumns:
            grid += self._buildData.get('grid_v_lines', [])
        
        if grid:
            painter.drawLines(grid)
        
        # restores the painter when finished
        painter.restore()
    
    def drawItem(self, item, painter, option):
        """
        Draws the given item for this renderer.  By default, it will not
        draw any information.  This method should be overloaded in a subclass
        to handle per renderer drawing.
        
        :param      item    | <XChartDatasetItem>
                    painter | <QPainter>
                    option  | <QStyleOptionGraphicsItem>
        """
        pass
    
    def horizontalLabelPadding(self):
        """
        Returns the padding that will be used for the horiztonal
        direction for labels.
        
        :return     <int>
        """
        return self._horizontalLabelPadding
    
    def name(self):
        """
        Returns the name for this renderer to the inputed name.
        
        :return     <str>
        """
        return self._name
    
    def pointAt(self, axes, axis_values):
        """
        Returns the point that best represents this graph information.
        
        :param      axes        | [<XChartAxis>, ..]
                    axis_values | {<str> axisName, <variant> value
        
        :return     <QPointF>
        """
        point = QPointF()
        
        rect = self._buildData.get('axis_rect')
        if not rect:
            return point
        
        x_range = rect.right() - rect.left()
        y_range = rect.bottom() - rect.top()
        
        for axis in axes:
            if not axis.name() in axis_values:
                continue
            
            perc = axis.percentAt(axis_values[axis.name()])
            if axis.orientation() == Qt.Vertical:
                point.setY(rect.bottom() - perc * y_range)
            else:
                point.setX(rect.left() + perc * x_range)
        
        return point
    
    def setAlternateColor(self, color):
        """
        Sets the alternate base color for this renderer to the inputed color.
        
        :param      color | <QColor>
        """
        self._alternateColor = QColor(color)
    
    def setAlternatingColumnColors(self, state):
        """
        Sets whether or not this renderer is alternating.
        
        :param      state | <bool>
        """
        return self._alternatingColumnColors
    
    def setAlternatingRowColors(self, state):
        """
        Sets whether or not this renderer is alternating.
        
        :param      state | <bool>
        """
        return self._alternatingRowColors
    
    def setAxisColor(self, color):
        """
        Sets the axis base color for this renderer to the inputed color.
        
        :param      color | <QColor>
        """
        self._axisColor = QColor(color)
    
    def setBaseColor(self, color):
        """
        Sets the base base color for this renderer to the inputed color.
        
        :param      color | <QColor>
        """
        self._baseColor = QColor(color)
    
    def setBuildData(self, key, value):
        self._buildData[key] = value
    
    def setBorderColor(self, color):
        """
        Sets the border base color for this renderer to the inputed color.
        
        :param      color | <QColor>
        """
        self._borderColor = QColor(color)
    
    def setName(self, name):
        """
        Sets the name for this renderer to the inputed name.
        
        :param      <str>
        """
        self._name = name
    
    def setShowColumns(self, state):
        """
        Sets the whether or not this renderer should draw the grid.
        
        :param      state | <bool>
        """
        self._showColumns = state
        
    def setShowGrid(self, state):
        """
        Sets the whether or not this renderer should draw the grid.
        
        :param      state | <bool>
        """
        self._showGrid = state
    
    def setShowRows(self, state):
        """
        Sets the whether or not this renderer should draw the grid.
        
        :param      state | <bool>
        """
        self._showRows = state
    
    def setShowXAxis(self, state):
        """
        Sets the whether or not this renderer should draw the x-axis.
        
        :param      state | <bool>
        """
        self._showXAxis = state
    
    def setShowYAxis(self, state):
        """
        Sets the whether or not this renderer should draw the y-axis.
        
        :param      state | <bool>
        """
        self._showYAxis = state
    
    def showColumns(self):
        """
        Returns whether or not this renderer should draw the grid.
        
        :return     <bool>
        """
        return self._showColumns
    
    def showGrid(self):
        """
        Returns whether or not this renderer should draw the grid.
        
        :return     <bool>
        """
        return self._showGrid
    
    def showRows(self):
        """
        Returns whether or not this renderer should draw the grid.
        
        :return     <bool>
        """
        return self._showRows
    
    def showXAxis(self):
        """
        Returns whether or not this renderer should draw the x-axis.
        
        :return     <bool>
        """
        return self._showXAxis
    
    def showYAxis(self):
        """
        Returns whether or not this renderer should draw the y-axis.
        
        :return     <bool>
        """
        return self._showYAxis
    
    def valueAt(self, axes, point):
        """
        Returns the values for each axis at the given point within this
        renderer's axis rectangle.
        
        :param      axes  | [<XChartAxis>, ..]
                    point | <QPointF>
        
        :return     {<str> axis name: <variant> value}
        """
        rect = self._buildData.get('axis_rect')
        if not rect:
            return dict([(axis.name(), None) for axis in axes])
            
        try:
            x_perc = (point.x() - rect.left()) / (rect.right() - rect.left())
        except ZeroDivisionError:
            x_perc = 0.0
        
        try:
            y_perc = (rect.bottom() - point.y()) / (rect.bottom() - rect.top())
        except ZeroDivisionError:
            y_perc = 0.0
        
        out = {}
        for axis in axes:
            if axis.orientation() == Qt.Vertical:
                out[axis.name()] = axis.valueAt(y_perc)
            else:
                out[axis.name()] = axis.valueAt(x_perc)
        
        return out
    
    def verticalLabelPadding(self):
        """
        Returns the vertical padding for the labels for this renderer.
        
        :return     <int>
        """
        return self._verticalLabelPadding
    
    @staticmethod
    def plugin(name):
        """
        Returns the plugin renderer based on the inputed name.
        
        :param      name | <str>
        
        :return     <XChartRenderer> || None
        """
        cls = XChartRenderer._plugins.get(name)
        if cls:
            renderer = cls()
            renderer.setName(name)
            return renderer
        return None
    
    @staticmethod
    def plugins():
        """
        Returns a list of the plugin names for associated renderers.
        
        :return     [<str>, ..]
        """
        return sorted(XChartRenderer._plugins.keys())
    
    @staticmethod
    def register(name, plugin):
        """
        Registers the given plugin to the chart system.
        
        :param      plugin | <XChartRenderer>
        """
        XChartRenderer._plugins[nativestring(name)] = plugin
    