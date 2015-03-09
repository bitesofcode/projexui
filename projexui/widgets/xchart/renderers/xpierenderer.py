#!/usr/bin/python

""" 
Defines the Pie renderer class that will be used to render pie graphs for
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

from projexui.qt.QtCore import Qt, QRectF, QPointF
from projexui.qt.QtGui import QPainterPath,\
                              QColor,\
                              QPen,\
                              QStyle

from ..xchartrenderer import XChartRenderer
from ..axes.xdatasetaxis import XDatasetAxis

class XPieRenderer(XChartRenderer):
    def __init__(self):
        super(XPieRenderer, self).__init__()
        
        # don't bother use axis information for the pie renderer
        self.setShowXAxis(False)
        self.setShowYAxis(False)
        self.setShowGrid(False)
    
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
        
        xaxis = scene.chart().horizontalAxis()
        yaxis = scene.chart().verticalAxis()
        data_axis = None
        all_values = []
        
        # determine if we're mapping data aginst the sets themselves, in
        # which case, create a pie chart of the dataset vs. its 
        if isinstance(xaxis, XDatasetAxis):
            per_dataset = False
            data_axis = yaxis
            total = 1
        
        elif isinstance(yaxis, XDatasetAxis):
            per_dataset = False
            total = 1
            data_axis = xaxis
        
        else:
            per_dataset = True
            total = len(items)
        
        if not per_dataset:
            all_values = [dataset.sum(data_axis) \
                          for dataset in datasets]
        
        # generate the build information
        rect = self.buildData('grid_rect')
        rect.setX(rect.x() + 10)
        rect.setY(rect.y() + 10)
        rect.setWidth(rect.width() - 20)
        rect.setHeight(rect.height() - 20)
        
        if rect.width() > rect.height():
            radius = min(rect.width() / 2.0, rect.height() / 2.0)
            x = rect.left()
            y = rect.top() + radius
            deltax = min(radius * 2, rect.width() / float(total + 1))
            deltay = 0
        else:
            radius = min(rect.height() / 2.0, rect.width() / 2.0)
            x = rect.left() + radius
            y = rect.top()
            deltax = 0
            deltay = min(radius * 2, rect.height() / float(total + 1))
        
        # initialize the first pie chart
        angle = 0
        cx = x + deltax
        cy = y + deltay
        
        x += deltax
        y += deltay
        
        self.setBuildData('center', QPointF(cx, cy))
        self.setBuildData('radius', radius)
        
        for dataset in datasets:
            item = items.get(dataset)
            if not item:
                continue
            
            item.setBuildData('center', QPointF(cx, cy))
            item.setBuildData('radius', radius)
            
            subpaths = []
            bound = QRectF(cx-radius, cy-radius, radius * 2, radius * 2)
            path = QPainterPath()
            if per_dataset:
                data_values = dataset.values(yaxis.name())
                andle = 0
                for value in dataset.values():
                    perc = yaxis.percentOfTotal(value.get(yaxis.name()),
                                                data_values)
                    
                    # calculate the angle as the perc
                    item_angle = perc * 360
                    
                    subpath = QPainterPath()
                    subpath.moveTo(cx, cy)
                    subpath.arcTo(bound, angle, item_angle)
                    subpath.lineTo(cx, cy)
                    
                    path.addPath(subpath)
                    subpaths.append((value.get(xaxis.name()), subpath))
                    
                    angle += item_angle
                    
                cx = x + deltax
                cy = y + deltay
                
                x += deltax
                y += deltay
            else:
                value = dataset.sum(data_axis)
                perc = data_axis.percentOfTotal(value, all_values)
                
                # calculate the angle as the perc
                item_angle = perc * 360
                
                subpath = QPainterPath()
                subpath.moveTo(cx, cy)
                subpath.arcTo(bound, angle, item_angle)
                subpath.lineTo(cx, cy)
                
                path.addPath(subpath)
                subpaths.append((value, subpath))
                
                angle += item_angle
                
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
        
        center = item.buildData('center')
        radius = item.buildData('radius')
        
        if int(option.state) & QStyle.State_MouseOver != 0:
            alpha = 20
            mouse_over = True
        else:
            alpha = 0
            mouse_over = False
        
        for value, subpath in item.buildData('subpaths', []):
            clr = dataset.color(value)
            
            bg = clr.lighter(110)
            bg.setAlpha(alpha + 100)
            painter.setBrush(bg)
            
            if mouse_over:
                scale = 1.08
                dx = (center.x() / scale) - center.x()
                dy = (center.y() / scale) - center.y()
                
                painter.save()
                painter.scale(scale, scale)
                painter.translate(dx, dy)
                painter.setPen(Qt.NoPen)
                painter.drawPath(subpath)
                painter.restore()
            
            pen = QPen(clr)
            pen.setWidth(0.5)
            painter.setPen(pen)
            
            painter.drawPath(subpath)
            
        painter.restore()
    
    
XChartRenderer.register('Pie', XPieRenderer)