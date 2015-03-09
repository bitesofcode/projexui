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
from projexui.qt.QtCore   import Qt

from projexui.qt.QtGui    import QWidget,\
                                 QVBoxLayout

import projexui

from projexui.widgets.xquerybuilderwidget.xqueryrule \
                                        import XQueryRule

from projexui.widgets.xquerybuilderwidget.xquerylinewidget \
                                        import XQueryLineWidget

class XQueryBuilderWidget(QWidget):
    """ """
    saveRequested   = Signal()
    resetRequested  = Signal()
    cancelRequested = Signal()
    
    def __init__( self, parent = None ):
        super(XQueryBuilderWidget, self).__init__( parent )
        
        # load the user interface
        projexui.loadUi(__file__, self)
        
        self.setMinimumWidth(470)
        
        # define custom properties
        self._rules           = {}
        self._defaultQuery    = []
        self._completionTerms = []
        self._minimumCount    = 1
        
        # set default properties
        self._container = QWidget(self)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addStretch(1)
        self._container.setLayout(layout)
        self.uiQueryAREA.setWidget(self._container)
        
        # create connections
        self.uiResetBTN.clicked.connect(  self.emitResetRequested )
        self.uiSaveBTN.clicked.connect(   self.emitSaveRequested )
        self.uiCancelBTN.clicked.connect( self.emitCancelRequested )
        
        self.resetRequested.connect(      self.reset )
    
    def addLineWidget( self, query = None ):
        """
        Adds a new line widget to the system with the given values.
        
        :param      query | (<str> term, <str> operator, <str> vlaue) || None
        """
        widget = XQueryLineWidget(self)
        widget.setTerms(sorted(self._rules.keys()))
        widget.setQuery(query)
        
        index = self._container.layout().count() - 1
        self._container.layout().insertWidget(index, widget)
        
        widget.addRequested.connect(     self.addLineWidget )
        widget.removeRequested.connect(  self.removeLineWidget )
        
        # update the remove enabled options for these widgets
        self.updateRemoveEnabled()
    
    def addRule( self, rule ):
        """
        Adds a rule to the system.
        
        :param      rule | <XQueryRule>
        """
        self._rules[rule.term()] = rule
        self.updateRules()
    
    def clear( self ):
        """
        Clears out all the widgets from the system.
        """
        for lineWidget in self.lineWidgets():
            lineWidget.setParent(None)
            lineWidget.deleteLater()
    
    def completionTerms( self ):
        """
        Returns the list of terms that will be used as a global override
        for completion terms when the query rule generates a QLineEdit instance.
        
        :return     [<str>, ..]
        """
        return self._completionTerms
    
    def count( self ):
        """
        Returns the count of the line widgets in the system.
        
        :return     <int>
        """
        return len(self.lineWidgets())
    
    def currentQuery( self ):
        """
        Returns the current query string for this widget.
        
        :return     [(<str> term, <str> operator, <str> value), ..]
        """
        widgets = self.lineWidgets()
        output = []
        for widget in widgets:
            output.append(widget.query())
        return output
    
    def defaultQuery( self ):
        """
        Returns the default query for the system.
        
        :return     [(<str> term, <str> operator, <str> value), ..]
        """
        return self._defaultQuery
    
    def keyPressEvent( self, event ):
        """
        Emits the save requested signal for this builder for when the enter
        or return press is clicked.
        
        :param      event | <QKeyEvent>
        """
        if ( event.key() in (Qt.Key_Enter, Qt.Key_Return) ):
            self.emitSaveRequested()
        
        super(XQueryBuilderWidget, self).keyPressEvent(event)
    
    def emitCancelRequested( self ):
        """
        Emits the cancel requested signal.
        """
        if ( not self.signalsBlocked() ):
            self.cancelRequested.emit()
            
    def emitResetRequested( self ):
        """
        Emits the reste requested signal.
        """
        if ( not self.signalsBlocked() ):
            self.resetRequested.emit()
            
    def emitSaveRequested( self ):
        """
        Emits the save requested signal.
        """
        if ( not self.signalsBlocked() ):
            self.saveRequested.emit()
    
    def findRule( self, term ):
        """
        Looks up a rule by the inputed term.
        
        :param      term | <str>
        
        :return     <XQueryRule> || None
        """
        return self._rules.get(nativestring(term))
    
    def removeLineWidget( self, widget ):
        """
        Removes the line widget from the query.
        
        :param      widget | <XQueryLineWidget>
        """
        widget.setParent(None)
        widget.deleteLater()
        
        self.updateRemoveEnabled()
    
    def minimumCount( self ):
        """
        Defines the minimum number of query widgets that are allowed.
        
        :return     <int>
        """
        return self._minimumCount
    
    def lineWidgets( self ):
        """
        Returns a list of line widgets for this system.
        
        :return     [<XQueryLineWidget>, ..]
        """
        return self.findChildren(XQueryLineWidget)
    
    def reset( self ):
        """
        Resets the system to the default query.
        """
        self.setCurrentQuery(self.defaultQuery())
    
    def setCompletionTerms( self, terms ):
        """
        Sets the list of terms that will be used as a global override
        for completion terms when the query rule generates a QLineEdit instance.
        
        :param     terms | [<str>, ..]
        """
        self._completionTerms = terms
    
    def setCurrentQuery( self, query ):
        """
        Sets the query for this system to the inputed query.
        
        :param      query | [(<str> term, <str> operator, <str> value), ..]
        """
        self.clear()
        
        for entry in query:
            self.addLineWidget(entry)
        
        # make sure we have the minimum number of widgets
        for i in range(self.minimumCount() - len(query)):
            self.addLineWidget()
    
    def setDefaultQuery( self, query ):
        """
        Sets the default query that will be used when the user clicks on the \
        reset button or the reset method is called.
        
        :param      query | [(<str> term, <str> operator, <str> value), ..]
        """
        self._defaultQuery = query[:]
    
    def setMinimumCount( self, count ):
        """
        Sets the minimum number of line widgets that are allowed at any \
        given time.
        
        :param      count | <int>
        """
        self._minimumCount = count
    
    def setRules( self, rules ):
        """
        Sets all the rules for this builder.
        
        :param      rules | [<XQueryRule>, ..]
        """
        if ( type(rules) in (list, tuple) ):
            self._rules = dict([(x.term(), x) for x in rules])
            self.updateRules()
            return True
            
        elif ( type(rules) == dict ):
            self._rules = rules.copy()
            self.updateRules()
            return True
            
        else:
            return False
    
    def setTerms( self, terms ):
        """
        Sets a simple rule list by accepting a list of strings for terms.  \
        This is a convenience method for the setRules method.
        
        :param      rules | [<str> term, ..]
        """
        return self.setRules([XQueryRule(term = term) for term in terms])
    
    def updateRemoveEnabled( self ):
        """
        Updates the remove enabled baesd on the current number of line widgets.
        """
        lineWidgets = self.lineWidgets()
        count       = len(lineWidgets)
        state       = self.minimumCount() < count
        
        for widget in lineWidgets:
            widget.setRemoveEnabled(state)
    
    def updateRules( self ):
        """
        Updates the query line items to match the latest rule options.
        """
        terms = sorted(self._rules.keys())
        for child in self.lineWidgets():
            child.setTerms(terms)