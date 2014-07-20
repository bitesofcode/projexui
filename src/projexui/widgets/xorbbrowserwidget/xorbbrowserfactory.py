""" Defines a factory class to provide thumbnail and widget information for
    a record used by the XOrbBrowserWidget.
"""

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software, LLC'
__license__         = 'LGPL'

__maintainer__      = 'Projex Software, LLC'
__email__           = 'team@projexsoftware.com'

from projex.text import nativestring

from projexui.qt.QtGui import QIcon,\
                              QLineEdit,\
                              QComboBox

from orb import Query as Q, ColumnType
import projexui.resources

from projexui.widgets.xorbrecordbox    import XOrbRecordBox
from projexui.widgets.xmultitagedit import XMultiTagEdit
from projexui.widgets.xorbbrowserwidget.xcardwidget import XBasicCardWidget

class XOrbBrowserFactory(object):
    """
    Class to create a bridge between the ORB database system and the browser
    widget.
    """
    def __init__( self ):
        self._cardClasses = {None: XBasicCardWidget}
    
    def cardClass( self, record ):
        """
        Returns the class that will be used by the createCard method to generate
        card widgets for records.
        
        :param      record | <orb.Table>
        
        :return     <XAbstractCardWidget>
        """
        return self._cardClasses.get(type(record), self._cardClasses[None])
    
    def collectRecords( self, column ):
        """
        Collects records for the inputed column to choose from.
        
        :param      column | <orb.Column>
        
        :return     [<orb.Table>, ..]
        """
        model   = column.referenceModel()
        if ( not model ):
            return []
        
        records = model.select()
        records.sort()
        return records
    
    def columnOptions( self, tableType ):
        """
        Returns the column options for the inputed table type.
        
        :param      tableType | <subclass of orb.Table>
        
        :return     [<str>, ..]
        """
        if ( not tableType ):
            return []
        
        schema = tableType.schema()
        return map(lambda x: x.name(), schema.columns())
    
    def createCard( self, parent, record ):
        """
        Creates a new widget that will represent the card view for the inpued
        record.
        
        :param      parent | <QWidget>
                    record | <orb.Table>
        
        :return     <QWidget> || None
        """
        cls = self.cardClass(record)
        if ( cls ):
            card = cls(parent)
            card.setRecord(record)
            return card
        return None
    
    def createEditor( self, parent, schema, columnName, operatorType ):
        """
        Returns an editor for the inputed table type, based on the column and
        operator types.
        
        :param      schema          | <orb.TableSchema>
                    columnName      | <str>
                    operatorType    | <orb.Query.Op>
        
        :return     <QWidget>
        """
        column = schema.column(columnName)
        if ( not column ):
            return None
        
        ctype  = column.columnType()
        
        # based on the column and operator type, the editor may change
        if ( ctype == ColumnType.String ):
            if ( operatorType in (Q.Op.IsIn, Q.Op.IsNotIn) ):
                widget = XMultiTagEdit(parent)
            else:
                widget = QLineEdit(parent)
        
        elif ( ctype == ColumnType.Bool ):
            widget = QComboBox(parent)
            widget.addItems(['True', 'False'])
            widget.setEditable(True)
            widget.setInsertPolicy(QComboBox.NoInsert)
        
        elif ( ctype == ColumnType.ForeignKey ):
            widget = XOrbRecordBox(parent)
            widget.setRecords(self.collectRecords(column))
        
        else:
            widget = None
        
        return widget
    
    def editorData( self, editor ):
        """
        Pulls the value from the inputed editor.
        
        :param      editor | <QWidget>
        
        :return     <variant>
        """
        # set the information from a multi-tag edit
        if ( isinstance(editor, XMultiTagEdit) ):
            return editor.tags()
        
        # set the information from a combo box
        elif ( isinstance(editor, QComboBox) ):
            return nativestring(editor.currentText())
        
        # set the information from a line edit
        elif ( isinstance(editor, QLineEdit) ):
            return nativestring(editor.text())
        
        return None
    
    def setEditorData( self, editor, value ):
        """
        Sets the value for the given editor to the inputed value.
        
        :param      editor | <QWidget>
                    value  | <variant>
        """
        
        # set the data for a multitagedit
        if ( isinstance(editor, XMultiTagEdit) ):
            if ( not isinstance(value, list) ):
                value = [nativestring(value)]
            else:
                value = map(nativestring, value)
            
            editor.setTags(value)
            editor.setCurrentItem(editor.createItem())
            
        # set the data for a combobox
        elif ( isinstance(editor, QComboBox) ):
            i = editor.findText(nativestring(value))
            editor.setCurrentIndex(i)
            editor.lineEdit().selectAll()
        
        # set the data for a line edit
        elif ( isinstance(editor, QLineEdit) ):
            editor.setText(nativestring(value))
            editor.selectAll()
    
    def setCardClass( self, cardClass, tableType = None ):
        """
        Sets the card class for the system.  If the optional tableType parameter
        is supplied, then the card will be used only for specific record types.
        
        :param      cardClass | <subclass of XAbstractCardWidget>
                    tableType | <subclass of orb.Table>
        """
        self._cardClasses[tableType] = cardClass
    
    def thumbnail( self, record ):
        """
        Creates a new thumbnail for the inputed record.
        
        :param      record | <orb.Table>
        
        :return     <QIcon>
        """
        return QIcon(projexui.resources.find('img/missing_large.png'))
    
    def thumbnailText( self, record ):
        """
        Returns the text that will be used with the thumbnail in thumb mode.
        
        :param      record | <orb.Table>
        
        :return     <str>
        """
        return nativestring(record)