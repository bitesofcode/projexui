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

import datetime

from orb import ColumnType, Query

from projex.text import nativestring

from projexui.qt.QtCore import Qt, QRegExp
from projexui.qt.QtGui import QCheckBox,\
                              QSpinBox,\
                              QDoubleSpinBox,\
                              QRegExpValidator,\
                              QLineEdit

from projexui.widgets.xboolcombobox   import XBoolComboBox
from projexui.widgets.xdateedit       import XDateEdit
from projexui.widgets.xdatetimeedit   import XDateTimeEdit
from projexui.widgets.xenumbox        import XEnumBox
from projexui.widgets.xlineedit       import XLineEdit
from projexui.widgets.xorbrecordbox   import XOrbRecordBox
from projexui.widgets.xtimedeltaedit  import XTimeDeltaEdit
from projexui.widgets.xtimeedit       import XTimeEdit
from projexui.widgets.xorbquerywidget import XOrbQueryPlugin

# B
#----------------------------------------------------------------------

class BoolPlugin(XOrbQueryPlugin):
    def __init__(self):
        super(BoolPlugin, self).__init__()
        
        self.registerEditor('is', Query.Op.Is, XBoolComboBox)
        self.registerEditor('is not', Query.Op.IsNot, XBoolComboBox)
        self.registerEditor('is none', Query.Op.Is)
        self.registerEditor('is not none', Query.Op.IsNot)


# D
#----------------------------------------------------------------------

class DateTimePlugin(XOrbQueryPlugin):
    def __init__(self, cls=None):
        super(DateTimePlugin, self).__init__()
        
        if cls is None:
            cls = XDateEdit
        
        self.registerEditor('is', Query.Op.Is, cls)
        self.registerEditor('is not', Query.Op.IsNot, cls)
        self.registerEditor('after', Query.Op.After, cls)
        self.registerEditor('after (delta)', Query.Op.After, XTimeDeltaEdit)
        self.registerEditor('before', Query.Op.Before, cls)
        self.registerEditor('before (delta)', Query.Op.Before, XTimeDeltaEdit)
        self.registerEditor('is none', Query.Op.Is)
        self.registerEditor('is not none', Query.Op.IsNot)
    
    def createEditor(self, parent, column, operator, value):
        """
        Creates a new editor for the given parent and operator.
        
        :param      parent      | <QWidget>
                    operator    | <str>
                    value       | <variant>
        """
        if type(value) == datetime.timedelta:
            editor = XTimeDeltaEdit(parent)
            editor.setAttribute(Qt.WA_DeleteOnClose)
            editor.setDelta(value)
            return editor
        
        else:
            editor = super(DateTimePlugin, self).createEditor(parent,
                                                              column,
                                                              operator,
                                                              value)
        
            if isinstance(editor, XDateTimeEdit) or \
               isinstance(editor, XDateEdit):
                editor.setCalendarPopup(True)
            
            return editor
    
    def operator(self, operatorType, value):
        """
        Returns the best match for the given operator type from the list
        of choices.
        
        :param      operatorType | <Query.Op>
                    value        | <variant>
        
        :return     <str>
        """
        if type(value) == datetime.timedelta:
            if operatorType == Query.Op.After:
                return 'after (delta)'
            elif operatorType == Query.Op.Before:
                return 'before (delta)'
        
        return super(DateTimePlugin, self).operator(operatorType, value)

# E
#----------------------------------------------------------------------

class EnumPlugin(XOrbQueryPlugin):
    def __init__(self):
        super(EnumPlugin, self).__init__()
        
        self.registerEditor('is', Query.Op.Is, XEnumBox)
        self.registerEditor('is not', Query.Op.IsNot, XEnumBox)
        self.registerEditor('contains', Query.Op.Contains, XEnumBox)
        self.registerEditor('does not contain', Query.Op.DoesNotContain, XEnumBox)
        self.registerEditor('is none', Query.Op.Is)
        self.registerEditor('is not none', Query.Op.IsNot)

    def createEditor(self, parent, column, operator, value):
        """
        Creates a new editor for the system.
        """
        editor = super(EnumPlugin, self).createEditor(parent,
                                                      column,
                                                      operator,
                                                      value)
        
        editor.setEnum(column.enum())
        if operator in ('contains', 'does not contain'):
            editor.setCheckable(True)
        
        editor.setCurrentValue(value)
        return editor

# F
#----------------------------------------------------------------------

class ForeignKeyPlugin(XOrbQueryPlugin):
    def __init__(self):
        super(ForeignKeyPlugin, self).__init__()
        
        flags = XOrbQueryPlugin.Flags.ReferenceRequired
        
        self.registerEditor('is', Query.Op.Is, XOrbRecordBox, flags=flags)
        self.registerEditor('is not', Query.Op.IsNot, XOrbRecordBox,
                            flags=flags)
        self.registerEditor('is none', Query.Op.Is)
        self.registerEditor('is not none', Query.Op.IsNot)
        self.registerEditor('is in', Query.Op.IsIn, XOrbRecordBox, flags=flags)
        self.registerEditor('is not in', Query.Op.IsNotIn, XOrbRecordBox,
                            flags=flags)
    
    def createEditor(self, parent, column, operator, value):
        """
        Creates a new editor for the given parent and operator.
        
        :param      parent      | <QWidget>
                    operator    | <str>
                    value       | <variant>
        """
        editor = super(ForeignKeyPlugin, self).createEditor(parent,
                                                            column,
                                                            operator,
                                                            value)
        
        if editor is not None:
            editor.setRequired(column.required())
            editor.setMinimumWidth(150)
            
            model = column.referenceModel()
            if model:
                text = model.schema().displayName().lower()
                editor.setHint('any {0}'.format(text))
                
                editor.setRecords(model.select())
                if operator in ('is in', 'is not in'):
                    editor.setCheckable(True)
        
        return editor
    
    def setupQuery(self, query, op, editor):
        """
        Sets up the query for this editor.
        """
        if editor is not None:
            value = editor.currentRecord()
            if value is None:
                return False
        
        return super(ForeignKeyPlugin, self).setupQuery(query, op, editor)

