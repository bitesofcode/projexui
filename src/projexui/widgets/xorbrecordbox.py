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

from projex.text import nativestring as nstr

from projexui.qt import Signal,\
                        Property,\
                        Slot,\
                        wrapVariant,\
                        unwrapVariant,\
                        SIGNAL

from projexui.qt.QtGui import QApplication
from projexui.qt.QtCore import QPoint, Qt, QObject, QTimer
from projexui.widgets.xcombobox import XComboBox
from projexui.widgets.xloaderwidget import XLoaderWidget
from projexui.widgets.xtreewidget import XTreeWidget
from projexui.widgets.xorbtreewidget import XOrbRecordItem
from projexui.xorblookupworker import XOrbLookupWorker

logger = logging.getLogger(__name__)

try:
    from orb import Orb, RecordSet, Column, Table
except ImportError:
    logger.warning('Could not import the ORB library.')
    Orb = None

#----------------------------------------------------------------------

class XOrbRecordBox(XComboBox):
    __designer_group__ = 'ProjexUI - ORB'
    
    """ Defines a combo box that contains records from the ORB system. """
    loadRequested = Signal(object)
    
    loadingStarted = Signal()
    loadingFinished = Signal()
    currentRecordChanged = Signal(object)
    currentRecordEdited = Signal(object)
    initialized = Signal()
    
    def __init__(self, parent=None):
        # needs to be defined before the base class is initialized or the
        # event filter won't work
        self._treePopupWidget   = None
        
        super(XOrbRecordBox, self).__init__( parent )
        
        # define custom properties
        self._currentRecord     = None # only used while loading
        self._changedRecord     = -1
        
        self._tableTypeName     = ''
        self._tableLookupIndex  = ''
        self._baseHints         = ('', '')
        self._batchSize         = 100
        self._tableType         = None
        self._order             = None
        self._query             = None
        self._iconMapper        = None
        self._labelMapper       = nstr
        self._required          = True
        self._loaded            = False
        self._showTreePopup     = False
        self._autoInitialize    = False
        self._threadEnabled     = True
        self._specifiedColumns  = None
        self._specifiedColumnsOnly = False
        
        # define an editing timer
        self._editedTimer = QTimer(self)
        self._editedTimer.setSingleShot(True)
        self._editedTimer.setInterval(500)
        
        # create threading options
        self._worker = None
        self._workerThread = None
        
        # create connections
        edit = self.lineEdit()
        if edit:
            edit.textEntered.connect(self.assignCurrentRecord)
            edit.editingFinished.connect(self.emitCurrentRecordEdited)
            edit.returnPressed.connect(self.emitCurrentRecordEdited)
        
        self.currentIndexChanged.connect(self.emitCurrentRecordChanged)
        self.currentIndexChanged.connect(self.startEditTimer)
        self._editedTimer.timeout.connect(self.emitCurrentRecordEdited)
        QApplication.instance().aboutToQuit.connect(self._cleanupWorker)
    
    def _cleanupWorker(self):
        if not self._workerThread:
            return
        
        thread = self._workerThread
        worker = self._worker
        
        self._workerThread = None
        self._worker = None
        
        worker.deleteLater()
        
        thread.finished.connect(thread.deleteLater)
        thread.quit()
        thread.wait()
    
    def addRecord(self, record):
        """
        Adds the given record to the system.
        
        :param      record | <str>
        """
        label_mapper    = self.labelMapper()
        icon_mapper     = self.iconMapper()
        
        self.addItem(label_mapper(record))
        self.setItemData(self.count() - 1, wrapVariant(record), Qt.UserRole)
        
        # load icon
        if icon_mapper:
            self.setItemIcon(self.count() - 1, icon_mapper(record))
        
        if self.showTreePopup():
            XOrbRecordItem(self.treePopupWidget(), record)
    
    def addRecords(self, records):
        """
        Adds the given record to the system.
        
        :param      records | [<orb.Table>, ..]
        """
        label_mapper    = self.labelMapper()
        icon_mapper     = self.iconMapper()
        
        # create the items to display
        tree = None
        if self.showTreePopup():
            tree = self.treePopupWidget()
            tree.blockSignals(True)
            tree.setUpdatesEnabled(False)
        
        # add the items to the list
        start = self.count()
        self.addItems(map(label_mapper, records))
        
        # update the item information
        for i, record in enumerate(records):
            index = start + i
            
            self.setItemData(index, wrapVariant(record), Qt.UserRole)
            
            if icon_mapper:
                self.setItemIcon(index, icon_mapper(record))
            
            if tree:
                XOrbRecordItem(tree, record)
        
        if tree:
            tree.blockSignals(False)
            tree.setUpdatesEnabled(True)
    
    def addRecordsFromThread(self, records):
        """
        Adds the given record to the system.
        
        :param      records | [<orb.Table>, ..]
        """
        label_mapper    = self.labelMapper()
        icon_mapper     = self.iconMapper()
        
        tree = None
        if self.showTreePopup():
            tree = self.treePopupWidget()
        
        # add the items to the list
        start = self.count()
        
        # update the item information
        blocked = self.signalsBlocked()
        self.blockSignals(True)
        for i, record in enumerate(records):
            index = start + i
            self.addItem(label_mapper(record))
            self.setItemData(index, wrapVariant(record), Qt.UserRole)
            
            if icon_mapper:
                self.setItemIcon(index, icon_mapper(record))
            
            if record == self._currentRecord:
                self.setCurrentIndex(self.count() - 1)
            
            if tree:
                XOrbRecordItem(tree, record)
        self.blockSignals(blocked)
    
    def acceptRecord(self, item):
        """
        Closes the tree popup and sets the current record.
        
        :param      record | <orb.Table>
        """
        record = item.record()
        self.treePopupWidget().close()
        self.setCurrentRecord(record)
    
    def assignCurrentRecord(self, text):
        """
        Assigns the current record from the inputed text.
        
        :param      text | <str>
        """
        if self.showTreePopup():
            item = self._treePopupWidget.currentItem()
            if item:
                self._currentRecord = item.record()
            else:
                self._currentRecord = None
            return
        
        # look up the record for the given text
        if text:
            index = self.findText(text)
        elif self.isRequired():
            index = 0
        else:
            index = -1
        
        # determine new record to look for
        record = self.recordAt(index)
        if record == self._currentRecord:
            return
        
        # set the current index and record for any changes
        self._currentRecord = record
        self.setCurrentIndex(index)
    
    def autoInitialize(self):
        """
        Returns whether or not this record box should auto-initialize its
        records.
        
        :return     <bool>
        """
        return self._autoInitialize
    
    def batchSize(self):
        """
        Returns the batch size to use when processing this record box's list
        of entries.
        
        :return     <int>
        """
        return self._batchSize
    
    def checkedRecords( self ):
        """
        Returns a list of the checked records from this combo box.
        
        :return     [<orb.Table>, ..]
        """
        indexes = self.checkedIndexes()
        return map(self.recordAt, indexes)
    
    def currentRecord( self ):
        """
        Returns the record found at the current index for this combo box.
        
        :rerturn        <orb.Table> || None
        """
        if self._currentRecord is None and self.isRequired():
            self._currentRecord = self.recordAt(self.currentIndex())
        return self._currentRecord
    
    def dragEnterEvent(self, event):
        """
        Listens for query's being dragged and dropped onto this tree.
        
        :param      event | <QDragEnterEvent>
        """
        data = event.mimeData()
        if data.hasFormat('application/x-orb-table') and \
           data.hasFormat('application/x-orb-query'):
            tableName = self.tableTypeName()
            if nstr(data.data('application/x-orb-table')) == tableName:
                event.acceptProposedAction()
                return
        elif data.hasFormat('application/x-orb-records'):
            event.acceptProposedAction()
            return
        
        super(XOrbRecordBox, self).dragEnterEvent(event)
    
    def dragMoveEvent(self, event):
        """
        Listens for query's being dragged and dropped onto this tree.
        
        :param      event | <QDragEnterEvent>
        """
        data = event.mimeData()
        if data.hasFormat('application/x-orb-table') and \
           data.hasFormat('application/x-orb-query'):
            tableName = self.tableTypeName()
            if nstr(data.data('application/x-orb-table')) == tableName:
                event.acceptProposedAction()
                return
        elif data.hasFormat('application/x-orb-records'):
            event.acceptProposedAction()
            return
        
        super(XOrbRecordBox, self).dragMoveEvent(event)
    
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
            if nstr(data.data('application/x-orb-table')) == tableName:
                data = nstr(data.data('application/x-orb-query'))
                query = Q.fromXmlString(data)
                self.setQuery(query)
                return
        
        elif self.tableType() and data.hasFormat('application/x-orb-records'):
            from projexui.widgets.xorbtreewidget import XOrbTreeWidget
            records = XOrbTreeWidget.dataRestoreRecords(data)
            
            for record in records:
                if isinstance(record, self.tableType()):
                    self.setCurrentRecord(record)
                    return
        
        super(XOrbRecordBox, self).dropEvent(event)
    
    def emitCurrentRecordChanged(self):
        """
        Emits the current record changed signal for this combobox, provided \
        the signals aren't blocked.
        """
        record = unwrapVariant(self.itemData(self.currentIndex(), Qt.UserRole))
        if not Table.recordcheck(record):
            record = None
        
        self._currentRecord = record
        if not self.signalsBlocked():
            self._changedRecord = record
            self.currentRecordChanged.emit(record)
    
    def emitCurrentRecordEdited(self):
        """
        Emits the current record edited signal for this combobox, provided the
        signals aren't blocked and the record has changed since the last time.
        """
        if self._changedRecord == -1:
            return
        
        if self.signalsBlocked():
            return
        
        record = self._changedRecord
        self._changedRecord = -1
        self.currentRecordEdited.emit(record)
    
    def eventFilter(self, object, event):
        """
        Filters events for the popup tree widget.
        
        :param      object | <QObject>
                    event  | <QEvent>
        
        :retuen     <bool> | consumed
        """
        edit = self.lineEdit()
        
        if not (object and object == self._treePopupWidget):
            return super(XOrbRecordBox, self).eventFilter(object, event)
        
        elif event.type() == event.Show:
            object.resizeToContents()
            object.horizontalScrollBar().setValue(0)
        
        elif edit and event.type() == event.KeyPress:
            # accept lookup
            if event.key() in (Qt.Key_Enter,
                               Qt.Key_Return,
                               Qt.Key_Tab,
                               Qt.Key_Backtab):
                
                item = object.currentItem()
                text = edit.text()
                
                if not text:
                    record = None
                    item = None
                
                elif isinstance(item, XOrbRecordItem):
                    record = item.record()
                
                if record and item.isSelected() and not item.isHidden():
                    self.hidePopup()
                    self.setCurrentRecord(record)
                    event.accept()
                    return True
                
                else:
                    self.setCurrentRecord(None)
                    self.hidePopup()
                    edit.setText(text)
                    edit.keyPressEvent(event)
                    event.accept()
                    return True
                
            # cancel lookup
            elif event.key() == Qt.Key_Escape:
                text = edit.text()
                self.setCurrentRecord(None)
                edit.setText(text)
                self.hidePopup()
                event.accept()
                return True
            
            # update the search info
            else:
                edit.keyPressEvent(event)
        
        elif edit and event.type() == event.KeyRelease:
            edit.keyReleaseEvent(event)
        
        elif edit and event.type() == event.MouseButtonPress:
            local_pos = object.mapFromGlobal(event.globalPos())
            in_widget = object.rect().contains(local_pos)
            
            if not in_widget:
                text = edit.text()
                self.setCurrentRecord(None)
                edit.setText(text)
                self.hidePopup()
                event.accept()
                return True
            
        return super(XOrbRecordBox, self).eventFilter(object, event)
    
    def focusNextChild(self, event):
        edit = self.lineEdit()
        if not self.isLoading() and edit:
            self.assignCurrentRecord(edit.text())
        
        return super(XOrbRecordBox, self).focusNextChild(event)
    
    def focusNextPrevChild(self, event):
        edit = self.lineEdit()
        if not self.isLoading() and edit:
            self.assignCurrentRecord(edit.text())
        
        return super(XOrbRecordBox, self).focusNextPrevChild(event)
    
    def focusInEvent(self, event):
        """
        When this widget loses focus, try to emit the record changed event
        signal.
        """
        self._changedRecord = -1
        super(XOrbRecordBox, self).focusInEvent(event)
    
    def focusOutEvent(self, event):
        """
        When this widget loses focus, try to emit the record changed event
        signal.
        """
        edit = self.lineEdit()
        if not self.isLoading() and edit:
            self.assignCurrentRecord(edit.text())
        
        super(XOrbRecordBox, self).focusOutEvent(event)
    
    def hidePopup(self):
        """
        Overloads the hide popup method to handle when the user hides
        the popup widget.
        """
        if self._treePopupWidget and self.showTreePopup():
            self._treePopupWidget.close()
        
        super(XOrbRecordBox, self).hidePopup()
    
    def iconMapper( self ):
        """
        Returns the icon mapping method to be used for this combobox.
        
        :return     <method> || None
        """
        return self._iconMapper
    
    def isLoading(self):
        """
        Returns whether or not this combobox is loading records.
        
        :return     <bool>
        """
        try:
            return self._worker.isRunning()
        except AttributeError:
            return False
    
    def isRequired( self ):
        """
        Returns whether or not this combo box requires the user to pick a
        selection.
        
        :return     <bool>
        """
        return self._required
    
    def isThreadEnabled(self):
        """
        Returns whether or not threading is enabled for this combo box.
        
        :return     <bool>
        """
        return self._threadEnabled
    
    def labelMapper( self ):
        """
        Returns the label mapping method to be used for this combobox.
        
        :return     <method> || None
        """
        return self._labelMapper
    
    @Slot(object)
    def lookupRecords(self, record):
        """
        Lookups records based on the inputed record.  This will use the 
        tableLookupIndex property to determine the Orb Index method to
        use to look up records.  That index method should take the inputed
        record as an argument, and return a list of records.
        
        :param      record | <orb.Table>
        """
        table_type = self.tableType()
        if not table_type:
            return
        
        index = getattr(table_type, self.tableLookupIndex(), None)
        if not index:
            return
        
        self.setRecords(index(record))
    
    def markLoadingStarted(self):
        """
        Marks this widget as loading records.
        """
        if self.isThreadEnabled():
            XLoaderWidget.start(self)
        
        if self.showTreePopup():
            tree = self.treePopupWidget()
            tree.setCursor(Qt.WaitCursor)
            tree.clear()
            tree.setUpdatesEnabled(False)
            tree.blockSignals(True)
            
            self._baseHints = (self.hint(), tree.hint())
            tree.setHint('Loading records...')
            self.setHint('Loading records...')
        else:
            self._baseHints = (self.hint(), '')
            self.setHint('Loading records...')
        
        self.setCursor(Qt.WaitCursor)
        self.blockSignals(True)
        self.setUpdatesEnabled(False)
        
        # prepare to load
        self.clear()
        use_dummy = not self.isRequired() or self.isCheckable()
        if use_dummy:
            self.addItem('')
        
        self.loadingStarted.emit()
    
    def markLoadingFinished(self):
        """
        Marks this widget as finished loading records.
        """
        XLoaderWidget.stop(self, force=True)
        
        hint, tree_hint = self._baseHints
        self.setHint(hint)
        
        # set the tree widget
        if self.showTreePopup():
            tree = self.treePopupWidget()
            tree.setHint(tree_hint)
            tree.unsetCursor()
            tree.setUpdatesEnabled(True)
            tree.blockSignals(False)
        
        self.unsetCursor()
        self.blockSignals(False)
        self.setUpdatesEnabled(True)
        self.loadingFinished.emit()
    
    def order(self):
        """
        Returns the ordering for this widget.
        
        :return     [(<str> column, <str> asc|desc, ..] || None
        """
        return self._order
    
    def query( self ):
        """
        Returns the query used when querying the database for the records.
        
        :return     <Query> || None
        """
        return self._query
    
    def records( self ):
        """
        Returns the record list that ist linked with this combo box.
        
        :return     [<orb.Table>, ..]
        """
        records = []
        for i in range(self.count()):
            record = self.recordAt(i)
            if record:
                records.append(record)
        return records
    
    def recordAt(self, index):
        """
        Returns the record at the inputed index.
        
        :return     <orb.Table> || None
        """
        return unwrapVariant(self.itemData(index, Qt.UserRole))
    
    def refresh(self, records):
        """
        Refreshs the current user interface to match the latest settings.
        """
        self._loaded = True
        
        if self.isLoading():
            return
        
        # load the information
        if RecordSet.typecheck(records):
            table = records.table()
            self.setTableType(table)
            
            if self.order():
                records.setOrder(self.order())
            
            # load specific data for this record box
            if self.specifiedColumnsOnly():
                records.setColumns(map(lambda x: x.name(),
                                       self.specifiedColumns()))
            
            # load the records asynchronously
            if self.isThreadEnabled() and table:
                try:
                    thread_enabled = table.getDatabase().isThreadEnabled()
                except AttributeError:
                    thread_enabled = False
                
                if thread_enabled:
                    # ensure we have a worker thread running
                    self.worker()
                    
                    # assign ordering based on tree table
                    if self.showTreePopup():
                        tree = self.treePopupWidget()
                        if tree.isSortingEnabled():
                            col = tree.sortColumn()
                            colname = tree.headerItem().text(col)
                            column = table.schema().column(colname)
                            
                            if column:
                                if tree.sortOrder() == Qt.AscendingOrder:
                                    sort_order = 'asc'
                                else:
                                    sort_order = 'desc'
                                
                                records.setOrder([(column.name(), sort_order)])
                    
                    self.loadRequested.emit(records)
                    return
        
        # load the records synchronously
        self.loadingStarted.emit()
        curr_record = self.currentRecord()
        self.blockSignals(True)
        self.setUpdatesEnabled(False)
        self.clear()
        use_dummy = not self.isRequired() or self.isCheckable()
        if use_dummy:
            self.addItem('')
        self.addRecords(records)
        self.setUpdatesEnabled(True)
        self.blockSignals(False)
        self.setCurrentRecord(curr_record)
        self.loadingFinished.emit()
    
    def setAutoInitialize(self, state):
        """
        Sets whether or not this combo box should auto initialize itself
        when it is shown.
        
        :param      state | <bool>
        """
        self._autoInitialize = state
    
    def setBatchSize(self, size):
        """
        Sets the batch size of records to look up for this record box.
        
        :param      size | <int>
        """
        self._batchSize = size
        try:
            self._worker.setBatchSize(size)
        except AttributeError:
            pass
    
    def setCheckedRecords( self, records ):
        """
        Sets the checked off records to the list of inputed records.
        
        :param      records | [<orb.Table>, ..]
        """
        QApplication.sendPostedEvents(self, -1)
        indexes = []
        
        for i in range(self.count()):
            record = self.recordAt(i)
            if record is not None and record in records:
                indexes.append(i)
        
        self.setCheckedIndexes(indexes)
    
    def setCurrentRecord(self, record, autoAdd=False):
        """
        Sets the index for this combobox to the inputed record instance.
        
        :param      record      <orb.Table>
        
        :return     <bool> success
        """
        if record is not None and not Table.recordcheck(record):
            return False
        
        # don't reassign the current record
        # clear the record
        if record is None:
            self._currentRecord = None
            blocked = self.signalsBlocked()
            self.blockSignals(True)
            self.setCurrentIndex(-1)
            self.blockSignals(blocked)
            
            if not blocked:
                self.currentRecordChanged.emit(None)
            
            return True
        
        elif record == self.currentRecord():
            return False
        
        self._currentRecord = record
        found = False
        
        blocked = self.signalsBlocked()
        self.blockSignals(True)
        for i in range(self.count()):
            stored = unwrapVariant(self.itemData(i, Qt.UserRole))
            if stored == record:
                self.setCurrentIndex(i)
                found = True
                break
        
        if not found and autoAdd:
            self.addRecord(record)
            self.setCurrentIndex(self.count() - 1)
        
        self.blockSignals(blocked)
        
        if not blocked:
            self.currentRecordChanged.emit(record)
        return False
    
    def setIconMapper( self, mapper ):
        """
        Sets the icon mapping method for this combobox to the inputed mapper. \
        The inputed mapper method should take a orb.Table instance as input \
        and return a QIcon as output.
        
        :param      mapper | <method> || None
        """
        self._iconMapper = mapper
    
    def setLabelMapper( self, mapper ):
        """
        Sets the label mapping method for this combobox to the inputed mapper.\
        The inputed mapper method should take a orb.Table instance as input \
        and return a string as output.
        
        :param      mapper | <method>
        """
        self._labelMapper = mapper
    
    def setOrder(self, order):
        """
        Sets the order for this combo box to the inputed order.  This will
        be used in conjunction with the query when loading records to the
        combobox.
        
        :param      order | [(<str> column, <str> asc|desc), ..] || None
        """
        self._order = order
    
    def setQuery(self, query, autoRefresh=True):
        """
        Sets the query for this record box for generating records.
        
        :param      query | <Query> || None
        """
        self._query = query
        
        tableType = self.tableType()
        if not tableType:
            return False
        
        if autoRefresh:
            self.refresh(tableType.select(where = query))
        
        return True
    
    def setRecords(self, records):
        """
        Sets the records on this combobox to the inputed record list.
        
        :param      records | [<orb.Table>, ..]
        """
        self.refresh(records)
    
    def setRequired( self, state ):
        """
        Sets the required state for this combo box.  If the column is not
        required, a blank record will be included with the choices.
        
        :param      state | <bool>
        """
        self._required = state
    
    def setShowTreePopup(self, state):
        """
        Sets whether or not to use an ORB tree widget in the popup for this
        record box.
        
        :param      state | <bool>
        """
        self._showTreePopup = state
    
    def setSpecifiedColumns(self, columns):
        """
        Sets the specified columns for this combobox widget.
        
        :param      columns | [<orb.Column>, ..] || [<str>, ..] || None
        """
        self._specifiedColumns = columns
        self._specifiedColumnsOnly = columns is not None
    
    def setSpecifiedColumnsOnly(self, state):
        """
        Sets whether or not only specified columns should be
        loaded for this record box.
        
        :param      state | <bool>
        """
        self._specifiedColumnsOnly = state
    
    def setTableLookupIndex(self, index):
        """
        Sets the name of the index method that will be used to lookup
        records for this combo box.
        
        :param    index | <str>
        """
        self._tableLookupIndex = nstr(index)
    
    def setTableType( self, tableType ):
        """
        Sets the table type for this record box to the inputed table type.
        
        :param      tableType | <orb.Table>
        """
        self._tableType     = tableType
        
        if tableType:
            self._tableTypeName = tableType.schema().name()
        else:
            self._tableTypeName = ''
    
    def setTableTypeName(self, name):
        """
        Sets the table type name for this record box to the inputed name.
        
        :param      name | <str>
        """
        self._tableTypeName = nstr(name)
        self._tableType = None
    
    def setThreadEnabled(self, state):
        """
        Sets whether or not threading should be enabled for this widget.  
        Actual threading will be determined by both this property, and whether
        or not the active ORB backend supports threading.
        
        :param      state | <bool>
        """
        self._threadEnabled = state
    
    def setVisible(self, state):
        """
        Sets the visibility for this record box.
        
        :param      state | <bool>
        """
        super(XOrbRecordBox, self).setVisible(state)
        
        if state and not self._loaded:
            if self.autoInitialize():
                table = self.tableType()
                if not table:
                    return
                
                self.setRecords(table.select(where=self.query()))
            else:
                self.initialized.emit()
    
    def showPopup(self):
        """
        Overloads the popup method from QComboBox to display an ORB tree widget
        when necessary.
        
        :sa     setShowTreePopup
        """
        if not self.showTreePopup():
            return super(XOrbRecordBox, self).showPopup()
        
        tree = self.treePopupWidget()
        
        if tree and not tree.isVisible():
            tree.move(self.mapToGlobal(QPoint(0, self.height())))
            tree.resize(self.width(), 250)
            tree.resizeToContents()
            tree.filterItems('')
            tree.setFilteredColumns(range(tree.columnCount()))
            tree.show()
    
    def showTreePopup(self):
        """
        Sets whether or not to use an ORB tree widget in the popup for this
        record box.
        
        :return     <bool>
        """
        return self._showTreePopup
    
    def specifiedColumns(self):
        """
        Returns the list of columns that are specified based on the column
        view for this widget.
        
        :return     [<orb.Column>, ..]
        """
        columns = []
        table = self.tableType()
        tree = self.treePopupWidget()
        schema = table.schema()
        
        if self._specifiedColumns is not None:
            colnames = self._specifiedColumns
        else:
            colnames = tree.columns()
        
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
        Returns whether or not only specified columns should be loaded
        for this record box.
        
        :return     <int>
        """
        return self._specifiedColumnsOnly
    
    def startEditTimer(self):
        self._editedTimer.start()
    
    def tableLookupIndex(self):
        """
        Returns the name of the index method that will be used to lookup
        records for this combo box.
        
        :return     <str>
        """
        return self._tableLookupIndex
    
    def tableType( self ):
        """
        Returns the table type for this instance.
        
        :return     <subclass of orb.Table> || None
        """
        if not self._tableType:
            if self._tableTypeName:
                self._tableType = Orb.instance().model(nstr(self._tableTypeName))
            
        return self._tableType
    
    def tableTypeName(self):
        """
        Returns the table type name that is set for this combo box.
        
        :return     <str>
        """
        return self._tableTypeName
    
    def treePopupWidget(self):
        """
        Returns the popup widget for this record box when it is supposed to
        be an ORB tree widget.
        
        :return     <XTreeWidget>
        """
        edit = self.lineEdit()
        if not self._treePopupWidget:
            # create the treewidget
            tree = XTreeWidget(self)
            tree.setWindowFlags(Qt.Popup)
            tree.setFocusPolicy(Qt.StrongFocus)
            tree.installEventFilter(self)
            tree.setAlternatingRowColors(True)
            tree.setShowGridColumns(False)
            tree.setRootIsDecorated(False)
            tree.setVerticalScrollMode(tree.ScrollPerPixel)
            
            # create connections
            tree.itemClicked.connect(self.acceptRecord)
            
            if edit:
                edit.textEdited.connect(tree.filterItems)
                edit.textEdited.connect(self.showPopup)
            
            self._treePopupWidget = tree
        
        return self._treePopupWidget
    
    def worker(self):
        """
        Returns the worker object for loading records for this record box.
        
        :return     <XOrbLookupWorker>
        """
        if self._worker is None:
            self._worker = XOrbLookupWorker(self.isThreadEnabled())
            self._worker.setBatchSize(self._batchSize)
            self._worker.setBatched(not self.isThreadEnabled())
            
            # connect the worker
            self.loadRequested.connect(self._worker.loadRecords)
            self._worker.loadingStarted.connect(self.markLoadingStarted)
            self._worker.loadingFinished.connect(self.markLoadingFinished)
            self._worker.loadedRecords.connect(self.addRecordsFromThread)
        
        return self._worker
    
    x_batchSize         = Property(int, batchSize, setBatchSize)
    x_required          = Property(bool, isRequired, setRequired)
    x_tableTypeName     = Property(str, tableTypeName, setTableTypeName)
    x_tableLookupIndex  = Property(str, tableLookupIndex, setTableLookupIndex)
    x_showTreePopup     = Property(bool, showTreePopup, setShowTreePopup)
    x_threadEnabled     = Property(bool, isThreadEnabled, setThreadEnabled)
    
__designer_plugins__ = [XOrbRecordBox]

# register save and load methods
def getWidgetValue(w):
    if w.isCheckable():
        return w.checkedRecords()
    return w.currentRecord()

def setWidgetValue(w, v):
    if w.isCheckable():
        w.setCheckedRecords(v)
    else:
        w.setCurrentRecord(v)

import projexui
projexui.registerWidgetValue(XOrbRecordBox, getWidgetValue, setWidgetValue)