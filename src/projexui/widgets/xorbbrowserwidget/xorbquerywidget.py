""" Defines the query widget used by the popup editor in the browser. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software, LLC'
__license__         = 'LGPL'

__maintainer__      = 'Projex Software, LLC'
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
                              QComboBox,\
                              QFontMetrics,\
                              QTextEdit,\
                              QListWidget

import projex.text
import projexui
import projexui.resources

from projexui.widgets.xtreewidget import XTreeWidgetDelegate
from projexui.widgets.xorbbrowserwidget.xorbbrowserfactory \
                                  import XOrbBrowserFactory

from orb import Query as Q, QueryCompound, RecordSet, ColumnType

class ColumnDelegate(XTreeWidgetDelegate):
    def createEditor( self, parent, option, index ):
        tree = self.parent()
        querywidget = tree.parent()
        item = tree.itemFromIndex(index)
        if ( isinstance(item, XQueryItem) and not item.childCount() ):
            ttype = querywidget.tableType()
            options = querywidget.factory().columnOptions(ttype)
        
        elif ( isinstance(item, XJoinItem) ):
            options = ['and', 'or']
        
        combo = QComboBox(parent)
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.NoInsert)
        combo.addItems(sorted(options))
        
        return combo
    
    def setEditorData( self, editor, index ):
        i = editor.findText(unwrapVariant(index.data()))
        editor.setCurrentIndex(i)
        editor.lineEdit().selectAll()
    
    def setModelData( self, editor, model, index ):
        model.setData(index, wrapVariant(editor.currentText()))
        
    def updateEditorGeometry( self, editor, option, index ):
        super(ColumnDelegate, self).updateEditorGeometry(editor, 
                                                           option, 
                                                           index)
        
        keys = map(lambda x: nativestring(editor.itemText(x)), range(editor.count()))
        longest = max(map(lambda x: (len(x), x), keys))[1]
        
        metrics = QFontMetrics(editor.font())
        width   = metrics.width(longest) + 30
        tree    = self.parent()
        item    = tree.itemFromIndex(index)
        rect    = tree.visualItemRect(item)
        
        if ( index.column() == 0 ):
            width += rect.x()
        
        editor.resize(width, rect.height())

#------------------------------------------------------------------------------

class OperatorDelegate(XTreeWidgetDelegate):
    def createEditor( self, parent, option, index ):
        combo = QComboBox(parent)
        
        item = self.parent().itemFromIndex(index)
        columnType = item.columnType()
        
        operators = Q.ColumnOps.get(columnType,
                                    Q.ColumnOps[None])
        
        # create the keys based on the column type
        keys = []
        for operator in operators:
            op_name = Q.Op[operator]
            keys.append(projex.text.joinWords(op_name, ' ').lower())
        
        combo.addItems(sorted(keys))
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.NoInsert)
        
        return combo
    
    def setEditorData( self, editor, index ):
        i = editor.findText(unwrapVariant(index.data()))
        editor.setCurrentIndex(i)
        editor.lineEdit().selectAll()
    
    def setModelData( self, editor, model, index ):
        model.setData(index, wrapVariant(editor.currentText()))
        
    def updateEditorGeometry( self, editor, option, index ):
        super(OperatorDelegate, self).updateEditorGeometry(editor, 
                                                           option, 
                                                           index)
        
        keys = map(lambda x: nativestring(editor.itemText(x)), range(editor.count()))
        longest = max(map(lambda x: (len(x), x), keys))[1]
        
        metrics = QFontMetrics(editor.font())
        width   = metrics.width(longest) + 30
        tree    = self.parent()
        item    = tree.itemFromIndex(index)
        rect    = tree.visualItemRect(item)
        
        if ( index.column() == 0 ):
            width += rect.x()
        
        editor.resize(width, rect.height())

class ValueDelegate(XTreeWidgetDelegate):
    def createEditor( self, parent, option, index ):
        # grab the item to determine our options
        tree         = self.parent()
        queryWidget  = tree.parent()
        schema       = queryWidget.schema()
        item         = tree.itemFromIndex(index)
        factory      = queryWidget.factory()
        
        if ( not schema ):
            return None
        
        operatorType = item.operatorType()
        
        return factory.createEditor(parent, schema, columnName, operatorType)
    
    def setEditorData( self, editor, index ):
        """
        Set the data for the editor of this delegate to the inputed information.
        
        :param      editor | <QWidget>
                    index  | <QModelIndex>
        """
        item        = self.parent().itemFromIndex(index)
        value       = item.value()
        tree        = self.parent()
        querywidget = tree.parent()
        factory     = querywidget.factory()
        
        factory.setEditorData(editor, value)
    
    def setModelData( self, editor, model, index ):
        """
        Sets the data for the given index from the editor's value.
        
        :param      editor | <QWidget>
                    model  | <QAbstractItemModel>
                    index  | <QModelIndex>
        """
        tree        = self.parent()
        querywidget = tree.parent()
        factory     = querywidget.factory()
        item        = tree.itemFromIndex(index)
        
        value = factory.editorData(editor)
        item.setValue(value)
    
    def updateEditorGeometry( self, editor, option, index ):
        super(ValueDelegate, self).updateEditorGeometry(editor, 
                                                        option, 
                                                        index)
        
        if ( isinstance(editor, QTextEdit) or isinstance(editor, QListWidget) ):
            editor.resize(editor.width(), 40)

#------------------------------------------------------------------------------

class XJoinItem(QTreeWidgetItem):
    def __init__( self, parent, operator, preceeding = None ):
        if ( preceeding ):
            super(XJoinItem, self).__init__(parent, preceeding)
        else:
            super(XJoinItem, self).__init__(parent)
        
        # setup the sizing options
        self.setSizeHint(0, QSize(150, 20))
        self.setFirstColumnSpanned(True)
        self.setText(0, operator)
        
        # update the flags for this item
        flags = self.flags()
        flags |= Qt.ItemIsEditable
        self.setFlags(flags)
        
#------------------------------------------------------------------------------

class XQueryItem(QTreeWidgetItem):
    def __init__( self, parent, query, preceeding = None ):
        if ( preceeding ):
            super(XQueryItem, self).__init__(parent, preceeding)
        else:
            super(XQueryItem, self).__init__(parent)
        
        self.setSizeHint(2, QSize(150, 20))
        
        # create custom properties
        self._value = None
        
        # add a simple query item
        if ( Q.typecheck(query) ):
            
            self.setTextAlignment(1, Qt.AlignCenter)
            
            # set the data for this item
            if ( not query.isNull() ):
                self.setColumnName(query.columnName())
                self.setOperatorType(query.operatorType())
                self.setValue(query.value())
            else:
                self.setColumnName('')
                self.setOperatorType(Q.Op.Is)
                self.setValue('')
            
            # set the flags for this item
            self.setFlags( Qt.ItemIsEnabled | \
                           Qt.ItemIsEditable | \
                           Qt.ItemIsSelectable )
            
        else:
            operator = QueryCompound.Op[query.operatorType()].lower()
            for i, sub_query in enumerate(query.queries()):
                if ( i ):
                    XJoinItem(self, operator)
                
                XQueryItem(self, sub_query)
        
        self.update()
    
    def columnName( self ):
        """
        Returns the name of the column that this item is using.
        
        :return     <str>
        """
        return nativestring(self.text(0))
    
    def columnType( self ):
        """
        Returns the column type for this item based on the current column.
        
        :return     <orb.ColumnType>
        """
        schema = self.treeWidget().parent().schema()
        if ( not schema ):
            return 0
        column = schema.column(self.text(0))
        if ( column ):
            return column.columnType()
        return ColumnType.String
    
    def operatorType( self ):
        """
        Returns the operator type for this item based on the current column.
        
        :return     <Q.Op>
        """
        return Q.Op[projex.text.joinWords(projex.text.capitalizeWords(self.text(1)))]
    
    def query( self ):
        """
        Returns the query for this item by joining together its children, 
        or building its data.
        
        :return     <Query> || <QueryCompound>
        """
        # create the query compound
        if ( self.childCount() ):
            q = Q()
            operator = 'and'
            for i in range(self.childCount()):
                item = self.child(i)
                if ( isinstance(item, XQueryItem) ):
                    if ( operator == 'and' ):
                        q &= item.query()
                    else:
                        q |= item.query()
                else:
                    operator = nativestring(item.text(0))
            return q
        
        # create the query for this individual item
        else:
            q = Q(self.columnName())
            q.setOperatorType(self.operatorType())
            q.setValue(self.value())
            return q
    
    def setColumnName( self, columnName ):
        """
        Sets the name that will be used for this column to the inputed value.
        
        :param      columnName | <str>
        """
        self.setText(0, nativestring(columnName))
    
    def setOperatorType( self, operatorType ):
        """
        Sets the operator type value to the inputed type.
        
        :param      opeartorType | <Q.Op>
        """
        op_name = Q.Op[operatorType]
        op_name = projex.text.joinWords(op_name, ' ').lower()
        self.setText(1, op_name)
    
    def setValue( self, value ):
        """
        Sets the value for this item to the inputed value.
        
        :param      value | <variant>
        """
        self._value = value
        
        # map a list of choices to the system
        if ( isinstance(value, list) ):
            self.setText(2, '[%s]' % ','.join(map(str, value)))
        else:
            self.setText(2, nativestring(value))
    
    def summary( self ):
        """
        Creates a text string representing the current query and its children
        for this item.
        
        :return     <str>
        """
        child_text = []
        
        for c in range(self.childCount()):
            child = self.child(c)
            text = [child.text(0), child.text(1), child.text(2), child.text(3)]
            text = map(str, text)
            
            while ( '' in text ):
                text.remove('')
            
            child_text.append( ' '.join(text) )
        
        return ' '.join(child_text)
    
    def value( self ):
        """
        Returns the value that this query item holds.
        
        :return     <variant>
        """
        return self._value
    
    def update( self, recursive = False ):
        if ( not self.childCount() ):
            return
        
        # update the look for the group
        font = self.font(0)
        font.setBold(True)
        self.setFont(0, font)
        
        for i in range(self.columnCount()):
            self.setText(i, '')
        
        # make sure we size properly
        self.setSizeHint(0, QSize(150, 20))
        self.setFirstColumnSpanned(True)
        
        palette = QApplication.instance().palette()
        if ( not self.isExpanded() ):
            self.setForeground(0, palette.color(palette.Mid))
        else:
            self.setForeground(0, palette.color(palette.AlternateBase))
        
        self.setText(0, '(%s)' % self.summary())
        
        if ( recursive ):
            for c in range( self.childCount() ):
                self.child(c).update(True)

#------------------------------------------------------------------------------

class XOrbQueryWidget(QWidget):
    """ """
    def __init__( self, parent = None, factory = None ):
        super(XOrbQueryWidget, self).__init__( parent )
        
        # load the user interface
        projexui.loadUi(__file__, self)
        
        if ( not factory ):
            factory = XOrbBrowserFactory()
        
        # define custom properties
        self._tableType = None
        self._factory = factory
        
        # setup delegates
        delegates = [self.uiQueryTREE.itemDelegate()]
        
        # create the column delegate
        column_delegate   = ColumnDelegate(self.uiQueryTREE)
        operator_delegate = OperatorDelegate(self.uiQueryTREE)
        value_delegate    = ValueDelegate(self.uiQueryTREE)
        
        delegates.append(column_delegate)
        delegates.append(operator_delegate)
        delegates.append(value_delegate)
        
        self.uiQueryTREE.setItemDelegateForColumn(0, column_delegate)
        self.uiQueryTREE.setItemDelegateForColumn(1, operator_delegate)
        self.uiQueryTREE.setItemDelegateForColumn(2, value_delegate)
        
        # set the resize mode
        header = self.uiQueryTREE.header()
        header.setResizeMode(0, header.ResizeToContents)
        header.setResizeMode(1, header.ResizeToContents)
        
        # create event filter information
        self.uiQueryTXT.installEventFilter(self)
        
        # create connections
        self.uiQueryTREE.itemExpanded.connect(self.updateQueryItem)
        self.uiQueryTREE.itemCollapsed.connect(self.updateQueryItem)
        self.uiAddBTN.clicked.connect(self.addQuery)
        self.uiGroupBTN.clicked.connect(self.groupQuery)
        self.uiRemoveBTN.clicked.connect(self.removeQuery)
    
    def addQuery( self ):
        """
        Sets the query for this widget from the quick query text builder.
        """
        insert_item = self.uiQueryTREE.currentItem()
        if ( insert_item and not insert_item.isSelected() ):
            insert_item = None
        
        # create the query
        if ( self.uiQueryTXT.text() ):
            query = Q.fromString(nativestring(self.uiQueryTXT.text()))
            self.uiQueryTXT.setText('')
        else:
            query = Q()
        
        # determine where to create the item at
        tree = self.uiQueryTREE
        
        if ( not insert_item ):
            # determine if we are already joining queries together
            count = tree.topLevelItemCount()
            
            # create the first item
            if ( not count ):
                XQueryItem(tree, query)
            else:
                if ( 1 < count ):
                    join = tree.topLevelItem(count - 2).text(0)
                else:
                    join = 'and'
                
                # create the join item & query item
                XJoinItem(tree, join)
                XQueryItem(tree, query)
        
        # add a query into a group
        elif ( insert_item.childCount() ):
            count = insert_item.childCount()
            join = insert_item.child(count - 2).text(0)
            
            # add the query to the group
            XJoinItem(insert_item, join)
            XQueryItem(tree, query)
        
        # add a query underneath another item
        else:
            parent_item = insert_item.parent()
            
            # add into the tree
            if ( not parent_item ):
                count = tree.topLevelItemCount()
                index = tree.indexOfTopLevelItem(insert_item)
                
                # add to the end
                if ( index == count - 1 ):
                    if ( 1 < count ):
                        join = tree.topLevelItem(count - 2).text(0)
                    else:
                        join = 'and'
                    
                    XJoinItem(tree, join)
                    XQueryItem(tree, query)
                
                # insert in the middle
                else:
                    join_item = tree.topLevelItem(index + 1)
                    join = join_item.text(0)
                    XJoinItem(tree, join, preceeding = join_item)
                    XQueryItem(tree, query, preceeding = join_item)
            else:
                count = parent_item.childCount()
                index = parent_item.indexOfChild(insert_item)
                
                # add to the end
                if ( index == count - 1 ):
                    if ( 1 < count ):
                        join = parent_item.child(count - 2).text(0)
                    else:
                        join = 'and'
                    
                    XJoinItem(parent_item, join)
                    XQueryItem(parent_item, query)
                
                # insert in the middle
                else:
                    join_item = parent_item.child(index + 1)
                    join = join_item.text(0)
                    XJoinItem(parent_item, join, preceeding = join_item)
                    XQueryItem(parent_item, join, preceeding = join_item)
    
    def clear( self ):
        """
        Clears the query information.
        """
        self.uiQueryTREE.clear()
    
    def eventFilter( self, object, event ):
        """
        Filters the object for particular events.
        
        :param      object | <QObject>
                    event  | <QEvent>
        
        :return     <bool> | consumed
        """
        if ( event.type() == event.KeyPress ):
            if ( event.key() in (Qt.Key_Return, Qt.Key_Enter) ):
                self.addQuery()
                return True
        
        return False
    
    def factory( self ):
        """
        Returns the factory linked with this query widget.
        
        :return     <XOrbBrowserFactory>
        """
        return self._factory
    
    def groupQuery( self ):
        """
        Groups the selected items together into a sub query
        """
        items = self.uiQueryTREE.selectedItems()
        if ( not len(items) > 2 ):
            return
        
        if ( isinstance(items[-1], XJoinItem) ):
            items = items[:-1]
        
        tree   = self.uiQueryTREE
        parent = items[0].parent()
        if ( not parent ):
            parent = tree
        
        preceeding = items[-1]
        
        tree.blockSignals(True)
        tree.setUpdatesEnabled(False)
        
        grp_item = XQueryItem(parent, Q(), preceeding = preceeding)
        for item in items:
            parent = item.parent()
            if ( not parent ):
                tree.takeTopLevelItem(tree.indexOfTopLevelItem(item))
            else:
                parent.takeChild(parent.indexOfChild(item))
            grp_item.addChild(item)
        grp_item.update()
        
        tree.blockSignals(False)
        tree.setUpdatesEnabled(True)
    
    def query( self ):
        """
        Returns the query this widget is representing from the tree widget.
        
        :return     <Query> || <QueryCompound> || None
        """
        # build a query if not searching all
        q        = Q()
        operator = 'and'
        
        for i in range(self.uiQueryTREE.topLevelItemCount()):
            item = self.uiQueryTREE.topLevelItem(i)
            
            if ( isinstance(item, XQueryItem) ):
                if ( operator == 'and' ):
                    q &= item.query()
                else:
                    q |= item.query()
            else:
                operator = nativestring(item.text(0))
        return q
    
    def removeQuery( self ):
        """
        Removes the currently selected query.
        """
        items = self.uiQueryTREE.selectedItems()
        tree  = self.uiQueryTREE
        for item in items:
            parent = item.parent()
            if ( parent ):
                parent.takeChild(parent.indexOfChild(item))
            else:
                tree.takeTopLevelItem(tree.indexOfTopLevelItem(item))
        
        self.setQuery(self.query())
    
    def schema( self ):
        """
        Returns the schema that is linked with the table assigned to this widget
        
        :return     <orb.TableSchema> || None
        """
        if ( self._tableType ):
            return self._tableType.schema()
        return None
    
    def setFactory( self, factory ):
        """
        Sets the orb factory used for bridging the gap between the interface and
        the ORB classes.
        
        :param      factory | <XOrbBrowserFactory>
        """
        self._factory = factory
    
    def setFocus( self ):
        """
        Sets the focus for this widget.
        """
        super(XOrbQueryWidget, self).setFocus()
        self.uiQueryTXT.setFocus()
    
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
        
        # assign a top level query item
        if ( Q.typecheck(query) and not query.isNull() ):
            XQueryItem(tree, query)
        
        # assign a top level query group
        elif ( QueryCompound.typecheck(query) and not query.isNull() ):
            op_name = QueryCompound.Op[query.operatorType()].lower()
            
            for i, sub_query in enumerate(query.queries()):
                if ( i ):
                    XJoinItem(tree, op_name)
                
                XQueryItem(tree, sub_query)
            
        tree.resizeToContents()
        tree.setUpdatesEnabled(True)
        tree.blockSignals(False)
    
    def setTableType( self, tableType ):
        """
        Sets the table type instance for this query widget.
        
        :param      tableType | <orb.Table>
        """
        self._tableType = tableType
    
    def tableType( self ):
        """
        Returns the table type for this query widget.
        
        :return     <orb.Table> || None
        """
        return self._tableType
    
    def updateQueryItem( self, item ):
        """
        Updates the query tree item by either showing its expanded data or
        hiding it based on its collapse state.
        """
        item.update()