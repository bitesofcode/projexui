#!/usr/bin/python

""" Defines a gantt widget item class for adding items to the widget. """

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

from projexui.qt.QtCore   import QPointF

from projexui.qt.QtGui    import QGraphicsPathItem,\
                                 QColor,\
                                 QPainterPath,\
                                 QPolygonF

#------------------------------------------------------------------------------

class XGanttDepItem(QGraphicsPathItem):
    def __init__( self, source, target ):
        super(XGanttDepItem, self).__init__()
        
        # define custom properties
        self._sourceItem = source
        self._targetItem = target
        self._polygon    = None
        
        # set standard properties
        self.setZValue(-1)
        self.setPen(QColor('green'))
    
    def paint( self, painter, option, widget ):
        """
        Overloads the paint method from QGraphicsPathItem to \
        handle custom drawing of the path using this items \
        pens and polygons.
        
        :param      painter     <QPainter>
        :param      option      <QGraphicsItemStyleOption>
        :param      widget      <QWidget>
        """
        super(XGanttDepItem, self).paint(painter, option, widget)
        
        # redraw the poly to force-fill it
        if ( self._polygon ):
            painter.setRenderHint(painter.Antialiasing)
            painter.setBrush(self.pen().color())
            painter.drawPolygon(self._polygon)
    
    def rebuild( self ):
        """
        Rebuilds the dependency path for this item.
        """
        scene      = self.scene()
        if ( not scene ):
            return
        
        sourcePos  = self.sourceItem().viewItem().pos()
        sourceRect = self.sourceItem().viewItem().rect()
        
        targetPos  = self.targetItem().viewItem().pos()
        targetRect = self.targetItem().viewItem().rect()
        
        cellWidth  = scene.ganttWidget().cellWidth()
        
        startX = sourcePos.x() + sourceRect.width() - (cellWidth / 2.0)
        startY = sourcePos.y() + (sourceRect.height() / 2.0)
        
        endX   = targetPos.x() - 2
        endY   = targetPos.y() + (targetRect.height() / 2.0)
        
        path = QPainterPath()
        path.moveTo(startX, startY)
        path.lineTo(startX, endY)
        path.lineTo(endX, endY)
        
        a = QPointF(endX - 10, endY - 3)
        b = QPointF(endX, endY)
        c = QPointF(endX - 10, endY + 3)
        
        self._polygon = QPolygonF([a, b, c, a])
        
        path.addPolygon(self._polygon)
        
        self.setPath(path)
    
    def sourceItem( self ):
        """
        Returns the source gantt item for this dependency.
        
        :return     <XGanttWidgetItem>
        """
        return self._sourceItem
    
    def targetItem( self ):
        """
        Returns the target gantt item for this dependency.
        
        :return     <XGanttWidgetItem>
        """
        return self._targetItem