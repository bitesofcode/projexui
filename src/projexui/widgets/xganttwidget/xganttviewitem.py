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

from projexui.qt          import wrapVariant
from projexui.qt.QtCore   import Qt
from projexui.qt.QtGui    import QGraphicsRectItem,\
                                 QColor,\
                                 QBrush,\
                                 QLinearGradient,\
                                 QPainterPath,\
                                 QGraphicsDropShadowEffect

#------------------------------------------------------------------------------

class XGanttViewItem(QGraphicsRectItem):
    def __init__(self, treeItem):
        super(XGanttViewItem, self).__init__()
        
        # define custom properties
        self._color                     = QColor('white')
        self._alternateColor            = QColor(230, 230, 230)
        self._highlightColor            = QColor('yellow')
        self._alternateHighlightColor   = self._highlightColor.darker(110)
        self._textColor                 = QColor('black')
        self._borderColor               = QColor(50, 50, 50)
        self._progressColor             = QColor(200, 200, 250)
        self._alternateProgressColor    = QColor(180, 180, 230)
        self._showProgress              = True
        self._padding                   = 3
        self._borderRadius              = 5
        self._percentComplete           = 0
        self._text                      = ''
        self._syncing                   = False
        self._treeItem                  = weakref.ref(treeItem)
        
        # setup standard properties
        flags  = self.ItemIsSelectable 
        flags |= self.ItemIsFocusable
        
        if treeItem.flags() & Qt.ItemIsEditable:
            flags |= self.ItemIsMovable
        
        effect = QGraphicsDropShadowEffect()
        effect.setXOffset(0)
        effect.setYOffset(0)
        effect.setColor(QColor(40, 40, 40, 100))
        effect.setBlurRadius(10)
        
        self.setFlags( flags )
        self.setAcceptHoverEvents(True)
        self.setGraphicsEffect(effect)
        
        # need this flag for Qt 4.6+
        try:
            self.setFlag(self.ItemSendsGeometryChanges)
        except AttributeError:
            pass
    
    def alternateColor( self ):
        """
        Returns the alternate color for this widget.
        
        :return     <QColor>
        """
        return self._alternateColor
    
    def alternateHighlightColor( self ):
        """
        Returns the alternate selection color for this item.
        
        :return     <QColor>
        """
        return self._alternateHighlightColor
    
    def alternateProgressColor( self ):
        """
        Returns the alternate progress color that will be used when drawing a
        progress bar for this item.
        
        :return     <QColor>
        """
        return self._alternateProgressColor
    
    def borderColor( self ):
        """
        Returns the border color that will be used when drawing this item.
        
        :return     <QColor>
        """
        return self._borderColor
    
    def borderRadius( self ):
        """
        Returns the border radius for this item.
        
        :return     <int>
        """
        return self._borderRadius
    
    def color( self ):
        """
        Returns the color for this widget.
        
        :return     <QColor>
        """
        return self._color
    
    def highlightColor( self ):
        """
        Returns the primary color used for highlighting this view item.
        
        :return     <QColor>
        """
        return self._highlightColor
    
    def isSyncing( self ):
        """
        Return whether or not this item is syncing.
        
        :return     <bool>
        """
        return self._syncing
    
    def itemChange( self, change, value ):
        """
        Overloads the base QGraphicsItem itemChange method to block user ability
        to move along the y-axis.
        
        :param      change      <int>
        :param      value       <variant>
        
        :return     <variant>
        """
        # only operate when it is a visible, geometric change
        if not (self.isVisible() and change == self.ItemPositionChange):
            return super(XGanttViewItem, self).itemChange( change, value )
        
        if self.isSyncing():
            return super(XGanttViewItem, self).itemChange(change, value)
        
        scene = self.scene()
        # only operate when we have a scene
        if not scene:
            return super(XNode, self).itemChange( change, value )
        
        point = value.toPointF()
        point.setY(self.pos().y())
        
        # create the return value
        new_value = wrapVariant(point)
        
        # call the base method to operate on the new point
        return super(XGanttViewItem, self).itemChange(change, new_value)
    
    def itemStyle(self):
        """
        Returns the style that this item will be rendered as.
        
        :return     <XGanttWidgetItem.ItemStyle>
        """
        item = self.treeItem()
        if item:
            return item.itemStyle()
        return 0
    
    def mouseReleaseEvent(self, event):
        """
        Overloads the mouse release event to apply the current changes.
        
        :param      event | <QEvent>
        """
        super(XGanttViewItem, self).mouseReleaseEvent(event)
        
        if not self.flags() & self.ItemIsMovable:
            return
        
        # force the x position to snap to the nearest date
        scene = self.scene()
        
        if scene:
            gantt  = scene.ganttWidget()
            curr_x = self.pos().x() + gantt.cellWidth() / 2.0
            new_x  = curr_x - curr_x % gantt.cellWidth()
            self.setPos(new_x, self.pos().y())
        
        # look for date based times
        gantt = self.scene().ganttWidget()
        
        # determine hour/minute information
        if gantt.timescale() in (gantt.Timescale.Minute,
                                 gantt.Timescale.Hour,
                                 gantt.Timescale.Day):
            dstart = self.scene().datetimeAt(self.pos().x())
            dend = self.scene().datetimeAt(self.pos().x() + self.rect().width())
            dend.addSecs(-60)
        else:
            dstart = self.scene().dateAt(self.pos().x())
            dend   = self.scene().dateAt(self.pos().x() + self.rect().width())
            dend   = dend.addDays(-1)
        
        item = self._treeItem()
        if item:
            item.viewChanged(dstart, dend)
        
    def padding( self ):
        """
        Returns the top and bottom padding for this item.
        
        :return     <int>
        """
        return self._padding
    
    def paint( self, painter, option, widget ):
        """
        Paints this item to the system.
        
        :param      painter | <QPainter>
                    option  | <QStyleOptionGraphicItem>
                    widget  | <QWidget>
        """
        style       = self.itemStyle()
        ItemStyle   = self.treeItem().ItemStyle
        
        if ( style == ItemStyle.Group ):
            self.paintGroup( painter )
        
        elif ( style == ItemStyle.Milestone ):
            self.paintMilestone( painter )
        
        else:
            self.paintNormal( painter )
    
    def paintGroup( self, painter ):
        """
        Paints this item as the group look.
        
        :param      painter | <QPainter>
        """
        # generate the rect
        rect    = self.rect()
        
        padding = self.padding()
        gantt   = self.scene().ganttWidget()
        cell_w  = gantt.cellWidth()
        cell_h  = gantt.cellHeight()
        
        x       = 0
        y       = self.padding()
        w       = rect.width()
        h       = rect.height() - (padding + 1)
        
        # grab the color options
        color       = self.color()
        alt_color   = self.alternateColor()
        
        if ( self.isSelected() ):
            color       = self.highlightColor()
            alt_color   = self.alternateHighlightColor()
        
        # create the background brush
        gradient = QLinearGradient()
        gradient.setStart(0, 0)
        gradient.setFinalStop(0, h)
        
        gradient.setColorAt(0,   color)
        gradient.setColorAt(0.8, alt_color)
        gradient.setColorAt(1,   color)
        
        painter.setPen(self.borderColor())
        painter.setBrush(QBrush(gradient))
        
        pen = painter.pen()
        pen.setWidthF(0.5)
        painter.setPen(pen)
        painter.setRenderHint( painter.Antialiasing )
        
        path = QPainterPath()
        path.moveTo(x - cell_w / 4.0, y)
        path.lineTo(w + cell_w / 4.0, y)
        path.lineTo(w + cell_w / 4.0, y + h / 2.0)
        path.lineTo(w, h)
        path.lineTo(w - cell_w / 4.0, y + h / 2.0)
        path.lineTo(x + cell_w / 4.0, y + h / 2.0)
        path.lineTo(x, h)
        path.lineTo(x - cell_w / 4.0, y + h / 2.0)
        path.lineTo(x - cell_w / 4.0, y)
        
        painter.drawPath(path)
        
        # create the progress brush
        if ( self.showProgress() ):
            gradient = QLinearGradient()
            gradient.setStart(0, 0)
            gradient.setFinalStop(0, h)
            gradient.setColorAt(0, self.progressColor())
            gradient.setColorAt(0.8, self.alternateProgressColor())
            gradient.setColorAt(1, self.progressColor())
            
            prog_w = (w - 4) * (self._percentComplete/100.0)
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(gradient))
            painter.drawRect(x, y, prog_w, y + h / 2.0)
        
        # draw the text on this item
        if ( self.text() ):
            painter.setPen(self.textColor())
            painter.drawText(x, y, w, h, Qt.AlignCenter, self.text())
    
    def paintMilestone( self, painter ):
        """
        Paints this item as the milestone look.
        
        :param      painter | <QPainter>
        """
        # generate the rect
        rect    = self.rect()
        
        padding = self.padding()
        gantt   = self.scene().ganttWidget()
        cell_w  = gantt.cellWidth()
        cell_h  = gantt.cellHeight()
        
        x       = rect.width() - cell_w
        y       = self.padding()
        w       = cell_w
        h       = rect.height() - padding - 2
        
        # grab the color options
        color       = self.color()
        alt_color   = self.alternateColor()
        
        if ( self.isSelected() ):
            color       = self.highlightColor()
            alt_color   = self.alternateHighlightColor()
        
        # create the background brush
        gradient = QLinearGradient()
        gradient.setStart(0, 0)
        gradient.setFinalStop(0, h)
        
        gradient.setColorAt(0,   color)
        gradient.setColorAt(0.8, alt_color)
        gradient.setColorAt(1,   color)
        
        painter.setPen(self.borderColor())
        painter.setBrush(QBrush(gradient))
        
        pen = painter.pen()
        pen.setWidthF(0.5)
        painter.setPen(pen)
        painter.setRenderHint( painter.Antialiasing )
        
        path = QPainterPath()
        path.moveTo(x - cell_w / 3.0, y + h / 2.0)
        path.lineTo(x, y)
        path.lineTo(x + cell_w / 3.0, y + h / 2.0)
        path.lineTo(x, y + h)
        path.lineTo(x - cell_w / 3.0, y + h / 2.0)
        
        painter.drawPath(path)
        
    def paintNormal( self, painter ):
        """
        Paints this item as the normal look.
        
        :param      painter | <QPainter>
        """
        # generate the rect
        rect    = self.rect()
        
        x       = 0
        y       = self.padding()
        w       = rect.width()
        h       = rect.height() - (2 * self.padding()) - 1
        radius  = self.borderRadius()
        
        # grab the color options
        color       = self.color()
        alt_color   = self.alternateColor()
        
        if ( self.isSelected() ):
            color       = self.highlightColor()
            alt_color   = self.alternateHighlightColor()
        
        # create the background brush
        gradient = QLinearGradient()
        gradient.setStart(0, 0)
        gradient.setFinalStop(0, h)
        
        gradient.setColorAt(0,   color)
        gradient.setColorAt(0.8, alt_color)
        gradient.setColorAt(1,   color)
        painter.setPen(self.borderColor())
        
        if ( radius ):
            painter.setRenderHint(painter.Antialiasing)
            pen = painter.pen()
            pen.setWidthF(0.5)
            painter.setPen(pen)
        
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(x, y, w, h, radius, radius)
        
        # create the progress brush
        if ( self.showProgress() ):
            gradient = QLinearGradient()
            gradient.setStart(0, 0)
            gradient.setFinalStop(0, h)
            gradient.setColorAt(0, self.progressColor())
            gradient.setColorAt(0.8, self.alternateProgressColor())
            gradient.setColorAt(1, self.progressColor())
            
            prog_w = (w - 4) * (self._percentComplete/100.0)
            radius -= 2
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(x + 2, y + 2, prog_w, h - 4, radius, radius)
        
        # draw the text on this item
        if ( self.text() ):
            painter.setPen(self.textColor())
            painter.drawText(x, y, w, h, Qt.AlignCenter, self.text())
    
    def percentComplete( self ):
        """
        Returns the percent complete that this item is in.
        
        :return     <int>
        """
        return self._percentComplete
    
    def progressColor( self ):
        """
        Returns the color that will be displayed with the progress bar for this
        widget.
        
        :return     <QColor>
        """
        return self._progressColor
    
    def setAlternateColor( self, color ):
        """
        Sets the alternate color for this widget to the inputed color.
        
        :param      color | <QColor>
        """
        self._alternateColor = QColor(color)
    
    def setAlternateProgressColor( self, color ):
        """
        Sets the alternate progress color that will be used when drawing a
        progress bar for this item.
        
        :return     <QColor>
        """
        self._alternateProgressColor = QColor(color)
    
    def setAlternateHighlightColor( self, color ):
        """
        Sets the alternate selection color for this item to the inputed color.
        
        :param      color | <QColor>
        """
        self._alternateHighlightColor = QColor(color)
    
    def setBorderRadius( self, radius ):
        """
        Sets the radius that will be used for this item to the inputed radius.
        
        :param      radius | <int>
        """
        self._borderRadius = radius
    
    def setColor( self, color ):
        """
        Sets the color for this widget.
        
        :param      color | <QColor> || <str>
        """
        self._color = QColor(color)
        self.setAlternateColor(self._color.darker(110))
    
    def setHighlightColor( self, color ):
        """
        Sets the primary color used for highlighting this item.
        
        :param      color | <QColor>
        """
        self._highlightColor = QColor(color)
        self.setAlternateHighlightColor(self._highlightColor.darker(110))
    
    def setPadding( self, padding ):
        """
        Sets the padding that will be used to pad the top and bottom for this
        item.
        
        :param      padding | <int>
        """
        self._padding = padding
    
    def setPercentComplete( self, percent ):
        """
        Sets the completion percentage for this item to the inputed amount.
        
        :param      percent | <int>
        """
        self._percentComplete = percent
    
    def setProgressColor( self, color ):
        """
        Sets the color that for the progress bar for this item.
        
        :param      color | <QColor>
        """
        self._progressColor = QColor(color)
        self.setAlternateProgressColor(self._progressColor.darker(110))
    
    def setShowProgress( self, state ):
        """
        Sets whether or not the progress information should be displayed.
        
        :param      state | <bool>
        """
        self._showProgress = state
    
    def setSyncing( self, state ):
        """
        Sets whether or not this item is syncing.
        
        :param      state | <bool>
        """
        self._syncing = state
    
    def setText( self, text ):
        """
        Sets the text for this item.
        
        :param      text | <str>
        """
        self._text = text
    
    def setTextColor( self, color ):
        """
        Sets the color that will be used for this widget's text.
        
        :param      color | <QColor> || <str>
        """
        self._textColor = QColor(color)
    
    def showProgress( self ):
        """
        Returns whether or not the progress should be displayed for this item.
        
        :return     <bool>
        """
        return self._showProgress
    
    def text( self ):
        """
        Returns the text for this widget.
        
        :return     <str>
        """
        return self._text
    
    def textColor( self ):
        """
        Returns the text color that will be used for this item's text.
        
        :return     <QColor>
        """
        return self._textColor
    
    def treeItem( self ):
        """
        Returns the tree item that is linked with this view item.
        
        :return     <XGanttWidgetItem>
        """
        return self._treeItem()