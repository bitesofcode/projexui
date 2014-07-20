#!/usr/bin/python

""" Defines a gantt chart widget for use in scheduling applications. """

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

from projexui.qt import Signal
from projexui.qt.QtCore   import QDate,\
                                 QSize,\
                                 QDateTime,\
                                 QTime,\
                                 Qt,\
                                 QPoint

from projexui.qt.QtGui    import QWidget,\
                                 QPen,\
                                 QBrush,\
                                 QPalette,\
                                 QColor,\
                                 QApplication,\
                                 QTreeWidgetItem,\
                                 QGraphicsItem

from projex.enum import enum

import projexui

from projexui.qt import unwrapVariant, wrapVariant
from projexui.widgets.xganttwidget.xganttscene   import XGanttScene

class XGanttWidget(QWidget):
    dateRangeChanged = Signal()
    itemMenuRequested = Signal(QTreeWidgetItem, QPoint)
    viewMenuRequested = Signal(QGraphicsItem, QPoint)
    treeMenuRequested = Signal(QTreeWidgetItem, QPoint)
    
    Timescale = enum('Minute', 'Hour', 'Day', 'Week', 'Month', 'Year')
    
    def __init__( self, parent = None ):
        super(XGanttWidget, self).__init__( parent )
        
        # load the user interface
        projexui.loadUi(__file__, self)
        
        # define custom properties
        self._backend               = None
        self._dateStart             = QDate.currentDate().addMonths(-2)
        self._dateEnd               = QDate.currentDate().addMonths(2)
        self._timeStart             = QTime(0, 0, 0)
        self._timeEnd               = QTime(23, 59, 59)
        self._alternatingRowColors  = False
        self._cellWidth             = 20
        self._cellHeight            = 20
        self._first                 = True
        self._dateFormat            = 'M/d/yy'
        self._timescale             = XGanttWidget.Timescale.Month
        self._scrolling             = False
        self._dirty                 = False
        
        # setup the palette colors
        palette = self.palette()
        color   = palette.color(palette.Base)
        
        self._gridPen           = QPen(color.darker(115))
        self._brush             = QBrush(color)
        self._alternateBrush    = QBrush(color.darker(105))
        
        weekendColor            = color.darker(108)
        self._weekendBrush      = QBrush(weekendColor)
        
        # setup the columns for the tree
        self.setColumns(['Name', 'Start', 'End', 'Calendar Days', 'Work Days'])
        
        header = self.uiGanttTREE.header()
        header.setFixedHeight(self._cellHeight * 2)
        headerItem = self.uiGanttTREE.headerItem()
        headerItem.setSizeHint(0, QSize(80, header.height()))
        
        # initialize the tree widget
        self.uiGanttTREE.setShowGrid(False)
        self.uiGanttTREE.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.uiGanttTREE.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.uiGanttTREE.setVerticalScrollMode(self.uiGanttTREE.ScrollPerPixel)
        self.uiGanttTREE.setResizeToContentsInteractive(True)
        self.uiGanttTREE.setEditable(True)
        self.uiGanttTREE.resize(500, 20)
        self.uiGanttTREE.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # initialize the view widget
        self.uiGanttVIEW.setDragMode( self.uiGanttVIEW.RubberBandDrag )
        self.uiGanttVIEW.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.uiGanttVIEW.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.uiGanttVIEW.setScene(XGanttScene(self))
        self.uiGanttVIEW.installEventFilter(self)
        self.uiGanttVIEW.horizontalScrollBar().setValue(50)
        self.uiGanttVIEW.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # create connections
        self.uiGanttTREE.itemExpanded.connect(self.syncView)
        self.uiGanttTREE.itemCollapsed.connect(self.syncView)
        
        # connect scrollbars
        tree_bar = self.uiGanttTREE.verticalScrollBar()
        view_bar = self.uiGanttVIEW.verticalScrollBar()
        
        tree_bar.rangeChanged.connect(self._updateViewRect)
        tree_bar.valueChanged.connect(self._scrollView)
        view_bar.valueChanged.connect(self._scrollTree)
        
        # connect selection
        self.uiGanttTREE.itemSelectionChanged.connect(self._selectView)
        self.uiGanttVIEW.scene().selectionChanged.connect(self._selectTree)
        self.uiGanttTREE.itemChanged.connect(self.updateItemData)
        self.uiGanttTREE.customContextMenuRequested.connect(self.requestTreeMenu)
        self.uiGanttVIEW.customContextMenuRequested.connect(self.requestViewMenu)
    
    def _scrollTree( self, value ):
        """
        Updates the tree view scrolling to the inputed value.
        
        :param      value | <int>
        """
        if self._scrolling:
            return
        
        tree_bar = self.uiGanttTREE.verticalScrollBar()
        self._scrolling = True
        tree_bar.setValue(value)
        self._scrolling = False
        
    def _scrollView( self, value ):
        """
        Updates the gantt view scrolling to the inputed value.
        
        :param      value | <int>
        """
        if self._scrolling:
            return
        
        view_bar = self.uiGanttVIEW.verticalScrollBar()
        self._scrolling = True
        view_bar.setValue(value)
        self._scrolling = False
    
    def _selectTree( self ):
        """
        Matches the tree selection to the views selection.
        """
        self.uiGanttTREE.blockSignals(True)
        self.uiGanttTREE.clearSelection()
        for item in self.uiGanttVIEW.scene().selectedItems():
            item.treeItem().setSelected(True)
        self.uiGanttTREE.blockSignals(False)
    
    def _selectView( self ):
        """
        Matches the view selection to the trees selection.
        """
        scene = self.uiGanttVIEW.scene()
        scene.blockSignals(True)
        scene.clearSelection()
        for item in self.uiGanttTREE.selectedItems():
            item.viewItem().setSelected(True)
        scene.blockSignals(False)
        
        curr_item = self.uiGanttTREE.currentItem()
        vitem = curr_item.viewItem()
        
        if vitem:
            self.uiGanttVIEW.centerOn(vitem)
    
    def _updateViewRect( self ):
        """
        Updates the view rect to match the current tree value.
        """
        if not self.updatesEnabled():
            return
        
        header_h    = self._cellHeight * 2
        rect        = self.uiGanttVIEW.scene().sceneRect()
        sbar_max    = self.uiGanttTREE.verticalScrollBar().maximum()
        sbar_max   += self.uiGanttTREE.viewport().height() + header_h
        widget_max  = self.uiGanttVIEW.height()
        widget_max -= (self.uiGanttVIEW.horizontalScrollBar().height() + 10)
        
        rect.setHeight(max(widget_max, sbar_max))
        self.uiGanttVIEW.scene().setSceneRect(rect)
    
    def addTopLevelItem(self, item):
        """
        Adds the inputed item to the gantt widget.
        
        :param      item | <XGanttWidgetItem>
        """
        vitem = item.viewItem()
        
        self.treeWidget().addTopLevelItem(item)
        self.viewWidget().scene().addItem(vitem)
        
        item._viewItem = weakref.ref(vitem)
        
        if self.updatesEnabled():
            try:
                item.sync(recursive=True)
            except AttributeError:
                pass
        
    def alternateBrush( self ):
        """
        Returns the alternate brush to be used for the grid view.
        
        :return     <QBrush>
        """
        return self._alternateBrush
    
    def alternatingRowColors( self ):
        """
        Returns whether or not this widget should show alternating row colors.
        
        :return     <bool>
        """
        return self._alternatingRowColors

    def blockSignals(self, state):
        """
        Sets whether or not updates will be enabled.
        
        :param      state | <bool>
        """
        super(XGanttWidget, self).blockSignals(state)
        self.treeWidget().blockSignals(state)
        self.viewWidget().blockSignals(state)

    def brush( self ):
        """
        Returns the background brush to be used for the grid view.
        
        :return     <QBrush>
        """
        return self._brush
    
    def centerOnDateTime(self, dtime):
        """
        Centers the view on a given datetime for the gantt widget.
        
        :param      dtime | <QDateTime>
        """
        view = self.uiGanttVIEW
        scene = view.scene()
        point = view.mapToScene(0, 0)
        x = scene.datetimeXPos(dtime)
        y = point.y()
        view.centerOn(x, y)
    
    def cellHeight( self ):
        """
        Returns the height for the cells in this gantt's views.
        
        :return     <int>
        """
        return self._cellHeight
    
    def cellWidth( self ):
        """
        Returns the width for the cells in this gantt's views.
        
        :return     <int>
        """
        return self._cellWidth
    
    def clear( self ):
        """
        Clears all the gantt widget items for this widget.
        """
        self.uiGanttTREE.clear()
        self.uiGanttVIEW.scene().clear()
    
    def columns( self ):
        """
        Returns a list of the columns being used in the treewidget of this gantt
        chart.
        
        :return     [<str>, ..]
        """
        return self.treeWidget().columns()
    
    def currentDateTime(self):
        """
        Returns the current date time for this widget.
        
        :return     <datetime.datetime>
        """
        view = self.uiGanttVIEW
        scene = view.scene()
        point = view.mapToScene(0, 0)
        return scene.datetimeAt(point.x())
    
    def dateEnd( self ):
        """
        Returns the date end for this date range of this gantt widget.
        
        :return     <QDate>
        """
        return self._dateEnd
    
    def dateFormat( self ):
        """
        Returns the date format that will be used when rendering items in the
        view.
        
        :return     <str>
        """
        return self._dateFormat
    
    def dateTimeEnd(self):
        """
        Returns the end date time for this gantt chart.
        
        :return     <QDateTime>
        """
        return QDateTime(self.dateEnd(), self.timeEnd())
    
    def dateTimeStart(self):
        """
        Returns the start date time for this gantt chart.
        
        :return     <QDateTime>
        """
        return QDateTime(self.dateStart(), self.timeStart())
    
    def dateStart( self ):
        """
        Returns the date start for the date range of this gantt widget.
        
        :return     <QDate>
        """
        return self._dateStart
    
    def emitDateRangeChanged( self ):
        """
        Emits the date range changed signal provided signals aren't being
        blocked.
        """
        if not self.signalsBlocked():
            self.dateRangeChanged.emit()
    
    def gridPen( self ):
        """
        Returns the pen that this widget uses to draw in the view.
        
        :return     <QPen>
        """
        return self._gridPen
    
    def indexOfTopLevelItem( self, item ):
        """
        Returns the index for the inputed item from the tree.
        
        :return     <int>
        """
        return self.treeWidget().indexOfTopLevelItem(item)
    
    def insertTopLevelItem( self, index, item ):
        """
        Inserts the inputed item at the given index in the tree.
        
        :param      index   | <int>
                    item    | <XGanttWidgetItem>
        """
        self.treeWidget().insertTopLevelItem(index, item)
        
        if self.updatesEnabled():
            try:
                item.sync(recursive = True)
            except AttributeError:
                pass

    def rebuild(self):
        self.uiGanttVIEW.scene().rebuild()

    def requestTreeMenu(self, point):
        """
        Emits the itemMenuRequested and treeMenuRequested signals
        for the given item.
        
        :param      point | <QPoint>
        """
        item = self.uiGanttTREE.itemAt(point)
        if item:
            glbl_pos = self.uiGanttTREE.viewport().mapToGlobal(point)
            self.treeMenuRequested.emit(item, glbl_pos)
            self.itemMenuRequested.emit(item, glbl_pos)

    def requestViewMenu(self, point):
        """
        Emits the itemMenuRequested and viewMenuRequested signals
        for the given item.
        
        :param      point | <QPoint>
        """
        vitem = self.uiGanttVIEW.itemAt(point)
        if vitem:
            glbl_pos = self.uiGanttVIEW.mapToGlobal(point)
            item = vitem.treeItem()
            self.viewMenuRequested.emit(vitem, glbl_pos)
            self.itemMenuRequested.emit(item, glbl_pos)

    def setAlternateBrush( self, brush ):
        """
        Sets the alternating brush used for this widget to the inputed brush.
        
        :param      brush | <QBrush> || <QColor>
        """
        self._alternateBrush = QBrush(brush)
    
    def setAlternatingRowColors( self, state ):
        """
        Sets the alternating row colors state for this widget.
        
        :param      state | <bool>
        """
        self._alternatingRowColors = state
        
        self.treeWidget().setAlternatingRowColors(state)
    
    def setBrush( self, brush ):
        """
        Sets the main background brush used for this widget to the inputed
        brush.
        
        :param      brush | <QBrush> || <QColor>
        """
        self._brush = QBrush(brush)
    
    def setCellHeight( self, cellHeight ):
        """
        Sets the height for the cells in this gantt's views.
        
        :param      cellHeight | <int>
        """
        self._cellHeight = cellHeight
    
    def setCellWidth( self, cellWidth ):
        """
        Sets the width for the cells in this gantt's views.
        
        :param      cellWidth | <int>
        """
        self._cellWidth = cellWidth
    
    def setColumns( self, columns ):
        """
        Sets the columns for this gantt widget's tree to the inputed list of
        columns.
        
        :param      columns | {<str>, ..]
        """
        self.treeWidget().setColumns(columns)
        item = self.treeWidget().headerItem()
        for i in range(item.columnCount()):
            item.setTextAlignment(i, Qt.AlignBottom | Qt.AlignHCenter)
    
    def setDateEnd( self, dateEnd ):
        """
        Sets the end date for the range of this gantt widget.
        
        :param      dateEnd | <QDate>
        """
        self._dateEnd = dateEnd
        self.emitDateRangeChanged()
    
    def setDateFormat( self, format ):
        """
        Sets the date format that will be used when rendering in the views.
        
        :return     <str>
        """
        return self._dateFormat
    
    def setDateStart( self, dateStart ):
        """
        Sets the start date for the range of this gantt widget.
        
        :param      dateStart | <QDate>
        """
        self._dateStart = dateStart
        self.emitDateRangeChanged()
    
    def setDateTimeEnd(self, dtime):
        """
        Sets the endiing date time for this gantt chart.
        
        :param      dtime | <QDateTime>
        """
        self._dateEnd = dtime.date()
        
        if self.timescale() in (self.Timescale.Minute, self.Timescale.Hour):
            self._timeEnd = dtime.time()
        else:
            self._timeEnd = QTime(23, 59, 59)
    
    def setDateTimeStart(self, dtime):
        """
        Sets the starting date time for this gantt chart.
        
        :param      dtime | <QDateTime>
        """
        self._dateStart = dtime.date()
        if self.timescale() in (self.Timescale.Minute, self.Timescale.Hour):
            self._timeStart = dtime.time()
        else:
            self._timeStart = QTime(0, 0, 0)
    
    def setCurrentDateTime(self, dtime):
        """
        Sets the current date time for this widget.
        
        :param      dtime | <datetime.datetime>
        """
        view = self.uiGanttVIEW
        scene = view.scene()
        point = view.mapToScene(0, 0)
        x = scene.datetimeXPos(dtime)
        y = point.y()
        view.ensureVisible(x, y, 1, 1)
    
    def setGridPen( self, pen ):
        """
        Sets the pen used to draw the grid lines for the view.
        
        :param      pen | <QPen> || <QColor>
        """
        self._gridPen = QPen(pen)
    
    def setTimescale( self, timescale ):
        """
        Sets the timescale value for this widget to the inputed value.
        
        :param      timescale | <XGanttWidget.Timescale>
        """
        self._timescale = timescale
        
        # show hour/minute scale
        if timescale == XGanttWidget.Timescale.Minute:
            self._cellWidth = 60 # (60 seconds)
            self._dateStart = QDate.currentDate()
            self._timeStart = QTime(0, 0, 0)
            
            self._dateEnd = QDate.currentDate()
            self._timeEnd = QTime(23, 59, 59)
            
        elif timescale == XGanttWidget.Timescale.Hour:
            self._cellWidth = 30 # (60 seconds / 2.0)
            
            self._dateStart = QDate.currentDate()
            self._timeStart = QTime(0, 0, 0)
            
            self._dateEnd = QDate.currentDate()
            self._timeEnd = QTime(23, 59, 59)
        
        # show day/hour scale
        elif timescale == XGanttWidget.Timescale.Day:
            self._cellWidth = 30 # (60 minutes / 2.0)
            
            self._dateStart = QDate.currentDate().addDays(-7)
            self._timeStart = QTime(0, 0, 0)
            
            self._dateEnd = QDate.currentDate().addDays(7)
            self._timeEnd = QTime(23, 59, 59)
    
    def setTimeEnd(self, time):
        """
        Sets the ending time for this gantt chart.
        
        :param      time | <QTime>
        """
        self._timeEnd = time
    
    def setTimeStart(self, time):
        """
        Sets the starting time for this gantt chart.
        
        :param      time | <QTime>
        """
        self._timeStart = time

    def setUpdatesEnabled(self, state):
        """
        Sets whether or not updates will be enabled.
        
        :param      state | <bool>
        """
        super(XGanttWidget, self).setUpdatesEnabled(state)
        self.treeWidget().setUpdatesEnabled(state)
        self.viewWidget().setUpdatesEnabled(state)
        
        if state:
            self._updateViewRect()
            for i in range(self.topLevelItemCount()):
                item = self.topLevelItem(i)
                try:
                    item.sync(recursive=True)
                except AttributeError:
                    continue

    def setWeekendBrush( self, brush ):
        """
        Sets the brush to be used when coloring weekend columns.
        
        :param      brush | <QBrush> || <QColor>
        """
        self._weekendBrush = QBrush(brush)
    
    def syncView(self):
        """
        Syncs all the items to the view.
        """
        if not self.updatesEnabled():
            return
        
        for item in self.topLevelItems():
            try:
                item.syncView(recursive=True)
            except AttributeError:
                continue

    def takeTopLevelItem( self, index ):
        """
        Removes the top level item at the inputed index from the widget.
        
        :param      index | <int>
        
        :return     <XGanttWidgetItem> || None
        """
        item = self.topLevelItem(index)
        if item:
            self.viewWidget().scene().removeItem(item.viewItem())
            self.treeWidget().takeTopLevelItem(index)
            
            return item
        return None
    
    def timescale( self ):
        """
        Returns the timescale that is being used for this widget.
        
        :return     <XGanttWidget.Timescale>
        """
        return self._timescale
    
    def timeEnd(self):
        """
        Returns the ending time for this gantt chart.  Default value
        will be QTime(0, 0, 0)
        
        :return     <QTime>
        """
        return self._timeEnd
    
    def timeStart(self):
        """
        Returns the starting time for this gantt chart.  Default value
        will be QTime(0, 0, 0)
        
        :return     <QTime>
        """
        return self._timeStart
    
    def topLevelItems(self):
        """
        Return the top level item generator.
        
        :return     <generator [<QTreeWidgetItem>, ..]>
        """
        return self.treeWidget().topLevelItems()
    
    def topLevelItem(self, index):
        """
        Returns the top level item at the inputed index.
        
        :return     <QTreeWidgetItem>
        """
        return self.treeWidget().topLevelItem(index)
    
    def topLevelItemCount(self):
        """
        Returns the number of top level items for this widget.
        
        :return     <int>
        """
        return self.treeWidget().topLevelItemCount()
    
    def treeWidget(self):
        """
        Returns the tree widget for this gantt widget.
        
        :return     <QTreeWidget>
        """
        return self.uiGanttTREE
    
    def updateItemData(self, item, index):
        """
        Updates the item information from the tree.
        
        :param      item    | <XGanttWidgetItem>
                    index   | <int>
        """
        from projexui.widgets.xganttwidget.xganttwidgetitem import XGanttWidgetItem
        if not isinstance(item, XGanttWidgetItem):
            return
        
        value = unwrapVariant(item.data(index, Qt.EditRole))
        
        if type(value) == QDateTime:
            value = value.date()
            item.setData(index, Qt.EditRole, wrapVariant(value))
        
        if type(value) == QDate:
            value = value.toPython()
        
        columnName = self.treeWidget().columnOf(index)
        item.setProperty(columnName, value)
        item.sync()
    
    def viewWidget( self ):
        """
        Returns the view widget for this gantt widget.
        
        :return     <QGraphicsView>
        """
        return self.uiGanttVIEW
    
    def weekendBrush( self ):
        """
        Returns the weekend brush to be used for coloring in weekends.
        
        :return     <QBrush>
        """
        return self._weekendBrush


