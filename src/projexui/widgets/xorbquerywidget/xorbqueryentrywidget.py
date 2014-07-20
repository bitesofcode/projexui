""" [desc] """

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

from projexui.qt import Signal, SIGNAL, Slot
from projexui.qt.QtCore import Qt
from projexui.qt.QtGui import QWidget, QPalette
from projexui.widgets.xlineedit import XLineEdit
from projexui.widgets.xorbcolumnnavigator import XOrbColumnNavigator

from orb import Query, QueryCompound

import projexui

class XOrbQueryEntryWidget(QWidget):
    """ """
    def __init__(self, parent, tableType):
        super(XOrbQueryEntryWidget, self).__init__( parent )
        
        # load the user interface
        projexui.loadUi(__file__, self)
        
        # define custom properties
        self._queryWidget       = parent.queryWidget()
        self._containerWidget   = parent
        self._tableType         = tableType
        self._query             = None
        self._first             = False
        self._last              = False
        self._checked           = False
        
        self.uiEditorAREA.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        # set default properties
        font = self.font()
        font.setPointSize(9)
        font.setBold(True)
        
        self.uiJoinSBTN.setFont(font)
        self.uiColumnDDL.setTableType(tableType)
        
        # create connections (use old-style syntax or PySide errors out)
        self.connect(self.uiSelectBTN, SIGNAL('clicked()'), self.toggleChecked)
        self.connect(self.uiJoinSBTN, SIGNAL('clicked()'), self.addEntry)
        self.connect(self.uiRemoveBTN, SIGNAL('clicked()'), self.removeEntry)
        self.connect(self.uiEnterBTN, SIGNAL('clicked()'), self.enterCompound)
        self.connect(self.uiOperatorDDL,
                     SIGNAL('currentIndexChanged(int)'),
                     self.assignEditor)
        
        self.uiColumnDDL.schemaColumnChanged.connect(self.assignPlugin)
    
    @Slot()
    def addEntry(self):
        """
        This will either add a new widget or switch the joiner based on the
        state of the entry
        """
        joiner = self.joiner()
        curr_joiner = self._containerWidget.currentJoiner()
        
        # update the joining option if it is modified
        if joiner != curr_joiner:
            if not self._last:
                self.updateJoin()
                return
            
            self._containerWidget.setCurrentJoiner(joiner)
        
        # otherwise, add a new entry
        self._containerWidget.addEntry(entry=self)
    
    @Slot()
    def assignPlugin(self):
        """
        Assigns an editor based on the current column for this schema.
        """
        self.uiOperatorDDL.blockSignals(True)
        self.uiOperatorDDL.clear()
        
        plugin = self.currentPlugin()
        if plugin:
            flags = 0
            if not self.queryWidget().showReferencePlugins():
                flags |= plugin.Flags.ReferenceRequired
            
            self.uiOperatorDDL.addItems(plugin.operators(ignore=flags))
        
        self.uiOperatorDDL.blockSignals(False)
        self.assignEditor()
    
    @Slot()
    def assignEditor(self):
        """
        Assigns the editor for this entry based on the plugin.
        """
        plugin = self.currentPlugin()
        column = self.currentColumn()
        value = self.currentValue()
        
        if not plugin:
            self.setEditor(None)
            return
        
        self.setUpdatesEnabled(False)
        self.blockSignals(True)
        op = self.uiOperatorDDL.currentText()
        self.setEditor(plugin.createEditor(self, column, op, value))
        self.setUpdatesEnabled(True)
        self.blockSignals(False)
    
    def currentColumn(self):
        return self.uiColumnDDL.currentSchemaColumn()
    
    def currentPlugin(self):
        column = self.currentColumn()
        if not column:
            return None
        
        return self.pluginFactory().plugin(column)
    
    def currentValue(self):
        plugin = self.currentPlugin()
        value = None
        if plugin:
            value = plugin.editorValue(self.editor())
        
        if value is None and self._query is not None:
            q_value = self._query.value()
            if q_value != Query.UNDEFINED:
                value = q_value
        
        return value
    
    def editor(self):
        """
        Returns the editor instance for this widget.
        
        :return     <QWidget> || None
        """
        return self.uiEditorAREA.widget()
    
    @Slot()
    def enterCompound(self):
        self._containerWidget.enterCompound(self, self.query())
    
    def isChecked(self):
        """
        Returns whether or not this widget is checked.
        
        :return     <bool>
        """
        return self._checked
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MidButton:
            self.setChecked(not self.isChecked())
        
        super(XOrbQueryEntryWidget, self).mousePressEvent(event)
    
    def query(self):
        """
        Returns the query instance for this widget.
        
        :return     <orb.Query> || <orb.QueryCompound>
        """
        queryWidget = self.queryWidget()
        
        # check to see if there is an active container for this widget
        container = queryWidget.containerFor(self)
        if container:
            return container.query()
        
        elif QueryCompound.typecheck(self._query):
            return self._query
        
        # generate a new query from the editor
        column = self.uiColumnDDL.currentSchemaPath()
        plugin = self.currentPlugin()
        editor = self.editor()
        op     = self.uiOperatorDDL.currentText()
        
        if column and plugin:
            query = Query(column)
            plugin.setupQuery(query, op, editor)
            return query
        else:
            return Query()
    
    def joiner(self):
        """
        Returns the joiner operator type for this entry widget.
        
        :return     <QueryCompound.Op>
        """
        act = self.uiJoinSBTN.currentAction()
        if not act:
            return None
        elif act.text() == 'AND':
            return QueryCompound.Op.And
        return QueryCompound.Op.Or
    
    def queryWidget(self):
        return self._queryWidget
    
    def pluginFactory(self):
        return self._queryWidget.pluginFactory()
    
    def refreshButtons(self):
        """
        Refreshes the buttons for building this sql query.
        """
        last = self._last
        first = self._first
        
        joiner = self._containerWidget.currentJoiner()
        
        # the first button set can contain the toggle options
        if first:
            self.uiJoinSBTN.setActionTexts(['AND', 'OR'])
        elif joiner == QueryCompound.Op.And:
            self.uiJoinSBTN.setActionTexts(['AND'])
        else:
            self.uiJoinSBTN.setActionTexts(['OR'])
        
        # the last option should not show an active action
        if last:
            self.uiJoinSBTN.setCurrentAction(None)
        
        # otherwise, highlight the proper action
        else:
            act = self.uiJoinSBTN.findAction(QueryCompound.Op[joiner].upper())
            self.uiJoinSBTN.setCurrentAction(act)
        
        enable = QueryCompound.typecheck(self._query) or self.isChecked()
        self.uiEnterBTN.setEnabled(enable)
    
    @Slot()
    def removeEntry(self):
        self._containerWidget.removeEntry(self)
    
    def setChecked(self, state):
        self._checked = state
        if state:
            self.setBackgroundRole(QPalette.Highlight)
            self.setAutoFillBackground(True)
        else:
            self.setBackgroundRole(QPalette.Window)
            self.setAutoFillBackground(False)
        
        enable = QueryCompound.typecheck(self._query) or self.isChecked()
        self.uiEnterBTN.setEnabled(enable)
    
    def setEditor(self, editor):
        """
        Sets the editor widget for this entry system.
        
        :param      editor | <QWidget> || None
        """
        widget = self.uiEditorAREA.takeWidget()
        if widget:
            widget.close()
        
        if editor is not None:
            editor.setMinimumHeight(28)
            self.uiEditorAREA.setWidget(editor)
    
    def setQuery(self, query):
        """
        Sets the query instance for this widget to the inputed query.
        
        :param      query | <orb.Query> || <orb.QueryCompound>
        """
        if not query.isNull() and hash(query) == hash(self._query):
            return
        
        self._query = query
        
        if QueryCompound.typecheck(query):
            self.uiColumnDDL.hide()
            self.uiOperatorDDL.hide()
            
            # setup the compound editor
            editor = XLineEdit(self)
            editor.setReadOnly(True)
            editor.setText(query.name() + ' %s' % nativestring(query))
            editor.setHint(nativestring(query))
            
            self.setEditor(editor)
        
        else:
            self.uiColumnDDL.show()
            self.uiOperatorDDL.show()
            
            text = query.columnName()
            self.uiColumnDDL.setCurrentSchemaPath(nativestring(text))
            
            self.uiOperatorDDL.blockSignals(True)
            plug = self.currentPlugin()
            if plug:
                op = plug.operator(query.operatorType(), query.value())
                
                index = self.uiOperatorDDL.findText(op)
                if index != -1:
                    self.uiOperatorDDL.setCurrentIndex(index)
            
            self.uiOperatorDDL.blockSignals(False)
        
        self.refreshButtons()
    
    def setFirst(self, first):
        self._first = first
        self.refreshButtons()
    
    def setLast(self, last):
        self._last = last
        self.refreshButtons()
        
    def setJoiner(self, joiner):
        """
        Sets the join operator type for this entry widget to the given value.
        
        :param      joiner | <QueryCompound.Op>
        """
        text = QueryCompound.Op[joiner].upper()
        
        if self._first:
            if self._last:
                self.uiJoinSBTN.setCurrentAction(None)
            else:
                act = self.uiJoinSBTN.findAction(text)
                self.uiJoinSBTN.setCurrentAction(act)
        else:
            self.uiJoinSBTN.actions()[0].setText(text)
    
    def updateJoin(self):
        """
        Updates the joining method used by the system.
        """
        text = self.uiJoinSBTN.currentAction().text()
        if text == 'AND':
            joiner = QueryCompound.Op.And
        else:
            joiner = QueryCompound.Op.Or
        
        self._containerWidget.setCurrentJoiner(self.joiner())
    
    def tableType(self):
        return self._tableType
    
    def toggleChecked(self):
        """
        Toggles the selected state for this entry widget.
        """
        self.setChecked(not self.isChecked())