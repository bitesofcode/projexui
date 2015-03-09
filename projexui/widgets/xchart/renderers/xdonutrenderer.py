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

from projexui.qt import QtGui, QtCore
from .xpierenderer import XPieRenderer, XChartRenderer

class XDonutRenderer(XPieRenderer):
    def drawForeground(self, painter, rect, showGrid, showColumns, showRows):
        """
        Draws the grid on the inputed painter
        
        :param      painter     | <QPainter>
                    rect        | <QRect>
                    showGrid    | <bool>
                    showColumns | <bool>
                    showRows    | <bool>
        """
        painter.save()
        center = self.buildData('center')
        radius = self.buildData('radius') / 2.0
        palette = QtGui.QApplication.palette()
        pen = QtGui.QPen(palette.color(palette.Text))
        pen.setWidthF(0.75)
        painter.setBrush(palette.color(palette.Base))
        painter.setPen(pen)
        painter.setRenderHint(painter.Antialiasing)
        painter.drawEllipse(center, radius, radius)
        painter.restore()

XChartRenderer.register('Donut', XDonutRenderer)