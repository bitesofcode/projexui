#!/usr/bin/python

""" Custom backend for managing gantt widget items within the view. """

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

from projex.text import nativestring

from projexui.qt.QtCore   import QDate,\
                                 QTime,\
                                 QDateTime,\
                                 QLine,\
                                 QRect,\
                                 QRectF,\
                                 Qt
                           
from projexui.qt.QtGui    import QGraphicsScene,\
                                 QLinearGradient,\
                                 QBrush,\
                                 QColor,\
                                 QPixmap

from projexui.xpainter import XPainter

class XGanttRenderOptions(object):
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

class XGanttScene(QGraphicsScene):
    def __init__(self, ganttWidget):
        super(XGanttScene, self).__init__(ganttWidget)
        
        # setup custom properties
        self._ganttWidget       = ganttWidget
        self._hlines            = []
        self._vlines            = []
        self._alternateRects    = []
        self._weekendRects      = []
        self._topLabels         = []
        self._labels            = []
        self._dirty             = True
        self._tiles   = {}
        
        # create connections
        ganttWidget.dateRangeChanged.connect(self.setDirty)
    
    def dateAt(self, x):
        """
        Returns the date at the inputed x position.
        
        :return     <QDate>
        """
        gantt       = self.ganttWidget()
        dstart      = gantt.dateStart()
        days        = int(x / float(gantt.cellWidth()))
        
        return dstart.addDays(days)
    
    def datetimeAt(self, x):
        """
        Returns the datetime at the inputed x position.
        
        :return     <QDateTime>
        """
        gantt = self.ganttWidget()
        dstart = gantt.dateTimeStart()
        distance = int(x / float(gantt.cellWidth()))
        
        # calculate the time for a minute
        if scale == gantt.Timescale.Minute:
            return dstart.addSecs(distance)
        
        # calculate the time for an hour
        elif scale == gantt.Timescale.Hour:
            return dstart.addSecs(distance * 2.0)

        # calculate the time for a day
        elif scale == gantt.Timescale.Day:
            dstart = QDateTime(gantt.dateStart(), QTime(0, 0, 0))
            return dstart.addSecs(distance * (60 * 2.0))
        
        # calculate the time off the date only
        else:
            date = self.dateAt(x)
            return QDateTime(date, QTime(0, 0, 0))
    
    def dateXPos(self, date):
        """
        Returns the x-position for the inputed date.
        
        :return     <int>
        """
        gantt = self.ganttWidget()
        distance = gantt.dateStart().daysTo(date)
        return gantt.cellWidth() * distance
    
    def datetimeXPos(self, dtime):
        """
        Returns the x-position for the inputed date time.
        
        :return     <float>
        """
        gantt = self.ganttWidget()
        scale = gantt.timescale()
        
        # calculate the distance for a minute
        if scale == gantt.Timescale.Minute:
            dstart = gantt.dateTimeStart()
            secs = dstart.secsTo(dtime)
            return secs
        
        # calculate the distance for an hour
        elif scale == gantt.Timescale.Hour:
           dstart = gantt.dateTimeStart()
           secs = dstart.secsTo(dtime)
           return secs / 2.0
        
        # calculate the distance for a day
        elif scale == gantt.Timescale.Day:
            dstart = QDateTime(gantt.dateStart(), QTime(0, 0, 0))
            secs = dstart.secsTo(dtime)
            return (secs / (60.0 * 2.0))
        
        # calculate the distance off the date only
        else:
            return self.dateXPos(dtime.date())
    
    def drawForeground(self, painter, rect):
        """
        Draws the foreground for this scene.
        
        :param      painter | <QPainter>
                    rect    | <QRect>
        """
        gantt  = self.ganttWidget()
        header = gantt.treeWidget().header()
        width  = self.sceneRect().width()
        height = header.height()
        
        for tile_rect, tile in self._tiles:
            painter.drawPixmap(tile_rect.x(), rect.top(), tile)
        
        palette = self.palette()
        textColor = palette.color(palette.Button).darker(125)
        painter.setPen(textColor)
        painter.drawLine(0, rect.top() + height, width, rect.top() + height)
    
    def rebuildTiles(self):
        # create the foreground pixmap
        gantt  = self.ganttWidget()
        header = gantt.treeWidget().header()
        width  = self.sceneRect().width()
        height = header.height()
        
        # create the main color
        palette     = gantt.palette()
        color       = palette.color(palette.Button)
        textColor   = palette.color(palette.ButtonText)
        borderColor = color.darker(140)
        text_align  = Qt.AlignBottom | Qt.AlignHCenter
        
        # create the gradient
        gradient = QLinearGradient()
        gradient.setStart(0, 0)
        gradient.setFinalStop(0, height)
        gradient.setColorAt(0, color)
        gradient.setColorAt(1, color.darker(120))
        
        # generate the tiles
        tiles = []
        painters = []
        for rect, label in self._topLabels:
            tile_rect = QRectF(rect.x(), 0, rect.width(), height)
            pixmap = QPixmap(rect.width(), height)
            
            with XPainter(pixmap) as painter:
                painter.setBrush(QBrush(gradient))
                painter.drawRect(tile_rect)
                
                rx = 0
                ry = 0
                rw = rect.width()
                rh = rect.height()
                
                painter.setPen(borderColor)
                painter.drawRect(rx, ry, rw, rh)
                
                painter.setPen(textColor)
                painter.drawText(rx, ry, rw, rh - 2, text_align, label)
                
                tiles.append((tile_rect, pixmap))
                painters.append((tile_rect, pixmap, painter))
        
        # add bottom labels
        for rect, label in self._labels:
            for tile_rect, tile, painter in painters:
                if tile_rect.x() <= rect.x() and \
                   rect.right() <= tile_rect.right():
                    rx = rect.x() - tile_rect.x()
                    ry = rect.y()
                    rw = rect.width()
                    rh = rect.height()
                    
                    with painter:
                        painter.setPen(borderColor)
                        painter.drawRect(rx, ry, rw, rh)
                        
                        painter.setPen(textColor)
                        painter.drawText(rx, ry, rw, rh - 2, text_align, label)

        self._tiles = tiles
    
    def drawBackground(self, painter, rect):
        """
        Draws the background for this scene.
        
        :param      painter | <QPainter>
                    rect    | <QRect>
        """
        if self._dirty:
            self.rebuild()
        
        # draw the alternating rects
        gantt   = self.ganttWidget()
        
        # draw the alternating rects
        painter.setPen(Qt.NoPen)
        painter.setBrush(gantt.alternateBrush())
        for rect in self._alternateRects:
            painter.drawRect(rect)
        
        # draw the weekends
        painter.setBrush(gantt.weekendBrush())
        for rect in self._weekendRects:
            painter.drawRect(rect)
        
        # draw the default background
        painter.setPen(gantt.gridPen())
        painter.drawLines(self._hlines + self._vlines)
    
    def ganttWidget(self):
        """
        Returns the gantt view that this scene is linked to.
        
        :return     <XGanttWidget>
        """
        return self._ganttWidget
    
    def isDirty(self):
        """
        Returns if this gantt widget requires a redraw.
        
        :return     <bool>
        """
        return self._dirty
    
    def rebuild(self):
        """
        Rebuilds the scene based on the current settings.
        
        :param      start | <QDate>
                    end   | <QDate>
        """
        gantt = self.ganttWidget()
        scale = gantt.timescale()
        rect = self.sceneRect()
        header = gantt.treeWidget().header()
        
        # define the rendering options
        options = {}
        options['start']         = gantt.dateStart()
        options['end']           = gantt.dateEnd()
        options['cell_width']    = gantt.cellWidth()
        options['cell_height']   = gantt.cellHeight()
        options['rect']          = rect
        options['height']        = rect.height()
        
        options['header_height'] = header.height()
        if not header.isVisible():
            options['header_height'] = 0
        
        opt = XGanttRenderOptions(**options)
        
        # rebuild the minute timescale
        if scale in (gantt.Timescale.Minute, gantt.Timescale.Hour):
            opt.start = gantt.dateTimeStart()
            opt.end = gantt.dateTimeEnd()
            
            self.rebuildHour(opt)
        
        # rebuild the day timescale
        elif scale == gantt.Timescale.Day:
            self.rebuildDay(opt)
        
        # rebuild the week timescale
        elif scale == gantt.Timescale.Week:
            self.rebuildWeek(opt)
        
        self.rebuildTiles()

    def rebuildDay(self, opt):
        """
        Rebuilds the scale for the day mode.
        
        :param      opt | <XGanttRenderOptions>
        """
        self._labels            = []
        self._hlines            = []
        self._vlines            = []
        self._weekendRects      = []
        self._alternateRects    = []
        self._topLabels         = []
        
        top_format = 'dddd MMMM dd'
        label_format = 'ha'
        increment = 60 # hour
        
        # generate vertical lines
        x           = 0
        i           = 0
        half        = opt.header_height / 2.0
        curr        = QDateTime(opt.start, QTime(0, 0, 0))
        end         = QDateTime(opt.end, QTime(23, 0, 0))
        top_label   = opt.start.toString(top_format)
        top_rect    = QRect(0, 0, 0, half)
        alt_rect    = None
        
        while curr <= end:
            # update the top rect
            new_top_label = curr.toString(top_format)
            if new_top_label != top_label:
                top_rect.setRight(x)
                self._topLabels.append((top_rect, top_label))
                top_rect  = QRect(x, 0, 0, half)
                top_label = new_top_label
                
                if alt_rect is not None:
                    alt_rect.setRight(x)
                    self._alternateRects.append(alt_rect)
                    alt_rect = None
                else:
                    alt_rect = QRect(x, 0, 0, opt.height)
            
            # create the line
            self._hlines.append(QLine(x, 0, x, opt.height))
            
            # create the header label/rect
            label = nativestring(curr.toString(label_format))[:-1]
            rect  = QRect(x, half, opt.cell_width, half)
            self._labels.append((rect, label))
            
            # increment the dates
            curr = curr.addSecs(increment * 60)
            x += opt.cell_width
            i += 1
        
        # update the top rect
        top_rect.setRight(x)
        top_label = opt.end.toString(top_format)
        self._topLabels.append((top_rect, top_label))
        
        if alt_rect is not None:
            alt_rect.setRight(x)
            self._alternateRects.append(alt_rect)
        
        # resize the width to match the last date range
        new_width = x
        self.setSceneRect(0, 0, new_width, opt.height)
        
        # generate horizontal lines
        y       = 0
        h       = opt.height
        width   = new_width
        
        while y < h:
            self._vlines.append(QLine(0, y, width, y))
            y += opt.cell_height
        
        # clear the dirty flag
        self._dirty = False

    def rebuildHour(self, opt):
        """
        Rebuilds the scale for the minute mode.
        
        :param      opt | <XGanttRenderOptions>
        """
        self._labels            = []
        self._hlines            = []
        self._vlines            = []
        self._weekendRects      = []
        self._alternateRects    = []
        self._topLabels         = []
        
        top_format = 'MMM d h:00a'
        gantt = self.ganttWidget()
        if gantt.timescale() == gantt.Timescale.Minute:
            label_format = 'h:mma'
        else:
            label_format = 'mm'
        
        increment = 1 # minute
        
        # generate vertical lines
        x           = 0
        i           = 0
        half        = opt.header_height / 2.0
        curr        = opt.start
        top_label   = opt.start.toString(top_format)
        top_rect    = QRect(0, 0, 0, half)
        alt_rect    = None
        
        while curr <= opt.end:
            # update the top rect
            new_top_label = curr.toString(top_format)
            if new_top_label != top_label:
                top_rect.setRight(x)
                self._topLabels.append((top_rect, top_label))
                top_rect  = QRect(x, 0, 0, half)
                top_label = new_top_label
                
                if alt_rect is not None:
                    alt_rect.setRight(x)
                    self._alternateRects.append(alt_rect)
                    alt_rect = None
                else:
                    alt_rect = QRect(x, 0, 0, opt.height)
            
            # create the line
            self._hlines.append(QLine(x, 0, x, opt.height))
            
            # create the header label/rect
            label = nativestring(curr.toString(label_format))
            rect  = QRect(x, half, opt.cell_width, half)
            self._labels.append((rect, label))
            
            # increment the dates
            curr = curr.addSecs(increment * 60)
            x += opt.cell_width
            i += 1
        
        # update the top rect
        top_rect.setRight(x)
        top_label = opt.end.toString(top_format)
        self._topLabels.append((top_rect, top_label))
        
        if alt_rect is not None:
            alt_rect.setRight(x)
            self._alternateRects.append(alt_rect)
        
        # resize the width to match the last date range
        new_width = x
        self.setSceneRect(0, 0, new_width, opt.height)
        
        # generate horizontal lines
        y       = 0
        h       = opt.height
        width   = new_width
        
        while y < h:
            self._vlines.append(QLine(0, y, width, y))
            y += opt.cell_height
        
        # clear the dirty flag
        self._dirty = False

    def rebuildWeek(self, opt):
        """
        Rebuilds the scale for the week mode.
        
        :param      opt | <XOrbRenderOptions>
        """
        self._labels            = []
        self._hlines            = []
        self._vlines            = []
        self._weekendRects      = []
        self._alternateRects    = []
        self._topLabels         = []
        
        top_format = 'MMM'
        label_format = 'd'
        increment = 1     # days
        
        # generate vertical lines
        x           = 0
        i           = 0
        half        = opt.header_height / 2.0
        curr        = opt.start
        top_label   = opt.start.toString(top_format)
        top_rect    = QRect(0, 0, 0, half)
        alt_rect    = None
        
        while curr <= opt.end:
            # update the month rect
            new_top_label = curr.toString(top_format)
            if new_top_label != top_label:
                top_rect.setRight(x)
                self._topLabels.append((top_rect, top_label))
                top_rect  = QRect(x, 0, 0, half)
                top_label = new_top_label
                
                if alt_rect is not None:
                    alt_rect.setRight(x)
                    self._alternateRects.append(alt_rect)
                    alt_rect = None
                else:
                    alt_rect = QRect(x, 0, 0, opt.height)
            
            # create the line
            self._hlines.append(QLine(x, 0, x, opt.height))
            
            # create the header label/rect
            label = nativestring(curr.toString(label_format))
            rect  = QRect(x, half, opt.cell_width, half)
            self._labels.append((rect, label))
            
            # store weekend rectangles
            if curr.dayOfWeek() in (6, 7):
                rect = QRect(x, 0, opt.cell_width, opt.height)
                self._weekendRects.append(rect)
            
            # increment the dates
            curr = curr.addDays(increment)
            x += opt.cell_width
            i += 1
        
        # update the month rect
        top_rect.setRight(x)
        top_label = opt.end.toString(top_format)
        self._topLabels.append((top_rect, top_label))
        
        if alt_rect is not None:
            alt_rect.setRight(x)
            self._alternateRects.append(alt_rect)
        
        # resize the width to match the last date range
        new_width = x
        self.setSceneRect(0, 0, new_width, opt.height)
        
        # generate horizontal lines
        y       = 0
        h       = opt.height
        width   = new_width
        
        while y < h:
            self._vlines.append(QLine(0, y, width, y))
            y += opt.cell_height
        
        # clear the dirty flag
        self._dirty = False
    
    def setDayWidth(self, width):
        """
        Sets the day width that will be used for drawing this gantt widget.
        
        :param      width | <int>
        """
        self._dayWidth = width
        
        start = self.ganttWidget().dateStart()
        end = self.ganttWidget().dateEnd()
        
        self._dirty = True
    
    def setDirty(self, state=True):
        """
        Sets the dirty state for this scene.  When the scene is dirty, it will
        be rebuilt on the next draw.
        
        :param      state | <bool>
        """
        self._dirty = state
    
    def setSceneRect(self, *args):
        """
        Overloads the set rect method to signal that the scene needs to be 
        rebuilt.
        
        :param      args | <arg variant>
        """
        curr = self.sceneRect()
        
        super(XGanttScene, self).setSceneRect(*args)
        
        if curr != QRectF(*args):
            self._dirty = True


