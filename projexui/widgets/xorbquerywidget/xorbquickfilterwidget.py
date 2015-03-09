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

import re

try:
    from orb import Query, QueryCompound
except ImportError:
    Query = None
    QueryCompound = None

import projexui

from projex.text import nativestring

from projexui.qt import Signal, Property
from projexui.qt.QtCore import Qt
from projexui.qt.QtGui import QWidget,\
                              QHBoxLayout,\
                              QVBoxLayout,\
                              QSizePolicy,\
                              QLabel,\
                              QMenu

from projexui.widgets.xtextedit import XTextEdit
from .xorbqueryplugin import XOrbQueryPluginFactory

import projexui

FORMAT_SPLITTER = re.compile('(?P<label>[^{]*)\{?(?P<column>[^\}]*)\}?')

class XOrbQuickFilterWidget(QWidget):
    """ """
    __designer_group__ = 'ProjexUI - ORB'
    
    queryEntered = Signal(object)
    
    def __init__(self, parent=None):
        super(XOrbQuickFilterWidget, self).__init__(parent)
        
        # define custom properties
        self._tableType = None
        self._plugins = []
        self._filterFormat = ''
        self._pluginFactory = XOrbQueryPluginFactory()
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 3, 0, 3)
        self.setLayout(layout)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        
        self.customContextMenuRequested.connect(self.showMenu)
    
    def filterFormat(self):
        """
        Returns the text that defines the filtering options for this widget.
        
        :return     <str>
        """
        return self._filterFormat
    
    def pluginFactory(self):
        """
        Returns the plugin for this filter widget.
        
        :return     <XOrbQueryPluginFactory>
        """
        return self._pluginFactory
    
    def query(self):
        """
        Builds the query for this quick filter.
        
        :return     <orb.Query>
        """
        output = Query()
        for column, op, plugin, editor in self._plugins:
            query = Query(column)
            if plugin.setupQuery(query, op, editor):
                output &= query
        return output
    
    def keyPressEvent(self, event):
        """
        Listens for the enter event to check if the query is setup.
        """
        if event.key() in (Qt.Key_Enter, Qt.Key_Return):
            self.queryEntered.emit(self.query())
        
        super(XOrbQuickFilterWidget, self).keyPressEvent(event)
    
    def rebuild(self):
        """
        Rebuilds the data associated with this filter widget.
        """
        table = self.tableType()
        form  = nativestring(self.filterFormat())
        
        if not table and form:
            if self.layout().count() == 0:
                self.layout().addWidget(QLabel(form, self))
            else:
                self.layout().itemAt(0).widget().setText(form)
            return
        
        elif not form:
            return
        
        for child in self.findChildren(QWidget):
            child.close()
            child.setParent(None)
            child.deleteLater()
        
        self.setUpdatesEnabled(False)
        schema = table.schema()
        
        vlayout = self.layout()
        for i in range(vlayout.count()):
            vlayout.takeAt(0)
        
        self._plugins = []
        for line in form.split('\n'):
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(0)
            
            for label, lookup in FORMAT_SPLITTER.findall(line):
                # create the label
                lbl = QLabel(label, self)
                row.addWidget(lbl)
                
                # create the query plugin
                opts = lookup.split(':')
                if len(opts) == 1:
                    opts.append('is')
                
                column = schema.column(opts[0])
                if not column:
                    continue
                
                plugin = self.pluginFactory().plugin(column)
                if not plugin:
                    continue
                
                editor = plugin.createEditor(self, column, opts[1], None)
                if editor:
                    editor.setObjectName(opts[0])
                    row.addWidget(editor)
                    self._plugins.append((opts[0], opts[1], plugin, editor))
            
            row.addStretch(1)
            vlayout.addLayout(row)
        
        self.setUpdatesEnabled(True)
        self.adjustSize()
    
    def showMenu(self, point):
        """
        Displays the menu for this filter widget.
        """
        menu = QMenu(self)
        acts = {}
        acts['edit'] = menu.addAction('Edit quick filter...')
        
        trigger = menu.exec_(self.mapToGlobal(point))
        
        if trigger == acts['edit']:
            text, accepted = XTextEdit.getText(self.window(),
                                                  'Edit Format',
                                                  'Format:',
                                                  self.filterFormat(),
                                                  wrapped=False)
            
            if accepted:
                self.setFilterFormat(text)
    
    def setQuery(self, query):
        """
        Sets the query information for this filter widget.
        
        :param      query | <orb.Query> || None
        """
        if query is None:
            return
        
        count = {}
        
        for widget in self.findChildren(QWidget):
            column = nativestring(widget.objectName())
            count.setdefault(column, 0)
            count[column] += 1
            
            success, value, _ = query.findValue(column, count[column])
            if success:
                projexui.setWidgetValue(widget, value)
    
    def setPluginFactory(self, pluginFactory):
        """
        Sets the plugin factory for this widget to the inputed factory.
        
        :param      pluginFactory | <XOrbPluginFactory>
        """
        self._pluginFactory = pluginFactory
    
    def setFilterFormat(self, format):
        """
        Sets the text that defines the filtering options for this widget.
        
        :param      filterFormat | <str>
        """
        self._filterFormat = format
        self.rebuild()
    
    def setTableType(self, tableType):
        """
        Sets the table type associated with this filter widget.
        
        :param      tableType | <subclass of orb.TableType>
        """
        self._tableType = tableType
        self.rebuild()
    
    def tableType(self):
        """
        Returns the table type associated with this filter widget.
        
        :return     <subclass of orb.TableType>
        """
        return self._tableType
    
    x_filterFormat = Property(str, filterFormat, setFilterFormat)