#!/usr/bin/python

""" Defines a widget for editing orb records within a grid. """

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

from xml.etree import ElementTree

from projexui.qt import Property
from projexui.qt.QtCore import Qt, QSize
from projexui.qt.QtGui import QWidget, QAction, QHBoxLayout
from projexui.widgets.xorbquerywidget   import XOrbQueryWidget
from projexui.widgets.xorbtreewidget    import XOrbRecordItem
from projexui.widgets.xpopupwidget      import XPopupWidget

import projexui

try:
    from orb import Query as Q

except ImportError:
    logger.warning('The XOrbGridEdit will not work without the orb package.')
    RecordSet = None
    Orb = None
    Q = None

#----------------------------------------------------------------------

class XOrbGridEdit(QWidget):
    """ """
    __designer_group__ = 'ProjexUI - ORB'
    
    def __init__( self, parent = None ):
        super(XOrbGridEdit, self).__init__( parent )
        
        # load the user interface
        projexui.loadUi(__file__, self)
        
        # define custom properties
        self._queryWidget = XOrbQueryWidget(self)
        
        self.uiSaveBTN.hide()
        self.uiSearchTXT.setIconSize(QSize(28, 28))
        self.uiSearchTXT.addButton(self.uiQueryBTN)
        
        self.uiQueryBTN.setCentralWidget(self._queryWidget)
        self.uiQueryBTN.setDefaultAnchor(XPopupWidget.Anchor.TopRight)
        popup = self.uiQueryBTN.popupWidget()
        popup.setShowTitleBar(False)

        # set default properties
        self.uiRecordTREE.setUserGroupingEnabled(False)
        self.uiRecordTREE.setGroupingActive(False)
        self.uiRecordTREE.setEditable(False)
        self.uiRecordTREE.setPageSize(50)
        self.uiRecordTREE.setTabKeyNavigation(True)
        
        # create connections
        self.uiRefreshBTN.clicked.connect(self.refresh)
        self.uiSaveBTN.clicked.connect(self.commit)
        self.uiQueryBTN.popupAboutToShow.connect(self.loadQuery)
        self.uiQueryBTN.popupAccepted.connect(self.assignQuery)
        
        popup.resetRequested.connect(self._queryWidget.reset)
    
    def addWidget(self, widget, align=Qt.AlignLeft, before=None):
        """
        Adds a widget to the grid edit's toolbar with the given
        alignment.
        
        :param      widget | <QtGui.QWidget>
                    align  | <QtCore.Qt.Alignment>
        """
        # self.uiToolbarLAYOUT points to a deleted C/C++ object in PySide...
        layout = self.findChild(QHBoxLayout, 'uiToolbarLAYOUT')
        
        if before is not None:
            index = None
            for i in range(layout.count()):
                if layout.itemAt(i).widget() == before:
                    index = i
                    break
            
            if index is not None:
                layout.insertWidget(index, widget)
            else:
                layout.addWidget(widget)
            
        if align == Qt.AlignLeft:
            layout.insertWidget(0, widget)
        else:
            layout.addWidget(widget)
    
    def autoloadPages(self):
        """
        Returns whether or not to automatically load pages for this edit.
        
        :sa     XOrbTreeWidget.autoloadPages
        
        :return     <bool>
        """
        return self.uiRecordTREE.autoloadPages()
    
    def assignQuery(self):
        """
        Assigns the query from the query widget to the edit.
        """
        self.uiRecordTREE.setQuery(self._queryWidget.query(), autoRefresh=True)
    
    def currentRecord(self):
        """
        Returns the current record based on the user selection in the
        tree.
        
        :return     <orb.Table> || None
        """
        return self.uiRecordTREE.currentRecord()
    
    def commit(self):
        """
        Commits changes stored in the interface to the database.
        """
        self.uiRecordTREE.commit()
    
    def isEditable(self):
        """
        Returns whether or not this grid edit is editable.
        
        :return     <bool>
        """
        return self.uiRecordTREE.isEditable()
    
    def isPaged(self):
        """
        Returns whether or not to pages the results from the database query.
        
        :sa     XOrbTreeWidget.isPaged
        
        :param      state | <bool>
        """
        return self.uiRecordTREE.isPaged()
    
    def loadQuery(self):
        """
        Loads the query for the query widget when it is being shown.
        """
        self._queryWidget.setQuery(self.query())
    
    def pageSize(self):
        """
        Returns the number of records that should be loaded per page.
        
        :sa     XOrbTreeWidget.pageSize
        
        :return     <int>
        """
        return self.uiRecordTREE.pageSize()
    
    def query(self):
        """
        Returns the query that is being represented by the current results.
        
        :return     <orb.Query>
        """
        return self.uiRecordTREE.query()
    
    def records(self):
        """
        Returns the records that are currently assigned to this widget.
        
        :return     <orb.RecordSet>
        """
        return self.uiRecordTREE.records()
    
    def refresh(self):
        """
        Commits changes stored in the interface to the database.
        """
        table = self.tableType()
        if table:
            table.markTableCacheExpired()
        
        self.uiRecordTREE.searchRecords(self.uiSearchTXT.text())
    
    def restoreXml(self, xml):
        """
        Restores the settings for this edit from xml.
        
        :param      xml | <xml.etree.ElementTree>
        """
        self.uiRecordTREE.restoreXml(xml.find('tree'))
        
        # restore the query
        xquery = xml.find('query')
        if xquery is not None:
            self.setQuery(Q.fromXml(xquery[0]))
    
    def saveXml(self, xml):
        """
        Saves the settings for this edit to the xml parent.
        
        :param      xparent | <xml.etree.ElementTree>
        """
        # save grouping
        xtree = ElementTree.SubElement(xml, 'tree')
        self.uiRecordTREE.saveXml(xtree)
        
        # save the query
        query = self.query()
        if query:
            query.toXml(ElementTree.SubElement(xml, 'query'))
    
    def searchWidget(self):
        """
        Returns the search text edit for this grid edit.
        
        :return     <XLineEdit>
        """
        return self.uiSearchTXT
    
    def setAutoloadPages(self, state):
        """
        Sets whether or not to automatically load pages for this edit.
        
        :sa     XOrbTreeWidget.setAutoloadPages
        
        :param      state | <bool>
        """
        return self.uiRecordTREE.setAutoloadPages(state)
    
    def setCurrentRecord(self, record):
        """
        Sets the current record based on the user selection in the
        tree.
        
        :param      record | <orb.Table> || None
        """
        self.uiRecordTREE.setCurrentRecord(record)
    
    def setEditable(self, state):
        """
        Sets the editable state for this grid widget.
        
        :param      state | <bool>
        """
        self.uiRecordTREE.setEditable(state)
        self.uiSaveBTN.setVisible(state)
    
    def setQuery(self, query, autoRefresh=True):
        """
        Sets the query for this edit to the inputed query.
        
        :param      query | <orb.Query>
        """
        self.uiRecordTREE.setQuery(query, autoRefresh=autoRefresh)
    
    def setPaged(self, state):
        """
        Sets whether or not to pages the results from the database query.
        
        :sa     XOrbTreeWidget.setPaged
        
        :param      state | <bool>
        """
        return self.uiRecordTREE.setPaged(state)
    
    def setPageSize(self, size):
        """
        Sets the number of records that should be loaded per page.
        
        :sa     XOrbTreeWidget.setPageSize
        
        :param      size | <int>
        """
        return self.uiRecordTREE.setPageSize(size)
    
    def setRecords(self, records):
        """
        Sets the records for this widget to the inputed records.
        
        :param      records | [<orb.Table>, ..] || <orb.RecordSet>
        """
        self.uiRecordTREE.setRecords(records)
    
    def setTableType(self, tableType, autoRefresh=True):
        """
        Sets the table type associated with this edit.
        
        :param      tableType | <subclass of orb.Table>
        """
        self.uiRecordTREE.setTableType(tableType)
        self._queryWidget.setTableType(tableType)
        
        if autoRefresh:
            self.setQuery(Q())
    
    def setUserGroupingEnabled(self, state=True):
        """
        Sets whether or not to allow the user to manipulating grouping.
        
        :param      state | <bool>
        """
        self.uiRecordTREE.setUserGroupingEnabled(state)
    
    def tableType(self):
        """
        Returns the table type associated with this edit.
        
        :return     <subclass of orb.Table>
        """
        return self.uiRecordTREE.tableType()
    
    def treeWidget(self):
        """
        Returns the tree widget that is for editing records for this grid.
        
        :return     <XOrbTreeWidget>
        """
        return self.uiRecordTREE
    
    def userGroupingEnabled(self):
        """
        Returns whether or not user grouping is enabled.
        
        :return     <bool>
        """
        return self.uiRecordTREE.userGroupingEnabled()
    
    x_autoloadPages = Property(bool, autoloadPages, setAutoloadPages)
    x_paged = Property(bool, isPaged, setPaged)
    x_pageSize = Property(int, pageSize, setPageSize)
    x_editable = Property(bool, isEditable, setEditable)
    x_userGroupingEnabled = Property(bool, userGroupingEnabled,
                                           setUserGroupingEnabled)