#!/usr/bin/python

""" [desc] """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintenance information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'


#------------------------------------------------------------------------------

import logging
import re
import time
import weakref

from projex.text import nativestring

from projex.enum import enum
import projexui
from projexui import resources

from projexui.qt import Signal, Slot, Property, SIGNAL, unwrapNone
from projexui.qt.QtCore import Qt,\
                               QMimeData,\
                               QByteArray,\
                               QObject,\
                               QTimer

from projexui.qt.QtGui import QTreeWidgetItem,\
                              QColor,\
                              QApplication,\
                              QMessageBox,\
                              QMenu,\
                              QIcon,\
                              QDialogButtonBox,\
                              QLabel,\
                              QAction

from projexui.qt import QtGui

from projexui.xcolorset                             import XColorSet
from projexui.widgets.xtreewidget                   import XTreeWidget,\
                                                           XTreeWidgetDelegate,\
                                                           XTreeWidgetItem,\
                                                           XLoaderItem
from projexui.widgets.xenumbox                      import XEnumBox
from projexui.widgets.xorbtreewidget.xorbrecorditem import XOrbRecordItem
from projexui.widgets.xorbtreewidget.xorbgroupitem  import XOrbGroupItem
from projexui.widgets.xloaderwidget                 import XLoaderWidget
from projexui.widgets.xurlwidget                    import XUrlWidget
from projexui.widgets.xfilepathedit                 import XFilepathEdit
from projexui.widgets.xdatetimeedit                 import XDateTimeEdit
from projexui.widgets.xtimeedit                     import XTimeEdit
from projexui.widgets.xdateedit                     import XDateEdit
from projexui.xorblookupworker                      import XOrbLookupWorker
from projexui.widgets.xboolcombobox                 import XBoolComboBox
from projexui.widgets.xpopupwidget                  import XPopupWidget

logger = logging.getLogger(__name__)

try:
    from orb import RecordSet, Orb, Query as Q, ColumnType, Column

except ImportError:
    logger.warning('The XOrbTreeWidget will not work without the orb package.')
    RecordSet = None
    Orb = None
    Q = None

#----------------------------------------------------------------------

class XOrbEditorPlugin(object):
    def __init__(self, editorClass=None):
        self._editorClass = editorClass
        
    def createEditor(self, parent, record, column):
        if self._editorClass:
            return self._editorClass(parent)
        return None
    
    def setEditorValue(self, editor, record, column):
        value = record.recordValue(column.name(), autoInflate=True)
        projexui.setWidgetValue(editor, value)
    
    def setRecordValue(self, editor, record, column):
        value, success = projexui.widgetValue(editor)
        if success:
            record.setRecordValue(column.name(), value)

#----------------------------------------------------------------------

class ForeignKeyPlugin(XOrbEditorPlugin):
    def createEditor(self, parent, record, column):
        editor = super(ForeignKeyPlugin, self).createEditor(parent,
                                                            record,
                                                            column)
        
        if editor:
            model = column.referenceModel()
            if model:
                editor.setRequired(column.required())
                editor.setRecords(model.select())
        
        return editor

#----------------------------------------------------------------------

class EnumPlugin(XOrbEditorPlugin):
    def createEditor(self, parent, record, column):
        editor = super(EnumPlugin, self).createEditor(parent, record, column)
        editor.setCheckable(True)
        try:
            editor.setEnum(column.enum())
        except:
            pass
        return editor

#----------------------------------------------------------------------

class NumericPlugin(XOrbEditorPlugin):
    def createEditor(self, parent, record, column):
        editor = super(NumericPlugin, self).createEditor(parent,
                                                         record,
                                                         column)
        
        if editor:
            editor.setMaximum(1000000)
            editor.setMinimum(-1000000)
        
        return editor

#----------------------------------------------------------------------

class XOrbTreeWidgetDelegate(XTreeWidgetDelegate):
    def __init__(self, *args, **kwds):
        super(XOrbTreeWidgetDelegate, self).__init__(*args, **kwds)
        
        self._plugins = {}
        
        # register default plugins
        self.registerPlugin(XOrbEditorPlugin(XDateEdit),
                            ColumnType.Date)
        
        self.registerPlugin(EnumPlugin(XEnumBox), ColumnType.Enum)
        
        self.registerPlugin(XOrbEditorPlugin(XDateTimeEdit),
                            ColumnType.Datetime)
        
        self.registerPlugin(XOrbEditorPlugin(XTimeEdit),
                            ColumnType.Time)
        
        for typ in (ColumnType.String, ColumnType.Password, ColumnType.Text):
            self.registerPlugin(XOrbEditorPlugin(QtGui.QLineEdit), typ)
        
        self.registerPlugin(XOrbEditorPlugin(XFilepathEdit),
                            ColumnType.Filepath)
        
        self.registerPlugin(NumericPlugin(QtGui.QSpinBox),
                            ColumnType.Integer)
        
        self.registerPlugin(XOrbEditorPlugin(XBoolComboBox), ColumnType.Bool)
        
        #----------------------------------------------------------------------
        
        for typ in (ColumnType.Double, ColumnType.Decimal):
            self.registerPlugin(NumericPlugin(QtGui.QDoubleSpinBox), typ)
        
        from projexui.widgets.xorbrecordbox import XOrbRecordBox
        self.registerPlugin(XOrbEditorPlugin(XUrlWidget), ColumnType.Url)
        self.registerPlugin(ForeignKeyPlugin(XOrbRecordBox),
                            ColumnType.ForeignKey)
    
    def column(self, index):
        tree = self.parent()
        tableType = tree.tableType()
        column_name = tree.columnOf(index.column())
        
        if not tableType:
            return None
        
        return tableType.schema().column(column_name)
    
    def createEditor( self, parent, option, index ):
        """
        Creates a new editor for the given index parented to the inputed widget.
        
        :param      parent | <QWidget>
                    option | <QStyleOption>
                    index  | <QModelIndex>
        
        :return     <QWidget> || None
        """
        # determine the editor to use for the inputed index based on the
        # table column
        item   = self.parent().itemFromIndex(index)
        column = self.column(index)
        
        # edit based on column preferences
        if column and \
           not column.isReadOnly() and \
           isinstance(item, XOrbRecordItem):
            plugin = self.plugin(column)
            if not plugin:
                return None
            
            return plugin.createEditor(parent, item.record(), column)
        
        return super(XOrbTreeWidgetDelegate, self).createEditor(parent,
                                                                option,
                                                                index)
        
    def plugin(self, column):
        if not column:
            return None
        
        a = (column.columnType(), column.name())
        b = (column.columnType(), None)
        c = (None, column.name())
        d = (None, None)
        
        for typ in (a, b, c, d):
            try:
                return self._plugins[typ]
            except:
                continue
        
        return None
    
    def registerPlugin(self, plugin, columnType=None, columnName=None):
        self._plugins[(columnType, columnName)] = plugin

    def setEditorData(self, editor, index):
        item   = self.parent().itemFromIndex(index)
        column = self.column(index)
        
        # edit based on column preferences
        if column and isinstance(item, XOrbRecordItem):
            plugin = self.plugin(column)
            if not plugin:
                return
            
            plugin.setEditorValue(editor, item.record(), column)
        else:
            super(XOrbTreeWidgetDelegate, self).setEditorData(editor, index)
    
    def setModelData(self, editor, model, index):
        item   = self.parent().itemFromIndex(index)
        column = self.column(index)
        
        # edit based on column preferences
        if column and isinstance(item, XOrbRecordItem):
            plugin = self.plugin(column)
            if not plugin:
                return
            
            record = item.record()
            plugin.setRecordValue(editor, record, column)
            item.updateRecordValues()
        
        # edit standard mechanism
        else:
            super(XOrbTreeWidgetDelegate, self).setModelData(editor, model, index)

#----------------------------------------------------------------------

class XAddRecordItem(XTreeWidgetItem):
    def __lt__(self, other):
        return True

    def __init__(self, parent, text):
        super(XAddRecordItem, self).__init__(parent, [text])
        
        self.setFixedHeight(22)
        self.setFlags(Qt.ItemIsEnabled)
        self.setFirstColumnSpanned(True)
        font = self.font(0)
        font.setBold(True)
        self.setFont(0, font)

#----------------------------------------------------------------------

class XBatchItem(XLoaderItem):
    def __init__(self, parent, count, batch):
        super(XBatchItem, self).__init__(parent)
        
        # define custom properties
        self._batch = batch
        
        self.setText(0, 'Load {0} more...'.format(count))
    
    def batch(self):
        """
        Returns the batch record set associated with this item.
        
        :return     <orb.RecordSet>
        """
        return self._batch
    
    def startLoading(self):
        """
        Starts loading this item for the batch.
        """
        if super(XBatchItem, self).startLoading():
            tree = self.treeWidget()
            if not isinstance(tree, XOrbTreeWidget):
                self.takeFromTree()
                return
            
            next_batch = self.batch()
            tree._loadBatch(self, next_batch)

