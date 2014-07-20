#!/usr/bin/python

""" Defines commonly used config settings for different apps. """

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
from projexui.qt.QtGui  import QAction,\
                               QKeySequence,\
                               QMessageBox,\
                               QTreeWidgetItem

from projexui.dialogs.xconfigdialog import XConfigWidget

import projexui

class ActionItem( QTreeWidgetItem ):
    def __init__( self, action ):
        super(QTreeWidgetItem, self).__init__()
        
        # set item properties
        self.setText(0, nativestring(action.text()).replace('&',''))
        self.setText(1, action.shortcut().toString())
        self.setToolTip(0, action.toolTip())
        
        # set custom properties
        self._action = action
    
    def action( self ):
        """
        Returns the action that is associated with this item.
        
        :return     <QAction>
        """
        return self._action

#------------------------------------------------------------------------------

class XShortcutWidget(XConfigWidget):
    """ """
    def __init__( self, parent = None, uifile = '' ):
        super(XShortcutWidget, self).__init__( parent, uifile )
        
        # load the user interface
        projexui.loadUi(__file__, self)
        
        # update the tree view
        header = self.uiActionTREE.header()
        header.setStretchLastSection(False)
        header.setResizeMode(0, header.Stretch)
        header.setResizeMode(1, header.ResizeToContents)
        
        window = projexui.topWindow()
        self.setActions(window.actions())
        
        # intercept key press events for the shortcut widget
        self.uiShortcutTXT.installEventFilter(self)
        
        # create connections
        self.uiActionTREE.itemSelectionChanged.connect( self.updateAction )
        self.uiClearBTN.clicked.connect( self.clear )
        self.uiSaveBTN.clicked.connect( self.updateShortcut )
    
    def actions( self ):
        """
        Returns a list of actions that are associated with this shortcut edit.
        
        :return     [<QAction>, ..]
        """
        output = []
        for i in range(self.uiActionTREE.topLevelItemCount()):
            output.append(self.uiActionTREE.topLevelItem(i).action())
        return output
    
    def clear( self ):
        """
        Clears the current settings for the current action.
        """
        item = self.uiActionTREE.currentItem()
        if ( not item ):
            return
        
        self.uiShortcutTXT.setText('')
        item.setText(1, '')
    
    def eventFilter( self, object, event ):
        """
        Filters out key press events for the shortcut section for this edit.
        
        :param      object | <QObject>
                    event  | <QEvent>
        """
        if ( object != self.uiShortcutTXT ):
            return False
            
        if ( event.type() == event.KeyPress ):
            seq = QKeySequence(event.key() + int(event.modifiers()))
            self.uiShortcutTXT.setText( seq.toString() )
            return True
            
        elif ( event.type() == event.KeyRelease):
            return True
        
        return False
    
    def save( self ):
        """
        Saves the current settings for the actions in the list and exits the
        widget.
        """
        if ( not self.updateShortcut() ):
            return False
            
        for i in range(self.uiActionTREE.topLevelItemCount()):
            item = self.uiActionTREE.topLevelItem(i)
            action = item.action()
            action.setShortcut( QKeySequence(item.text(1)) )
        
        return True
    
    def setActions( self, actions ):
        """
        Sets the list of actions that will be used for this shortcut widget \
        when editing.
        
        :param      actions | [<QAction>, ..]
        """
        self.uiActionTREE.blockSignals(True)
        self.uiActionTREE.setUpdatesEnabled(False)
        
        self.uiActionTREE.clear()
        for action in actions:
            self.uiActionTREE.addTopLevelItem(ActionItem(action))
        
        self.uiActionTREE.sortByColumn(0, Qt.AscendingOrder)
        self.uiActionTREE.blockSignals(False)
        self.uiActionTREE.setUpdatesEnabled(True)
    
    def updateAction( self ):
        """
        Updates the action to edit based on the current item.
        """
        item = self.uiActionTREE.currentItem()
        if ( item ):
            action = item.action()
        else:
            action = QAction()
            
        self.uiShortcutTXT.setText(action.shortcut().toString())
    
    def updateShortcut( self ):
        """
        Saves the current shortuct settings to the current item.
        
        :return     <bool> success
        """
        aitem = self.uiActionTREE.currentItem()
        if ( not aitem ):
            return True
        
        scut = self.uiShortcutTXT.text()
        if ( not scut ):
            aitem.setText(1, '')
            return True
            
        for i in range(self.uiActionTREE.topLevelItemCount()):
            item = self.uiActionTREE.topLevelItem(i)
            if (item != aitem and item.text(1) == scut):
                msg = '%s already is using the %s shortcut.' % (item.text(0),
                                                                scut)
                QMessageBox.critical( self,
                                      'Duplicate Shortcut',
                                      msg )
                return False
        
        # update the item
        aitem.setText(1, scut)
        return True