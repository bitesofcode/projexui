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

import weakref

from projex.text import nativestring

from projexui.qt import wrapVariant
from projexui.qt.QtCore   import QSize,\
                                 Qt,\
                                 QDate,\
                                 QDateTime,\
                                 QTime

from projexui.qt.QtGui    import QColor, QBrush

import datetime
import projex.dates

try:
    from orb import Orb, Query as Q, RecordSet
except ImportError:
    pass

from projex.enum import enum
from projexui.widgets.xtreewidget import XTreeWidget, XTreeWidgetItem

class XOrbRecordItem( XTreeWidgetItem ):
    State = enum('Normal', 'New', 'Removed', 'Modified')
    
    def __init__(self, parent, record):
        super(XOrbRecordItem, self).__init__(parent)
        
        # sets whether or not this record is loaded
        self._record        = record
        self.__loaded       = False
        self._childRecords  = None
        self._recordState   = XOrbRecordItem.State.Normal
        self._dragQuery     = None
        
        # initialize the item
        self.setFixedHeight(22)
        self.setRecord(record)
        
        tree = self.treeWidget()
        try:
            tree._recordMapping[record] = weakref.ref(self)
        except AttributeError:
            pass
    
    def addRecordState( self, state ):
        """
        Adds the inputed record state to the set for this item.
        
        :param      state | <XOrbRecordItem.State>
        """
        curr_state = self.recordState()
        self.setRecordState(curr_state | state)
    
    def childRecords(self):
        """
        Returns a record set of children for this item based on the record.  If
        no record set is manually set for this instance, then it will use the
        hierarchyColumn value from the tree widget with this record.  If no
        hierarchyColumn is speified, then a blank record set is returned.
        
        :return     <orb.RecordSet>
        """
        if self._childRecords is not None:
            return self._childRecords
        
        tree = self.treeWidget()
        try:
            table, column = tree.hierarchyLookup(self.record())
        except AttributeError:
            table = None
            column = ''
        
        # returns the children for this information
        if table and column:
            return table.select(where=Q(column) == self.record())
        
        # returns a blank record set if no other records can be found
        return RecordSet()
    
    def dragTable(self):
        """
        Returns the drag table that is assigned to this record item.
        
        :return     <subclass of orb.Table> || None
        """
        return Orb.instance().model(self.dragData('application/x-table'))
    
    def dragQuery(self):
        """
        Returns the drag query that is assigned to this record item.
        
        :return     <orb.Query>
        """
        return Q.fromXmlString(self.dragData('application/x-query'))
    
    def findItemsByState( self, state ):
        """
        Looks up all the items within this record based on the state.
        
        :param      state | <XOrbRecordItem.State>
        
        :return     [<XOrbRecordItem>, ..]
        """
        out = []
        if ( self.hasRecordState(state) ):
            out.append(self)
        
        for c in range(self.childCount()):
            out += self.child(c).findItemsByState(state)
        
        return out
    
    def hasRecords(self):
        """
        Returns whether or not this record has children.
        
        :return     <bool>
        """
        records = self.childRecords()
        if records and len(records) > 0:
            return True
        return False
    
    def hasRecordState( self, state ):
        """
        Returns whether or not this items state contains the inputed state.
        
        :param      state | <XOrbRecordItem.State>
        
        :return     <bool>
        """
        return (self._recordState & state) != 0
    
    def load(self):
        """
        Loads the children for this record item.
        
        :return     <bool> | changed
        """
        if self.__loaded:
            return False
        
        self.__loaded = True
        self.setChildIndicatorPolicy(self.DontShowIndicatorWhenChildless)
        
        # loads the children for this widget
        tree = self.treeWidget()
        if tree.groupBy():
            grps = self.childRecords().grouped(tree.groupBy())
            for grp, records in grps.items():
                tree.createGroupItem(grp, records, self)
        else:
            for record in self.childRecords():
                tree.createRecordItem(record, self)
        
        return True
    
    def record( self ):
        """
        Returns the record for this item.
        
        :return     <orb.Table>
        """
        return self._record
    
    def recordState( self ):
        """
        Returns the record state for this item.
        
        :return     <XOrbRecordItem.State>
        """
        return self._recordState
    
    def removeRecordState( self, state ):
        """
        Removes the state from this item.
        
        :param      state | <XOrbRecordItem.State>
        """
        curr_state = self.recordState()
        if curr_state & state:
            self.setRecordState(curr_state ^ state)
    
    def setChildRecords(self, records):
        """
        Sets a record set of children for this item based on the record.  If
        no record set is manually set for this instance, then it will use the
        hierarchyColumn value from the tree widget with this record.  If no
        hierarchyColumn is speified, then a blank record set is returned.
        
        :param      records | <orb.RecordSet>
        """
        self._records = records
    
    def setDragTable(self, table):
        """
        Sets the table that will be linked with the drag query for this
        record.  This information will be added to the drag & drop information
        when this record is dragged from the tree and will be set into
        the application/x-table format for mime data.
        
        :sa     setDragQuery, XTreeWidgetItem.setDragData
        
        :param      table | <subclass of orb.Table>
        """
        if table and table.schema():
            self.setDragData('application/x-orb-table', table.schema().name())
        else:
            self.setDragData('application/x-orb-table', None)
    
    def setDragQuery(self, query):
        """
        Sets the query that should be used when this record is dragged.  This
        value will be set into the application/x-query format for mime
        data.
        
        :param      query | <orb.Query> || None
        """
        if query is not None:
            self.setDragData('application/x-orb-query', query.toXmlString())
        else:
            self.setDragData('application/x-orb-query', None)
    
    def setRecord( self, record ):
        """
        Sets the record instance for this item to the inputed record.
        
        :param      record | <orb.Table>
        """
        self._record = record
        self.updateRecordValues()
    
    def setRecordState( self, recordState ):
        """
        Sets the record state for this item to the inputed state.
        
        :param      recordState | <XOrbRecordItem.State>
        """
        self._recordState = recordState
        
        try:
            is_colored = self.treeWidget().isColored()
        except AttributeError:
            return
        
        if not is_colored:
            return
        
        # determine the color for the item based on the state
        if recordState & XOrbRecordItem.State.Removed:
            clr = self.treeWidget().colorSet().color('RecordRemoved')
        elif recordState & XOrbRecordItem.State.New:
            clr = self.treeWidget().colorSet().color('RecordNew')
        elif recordState & XOrbRecordItem.State.Modified:
            clr = self.treeWidget().colorSet().color('RecordModified')
        else:
            clr = None
        
        # set the color based on the record state
        if clr is not None:
            clr = QColor(clr)
            clr.setAlpha(40)
            brush = QBrush(clr)
        else:
            brush = QBrush()
        
        for c in range(self.treeWidget().columnCount()):
            self.setBackground(c, brush)
    
    def updateRecordValues(self):
        """
        Updates the ui to show the latest record values.
        """
        record = self.record()
        if not record:
            return
        
        # update the record information
        tree = self.treeWidget()
        if not isinstance(tree, XTreeWidget):
            return
        
        for column in record.schema().columns():
            c = tree.column(column.displayName())
            if c == -1:
                continue
            
            elif tree.isColumnHidden(c):
                continue
            
            else:
                val = record.recordValue(column.name())
                self.updateColumnValue(column, val, c)
        
        # update the record state information
        if not record.isRecord():
            self.addRecordState(XOrbRecordItem.State.New)
        
        elif record.isModified():
            self.addRecordState(XOrbRecordItem.State.Modified)
    
    def updateColumnValue(self, column, value, index=None):
        """
        Assigns the value for the column of this record to the inputed value.
        
        :param      index | <int>
                    value | <variant>
        """
        if index is None:
            index = self.treeWidget().column(column.name())
        
        if type(value) == datetime.date:
            self.setData(index, Qt.EditRole, wrapVariant(value))
        elif type(value) == datetime.time:
            self.setData(index, Qt.EditRole, wrapVariant(value))
        elif type(value) == datetime.datetime:
            self.setData(index, Qt.EditRole, wrapVariant(value))
        elif type(value) in (float, int):
            if column.enum():
                self.setText(index, column.enum().displayText(value))
            else:
                self.setData(index, Qt.EditRole, wrapVariant(value))
        elif value is not None:
            self.setText(index, nativestring(value))
        else:
            self.setText(index, '')
        
        self.setSortData(index, value)
        
        # map default value information
        try:
            mapper = self.treeWidget().columnMappers().get(column.columnName())
        except AttributeError:
            mapper = None
        
        if mapper is None:
            form = column.stringFormat()
            if form:
                mapper = form.format
        
        if mapper:
            self.setText(index, mapper(value))