# N
#----------------------------------------------------------------------

class NumericPlugin(XOrbQueryPlugin):
    def __init__(self, cls):
        super(NumericPlugin, self).__init__()
        
        self.registerEditor('=', Query.Op.Is, cls)
        self.registerEditor('!=', Query.Op.IsNot, cls)
        self.registerEditor('<', Query.Op.LessThan, cls)
        self.registerEditor('<=', Query.Op.LessThanOrEqual, cls)
        self.registerEditor('>', Query.Op.GreaterThan, cls)
        self.registerEditor('>=', Query.Op.GreaterThanOrEqual, cls)
        self.registerEditor('is none', Query.Op.Is)
        self.registerEditor('is not none', Query.Op.IsNot)

    def createEditor(self, parent, column, operator, value):
        """
        Creates a new editor for the given parent and operator.
        
        :param      parent      | <QWidget>
                    operator    | <str>
                    value       | <variant>
        """
        editor = super(NumericPlugin, self).createEditor(parent,
                                                         column,
                                                         operator,
                                                         value)
        
        if isinstance(editor, QLineEdit):
            validator = QRegExpValidator(QRegExp('^-?\d+\.?\d*'), editor)
            editor.setValidator(validator)
            if value is None:
                value = 0
            editor.setText(nativestring(value))
        return editor
    
    def editorValue(self, editor):
        """
        Returns the value for this plugin from the inputed editor.
        
        :param      editor | <QtGui.QWidget>
        
        :return     <variant>
        """
        if isinstance(editor, QLineEdit):
            try:
                return eval(nativestring(editor.text()))
            except:
                return 0
        else:
            return super(NumericPlugin, self).editorValue(editor)

# P
#----------------------------------------------------------------------

class PasswordPlugin(XOrbQueryPlugin):
    def __init__(self):
        super(PasswordPlugin, self).__init__()
        
        self.registerEditor('is', Query.Op.Is, XLineEdit)
        self.registerEditor('is not', Query.Op.IsNot, XLineEdit)
        self.registerEditor('is none', Query.Op.Is)
        self.registerEditor('is not none', Query.Op.IsNot)
    
    def createEditor(self, parent, column, operator, value):
        editor = super(PasswordPlugin, self).createEditor(parent,
                                                          column,
                                                          operator,
                                                          value)
        
        if editor:
            editor.setEchoMode(editor.Password)
        
        return editor

# S
#----------------------------------------------------------------------

class StringPlugin(XOrbQueryPlugin):
    def __init__(self, cls=None):
        super(StringPlugin, self).__init__()
        
        if cls is None:
            cls = XLineEdit
        
        self.registerEditor('is', Query.Op.Is, cls)
        self.registerEditor('is not', Query.Op.IsNot, cls)
        self.registerEditor('contains', Query.Op.Contains, cls)
        self.registerEditor('matches', Query.Op.Matches, cls)
        self.registerEditor('startswith', Query.Op.Startswith, cls)
        self.registerEditor('endswith', Query.Op.Endswith, cls)
        self.registerEditor("doesn't contain", Query.Op.DoesNotContain, cls)
        self.registerEditor("doesn't match", Query.Op.DoesNotMatch, cls)
        self.registerEditor('is none', Query.Op.Is)
        self.registerEditor('is not none', Query.Op.IsNot)

#----------------------------------------------------------------------

def init(factory):
    # simple types
    factory.register(BoolPlugin(),                  ColumnType.Bool)
    factory.register(NumericPlugin(QLineEdit),      ColumnType.Double)
    factory.register(NumericPlugin(QLineEdit),      ColumnType.Decimal)
    factory.register(NumericPlugin(QLineEdit),      ColumnType.Integer)
    factory.register(NumericPlugin(QLineEdit),      ColumnType.BigInt)
    
    # Enum
    factory.register(EnumPlugin(),                  ColumnType.Enum)
    
    # string types
    factory.register(StringPlugin(XLineEdit),       ColumnType.String)
    factory.register(StringPlugin(XLineEdit),       ColumnType.Text)
    factory.register(StringPlugin(XLineEdit),       ColumnType.Xml)
    factory.register(StringPlugin(XLineEdit),       ColumnType.Html)
    factory.register(StringPlugin(XLineEdit),       ColumnType.Color)
    factory.register(PasswordPlugin(),              ColumnType.Password)
    
    # date/time types
    dtimeplug = DateTimePlugin(XDateTimeEdit)
    factory.register(DateTimePlugin(XDateEdit),     ColumnType.Date)
    factory.register(dtimeplug, ColumnType.Datetime)
    factory.register(dtimeplug, ColumnType.DatetimeWithTimezone)
    factory.register(DateTimePlugin(XTimeEdit),     ColumnType.Time)
    
    # data types
    'Image'        # stores images in the database as binary
    'ByteArray'    # stores additional binary information
    'Dict'         # stores python dictionary types
    
    # relation types
    factory.register(ForeignKeyPlugin(), ColumnType.ForeignKey)
