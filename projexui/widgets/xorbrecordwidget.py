""" 
Defines a base widget for modifying orb records.
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

import logging
import weakref

from projex.text import nativestring

from projexui.qt import Signal, unwrapVariant
from projexui.qt.QtCore import Qt,\
                               QDateTime,\
                               QDate,\
                               QTime,\
                               QSize

from projexui.qt.QtGui import QApplication,\
                              QDialog,\
                              QDialogButtonBox,\
                              QWidget,\
                              QMessageBox,\
                              QVBoxLayout

import projexui
from projexui.widgets.xenumbox import XEnumBox
from orb.errors import OrbError

logger = logging.getLogger(__name__)

class XOrbRecordWidget(QWidget):
    """ """
    __designer_group__ = 'ProjexUI - ORB'
    
    saved = Signal()
    aboutToSave = Signal()
    aboutToSaveRecord = Signal(object)
    recordSaved = Signal(object)
    resizeRequested = Signal()
    
    _tableType = None
    
    def __init__(self, parent=None):
        super(XOrbRecordWidget, self).__init__(parent)
        
        # define custom properties
        self._record = None
        self._autoCommitOnSave = False
        self._multipleCreateEnabled = True
        self._savedColumnsOnReset = []
        self._saveSignalBlocked = False
        
    def autoCommitOnSave(self):
        """
        Returns whether or not this widget should automatically commit changes
        when the widget is saved.
        
        :return     <bool>
        """
        return self._autoCommitOnSave
    
    def fitToContents(self):
        """
        Adjusts the size for this widget.
        """
        self.adjustSize()
        self.resizeRequested.emit()
    
    def loadValues(self, values):
        """
        Loads the values from the inputed dictionary to the widget.
        
        :param      values | <dict>
        """
        table = self.tableType()
        if table:
            schema = table.schema()
        else:
            schema = None
        
        process = []
        for widget in self.findChildren(QWidget):
            prop = widget.property('columnName')
            if not prop:
                continue
            
            order = widget.property('columnOrder')
            if order:
                order = unwrapVariant(order)
            else:
                order = 10000000
            
            process.append((order, widget, prop))
        
        process.sort()
        for order, widget, prop in process:
            columnName = nativestring(unwrapVariant(prop, ''))
            
            if not columnName:
                continue
            
            if isinstance(widget, XEnumBox) and schema:
                column = schema.column(columnName)
                if column.enum() is not None:
                    widget.setEnum(column.enum())
            
            if columnName in values:
                projexui.setWidgetValue(widget, values.get(columnName))
    
    def multipleCreateEnabled(self):
        """
        Returns whether or not multiple records can be created in succession
        for this widget.
        
        :return     <bool>
        """
        return self._multipleCreateEnabled
    
    def record(self):
        """
        Returns the record linked with this widget.
        
        :return     <orb.Table>
        """
        return self._record
    
    def reset(self):
        """
        Resets this widget's data to a new class an reinitializes.  This method
        needs to have a table type defined for this widget to work.
        
        :sa     setTableType, tableType
        
        :return     <bool> | success
        """
        ttype = self.tableType()
        if ( not ttype ):
            return False
        
        values = self.saveValues()
        self.setRecord(ttype())
        restore_values = {}
        for column in self.savedColumnsOnReset():
            if column in restore_values:
                restore_values[column] = values[column]
        if restore_values:
            self.loadValues(restore_values)
        
        return True
        
    def saveValues(self):
        """
        Generates a dictionary of values from the widgets in this editor that
        will be used to save the values on its record.
        
        :return     {<str> columnName: <variant> value, ..}
        """
        output = {}
        
        for widget in self.findChildren(QWidget):
            prop = widget.property('columnName')
            if not prop:
                continue
            
            columnName = nativestring(unwrapVariant(prop, ''))
            
            if ( not columnName ):
                continue
            
            value, success = projexui.widgetValue(widget)
            if ( not success ):
                continue
            
            # convert from values to standard python values
            if ( isinstance(value, QDateTime) ):
                value = value.toPyDateTime()
            elif ( isinstance(value, QDate) ):
                value = value.toPyDate()
            elif ( isinstance(value, QTime) ):
                value = value.toPyTime()
            elif ( type(value).__name__ == 'QString' ):
                value = nativestring(value)
            
            output[columnName] = value
        
        return output
    
    def save(self):
        """
        Saves the changes from the ui to this widgets record instance.
        """
        record = self.record()
        if not record:
            logger.warning('No record has been defined for %s.' % self)
            return False
        
        if not self.signalsBlocked():
            self.aboutToSaveRecord.emit(record)
            self.aboutToSave.emit()
        
        values = self.saveValues()
        
        # ignore columns that are the same (fixes bugs in encrypted columns)
        check = values.copy()
        for column_name, value in check.items():
            try:
                equals = value == record.recordValue(column_name)
            except UnicodeWarning:
                equals = False
            
            if equals:
                check.pop(column_name)
        
        # check to see if nothing has changed
        if not check and record.isRecord():
            if not self.signalsBlocked():
                self.recordSaved.emit(record)
                self.saved.emit()
                self._saveSignalBlocked = False
            else:
                self._saveSignalBlocked = True
            
            if self.autoCommitOnSave():
                status, result = record.commit()
                if status == 'errored':
                    if 'db_error' in result:
                        msg = nativestring(result['db_error'])
                    else:
                        msg = 'An unknown database error has occurred.'
                    
                    QMessageBox.information(self,
                                            'Commit Error',
                                            msg)
                    return False
            return True
        
        # validate the modified values
        success, msg = record.validateValues(check)
        if ( not success ):
            QMessageBox.information(None, 'Could Not Save', msg)
            return False
        
        record.setRecordValues(**values)
        success, msg = record.validateRecord()
        if not success:
            QMessageBox.information(None, 'Could Not Save', msg)
            return False
        
        if ( self.autoCommitOnSave() ):
            result = record.commit()
            if 'errored' in result:
                QMessageBox.information(None, 'Could Not Save', msg)
                return False
        
        if ( not self.signalsBlocked() ):
            self.recordSaved.emit(record)
            self.saved.emit()
            self._saveSignalBlocked = False
        else:
            self._saveSignalBlocked = True
        
        return True
    
    def saveSignalBlocked(self):
        """
        Returns whether or not a save has occurred silently, and the signal
        has been surpressed.
        
        :return     <bool>
        """
        return self._saveSignalBlocked
    
    def saveSilent(self):
        """
        Saves the record, but does not emit the saved signal.  This method
        is useful when chaining together multiple saves.  Check the 
        saveSignalBlocked value to know if it was muted to know if any
        saves occurred.
        
        :return     <bool>
        """
        self.blockSignals(True)
        success = self.save()
        self.blockSignals(False)
        return success
    
    def savedColumnsOnReset(self):
        """
        Returns a list of the columns that should be stored when the widget
        is reset.
        
        :return     [<str>, ..]
        """
        return self._savedColumnsOnReset
    
    def setAutoCommitOnSave(self, state):
        """
        Sets whether or not the widget will automatically commit changes when
        the widget is saved.
        
        :param      state | <bool>
        """
        self._autoCommitOnSave = state
    
    def setMultipleCreateEnabled(self, state):
        """
        Sets whether or not multiple creation is enabled for this widget.
        
        :param      state | <bool>
        """
        self._multipleCreateEnabled = state
    
    def setRecord(self, record):
        """
        Sets the record instance linked with this widget.
        
        :param      record | <orb.Table>
        """
        self._record = record
        if record is not None:
            self.loadValues(record.recordValues(autoInflate=True))
        else:
            self.loadValues({})
    
    def setSavedColumnsOnReset(self, columns):
        """
        Sets a list of the columns that should be stored when the widget
        is reset.
        
        :param      columns | [<str>, ..]
        """
        self._savedColumnsOnReset = columns
    
    @classmethod
    def getDialog(cls, name, parent=None):
        """
        Generates a dialog for this class widget and returns it.
        
        :param      parent | <QtGui.QWidget> || None
        
        :return     <QtGui.QDialog>
        """
        key = '_{0}__{1}_dialog'.format(cls.__name__, name)
        dlgref = getattr(cls, key, None)
        
        if dlgref is not None:
            dlg = dlgref()
            if dlg:
                return dlg
            
        if parent is None:
            parent = QApplication.activeWindow()
        
        dlg = QDialog(parent)
        
        # create widget
        widget = cls(dlg)
        dlg.__dict__['_mainwidget'] = widget
        widget.layout().setContentsMargins(0, 0, 0, 0)
        
        # create buttons
        opts    = QDialogButtonBox.Save | QDialogButtonBox.Cancel
        buttons = QDialogButtonBox(opts, Qt.Horizontal, dlg)
        
        # create layout
        layout = QVBoxLayout()
        layout.addWidget(widget)
        layout.addWidget(buttons)
        dlg.setLayout(layout)
        dlg.resize(widget.minimumSize() + QSize(15, 15))
        widget.resizeRequested.connect(dlg.adjustSize)
        
        # create connections
        buttons.accepted.connect(widget.save)
        buttons.rejected.connect(dlg.reject)
        widget.saved.connect(dlg.accept)
        widget.setFocus()
        
        dlg.adjustSize()
        if parent and parent.window():
            center = parent.window().geometry().center()
            dlg.move(center.x() - dlg.width() / 2.0,
                     center.y() - dlg.height() / 2.0)
        
        setattr(cls, key, weakref.ref(dlg))
        return dlg
    
    @classmethod
    def edit(cls, record, parent=None, autoCommit=True, title=''):
        """
        Prompts the user to edit the inputed record.
        
        :param      record | <orb.Table>
                    parent | <QWidget>
        
        :return     <bool> | accepted
        """
        dlg = cls.getDialog('edit', parent)
        
        # update the title
        try:
            name = record.schema().displayName()
        except AttributeError:
            name = record.__class__.__name__
        
        if not title:
            title = 'Edit {0}'.format(name)
        dlg.setWindowTitle(title)
        
        widget = dlg._mainwidget
        widget.setRecord(record)
        widget.setAutoCommitOnSave(autoCommit)
        
        result = dlg.exec_()
        
        return result == 1
    
    @classmethod
    def create(cls,
               model=None,
               parent=None,
               autoCommit=True,
               defaults=None,
               title=''):
        """
        Prompts the user to create a new record.
        
        :param      model  | <subclass of orb.Table>
                    parent | <QWidget>
                    autoCommit | <bool>
                    defaults | <dict> || None
        
        :return     <orb.Table> || None
        """
        if model is None:
            model = cls.tableType()
            if model is None:
                return None
        
        dlg = cls.getDialog('create', parent)
        
        # create dialog
        if not title:
            title = 'Create {0}'.format(type(model).__name__)
        dlg.setWindowTitle(title)
        
        widget = dlg._mainwidget
        widget.setRecord(model())
        widget.setAutoCommitOnSave(autoCommit)
        
        if defaults:
            widget.loadValues(defaults)
        else:
            widget.loadValues({})
        
        result = dlg.exec_()
        if result or widget.saveSignalBlocked():
            output = widget.record()
        else:
            output = None
        
        return output
    
    @classmethod
    def setTableType(cls, tableType):
        """
        Sets the table type for this widget to the inputed type.
        
        :param      tableType | <subclass of orb.Table>
        """
        cls._tableType = tableType
    
    @classmethod
    def tableType(cls):
        """
        Returns the table type for this widget.
        
        :return     <subclass of orb.Table> || None
        """
        return cls._tableType
