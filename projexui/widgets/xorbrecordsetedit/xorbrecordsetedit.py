""" 
Defines the XQueryEdit widget that allows users to visually build queries into
an ORB database.
"""

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

from projexui.qt import wrapVariant, unwrapVariant
from projexui.qt.QtCore import Qt,\
                               QSize,\
                               QPoint

from projexui.qt.QtGui import QWidget,\
                              QTreeWidgetItem,\
                              QApplication,\
                              QDialogButtonBox,\
                              QToolButton,\
                              QIcon,\
                              QItemDelegate,\
                              QComboBox

import projex.text
import projexui
import projexui.resources

from projexui.widgets.xpopupwidget import XPopupWidget

from orb import Query as Q, QueryCompound, RecordSet

class ColumnDelegate(QItemDelegate):
    def createEditor( self, parent, option, index ):
        schema = self.parent().schema()
        if ( not schema ):
            return None
        
        colNames = map(lambda x: x.displayName(), schema.columns())
        
        combo = QComboBox(parent)
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.NoInsert)
        combo.addItems(colNames)
        
        return combo

#------------------------------------------------------------------------------

class OperatorDelegate(QItemDelegate):
    def createEditor( self, parent, option, index ):
        combo = QComboBox(parent)
        
        keys = Q.Op.keys()
        keys = map(lambda x: projex.text.joinWords(x, ' ').lower(), keys)
        
        combo.addItems(sorted(keys))
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.NoInsert)
        
        return combo
    
    def setEditorData( self, editor, index ):
        i = editor.findText(unwrapVariant(index.data()))
        editor.setCurrentIndex(i)
    
    def setModelData( self, editor, model, index ):
        model.setData(index, wrapVariant(editor.currentText()))

#------------------------------------------------------------------------------

class XQueryItem(QTreeWidgetItem):
    def __init__( self, query, joiner = '' ):
        super(XQueryItem, self).__init__()
        
        # set the joiner
        self._joiner = joiner
        
        # update the hint
        self.setText(0, joiner)
        self.setSizeHint(1, QSize(80, 20))
        
        if ( Q.typecheck(query) ):
            op_name = Q.Op[query.operatorType()]
            op_name = projex.text.joinWords(op_name, ' ').lower()
            
            palette = QApplication.palette()
            for i in range(4):
                self.setBackground(i, palette.color(palette.Base))
            
            self.setTextAlignment(0, Qt.AlignRight | Qt.AlignVCenter)
            self.setText(1, query.columnName())
            self.setText(2, op_name)
            self.setText(3, query.valueString())
            
            flags = self.flags()
            flags |= Qt.ItemIsEditable
            self.setFlags(flags)
        
        else:
            sub_joiner = QueryCompound.Op[query.operatorType()].lower()
            for i, sub_query in enumerate(query.queries()):
                if ( i ):
                    item = XQueryItem(sub_query, sub_joiner)
                else:
                    item = XQueryItem(sub_query)
                    
                self.addChild(item)
    
    def query( self ):
        """
        Returns the query for this item by joining together its children, 
        or building its data.
        
        :return     <Query> || <QueryCompound>
        """
        if ( self.childCount() ):
            q = Q()
            for i in range(self.childCount()):
                q &= self.child(i).query()
            return q
        else:
            op_name = projex.text.classname(self.text(2))
            q = Q(nativestring(self.text(1)))
            q.setOperatorType(Q.Op[op_name])
            q.setValueString(nativestring(self.text(3)))
            return q
    
    def summary( self ):
        child_text = []
        
        for c in range(self.childCount()):
            child = self.child(c)
            text = [child.text(0), child.text(1), child.text(2), child.text(3)]
            text = map(str, text)
            
            while ( '' in text ):
                text.remove('')
            
            child_text.append( ' '.join(text) )
        
        return ' '.join(child_text)
    
    def update( self, recursive = False ):
        if ( not self.childCount() ):
            return
        
        self.setFirstColumnSpanned(True)
        
        if ( self.isExpanded() ):
            self.setText(0, self._joiner)
        
        elif ( self._joiner ):
            self.setText(0, self._joiner + ' (%s)' % self.summary())
        
        else:
            self.setText(0, '(%s)' % self.summary())
        
        if ( recursive ):
            for c in range( self.childCount() ):
                self.child(c).update(True)

#------------------------------------------------------------------------------