#------------------------------------------------------------------------------

class XOrbTreeWidget(XTreeWidget):
    """ """
    __designer_group__ = 'ProjexUI - ORB'
    
    EditorFlags = enum('Create', 'Edit', 'Remove')
    QueryAction = enum('Replace', 'Join')
    
    aboutToSaveRecord           = Signal(object)
    currentRecordChanged        = Signal(object)
    loadColumnsRequested        = Signal(object, str)
    loadBatchRequested          = Signal(object)
    loadRequested               = Signal(object)
    queryChanged                = Signal()
    recordCreated               = Signal(object)
    recordClicked               = Signal(object)
    recordDoubleClicked         = Signal(object)
    recordMiddleClicked         = Signal(object)
    recordMiddleDoubleClicked   = Signal(object)
    recordCountChanged          = Signal(int)
    recordsCommitted            = Signal()
    recordsChanged              = Signal()
    recordUpdated               = Signal(object)
    recordsRemoved              = Signal(list)
    tableTypeChanged            = Signal()
    
    def __init__( self, parent=None):
        super(XOrbTreeWidget, self).__init__(parent, XOrbTreeWidgetDelegate)
        
        # define table information
        self._tableTypeName     = ''
        self._tableType         = None
        self._recordMapping     = {}
        
        # define lookup information
        self._database          = None
        self._query             = None
        self._queryAction       = XOrbTreeWidget.QueryAction.Replace
        self._order             = None
        self._groupBy           = None
        self._searchTerms       = ''
        self._baseHint          = ''
        self._useLoader         = True
        self._loaderThreshold   = 100
        self._columnsInitialized = False
        self._groupingActive   = True
        self._specifiedColumnsOnly = False
        self._specifiedColumns  = None
        self._useDefaultKeystrokes = False
        self._useGroupStyle     = False
        self._showAddEntryItem  = False
        self._tempCurrentRecord = None
        self._threadEnabled     = True
        self._autoExpand        = {}
        self._preloadColumns    = []
        self._userGroupingEnabled = False
        
        # define record editing information
        self._recordEditors     = {}
        self._popup             = None
        self._popupEditing      = True
        self._editOnDoubleClick = True
        self._editorFlags       = XOrbTreeWidget.EditorFlags.all()
        
        # define record information
        self._searched          = False
        self._searchableRecords = None
        self._recordSet         = None  # defines the base record set
        self._currentRecordSet  = None  # defines the current working set
        
        # define paging information
        self._fullyLoaded       = False
        self._fullyLoaded       = False
        self._paged             = False
        self._autoloadPages     = True
        self._pageSize          = 0
        
        # define refresh timer - delays when the records will be loaded until
        # necessary
        self._refreshTimer = QTimer(self)
        self._refreshTimer.setInterval(500)
        self._refreshTimer.setSingleShot(True)
        
        # define worker thread
        self._worker            = None
        
        # define column information
        self._loadedColumns     = set()
        self._columnMappers     = {}
        self._columnOrderNames  = {}
        self._batchloaders      = []
        
        # define UI information
        self._editColumn        = None
        self._recordItemClass   = {None: XOrbRecordItem}
        self._recordGroupClass  = {None: XOrbGroupItem}
        self._hierarchyLookup   = {}
        self._colored           = True
        
        self._colorSet          = XColorSet()
        self._colorSet.setColor('RecordNew',      QColor('green'))
        self._colorSet.setColor('RecordRemoved',  QColor('red'))
        self._colorSet.setColor('RecordModified', QColor('blue'))
        
        # create connections
        self.sortingChanged.connect(self.reorder)
        
        # create threading connections
        self.itemExpanded.connect(self.loadItem)
        self.itemExpanded.connect(self.updateItemIcon)
        self.itemCollapsed.connect(self.updateItemIcon)
        self.itemClicked.connect(self.emitRecordClicked)
        self.itemDoubleClicked.connect(self.emitRecordDoubleClicked)
        self.itemMiddleClicked.connect(self.emitRecordMiddleClicked)
        self.itemMiddleDoubleClicked.connect(self.emitRecordMiddleDoubleClicked)
        self.currentItemChanged.connect(self.emitCurrentRecordChanged)
        self.columnHiddenChanged.connect(self._updateColumnValues)
        self._refreshTimer.timeout.connect(self.refresh)
        self.headerMenuAboutToShow.connect(self.setupHeaderMenu)
    
    def _commitToSelected(self, item, columnIndex):
        if columnIndex != self._editColumn:
            return
        
        tableType = self.tableType()
        if not tableType:
            return
        
        if not isinstance(item, XOrbRecordItem):
            return
        
        schema = tableType.schema()
        columnTitle = self.columnOf(columnIndex)
        column = schema.column(columnTitle)
        if not column:
            return
        
        columnName = column.name()
        value = item.record().recordValue(columnName)
        
        self.blockSignals(True)
        for sel_item in self.selectedItems():
            if not isinstance(sel_item, XOrbRecordItem):
                continue
            
            if sel_item != item:
                sel_item.record().setRecordValue(columnName, value)
                sel_item.updateRecordValues()
        self.blockSignals(False)

    def _loadBatch(self, item, batch):
        """
        Loads the batch of items for this tree based on the inputed batch item.
        
        :param      item  | <XBatchItem>
                    batch | <orb.RecordSet>
        """
        if self.isThreadEnabled() and batch.isThreadEnabled():
            self.loadBatchRequested.emit(batch)
            self._batchloaders.append(weakref.ref(item))
        else:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.worker().loadRecords(batch)
            QApplication.restoreOverrideCursor()
    
    def _connectionLost(self):
        XLoaderWidget.stop(self, force=True)
        msg = 'Connection to database was lost.  Please refresh to try again.'
        self.setHint(msg)
    
    def _loadColumns(self, record, columnName, value):
        """
        Loads the column information for this tree widget for the given record.
        
        :param      record      | <orb.Table>
                    columnName  | <str>
                    value       | <variant>
        """
        value = unwrapNone(value)
        item = self.findRecordItem(record)
        if item:
            item.updateColumnValue(record.schema().column(columnName),
                                   value,
                                   self.column(columnName))
    
    def _loadRecords(self, records, nextBatch=None, parent=None):
        # clear out old batch loaders
        for loader in self._batchloaders:
            item = loader()
            if item:
                item.takeFromTree()
        
        self._batchloaders = []
        
        # assign the parent for this record set
        if parent is None:
            parent = self
        
        for record in records:
            cls = self.recordItemClass(record)
            cls(parent, record)
        
        # create the load next records item if there are remaining records
        if nextBatch is not None:
            self._fullyLoaded = False
            item = XBatchItem(parent, self.pageSize(), nextBatch)
            item.autoload(self.autoloadPages())
        else:
            self._fullyLoaded = True
        
        self.smartResizeColumnsToContents()
    
    def _setCurrentRecord(self, item, record):
        """
        Sets the current record for this tree to the inputed record.
        
        :param      item   | <QTreeWidgetItem>
                    record | <orb.Table>
        """
        try:
            is_record = item.record() == record
        except:
            is_record = False
        
        if is_record:
            self.setCurrentItem(item)
            return True
        
        for c in range(item.childCount()):
            if self._setCurrentRecord(item.child(c), record):
                return True
        
        return False
    
    def _updateColumnValues(self, index, hidden):
        """
        Updates the column values for the inputed column.
        
        :param      column | <int>
                    state  | <bool>
        """
        if hidden or not self.isVisible():
            return
        
        column = self.columnOf(index)
        if not column in self._loadedColumns:
            self._loadedColumns.add(column)
            
            records = self.collectRecords()
            self.loadColumnsRequested.emit(records, column)
    
    def addEntryItem(self):
        """
        Returns the add entry item for this tree.
        
        :return     <XAddEntryItem> || None
        """
        for item in self.topLevelItems():
            if isinstance(item, XAddRecordItem):
                return item
        return None
    
    def addEntryText(self):
        """
        Returns the text to be used for the add new record item.
        
        :return     <str>
        """
        if self.tableType():
            name = self.tableType().schema().displayName().lower()
            return 'add new {0}...'.format(name)
        return 'add new record...'
    
    @Slot()
    def activateGrouping(self):
        """
        Enables the grouping system for this widget.
        """
        self.setGroupingActive(True)
    
    def assignOrderNames(self):
        """
        Assigns the order names for this tree based on the name of the
        columns.
        """
        try:
            schema = self.tableType().schema()
        except AttributeError:
            return
        
        for colname in self.columns():
            column = schema.column(colname)
            if column:
                self.setColumnOrderName(colname, column.name())
    
    def autoExpand(self, level=None):
        """
        Returns whether or not to expand for the inputed level.
        
        :param      level | <int> || None
        
        :return     <bool>
        """
        return self._autoExpand.get(level, self._autoExpand.get(None, False))
    
    def autoloadPages(self):
        """
        Returns whether or not to autoload paged results.
        
        :return     <bool>
        """
        return self._autoloadPages
    
    def clearAll(self):
        """
        Clears the tree and record information.
        """
        # clear the tree information
        self.clear()
        
        # clear table information
        self._tableTypeName  = ''
        self._tableType      = None
        
        # clear the records information
        self._recordSet         = None
        self._currentRecordSet  = None
        
        # clear lookup information
        self._query             = None
        self._order             = None
        self._groupBy           = None
        
        # clear paging information
        
        if not self.signalsBlocked():
            self.recordsChanged.emit()
    
    def clearSearch(self):
        """
        Clears the serach information for this tree.
        """
        self._currentRecordSet = None
        
        if not self.signalsBlocked():
            self.recordsChanged.emit()
    
    def checkedRecords(self, column=0, parent=None, recurse=True):
        """
        Returns a list of the records from this tree that have been checked 
        by the user.
        
        :return     [<orb.Table>, ..]
        """
        output = []
        for item in self.checkedItems(column, parent, recurse):
            try:
                record = item.record()
                if record is not None:
                    output.append(record)
            except AttributeError:
                continue
        return output
    
    def colorSet(self):
        """
        Returns the color set linked with this tree.
        
        :return     <XColorSet>
        """
        return self._colorSet
    
    def collectRecords(self, parent=None):
        """
        Collects all the record instances from the tree.
        
        :return     [<orb.Table>
        """
        out = []
        if not parent:
            for i in range(self.topLevelItemCount()):
                item = self.topLevelItem(i)
                try:
                    out.append(item.record())
                except AttributeError:
                    pass
                
                out += self.collectRecords(item)
        else:
            for c in range(parent.childCount()):
                item = parent.child(c)
                try:
                    out.append(item.record())
                except AttributeERror:
                    pass
                
                out += self.collectRecords(item)
        
        return out
    
    def columnOrderName(self, columnName):
        """
        Returns the order name that will be used for this column when
        sorting the database model.
        
        :param      columnName     | <str>
        
        :return     <str> | orderName
        """
        return self._columnOrderNames.get(nativestring(columnName), '')
    
    def columnMapper(self, columnName):
        """
        Returns the callable method that is associated with the inputed
        column name.
        
        :param      columnName | <str>
        
        :sa         setColumnMapper
        
        :return     <method> || <function> || <lambda> || None
        """
        return self._columnMappers.get(nativestring(columnName))
    
    def columnMappers(self):
        """
        Returns the dictionary of column mappers linked with this tree.
        
        :sa         setColumnMapper
        
        :return     {<str> columnName: <callable>, ..}
        """
        return self._columnMappers
    
    @Slot()
    def commit(self):
        """
        Commits the changes for all the items in the tree.
        
        :return     <bool> | success
        """
        remove_items = []
        commit_items = []
        
        # remove all the items
        commit_state = XOrbRecordItem.State.Modified | XOrbRecordItem.State.New
        remove_state = XOrbRecordItem.State.Removed
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            
            if isinstance(item, XOrbRecordItem) or\
                isinstance(item, XOrbGroupItem):
                remove_items += item.findItemsByState(remove_state)
                commit_items += item.findItemsByState(commit_state)
        
        # make sure we can remove the records
        for item in remove_items:
            record = item.record()
            try:
                record.remove(dryRun = True, throw=True)
            except orb.errors.CannotRemoveError, err:
                QMessageBox.information(self,
                                        'Cannot Remove',
                                        nativestring(err))
                return False
        
        # remove the records
        remove_set = RecordSet([item.record() for item in remove_items])
        remove_set.remove()
        
        for item in remove_items:
            item.record().remove()
            parent = item.parent()
            if parent:
                index = parent.indexOfChild(item)
                parent.takeChild(index)
            else:
                index = self.indexOfTopLevelItem(item)
                self.takeTopLevelItem(index)
        
        # commit the new records
        for item in commit_items:
            self.aboutToSaveRecord.emit(item.record())
            item.record().commit()
            item.setRecordState(XOrbRecordItem.State.Normal)
        
        self.recordsCommitted.emit()
        
        return True
    
    def commitData(self, widget):
        """
        Commits the data from the widget to the model.
        
        :param      widget | <QWidget>
        """
        self._editColumn = self.currentColumn()
        self.itemChanged.connect(self._commitToSelected)
        super(XOrbTreeWidget, self).commitData(widget)
        self.itemChanged.disconnect(self._commitToSelected)
        self._editColumn = None
    
    def contextMenuEvent(self, event):
        """
        Handles the default menu options for the orb widget.
        
        :param      event | <QContextMenuEvent>
        """
        if self.contextMenuPolicy() == Qt.DefaultContextMenu:
            self.showMenu(event.pos())
        else:
            super(XOrbTreeWidget, self).contextMenuEvent(event)
    
    def createRecordItem(self, record, parent=None):
        """
        Creates the record item instance for the given record.
        
        :param      parent      | <QTreeWidgetItem> || <QTreeWidget>
                    record      | <orb.Table>
        
        :return     <QTreeWidgetItem>
        """
        if parent is None:
            parent=self
        
        return self.recordItemClass(record)(parent, record)
    
    def createRecordItems(self, records, parent=None):
        """
        Creates the record item instance for the given record.
        
        :param      records     | [<orb.Table>, ..]
                    parent      | <QTreeWidgetItem> || <QTreeWidget>
        
        :return     <QTreeWidgetItem>
        """
        if parent is None:
            parent=self
            
        blocked = self.signalsBlocked()
        self.blockSignals(True)
        self.setUpdatesEnabled(False)
        for record in records:
            self.recordItemClass(record)(parent, record)
        
        if not blocked:
            self.blockSignals(False)
            self.setUpdatesEnabled(True)
    
    def createGroupItem(self, grp, records, nextLevels=None, parent=None):
        """
        Creates the grouping item instance for the group with the given record
        information.
        
        :param      grp         | <variant>
                    record      | [<orb.Table>, ..] || <dict>
                    parent      | <QTreeWidgetItem> || <QTreeWidget>
        
        :return     <QTreeWidgetItem>
        """
        if parent is None:
            parent = self
        
        item = self.recordGroupClass(type(grp))(parent,
                                                grp,
                                                records,
                                                nextLevels)
        
        if parent == self and self.useGroupStyle():
            item.initGroupStyle()
        
        level = 0
        while parent and parent != self:
            level += 1
            parent = parent.parent()
        
        expand = self.autoExpand(level)
        if expand:
            try:
                item.load()
            except AttributeError:
                pass
            item.setExpanded(True)
        
        return item
    
    def currentRecord(self):
        """
        Returns the current record from the tree view.
        
        :return     <orb.Table> || None
        """
        item = self.currentItem()
        if isinstance(item, XOrbRecordItem):
            return item.record()
        return None
    
    def currentRecordSet(self):
        """
        Returns the current record set for this widget, after all searching,
        paging, refining, etc. that has occurred from the base record set.
        
        :sa     refine, search, records
        
        :return     <orb.RecordSet>
        """
        if self._currentRecordSet is None:
            return self.recordSet()
        
        return self._currentRecordSet
    
    def database(self):
        """
        Returns the database associated with this tree widget.
        
        :return     <orb.Database> || None
        """
        if self._database:
            return self._database
        if self._recordSet is not None:
            return self._recordSet.database()
        else:
            return Orb.instance().database()
    
    @Slot()
    def deactivateGrouping(self):
        """
        Disables the grouping system for this widget.
        """
        self.setGroupingActive(False)
    
    def dragEnterEvent(self, event):
        """
        Listens for query's being dragged and dropped onto this tree.
        
        :param      event | <QDragEnterEvent>
        """
        data = event.mimeData()
        if data.hasFormat('application/x-orb-table') and \
           data.hasFormat('application/x-orb-query'):
            tableName = self.tableTypeName()
            if nativestring(data.data('application/x-orb-table')) == tableName:
                event.acceptProposedAction()
                return
        
        super(XOrbTreeWidget, self).dragEnterEvent(event)
    
    def dragMoveEvent(self, event):
        """
        Listens for query's being dragged and dropped onto this tree.
        
        :param      event | <QDragEnterEvent>
        """
        data = event.mimeData()
        if data.hasFormat('application/x-orb-table') and \
           data.hasFormat('application/x-orb-query'):
            tableName = self.tableTypeName()
            if nativestring(data.data('application/x-orb-table')) == tableName:
                event.acceptProposedAction()
                return
        
        super(XOrbTreeWidget, self).dragMoveEvent(event)
    
    def dropEvent(self, event):
        """
        Listens for query's being dragged and dropped onto this tree.
        
        :param      event | <QDropEvent>
        """
        # overload the current filtering options
        data = event.mimeData()
        if data.hasFormat('application/x-orb-table') and \
           data.hasFormat('application/x-orb-query'):
            tableName = self.tableTypeName()
            if nativestring(data.data('application/x-orb-table')) == tableName:
                data = nativestring(data.data('application/x-orb-query'))
                query = Q.fromXmlString(data)
                self.setQuery(query)
                return
        
        super(XOrbTreeWidget, self).dropEvent(event)
    
    def groupBy(self):
        """
        Returns the group by information for this tree.
        
        :return     [<str>, ..]
        """
        return self._groupBy
    
    @Slot()
    def groupByHeaderIndex(self):
        """
        Assigns the grouping to the current header index.
        """
        index = self.headerMenuColumn()
        columnTitle = self.columnOf(index)
        tableType = self.tableType()
        
        if not tableType:
            return
        
        column = tableType.schema().column(columnTitle)
        if not column:
            return
        
        self.setGroupBy(column.name())
        self.setGroupingActive(True)
    
    def hierarchyLookup(self, record):
        """
        Looks up additional hierarchy information for the inputed record.
        
        :param      record | <orb.Table>
        
        :return     (<subclass of orb.Table> || None, <str> column)
        """
        def _get_lookup(cls):
            if cls in self._hierarchyLookup:
                return self._hierarchyLookup[cls]
            
            for base in cls.__bases__:
                results = _get_lookup(base)
                if results:
                    return results
            
            return (None, None)
        
        tableType, column = _get_lookup(type(record))
        
        if tableType and column:
            return (tableType, column)
        
        default = self._hierarchyLookup.get(None)
        if default:
            return default
        return (None, None)
        
    def editorFlags(self):
        """
        Returns the editor options for this record.
        
        :return     <XOrbTreeWidget.EditorFlags>
        """
        return self._editorFlags
    
    def editOnDoubleClick(self):
        """
        Returns whether or not editing should happen on a double click.
        
        :return     <bool>
        """
        return self._editOnDoubleClick
    
    def editRecord(self, record, pos=None):
        """
        Prompts the user to edit using a preset editor defined in the
        setRecordEditors method.
        
        :param      record | <orb.Table>
        
        :return     <bool> | success
        """
        
        typ = type(record)
        editor = self._recordEditors.get(typ)
        if not editor:
            return False
        
        if self.popupEditing():
            popup = self.popupWidget()
            edit = popup.centralWidget()
            
            # create a new editor if required
            if type(edit) != editor:
                if edit:
                    edit.close()
                    edit.deleteLater()
                
                edit = editor(popup)
                edit.setAutoCommitOnSave(True)
                popup.setCentralWidget(edit)
                popup.accepted.connect(edit.save)
                edit.aboutToSaveRecord.connect(self.recordUpdated)
                edit.saved.connect(self.refresh)
            
            edit.setRecord(record)
            popup.popup(pos)
        
        else:
            if editor.edit(record, autoCommit=False):
                self.recordUpdated.emit(record)
                record.commit()
                self.refresh()
        
        return True
    
    def emitCurrentRecordChanged(self, item):
        """
        Emits the record changed signal for the given item, provided the
        signals are not currently blocked.
        
        :param      item | <QTreeWidgetItem>
        """
        if self.signalsBlocked():
            return
        
        # emit that the record has been clicked
        if isinstance(item, XOrbRecordItem):
            self.currentRecordChanged.emit(item.record())
        else:
            self.currentRecordChanged.emit(None)
    
    def emitRecordClicked(self, item):
        """
        Emits the record clicked signal for the given item, provided the
        signals are not currently blocked.
        
        :param      item | <QTreeWidgetItem>
        """
        # load the next page
        if isinstance(item, XBatchItem):
            item.startLoading()
            self.clearSelection()
            
        # emit that the record has been clicked
        if isinstance(item, XOrbRecordItem) and not self.signalsBlocked():
            self.recordClicked.emit(item.record())
    
    def emitRecordDoubleClicked(self, item):
        """
        Emits the record clicked signal for the given item, provided the
        signals are not currently blocked.
        
        :param      item | <QTreeWidgetItem>
        """
        # emit that the record has been double clicked
        if isinstance(item, XOrbRecordItem) and not self.signalsBlocked():
            self.recordDoubleClicked.emit(item.record())
        
        # add a new blank entry if this tree supports it
        elif isinstance(item, XAddRecordItem) and self.tableType():
            self.blockSignals(True)
            item_cls = self.recordItemClass()
            new_item = item_cls(self, self.tableType()())
            self.takeTopLevelItem(self.indexOfTopLevelItem(item))
            self.addTopLevelItem(item)
            self.setCurrentItem(item)
            self.editItem(new_item, 0)
            self.blockSignals(False)
    
    def emitRecordMiddleClicked(self, item):
        """
        Emits the record clicked signal for the given item, provided the
        signals are not currently blocked.
        
        :param      item | <QTreeWidgetItem>
        """
        # emit that the record has been double clicked
        if isinstance(item, XOrbRecordItem) and not self.signalsBlocked():
            self.recordMiddleClicked.emit(item.record())
        
    def emitRecordMiddleDoubleClicked(self, item):
        """
        Emits the record clicked signal for the given item, provided the
        signals are not currently blocked.
        
        :param      item | <QTreeWidgetItem>
        """
        # emit that the record has been double clicked
        if isinstance(item, XOrbRecordItem) and not self.signalsBlocked():
            self.recordMiddleDoubleClicked.emit(item.record())
        
    def findRecordItem(self, record, parent=None):
        """
        Looks through the tree hierarchy for the given record.
        
        :param      record | <orb.Record>
                    parent | <QTreeWidgetItem> || None
        
        :return     <XOrbRecordItem> || None
        """
        try:
            item = self._recordMapping[record]()
        except KeyError:
            return None
        
        if item is None:
            self._recordMapping.pop(record)
        
        return item
    
    def initializeColumns(self):
        """
        Initializes the columns that will be used for this tree widget based \
        on the table type linked to it.
        """
        tableType = self.tableType()
        if not tableType:
            return
        elif self._columnsInitialized or self.columnOf(0) != '1':
            self.assignOrderNames()
            return
        
        # set the table header information
        tschema = tableType.schema()
        columns = tschema.columns()
        
        names = [col.displayName() for col in columns if not col.isPrivate()]
        self.setColumns(sorted(names))
        self.assignOrderNames()
        self.resizeToContents()
    
    def isColored(self):
        """
        Returns whether or not this widget should color its records.
        
        :return     <bool>
        """
        return self._colored
    
    def isFullyLoaded(self):
        """
        Returns whether or not this widget is fully loaded.
        
        :return     <bool>
        """
        return self._fullyLoaded
    
    def isGroupingActive(self):
        """
        Returns whether or not the grouping system is enabled for this
        widget.
        
        :return     <bool>
        """
        return self._groupingActive
    
    def isLoading(self):
        """
        Returns whether or not this widget is loading the records.
        
        :return     <bool>
        """
        return self._worker is not None and self._worker.isRunning()
    
    def isPaged(self):
        """
        Returns whether or not this tree contains paged information.
        
        :return     <bool>
        """
        return self._paged
    
    def isShowingSearchResults(self):
        """
        Returns whether or not the tree is showing search results or the
        main record items.
        
        :return     <bool>
        """
        return self._searched
    
    def isThreadEnabled(self):
        """
        Returns whether or not threading is enabled for this combo box.
        
        :return     <bool>
        """
        return self._threadEnabled
    
    def keyPressEvent(self, event):
        """
        Listen for the delete key and check to see if this should auto
        set the remove property on the object.
        
        :param      event | <QKeyPressEvent>
        """
        # tag the item for deletion
        if self.useDefaultKeystrokes() and self.isEditable():
            if event.key() == Qt.Key_Delete:
                for item in self.selectedItems():
                    item.setRecordState(XOrbRecordItem.State.Removed)
            
            # save/commit to the database
            elif event.key() == Qt.Key_S and\
                 event.modifiers() == Qt.ControlModifier:
                self.commit()
        
        super(XOrbTreeWidget, self).keyPressEvent(event)
    
    def loaderThreshold(self):
        """
        Returns the number of records that should be required before showing
        the loader.  You can alter this number if you know certain records
        or tables take longer than others to load.
        
        :return     <int>
        """
        return self._loaderThreshold
    
    def loadItem(self, item):
        """
        Prompts the item to use its lazy loading logic.
        
        :param      item | <QTreeWidgetItem>
        """
        try:
            item.load()
        except AttributeError:
            pass
    
    def markLoadingStarted(self):
        self.setCursor(Qt.WaitCursor)
        self._baseHint = self.hint()
        self._fullyLoaded = False
        
        self.setHint('Loading records...')
        
        self.setUpdatesEnabled(False)
        self.blockAllSignals(True)
        
        self.clear()
    
    def markLoadingFinished(self):
        self.smartResizeColumnsToContents()
        self.setUpdatesEnabled(True)
        self.blockAllSignals(False)
        
        self.setHint(self._baseHint)
        
        self.unsetCursor()
        XLoaderWidget.stop(self, force=True)
        
        # create an add entry item
        if self.showAddEntryItem() and not self.addEntryItem():
            XAddRecordItem(self, self.addEntryText())
        
        if self._tempCurrentRecord:
            record = self._tempCurrentRecord
            self.setCurrentRecord(record)
        
        # force-refresh of the sorting
        if self.isSortingEnabled():
            self.sortItems(self.sortColumn(), self.sortOrder())
    
    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.pos())
        
        # enable popup editing
        if isinstance(item, XOrbRecordItem) and \
           self.editOnDoubleClick() and \
           self.editorFlags() & XOrbTreeWidget.EditorFlags.Edit:
            if self.editRecord(item.record(), event.globalPos()):
                event.accept()
                return
        
        super(XOrbTreeWidget, self).mouseDoubleClickEvent(event)
    
    def mimeData(self, items):
        """
        Returns the mime data for dragging for this instance.
        
        :param      items | [<QTreeWidgetItem>, ..]
        """
        func = self.dataCollector()
        if func:
            return func(self, items)
        
        # extract the records from the items
        record_items = []
        for item in self.selectedItems():
            if isinstance(item, XOrbRecordItem):
                record_items.append(item)
        
        # create the mime data
        data = QMimeData()
        self.dataStoreRecords(data, record_items)
        return data
    
    def order(self):
        """
        Returns the order for this instance.
        
        :return     [(<str> column, <str> order), ..] || None
        """
        return self._order
    
    def query(self):
        """
        Returns the query that will be used for the records for this tree.
        
        :return     <orb.Query>
        """
        return self._query
    
    def queryAction(self):
        """
        Returns the action that should be taken when joining together
        a query assigned to this tree with a base record set that may or
        may not already have a query associated with it.
        
        :return     <XOrbTreeWidget.QueryAction>
        """
        return self._queryAction
    
    def pageSize(self):
        """
        Returns the page size for this widget.  If the page size is set to -1,
        then there is no sizing and all records are displayed.
        
        :return     <int>
        """
        if not self.isPaged():
            return 0
        return self._pageSize
    
    def popupEditing(self):
        """
        Returns whether or not this widget uses popup editing.
        
        :return     <bool>
        """
        return self._popupEditing
    
    def popupWidget(self):
        """
        Returns the popup widget for this editor.
        
        :return     <skyline.gui.XPopupWidget>
        """
        if not self._popup:
            btns = QDialogButtonBox.Save | QDialogButtonBox.Cancel
            self._popup = XPopupWidget(self, btns)
            self._popup.setShowTitleBar(False)
            self._popup.setAutoCalculateAnchor(True)
            self._popup.setPositionLinkedTo(self)
        return self._popup
    
    def preloadColumns(self):
        """
        Returns the list of columns that will be automatically preloaded 
        during the lookup thread.
        
        :return     [<str>, ..]
        """
        return self._preloadColumns
    
    def recordGroupClass(self, typ=None):
        """
        Returns the record group class instance linked with this tree widget.
        
        :return     <XOrbGroupItem>
        """
        return self._recordGroupClass.get(typ, self._recordGroupClass[None])
    
    def recordItemClass(self, record=None):
        """
        Returns the record item class instance linked with this tree widget.
        
        :return     <XOrbRecordItem>
        """
        if record is not None:
            key = type(record)
        else:
            key = None
        
        return self._recordItemClass.get(key, self._recordItemClass[None])
    
    def records(self):
        """
        Returns the record set instance linked with this tree.
        
        :sa         recordSet
        
        :return     <orb.RecordSet>
        """
        return self.recordSet()
    
    def recordEditor(self, tableType=None):
        """
        Returns the record editor from the set for the given table type.
        
        :param      tableType | <subclass of orb.Table> || None
        
        :return     <subclass of XOrbRecordWidget> || None
        """
        if tableType == None:
            tableType = self.tableType()
        
        return self._recordEditors.get(tableType, None)
    
    def recordSet(self):
        """
        Returns the record set instance linked with this tree.
        
        :return     <orb.RecordSet>
        """
        # define the base record set
        if self._recordSet is None:
            return RecordSet()
            
        return self._recordSet
    
    def registerEditorPlugin(self, plugin, columnType=None, columnName=None):
        self.itemDelegate().registerPlugin(plugin, columnType, columnName)
    
    def reorder(self, index, direction):
        """
        Reorders the data being displayed in this tree.  It will check to
        see if a server side requery needs to happen based on the paging
        information for this tree.
        
        :param      index     | <column>
                    direction | <Qt.SortOrder>
        
        :sa         setOrder
        """
        columnTitle = self.columnOf(index)
        columnName  = self.columnOrderName(columnTitle)
        
        if not columnName:
            return
        
        # grab the table and ensure we have a valid column
        table = self.tableType()
        if not table:
            return
        
        column = table.schema().column(columnName)
        if not column:
            return
        
        if direction == Qt.AscendingOrder:
            db_dir = 'asc'
        else:
            db_dir = 'desc'
        
        order = [(columnName, db_dir)]
        
        # lookup reference column ordering
        if column.isReference():
            ref = column.referenceModel()
            if ref:
                ref_order = ref.schema().defaultOrder()
                if ref_order:
                    order = [(columnName + '.' + ref_order[0][0], db_dir)]
                    order += ref_order[1:]
        
        # update the information
        self.clear()
        super(XOrbTreeWidget, self).sortByColumn(index, direction)
        
        self.setOrder(order)
        self.refresh()
    
    def refresh(self, reloadData=False, force=False):
        """
        Refreshes the record list for the tree.
        """
        if not (self.isVisible() or force):
            self._refreshTimer.start()
            return
        
        if self.isLoading():
            return
        
        if reloadData:
            self.refreshQueryRecords()
        
        # cancel current work
        self._refreshTimer.stop()
        self.worker().cancel()
        
        if self._popup:
            self._popup.close()
        
        # grab the record set
        currset = self.currentRecordSet()
        
        self.worker().setBatched(self.isPaged())
        self.worker().setBatchSize(self.pageSize())
        
        # group the information
        if self._searchTerms:
            currset.setGroupBy(None)
            pageSize = 0
        
        # work with groups
        elif self.groupBy() and self.isGroupingActive():
            currset.setGroupBy(self.groupBy())
        
        # work with batching
        else:
            currset.setGroupBy(None)
        
        # order the information
        if self.order():
            currset.setOrdered(True)
            currset.setOrder(self.order())
        
        # for larger queries, run it through the thread
        if self.useLoader():
            loader = XLoaderWidget.start(self)
        
        # specify the columns to load
        if self.specifiedColumnsOnly():
            currset.setColumns(map(lambda x: x.name(),
                                   self.specifiedColumns()))
        
        self._loadedColumns = set(self.visibleColumns())
        
        if self.isThreadEnabled() and currset.isThreadEnabled():
            self.worker().setPreloadColumns(self._preloadColumns)
            self.loadRequested.emit(currset)
        else:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.worker().loadRecords(currset)
            QApplication.restoreOverrideCursor()
    
    def refreshQueryRecords(self):
        """
        Refreshes the query results based on the tree's query.
        """
        if self._recordSet is not None:
            records = RecordSet(self._recordSet)
        elif self.tableType():
            records = self.tableType().select()
        else:
            return
        
        records.setDatabase(self.database())
        
        # replace the base query with this widget
        if self.queryAction() == XOrbTreeWidget.QueryAction.Replace:
            if self.query():
                records.setQuery(self.query())
            else:
                records.setQuery(None)
        
        # join together the query for this widget
        elif self.queryAction() == XOrbTreeWidget.QueryAction.Join:
            if records.query():
                records.setQuery(self.query() & self.query())
            elif self.query():
                records.setQuery(self.query())
            else:
                records.setQuery(None)
        
        self._recordSet = records
        
        if not self.signalsBlocked():
            self.queryChanged.emit()
            self.recordsChanged.emit()
    
    def restoreXml(self, xml):
        """
        Restores data from the xml entry.
        
        :param      xml | <xml.etree.ElementTree.Element>
        
        :return     <bool> | success
        """
        if xml is None:
            return False
        
        # restore grouping
        grps = xml.get('grouping')
        if grps is not None:
            self.setGroupingActive(True)
            self.setGroupBy(grps.split(','))
        
        # restore grouping enabled
        grp_enabled = xml.get('groupingActive')
        if grp_enabled is not None:
            self.setGroupingActive(grp_enabled == 'True', autoRefresh=False)
        
        # restore standard tree options
        return super(XOrbTreeWidget, self).restoreXml(xml)
    
    def saveXml(self, xml):
        """
        Saves the data for this tree to the inputed xml entry.
        
        :param      xml | <xml.etree.ElementTree.Element>
        
        :return     <bool> success
        """
        if xml is None:
            return False
        
        # save the grouping enabled information
        xml.set('groupingActive', nativestring(self.isGroupingActive()))
        
        # save the grouping information
        if self.groupBy():
            xml.set('grouping', ','.join(self.groupBy()))
        
        # save standard tree options
        return super(XOrbTreeWidget, self).saveXml(xml)
    
    def searchableRecords(self):
        """
        Returns the searchable records for this tree widget.
        
        :return     <orb.RecordSet>
        """
        if self._searchableRecords is not None:
            return self._searchableRecords
        return self.recordSet()
    
    @Slot('QString')
    def searchRecords(self, search):
        """
        Creates a search for the inputed records by joining the search terms
        and query from the inputed search string by using the 
        Orb.Query.fromSearch method.
        
        :param      search  | <str>
                    refined | <orb.Query> || None
        
        :return     <bool> | success
        """
        
        # take the base record set
        self._currentRecordSet  = None
        self._searchTerms       = nativestring(search)
        
        # if we don't have a search, then go back to the default records
        if not search:
            if not self.signalsBlocked():
                if self._recordSet is not None:
                    self._recordSet.clear()
                
                self._searched = False
                self.refresh()
                self.recordsChanged.emit()
                return False
            return False
        
        self._searched=True
        
        # start from our default record set
        rset = self.searchableRecords()
        self._currentRecordSet = rset.search(search)
        
        # update widget and notify any listeners
        if not self.signalsBlocked():
            self.refresh()
            self.recordsChanged.emit()
        
        return True
    
    def selectedRecords(self):
        """
        Returns a list of all the selected records for this widget.
        
        :return     [<orb.Table>, ..]
        """
        output = []
        for item in self.selectedItems():
            if ( isinstance(item, XOrbRecordItem) ):
                output.append(item.record())
        return output
    
    def setAutoExpand(self, state, level=None):
        """
        Sets whether or not to auto-expand items.  If you provide
        a level value, then only items at that level of deepness will
        expand.  If level is left as None, then all levels will
        expand by default to the inputed state.
        
        :param      state | <bool>
                    level | <int> || None
        """
        self._autoExpand[level] = state
    
    def setAutoloadPages(self, state):
        """
        Sets whether or not to autoload the pages for the widget.
        
        :param      state | <bool>
        """
        self._autoloadPages = state
    
    def setCheckedRecords(self, records, column=0, parent=None):
        """
        Sets the checked items based on the inputed list of records.
        
        :param      records | [<orb.Table>, ..]
                    parent  | <QTreeWidgetItem> || None
        """
        if parent is None:
            for i in range(self.topLevelItemCount()):
                item = self.topLevelItem(i)
                try:
                    has_record = item.record() in records
                except AttributeError:
                    has_record = False
                
                if has_record:
                    item.setCheckState(column, Qt.Checked)
                
                self.setCheckedRecords(records, column, item)
        else:
            for c in range(parent.childCount()):
                item = parent.child(c)
                try:
                    has_record = item.record() in records
                except AttributeError:
                    has_record = False
                
                if has_record:
                    item.setCheckState(column, Qt.Checked)
                
                self.setCheckedRecords(records, column, item)
    
    def setColored(self, state):
        """
        Sets the colored state for this tree.
        
        :param      state | <bool>
        """
        self._colored = state
    
    def setColorSet(self, colorSet):
        """
        Sets the color set linked with this tree.
        
        :param     colorSet | <XColorSet>
        """
        self._colorSet = colorSet
    
    def setColumns(self, columns):
        """
        Sets the columns for this widget, and marks the system as having
        been initialized.
        
        :param      columns | [<str>, ..]
        """
        super(XOrbTreeWidget, self).setColumns(columns)
        self.setFilteredColumns(range(len(columns)))
        self.assignOrderNames()
        self._columnsInitialized = True
    
    def setColumnMapper(self, columnName, callable):
        """
        Sets the mapper for the given column name to the callable.  The inputed
        callable should accept a single argument for a record from the tree and
        return the text that should be displayed in the column.
        
        :param      columnName | <str>
                    callable   | <function> || <method> || <lambda>
        """
        columnName = nativestring(columnName)
        if ( callable is None and columnName in self._columnMappers ):
            self._columnMappers.pop(columnName)
            return
        
        self._columnMappers[nativestring(columnName)] = callable
    
    def setCurrentRecord(self, record):
        """
        Sets the current record for this tree to the inputed record.
        
        :param      record | <orb.Table>
        """
        if self.isLoading():
            self._tempCurrentRecord = record
            return
        
        for i in range(self.topLevelItemCount()):
            if self._setCurrentRecord(self.topLevelItem(i), record):
                return True
        return False
    
    def setDatabase(self, database):
        """
        Sets the database explicitly associated with this widget.
        
        :param      database | <orb.Database> || None
        """
        self._database = database
    
    def setEditorFlags(self, flags):
        """
        Sets the editor options for this record.
        
        :param      flags | <XOrbTreeWidget.EditorFlags>
        """
        self._editorFlags = flags
    
    def setEditOnDoubleClick(self, state):
        """
        Sets whether or not double clicking on an a record will cause editing
        to occur.
        
        :param      state | <bool>
        """
        self._editOnDoubleClick = state
    
    def setGroupBy(self, groupBy):
        """
        Sets the grouping information for this tree.
        
        :param      groupBy | [<str> group level, ..] || None
        """
        if groupBy and not type(groupBy) in (list, tuple):
            groupBy = [nativestring(groupBy)]
        elif not groupBy:
            groupBy = None
        
        self._groupBy = groupBy
    
    def setGroupingActive(self, state, autoRefresh=False):
        """
        Sets whether or not grouping is enabled for this system.
        
        :param      state | <bool>
        """
        self._groupingActive = state
        
        self.setRootIsDecorated(state)
        
        if autoRefresh:
            self.refresh()
    
    def setColumnOrderName(self, columnName, orderName):
        """
        Sets the database name to use when ordering this widget by the 
        given column.  When set, this will trigger a server side reorder
        of information rather than a client side reorder if the information
        displayed is paged - as it will modify what to show for this page
        based on the order.
        
        :param      columnName | <str>
                    orderName  | <str>
        """
        self._columnOrderNames[nativestring(columnName)] = nativestring(orderName)
    
    def setHierarchyLookup(self, columnName, tableType=None):
        """
        Sets the hierarchy lookup for the inputed table type and column.
        
        :param      columnName | <str>
                    tableType  | <subclass of Table>
        """
        if tableType:
            tableType = self.tableType()
        self._hierarchyLookup[tableType] = (tableType, columnName)
    
    def setLoaderThreshold(self, threshold):
        self._loaderThreshold = threshold
    
    def setOrder(self, order):
        """
        Sets the order for the query to the inputed order.
        
        :param      order | [(<str> columName, <str> order), ..]
        """
        self._order = order
    
    def setPaged(self, state):
        """
        Sets whether or not the contents of this tree are going to be
        paged.
        
        :param      state | <bool>
        """
        self._paged = state
    
    @Slot(int)
    def setPageSize(self, pageSize):
        """
        Sets the page size for this widget.  If the page size is set to -1,
        then there is no sizing and all records are displayed.
        
        :return     <int>
        """
        if pageSize == self._pageSize:
            return
        
        self._pageSize = pageSize
        self.setPaged(pageSize > 0)
    
    def setPreloadColumns(self, columns):
        """
        Sets the list of columns that will be automatically preloaded 
        during the lookup thread.
        
        :return     [<str>, ..]
        """
        self._preloadColumns = columns
    
    def setPopupEditing(self, state):
        """
        Sets whether or not to use popup editing for this widget.  When True,
        a popup widget will be used when the user chooses to edit a record,
        either via right-click or from a double click action.
        
        :param      state | <bool>
        """
        self._popupEditing = state
    
    @Slot(object)
    def setQuery(self, query, autoRefresh=False):
        """
        Sets the query instance for this tree widget to the inputed query.
        
        :param      query | <orb.Query>
        """
        self._query             = query
        self._currentRecordSet  = None
        
        if autoRefresh:
            self.refreshQueryRecords()
            self.refresh()
    
    def setQueryAction(self, action):
        """
        Sets the action that should be taken when joining together
        a query assigned to this tree with a base record set that may or
        may not already have a query associated with it.
        
        :param      action | <XOrbTreeWidget.QueryAction>
        """
        self._queryAction = action
    
    def setRecords(self, records):
        """
        Manually sets the list of records that will be displayed in this tree.
        
        This is a shortcut method to creating a RecordSet with a list of records
        and assigning it to the tree.
        
        :param      records | [<orb.Table>, ..]
        """
        self._searchTerms = ''
        
        if not isinstance(records, RecordSet):
            records = RecordSet(records)
        self.setRecordSet(records)
    
    def setRecordEditor(self, editorClass, tableType=None):
        """
        Sets the record editor for this tree based on the given table type.
        If no tableType is supplied, then the assigned table type will be
        used.
        
        :param      editorClass | <subclass of XOrbRecordWidget>
                    tableType   | <subclass of orb.Table> || None
        """
        if tableType is None:
            tableType = editorClass.tableType()
        
        self._recordEditors[tableType] = editorClass
    
    def setRecordGroupClass(self, groupClass, typ=None):
        """
        Sets the record group class that will be used for this tree instance.
        If the optional typ is supplied then it will use that specific group
        class for group entries of that given type.
        
        :param      groupClass | <subclass of XOrbGroupItem>
                    typ        | <object>
        """
        self._recordGroupClass[typ] = groupClass
    
    def setRecordItemClass(self, itemClass, tableType=None):
        """
        Sets the record item class that will be used for this tree instance.
        You can specify different class types per table type, with the default
        None type being used for by any table types it cannot find.
        
        :param      itemClass | <subclass of XOrbRecordItem>
                    tableType | <subclass of orb.Table>
        """
        self._recordItemClass[tableType] = itemClass
    
    @Slot(object)
    def setRecordSet(self, recordSet):
        """
        Defines the record set that will be used to lookup the information for
        this tree.
        
        :param      records | [<Table>, ..] || None
        """
        if not self.tableType():
            self.setTableType(recordSet.table())
        
        self._currentRecordSet = None
        self._recordSet = recordSet
        
        try:
            self.setDatabase(recordSet.database())
        except AttributeError:
            pass
        
        if not self.signalsBlocked():
            self.refresh()
            self.recordsChanged.emit()
    
    def setSearchableRecords(self, records):
        """
        Sets the records that will be used as the base search set.  If no
        search records are defined then the default records will be returned.
        
        :param      records | <orb.RecordSet>
        """
        self._searchableRecords = records
    
    def setSearchedRecords(self, records):
        """
        Sets a record set based off of an external search.  Searched results
        provide an overridden entry to the tree widget, by passing the
        grouping mechanism.
        
        :param      records | <orb.RecordSet>
        
        :return     <bool> | records
        """
        self._searchTerms = 'EXTERNAL_SEARCH'
        self._currentRecordSet = records
        
        # update widget and notify any listeners
        if not self.signalsBlocked():
            self.refresh()
            self.recordsChanged.emit()
        return True
    
    def setShowAddEntryItem(self, state):
        """
        Sets whether or not to have an 'Add New Record...' item at the
        bottom of the entries.
        
        :param      state | <bool>
        """
        self._showAddEntryItem = state
    
    def setSpecifiedColumns(self, columns):
        """
        Sets the specified columns for this tree widget.
        
        :param      columns | [<orb.Column>, ..] || [<str>, ..] || None
        """
        self._specifiedColumns = columns
        self._specifiedColumnsOnly = columns is not None
    
    def setSpecifiedColumnsOnly(self, state):
        """
        Sets whether or not only the columns specified within this tree
        should be looked up.
        
        :param      state | <bool>
        """
        self._specifiedColumnsOnly = state
    
    @Slot(object)
    def setTableType(self, tableType):
        """
        Defines the table class type that this tree will be displaying.
        
        :param      table | <subclass of orb.Table>
        """
        if tableType == self._tableType:
            return
        
        # clear all the information
        blocked = self.signalsBlocked()
        
        self.blockAllSignals(True)
        
        # only clear if necessary
        if self._tableType:
            self.clearAll()
        
        # update the table type data
        self._tableType = tableType
        
        if tableType:
            self._tableTypeName = tableType.__name__
        else:
            self._tableTypeName = ''
            
        self.initializeColumns()
        self.blockAllSignals(blocked)
        
        if not self.signalsBlocked():
            self.tableTypeChanged.emit()
            self.recordsChanged.emit()
    
    @Slot(str)
    def setTableTypeName(self, tableTypeName):
        """
        Defines the table type name that this tree will be displaying.
        
        :param      tableTypeName | <str>
        """
        self._tableTypeName = tableTypeName
        if ( not Orb ):
            return
        
        self.setTableType(Orb.instance().model(nativestring(tableTypeName)))
    
    @Slot(object)
    def setTableSchema(self, schema):
        """
        Sets the table schema for this tree to the inputed schema.
        
        :param      schema | <orb.TableSchema>
        """
        if schema:
            self.setTableType(schema.model())
    
    def setThreadEnabled(self, state):
        """
        Sets whether or not threading should be enabled for this widget.  
        Actual threading will be determined by both this property, and whether
        or not the active ORB backend supports threading.
        
        :param      state | <bool>
        """
        self._threadEnabled = state
    
    def setUseDefaultKeystrokes(self, state):
        """
        Sets whether or not this widget should be automatically tagged
        to delete the selected records when the user hits delete.
        
        :param      state | <bool>
        """
        self._useDefaultKeystrokes = state
    
    def setUseGroupStyle(self, state):
        """
        Sets whether or not the first group should draw with the
        grouping style or not.
        
        :param     state | <bool>
        """
        self._useGroupStyle = state
        if state:
            self.setRootIsDecorated(False)
    
    def setUserGroupingEnabled(self, state=True):
        """
        Sets whether or not to allow users to control the grouping options
        for the tree widget.
        
        :param      state | <bool>
        """
        self._userGroupingEnabled = state
    
    def setUseLoader(self, state):
        """
        Sets whether or not the loading widget whould be displayed.
        
        :param      state | <bool>
        """
        self._useLoader = state

    def setupHeaderMenu(self, menu, index):
        """
        Updates the header right-click menu to include grouping options if
        desired.
        
        :param      menu  | <QMenu>
                    index | <int>
        """
        if not self.userGroupingEnabled():
            return False
        
        first_action = menu.actions()[1]
        column = self.columnOf(index)
        
        enable_action = QAction(menu)
        enable_action.setText('Enable Grouping')
        
        disable_action = QAction(menu)
        disable_action.setText('Disable Grouping')
        
        quick_action = QAction(menu)
        quick_action.setText('Group by "%s"' % column)
        
