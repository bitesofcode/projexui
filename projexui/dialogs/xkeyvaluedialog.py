#!/usr/bin/python

""" Defines a dialog used to edit a key/value pairing of information. """

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
from projexui.qt.QtCore import Qt

from projexui.qt.QtGui  import QDialog,\
                               QDialogButtonBox,\
                               QHBoxLayout,\
                               QVBoxLayout

from projexui.widgets.xlineedit import XLineEdit

class XKeyValueDialog(QDialog):
    def __init__( self, parent = None ):
        super(XKeyValueDialog, self).__init__(parent)
        
        # create the interface
        self._keyEdit   = XLineEdit(self)
        self._keyEdit.setMaximumWidth(80)
        self._keyEdit.setHint( 'set key' )
        
        self._valueEdit = XLineEdit(self)
        self._valueEdit.setHint( 'set value' )
        
        hbox = QHBoxLayout()
        hbox.addWidget(self._keyEdit)
        hbox.addWidget(self._valueEdit)
        
        opts    = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        buttons = QDialogButtonBox( opts, Qt.Horizontal, self )
        
        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(buttons)
        
        # update the look and size
        self.setLayout(vbox)
        self.setWindowTitle('Edit Pair')
        self.setMinimumWidth(350)
        self.adjustSize()
        self.setFixedHeight(self.height())
        
        # create connections
        buttons.accepted.connect( self.accept )
        buttons.rejected.connect( self.reject )
    
    def key( self ):
        """
        Returns the current value of the current pair's key.
        
        :return     <str>
        """
        return nativestring(self._keyEdit.text())
    
    def setKey( self, key ):
        """
        Sets the current value of the current pair's key.
        
        :param      key | <str>
        """
        self._keyEdit.setText(key)
    
    def setValue( self, value ):
        """
        Sets the current value of the current pair's value.
        
        :param      value | <str>
        """
        self._valueEdit.setText(value)
    
    def value( self ):
        """
        Returns the current value of the current pair's value.
        
        :return     <str>
        """
        return nativestring(self._valueEdit.text())
    
    @staticmethod
    def edit( key = '', value = '', parent = None ):
        """
        Prompts the user to edit the inputed key/value pairing.
        
        :param      key     | <str>
                    value   | <str>
                    parent  | <QWidget>
        
        :return     (<bool> accepted, <str> key, <str> value)
        """
        dlg = XKeyValueDialog(parent)
        dlg.setKey(key)
        dlg.setValue(value)
        
        if ( dlg.exec_() ):
            return (True, dlg.key(), dlg.value())
        
        return (False, '', '')