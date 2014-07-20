""" Defines the tracker item for this chart widget. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software, LLC'
__license__         = 'LGPL'

__maintainer__      = 'Projex Software, LLC'
__email__           = 'team@projexsoftware.com'

from projexui.qt.QtCore import QPointF

from projexui.qt.QtGui import QGraphicsPathItem,\
                              QPainterPath,\
                              QColor,\
                              QPen

from projexui.widgets.xpopupwidget import XPopupWidget

class XChartTrackerItem(QGraphicsPathItem):
    """
    Defines an item for tracking information about chart items.
    """
    def __init__( self ):
        super(XChartTrackerItem, self).__init__()
        
        self._color     = QColor('blue')
        self._basePath  = None
        self._ellipses  = []
    
    def color( self ):
        """
        Returns the color for this tracker item.
        
        :return     <QColor>
        """
        return self._color
    
    def paint( self, painter, option, widget ):
        """
        Paints this item.
        
        :param      painter | <QPainter>
                    option  | <QGraphicsOption>
                    widget  | <QWidget>
        """
        painter.save()
        pen = QPen(self.color())
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawPath(self._basePath)
        painter.setRenderHint(painter.Antialiasing)
        
        
        pen.setColor(QColor('white'))
        painter.setPen(pen)
        painter.setBrush(self.color())
        for ellipse in self._ellipses:
            painter.drawEllipse(ellipse, 6, 6)
        
        painter.restore()
    
    def rebuild( self, gridRect ):
        """
        Rebuilds the tracker item.
        """
        scene = self.scene()
        if ( not scene ):
            return
        
        self.setVisible(gridRect.contains(self.pos()))
        self.setZValue(100)
        
        path = QPainterPath()
        path.moveTo(0, 0)
        path.lineTo(0, gridRect.height())
        
        tip             = ''
        tip_point       = None
        self._ellipses  = []
        items           = scene.collidingItems(self)
        self._basePath  = QPainterPath(path)
        
        for item in items:
            item_path = item.path()
            found = None
            for y in range(int(gridRect.top()), int(gridRect.bottom())):
                point = QPointF(self.pos().x(), y)
                if ( item_path.contains(point) ):
                    found = QPointF(0, y - self.pos().y())
                    break
            
            if ( found ):
                path.addEllipse(found, 6, 6)
                self._ellipses.append(found)
                
                # update the value information
                value     = scene.valueAt(self.mapToScene(found))
                tip_point = self.mapToScene(found)
                hruler    = scene.horizontalRuler()
                vruler    = scene.verticalRuler()
                
                x_value = hruler.formatValue(value[0])
                y_value = vruler.formatValue(value[1])
                
                tip = '<b>x:</b> %s<br/><b>y:</b> %s' % (x_value, y_value)
        
        self.setPath(path)
        self.setVisible(True)
        
        # show the popup widget
        if ( tip ):
            anchor    = XPopupWidget.Anchor.RightCenter
            widget    = self.scene().chartWidget()
            tip_point = widget.mapToGlobal(widget.mapFromScene(tip_point))
            
            XPopupWidget.showToolTip(tip, 
                                     anchor = anchor,
                                     parent = widget,
                                     point  = tip_point,
                                     foreground = QColor('blue'),
                                     background = QColor(148, 148, 255))
    
    def setColor( self, color ):
        """
        Sets the color for this tracker item to the given color.
        
        :param      color | <QColor>
        """
        self._color = QColor(color)
        
    def setValue( self, value ):
        """
        Moves the line to the given value and rebuilds it
        
        :param      value | <variant>
        """
        scene = self.scene()
        point = scene.mapFromChart(value, None)
        
        self.setPos(point.x(), self.pos().y())
        self.rebuild(scene.gridRect())