#!/usr/bin/python

""" Defines a chart widget for use in displaying data. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2013, Projex Software'
__license__         = 'LGPL'

# maintenance information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

from projexui.qt.QtGui import QGraphicsScene

from .xchartdatasetitem import XChartDatasetItem

class XChartScene(QGraphicsScene):
    def __init__(self, chart):
        super(XChartScene, self).__init__(chart)
        
        # define custom properties
        self._chart = chart
    
    def addDataset(self, dataset):
        """
        Creates a new dataset instance for this scene.
        
        :param      dataset | <XChartDataset>
        
        :return     <XChartDatasetItem>
        """
        item = XChartDatasetItem()
        self.addItem(item)
        item.setDataset(dataset)
        return item
    
    def chart(self):
        """
        Returns the chart associated with the scene.
        
        :return     <XChart>
        """
        return self._chart
    
    def datasetItems(self):
        """
        Returns the items in this scene mapped with their dataset instance.
        
        :return     {<XChartDataset>: <QGraphicsItem>, ..}
        """
        out = {}
        for item in self.items():
            if isinstance(item, XChartDatasetItem):
                out[item.dataset()] = item
        return out
    
    def drawBackground(self, painter, rect):
        """
        Draws the background for the chart scene.
        
        :param      painter | <QPainter>
                    rect    | <QRect>
        """
        chart = self.chart()
        chart._drawBackground(self, painter, rect)

    def drawForeground(self, painter, rect):
        """
        Draws the foreground for the chart scene.
        
        :param      painter | <QPainter>
                    rect    | <QRect>
        """
        chart = self.chart()
        chart._drawForeground(self, painter, rect)
