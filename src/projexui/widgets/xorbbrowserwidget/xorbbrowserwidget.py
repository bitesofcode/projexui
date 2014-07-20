""" Defines a generic and reusable widget for searching for and browsing ORB
    database records. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software, LLC'
__license__         = 'LGPL'

__maintainer__      = 'Projex Software, LLC'
__email__           = 'team@projexsoftware.com'


#------------------------------------------------------------------------------

import math

from projex.text import nativestring

from projexui.qt import Signal, Property, PyObject
from projexui.qt.QtCore import QPoint,\
                               QSize,\
                               Qt

from projexui.qt.QtGui import QWidget,\
                              QListWidget,\
                              QLabel,\
                              QVBoxLayout,\
                              QListWidgetItem,\
                              QPalette,\
                              QTreeWidgetItem,\
                              QApplication

from orb import RecordSet, Query as Q

from projex.enum import enum
import projexui

from projexui.menus.xmenu import XMenu
from projexui.widgets.xorbtreewidget import XOrbRecordItem
from projexui.widgets.xorbbrowserwidget.xorbquerywidget import XOrbQueryWidget
from projexui.widgets.xorbbrowserwidget.xcardwidget import XAbstractCardWidget
from projexui.widgets.xorbbrowserwidget.xorbbrowserfactory \
                                        import XOrbBrowserFactory

#------------------------------------------------------------------------------

class GroupListWidgetItem(QListWidgetItem):
    def __init__( self, text, widget ):
        super(GroupListWidgetItem, self).__init__(text, widget)
        
        # set the text alignment
        self.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setFlags(Qt.ItemFlags(0))
        
        # update the font
        font = self.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 2)
        self.setFont(font)
        
        # update the size hint
        hint = QSize(widget.width() - 20, 22)
        self.setSizeHint(hint)

#------------------------------------------------------------------------------

class RecordListWidgetItem(QListWidgetItem):
    def __init__( self, thumbnail, text, record, widget ):
        super(RecordListWidgetItem, self).__init__(thumbnail, text, widget)
        
        # store the record
        self._record = record
    
    def record( self ):
        """
        Returns the record linked with this item.
        
        :return     <orb.Table>
        """
        return self._record

#------------------------------------------------------------------------------

class XOrbBrowserWidget(QWidget):
    """ """
    __designer_group__ = 'ProjexUI - ORB'
    
    currentRecordChanged = Signal()
    queryChanged         = Signal(PyObject) # orb.Query
    recordDoubleClicked  = Signal(PyObject) # orb.Table
    
    GroupByAdvancedKey = '__ADVANCED__'
    Mode = enum('Detail', 'Card', 'Thumbnail')
    
    def __init__( self, parent = None ):
        super(XOrbBrowserWidget, self).__init__( parent )
        
        # load the user interface
        projexui.loadUi(__file__, self)
        
        # define custom properties
        self._hint              = ''
        self._query             = Q()
        self._advancedGrouping  = []
        self._records           = RecordSet()
        self._groupBy           = XOrbBrowserWidget.GroupByAdvancedKey
        self._factory           = XOrbBrowserFactory()
        self._queryWidget       = XOrbQueryWidget(self, self._factory)
        self._thumbnailSize     = QSize(128, 128)
        
        # set default properties
        self.uiSearchTXT.addButton(self.uiQueryBTN)
        self.uiQueryBTN.setCentralWidget(self._queryWidget)
        self.uiThumbLIST.installEventFilter(self)
        
        self.uiQueryACT.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        self.uiQueryBTN.setDefaultAction(self.uiQueryACT)
        
        self.uiViewModeWGT.addAction(self.uiDetailsACT)
        self.uiViewModeWGT.addAction(self.uiCardACT)
        self.uiViewModeWGT.addAction(self.uiThumbnailACT)
        
        # create connections
        self.uiGroupOptionsBTN.clicked.connect(self.showGroupMenu)
        self.uiSearchTXT.returnPressed.connect(self.refresh)
        self.queryChanged.connect(self.refresh)
        self.uiGroupBTN.toggled.connect(self.refreshResults)
        
        self.uiDetailsACT.triggered.connect(self.setDetailMode)
        self.uiCardACT.triggered.connect(self.setCardMode)
        self.uiThumbnailACT.triggered.connect(self.setThumbnailMode)
        
        self.uiQueryBTN.popupAboutToShow.connect(self.prepareQuery)
        self.uiQueryBTN.popupAccepted.connect(self.acceptQuery)
        self.uiQueryBTN.popupReset.connect(self.resetQuery)
        
        self.uiRefreshBTN.clicked.connect(self.refresh)
        
        self.uiRecordsTREE.itemDoubleClicked.connect(self.handleDetailDblClick)
        self.uiRecordsTREE.currentItemChanged.connect(
                                                 self.emitCurrentRecordChanged)
        
        self.uiThumbLIST.itemDoubleClicked.connect(self.handleThumbDblClick)
        self.uiThumbLIST.currentItemChanged.connect(
                                                self.emitCurrentRecordChanged)
        
        self.uiCardTREE.itemDoubleClicked.connect(self.handleCardDblClick)
        self.uiCardTREE.currentItemChanged.connect(
                                                self.emitCurrentRecordChanged)
    
    def _loadCardGroup( self, groupName, records, parent = None ):
        if ( not groupName ):
            groupName = 'None'
        
        cards  = self.cardWidget()
        factory = self.factory()
        
        # create the group item
        group_item = QTreeWidgetItem(parent, [groupName])
        font = group_item.font(0)
        font.setBold(True)
        font.setPointSize(font.pointSize() + 2)
        group_item.setFont(0, font)
        group_item.setFlags(Qt.ItemIsEnabled)
        
        # load sub-groups
        if ( type(records) == dict ):
            for subgroup, records in sorted(records.items()):
                self._loadCardGroup(subgroup, records, group_item)
        else:
            for record in records:
                widget = factory.createCard(cards, record)
                if ( not widget ):
                    continue
                
                widget.adjustSize()
                
                # create the card item
                item = QTreeWidgetItem(group_item)
                item.setSizeHint(0, QSize(0, widget.height()))
                cards.setItemWidget(item, 0, widget)
        
        group_item.setExpanded(True)
    
    def _loadThumbnailGroup( self, groupName, records ):
        if ( not groupName ):
            groupName = 'None'
        
        widget  = self.thumbnailWidget()
        factory = self.factory()
        
        # create the group item
        GroupListWidgetItem(groupName, widget)
        
        # load sub-groups
        if ( type(records) == dict ):
            for subgroup, records in sorted(records.items()):
                self._loadThumbnailGroup(subgroup, records)
        else:
            # create the record items
            for record in records:
                thumbnail = factory.thumbnail(record)
                text      = factory.thumbnailText(record)
                RecordListWidgetItem(thumbnail, text, record, widget)
    
    def acceptQuery( self ):
        """
        Accepts the changes made from the query widget to the browser.
        """
        self.setQuery(self._queryWidget.query())
    
    def advancedGrouping( self ):
        """
        Returns the advanced grouping options for this widget.
        
        :return     [<str> group level, ..]
        """
        return ['[lastName::slice(0, 1)]']
        return self._advancedGrouping
    
    def cardWidget( self ):
        """
        Returns the card widget for this browser.
        
        :return     <QTreeWidget>
        """
        return self.uiCardTREE
    
    def controlsWidget( self ):
        """
        Returns the controls widget for this browser.  This is the widget that
        contains the various control mechanisms.
        
        :return     <QWidget>
        """
        return self._controlsWidget
    
    def currentGrouping( self ):
        """
        Returns the current grouping for this widget.
        
        :return     [<str> group level, ..]
        """
        groupBy = self.groupBy()
        if ( groupBy == XOrbBrowserWidget.GroupByAdvancedKey ):
            return self.advancedGrouping()
        else:
            table = self.tableType()
            if ( not table ):
                return []
            
            for column in table.schema().columns():
                if ( column.displayName() == groupBy ):
                    return [column.name()]
            
            return []
    
    def currentRecord( self ):
        """
        Returns the current record from this browser.
        
        :return     <orb.Table> || None
        """
        if ( self.currentMode() == XOrbBrowserWidget.Mode.Detail ):
            return self.detailWidget().currentRecord()
        
        elif ( self.currentMode() == XOrbBrowserWidget.Mode.Thumbnail ):
            item = self.thumbnailWidget().currentItem()
            if ( isinstance(item, RecordListWidgetItem) ):
                return item.record()
            return None
        
        else:
            item = self.uiCardTREE.currentItem()
            widget = self.uiCardTREE.itemWidget(item, 0)
            if ( isinstance(widget, XAbstractCardWidget) ):
                return widget.record()
            
            return None
    
    def currentMode( self ):
        """
        Returns the current mode for this widget.
        
        :return     <XOrbBrowserWidget.Mode>
        """
        if ( self.uiCardACT.isChecked() ):
            return XOrbBrowserWidget.Mode.Card
        elif ( self.uiDetailsACT.isChecked() ):
            return XOrbBrowserWidget.Mode.Detail
        else:
            return XOrbBrowserWidget.Mode.Thumbnail
    
    def detailWidget( self ):
        """
        Returns the tree widget used by this browser.
        
        :return     <XOrbTreeWidget>
        """
        return self.uiRecordsTREE
        
    def emitCurrentRecordChanged( self ):
        """
        Emits the current record changed signal.
        """
        if ( not self.signalsBlocked() ):
            self.currentRecordChanged.emit()
    
    def emitRecordDoubleClicked( self, record ):
        """
        Emits the record double clicked signal.
        
        :param      record | <orb.Table>
        """
        if ( not self.signalsBlocked() ):
            self.recordDoubleClicked.emit(record)
    
    def enabledModes( self ):
        """
        Returns the binary value of the enabled modes.
        
        :return     <XOrbBrowserWidget.Mode>
        """
        output = 0
        for i, action in enumerate((self.uiDetailsACT,
                                    self.uiCardACT,
                                    self.uiThumbnailACT)):
            if ( action.isEnabled() ):
                output |= int(math.pow(2, i))
        return output
    
    def eventFilter( self, object, event ):
        """
        Processes resize events on the thumbnail widget to update the group
        items to force a proper sizing.
        
        :param      object | <QObject>
                    event  | <QEvent>
        
        :return     <bool> | consumed
        """
        if ( event.type() == event.Resize and \
             self.currentMode() == XOrbBrowserWidget.Mode.Thumbnail and \
             self.isGroupingActive() ):
            size = QSize(event.size().width() - 20, 22)
            for row in range(object.count()):
                item = object.item(row)
                if ( isinstance(item, GroupListWidgetItem) ):
                    item.setSizeHint(size)
        return False
    
    def factory( self ):
        """
        Returns the factory assigned to this browser for generating card and
        thumbnail information for records.
        
        :return     <XOrbBrowserFactory>
        """
        return self._factory
    
    def groupBy( self ):
        """
        Returns the group by key for this widget.  If GroupByAdvancedKey
        is returned, then the advanced grouping options will be used.  
        Otherwise, a column will be used for grouping.
        
        :return     <str>
        """
        return self._groupBy
    
    def handleCardDblClick( self, item ):
        """
        Handles when a card item is double clicked on.
        
        :param      item | <QTreeWidgetItem>
        """
        widget = self.uiCardTREE.itemWidget(item, 0)
        if ( isinstance(widget, XAbstractCardWidget) ):
            self.emitRecordDoubleClicked(widget.record())
    
    def handleDetailDblClick( self, item ):
        """
        Handles when a detail item is double clicked on.
        
        :param      item | <QTreeWidgetItem>
        """
        if ( isinstance(item, XOrbRecordItem) ):
            self.emitRecordDoubleClicked(item.record())
    
    def handleThumbDblClick( self, item ):
        """
        Handles when a thumbnail item is double clicked on.
        
        :param      item | <QListWidgetItem>
        """
        if ( isinstance(item, RecordListWidgetItem) ):
            self.emitRecordDoubleClicked(item.record())
    
    def hint( self ):
        """
        Returns the hint for this widget.
        
        :return     <str>
        """
        return self._hint
    
    def isGroupingActive( self ):
        """
        Returns if the grouping is currently on or not.
        
        :return     <bool>
        """
        return self.uiGroupBTN.isChecked()
    
    def isModeEnabled( self, mode ):
        """
        Returns whether or not the inputed mode is enabled.
        
        :param      mode | <XOrbBrowserWidget.Mode>
        
        :return     <bool>
        """
        return (self.enabledModes() & mode) != 0
    
    def modeWidget( self ):
        """
        Returns the mode widget for this instance.
        
        :return     <projexui.widgets.xactiongroupwidget.XActionGroupWidget>
        """
        return self.uiViewModeWGT
    
    def prepareQuery( self ):
        """
        Prepares the popup widget with the query data.
        """
        self._queryWidget.setQuery(self.query())
    
    def query( self ):
        """
        Returns the fixed query that is assigned via programmatic means.
        
        :return     <orb.Query> || None
        """
        return self._query
    
    def queryWidget( self ):
        """
        Returns the query building widget.
        
        :return     <XOrbQueryWidget>
        """
        return self._queryWidget
    
    def records( self ):
        """
        Returns the record set for the current settings of this browser.
        
        :return     <orb.RecordSet>
        """
        if ( self.isGroupingActive() ):
            self._records.setGroupBy(self.currentGrouping())
        else:
            self._records.setGroupBy(None)
        return self._records
    
    def refresh( self ):
        """
        Refreshes the interface fully.
        """
        self.refreshRecords()
        self.refreshResults()
    
    def refreshRecords( self ):
        """
        Refreshes the records being loaded by this browser.
        """
        table_type = self.tableType()
        if ( not table_type ):
            self._records = RecordSet()
            return False
        
        search = nativestring(self.uiSearchTXT.text())
        
        query = self.query().copy()
        terms, search_query = Q.fromSearch(search)
        
        if ( search_query ):
            query &= search_query
        
        self._records = table_type.select(where = query).search(terms)
        return True
    
    def refreshResults( self ):
        """
        Joins together the queries from the fixed system, the search, and the
        query builder to generate a query for the browser to display.
        """
        if ( self.currentMode() == XOrbBrowserWidget.Mode.Detail ):
            self.refreshDetails()
        elif ( self.currentMode() == XOrbBrowserWidget.Mode.Card ):
            self.refreshCards()
        else:
            self.refreshThumbnails()
    
    def refreshCards( self ):
        """
        Refreshes the results for the cards view of the browser.
        """
        cards = self.cardWidget()
        factory = self.factory()
        
        self.setUpdatesEnabled(False)
        self.blockSignals(True)
        
        cards.setUpdatesEnabled(False)
        cards.blockSignals(True)
        
        cards.clear()
        QApplication.instance().processEvents()
        
        if ( self.isGroupingActive() ):
            grouping = self.records().grouped()
            for groupName, records in sorted(grouping.items()):
                self._loadCardGroup(groupName, records, cards)
            
        else:
            for record in self.records():
                widget = factory.createCard(cards, record)
                if ( not widget ):
                    continue
                
                widget.adjustSize()
                
                # create the card item
                item = QTreeWidgetItem(cards)
                item.setSizeHint(0, QSize(0, widget.height()))
                cards.setItemWidget(item, 0, widget)
        
        cards.setUpdatesEnabled(True)
        cards.blockSignals(False)
        
        self.setUpdatesEnabled(True)
        self.blockSignals(False)
    
    def refreshDetails( self ):
        """
        Refreshes the results for the details view of the browser.
        """
        # start off by filtering based on the group selection
        tree = self.uiRecordsTREE
        tree.blockSignals(True)
        tree.setRecordSet(self.records())
        tree.blockSignals(False)
    
    def refreshThumbnails( self ):
        """
        Refreshes the thumbnails view of the browser.
        """
        # clear existing items
        widget = self.thumbnailWidget()
        widget.setUpdatesEnabled(False)
        widget.blockSignals(True)
        
        widget.clear()
        widget.setIconSize(self.thumbnailSize())
        
        factory = self.factory()
        
        # load grouped thumbnails (only allow 1 level of grouping)
        if ( self.isGroupingActive() ):
            grouping = self.records().grouped()
            for groupName, records in sorted(grouping.items()):
                self._loadThumbnailGroup(groupName, records)
        
        # load ungrouped thumbnails
        else:
            # load the records into the thumbnail
            for record in self.records():
                thumbnail = factory.thumbnail(record)
                text      = factory.thumbnailText(record)
                RecordListWidgetItem(thumbnail, text, record, widget)
        
        widget.setUpdatesEnabled(True)
        widget.blockSignals(False)
    
    def resetQuery( self ):
        """
        Resets the popup query widget's query information
        """
        self._queryWidget.clear()
    
    def setCardMode( self ):
        """
        Sets the mode for this widget to the Card mode.
        """
        self.setCurrentMode(XOrbBrowserWidget.Mode.Card)
    
    def setCurrentMode( self, mode ):
        """
        Sets the current mode for this widget to the inputed mode.  This will
        check against the valid modes for this browser and return success.
        
        :param      mode | <XOrbBrowserWidget.Mode>
        
        :return     <bool> | success
        """
        if ( not self.isModeEnabled(mode) ):
            return False
        
        if ( mode == XOrbBrowserWidget.Mode.Detail ):
            self.uiModeSTACK.setCurrentIndex(0)
            self.uiDetailsACT.setChecked(True)
        elif ( mode == XOrbBrowserWidget.Mode.Card ):
            self.uiModeSTACK.setCurrentIndex(1)
            self.uiCardACT.setChecked(True)
        else:
            self.uiModeSTACK.setCurrentIndex(2)
            self.uiThumbnailACT.setChecked(True)
        
        self.refreshResults()
        
        return True
    
    def setCurrentRecord( self, record ):
        """
        Sets the current record for this browser to the inputed record.
        
        :param      record | <orb.Table> || None
        """
        mode = self.currentMode()
        if ( mode == XOrbBrowserWidget.Mode.Detail ):
            self.detailWidget().setCurrentRecord(record)
        
        elif ( mode == XOrbBrowserWidget.Mode.Thumbnail ):
            thumbs = self.thumbnailWidget()
            for row in range(thumbs.count()):
                item = thumbs.item(row)
                if ( isinstance(item, RecordListWidgetItem) and \
                     item.record() == item ):
                    thumbs.setCurrentItem(item)
                    break
    
    def setDetailMode( self ):
        """
        Sets the mode for this widget to the Detail mode.
        """
        self.setCurrentMode(XOrbBrowserWidget.Mode.Detail)
    
    def setFactory( self, factory ):
        """
        Sets the factory assigned to this browser for generating card and
        thumbnail information for records.
        
        :param      factory | <XOrbBrowserFactory>
        """
        self._factory = factory
        self._queryWidget.setFactory(factory)
    
    def setGroupByAdvanced( self ):
        """
        Sets the groupBy key for this widget to GroupByAdvancedKey signaling 
        that the advanced user grouping should be used.
        """
        self.setGroupBy(XOrbBrowserWidget.GroupByAdvancedKey)
    
    def setGroupBy( self, groupBy ):
        """
        Sets the group by key for this widget.  This should correspond to a 
        display name for the columns, or the GroupByAdvancedKey keyword.  It is
        recommended to use setGroupByAdvanced for setting advanced groupings.
        
        :param      groupBy | <str>
        """
        self._groupBy = groupBy
    
    def setGroupingActive( self, state ):
        """
        Sets whether or not the grouping should be enabled for the widget.
        
        :param      state | <bool>
        """
        self.uiGroupBTN.setChecked(state)
    
    def setHint( self, hint ):
        """
        Sets the hint for this widget.
        
        :param      hint | <str>
        """
        self._hint = hint
        self.detailWidget().setHint(hint)
    
    def setModeEnabled( self, mode, state ):
        """
        Sets whether or not the mode should be enabled.
        
        :param      mode  | <XOrbBrowserWidget.Mode>
                    state | <bool>
        """
        if ( mode == XOrbBrowserWidget.Mode.Detail ):
            self.uiDetailsACT.setEnabled(state)
        elif ( mode == XOrbBrowserWidget.Mode.Card ):
            self.uiCardACT.setEnabled(state)
        else:
            self.uiThumbnailACT.setEnabled(state)
    
    def setQuery( self, query ):
        """
        Sets the fixed lookup query for this widget to the inputed query.
        
        :param      query | <orb.Query>
        """
        self._query = query
        if ( not self.signalsBlocked() ):
            self.queryChanged.emit(query)
    
    def setTableType( self, tableType ):
        """
        Sets the table type for this widget to the inputed type.
        
        :param      tableType | <orb.Table>
        """
        self.detailWidget().setTableType(tableType)
        self.queryWidget().setTableType(tableType)
    
    def setThumbnailMode( self ):
        """
        Sets the mode for this widget to the thumbnail mode.
        """
        self.setCurrentMode(XOrbBrowserWidget.Mode.Thumbnail)
    
    def setThumbnailSize( self, size ):
        """
        Sets the size that will be used for the thumbnails in this widget.
        
        :param      size | <QSize>
        """
        self._thumbnailSize = QSize(size)
    
    def showGroupMenu( self ):
        """
        Displays the group menu to the user for modification.
        """
        group_active = self.isGroupingActive()
        group_by     = self.groupBy()
        
        menu = XMenu(self)
        menu.setTitle('Grouping Options')
        menu.setShowTitle(True)
        menu.addAction('Edit Advanced Grouping')
        
        menu.addSeparator()
        
        action = menu.addAction('No Grouping')
        action.setCheckable(True)
        action.setChecked(not group_active)
        
        action = menu.addAction('Advanced')
        action.setCheckable(True)
        action.setChecked(group_by == self.GroupByAdvancedKey and group_active)
        if ( group_by == self.GroupByAdvancedKey ):
            font = action.font()
            font.setBold(True)
            action.setFont(font)
        
        menu.addSeparator()
        
        # add dynamic options from the table schema
        tableType = self.tableType()
        if ( tableType ):
            columns = tableType.schema().columns()
            columns.sort(key = lambda x: x.displayName())
            for column in columns:
                action = menu.addAction(column.displayName())
                action.setCheckable(True)
                action.setChecked(group_by == column.displayName() and
                                  group_active)
                
                if ( column.displayName() == group_by ):
                    font = action.font()
                    font.setBold(True)
                    action.setFont(font)
        
        point = QPoint(0, self.uiGroupOptionsBTN.height())
        action = menu.exec_(self.uiGroupOptionsBTN.mapToGlobal(point))
        
        if ( not action ):
            return
        elif ( action.text() == 'Edit Advanced Grouping' ):
            print 'edit advanced grouping options'
        elif ( action.text() == 'No Grouping' ):
            self.setGroupingActive(False)
            
        elif ( action.text() == 'Advanced' ):
            self.uiGroupBTN.blockSignals(True)
            self.setGroupBy(self.GroupByAdvancedKey)
            self.setGroupingActive(True)
            self.uiGroupBTN.blockSignals(False)
            
            self.refreshResults()
        
        else:
            self.uiGroupBTN.blockSignals(True)
            self.setGroupBy(nativestring(action.text()))
            self.setGroupingActive(True)
            self.uiGroupBTN.blockSignals(False)
            
            self.refreshResults()
    
    def stackWidget( self ):
        """
        Returns the stack widget linked with this browser.  This contains the
        different views linked with the view mode.
        
        :return     <QStackWidget>
        """
        return self.uiModeSTACK
    
    def tableType( self ):
        """
        Returns the table type for this widget.
        
        :return     <orb.Table>
        """
        return self.detailWidget().tableType()
    
    def thumbnailSize( self ):
        """
        Returns the size that will be used for displaying thumbnails for this
        widget.
        
        :return     <QSize>
        """
        return self._thumbnailSize
    
    def thumbnailWidget( self ):
        """
        Returns the thumbnail widget for this widget.
        
        :return     <QListWidget>
        """
        return self.uiThumbLIST
    
    x_hint = Property(str, hint, setHint)