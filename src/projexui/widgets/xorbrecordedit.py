""" 
Defines a widget that will generate a widget to edit an Orb schema record 
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

from projexui.qt import Signal, Slot
from projexui.qt.QtCore import QObject, Qt

from projexui.qt.QtGui  import QWidget,\
                               QFormLayout,\
                               QLabel,\
                               QDialogButtonBox,\
                               QDialog,\
                               QVBoxLayout,\
                               QMessageBox

from projexui.widgets.xorbcolumnedit import XOrbColumnEdit, IGNORED

import projex
projex.requires('orb')

import projexui

from orb import Query as Q

logger = logging.getLogger(__name__)

class XOrbRecordEdit(QWidget):
    """ """
    __designer_container__ = True
    __designer_group__ = 'ProjexUI - ORB'
    
    saved = Signal()
    
    def __init__( self, parent = None ):
        super(XOrbRecordEdit, self).__init__( parent )
        
        # define custom properties
        self._record = None
        self._model  = None
        self._uifile = ''
        
        # set default properties
        
        # create connections
    
    def model( self ):
        """
        Returns the model that is linked to this widget.
        
        :return     <orb.Table>
        """
        return self._model
    
    def record( self ):
        """
        Returns the record linked with widget.
        
        :return     <orb.Table> || None
        """
        return self._record
    
    def rebuild( self ):
        """
        Rebuilds the interface for this widget based on the current model.
        """
        self.setUpdatesEnabled(False)
        self.blockSignals(True)
        
        # clear out all the subwidgets for this widget
        for child in self.findChildren(QObject):
            child.setParent(None)
            child.deleteLater()
        
        # load up all the interface for this widget
        schema = self.schema()
        if ( schema ):
            self.setEnabled(True)
            
            uifile = self.uiFile()
            
            # load a user defined file
            if ( uifile ):
                projexui.loadUi('', self, uifile)
                
                for widget in self.findChildren(XOrbColumnEdit):
                    columnName = widget.columnName()
                    column     = schema.column(columnName)
                    
                    if ( column ):
                        widget.setColumn(column)
                    else:
                        logger.debug('%s is not a valid column of %s' % \
                                     (columnName, schema.name()))
            
            # dynamically load files
            else:
                layout = QFormLayout()
                layout.setContentsMargins(0, 0, 0, 0)
                columns = schema.columns()
                columns.sort(key = lambda x: x.displayName())
                
                record = self.record()
                
                for column in columns:
                    # ignore protected columns
                    if ( column.name().startswith('_') ):
                        continue
                    
                    label   = column.displayName()
                    coltype = column.columnType()
                    name    = column.name()
                    
                    # create the column edit widget
                    widget  = XOrbColumnEdit(self)
                    widget.setObjectName('ui_' + name)
                    widget.setColumnName(name)
                    widget.setColumnType(coltype)
                    widget.setColumn(column)
                    
                    layout.addRow(QLabel(label, self), widget)
                
                self.setLayout(layout)
                self.adjustSize()
                
                self.setWindowTitle('Edit %s' % schema.name())
        else:
            self.setEnabled(False)
        
        self.setUpdatesEnabled(True)
        self.blockSignals(False)
    
    @Slot()
    def save( self ):
        """
        Saves the values from the editor to the system.
        """
        schema = self.schema()
        if ( not schema ):
            self.saved.emit()
            return
        
        record = self.record()
        if not record:
            record = self._model()
        
        # validate the information
        save_data    = []
        column_edits = self.findChildren(XOrbColumnEdit)
        for widget in column_edits:
            columnName  = widget.columnName()
            column      = schema.column(columnName)
            
            if ( not column ):
                logger.warning('%s is not a valid column of %s.' % \
                               (columnName, schema.name()))
                continue
            
            value = widget.value()
            if ( value == IGNORED ):
                continue
            
            # check for required columns
            if ( column.required() and not value ):
                name = column.displayName()
                QMessageBox.information(self, 
                                        'Missing Required Field',
                                        '%s is a required field.' % name)
                return
            
            # check for unique columns
            elif ( column.unique() ):
                # check for uniqueness
                query        = Q(column.name()) == value
                if ( record.isRecord() ):
                    query   &= Q(self._model) != record
                
                columns  = self._model.schema().primaryColumns()
                result   = self._model.select(columns = columns, where = query)
                
                if ( result.total() ):
                    QMessageBox.information(self,
                                            'Duplicate Entry',
                                            '%s already exists.' % value)
                    return
            
            save_data.append((column, value))
        
        # record the properties for the record
        for column, value in save_data:
            record.setRecordValue(column.name(), value)
        
        self._record = record
        
        self.saved.emit()
    
    def schema( self ):
        """
        Returns the schema instance linked to this object.
        
        :return     <orb.TableSchema> || None
        """
        if ( self._model ):
            return self._model.schema()
        return None
    
    def setRecord( self, record ):
        """
        Sets the record instance for this widget to the inputed record.
        
        :param      record | <orb.Table>
        """
        self._record = record
        
        if ( not record ):
            return
        
        self.setModel(record.__class__)
        schema = self.model().schema()
        
        # set the information
        column_edits = self.findChildren(XOrbColumnEdit)
        for widget in column_edits:
            columnName  = widget.columnName()
            column      = schema.column(columnName)
            
            if ( not column ):
                logger.warning('%s is not a valid column of %s.' % \
                               (columnName, schema.name()))
                continue
                
            # update the values
            widget.setValue(record.recordValue(columnName))
            
    def setModel( self, model ):
        """
        Defines the model that is going to be used to define the interface for
        this widget.
        
        :param      model | <subclass of orb.Table>
        """
        if model == self._model:
            return False
            
        self._model = model
        
        if not self._record and model:
            self._record = model()
        
        if model:
            uifile = model.schema().property('uifile')
            if ( uifile ):
                self.setUiFile(uifile)
        
        self.rebuild()
        
        return True
    
    def setUiFile( self, uifile ):
        """
        Sets the ui file that will be loaded for this record edit.
        
        :param      uifile | <str>
        """
        self._uifile = uifile
    
    def uiFile( self ):
        """
        Returns the ui file that is assigned to this edit.
        
        :return     <str>
        """
        return self._uifile
    
    @classmethod
    def edit( cls, record, parent = None, uifile = '', commit = True ):
        """
        Prompts the user to edit the inputed record.
        
        :param      record | <orb.Table>
                    parent | <QWidget>
        
        :return     <bool> | accepted
        """
        # create the dialog
        dlg = QDialog(parent)
        dlg.setWindowTitle('Edit %s' % record.schema().name())
        
        # create the widget
        cls    = record.schema().property('widgetClass', cls)
        
        widget = cls(dlg)
        
        if ( uifile ):
            widget.setUiFile(uifile)
        
        widget.setRecord(record)
        widget.layout().setContentsMargins(0, 0, 0, 0)
        
        # create buttons
        opts = QDialogButtonBox.Save | QDialogButtonBox.Cancel
        btns = QDialogButtonBox(opts, Qt.Horizontal, dlg)
        
        # create layout
        layout = QVBoxLayout()
        layout.addWidget(widget)
        layout.addWidget(btns)
        
        dlg.setLayout(layout)
        dlg.adjustSize()
        
        # create connections
        #btns.accepted.connect(widget.save)
        btns.rejected.connect(dlg.reject)
        widget.saved.connect(dlg.accept)
        
        if ( dlg.exec_() ):
            if commit:
                result = widget.record().commit()
                if 'errored' in result:
                    QMessageBox.information(self.window(),
                                            'Error Committing to Database',
                                            result['errored'])
                    return False
            return True
        return False
    
    @classmethod
    def create( cls, model, parent = None, uifile = '', commit = True ):
        """
        Prompts the user to create a new record for the inputed table.
        
        :param      model   | <subclass of orb.Table>
                    parent  | <QWidget>
        
        :return     <orb.Table> || None/ | instance of the inputed table class
        """
        # create the dialog
        dlg = QDialog(parent)
        dlg.setWindowTitle('Create %s' % model.schema().name())
        
        # create the widget
        cls    = model.schema().property('widgetClass', cls)
        widget = cls(dlg)
        
        if ( uifile ):
            widget.setUiFile(uifile)
        
        widget.setModel(model)
        widget.layout().setContentsMargins(0, 0, 0, 0)
        
        # create buttons
        opts = QDialogButtonBox.Save | QDialogButtonBox.Cancel
        btns = QDialogButtonBox(opts, Qt.Horizontal, dlg)
        
        # create layout
        layout = QVBoxLayout()
        layout.addWidget(widget)
        layout.addWidget(btns)
        
        dlg.setLayout(layout)
        dlg.adjustSize()
        
        # create connections
        btns.accepted.connect(widget.save)
        btns.rejected.connect(dlg.reject)
        widget.saved.connect(dlg.accept)
        
        if ( dlg.exec_() ):
            record = widget.record()
            if ( commit ):
                record.commit()
            return record
        return None

__designer_plugins__ = [XOrbRecordEdit]