class XOrbRecordSetEdit(QWidget):
    """ """
    __designer_group__ = 'ProjexUI - ORB'
    
    def __init__( self, parent = None ):
        super(XOrbRecordSetEdit, self).__init__( parent )
        
        # load the user interface
        projexui.loadUi(__file__, self)
        
        # define custom properties
        self._table    = None
        
        # setup delegates
        self.uiQueryTREE.setItemDelegateForColumn(1, ColumnDelegate(self))
        self.uiQueryTREE.setItemDelegateForColumn(2, OperatorDelegate(self))
        
        # set default properties
        palette = self.palette()
        palette.setColor(palette.Base, palette.color(palette.AlternateBase))
        self.uiQueryTREE.setPalette(palette)
        self.uiQueryTREE.setGridPen(palette.color(palette.AlternateBase))
        self.uiQueryTREE.setArrowStyle(True)
        self.uiQueryTXT.setHint('enter quick query...')
        self.uiQueryBTN.setChecked(False)
        self.setTable(None)
        
        # create connections
        self.uiQueryTXT.returnPressed.connect(self.applyQuery)
        self.uiQueryTREE.itemExpanded.connect(self.updateQueryItem)
        self.uiQueryTREE.itemCollapsed.connect(self.updateQueryItem)
    
    def applyQuery( self ):
        """
        Sets the query for this widget from the quick query text builder.
        """
        query = Q.fromString(nativestring(self.uiQueryTXT.text()))
        self.setQuery(query)
        self.uiQueryTXT.setText('')
    
    def clear( self ):
        """
        Clears the information for this edit.
        """
        self.uiQueryTXT.setText('')
        self.uiQueryTREE.clear()
        self.uiGroupingTXT.setText('')
        self.uiSortingTXT.setText('')
    
    def query( self ):
        """
        Returns the query this widget is representing from the tree widget.
        
        :return     <Query> || <QueryCompound> || None
        """
        if ( not self.uiQueryCHK.isChecked() ):
            return None
        
        # build a query if not searching all
        q = Q()
        for i in range(self.uiQueryTREE.topLevelItemCount()):
            item = self.uiQueryTREE.topLevelItem(i)
            q &= item.query()
        return q
    
    def recordSet( self ):
        """
        Returns the record set that is associated with this widget.
        
        :return     <orb.RecordSet> || None
        """
        if ( not self.table() ):
            return None
        
        recordSet = RecordSet(self.table())
        recordSet.setQuery(self.query())
        
        # set the grouping options
        grouping = nativestring(self.uiGroupingTXT.text()).split(',')
        while ( '' in grouping ):
            grouping.remove('')
        
        recordSet.setGroupBy( grouping )
        
        # set the sorting options
        sorting = nativestring(self.uiSortingTXT.text()).split(',')
        while ( '' in sorting ):
            sorting.remove('')
        
        recordSet.setOrder([i.split('|') for i in sorting])
        
        # set the paged options
        recordSet.setPaged(self.uiPagedCHK.isChecked())
        recordSet.setPageSize(self.uiPagedSPN.value())
        
        return recordSet
    
    def schema( self ):
        """
        Returns the schema that is linked with the table assigned to this widget
        
        :return     <orb.TableSchema> || None
        """
        if ( self._table ):
            return self._table.schema()
        return None
    
    def setQuery( self, query ):
        """
        Assigns the query for this widget, loading the query builder tree with
        the pertinent information.
        
        :param      query | <Query> || <QueryCompound> || None
        """
        tree = self.uiQueryTREE
        tree.blockSignals(True)
        tree.setUpdatesEnabled(False)
        
        tree.clear()
        
        self.uiQueryCHK.setChecked(query is not None)
        
        # assign a top level query item
        if ( Q.typecheck(query) and not query.isNull() ):
            tree.addTopLevelItem(XQueryItem(query))
        
        # assign a top level query group
        elif ( QueryCompound.typecheck(query) ):
            op_name = QueryCompound.Op[query.operatorType()].lower()
            for i, sub_query in enumerate(query.queries()):
                if ( i ):
                    item = XQueryItem(sub_query, op_name)
                    tree.addTopLevelItem(item)
                    item.update(True)
                else:
                    item = XQueryItem(sub_query)
                    tree.addTopLevelItem(item)
                    item.update(True)
        
        tree.resizeToContents()
        tree.setUpdatesEnabled(True)
        tree.blockSignals(False)
    
    def setRecordSet( self, recordSet ):
        """
        Sets the record set instance that this widget will use.
        
        :param      recordSet | <orb.RecordSet>
        """
        if ( recordSet ):
            self.setQuery(      recordSet.query() )
            self.setGroupBy(    recordSet.groupBy() )
            self.setPageSize(   recordSet.pageSize() )
            self.setSortBy(     recordSet.order() )
            
            self.uiPagedCHK.setChecked( recordSet.isPaged() )
        else:
            self.setQuery(Q())
            self.setGroupBy('')
            self.setPageSize(100)
            self.setSortBy('')
            
            self.uiPagedCHK.setChecked( False )
    
    def setGroupBy( self, groupBy ):
        """
        Sets the group by information for this widget to the inputed grouping
        options.  This can be either a list of strings, or a comma deliminated
        string.
        
        :param      groupBy | <str> || [<str>, ..]
        """
        if ( type(groupBy) in (list, tuple) ):
            groupBy = ','.join(map(str, groupBy))
        
        self.uiGroupingTXT.setText(groupBy)
    
    def setPageSize( self, pageSize ):
        """
        Sets the page size value for this widget.
        
        :param      pageSize | <int>
        """
        self.uiPagedSPN.setValue(pageSize)
    
    def setSortedBy( self, sortedBy ):
        """
        Sets the sorting information for this widget to the inputed sorting
        options.  This can be either a list of terms, or a comma deliminated
        string.
        
        :param      sortedBy | <str> || [(<str> column, <str> direction), ..]
        """
        if ( type(groupBy) in (list, tuple) ):
            sortedBy = ','.join(map(lambda x: '%s|%s' % x, sortedBy))
        
        self.uiSortingTXT.setText(sortedBy)
    
    def setTable( self, table ):
        """
        Sets the table that is assigned to this widget to the inputed table.
        
        :param      table | <subclass of orb.Table>
        """
        self._table = table
        self.setEnabled(table is not None)
        self.clear()
    
    def table( self ):
        """
        Returns the table instance that is linked with this widget.
        
        :return     <orb.Table>
        """
        return self._table
    
    def updateQueryItem( self, item ):
        """
        Updates the query tree item by either showing its expanded data or
        hiding it based on its collapse state.
        """
        item.update()