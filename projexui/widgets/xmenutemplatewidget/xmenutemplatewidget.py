#!/usr/bin/python

""" Defines a widget for manipulating menu templates. """

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

from xml.etree          import ElementTree
from xml.parsers.expat  import ExpatError

from projex.text import nativestring

from projexui.qt import wrapVariant, unwrapVariant
from projexui.qt.QtCore import Qt,\
                               QSize,\
                               QMimeData,\
                               QByteArray,\
                               QEvent

from projexui.qt.QtGui import QWidget,\
                              QDialog,\
                              QVBoxLayout,\
                              QDialogButtonBox,\
                              QTreeWidgetItem,\
                              QCursor,\
                              QIcon,\
                              QMenu,\
                              QInputDialog,\
                              QMessageBox,\
                              QLineEdit

import projex.text

import projexui
import projexui.resources

class XMenuTemplateWidget(QWidget):
    """ """
    def __init__( self, parent = None ):
        super(XMenuTemplateWidget, self).__init__( parent )
        
        # load the user interface
        projexui.loadUi(__file__, self)
        
        # define custom properties
        self._actions = {}
        
        # set default properties
        self.uiActionTREE.setDataCollector( XMenuTemplateWidget.dataCollector )
        self.uiMenuTREE.installEventFilter(self)
        
        palette = self.uiMenuTREE.palette()
        palette.setColor(palette.Base, palette.color(palette.Window))
        palette.setColor(palette.Text, palette.color(palette.WindowText))
        self.uiMenuTREE.setPalette(palette)
        
        # create connections
        self.uiMenuTREE.customContextMenuRequested.connect( self.showMenu )
    
    def addMenuItem( self, newItem, atItem ):
        """
        Adds a new menu item at the given item.
        
        :param      newItem | <QTreeWidgetItem>
                    atItem  | <QTreeWidgetItem>
        """
        tree = self.uiMenuTREE
        
        if ( not atItem ):
            tree.addTopLevelItem(newItem)
            
        elif ( atItem.data(0, Qt.UserRole) == 'menu' ):
            atItem.addChild(newItem)
        
        elif ( atItem.parent() ):
            index = atItem.parent().indexOfChild(atItem)
            atItem.parent().insertChild(index + 1, newItem)
        
        else:
            index = tree.indexOfTopLevelItem(atItem)
            tree.insertTopLevelItem(index + 1, newItem)
    
    def createActionItem( self, key ):
        """
        Creates a new action item for the inputed key.
        
        :param      key | <str>
        
        :return     <QTreeWidgetItem>
        """
        action = self._actions.get(key)
        if ( not action ):
            text = 'Missing Action: %s' % key
            item = QTreeWidgetItem([text])
            ico = projexui.resources.find('img/log/warning.png')
            item.setIcon(0, QIcon(ico))
        else:
            item = QTreeWidgetItem([nativestring(action.text()).replace('&', '')])
            item.setIcon(0, action.icon())
        
        item.setSizeHint(0, QSize(120, 20))
        item.setData(0, Qt.UserRole, wrapVariant(key))
        
        flags = item.flags()
        flags ^= Qt.ItemIsDropEnabled
        item.setFlags(flags)
        
        return item
    
    def createMenu( self ):
        """
        Creates a new menu with the given name.
        """
        name, accepted = QInputDialog.getText( self,
                                               'Create Menu',
                                               'Name: ')
        
        if ( accepted ):
            self.addMenuItem(self.createMenuItem(name), 
                             self.uiMenuTREE.currentItem())
    
    def createMenuItem( self, title ):
        """
        Creates a new menu item with the given title.
        
        :param      title | <str>
        
        :return     <QTreeWidgetItem>
        """
        item = QTreeWidgetItem([title])
        ico = projexui.resources.find('img/folder.png')
        
        item.setIcon(0, QIcon(ico))
        item.setSizeHint(0, QSize(120, 20))
        item.setData(0, Qt.UserRole, wrapVariant('menu'))
        
        return item
    
    def createSeparator( self ):
        """
        Creates a new separator in the tree.
        """
        self.addMenuItem(self.createSeparatorItem(), 
                         self.uiMenuTREE.currentItem())
    
    def createSeparatorItem( self ):
        """
        Creates a new separator item.
        
        :return     <QTreeWidgetItem>
        """
        item = QTreeWidgetItem(['                                    '])
        font = item.font(0)
        font.setStrikeOut(True)
        item.setFont(0, font)
        item.setData(0, Qt.UserRole, wrapVariant('separator'))
        flags = item.flags()
        flags ^= Qt.ItemIsDropEnabled
        item.setFlags(flags)
        
        return item
    
    def eventFilter( self, object, event ):
        """
        Processes events for the menu tree.
        
        :param      event | <QEvent>
        """
        if ( not event.type() in (QEvent.DragEnter,
                                  QEvent.DragMove,
                                  QEvent.Drop) ):
            return False
        
        # support dragging and dropping
        if ( event.type() in (event.DragEnter, event.DragMove) ):
            data = event.mimeData()
            if ( data.hasFormat('application/x-actions') ):
                event.acceptProposedAction()
            return True
        
        # handle creation of new items
        if ( event.type() == QEvent.Drop ):
            data      = event.mimeData()
            actions   = nativestring(data.data('application/x-actions'))
            
            # determine the drop item
            pos       = event.pos()
            pos.setY(pos.y() - 20)
            drop_item = self.uiMenuTREE.itemAt(pos)
            
            tree = self.uiMenuTREE
            for key in actions.split(','):
                if ( not key ):
                    continue
                
                item = self.createActionItem(key)
                self.addMenuItem(item, drop_item)
                drop_item = item
                
            return True
            
        return False
    
    def loadXml( self, xaction ):
        """
        Loads the xml action to the menu template tree.
        
        :param      xaction | <xml.etree.ElementTree>
        """
        if ( xaction.tag == 'menu' ):
            title = xaction.get('title', '')
            item = self.createMenuItem(title)
            for xchild in xaction:
                item.addChild(self.loadXml(xchild))
            
        elif ( xaction.tag == 'separator' ):
            item = self.createSeparatorItem()
        
        else:
            key = xaction.get('name', '')
            item = self.createActionItem(key)
        
        return item
    
    def menuTemplate( self ):
        """
        Returns the new menu template based on the user preferences.
        
        :return     <str>
        """
        xml = ElementTree.Element('menu')
        for i in range(self.uiMenuTREE.topLevelItemCount()):
            self.saveXml(xml, self.uiMenuTREE.topLevelItem(i))
        
        projex.text.xmlindent(xml)
        return ElementTree.tostring(xml)
    
    def removeItem( self ):
        """
        Removes the item from the menu.
        """
        item = self.uiMenuTREE.currentItem()
        if ( not item ):
            return
        
        opts = QMessageBox.Yes | QMessageBox.No
        answer = QMessageBox.question( self,
                                       'Remove Item',
                                       'Are you sure you want to remove this '\
                                       ' item?',
                                       opts )
        
        if ( answer == QMessageBox.Yes ):
            parent = item.parent()
            if ( parent ):
                parent.takeChild(parent.indexOfChild(item))
            else:
                tree = self.uiMenuTREE
                tree.takeTopLevelItem(tree.indexOfTopLevelItem(item))
    
    def renameMenu( self ):
        """
        Prompts the user to supply a new name for the menu.
        """
        item = self.uiMenuTREE.currentItem()
        
        name, accepted = QInputDialog.getText( self,
                                               'Rename Menu',
                                               'Name:',
                                               QLineEdit.Normal,
                                               item.text(0))
        if ( accepted ):
            item.setText(0, name)
    
    def saveXml( self, xparent, item ):
        """
        Saves the information from the tree item to xml.
        
        :param      xparent | <xml.etree.ElementTree.Element>
                    item    | <QTreeWidgetItem>
        """
        key = nativestring(unwrapVariant(item.data(0, Qt.UserRole)))
        
        if ( key == 'separator' ):
            ElementTree.SubElement(xparent, 'separator')
        elif ( key == 'menu' ):
            elem = ElementTree.SubElement(xparent, 'menu')
            elem.set('title', nativestring(item.text(0)))
            
            for c in range(item.childCount()):
                self.saveXml(elem, item.child(c))
        else:
            elem = ElementTree.SubElement(xparent, 'action')
            elem.set('name', key)
    
    def setActions( self, actions ):
        """
        Sets the action options for this widget to the inputed list of actions.
        
        :param      actions | {<str> key: <QAction>, ..}
        """
        self._actions = actions
        
        self.uiActionTREE.blockSignals(True)
        self.uiActionTREE.setUpdatesEnabled(False)
        
        self.uiActionTREE.clear()
        actions = actions.items()
        actions.sort(key = lambda x: nativestring(x[1].text()).replace('&', ''))
        
        for key, action in actions:
            item = self.createActionItem(key)
            self.uiActionTREE.addTopLevelItem(item)
        
        self.uiActionTREE.setUpdatesEnabled(True)
        self.uiActionTREE.blockSignals(False)
    
    def setMenuTemplate( self, template ):
        """
        Sets the menu template for this widget to the inputed string template.
        
        :param      template | <str>
        """
        try:
            xtree = ElementTree.fromstring(nativestring(template))
        except ExpatError, e:
            logger.exception(e)
            return
        
        self.uiMenuTREE.setUpdatesEnabled(False)
        self.uiMenuTREE.blockSignals(True)
        
        self.uiMenuTREE.clear()
        for xaction in xtree:
            self.uiMenuTREE.addTopLevelItem(self.loadXml(xaction))
        
        self.uiMenuTREE.setUpdatesEnabled(True)
        self.uiMenuTREE.blockSignals(False)
    
    def showMenu( self ):
        """
        Creates a menu to display for the editing of template information.
        """
        item = self.uiMenuTREE.currentItem()
        
        menu = QMenu(self)
        act = menu.addAction('Add Menu...')
        act.setIcon(QIcon(projexui.resources.find('img/folder.png')))
        act.triggered.connect(self.createMenu)
        
        if ( item and item.data(0, Qt.UserRole) == 'menu' ):
            act = menu.addAction('Rename Menu...')
            ico = QIcon(projexui.resources.find('img/edit.png'))
            act.setIcon(ico)
            act.triggered.connect(self.renameMenu)
        
        act = menu.addAction('Add Separator')
        act.setIcon(QIcon(projexui.resources.find('img/ui/splitter.png')))
        act.triggered.connect(self.createSeparator)
        
        menu.addSeparator()
        
        act = menu.addAction('Remove Item')
        act.setIcon(QIcon(projexui.resources.find('img/remove.png')))
        act.triggered.connect(self.removeItem)
        act.setEnabled(item is not None)
        
        menu.exec_(QCursor.pos())
    
    @staticmethod
    def dataCollector( tree, items ):
        data = QMimeData()
        
        actions = []
        for item in items:
            actions.append(nativestring(unwrapVariant(item.data(0, Qt.UserRole))))
        actionstr = ','.join(actions)
        
        data.setData('application/x-actions', QByteArray(actionstr))
        return data
    
    @staticmethod
    def edit( parent, template, actions = None ):
        """
        Prompts the user to edit the menu template with the given actions. \
        If no actions are supplied, then the actions from the parent will \
        be used.
        
        :param      parent   | <QWidget>
                    template | <str>
                    actions  | {<str> name: <QAction>, .. } || None
        
        :return     (<str> template, <bool> accepted)
        """
        # collect the potential actions from the widget
        if ( actions is None ):
            actions = {}
            for action in parent.actions():
                key = nativestring(action.objectName())
                if ( not key ):
                    key = nativestring(action.text()).replace('&', '')
                
                if ( key ):
                    actions[key] = action
        
        if ( not actions ):
            return ('', False)
        
        dlg = QDialog(parent)
        dlg.setWindowTitle('Edit Menu')
        
        widget = XMenuTemplateWidget(dlg)
        widget.setActions(actions)
        widget.setMenuTemplate(template)
        widget.layout().setContentsMargins(0, 0, 0, 0)
        
        opts = QDialogButtonBox.Save | QDialogButtonBox.Cancel
        btns = QDialogButtonBox(opts, Qt.Horizontal, dlg)
        
        btns.accepted.connect( dlg.accept )
        btns.rejected.connect( dlg.reject )
        
        layout = QVBoxLayout()
        layout.addWidget(widget)
        layout.addWidget(btns)
        
        dlg.setLayout(layout)
        dlg.adjustSize()
        dlg.resize(650, 400)
        
        if ( dlg.exec_() ):
            return (widget.menuTemplate(), True)
        return ('', False)