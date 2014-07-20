#!/usr/bin/python

""" 
Creates a key/value pair editing tree widget.
"""

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

from projex.text import nativestring

from xqt import QtCore, QtGui
from projexui import resources
from projexui.widgets.xtreewidget import XTreeWidget,\
                                         XTreeWidgetItem

class XKeyValueTreeWidget(XTreeWidget):
    def __init__(self, parent=None):
        super(XKeyValueTreeWidget, self).__init__(parent)
        
        # define custom properties
        self._initialized = False
        
        # define editing options
        self.setEditable(True)
        self.setAlternatingRowColors(True)
        self.setRootIsDecorated(False)
        self.setColumnEditingEnabled(0, False)
        
        # create connections
        self.itemClicked.connect(self.handleClick)

    def addEntry(self, key='', value=''):
        """
        Creates a new entry item for this widget.
        
        :param      key     | <str>
                    value   | <variant>
        """
        img = resources.find('img/close.png')
        new_item = XTreeWidgetItem()
        new_item.setText(1, nativestring(key))
        new_item.setText(2, nativestring(value))
        new_item.setIcon(0, QtGui.QIcon(img))
        new_item.setFixedHeight(22)
        self.insertTopLevelItem(self.topLevelItemCount() - 1, new_item)
        
        return new_item

    def dictionary(self):
        """
        Returns a dictionary of the key/value pairing for the items in
        this widget.
        
        :return     {<str> key: <str> value, ..}
        """
        output = {}
        for i in range(self.topLevelItemCount() - 1):
            item = self.topLevelItem(i)
            output[nativestring(item.text(1))] = nativestring(item.text(2))
        return output

    def handleClick(self, item, column):
        """
        Handles when the user clicks on an item -- this method will listen
        for when the user clicks the 'add another item' item or when the
        user clicks on the remove icon next to the item.
        """
        if item.text(0) == 'add another item':
            new_item = self.addEntry()
            self.setCurrentItem(new_item, 1)
            self.editItem(new_item, 1)
        
        elif column == 0:
            self.takeTopLevelItem(self.indexOfTopLevelItem(item))

    def showEvent(self, event):
        super(XKeyValueTreeWidget, self).showEvent(event)
        
        if not self._initialized:
            self.setDictionary({})

    def setDictionary(self, props):
        """
        Sets a dictionary of the key/value pairing for the items in
        this widget.
        
        :param      props | {<str> key: <str> value, ..}
        """
        if not self._initialized:
            self.setColumns(['', 'Property', 'Value'])
            self.setColumnWidth(0, 22)
            
        self._initialized = True
        
        self.clear()
        
        palette = self.palette()
        item = XTreeWidgetItem(self, ['add another item'])
        item.setForeground(0, palette.color(palette.Disabled, palette.Text))
        item.setTextAlignment(0, QtCore.Qt.AlignCenter)
        item.setFlags(QtCore.Qt.ItemFlags(0))
        item.setFixedHeight(22)
        item.setFirstColumnSpanned(True)
        
        for key, text in props.items():
            self.addEntry(key, text)

__designer_plugins__ = [XKeyValueTreeWidget]