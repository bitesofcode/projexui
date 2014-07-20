#!/usr/bin/python

""" [desc] """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintenance information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

from xqt import QtGui, QtCore

from projex.lazymodule import LazyModule
from projexui.widgets.xloaderwidget import XLoaderWidget

from .xtreewidgetitem import XTreeWidgetItem

xtreewidget = LazyModule('projexui.widgets.xtreewidget')

class XLoaderItem(XTreeWidgetItem):
    def __lt__(self, other):
        tree = self.treeWidget()
        if not isinstance(tree, xtreewidget.XTreeWidget):
            return False
        
        return tree.sortOrder() != QtCore.Qt.AscendingOrder
    
    def __init__(self, *args):
        super(XLoaderItem, self).__init__(*args)
        
        # define custom properties
        self._loading = False
        self._timer   = None
        
        # define standard properties
        self.setFlags(QtCore.Qt.ItemIsEnabled)
        self.setFirstColumnSpanned(True)
        self.setFixedHeight(30)
        self.setTextAlignment(0, QtCore.Qt.AlignCenter)
        
        palette = QtGui.QApplication.palette()
        fg = palette.color(palette.Disabled, palette.Text)
        self.setForeground(0, fg)
    
    def __del__(self):
        if self._timer:
            del self._timer
            self._timer = None
    
    def autoload(self, state=True):
        """
        Begins the process for autoloading this item when it becomes visible
        within the tree.
        
        :param      state | <bool>
        """
        if state and not self._timer:
            self._timer = QtCore.QTimer()
            self._timer.setInterval(500)
            self._timer.timeout.connect(self.testAutoload)
        if state and self._timer and not self._timer.isActive():
            self._timer.start()
        elif not state and self._timer and self._timer.isActive():
            self._timer.stop()
            del self._timer
            self._timer = None
    
    def startLoading(self):
        """
        Updates this item to mark the item as loading.  This will create
        a QLabel with the loading ajax spinner to indicate that progress
        is occurring.
        """
        if self._loading:
            return False
        
        tree = self.treeWidget()
        if not tree:
            return
        
        self._loading = True
        self.setText(0, '')
        
        # create the label for this item
        lbl = QtGui.QLabel(self.treeWidget())
        lbl.setMovie(XLoaderWidget.getMovie())
        lbl.setAlignment(QtCore.Qt.AlignCenter)
        tree.setItemWidget(self, 0, lbl)
        
        try:
            tree.loadStarted.emit(self)
        except AttributeError:
            pass
        
        return True
    
    def finishLoading(self):
        """
        Stops the loader for this item and removes it from the tree.
        """
        self.takeFromTree()
    
    def testAutoload(self):
        """
        Checks to see if this item should begin the loading process.
        """
        tree = self.treeWidget()
        if not tree:
            return
        
        rect = tree.visualItemRect(self)
        if rect.isNull():
            return
        
        center = rect.center()
        if not tree.rect().contains(center):
            return
        
        self.startLoading()
        self._timer.stop()
