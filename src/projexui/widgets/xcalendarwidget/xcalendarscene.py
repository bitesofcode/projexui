#!/usr/bin/python

""" 
Defines a calendar widget similar to the ones found in outlook or ical.
"""

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

#------------------------------------------------------------------------------

from projex.text import nativestring

from projexui.qt.QtCore   import Qt,\
                                 QDate, \
                                 QLine,\
                                 QRectF,\
                                 QDateTime,\
                                 QTime
                           
from projexui.qt.QtGui    import QGraphicsScene,\
                                 QPalette,\
                                 QCursor

from projex.enum import enum
from projexui.widgets.xcalendarwidget.xcalendaritem import XCalendarItem
from projexui.widgets.xpopupwidget import XPopupWidget

class XCalendarScene(QGraphicsScene):
    Mode          = enum('Day', 'Week', 'Month', 'Agenda')
    TimelineScale = enum('Day', 'Week', 'Month', 'Year')
    
    def __init__( self, parent = None ):
        super(XCalendarScene, self).__init__( parent )
        
        # define custom properties
        self._currentDate   = QDate.currentDate()
        self._currentMode   = XCalendarScene.Mode.Month
        self._timelineScale = XCalendarScene.TimelineScale.Week
        self._minimumDate   = QDate()
        self._maximumDate   = QDate()
        
        self._dateGrid              = {}
        self._dateTimeGrid          = {}
        self._buildData             = {}
        self._rebuildRequired       = False
        
        # set default properties
        
        # create connections
    
    def addCalendarItem( self ):
        """
        Adds a new calendar item to the scene.
        
        :return     <XCalendarItem>
        """
        item = XCalendarItem()
        self.addItem(item)
        return item
    
    def addItem( self, item ):
        """
        Adds the item to the scene and redraws the item.
        
        :param      item | <QGraphicsItem>
        """
        result = super(XCalendarScene, self).addItem(item)
        
        if ( isinstance(item, XCalendarItem) ):
            item.rebuild()
        
        return result
    
    def currentDate( self ):
        """
        Returns the current date displayed with this calendar widget.
        
        :return     <QDate>
        """
        return self._currentDate
    
    def currentMode( self ):
        """
        Returns what calendar mode this calendar is currently displaying.
        
        :return     <XCalendarScene.Mode>
        """
        return self._currentMode
    
    def dateAt( self, point ):
        """
        Returns the date at the given point.
        
        :param      point | <QPoint>
        """
        for date, data in self._dateGrid.items():
            if ( data[1].contains(point) ):
                return QDate.fromJulianDay(date)
        return QDate()
    
    def dateTimeAt( self, point ):
        """
        Returns the date time at the inputed point.
        
        :param      point | <QPoint>
        """
        for dtime, data in self._dateTimeGrid.items():
            if ( data[1].contains(point) ):
                return QDateTime.fromTime_t(dtime)
        return QDateTime()
    
    def dateRect( self, date ):
        """
        Returns the rect that is defined by the inputed date.
        
        :return     <QRectF>
        """
        data = self._dateGrid.get(date.toJulianDay())
        if ( data ):
            return QRectF(data[1])
        return QRectF()
    
    def dateTimeRect( self, dateTime ):
        """
        Returns the rect that is defined by the inputed date time.
        
        :return     <QRectF>
        """
        data = self._dateTimeGrid.get(dateTime.toTime_t())
        if ( data ):
            return QRectF(data[1])
        return QRectF()
    
    def drawBackground( self, painter, rect ):
        """
        Draws the background of the scene using painter.
        
        :param      painter | <QPainter>
                    rect    | <QRectF>
        """
        if ( self._rebuildRequired ):
            self.rebuild()
        
        super(XCalendarScene, self).drawBackground(painter, rect)
        
        palette = self.palette()
        
        # draw custom options
        if ( 'curr_date' in self._buildData ):
            clr = palette.color(QPalette.Highlight)
            clr.setAlpha(40)
            painter.setBrush(clr)
            painter.setPen(Qt.NoPen)
            painter.drawRect(self._buildData['curr_date'])
            painter.setBrush(Qt.NoBrush)
        
        if ( 'today' in self._buildData ):
            painter.setPen(Qt.NoPen)
            clr = palette.color(QPalette.AlternateBase)
            clr.setAlpha(120)
            painter.setBrush(clr)
            painter.drawRect(self._buildData['today'])
            painter.setBrush(Qt.NoBrush)
        
        # draw the grid
        painter.setPen(palette.color(QPalette.Mid))
        painter.drawLines(self._buildData.get('grid', []))
        
        # draw text fields
        painter.setPen(palette.color(QPalette.Text))
        for data in self._buildData.get('regular_text', []):
            painter.drawText(*data)
        
        # draw mid text fields
        painter.setPen(palette.color(QPalette.Mid))
        for data in self._buildData.get('mid_text', []):
            painter.drawText(*data)
    
    def helpEvent( self, event ):
        """
        Displays a tool tip for the given help event.
        
        :param      event | <QHelpEvent>
        """
        item  = self.itemAt(event.scenePos())
        if ( item and item and item.toolTip() ):
            parent = self.parent()
            rect   = item.path().boundingRect()
            point  = event.scenePos()
            point.setY(item.pos().y() + rect.bottom())
            
            point  = parent.mapFromScene(point)
            point  = parent.mapToGlobal(point)
            
            XPopupWidget.showToolTip(item.toolTip(),
                                     point = point,
                                     parent = parent)
            event.accept()
        else:
            super(XCalendarScene, self).helpEvent(event)
    
    def markForRebuild( self, state = True ):
        """
        Marks this scene as needing to be rebuild.
        
        :param      state | <bool>
        """
        self._rebuildRequired = state
        self.invalidate()
    
    def maximumDate( self ):
        """
        Returns the maximum date for this widget.  This value will be used \
        when in timeline mode to determine the end for the date range to \
        search for.
        
        :return     <QDate>
        """
        return self._maximumDate
    
    def mousePressEvent( self, event ):
        """
        Changes the current date to the clicked on date.
        
        :param      event | <QMousePressEvent>
        """
        XPopupWidget.hideToolTip()
        
        # update the current date
        self.setCurrentDate(self.dateAt(event.scenePos()))
        
        super(XCalendarScene, self).mousePressEvent(event)
    
    def minimumDate( self ):
        """
        Returns the minimum date for this widget.  This value will be used \
        when in timeline mode to determine the start for the date range to \
        search for.
        
        :return     <QDate>
        """
        return self._minimumDate
    
    def rebuild( self ):
        """
        Rebuilds the information for this scene.
        """
        self._buildData.clear()
        self._dateGrid.clear()
        self._dateTimeGrid.clear()
        
        curr_min = self._minimumDate
        curr_max = self._maximumDate
        
        self._maximumDate = QDate()
        self._minimumDate = QDate()
        
        self.markForRebuild(False)
        
        # rebuilds the month view
        if ( self.currentMode() == XCalendarScene.Mode.Month ):
            self.rebuildMonth()
        elif ( self.currentMode() in (XCalendarScene.Mode.Week,
                                      XCalendarScene.Mode.Day)):
            self.rebuildDays()
        
        # rebuild the items in the scene
        items = sorted(self.items())
        for item in items:
            item.setPos(0, 0)
            item.hide()
        
        for item in items:
            if ( isinstance(item, XCalendarItem) ):
                item.rebuild()
        
        if ( curr_min != self._minimumDate or curr_max != self._maximumDate ):
            parent = self.parent()
            if ( parent and not parent.signalsBlocked() ):
                parent.dateRangeChanged.emit(self._minimumDate, 
                                             self._maximumDate)
    
    def rebuildMonth( self ):
        """
        Rebuilds the month for this scene.
        """
        # make sure we start at 0 for sunday vs. 7 for sunday
        day_map     = dict([(i+1, i+1) for i in range(7)])
        day_map[7]  = 0
        
        today   = QDate.currentDate()
        curr    = self.currentDate()
        first   = QDate(curr.year(), curr.month(), 1)
        last    = QDate(curr.year(), curr.month(), curr.daysInMonth())
        first   = first.addDays(-day_map[first.dayOfWeek()])
        last    = last.addDays(6-day_map[last.dayOfWeek()])
        
        cols    = 7
        rows    = (first.daysTo(last) + 1) / cols
        
        hlines  = []
        vlines  = []
        
        padx    = 6
        pady    = 6
        header  = 24
        
        w       = self.width() - (2 * padx)
        h       = self.height() - (2 * pady)
        
        dw      = (w / cols) - 1
        dh      = ((h - header) / rows) - 1
        
        x0      = padx
        y0      = pady + header
        
        x       = x0
        y       = y0
        
        for row in range(rows + 1):
            hlines.append(QLine(x0, y, w, y))
            y += dh
        
        for col in range(cols + 1):
            vlines.append(QLine(x, y0, x, h))
            x += dw
        
        self._buildData['grid'] = hlines + vlines
        
        # draw the date fields
        date = first
        row  = 0
        col  = 0
        
        # draw the headers
        x = x0
        y = pady
        
        regular_text = []
        mid_text     = []
        self._buildData['regular_text'] = regular_text
        self._buildData['mid_text']     = mid_text
        
        for day in ('Sun', 'Mon','Tue','Wed','Thu','Fri','Sat'):
            regular_text.append((x + 5,
                                 y,
                                 dw,
                                 y0,
                                 Qt.AlignLeft | Qt.AlignVCenter,
                                 day))
            x += dw
        
        for i in range(first.daysTo(last) + 1):
            top    = (y0 + (row * dh))
            left   = (x0 + (col * dw))
            rect   = QRectF(left - 1, top, dw, dh)
            
            # mark the current date on the calendar
            if ( date == curr ):
                self._buildData['curr_date'] = rect
            
            # mark today's date on the calendar
            elif ( date == today ):
                self._buildData['today'] = rect
            
            # determine how to draw the calendar
            format = 'd'
            if ( date.day() == 1 ):
                format = 'MMM d'
            
            # determine the color to draw the text
            if ( date.month() == curr.month() ):
                text = regular_text
            else:
                text = mid_text
            
            # draw the text
            text.append((left + 2,
                         top + 2,
                         dw - 4,
                         dh - 4,
                         Qt.AlignTop | Qt.AlignLeft,
                         date.toString(format)))
            
            # update the limits
            if ( not i ):
                self._minimumDate = date
            self._maximumDate = date
            
            self._dateGrid[date.toJulianDay()] = ((row, col), rect)
            if ( col == (cols - 1) ):
                row += 1
                col = 0
            else:
                col += 1
                
            date = date.addDays(1)
    
    def rebuildDays( self ):
        """
        Rebuilds the interface as a week display.
        """
        time = QTime(0, 0, 0)
        hour = True
        
        x = 6
        y = 6 + 24
        
        w = self.width() - 12 - 25
        
        dh         = 48
        indent     = 58
        text_data  = []
        
        vlines      = []
        hlines      = [QLine(x, y, w, y)]
        time_grids  = []
        
        for i in range(48):
            if ( hour ):
                hlines.append(QLine(x, y, w, y))
                text_data.append((x,
                                  y + 6, 
                                  indent - 6, 
                                  dh, 
                                  Qt.AlignRight | Qt.AlignTop,
                                  time.toString('hap')))
            else:
                hlines.append(QLine(x + indent, y, w, y))
            
            time_grids.append((time, y, dh / 2))
            
            # move onto the next line
            hour = not hour
            time = time.addSecs(30 * 60)
            y += dh / 2
        
        hlines.append(QLine(x, y, w, y))
        
        h = y
        y = 6 + 24
        
        # load the grid
        vlines.append(QLine(x, y, x, h))
        vlines.append(QLine(x + indent, y, x + indent, h))
        vlines.append(QLine(w, y, w, h))
        
        today     = QDate.currentDate()
        curr_date = self.currentDate()
        
        # load the days
        if ( self.currentMode() == XCalendarScene.Mode.Week ):
            date = self.currentDate()
            day_of_week = date.dayOfWeek()
            if ( day_of_week == 7 ):
                day_of_week = 0
            
            min_date = date.addDays(-day_of_week)
            max_date = date.addDays(6-day_of_week)
            
            self._minimumDate = min_date
            self._maximumDate = max_date
            
            dw    = (w - (x + indent)) / 7.0
            vx    = x + indent
            date  = min_date
            
            for i in range(7):
                vlines.append(QLine(vx, y, vx, h))
                
                text_data.append((vx + 6,
                                  6,
                                  dw,
                                  24,
                                  Qt.AlignCenter,
                                  date.toString('ddd MM/dd')))
                
                self._dateGrid[date.toJulianDay()] = ((0, i),
                                                      QRectF(vx, y, dw, h - y))
                
                # create the date grid for date time options
                for r, data in enumerate(time_grids):
                    time, ty, th = data
                    dtime = QDateTime(date, time)
                    key = dtime.toTime_t()
                    self._dateTimeGrid[key] = ((r, i), QRectF(vx, ty, dw, th))
                
                if ( date == curr_date ):
                    self._buildData['curr_date'] = QRectF(vx, y, dw, h - 29)
                elif ( date == today ):
                    self._buildData['today'] = QRectF(vx, y, dw, h - 29)
                
                date = date.addDays(1)
                vx += dw
        
        # load a single day
        else:
            date = self.currentDate()
            
            self._maximumDate = date
            self._minimumDate = date
            
            text_data.append((x + indent,
                              6,
                              w,
                              24,
                              Qt.AlignCenter,
                              date.toString('ddd MM/dd')))
            
            self._dateGrid[date.toJulianDay()] = ((0, 0), 
                                                  QRectF(x, y, w - x, h - y))
            
            # create the date grid for date time options
            for r, data in enumerate(time_grids):
                time, ty, th = data
                dtime = QDateTime(date, time)
                key = dtime.toTime_t()
                rect = QRectF(x + indent, ty, w - (x + indent), th)
                self._dateTimeGrid[key] = ((r, 0), rect)
        
        self._buildData['grid'] = hlines + vlines
        self._buildData['regular_text'] = text_data
        
        rect = self.sceneRect()
        rect.setHeight(h + 6)
        
        super(XCalendarScene, self).setSceneRect(rect)
    
    def setCurrentDate( self, date ):
        """
        Sets the current date displayed by this calendar widget.
        
        :return     <QDate>
        """
        if ( date == self._currentDate or not date.isValid() ):
            return
        
        self._currentDate = date
        self.markForRebuild()
        
        parent = self.parent()
        if ( not parent.signalsBlocked() ):
            parent.currentDateChanged.emit(date)
            parent.titleChanged.emit(self.title())
    
    def setCurrentMode( self, mode ):
        """
        Sets the current mode that this calendar will be displayed in.
        
        :param      mode | <XCalendarScene.Mode>
        """
        self._currentMode = mode
        self.markForRebuild()
    
    def setSceneRect( self, *args ):
        """
        Updates the scene rect for this item.
        
        :param      *args
        """
        h = self.height()
        super(XCalendarScene, self).setSceneRect(*args)
        if ( self.currentMode() != XCalendarScene.Mode.Month ):
            rect = self.sceneRect()
            rect.setHeight(h)
            super(XCalendarScene, self).setSceneRect(rect)
        
        self.markForRebuild()
    
    def setTimelineScale( self, timelineScale ):
        """
        Sets the timeline scale that will be used when rendering a calendar in \
        timeline mode.
        
        :param      timelineScale | <XCalendarScene.TimelineScale>
        """
        self._timelineScale = timelineScale
    
    def title( self ):
        """
        Returns the title for this scene based on its information.
        
        :return     <str>
        """
        if ( self.currentMode() == XCalendarScene.Mode.Day ):
            return self.currentDate().toString('dddd, MMMM dd, yyyy')
        
        elif ( self.currentMode() == XCalendarScene.Mode.Week ):
            title = nativestring(self.minimumDate().toString('dddd, MMMM dd'))
            title += ' - '
            title += nativestring(self.maximumDate().toString('dddd, MMMM dd, yyyy'))
            return title
        
        elif ( self.currentMode() == XCalendarScene.Mode.Month ):
            return self.currentDate().toString('MMMM yyyy')
        
        else:
            return ''
    
    def timelineScale( self ):
        """
        Returns the timeline scale that will be used when rendering a calendar \
        in timeline mode.
        
        :return     <XCalendarScene.TimelineScale>
        """
        return self._timelineScale