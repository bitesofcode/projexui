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

import projexui

from projex.text import nativestring

from projex.enum import enum
from projexui.qt.QtCore import Qt
from collections import OrderedDict
from orb import Query, ColumnType

#----------------------------------------------------------------------

class XEditorRegistry(object):
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

class XOrbQueryPlugin(object):
    Flags = enum('ReferenceRequired')
    
    def __init__(self):
        self._operatorMap = OrderedDict()
        
    def createEditor(self, parent, column, op, value):
        """
        Creates a new editor for the parent based on the plugin parameters.
        
        :param      parent | <QWidget>
        
        :return     <QWidget> || None
        """
        try:
            cls = self._operatorMap[nativestring(op)].cls
        except KeyError, AttributeError:
            return None
        
        # create the new editor
        if cls:
            widget = cls(parent)
            widget.setAttribute(Qt.WA_DeleteOnClose)
            projexui.setWidgetValue(widget, value)
            return widget
        
        return None
    
    def editorValue(self, editor):
        """
        Returns the value from the editor for this widget.
        
        :param      editor | <QWidget> || None
        
        :return     <variant> value
        """
        value, success = projexui.widgetValue(editor)
        if not success:
            return None
        return value
    
    def operator(self, operatorType, value):
        """
        Returns the operator that best matches the type and value.
        
        :param      operatorType | <Query.Op>
                    value        | <variant>
        
        :return     <str>
        """
        if value is None:
            if 'is none' in self._operatorMap and operatorType == Query.Op.Is:
                return 'is none'
            elif 'is not none' in self._operatorMap:
                return 'is not none'
            
        for op, data in self._operatorMap.items():
            if data.op == operatorType:
                return op
        return ''
    
    def operators(self, ignore=0):
        """
        Returns a list of operators for this plugin.
        
        :return     <str>
        """
        return [k for k, v in self._operatorMap.items() if not v.flags & ignore]
    
    def registerEditor(self,
                       name,
                       op,
                       cls=None,
                       defaultValue=None,
                       flags=0):
        """
        Registers an editor for the given operator as the given name.  If no
        editor class is supplied, no editor widget will be created for the
        operator unless you overload the createEditor method and create your own
        
        :param      name         | <str>
                    op           | <Query.Op>
                    cls          | <subclass of QWidget> || None
                    defaultValue | <variant>
        """
        registry = XEditorRegistry(op=op,
                                   cls=cls,
                                   defaultValue=defaultValue,
                                   flags=flags)
        
        self._operatorMap[nativestring(name)] = registry
    
    def setupQuery(self, query, op, editor):
        """
        Returns the value from the editor.
        
        :param      op       | <str>
                    editor   | <QWidget> || None
        
        :return     <bool> | success
        """
        try:
            registry = self._operatorMap[nativestring(op)]
        except KeyError:
            return False
        
        op = registry.op
        value = registry.defaultValue
        
        if op is None:
            return False
        
        if editor is not None:
            value = self.editorValue(editor)
        
        query.setOperatorType(op)
        query.setValue(value)
        return True
    
#----------------------------------------------------------------------

class XOrbQueryPluginFactory(object):
    def __init__(self):
        self._plugins = {}
        
        # register default plugins
        self.initializePlugins()
    
    def initializePlugins(self):
        from projexui.widgets.xorbquerywidget import plugins
        plugins.init(self)
    
    def plugin(self, column):
        """
        Looks up the plugin for the given column.
        
        :param      column | <orb.Column>
        
        :return     <XOrbQueryPlugin> || None
        """
        base = ColumnType.base(column.columnType())
        
        a = (column.columnType(), column.name())
        b = (column.columnType(), None)
        c = (base, column.name())
        d = (base, None)
        e = (None, column.name())
        f = (None, None)
        
        for check in (a, b, c, d, e, f):
            try:
                return self._plugins[check]
            except KeyError:
                continue
        
        return None
    
    def register(self, plugin, columnType=None, columnName=None):
        """
        Registers a plugin to handle particular column types and column names
        based on user selection.
        
        :param      plugin     | <XOrbQueryPlugin>
                    columnType | <orb.ColumnType> || None
                    columnName | <str> || None
        """
        self._plugins[(columnType, columnName)] = plugin