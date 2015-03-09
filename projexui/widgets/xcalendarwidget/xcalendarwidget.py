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

import weakref

from projexui.qt import Signal, Slot, PyObject
from projexui.qt.QtCore   import Qt,\
                                 QDate,\
                                 QDateTime

from projexui.qt.QtGui    import QGraphicsView

import projexui.resources
from projexui.widgets.xcalendarwidget.xcalendarscene import XCalendarScene
from projexui.widgets.xcalendarwidget.xcalendaritem  import XCalendarItem

class XCalendarWidget(QGraphicsView):
    """ """
    __designer_icon__ = projexui.resources.find('img/ui/calendar.png')
    
    Mode            = XCalendarScene.Mode
    TimelineScale   = XCalendarScene.TimelineScale
    
    calendarItemDoubleClicked   = Signal(PyObject)
    calendarItemClicked         = Signal(PyObject)
    currentDateChanged          = Signal(QDate)
    currentModeChanged          = Signal(int)
    dateClicked                 = Signal(QDate)
    dateDoubleClicked           = Signal(QDate)
    dateRangeChanged            = Signal(QDate, QDate)
    dateTimeClicked             = Signal(QDateTime)
    dateTimeDoubleClicked       = Signal(QDateTime)
    titleChanged                = Signal(str)
    
    def __getattr__( self, key ):
        """
        Maps the keys from the scene to this widget for convenience.
        
        :param      key | <str>
        """
        if ( hasattr(self.scene(), key) ):
            return getattr(self.scene(), key)
        
        raise AttributeError, key
    
    def __init__( self, parent = None ):
        super(XCalendarWidget, self).__init__( parent )
        
        # define custom properties
        self._dragDropFilterRef     = None
        
        # set default properties
        self.setScene(XCalendarScene(self))
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setDragMode(self.RubberBandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setAcceptDrops(True)
        
        # create connections
    
    def currentDate( self ):
        """
        Returns the current date displayed with this calendar widget.
        
        :return     <QDate>
        """
        return self.scene().currentDate()
    
    def currentMode( self ):
        """
        Returns what calendar mode this calendar is currently displaying.
        
        :return     <XCalendarWidget.Mode>
        """
        return self.scene().currentMode()
    
    def dragEnterEvent( self, event ):
        """
        Processes the drag drop event using the filter set by the \
        setDragDropFilter
        
        :param      event | <QDragEvent>
        """
        filt = self.dragDropFilter()
        if ( not filt ):
            super(XCalendarWidget, self).dragEnterEvent(event)
            return
        
        filt(self, event)
        
    def dragMoveEvent( self, event ):
        """
        Processes the drag drop event using the filter set by the \
        setDragDropFilter
        
        :param      event | <QDragEvent>
        """
        filt = self.dragDropFilter()
        if ( not filt ):
            super(XCalendarWidget, self).dragMoveEvent(event)
            return
        
        filt(self, event)
    
    def dragDropFilter( self ):
        """
        Returns a drag and drop filter method.  If set, the method should \
        accept 2 arguments: a QWidget and a drag/drop event and process it.
        
        :usage      |from projexui.qt.QtCore import QEvent
                    |
                    |class MyWidget(QWidget):
                    |   def __init__( self, parent ):
                    |       super(MyWidget, self).__init__(parent)
                    |       
                    |       self._tree = XCalendarWidget(self)
                    |       self._tree.setDragDropFilter(MyWidget.handleDragDrop)
                    |   
                    |   @staticmethod
                    |   def handleDragDrop(object, event):
                    |       if ( event.type() == QEvent.DragEnter ):
                    |           event.acceptProposedActions()
                    |       elif ( event.type() == QEvent.Drop ):
                    |           print 'dropping'
        
        :return     <function> || <method> || None
        """
        filt = None
        if ( self._dragDropFilterRef ):
            filt = self._dragDropFilterRef()
        
        if ( not filt ):
            self._dragDropFilterRef = None
        
        return filt
     
    def dropEvent( self, event ):
        """
        Processes the drag drop event using the filter set by the \
        setDragDropFilter
        
        :param      event | <QDropEvent>
        """
        filt = self.dragDropFilter()
        if ( not filt ):
            super(XCalendarWidget, self).dropEvent(event)
            return
        
        filt(self, event)
    
    @Slot()
    def gotoNext( self ):
        """
        Goes to the next date based on the current mode and date.
        """
        scene = self.scene()
        date  = scene.currentDate()
        
        # go forward a day
        if ( scene.currentMode() == scene.Mode.Day ):
            scene.setCurrentDate(date.addDays(1))
        
        # go forward a week
        elif ( scene.currentMode() == scene.Mode.Week ):
            scene.setCurrentDate(date.addDays(7))
        
        # go forward a month
        elif ( scene.currentMode() == scene.Mode.Month ):
            scene.setCurrentDate(date.addMonths(1))
    
    @Slot()
    def gotoPrevious( self ):
        """
        Goes to the previous date based on the current mode and date.
        """
        scene = self.scene()
        date  = scene.currentDate()
        
        # go back a day
        if ( scene.currentMode() == scene.Mode.Day ):
            scene.setCurrentDate(date.addDays(-1))
        
        # go back a week
        elif ( scene.currentMode() == scene.Mode.Week ):
            scene.setCurrentDate(date.addDays(-7))
        
        # go back a month
        elif ( scene.currentMode() == scene.Mode.Month ):
            scene.setCurrentDate(date.addMonths(-1))
    
    @Slot()
    def gotoToday( self ):
        """
        Goes to today as the current date.
        """
        self.scene().setCurrentDate(QDate.currentDate())
    
    def maximumDate( self ):
        """
        Returns the maximum date for this widget.  This value will be used \
        when in timeline mode to determine the end for the date range to \
        search for.
        
        :return     <QDate>
        """
        return self.scene().maximumDate()
    
    def minimumDate( self ):
        """
        Returns the minimum date for this widget.  This value will be used \
        when in timeline mode to determine the start for the date range to \
        search for.
        
        :return     <QDate>
        """
        return self.scene().minimumDate()
    
    def mousePressEvent( self, event ):
        """
        Handles the mouse press event.
        
        :param      event | <QMouseEvent>
        """
        scene_point = self.mapToScene(event.pos())
        date        = self.scene().dateAt(scene_point)
        date_time   = self.scene().dateTimeAt(scene_point)
        item        = self.scene().itemAt(scene_point)
        
        if ( not isinstance(item, XCalendarItem) ):
            item = None
        
        # checks to see if the signals are blocked
        if ( not self.signalsBlocked() ):
            if ( item ):
                self.calendarItemClicked.emit(item)
            
            elif ( date_time.isValid() ):
                self.dateTimeClicked.emit(date_time)
            
            elif ( date.isValid() ):
                self.dateClicked.emit(date)
        
        return super(XCalendarWidget, self).mousePressEvent(event)
    
    def mouseDoubleClickEvent( self, event ):
        """
        Handles the mouse double click event.
        
        :param      event | <QMouseEvent>
        """
        scene_point = self.mapToScene(event.pos())
        date        = self.scene().dateAt(scene_point)
        date_time   = self.scene().dateTimeAt(scene_point)
        item        = self.scene().itemAt(scene_point)
        
        if ( not isinstance(item, XCalendarItem) ):
            item = None
        
        # checks to see if the signals are blocked
        if ( not self.signalsBlocked() ):
            if ( item ):
                self.calendarItemDoubleClicked.emit(item)
            
            elif ( date_time.isValid() ):
                self.dateTimeDoubleClicked.emit(date_time)
            
            elif ( date.isValid() ):
                self.dateDoubleClicked.emit(date)
        
        return super(XCalendarWidget, self).mouseDoubleClickEvent(event)
    
    def resizeEvent( self, event ):
        super(XCalendarWidget, self).resizeEvent(event)
        
        self.scene().setSceneRect(0, 0, self.width() - 5, self.height() - 5)
    
    @Slot(QDate)
    def setCurrentDate( self, date ):
        """
        Sets the current date displayed by this calendar widget.
        
        :return     <QDate>
        """
        self.scene().setCurrentDate(date)
    
    @Slot(int)
    def setCurrentMode( self, mode ):
        """
        Sets the current mode that this calendar will be displayed in.
        
        :param      mode | <XCalendarWidget.Mode>
        """
        self.scene().setCurrentMode(mode)
        self.scene().setSceneRect(0, 0, self.width() - 5, self.height() - 5)
        if ( not self.signalsBlocked() ):
            self.currentModeChanged.emit(mode)
    
    def setDragDropFilter( self, ddFilter ):
        """
        Sets the drag drop filter for this widget.
        
        :warning    The dragdropfilter is stored as a weak-reference, so using \
                    mutable methods will not be stored well.  Things like \
                    instancemethods will not hold their pointer after they \
                    leave the scope that is being used.  Instead, use a \
                    classmethod or staticmethod to define the dragdropfilter.
        
        :param      ddFilter | <function> || <method> || None
        """
        if ( ddFilter ):
            self._dragDropFilterRef = weakref.ref(ddFilter)
        else:
            self._dragDropFilterRef = None
    
    def setMaximumDate( self, date ):
        """
        Sets the maximum date for this calendar widget to the inputed date.
        
        :param      date | <QDate>
        """
        self.scene().setMaximumDate(date)
    
    def setMinimumDate( self, date ):
        """
        Sets the minimum date for this calendar widget to the inputed date.
        
        :param      date | <QDate>
        """
        self.scene().setMinimumDate(date)
    
    def setTimelineScale( self, timelineScale ):
        """
        Sets the timeline scale that will be used when rendering a calendar in \
        timeline mode.
        
        :param      timelineScale | <XCalendarWidget.TimelineScale>
        """
        self.scene().setTimelineScale(timelineScale)
    
    def timelineScale( self ):
        """
        Returns the timeline scale that will be used when rendering a calendar \
        in timeline mode.
        
        :return     <XCalendarWidget.TimelineScale>
        """
        return self.scene().timelineScale()