#        adv_action = QAction(menu)
#        adv_action.setText('More Grouping Options...')
        
        menu.insertSeparator(first_action)
        menu.insertAction(first_action, enable_action)
        menu.insertAction(first_action, disable_action)
        menu.insertSeparator(first_action)
        menu.insertAction(first_action, quick_action)
#        menu.insertAction(first_action, adv_action)
        
        quick_action.triggered.connect(self.groupByHeaderIndex)
#        adv_action.triggered.connect(self.showAdvancedGroupingOptions)
        enable_action.triggered.connect(self.activateGrouping)
        disable_action.triggered.connect(self.deactivateGrouping)
        return True

    def showAddEntryItem(self):
        """
        Returns whether or not a 'Add New Record...' item will be displayed
        at the end of the entries.  This is useful when using the orb tree
        widget for adding and editing entries through a grid view.
        
        :return     <bool>
        """
        return self._showAddEntryItem

    def showAdvancedGroupingOptions(self):
        """
        Shows the advanced grouping options for the grid edit.
        """
        pass

    def showMenu(self, pos):
        """
        Creates a new menu for this widget and displays it.
        
        :param      pos | <QPoint>
        """
        glbl_pos = self.viewport().mapToGlobal(pos)
        
        # lookup the specific item at the given position
        item = self.itemAt(pos)
        selected = self.selectedRecords()
        
        if not self._recordEditors:
            return
        
        if item and not isinstance(item, XOrbRecordItem):
            return
        
        menu = QMenu(self)
        acts = {}
        
        # modify a particular item
        if item:
            if self.editorFlags() & XOrbTreeWidget.EditorFlags.Edit:
                record = item.record()
                editor = self.recordEditor(type(record))
                
                if editor:
                    name = record.schema().displayName()
                    act = menu.addAction('Edit {}...'.format(name))
                    act.setIcon(QIcon(resources.find('img/edit.png')))
                    acts[act] = (editor, 'edit', record)
        
        # add items
        if self.editorFlags() & XOrbTreeWidget.EditorFlags.Create:
            menu.addSeparator()
            
            typs = self._recordEditors.keys()
            typs.sort(key=lambda x: x.schema().displayName())
            
            for typ in typs:
                name = typ.schema().displayName()
                act  = menu.addAction('Add {}...'.format(name))
                act.setIcon(QIcon(resources.find('img/add.png')))
                acts[act] = (self._recordEditors[typ], 'create', None)
        
        # remove selected items
        if selected and self.editorFlags() & XOrbTreeWidget.EditorFlags.Remove:
            menu.addSeparator()
            
            act = menu.addAction('Remove Selected Records')
            act.setIcon(QIcon(resources.find('img/remove.png')))
            acts[act] =(None, 'remove', selected)
        
        if not acts:
            return
        
        act = menu.exec_(glbl_pos)
        
        editor, action, record = acts.get(act, (None, None, None))
        
        # create a new record
        if action == 'create':
            record = editor.create(autoCommit=False)
            if record:
                self.recordCreated.emit(record)
                record.commit()
                self.refresh()
        
        # edit an existing record
        elif action == 'edit':
            self.editRecord(record, glbl_pos)
        
        # remove selected records
        elif action == 'remove':
            title = 'Remove Records'
            msg = 'Are you sure you want to remove these records?'
            btns = QMessageBox.Yes | QMessageBox.No
            ans = QMessageBox.information(self.window(), title, msg, btns)
            if ans == QMessageBox.Yes:
                self.recordsRemoved.emit(selected)
                if RecordSet(selected).remove():
                    self.refresh()
    
    def sortByColumn(self, index, direction):
        """
        Sorts the data for this widget based on the inputed index & direction.
        
        :param      index | <int>
                    direction | <Qt.SortOrder
        """
        if self.isPaged() and not self.isFullyLoaded():
            self.reorder(index, direction)
        else:
            super(XOrbTreeWidget, self).sortByColumn(index, direction)
    
    def specifiedColumns(self):
        """
        Returns the list of columns that are specified based on the column
        view for this widget.
        
        :return     [<orb.Column>, ..]
        """
        columns = []
        table = self.tableType()
        schema = table.schema()
        
        if self._specifiedColumns is not None:
            colnames = self._specifiedColumns
        else:
            colnames = self.columns()
        
        for colname in colnames:
            if isinstance(colname, Column):
                columns.append(colname)
            else:
                col = schema.column(colname)
                if col and not col.isProxy():
                    columns.append(col)
        
        return columns
    
    def specifiedColumnsOnly(self):
        """
        Returns whether or not only the specified columns should be
        loaded up and returned.
        
        :return     <bool>
        """
        return self._specifiedColumnsOnly
    
    def tableType(self):
        """
        Returns the table class type that is linked with this tree widget.
        
        :return     <subclass of orb.Table>
        """
        return self._tableType
    
    def tableTypeName(self):
        """
        Returns the table type name for this instance.
        
        :return     <str>
        """
        return self._tableTypeName
    
    @Slot()
    def toggleGroupingActive(self):
        """
        Toggles whether or not grouping is enabled.
        """
        self.setGroupingActive(not self.isGroupingActive())
    
    def toggleSelectedItemState(self, state):
        """
        Toggles the selection for the inputed state.
        
        :param      state | <XOrbRecordItem.State>
        """
        items = self.selectedItems()
        for item in items:
            if ( item.hasRecordState(state) ):
                item.removeRecordState(state)
            else:
                item.addRecordState(state)
    
    def toggleSelectedRemovedState(self):
        """
        Toggles the selection for the removed state.
        """
        self.toggleSelectedItemState(XOrbRecordItem.State.Removed)
    
    def updateItemIcon(self, item):
        """
        Updates the items icon based on its state.
        
        :param      item | <QTreeWidgetItem>
        """
        # update the column width
        self.setUpdatesEnabled(False)
        colwidth = self.columnWidth(0)
        self.resizeColumnToContents(0)
        new_colwidth = self.columnWidth(0)
        
        if new_colwidth < colwidth:
            self.setColumnWidth(0, colwidth)
        self.setUpdatesEnabled(True)
    
    def useDefaultKeystrokes(self):
        """
        Returns whether or not the delete key will be used to automatically
        tag selected records for removal.
        
        :return     <bool>
        """
        return self._useDefaultKeystrokes
    
    def useGroupStyle(self):
        """
        Returns whether or not the first group should draw with the
        grouping style or not.
        
        :return     <bool>
        """
        return self._useGroupStyle
    
    def userGroupingEnabled(self):
        """
        Returns whether or not the user can control the grouping levels
        for this tree widget.
        
        :return     <bool>
        """
        return self._userGroupingEnabled
    
    def useLoader(self):
        """
        Returns whether or not to use the loading widget.
        
        :return     <bool>
        """
        return self._useLoader
    
    def waitUntilFinished(self):
        """
        Waits until this tree has finished its asynchronous load.  This will
        pause the main thread until the loading is complete.
        """
        if self._worker: self._worker.waitUntilFinished()
    
    def worker(self):
        """
        Returns the worker associated with this tree widget.
        
        :return     <projexui.xorblookupworker.XOrbLookupWorker>
        """
        if self._worker is None:
            self._worker = XOrbLookupWorker(self.isThreadEnabled())
            
            # create worker connections
            self.loadRequested.connect(self._worker.loadRecords)
            self.loadBatchRequested.connect(self._worker.loadBatch)
            self.loadColumnsRequested.connect(self._worker.loadColumns)
            
            self._worker.loadingStarted.connect(self.markLoadingStarted)
            self._worker.loadingFinished.connect(self.markLoadingFinished)
            self._worker.loadedRecords[object].connect(self._loadRecords)
            self._worker.loadedRecords[object, object].connect(self._loadRecords)
            self._worker.loadedGroup.connect(self.createGroupItem)
            self._worker.columnLoaded.connect(self._loadColumns)
            self._worker.connectionLost.connect(self._connectionLost)
            
        return self._worker
    
    @staticmethod
    def dataHasRecords(mimeData):
        """
        Returns whether or not the inputed mime data has orb record
        data.
        
        :param      mimeData | <QMimeData>
        
        :return     <bool>
        """
        return mimeData.hasFormat('application/x-orb-records')
    
    @staticmethod
    def dataRestoreRecords(mimeData):
        """
        Extracts the records from the inputed drag & drop mime data information.
        This will lookup the models based on their primary key information and
        generate the element class.
        
        :param      mimeData | <QMimeData>
        
        :return     [<orb.Table>, ..]
        """
        if not mimeData.hasFormat('application/x-orb-records'):
            return []
        
        from orb import Orb
        
        repros = nativestring(mimeData.data('application/x-orb-records'))
        repros = repros.split(';')
        
        output =[]
        for repro in repros:
            cls, pkey = re.match('^(\w+)\((.*)\)$', repro).groups()
            pkey = eval(pkey)
            
            model = Orb.instance().model(cls)
            if not model:
                continue
            
            record = model(pkey)
            if record.isRecord():
                output.append(record)
        
        return output
    
    @staticmethod
    def dataStoreRecords(mimeData, record_items):
        """
        Adds the records to the inputed mime data as a text representation
        under the application/x-orb-records
        
        :param      mimeData | [<orb.Table>, ..]
        """
        record_data = []
        for record_item in record_items:
            record = record_item.record()
            if record is None:
                continue
            
            repro = '%s(%s)' % (record.schema().name(), record.primaryKey())
            record_data.append(repro)
        
        if not record_data:
            return
        
        record_data = ';'.join(record_data)
        mimeData.setData('application/x-orb-records', QByteArray(record_data))
        
        # store the associated mime data for the individual record
        if len(record_items) == 1:
            for format, value in record_items[0].dragData().items():
                mimeData.setData(format, QByteArray(value))
    
    x_editOnDoubleClick = Property(bool, editOnDoubleClick, setEditOnDoubleClick)
    x_loaderThreshold = Property(int, loaderThreshold, setLoaderThreshold)
    x_popupEditing = Property(bool, popupEditing, setPopupEditing)
    x_paged = Property(bool, isPaged, setPaged)
    x_pageSize = Property(int, pageSize, setPageSize)
    x_autoloadPages = Property(bool, autoloadPages, setAutoloadPages)
    x_showAddEntryItem = Property(bool, showAddEntryItem, setShowAddEntryItem)
    x_specifiedColumnsOnly = Property(bool, specifiedColumnsOnly, setSpecifiedColumnsOnly)
    x_tableTypeName = Property(str, tableTypeName, setTableTypeName)
    x_threadEnabled     = Property(bool, isThreadEnabled, setThreadEnabled)
    x_useGroupStyle = Property(bool, useGroupStyle, setUseGroupStyle)
    x_useLoader = Property(bool, useLoader, setUseLoader)
    x_userGroupingEnabled = Property(bool, userGroupingEnabled, setUserGroupingEnabled)
    x_useDefaultKeystrokes = Property(bool,
                                      useDefaultKeystrokes,
                                      setUseDefaultKeystrokes)