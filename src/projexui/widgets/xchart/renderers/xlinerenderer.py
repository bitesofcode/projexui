#!/usr/bin/python

""" 
Defines the Line renderer class that will be used to render line graphs for
the chart.
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

from projexui.qt.QtCore import Qt, QPointF
from projexui.qt.QtGui import QPen, QApplication, QColor, QPainterPath

from ..xchartrenderer import XChartRenderer

class XLineRenderer(XChartRenderer):
    def __init__(self):
        super(XLineRenderer, self).__init__()
        
        # define custom properties
        self._showPoints = True
        self._pointRadius = 6
        
    def calculateDatasets(self, scene, axes, datasets):
        """
        Builds the datasets for this renderer.  Each renderer will need to
        subclass and implemenent this method, otherwise, no data will be
        shown in the chart.
        
        :param      scene | <XChartScene>
                    axes | [<
                    datasets | [<XChartDataset>, ..]
        """
        items = self.calculateDatasetItems(scene, datasets)
        if not items:
            scene.clear()
            return
        
        rect = self.buildData('axis_rect')
        
        for dataset, item in items.items():
            first = True
            pos = None
            home = None
            ellipses = []
            
            path = QPainterPath()
            for value in dataset.values():
                pos = self.pointAt(axes, value)
                ellipses.append(pos)
                
                if first:
                    path.moveTo(pos)
                    first = False
                else:
                    path.lineTo(pos)
            
            item.setPath(path)
            item.setBuildData('ellipses', ellipses)
    
    def drawItem(self, item, painter, option):
        """
        Draws the inputed item as a bar graph.
        
        :param      item    | <XChartDatasetItem>
                    painter | <QPainter>
                    option  | <QStyleOptionGraphicsItem>
        """
        dataset = item.dataset()
        
        painter.save()
        painter.setRenderHint(painter.Antialiasing)
        
        pen = QPen(dataset.color())
        pen.setWidth(3)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(item.path())
        
        if self.showPoints():
            palette = QApplication.palette()
            pen = QPen(palette.color(palette.Base))
            pen.setWidth(2)
            
            painter.setBrush(dataset.color())
            painter.setPen(pen)
            
            for point in item.buildData('ellipses', []):
                painter.drawEllipse(point,
                                    self.pointRadius(),
                                    self.pointRadius())
        
        painter.restore()
    
    def pointRadius(self):
        """
        Returns the point radius for this renderer.
        
        :return     <int>
        """
        return self._pointRadius
    
    def setPointRadius(self, radius):
        """
        Sets the point radius for this renderer.
        
        :param      radius | <int>
        """
        self._pointRadius = radius
    
    def setShowPoints(self, state):
        """
        Sets whether or not this renderer should show points in the line.
        
        :param      state | <bool>
        """
        self._showPoints = state
    
    def showPoints(self):
        """
        Returns whether or not this renderer should show the points in a line.
        
        :return     <bool>
        """
        return self._showPoints

XChartRenderer.register('Line', XLineRenderer)