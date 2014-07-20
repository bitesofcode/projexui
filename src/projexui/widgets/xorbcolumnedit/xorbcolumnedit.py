""" Generic widget for editing any type of an orb.Column instance. """

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

from projex.text import nativestring

from projexui.qt import Signal, Slot, Property, PyObject
from projexui.qt.QtGui  import QWidget, QHBoxLayout

import projex
projex.requires('orb')

from projexui.widgets.xorbcolumnedit import plugins

try:
    from orb import ColumnType

except ImportError:
    logger.warning('The XOrbColumnEdit widget requires the Projex orb package.')
    ColumnType = None

IGNORED = '!GNOR3D' # ignore...odds of a password being set to this is low

class XOrbColumnEdit(QWidget):
    """ """
    __designer_group__ = 'ProjexUI - ORB'
    
    def __init__( self, parent = None ):
        super(XOrbColumnEdit, self).__init__( parent )
        
        # define custom properties
        
        # set default properties
        self._columnType = None
        self._columnName = ''
        self._options    = None
        self._editor     = None
        
        # set the layout for this object
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        if ( ColumnType ):
            self.setColumnType(ColumnType.String)
        
        # create connections
    
    def columnName( self ):
        """
        Returns the column name that will be used for this record edit.
        
        :return     <str>
        """
        return self._columnName
    
    def columnType( self ):
        """
        Returns the column type that is linked with this widget.
        
        :return     <orb.ColumnType>
        """
        return self._columnType
    
    def columnTypeText( self ):
        """
        Returns the string representation of the current column type.
        
        :return     <str>
        """
        if ( ColumnType ):
            try:
                return ColumnType[self._columnType]
            except KeyError:
                return 0
        return 0
    
    def editor( self ):
        """
        Returns the editor instance being used for this widget.
        
        :return     <QWidget> || None
        """
        return self._editor
    
    def label( self ):
        """
        Returns the label for this widget.  Varies per type, not all
        types have labels.
        
        :return     <str>
        """
        if ( self._editor and hasattr(self._editor, 'label') ):
            return self._editor.label()
        return ''
    
    def isReadOnly( self ):
        """
        Returns the read only for this widget from the editor.
        Differs per type, not all types support read only.
        
        :param      text | <str>
        """
        if ( self._editor and hasattr(self._editor, 'isReadOnly') ):
            return self._editor.isReadOnly()
        return False
    
    def rebuild( self ):
        """
        Clears out all the child widgets from this widget and creates the 
        widget that best matches the column properties for this edit.
        """
        plugins.init()
        
        self.blockSignals(True)
        self.setUpdatesEnabled(False)
        
        # clear the old editor
        if ( self._editor ):
            self._editor.close()
            self._editor.setParent(None)
            self._editor.deleteLater()
            self._editor = None
        
        # create a new widget
        plugin_class = plugins.widgets.get(self._columnType)
        if ( plugin_class ):
            self._editor = plugin_class(self)
            self.layout().addWidget(self._editor)
        
        self.blockSignals(False)
        self.setUpdatesEnabled(True)
    
    def setColumn( self, column ):
        """
        Sets the column instance for this edit to the given column.
        
        :param      column | <orb.Column>
        """
        if ( not column ):
            return
        
        self._columnName = column.name()
        
        if ( column.columnType() != ColumnType.ForeignKey ):
            return
        
        if ( self._editor ):
            self._editor.setTableType(column.referenceModel())
            self._editor.setRequired(column.required())
    
    def setColumnName( self, columnName ):
        """
        Returns the column name that will be used for this edit.
        
        :param      columnName | <str>
        """
        self._columnName = nativestring(columnName)
    
    @Slot(int)
    def setColumnType( self, columnType ):
        """
        Sets the column type for this widget to the inputed type value.
        This will reset the widget to use one of the plugins for editing the
        value of the column.
        
        :param      columnType | <orb.ColumnType>
        """
        if ( columnType == self._columnType ):
            return False
        
        self._columnType = columnType
        self.rebuild()
        return True
    
    @Slot(str)
    def setColumnTypeText( self, columnTypeText ):
        """
        Sets the column type for this widget based on the inputed text.
        
        :param      columnTypeText | <str>
        """
        if ( not ColumnType ):
            return False
        
        try:
            columnType = ColumnType[nativestring(columnTypeText)]
        except KeyError:
            return False
        
        return self.setColumnType(columnType)
    
    def setLabel( self, text ):
        """
        Sets the label for this widget to the inputed text.  Differs per type.
        
        :param      text | <str>
        """
        if ( self._editor and hasattr(self._editor, 'setLabel') ):
            self._editor.setLabel(text)
            return True
        return False
    
    def setReadOnly( self, state ):
        """
        Sets the read only for this widget to the inputed state.  
        Differs per type, not all types support read only.
        
        :param      text | <str>
        """
        if ( self._editor and hasattr(self._editor, 'setReadOnly') ):
            self._editor.setReadOnly(state)
            return True
        return False
    
    @Slot(PyObject)
    def setValue( self, value ):
        """
        Sets the value for this edit to the inputed value.
        
        :param      value | <variant>
        """
        if ( self._editor ):
            self._editor.setValue(value)
            return True
        return False
    
    def value( self ):
        """
        Returns the current value for this widget.
        
        :return     <variant>
        """
        if ( self._editor ):
            return self._editor.value()
        return None
    
    x_columnTypeText = Property(str, columnTypeText, setColumnTypeText)
    x_columnName     = Property(str, columnName, setColumnName)
    x_label          = Property(str, label, setLabel)
    x_readOnly       = Property(bool, isReadOnly, setReadOnly)