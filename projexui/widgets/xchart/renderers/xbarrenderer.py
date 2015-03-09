#!/usr/bin/python

""" 
Defines the Bar renderer class that will be used to render bar graphs for
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

from projexui.qt.QtCore import Qt
from projexui.qt.QtGui import QPainterPath,\
                              QPen,\
                              QColor,\
                              QBrush,\
                              QLinearGradient

from ..xchartrenderer import XChartRenderer

class XBarRenderer(XChartRenderer):
    def __init__(self):
        super(XBarRenderer, self).__init__()
        
        # define custom properties
        self._orientation = Qt.Vertical
        self._maximumBarSize = 20
        
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
        half_size = self.maximumBarSize() / 2.0
        
        for dataset, item in items.items():
            path = QPainterPath()
            subpaths = []
            
            for value in dataset.values():
                pos = self.pointAt(axes, value)
                
                radius = min(rect.bottom() - pos.y(), 8)
                
                subpath = QPainterPath()
                
                # create a vertical bar graph
                if self.orientation() == Qt.Vertical:
                    subpath.moveTo(pos.x() - half_size, rect.bottom())
                    subpath.lineTo(pos.x() - half_size, pos.y() + radius)
                    subpath.quadTo(pos.x() - half_size, pos.y(),
                                   pos.x() - half_size + radius, pos.y())
                    subpath.lineTo(pos.x() + half_size - radius, pos.y())
                    subpath.quadTo(pos.x() + half_size, pos.y(),
                                   pos.x() + half_size, pos.y() + radius)
                    subpath.lineTo(pos.x() + half_size, rect.bottom())
                    subpath.lineTo(pos.x() - half_size, rect.bottom())
                
                # create a horizontal bar graph
                else:
                    subpath.moveTo(rect.left(), pos.y() - half_size)
                    subpath.lineTo(pos.x(),     pos.y() - half_size)
                    subpath.lineTo(pos.x(),     pos.y() + half_size)
                    subpath.lineTo(rect.left(), pos.y() + half_size)
                    subpath.lineTo(rect.left(), pos.y() - half_size)
                
                path.addPath(subpath)
                subpaths.append(subpath)
            
            item.setPath(path)
            item.setBuildData('subpaths', subpaths)
    
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
        pen.setWidth(0.75)
        painter.setPen(pen)
        
        for path in item.buildData('subpaths', []):
            gradient = QLinearGradient()
            
            clr = QColor(dataset.color())
            clr.setAlpha(220)
            
            gradient.setColorAt(0.0,  clr.lighter(180))
            gradient.setColorAt(0.1,  clr.lighter(160))
            gradient.setColorAt(0.25, clr.lighter(140))
            gradient.setColorAt(1.0,  clr.lighter(125))
            
            if self.orientation() == Qt.Vertical:
                gradient.setStart(0, path.boundingRect().bottom())
                gradient.setFinalStop(0, path.boundingRect().top())
            else:
                gradient.setStart(path.boundingRect().left(), 0)
                gradient.setFinalStop(path.boundingRect().right(), 0)
            
            painter.setBrush(gradient)
            painter.drawPath(path)
        
        painter.restore()
    
    def maximumBarSize(self):
        """
        Returns the maximum bar size for this renderer.
        
        :return     <int>
        """
        return self._maximumBarSize
    
    def orientation(self):
        """
        Returns the orientation that will be used for this bar chart.
        
        :return     <Qt.Orientation>
        """
        return self._orientation
    
    def setOrientation(self, orientation):
        """
        Sets the orientation that will be used for this bar chart.
        
        :param      orientation | <Qt.Orientation>
        """
        self._orientation = orientation

    def setMaximumBarSize(self, size):
        """
        Returns the maximum bar size for this renderer.
        
        :param      size | <int>
        """
        self._maximumBarSize = size
    
XChartRenderer.register('Bar', XBarRenderer)