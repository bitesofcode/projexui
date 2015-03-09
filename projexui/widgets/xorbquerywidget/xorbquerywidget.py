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

try:
    from orb import Query, QueryCompound
except ImportError:
    Query = None
    QueryCompound = None

from .xorbqueryplugin import XOrbQueryPluginFactory
from .xorbquerycontainer import XOrbQueryContainer
from projexui.qt import Property
from projexui.widgets.xstackedwidget import XStackedWidget

import projexui

class XOrbQueryWidget(XStackedWidget):
    """ """
    __designer_group__ = 'ProjexUI - ORB'
    
    def __init__( self, parent = None ):
        super(XOrbQueryWidget, self).__init__( parent )
        
        # define custom properties
        self._pluginFactory = XOrbQueryPluginFactory()
        self._loadQuery     = None
        self._tableType     = None
        self._compoundStack = []
        self._initialized   = False
        self._showReferencePlugins = True
        
        self.clear()
        self.setMinimumWidth(575)
        self.setMinimumHeight(145)
        
        # create connections
        self.animationFinished.connect(self.cleanupContainers)
    
    def addContainer(self, query):
        """
        Creates a new query container widget object and slides it into
        the frame.
        
        :return     <XOrbQueryContainer>
        """
        self.setUpdatesEnabled(False)
        self.blockSignals(True)
        container = XOrbQueryContainer(self)
        
        # setup properties
        container.setShowBack(self.count() > 0)
        
        # create connections
        container.enterCompoundRequested.connect(self.enterContainer)
        container.exitCompoundRequested.connect(self.exitContainer)
        
        # show the widget
        self.addWidget(container)
        self.setUpdatesEnabled(True)
        self.blockSignals(False)
        
        container.setQuery(query)
        self.slideInNext()
        return container
    
    def clear(self):
        """
        Clears all the container for this query widget.
        """
        for i in range(self.count()):
            widget = self.widget(i)
            if widget is not None:
                widget.close()
                widget.setParent(None)
                widget.deleteLater()
    
    def cleanupContainers(self):
        """
        Cleans up all containers to the right of the current one.
        """
        for i in range(self.count() - 1, self.currentIndex(), -1):
            widget = self.widget(i)
            widget.close()
            widget.setParent(None)
            widget.deleteLater()
    
    def containerFor(self, entry):
        """
        Returns a container for the inputed entry widget.
        
        :param      entry | <XOrbQueryEntryWidget>
        
        :return     <XOrbQueryContainer> || None
        """
        try:
            index = self._compoundStack.index(entry)
        except ValueError:
            return None
        
        return self.widget(index + 1)
    
    def currentContainer(self):
        """
        Returns the current query container.
        
        :return     <XOrbQueryContainer>
        """
        return self.currentWidget()
    
    def currentQuery(self):
        """
        Returns the current query for the active container.  This will reflect
        what is currently visible to the user.
        
        :return     <orb.Query>
        """
        container = self.currentContainer()
        if container:
            return container.query()
        return Query()
    
    def enterContainer(self, entry, query):
        """
        Enters a new container for the given entry widget.
        
        :param      entry | <XOrbQueryEntryWidget> || None
        """
        self._compoundStack.append(entry)
        self.addContainer(query)
    
    def exitContainer(self):
        """
        Removes the current query container.
        """
        try:
            entry = self._compoundStack.pop()
        except IndexError:
            return
        
        container = self.currentContainer()
        entry.setQuery(container.query())
        
        self.slideInPrev()
    
    def query(self):
        """
        Returns the full query for this widget.  This will reflect the complete
        combined query for all containers within this widget.
        
        :return     <orb.Query>
        """
        if self._loadQuery is not None:
            return self._loadQuery
        
        container = self.widget(0)
        if container:
            query = container.query()
        else:
            query = Query()
        
        return query
    
    def pluginFactory(self):
        """
        Returns the plugin factory that will be used to generate plugins for
        the query selector.  You can subclass the XOrbQueryPlugin and
        XOrbQueryPluginFactory to create custom plugins for schemas and widgets.
        
        :return     <XOrbQueryPluginFactory>
        """
        return self._pluginFactory
    
    def reset(self):
        """
        Resets this query builder to a blank query.
        """
        self.setQuery(Query())
    
    def setCurrentQuery(self, query):
        """
        Sets the query for the current container widget.  This will only change
        the active container, not parent containers.  You should use the
        setQuery method to completely assign a query to this widget.
        
        :param      query | <orb.Query>
        """
        container = self.currentContainer()
        if container:
            container.setQuery(query)
    
    def setQuery(self, query):
        """
        Sets the query for this widget to the inputed query.  This will clear
        completely the current inforamation and reest all containers to the
        inputed query information.
        
        :param      query | <orb.Query>
        """
        if not self.isVisible():
            self._loadQuery = query
        else:
            self._loadQuery = None
            
            if self._initialized and hash(query) == hash(self.query()):
                return
            
            self._initialized = True
            self.clear()
            self.addContainer(query)
    
    def setPluginFactory(self, factory):
        """
        Assigns the plugin factory for this query widget to the inputed factory.
        You can use this to create custom handlers for columns when your schema
        is being edited.
        
        :param      factory | <XOrbQueryPluginFactory>
        """
        self._pluginFactory = factory
    
    def setShowReferencePlugins(self, state=True):
        """
        Sets whether or not reference based plugins will be displayed to the
        user.
        
        :param      state | <bool>
        """
        self._showReferencePlugins = state
    
    def showReferencePlugins(self):
        """
        Returns whether or not reference based plugins will be displayed to the
        user.
        
        :return     <bool>
        """
        return self._showReferencePlugins
    
    def showEvent(self, event):
        if self._loadQuery is not None:
            self.setQuery(self._loadQuery)
        elif not self._initialized:
            self.setQuery(Query())
    
    def setTableType(self, tableType):
        """
        Sets the table type for this instance to the given type.
        
        :param      tableType | <orb.Table>
        """
        if tableType == self._tableType:
            return
        
        self._initialized = False
        self._tableType = tableType
        self.setQuery(Query())
        
    def tableType(self):
        """
        Returns the table type instance for this widget.
        
        :return     <subclass of orb.Table>
        """
        return self._tableType

    x_showReferencePlugins = Property(bool,
                                      showReferencePlugins,
                                      setShowReferencePlugins)

