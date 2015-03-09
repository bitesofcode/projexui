#!/usr/bin/python

""" Defines an interface to allow users to build their queries on the fly. """

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

from projexui.qt import Signal
from projexui.qt.QtGui  import QWidget,\
                               QLineEdit,\
                               QCompleter,\
                               QStandardItemModel,\
                               QStandardItem

import projexui
from projexui.completers.xquerycompleter import XQueryCompleter

#------------------------------------------------------------------------------

class XQueryLineWidget(QWidget):
    """ """
    addRequested        = Signal()
    removeRequested     = Signal(QWidget)
    
    def __init__( self, parent = None ):
        super(XQueryLineWidget, self).__init__( parent )
        
        # load the user interface
        projexui.loadUi(__file__, self)
        
        # define custom properties
        self._currentRule = None
        
        # create connections
        self.uiTermDDL.currentIndexChanged.connect( self.applyRule )
        self.uiOperatorDDL.currentIndexChanged.connect( self.updateEditor )
        
        self.uiAddBTN.clicked.connect(      self.emitAddRequested )
        self.uiRemoveBTN.clicked.connect(   self.emitRemoveRequested )
    
    def applyRule( self ):
        """
        Applies the rule from the builder system to this line edit.
        """
        widget = self.queryBuilderWidget()
        if ( not widget ):
            return
        
        rule = widget.findRule(self.uiTermDDL.currentText())
        self.setCurrentRule(rule)
    
    def currentRule( self ):
        """
        Returns the current rule that this line is using to calculate its \
        values.
        
        :return     <XQueryRule> || None
        """
        return self._currentRule
    
    def currentOperator( self ):
        """
        Returns the current operator for this widget.
        
        :return     <str>
        """
        return nativestring(self.uiOperatorDDL.currentText())
    
    def emitAddRequested( self ):
        """
        Emits the add requested signal for this item provided its signals \
        are not currently blocked.
        """
        if ( not self.signalsBlocked() ):
            self.addRequested.emit()
            
    def emitRemoveRequested( self ):
        """
        Emits the remove requested signal for this item provided its signals \
        are not currently blocked.
        """
        if ( not self.signalsBlocked() ):
            self.removeRequested.emit(self)
            
    def isAddEnabled( self ):
        """
        Returns whether or not there is an add enabled option for this item.
        
        :return     <bool>
        """
        return self.uiAddBTN.isEnabled()
    
    def isOperatorEnabled( self ):
        """
        Returns whether or not altering the operator is enabled for this item.
        
        :return     <bool>
        """
        return self.uiOperatorDDL.isEnabled()
    
    def isRemoveEnabled( self ):
        """
        Returns whether or not there is a remove enabled option for this item.
        
        :return     <bool>
        """
        return self.uiRemoveBTN.isEnabled()
    
    def isValueEnabled( self ):
        """
        Returns whether or not altering the value is enabled for this item.
        
        :return     <bool>
        """
        return self.uiWidgetAREA.isEnabled()
    
    def isTermEnabled( self ):
        """
        Returns whether or not altering the term is enabled for this item.
        
        :return     <bool>
        """
        return self.uiTermDDL.isEnabled()
    
    def query( self ):
        """
        Returns the query that will be used for the widget.
        
        :return     (<str> term, <str> operator, <str> value)
        """
        widget = self.uiWidgetAREA.widget()
        if ( widget and type(widget) != QWidget ):
            value = nativestring(widget.text())
        else:
            value = ''
        
        op = nativestring(self.uiOperatorDDL.currentText())
        if ( self.currentRule() ):
            op = self.currentRule().labelOperator(op)
        
        return (nativestring(self.uiTermDDL.currentText()), op, value)
    
    def queryBuilderWidget( self ):
        """
        Returns the query builder widget instance that this widget is \
        associated with.
        
        :return     <XQueryBuilderWidget>
        """
        from projexui.widgets.xquerybuilderwidget import XQueryBuilderWidget
        
        builder = self.parent()
        while ( builder and not isinstance(builder, XQueryBuilderWidget) ):
            builder = builder.parent()
        
        return builder
    
    def setAddEnabled( self, state ):
        """
        Sets whether or not there is an add enabled option for this item.
        
        :param      state | <bool>
        """
        self.uiAddBTN.setEnabled(state)
    
    def setCurrentRule( self, rule ):
        """
        Sets the current query rule for this widget, updating its widget \
        editor if the types do not match.
        
        :param      rule | <QueryRule> || None
        """
        curr_rule = self.currentRule()
        if ( curr_rule == rule ):
            return
        
        self._currentRule = rule
        
        curr_op     = self.uiOperatorDDL.currentText()
        self.uiOperatorDDL.blockSignals(True)
        self.uiOperatorDDL.clear()
        if ( rule ):
            self.uiOperatorDDL.addItems(rule.operators())
            index = self.uiOperatorDDL.findText(curr_op)
            if ( index != -1 ):
                self.uiOperatorDDL.setCurrentIndex(index)
                
        self.uiOperatorDDL.blockSignals(False)
        
        self.updateEditor()
        
    def setOperatorEnabled( self, state ):
        """
        Sets whether or not altering the operator is enabled for this item.
        
        :param      state | <bool>
        """
        self.uiOperatorDDL.setEnabled(state)
    
    def setQuery( self, query ):
        """
        Sets the query that is used for this widget to the inputed query.
        
        :param      query | (<str> term, <str> operator, <str> value)
        
        :return     <bool> | success
        """
        if ( not (type(query) in (list, tuple) and len(query) == 3) ):
            return False
        
        term, op, value = query
        
        if ( self.currentRule() ):
            op = self.currentRule().operatorLabel(op)
        
        self.uiTermDDL.setCurrentIndex(self.uiTermDDL.findText(term))
        self.applyRule()
        
        self.uiOperatorDDL.setCurrentIndex(self.uiOperatorDDL.findText(op))
        
        widget = self.uiWidgetAREA.widget()
        if ( widget and not type(widget) == QWidget ):
            widget.setText(value)
        
        return True
    
    def setRemoveEnabled( self, state ):
        """
        Sets whether or not there is a remove enabled option for this item.
        
        :param      state | <bool>
        """
        self.uiRemoveBTN.setEnabled(state)
    
    def setValueEnabled( self, state ):
        """
        Sets whether or not altering the value is enabled for this item.
        
        :param      state | <bool>
        """
        self.uiWidgetAREA.setEnabled(state)
    
    def setTermEnabled( self, state ):
        """
        Sets whether or not altering the term is enabled for this item.
        
        :param      state | <bool>
        """
        self.uiTermDDL.setEnabled(state)
    
    def setTerms( self, terms ):
        """
        Sets the term options for this widget.
        
        :param      terms | [<str>, ..]
        """
        self.uiTermDDL.blockSignals(True)
        
        term = self.uiTermDDL.currentText()
        self.uiTermDDL.clear()
        self.uiTermDDL.addItems(terms)
        self.uiTermDDL.setCurrentIndex(self.uiTermDDL.findText(term))
        self.applyRule()
        self.uiTermDDL.blockSignals(False)
    
    def updateEditor( self ):
        """
        Updates the editor based on the current selection.
        """
        
        # assignt the rule operators to the choice list
        rule        = self.currentRule()
        operator    = self.currentOperator()
        widget      = self.uiWidgetAREA.widget()
        editorType  = None
        text        = ''
        
        if ( rule ):
            editorType = rule.editorType(operator)
        
        # no change in types
        if ( widget and editorType and type(widget) == editorType ):
            return
            
        elif ( widget ):
            if ( type(widget) != QWidget ):
                text = widget.text()
            
            widget.setParent(None)
            widget.deleteLater()
        
        self.uiWidgetAREA.setWidget(None)
        
        # create the new editor
        if ( editorType ):
            widget = editorType(self)
            
            if ( isinstance(widget, QLineEdit) ):
                terms  = rule.completionTerms()
                if ( not terms ):
                    qwidget = self.queryBuilderWidget()
                    if ( qwidget ):
                        terms = qwidget.completionTerms()
                
                if ( terms ):
                    widget.setCompleter(XQueryCompleter(terms, widget))
            
            self.uiWidgetAREA.setWidget(widget)
            
            if ( type(widget) != QWidget ):
                widget.setText(text)
    