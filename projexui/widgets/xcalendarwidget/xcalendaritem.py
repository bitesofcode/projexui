""" Defines the base calendar item that will be used when drawing calendar 
    items """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software, LLC'
__license__         = 'LGPL'

__maintainer__      = 'Projex Software, LLC'
__email__           = 'team@projexsoftware.com'

from projex.text import nativestring

from projexui.qt.QtCore   import QDate,\
                                 QTime,\
                                 QDateTime,\
                                 QRectF,\
                                 Qt

from projexui.qt.QtGui    import QGraphicsPathItem,\
                                 QPainterPath,\
                                 QColor

from projexui.widgets.xpopupwidget import XPopupWidget
from projex.enum import enum
import projex.dates

class XCalendarItem(QGraphicsPathItem):
    def __cmp__( self, other ):
        """
        Returns the comparison of this item with the other.
        
        :param      other | <variant>
        
        :return     -1 | 0 | 1
        """
        if ( not isinstance(other, XCalendarItem) ):
            return -1
        
        out = cmp(self.dateStart(), other.dateStart())
        if ( not out ):
            out = cmp(other.dateEnd(), self.dateEnd())
            if ( not out ):
                out = cmp(self.timeStart(), other.timeStart())
                if ( not out ):
                    out = cmp(other.timeEnd(), self.timeEnd())
                    if ( not out ):
                        out = cmp(self.title(), other.title())
        return out
    
    def __init__( self ):
        super(XCalendarItem, self).__init__()
        
        curr_dtime = QDateTime.currentDateTime()
        curr_date  = curr_dtime.date()
        curr_time  = curr_dtime.time()
        
        self.setFlags(self.flags() | self.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        
        # round to the nearest 15 minute segment
        curr_time = QTime(curr_time.hour(),
                          curr_time.minute() - curr_time.minute() % 30,
                          0)
        
        self._rebuildBlocked = False
        self._textData   = []
        
        self._customData        = {}
        self._textColor         = QColor('white')
        self._fillColor         = QColor('blue')
        self._borderColor       = QColor('blue')
        self._highlightColor    = QColor('blue')
        
        self._title             = 'No Title'
        self._description       = ''
        self._dateStart         = curr_date
        self._dateEnd           = curr_date
        self._timeStart         = curr_time
        self._timeEnd           = curr_time.addSecs(60 * 60)
        self._allDay            = True
        self._rebuildRequired   = False
        
        if ( QTime(23, 0, 0) <= self._timeStart ):
            self._timeEnd       = QTime(23, 59, 0)
        
        self.setColor('blue')
    
    def borderColor( self ):
        """
        Returns the border color for this item.
        
        :return     <QColor>
        """
        return self._borderColor
    
    def blockRebuild( self, state ):
        """
        Sets whether or not the rebuilding is blocked for this item.  This
        is useful to block when modifying multiple properties for the item
        at once to avoid unnecessary rebuilds.
        
        :param      state | <bool>
        """
        self._rebuildBlocked = state
    
    def color( self ):
        """
        Returns the color of this item.
        
        :return     <QColor>
        """
        return self.pen().color()
    
    def customData( self, key, default = None ):
        """
        Returns the custom data held on this item for the inputed key.
        
        :param      key     | <str>
                    default | <variant>
        """
        return self._customData.get(nativestring(key), default)
    
    def dateEnd( self ):
        """
        Returns the end date of this item.
        
        :return     <QDate>
        """
        return self._dateEnd
    
    def dateStart( self ):
        """
        Returns the start date of this item.
        
        :return     <QDate>
        """
        return self._dateStart
    
    def description( self ):
        """
        Returns the description for this item.
        
        :return     <str>
        """
        return self._description
    
    def duration( self ):
        """
        Returns the duration of this item.  This is calculated as the start
        date (beginning of the day) to the end date (end of the day).  So 
        if the start date and end date are the same day, then the duration will
        be 1 day.
        
        :return     <int>
        """
        return self._dateStart.daysTo(self._dateEnd) + 1
    
    def fillColor( self ):
        """
        Returns the fill color for this item.
        
        :return     <QColor>
        """
        return self._fillColor
    
    def highlightColor( self ):
        """
        Returns the highlight color for this item.
        
        :return     <QColor>
        """
        return self._highlightColor
    
    def isAllDay( self ):
        """
        Returns whether or not this item is an all day event.
        
        :return     <bool>
        """
        return self._allDay
    
    def length( self ):
        """
        Returns the length of time in minutes between the start and end times.
        
        :return     <int>
        """
        return (self._timeStart.secsTo(self._timeEnd)) / 60
    
    def markForRebuild( self, state = True ):
        """
        Sets the rebuild state for this item.
        
        :param      state | <bool>
        """
        self._rebuildRequired = state
        if ( state ):
            self.show()
            self.update()
    
    def paint( self, painter, option, widget ):
        """
        Paints this item on the painter.
        
        :param      painter | <QPainter>
                    option  | <QStyleOptionGraphicsItem>
                    widget  | <QWidget>
        """
        if ( self._rebuildRequired ):
            self.rebuild()
        
        # set the coloring options
        painter.setPen(self.borderColor())
        
        if ( self.isSelected() ):
            painter.setBrush(self.highlightColor())
        else:
            painter.setBrush(self.fillColor())
        
        hints = painter.renderHints()
        if ( not self.isAllDay() ):
            painter.setRenderHint(painter.Antialiasing)
            pen = painter.pen()
            pen.setWidthF(0.25)
            painter.setPen(pen)
        
        painter.drawPath(self.path())
        
        # draw the text in the different rect locations
        title = self.title()
        painter.setPen(self.textColor())
        for data in self._textData:
            painter.drawText(*data)
        
        painter.setRenderHints(hints)
    
    def rebuild( self ):
        """
        Rebuilds the current item in the scene.
        """
        self.markForRebuild(False)
        
        self._textData = []
        
        if ( self.rebuildBlocked() ):
            return
        
        scene = self.scene()
        if ( not scene ):
            return
        
        # rebuild a month look
        if ( scene.currentMode() == scene.Mode.Month ):
            self.rebuildMonth()
        elif ( scene.currentMode() in (scene.Mode.Day, scene.Mode.Week) ):
            self.rebuildDay()
    
    def rebuildDay( self ):
        """
        Rebuilds the current item in day mode.
        """
        scene = self.scene()
        if ( not scene ):
            return
        
        # calculate the base information
        start_date = self.dateStart()
        end_date   = self.dateEnd()
        min_date   = scene.minimumDate()
        max_date   = scene.maximumDate()
        
        # make sure our item is visible
        if ( not (min_date <= end_date and start_date <= max_date)):
            self.hide()
            self.setPath(QPainterPath())
            return
        
        # make sure we have valid range information
        if ( start_date < min_date ):
            start_date    = min_date
            start_inrange = False
        else:
            start_inrange = True
        
        if ( max_date < end_date ):
            end_date     = max_date
            end_inrange  = False
        else:
            end_inrange  = True
        
        # rebuild the path
        path = QPainterPath()
        self.setPos(0, 0)
        
        pad         = 2
        offset      = 18
        height      = 16
        
        # rebuild a timed item
        if ( not self.isAllDay() ):
            start_dtime = QDateTime(self.dateStart(), self.timeStart())
            end_dtime   = QDateTime(self.dateStart(), 
                                    self.timeEnd().addSecs(-30*60))
            
            start_rect  = scene.dateTimeRect(start_dtime)
            end_rect    = scene.dateTimeRect(end_dtime)
            
            left   = start_rect.left() + pad
            top    = start_rect.top() + pad
            right  = start_rect.right() - pad
            bottom = end_rect.bottom() - pad
            
            path.moveTo(left, top)
            path.lineTo(right, top)
            path.lineTo(right, bottom)
            path.lineTo(left, bottom)
            path.lineTo(left, top)
            
            data = (left + 6, 
                    top + 6, 
                    right - left - 12, 
                    bottom - top - 12,
                    Qt.AlignTop | Qt.AlignLeft,
                    '%s - %s\n(%s)' % (self.timeStart().toString('h:mmap')[:-1],
                                       self.timeEnd().toString('h:mmap'),
                                       self.title()))
            
            self._textData.append(data)
        
        self.setPath(path)
        self.show()
    
    def rebuildMonth( self ):
        """
        Rebuilds the current item in month mode.
        """
        scene = self.scene()
        if ( not scene ):
            return
        
        start_date  = self.dateStart()
        end_date    = self.dateEnd()
        min_date    = scene.minimumDate()
        max_date    = scene.maximumDate()
        
        # make sure our item is visible
        if ( not (min_date <= end_date and start_date <= max_date)):
            self.hide()
            self.setPath(QPainterPath())
            return
        
        # make sure we have valid range information
        if ( start_date < min_date ):
            start_date    = min_date
            start_inrange = False
        else:
            start_inrange = True
        
        if ( max_date < end_date ):
            end_date     = max_date
            end_inrange  = False
        else:
            end_inrange  = True
        
        start_rect = scene.dateRect(start_date)
        end_rect   = scene.dateRect(end_date)
        
        if ( not (start_rect.isValid() and end_rect.isValid()) ):
            self.hide()
            return
        
        # rebuild an all day path
        path = QPainterPath()
        self.setPos(0, 0)
        
        pad         = 2
        offset      = 18
        height      = 16
        
        min_left    = 10
        max_right   = scene.width() - 16
        delta_h     = start_rect.height()
        
        # draw the all day event
        if ( self.isAllDay() ):
            top   = start_rect.top()
            left  = start_rect.left() + 3
            first = start_inrange
            
            while ( top <= end_rect.top() ):
                sub_path  = QPainterPath()
                
                # calculate the end position
                if ( end_rect.top() - 2 <= top and end_inrange ):
                    at_end = True
                    right = end_rect.right() - pad
                else:
                    at_end = False
                    right = max_right
                
                if ( first ):
                    sub_path.moveTo(left, top + offset)
                    text_left = left + 4
                else:
                    sub_path.moveTo(left + height / 2, top + offset)
                    text_left = left + height / 2 + 2
                
                if ( at_end ):
                    sub_path.lineTo(right, top + offset)
                    sub_path.lineTo(right, top + offset + height)
                else:
                    sub_path.lineTo(right - height / 2, top + offset)
                    sub_path.lineTo(right, top + offset + height / 2)
                    sub_path.lineTo(right - height / 2, top + offset + height)
                
                if ( first ):
                    sub_path.lineTo(left, top + offset + height)
                    sub_path.lineTo(left, top + offset)
                else:
                    sub_path.lineTo(left + height / 2, top + offset + height)
                    sub_path.lineTo(left, top + offset + height / 2)
                    sub_path.lineTo(left + height / 2, top + offset)
                
                path.addPath(sub_path)
                
                data = (text_left,
                        top + offset + 1,
                        right,
                        height,
                        Qt.AlignLeft | Qt.AlignVCenter,
                        self.title())
                
                self._textData.append(data)
                
                left = min_left
                top += delta_h
                first = False
        else:
            text = '%s: (%s)' % (self.timeStart().toString('h:mm ap'), 
                                 self.title())
            
            font   = scene.font()
            left   = start_rect.left() + 2 * pad
            top    = start_rect.top() + offset
            
            path.addText(left, top + height / 2, font, text)
        
        # setup the path for this item
        self.setPath(path)
        self.show()
        
        # make sure there are no collisions
        while ( self.collidingItems() ):
            self.setPos(self.pos().x(), self.pos().y() + height + 2)
            
            # hide the item if out of the visible scope
            if ( delta_h - offset <= self.pos().y() + height ):
                self.hide()
                break
    
    def rebuildBlocked( self ):
        """
        Returns whether or not the rebuild mechanism is blocked.  Using the
        blockRebuild method can be useful to control when the item recalculates
        its scene dimensions.
        
        :return     <bool>
        """
        return self._rebuildBlocked
    
    def setBorderColor( self, color ):
        """
        Sets the color that will be used for the border of this item.
        
        :param      color | <QColor>
        """
        self._borderColor = QColor(color)
    
    def setColor( self, color ):
        """
        Convenience method to set the border, fill and highlight colors based
        on the inputed color.
        
        :param      color | <QColor>
        """
        # sets the border color as the full value
        self.setBorderColor(color)
        
        # set the highlight color as the color with a 140 % alpha
        clr = QColor(color)
        clr.setAlpha(150)
        self.setHighlightColor(clr)
        
        # set the fill color as the color with a 50 % alpha
        clr = QColor(color)
        clr.setAlpha(80)
        self.setFillColor(clr)
        
    def setCustomData( self, key, value ):
        """
        Stores the inputed value at the given key as custom data on this item.
        
        :param      key   | <str>
                    value | <variant>
        """
        self._customData[nativestring(key)] = value
    
    def setHighlightColor( self, color ):
        """
        Sets the color that will be used for the highlight of this item.
        
        :param      color | <QColor>
        """
        self._highlightColor = QColor(color)
    
    def setFillColor( self, color ):
        """
        Sets the color that will be used for the fill of this item.
        
        :param      color | <QColor>
        """
        self._fillColor = QColor(color)
    
    def setAllDay( self, state ):
        """
        Sets whether or not this item is an all day event.
        
        :param      state | <bool>
        """
        self._allDay = state
        self.markForRebuild()
    
    def setDateStart( self, dateStart ):
        """
        Sets the start date for this item.  This will automatically push the
        end date to match the duration for this item.  So if the item starts
        on 1/1/12 and ends on 1/2/12, and the start date is changed to 2/1/12,
        the end date will change to 2/2/12.  To affect the duration of the 
        item, use either setDuration, or setDateEnd.
        
        :param      dateStart | <QDate>
        """
        dateStart = QDate(dateStart)
        
        duration = self.duration()
        self._dateStart = dateStart
        self._dateEnd   = dateStart.addDays(duration - 1)
        self.markForRebuild()
    
    def setDateEnd( self, dateEnd ):
        """
        Sets the end date for this item.  This method will only affect the 
        start date if the end date is set to occur before its start, in which
        case it will set the start date as the same date.  (1 day duration)
        Otherwise, this method will scale the duration of the event.
        
        :param      dateEnd | <QDate>
        """
        dateEnd = QDate(dateEnd)
        
        if ( dateEnd < self._dateStart ):
            self._dateStart = dateEnd
        self._dateEnd = dateEnd
        self.markForRebuild()
    
    def setDescription( self, description ):
        """
        Sets the description for this item to the inputed description.
        
        :param      description | <str>
        """
        self._description = description
    
    def setDuration( self, duration ):
        """
        Changes the number of days that this item represents.  This will move
        the end date the appropriate number of days away from the start date.
        The duration is calculated as the 1 plus the number of days from start
        to end, so a duration of 1 will have the same start and end date.  The
        duration needs to be a value greater than 0.
        
        :param      duration | <int>
        """
        if ( duration <= 0 ):
            return
        
        self._dateEnd = self._dateStart.addDays(duration - 1)
        self.markForRebuild()
    
    def setLength( self, length ):
        """
        Sets the length of time between the start and end times.  The inputed
        number should represent the number of minutes in between them, and
        will be automatically rounded to the nearest 15 minutes.
        
        :param      length | <int>
        """
        self._timeEnd = self._timeStart.addSecs((length - length % 15) * 60)
        self.markForRebuild()
    
    def setTextColor( self, textColor ):
        """
        Sets the text color that will be used for this item to the inputed
        color.
        
        :param      textColor | <QColor>
        """
        self._textColor = QColor(textColor)
    
    def setTimeEnd( self, timeEnd ):
        """
        Sets the end time for this item.  This method will only affect the 
        start time if the end time is set to occur before its start, in which
        case it will set the start time as 60 minutes before.
        Otherwise, this method will scale the duration of the event.
        
        :param      timeEnd | <QTime>
        """
        timeEnd = QTime(timeEnd)
        
        if ( timeEnd < self._timeStart ):
            self._timeStart = timeEnd.addSecs(-60 * 60)
        self._timeEnd = timeEnd
        self.markForRebuild()
    
    def setTimeStart( self, timeStart ):
        """
        Sets the start time for this item.  This will automatically push the
        end time to match the length for this item.  So if the item starts
        at 11a and ends on 1p, and the start time is changed to 12p
        the end time will change to 2p.  To affect the length of the 
        item, use either setLength, or setTimeEnd.
        
        :param      timeStart | <QDate>
        """
        timeStart = QTime(timeStart)
        
        length = self.length() # in minutes
        self._timeStart = timeStart
        self._timeEnd   = timeStart.addSecs(length * 60)
        self.markForRebuild()
    
    def setTitle( self, title ):
        """
        Sets the title for this item to the inputed item.
        
        :param      title | <str>
        """
        self._title = title
        self.update()
    
    def textColor( self ):
        """
        Returns the text color that will be used for this item.
        
        :return     <QColor>
        """
        return self._textColor
    
    def timeEnd( self ):
        """
        Returns the ending time for this item.
        
        :return     <QTime>
        """
        return self._timeEnd
    
    def timeStart( self ):
        """
        Returns the start time for this item.
        
        :return     <QTime>
        """
        return self._timeStart
    
    def title( self ):
        """
        Returns the title for this item.
        
        :return     <str>
        """
        return self._title