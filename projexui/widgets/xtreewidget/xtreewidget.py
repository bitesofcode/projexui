#!/usr/bin/python

""" 
Extends the base QTreeWidget class with additional methods.
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

#------------------------------------------------------------------------------

import datetime
import os
import re
import weakref

from xqt import QtGui, QtCore, Signal, Slot, Property, wrapVariant, unwrapVariant
from xml.etree import ElementTree

import projex.sorting

from projex.enum import enum
import projex.text
from projex.text import nativestring
from projexui.qt import Signal, Slot, Property, wrapVariant, unwrapVariant

from projexui import resources

from projexui.xexporter import XExporter
from projexui.widgets.xpopupwidget import XPopupWidget
from projexui.xpainter import XPainter

from .xtreewidgetdelegate import XTreeWidgetDelegate
from .xtreewidgetitem import XTreeWidgetItem
from .xloaderitem import XLoaderItem

COLUMN_FILTER_EXPR = re.compile('((\w+):([\w,\*]+|"[^"]+"?))')

ARROW_STYLESHEET = """
QTreeView::branch,
QTreeView::branch:has-siblings:!adjoins-item,
QTreeView::branch:has-siblings:adjoins-item {
    image: none;
}
QTreeView::branch:closed:has-children {
    image: url("%s");
}
QTreeView::branch:open:has-children {
    image: url("%s");
}
"""

class XTreeWidget(QtGui.QTreeWidget):
    """ Advanced QTreeWidget class. """
    
    __designer_icon__ = resources.find('img/ui/tree.png')
    
    columnHiddenChanged     = Signal(int, bool)
    headerMenuAboutToShow   = Signal(QtGui.QMenu, int)
    sortingChanged          = Signal(int, QtCore.Qt.SortOrder)
    itemCheckStateChanged   = Signal(QtGui.QTreeWidgetItem, int)
    itemMiddleClicked       = Signal(object, int)
    itemMiddleDoubleClicked = Signal(object, int)
    itemRightDoubleClicked  = Signal(object, int)
    loadStarted             = Signal(object)
    
    HoverMode = enum('NoHover', 'HoverRows', 'HoverItems')
    TraverseMode = enum('DepthFirst', 'BreadthFirst')
    
    def __init__(self, parent=None, delegateClass=None):
        super(XTreeWidget, self).__init__(parent)
        
        if delegateClass is None:
            delegateClass = XTreeWidgetDelegate
        
        # create custom properties
        self._headerMenu            = None
        self._maximumFilterLevel    = None
        self._filteredColumns       = [0]
        self._sortOrder             = QtCore.Qt.DescendingOrder
        self._dataCollectorRef      = None
        self._dragDropFilterRef     = None
        self._arrowStyle            = False
        self._columnMinimums        = {}
        self._columnEditing         = {}
        self._hint                  = ''
        self._useDragPixmaps        = True
        self._usePopupToolTip       = False
        self._lockedView            = None
        self._lockedColumn          = None
        self._editable              = False
        self._defaultItemHeight     = 0
        self._exporters             = {}
        self._resizeToContentsInteractive = False
        
        # record the down state items
        self._downItem              = None
        self._downState             = None
        self._downColumn            = None
        
        palette = self.palette()
        self._hintColor             = palette.color(palette.Disabled, 
                                                    palette.Text)
        
        ico = resources.find('img/treeview/drag_multi.png')
        self._dragMultiPixmap       = QtGui.QPixmap(ico)
        
        ico = resources.find('img/treeview/drag_single.png')
        self._dragSinglePixmap      = QtGui.QPixmap(ico)
        
        # store hovering information
        self._hoveredColumn         = -1
        self._hoveredItem           = None
        self._hoverBackground       = None
        self._hoverForeground       = None
        self._hoverMode             = XTreeWidget.HoverMode.NoHover
        
        # load exporters from the system
        for exporter in XExporter.plugins(XExporter.Flags.SupportsTree):
            self._exporters[exporter.filetype()] = exporter
        
        # create the delegate
        self.setItemDelegate(delegateClass(self))
        self.setMouseTracking(True)
        self.setTabKeyNavigation(True)
        self.setEditTriggers(QtGui.QTreeWidget.NoEditTriggers)
        
        self.header().installEventFilter(self)
        
        # setup header
        header = self.header()
        header.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        
        # connect signals
        header.customContextMenuRequested.connect( self.showHeaderMenu )
        header.sectionResized.connect(self.__setUserMinimumSize)
        header.sectionClicked.connect(self.emitSortingChanged)
        
        self.destroyed.connect(self.__destroyLockedView)
    
    def __collectFilterTerms( self, 
                            mapping, 
                            item = None, 
                            level = 0 ):
        """
        Generates a list of filter terms based on the column data for the \
        items in the tree.  If no parent is supplied, then the top level items \
        will be used, otherwise the children will be searched through.  The \
        level value will drive how far down the tree we will look for the terms.
        
        :param      mapping | {<int> column: <set> values, ..}
                    item    | <QtGui.QTreeWidgetItem> || None
                    level   | <int>
        """
        if not mapping:
            return
        
        max_level = self.maximumFilterLevel()
        if max_level != None and level > max_level:
            return False
        
        if not item:
            for i in range(self.topLevelItemCount()):
                self.__collectFilterTerms(mapping, self.topLevelItem(i))
        else:
            # add the item data to the mapping
            for index in mapping.keys():
                text = nativestring(item.text(index))
                if not text:
                    continue
                    
                mapping[index].add(text)
            
            for c in range(item.childCount()):
                self.__collectFilterTerms(mapping, item.child(c), level + 1)
    
    def __destroyLockedView(self):
        """
        Destroys the locked view from this widget.
        """
        if self._lockedView:
            self._lockedView.close()
            self._lockedView.deleteLater()
            self._lockedView = None
    
    def __filterItems(self,
                      terms,
                      autoExpand=True, 
                      caseSensitive=False,
                      parent=None,
                      level=0):
        """
        Filters the items in this tree based on the inputed keywords.
        
        :param      terms           | {<int> column: [<str> term, ..], ..}
                    autoExpand      | <bool>
                    caseSensitive   | <bool>
                    parent          | <QtGui.QTreeWidgetItem> || None
        
        :return     <bool> | found
        """
        # make sure we're within our mex level for filtering
        max_level = self.maximumFilterLevel()
        if max_level != None and level > max_level:
            return False
        
        found = False
        items = []
        
        # collect the items to process
        if not parent:
            for i in range(self.topLevelItemCount()):
                items.append(self.topLevelItem(i))
        else:
            for c in range(parent.childCount()):
                items.append(parent.child(c))
        
        for item in items:
            # if there is no filter keywords, then all items will be visible
            if not any(terms.values()):
                found = True
                item.setHidden(False)
                if autoExpand:
                    if item.parent() is not None or self.rootIsDecorated():
                        item.setExpanded(False)
                
                self.__filterItems(terms,
                                   autoExpand, 
                                   caseSensitive,
                                   item,
                                   level + 1)
            
            else:
                # match all generic keywords
                generic         = terms.get(-1, [])
                generic_found   = dict((key, False) for key in generic)
                
                # match all specific keywords
                col_found  = dict((col, False) for col in terms if col != -1)
                
                # look for any matches for any column
                mfound = False
                
                for column in self._filteredColumns:
                    # determine the check text based on case sensitivity
                    if caseSensitive:
                        check = nativestring(item.text(column))
                    else:
                        check = nativestring(item.text(column)).lower()
                    
                    specific = terms.get(column, [])
                    
                    # make sure all the keywords match
                    for key in generic + specific:
                        if not key:
                            continue
                        
                        # look for exact keywords
                        elif key.startswith('"') and key.endswith('"'):
                            if key.strip('"') == check:
                                if key in generic:
                                    generic_found[key] = True
                                
                                if key in specific:
                                    col_found[column] = True
                        
                        # look for ending keywords
                        elif key.startswith('*') and not key.endswith('*'):
                            if check.endswith(key.strip('*')):
                                if key in generic:
                                    generic_found[key] = True
                                if key in specific:
                                    col_found[column] = True
                        
                        # look for starting keywords
                        elif key.endswith('*') and not key.startswith('*'):
                            if check.startswith(key.strip('*')):
                                if key in generic:
                                    generic_found[key] = True
                                if key in specific:
                                    col_found[column] = True
                        
                        # look for generic keywords
                        elif key.strip('*') in check:
                            if key in generic:
                                generic_found[key] = True
                            if key in specific:
                                col_found[column] = True
                    
                    mfound = all(col_found.values()) and \
                             all(generic_found.values())
                    if mfound:
                        break
                
                # if this item is not found, then check all children
                if not mfound and (autoExpand or item.isExpanded()):
                    mfound = self.__filterItems(terms,
                                                autoExpand, 
                                                caseSensitive,
                                                item,
                                                level + 1)
                
                item.setHidden(not mfound)
                
                if mfound:
                    found = True
                
                if mfound and autoExpand and item.childCount():
                    item.setExpanded(True)
        
        return found
    
    def __setUserMinimumSize( self, section, oldSize, newSize ):
        """
        Records the user minimum size for a column.
        
        :param      section | <int>
                    oldSize | <int>
                    newSize | <int>
        """
        if self.isVisible():
            self._columnMinimums[section] = newSize
    
    def __updateLockedSection(self, index, oldSize, newSize):
        if self._lockedView:
            view = self._lockedView
            header = self._lockedView.header()
            
            view.blockSignals(True)
            header.blockSignals(True)
            view.setColumnWidth(index, newSize)
            header.blockSignals(False)
            view.blockSignals(False)
            
            self.__updateLockedView()
    
    def __updateStandardSection(self, index, oldSize, newSize):
        self.blockSignals(True)
        self.header().blockSignals(True)
        self.setColumnWidth(index, newSize)
        self.blockSignals(False)
        self.header().blockSignals(False)
        
        self.__updateLockedView()
    
    def __updateLockedView(self):
        width = 0
        for c in range(self._lockColumn+1):
            width += self.columnWidth(c)
        
        offset_h = self.horizontalScrollBar().height()
        self._lockedView.resize(width, self.height() - offset_h - 4)
    
    def blockAllSignals( self, state ):
        """
        Fully blocks all signals - tree, header signals.
        
        :param      state | <bool>
        """
        self.blockSignals(state)
        self.header().blockSignals(state)
    
    def checkedItems(self, column=0, parent=None, recurse=True):
        """
        Returns a list of the checked items for this tree widget based on
        the inputed column and parent information.
        
        :param      column  | <int>
                    parent  | <QtGui.QTreeWidget> || None
                    recurse | <bool>
        
        :return     [<QtGui.QTreeWidgetItem>, ..]
        """
        output = []
        if not parent:
            for i in range(self.topLevelItemCount()):
                item = self.topLevelItem(i)
                if item.checkState(column) == QtCore.Qt.Checked:
                    output.append(item)
                
                if recurse:
                    output += self.checkedItems(column, item, recurse)
        else:
            for c in range(parent.childCount()):
                item = parent.child(c)
                if item.checkState(column) == QtCore.Qt.Checked:
                    output.append(item)
                
                if recurse:
                    output += self.checkedItems(column, item, recurse)
        return output
    
    def clear(self):
        """
        Removes all the items from this tree widget.  This will go through
        and also destroy any XTreeWidgetItems prior to the model clearing
        its references.
        """
        # go through and properly destroy all the items for this tree
        for item in self.traverseItems():
            if isinstance(item, XTreeWidgetItem):
                item.destroy()
        
        super(XTreeWidget, self).clear()
    
    def collectFilterTerms( self, columns = None, ignore = None ):
        """
        Returns a collection of filter terms for this tree widget based on \
        the results in the tree items.  If the optional columns or ignore \
        values are supplied then the specific columns will be used to generate \
        the search terms, and the columns in the ignore list will be stripped \
        out.
        
        :param      columns | [<str> column, ..] || None
                    ignore  | [<str> column, ..] || None
        
        :return     {<str> column: [<str> term, ..]}
        """
        if ( columns == None ):
            columns = self.columns()
            
        if ( ignore ):
            columns = [column for column in columns if not column in ignore]
        
        # this will return an int/set pairing which we will change to a str/list
        terms = {}
        for column in columns:
            index = self.column(column)
            if ( index == -1 ):
                continue
            
            terms[index] = set()
        
        self.__collectFilterTerms(terms)
        return dict([(self.columnOf(i[0]), list(i[1])) for i in terms.items()])
    
    def column(self, name):
        """
        Returns the index of the column at the given name.
        
        :param      name | <str>
        
        :return     <int> (-1 if not found)
        """
        columns = self.columns()
        if name in columns:
            return columns.index(name)
        else:
            check = projex.text.underscore(name)
            for i, column in enumerate(columns):
                if projex.text.underscore(column) == check:
                    return i
        return -1
    
    def columnOf(self, index):
        """
        Returns the name of the column at the inputed index.
        
        :param      index | <int>
        
        :return     <str>
        """
        columns = self.columns()
        if ( 0 <= index and index < len(columns) ):
            return columns[index]
        return ''
    
    def columns( self ):
        """
        Returns the list of column names for this tree widget's columns.
        
        :return     [<str>, ..]
        """
        hitem = self.headerItem()
        output = []
        for c in range(hitem.columnCount()):
            text = nativestring(hitem.text(c))
            if ( not text ):
                text = nativestring(hitem.toolTip(c))
            output.append(text)
        return output
    
    def createHeaderMenu(self, index):
        """
        Creates a new header menu to be displayed.
        
        :return     <QtGui.QMenu>
        """
        menu = QtGui.QMenu(self)
        act = menu.addAction("Hide '%s'" % self.columnOf(index))
        act.triggered.connect( self.headerHideColumn )
        
        menu.addSeparator()
        
        act = menu.addAction('Sort Ascending')
        act.setIcon(QtGui.QIcon(resources.find('img/sort_ascending.png')))
        act.triggered.connect( self.headerSortAscending )
        
        act = menu.addAction('Sort Descending')
        act.setIcon(QtGui.QIcon(resources.find('img/sort_descending.png')))
        act.triggered.connect( self.headerSortDescending )
        
        act = menu.addAction('Resize to Contents')
        act.setIcon(QtGui.QIcon(resources.find('img/treeview/fit.png')))
        act.triggered.connect( self.resizeToContents )
        
        menu.addSeparator()
        
        colmenu = menu.addMenu( 'Show/Hide Columns' )
        colmenu.setIcon(QtGui.QIcon(resources.find('img/columns.png')))
        colmenu.addAction('Show All')
        colmenu.addAction('Hide All')
        colmenu.addSeparator()
        
        hitem = self.headerItem()
        columns = self.columns()
        for column in sorted(columns):
            col    = self.column(column)
            action = colmenu.addAction(column)
            action.setCheckable(True)
            action.setChecked(not self.isColumnHidden(col))
        
        colmenu.triggered.connect( self.toggleColumnByAction )
        
        menu.addSeparator()
        exporters = self.exporters()
        if exporters:
            submenu = menu.addMenu('Export as')
            submenu.setIcon(QtGui.QIcon(resources.find('img/export.png')))
            for exporter in exporters:
                act = submenu.addAction(exporter.name())
                act.setData(wrapVariant(exporter.filetype()))
            submenu.triggered.connect(self.exportAs)
        
        return menu
    
    def dataCollector( self ):
        """
        Returns a method or function that will be used to collect mime data \
        for a list of treewidgetitems.  If set, the method should accept a \
        single argument for a list of items and then return a QMimeData \
        instance.
        
        :usage      |from projexui.qt.QtCore import QMimeData, QWidget
                    |from projexui.widgets.xtreewidget import XTreeWidget
                    |
                    |def collectData(tree, items):
                    |   data = QMimeData()
                    |   data.setText(','.join(map(lambda x: x.text(0), items)))
                    |   return data
                    |
                    |class MyWidget(QWidget):
                    |   def __init__( self, parent ):
                    |       super(MyWidget, self).__init__(parent)
                    |       
                    |       self._tree = XTreeWidget(self)
                    |       self._tree.setDataCollector(collectData)
                    
        
        :return     <function> || <method> || None
        """
        func = None
        if self._dataCollectorRef:
            func = self._dataCollectorRef()
        if not func:
            self._dataCollectorRef = None
        return func
    
    def defaultItemHeight(self):
        """
        Returns the default item height for this instance.
        
        :return     <int>
        """
        return self._defaultItemHeight
    
    def dragEnterEvent( self, event ):
        """
        Processes the drag drop event using the filter set by the \
        setDragDropFilter
        
        :param      event | <QDragEvent>
        """
        filt = self.dragDropFilter()
        if not filt:
            super(XTreeWidget, self).dragEnterEvent(event)
            return
            
        filt(self, event)
        
    def dragMoveEvent( self, event ):
        """
        Processes the drag drop event using the filter set by the \
        setDragDropFilter
        
        :param      event | <QDragEvent>
        """
        filt = self.dragDropFilter()
        if not filt:
            super(XTreeWidget, self).dragMoveEvent(event)
            return
        
        filt(self, event)
    
    def dragMultiPixmap( self ):
        """
        Returns the pixmap used to show multiple items dragged.
        
        :return     <QtGui.QPixmap>
        """
        return self._dragMultiPixmap
    
    def dragSinglePixmap( self ):
        """
        Returns the pixmap used to show single items dragged.
        
        :return     <QtGui.QPixmap>
        """
        return self._dragSinglePixmap
    
    def dragDropFilter( self ):
        """
        Returns a drag and drop filter method.  If set, the method should \
        accept 2 arguments: a QWidget and a drag/drop event and process it.
        
        :usage      |from projexui.qt.QtCore import QEvent
                    |
                    |class MyWidget(QWidget):
                    |   def __init__( self, parent ):
                    |       super(MyWidget, self).__init__(parent)
                    |       
                    |       self._tree = XTreeWidget(self)
                    |       self._tree.setDragDropFilter(MyWidget.handleDragDrop)
                    |   
                    |   @staticmethod
                    |   def handleDragDrop(object, event):
                    |       if ( event.type() == QEvent.DragEnter ):
                    |           event.acceptProposedActions()
                    |       elif ( event.type() == QEvent.Drop ):
                    |           print 'dropping'
        
        :return     <function> || <method> || None
        """
        filt = None
        if self._dragDropFilterRef:
            filt = self._dragDropFilterRef()
        
        if not filt:
            self._dragDropFilterRef = None
            
        return filt
     
    def dropEvent( self, event ):
        """
        Processes the drag drop event using the filter set by the \
        setDragDropFilter
        
        :param      event | <QDropEvent>
        """
        filt = self.dragDropFilter()
        if not filt:
            super(XTreeWidget, self).dropEvent(event)
            return
        
        filt(self, event)
    
    def edit(self, index, trigger, event):
        """
        Prompts the edit for the inputed index given a trigger and event.
        
        :param      index   | <QModelIndex>
                    trigger | <EditTrigger>
                    event   | <QEvent>
        """
        # disable right-click editing
        if trigger in (self.SelectedClicked, self.DoubleClicked) and \
           event.button() in (QtCore.Qt.RightButton, QtCore.Qt.MidButton):
            return False
        
        if not self.isColumnEditingEnabled(index.column()):
            return False
        
        item = self.itemFromIndex(index)
        if isinstance(item, XTreeWidgetItem) and \
            not item.isColumnEditingEnabled(index.column()):
            return False
        
        return super(XTreeWidget, self).edit(index, trigger, event)
    
    def emitSortingChanged( self, index ):
        """
        Emits the sorting changed signal if the user clicks on a sorting
        column.
        
        :param      index | <int>
        """
        if not self.signalsBlocked() and self.isSortingEnabled():
            self.sortingChanged.emit(index, self.header().sortIndicatorOrder())
    
    def export(self, filename, exporter=None):
        """
        Exports the data from this tree to the given filename.
        
        :param      filename | <str>
        """
        filename = nativestring(filename)
        if exporter is None:
            ext = os.path.splitext(filename)[1]
            exporter = self.exporter(ext)
        
        if exporter:
            return exporter.exportTree(self, filename)
        else:
            return False
    
    def exporter(self, ext):
        """
        Returns the exporter for this tree for the given extension.
        
        :param      ext | <str>
        """
        return self._exporters.get(nativestring(ext))
    
    def exporters(self):
        """
        Returns a list of exporters associated with this tree widget.
        
        :return     [<projexui.xexporter.XExporter>, ..]
        """
        return self._exporters.values()
    
    def exportAs(self, action):
        """
        Prompts the user to export the information for this tree based on the
        available exporters.
        """
        plugin = self.exporter(unwrapVariant(action.data()))
        if not plugin:
            return False
        
        ftypes = '{0} (*{1});;All Files (*.*)'.format(plugin.name(),
                                                      plugin.filetype())
        filename = QtGui.QFileDialog.getSaveFileName(self.window(),
                                                     'Export Data',
                                                     '',
                                                     ftypes)
        
        if type(filename) == tuple:
            filename = filename[0]
        
        if filename:
            return self.export(nativestring(filename), exporter=plugin)
        return False
    
    def eventFilter(self, obj, event):
        if obj == self.header() and \
           self.isResizeToContentsInteractive() and \
           self.topLevelItemCount():
            if event.type() == event.Enter:
                for c in range(self.columnCount()):
                    if obj.resizeMode(c) == obj.ResizeToContents:
                        obj.setResizeMode(c, obj.Interactive)

        return super(XTreeWidget, self).eventFilter(obj, event)
    
    def isColumnEditingEnabled(self, column):
        """
        Sets whether or not the given column for this item should be editable.
        
        :param      column | <int>
        
        :return     <bool>
        """
        return self._columnEditing.get(column, True)
    
    def isResizeToContentsInteractive(self):
        return self._resizeToContentsInteractive
    
    def viewportEvent( self, event ):
        """
        Displays the help event for the given index.
        
        :param      event  | <QHelpEvent>
                    view   | <QAbstractItemView>
                    option | <QStyleOptionViewItem>
                    index  | <QModelIndex>
        
        :return     <bool>
        """
        # intercept tooltips to use the XPopupWidget when desired
        if event.type() == event.ToolTip and self.usePopupToolTip():
            index = self.indexAt(event.pos())
            item  = self.itemAt(event.pos())
            
            if not (index and item):
                event.ignore()
                return False
            
            tip   = item.toolTip(index.column())
            rect  = self.visualRect(index)
            point = QtCore.QPoint(rect.left() + 5, rect.bottom() + 1)
            point = self.viewport().mapToGlobal(point)
            
            if tip:
                XPopupWidget.showToolTip(tip, 
                                         anchor = XPopupWidget.Anchor.TopLeft,
                                         point  = point,
                                         parent = self)
            
            event.accept()
            return True
        else:
            return super(XTreeWidget, self).viewportEvent(event)
    
    def findNextItem(self, item):
        """
        Returns the next item in the tree.
        
        :param      item | <QtGui.QTreeWidgetItem>
        
        :return     <QtGui.QTreeWidgetItem>
        """
        if not item:
            return None
        
        if item.childCount():
            return item.child(0)
        
        while item.parent():
            index = item.parent().indexOfChild(item)
            child = item.parent().child(index+1)
            if child:
                return child
            
            item = item.parent()
        
        index = self.indexOfTopLevelItem(item)
        return self.topLevelItem(index+1)
    
    def findPreviousItem(self, item):
        """
        Returns the previous item in the tree.
        
        :param      item | <QtGui.QTreeWidgetItem>
        
        :return     <QtGui.QTreeWidgetItem> || None
        """
        if not item:
            return None
        
        while item.parent():
            index = item.parent().indexOfChild(item)
            if index == 0:
                return item.parent()
            
            child = item.parent().child(index-1)
            if child:
                while child.childCount():
                    child = child.child(child.childCount() - 1)
                return child
            
            item = item.parent()
        
        index = self.indexOfTopLevelItem(item)
        out = self.topLevelItem(index-1)
        while out and out.childCount():
            out = out.child(out.childCount() - 1)
        return out
    
    def filteredColumns( self ):
        """
        Returns the columns that are used for filtering for this tree.
        
        :return     [<int>, ..]
        """
        return self._filteredColumns
    
    @Slot(str)
    def filterItems(self,
                    terms,
                    autoExpand=True,
                    caseSensitive=False):
        """
        Filters the items in this tree based on the inputed text.
        
        :param      terms           | <str> || {<str> column: [<str> opt, ..]}
                    autoExpand      | <bool>
                    caseSensitive   | <bool>
        """
        # create a dictionary of options
        if type(terms) != dict:
            terms = {'*': nativestring(terms)}
        
        # create a dictionary of options
        if type(terms) != dict:
            terms = {'*': nativestring(terms)}
        
        # validate the "all search"
        if '*' in terms and type(terms['*']) != list:
            sterms = nativestring(terms['*'])
            
            if not sterms.strip():
                terms.pop('*')
            else:
                dtype_matches = COLUMN_FILTER_EXPR.findall(sterms)
                
                # generate the filter for each data type
                for match, dtype, values in dtype_matches:
                    sterms = sterms.replace(match, '')
                    terms.setdefault(dtype, [])
                    terms[dtype] += values.split(',')
                
                keywords = sterms.replace(',', '').split()
                while '' in keywords:
                    keywords.remove('')
                
                terms['*'] = keywords
        
        # filter out any columns that are not being searched
        filtered_columns = self.filteredColumns()
        filter_terms = {}
        for column, keywords in terms.items():
            index = self.column(column)
            if column != '*' and not index in filtered_columns:
                continue
            
            if not caseSensitive:
                keywords = [nativestring(keyword).lower() for keyword in keywords]
            else:
                keywords = map(str, keywords)
            
            filter_terms[index] = keywords
        
        self.__filterItems(filter_terms, autoExpand, caseSensitive, 0)
    
    def gridPen(self):
        """
        Returns the pen that will be used when drawing the grid lines.
        
        :return     <QtGui.QPen>
        """
        delegate = self.itemDelegate()
        if isinstance(delegate, XTreeWidgetDelegate):
            return delegate.gridPen()
        return QtGui.QPen()
    
    def extendsTree( self ):
        """
        Returns whether or not the grid lines should extend through the tree \
        area or not.
        
        :return <bool>
        """
        delegate = self.itemDelegate()
        if ( isinstance(delegate, XTreeWidgetDelegate) ):
            return delegate.extendsTree()
        return False
    
    def headerHideColumn( self ):
        """
        Hides the current column set by the header index.
        """
        self.setColumnHidden(self._headerIndex, True)
        
        # ensure we at least have 1 column visible
        found = False
        for col in range(self.columnCount()):
            if ( not self.isColumnHidden(col) ):
                found = True
                break
        
        if ( not found ):
            self.setColumnHidden(0, False)
    
    def headerMenu(self):
        """
        Returns the menu to be displayed for this tree's header menu request.
        
        :return     <QtGui.QMenu> || None
        """
        return self._headerMenu
    
    def headerMenuColumn(self):
        """
        Returns the index of the column that is being edited for the header
        menu.
        
        :return     <int>
        """
        return self._headerIndex
    
    def headerSortAscending( self ):
        """
        Sorts the column at the current header index by ascending order.
        """
        self.setSortingEnabled(True)
        self.sortByColumn(self._headerIndex, QtCore.Qt.AscendingOrder)
    
    def headerSortDescending( self ):
        """
        Sorts the column at the current header index by descending order.
        """
        self.setSortingEnabled(True)
        self.sortByColumn(self._headerIndex, QtCore.Qt.DescendingOrder)
    
    def hiddenColumns( self ):
        """
        Returns a list of the hidden columns for this tree.
        
        :return     [<str>, ..]
        """
        output  = []
        columns = self.columns()
        for c, column in enumerate(columns):
            if ( not self.isColumnHidden(c) ):
                continue
            output.append(column)
        return output
    
    def highlightByAlternate(self):
        """
        Sets the palette highlighting for this tree widget to use a darker
        version of the alternate color vs. the standard highlighting.
        """
        palette = QtGui.QApplication.palette()
        palette.setColor(palette.HighlightedText, palette.color(palette.Text))
        
        clr = palette.color(palette.AlternateBase)
        palette.setColor(palette.Highlight, clr.darker(110))
        self.setPalette(palette)
    
    def hint( self ):
        """
        Returns the hint that will be rendered for this tree if there are no
        items defined.
        
        :return     <str>
        """
        return self._hint
    
    def hintColor( self ):
        """
        Returns the color used for the hint rendering.
        
        :return     <QtGui.QColor>
        """
        return self._hintColor
    
    def hoverBackground( self ):
        """
        Returns the default hover background for this tree widget.
        
        :return     <QtGui.QBrush> || None
        """
        return self._hoverBackground
        
    def hoverForeground( self ):
        """
        Returns the default hover foreground for this tree widget.
        
        :return     <QtGui.QBrush> || None
        """
        return self._hoverForeground
    
    def hoverMode( self ):
        """
        Returns the hover mode for this tree widget.
        
        :return     <XTreeWidget.HoverMode>
        """
        return self._hoverMode
    
    def hoveredColumn( self ):
        """
        Returns the currently hovered column.  -1 will be returned if no
        column is hovered.
        
        :return     <int>
        """
        return self._hoveredColumn
    
    def hoveredItem(self):
        """
        Returns the currently hovered item.
        
        :return     <QtGui.QTreeWidgetItem> || None
        """
        out = None
        if ( self._hoveredItem is not None ):
            out = self._hoveredItem()
            
            if out is None:
                self._hoveredItem = None
        
        return out
    
    def isArrowStyle( self ):
        """
        Returns whether or not the stylesheet is using arrows to group.
        
        :return     <bool>
        """
        return self._arrowStyle
    
    def isEditable( self ):
        """
        Returns whether or not this tree widget is editable or not.
        
        :return     <bool>
        """
        return self._editable
    
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Right:
            item = self.currentItem()
            next = self.findNextItem(item)
            if next:
                self.setCurrentItem(next)
                self.scrollToItem(next)
                return

        elif event.key() == QtCore.Qt.Key_Left:
            item = self.currentItem()
            prev = self.findPreviousItem(item)
            if prev:
                prev.setExpanded(False)
                self.setCurrentItem(prev)
                self.scrollToItem(prev)
                return
        
        super(XTreeWidget, self).keyPressEvent(event)
    
    def leaveEvent( self, event ):
        """
        Dismisses the hovered item when the tree is exited.
        
        :param      event | <QEvent>
        """
        hitem = self.hoveredItem()
        hcol  = self.hoveredColumn()
        
        if ( hitem != None ):
            self._hoveredItem   = None
            self._hoveredColumn = -1
            
            rect = self.visualItemRect(hitem)
            rect.setWidth(self.viewport().width())
            self.viewport().update(rect)
        
        super(XTreeWidget, self).leaveEvent(event)
    
    def lockToColumn(self, index):
        """
        Sets the column that the tree view will lock to.  If None is supplied,
        then locking will be removed.
        
        :param      index | <int> || None
        """
        self._lockColumn = index
        
        if index is None:
            self.__destroyLockedView()
            return
        else:
            if not self._lockedView:
                view = QtGui.QTreeView(self.parent())
                view.setModel(self.model())
                view.setSelectionModel(self.selectionModel())
                view.setItemDelegate(self.itemDelegate())
                view.setFrameShape(view.NoFrame)
                view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
                view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
                view.setRootIsDecorated(self.rootIsDecorated())
                view.setUniformRowHeights(True)
                view.setFocusProxy(self)
                view.header().setFocusProxy(self.header())
                view.setStyleSheet(self.styleSheet())
                view.setAutoScroll(False)
                view.setSortingEnabled(self.isSortingEnabled())
                view.setPalette(self.palette())
                view.move(self.x(), self.y())
                
                self.setAutoScroll(False)
                self.setUniformRowHeights(True)
                
                view.collapsed.connect(self.collapse)
                view.expanded.connect(self.expand)
                view.expanded.connect(self.__updateLockedView)
                view.collapsed.connect(self.__updateLockedView)
                
                view_head = view.header()
                for i in range(self.columnCount()):
                    view_head.setResizeMode(i, self.header().resizeMode(i))
                
                view.header().sectionResized.connect(self.__updateStandardSection)
                self.header().sectionResized.connect(self.__updateLockedSection)
                
                vbar = view.verticalScrollBar()
                self.verticalScrollBar().valueChanged.connect(vbar.setValue)
                
                self._lockedView = view
            
            self.__updateLockedView()
    
    def maximumFilterLevel( self ):
        """
        Returns the maximum level from which the filtering of this tree's \
        items should finish.
        
        :return     <int> || None
        """
        return self._maximumFilterLevel
        
    def mimeData(self, items):
        """
        Returns the mime data for dragging for this instance.
        
        :param      items | [<QtGui.QTreeWidgetItem>, ..]
        """
        func = self.dataCollector()
        if func:
            return func(self, items)
        
        data = super(XTreeWidget, self).mimeData(items)
        
        # return defined custom data
        if len(items) == 1:
            try:
                dragdata = items[0].dragData()
            except AttributeError:
                return data
            
            if not data:
                data = QtCore.QMimeData()
            
            urls = []
            for format, value in dragdata.items():
                if format == 'url':
                    urls.append(QtCore.QUrl(value))
                else:
                    data.setData(format, QtCore.QByteArray(value))
            
            data.setUrls(urls)
            return data
        
        return data
    
    def moveEvent(self, event):
        super(XTreeWidget, self).moveEvent(event)
        
        if self._lockedView:
            self._lockedView.move(self.x() + self.frameWidth(), 
                                  self.y() + self.frameWidth())
    
    def mouseDoubleClickEvent(self, event):
        """
        Overloads when a mouse press occurs.  If in editable mode, and the
        click occurs on a selected index, then the editor will be created
        and no selection change will occur.
        
        :param      event | <QMousePressEvent>
        """
        item = self.itemAt(event.pos())
        column = self.columnAt(event.pos().x())
        
        mid_button = event.button() == QtCore.Qt.MidButton
        ctrl_click = event.button() == QtCore.Qt.LeftButton and \
                     event.modifiers() == QtCore.Qt.ControlModifier
        
        if mid_button or ctrl_click:
            self.itemMiddleDoubleClicked.emit(item, column)
        elif event.button() == QtCore.Qt.RightButton:
            self.itemRightDoubleClicked.emit(item, column)
        else:
            super(XTreeWidget, self).mouseDoubleClickEvent(event)
    
    def mousePressEvent(self, event):
        """
        Overloads when a mouse press occurs.  If in editable mode, and the
        click occurs on a selected index, then the editor will be created
        and no selection change will occur.

        :param      event | <QMousePressEvent>
        """
        item = self.itemAt(event.pos())
        column = self.columnAt(event.pos().x())

        mid_button = event.button() == QtCore.Qt.MidButton
        ctrl_click = event.button() == QtCore.Qt.LeftButton and \
                     event.modifiers() == QtCore.Qt.ControlModifier

        if item and column != -1:
            self._downItem   = weakref.ref(item)
            self._downColumn = column
            self._downState  = item.checkState(column)

        elif not item:
            self.setCurrentItem(None)
            self.clearSelection()

        if (mid_button or ctrl_click) and item and column != -1:
            self.itemMiddleClicked.emit(item, column)

        index = self.indexAt(event.pos())
        sel_model = self.selectionModel()

        if self.isEditable() and index and sel_model.isSelected(index):
            sel_model.setCurrentIndex(index, sel_model.NoUpdate)
            self.edit(index, self.SelectedClicked, event)
            event.accept()
        else:
            super(XTreeWidget, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """
        Tracks when an item is hovered and exited.

        :param      event | <QMoustEvent>
        """
        if self.hoverMode() != XTreeWidget.HoverMode.NoHover:
            item  = self.itemAt(event.pos())
            col   = self.columnAt(event.pos().x())
            hitem = self.hoveredItem()
            hcol  = self.hoveredColumn()

            if (id(item), col) != (id(hitem), hcol):
                if ( item ):
                    self._hoveredItem = weakref.ref(item)
                else:
                    self._hoveredItem = None

                self._hoveredColumn = col

                rect  = self.visualItemRect(item)
                hrect = self.visualItemRect(hitem)

                rect.setWidth(self.viewport().width())
                hrect.setWidth(self.viewport().width())

                self.viewport().update(rect)
                self.viewport().update(hrect)

        super(XTreeWidget, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        super(XTreeWidget, self).mouseReleaseEvent(event)

        if self._downItem and self._downItem():
            state = self._downItem().checkState(self._downColumn)
            if state != self._downState:
                self.itemCheckStateChanged.emit(self._downItem(), self._downColumn)

        self._downItem = None
        self._downState = None
        self._downColumn = None
    
    def moveCursor(self, cursorAction, modifiers):
        """
        Returns a QModelIndex object pointing to the next object in the 
        view, based on the given cursorAction and keyboard modifiers 
        specified by modifiers.
        
        :param      modifiers | <QtCore.Qt.KeyboardModifiers>
        """
        # moves to the next index
        if cursorAction not in (self.MoveNext,
                                self.MoveRight,
                                self.MovePrevious,
                                self.MoveLeft,
                                self.MoveHome,
                                self.MoveEnd):
            return super(XTreeWidget, self).moveCursor(cursorAction, modifiers)
        
        header = self.header()
        index = self.currentIndex()
        row  = index.row()
        col  = index.column()
        vcol = None
        
        if cursorAction == self.MoveEnd:
            vcol = header.count() - 1
            delta = -1
        elif cursorAction == self.MoveHome:
            vcol = 0
            delta = +1
        elif cursorAction in (self.MoveNext, self.MoveRight):
            delta = +1
        elif cursorAction in (self.MovePrevious, self.MoveLeft):
            delta = -1
        
        if vcol is None:
            vcol = header.visualIndex(col) + delta
        
        ncol = header.count()
        lcol = header.logicalIndex(vcol)
        
        while 0 <= vcol and vcol < ncol and self.isColumnHidden(lcol):
            vcol += delta
            lcol = header.logicalIndex(vcol)
        
        sibling = index.sibling(index.row(), lcol)
        if sibling and sibling.isValid():
            return sibling
        elif delta < 0:
            return index.sibling(index.row() - 1, header.logicalIndex(ncol - 1))
        else:
            return index.sibling(index.row() + 1, header.visualIndex(0))
    
    def paintEvent( self, event ):
        """
        Overloads the paint event to support rendering of hints if there are
        no items in the tree.
        
        :param      event | <QPaintEvent>
        """
        super(XTreeWidget, self).paintEvent(event)
        
        if not self.visibleTopLevelItemCount() and self.hint():
            text    = self.hint()
            rect    = self.rect()
            
            # modify the padding on the rect
            w = min(250, rect.width() - 30)
            x = (rect.width() - w) / 2
            
            rect.setX(x)
            rect.setY(rect.y() + 15)
            rect.setWidth(w)
            rect.setHeight(rect.height() - 30)
            
            align = int(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
            
            # setup the coloring options
            clr     = self.hintColor()
            
            # paint the hint
            with XPainter(self.viewport()) as painter:
                painter.setPen(clr)
                painter.drawText(rect, align | QtCore.Qt.TextWordWrap, text)
    
    def resizeEvent(self, event):
        super(XTreeWidget, self).resizeEvent(event)
        
        if self._lockedView:
            self.__updateLockedView()
    
    @Slot()
    def resizeToContents(self):
        """
        Resizes all of the columns for this tree to fit their contents.
        """
        for c in range(self.columnCount()):
            self.resizeColumnToContents(c)
    
    def resizeColumnToContents(self, column):
        """
        Resizes the inputed column to the given contents.
        
        :param      column | <int>
        """
        self.header().blockSignals(True)
        self.setUpdatesEnabled(False)
        
        super(XTreeWidget, self).resizeColumnToContents(column)
        
        min_w = self._columnMinimums.get(column, 0)
        cur_w = self.columnWidth(column)
        if cur_w < min_w:
            self.setColumnWidth(column, min_w)
        
        self.setUpdatesEnabled(True)
        self.header().blockSignals(False)
    
    def restoreXml(self, xml):
        """
        Restores properties for this tree widget from the inputed XML.
        
        :param      xml | <xml.etree.ElementTree.Element>
        
        :return     <bool> success
        """
        if xml is None:
            return False
        
        self.setUpdatesEnabled(False)
        self.blockSignals(True)
        
        # restore column data
        header = self.header()
        xcolumns = xml.find('columns')
        if xcolumns is not None:
            for xcolumn in xcolumns:
                name   = xcolumn.get('name')
                index  = self.column(name)
                vindex = int(xcolumn.get('visualIndex', index))
                currvi = header.visualIndex(index)
                
                # restore from name
                if index == -1:
                    continue
                
                if currvi != vindex:
                    header.moveSection(currvi, vindex)
                
                self.setColumnHidden(index, xcolumn.get('hidden') == 'True')
                
                if not self.isColumnHidden(index):
                    width  = int(xcolumn.get('width', self.columnWidth(index)))
                    self.setColumnWidth(index, width)
        
        # restore order data
        headerState = xml.get('headerState')
        if headerState is not None:
            state = QtCore.QByteArray.fromBase64(str(headerState))
            self.header().restoreState(state)
        
        sortColumn = int(xml.get('sortColumn', 0))
        sortingEnabled = xml.get('sortingEnabled') == 'True'
        sortOrder = QtCore.Qt.SortOrder(int(xml.get('sortOrder', 0)))
        
        if sortingEnabled:
            self.setSortingEnabled(sortingEnabled)
            self.sortByColumn(sortColumn, sortOrder)
        
        self.setUpdatesEnabled(True)
        self.blockSignals(False)
        
        return True
    
    def restoreSettings(self, settings):
        """
        Restores properties for this tree widget from the inputed XML.
        
        :param      xml | <xml.etree.ElementTree.Element>
        
        :return     <bool> success
        """
        self.setUpdatesEnabled(False)
        self.blockSignals(True)
        
        # restore order data
        headerState = unwrapVariant(settings.value('headerState'))
        if headerState is not None:
            state = QtCore.QByteArray.fromBase64(str(headerState))
            self.header().restoreState(state)
        
        sortingEnabled = unwrapVariant(settings.value('sortingEnabled'))
        if sortingEnabled:
            sortColumn = unwrapVariant(settings.value('sortColumn', 0))
            sortOrder = QtCore.Qt.SortOrder(unwrapVariant(settings.value('sortOrder')))
            self.setSortingEnabled(sortingEnabled)
            self.sortByColumn(sortColumn, sortOrder)
        
        self.setUpdatesEnabled(True)
        self.blockSignals(False)

    def saveSettings(self, settings):
        """
        Saves the data for this tree to the inputed xml entry.
        
        :param      xml | <xml.etree.ElementTree.Element>
        
        :return     <bool> success
        """
        # save order data
        settings.setValue('headerState', wrapVariant(str(self.header().saveState().toBase64())))
        settings.setValue('sortColumn', wrapVariant(str(self.sortColumn())))
        settings.setValue('sortOrder', wrapVariant(str(int(self.sortOrder()))))
        settings.setValue('sortingEnabled', wrapVariant(str(self.isSortingEnabled())))
        
    def saveXml(self, xml):
        """
        Saves the data for this tree to the inputed xml entry.
        
        :param      xml | <xml.etree.ElementTree.Element>
        
        :return     <bool> success
        """
        if xml is None:
            return False
        
        # save order data
        xml.set('headerState', str(self.header().saveState().toBase64()))
        xml.set('sortColumn', str(self.sortColumn()))
        xml.set('sortOrder', str(int(self.sortOrder())))
        xml.set('sortingEnabled', str(self.isSortingEnabled()))
        
        return True
    
    def setArrowStyle( self, state ):
        """
        Sets whether or not to use arrows for the grouping mechanism.
        
        :param      state | <bool>
        """
        self._arrowStyle = state
        
        if not state:
            self.setStyleSheet('')
        else:
            right = resources.find('img/treeview/triangle_right.png')
            down  = resources.find('img/treeview/triangle_down.png')
            opts  = (right.replace('\\', '/'), down.replace('\\', '/'))
            self.setStyleSheet(ARROW_STYLESHEET % opts)
    
    def setColumns(self, columns):
        """
        Sets the column count and list of columns to the inputed column list.
        
        :param      columns | [<str>, ..]
        """
        self.setColumnCount(len(columns))
        self.setHeaderLabels(columns)
    
    def setColumnEditingEnabled(self, column, state=True):
        """
        Sets whether or not the given column for this item should be editable.
        
        :param      column | <int>
                    state  | <bool>
        """
        self._columnEditing[column] = state
    
    def setDataCollector( self, collector ):
        """
        Sets the method that will be used to collect mime data for dragging \
        items from this tree.
        
        :warning    The data collector is stored as a weak-reference, so using \
                    mutable methods will not be stored well.  Things like \
                    instancemethods will not hold their pointer after they \
                    leave the scope that is being used.  Instead, use a \
                    classmethod or staticmethod to define the collector.
        
        :param      collector | <function> || <method> || None
        """
        if ( collector ):
            self._dataCollectorRef = weakref.ref(collector)
        else:
            self._dataCollectorRef = None
    
    def setDefaultItemHeight(self, height):
        """
        Sets the default item height for this instance.
        
        :param      height | <int>
        """
        self._defaultItemHeight = height
    
    def setDragMultiPixmap( self, pixmap ):
        """
        Returns the pixmap used to show multiple items dragged.
        
        :param      pixmap | <QtGui.QPixmap>
        """
        self._dragMultiPixmap = pixmap
    
    def setDragSinglePixmap( self, pixmap ):
        """
        Returns the pixmap used to show single items dragged.
        
        :param     pixmap | <QtGui.QPixmap>
        """
        self._dragSinglePixmap = pixmap
    
    def setDragDropFilter( self, ddFilter ):
        """
        Sets the drag drop filter for this widget.
        
        :warning    The dragdropfilter is stored as a weak-reference, so using \
                    mutable methods will not be stored well.  Things like \
                    instancemethods will not hold their pointer after they \
                    leave the scope that is being used.  Instead, use a \
                    classmethod or staticmethod to define the dragdropfilter.
        
        :param      ddFilter | <function> || <method> || None
        """
        if ddFilter:
            self._dragDropFilterRef = weakref.ref(ddFilter)
        else:
            self._dragDropFilterRef = None
    
    def setEditable( self, state ):
        """
        Sets the editable state for this instance.
        
        :param      state | <bool>
        """
        self._editable = state
        
        if not state:
            self.setEditTriggers(QtGui.QTreeWidget.NoEditTriggers)
        else:
            triggers  = QtGui.QTreeWidget.DoubleClicked
            triggers |= QtGui.QTreeWidget.AnyKeyPressed
            triggers |= QtGui.QTreeWidget.EditKeyPressed
            triggers |= QtGui.QTreeWidget.SelectedClicked
            
            self.setEditTriggers(triggers)
    
    def setExtendsTree( self, state ):
        """
        Set whether or not this delegate should render its row line through \
        the tree area.
        
        :return     <state>
        """
        delegate = self.itemDelegate()
        if ( isinstance(delegate, XTreeWidgetDelegate) ):
            delegate.setExtendsTree(state)
    
    def setFilteredColumns( self, columns ):
        """
        Sets the columns that will be used for filtering of this tree's items.
        
        :param      columns | [<int>, ..]
        """
        self._filteredColumns = columns
    
    def setGridPen( self, gridPen ):
        """
        Sets the pen that will be used when drawing the grid lines.
        
        :param      gridPen | <QtGui.QPen> || <QtGui.QColor>
        """
        delegate = self.itemDelegate()
        if ( isinstance(delegate, XTreeWidgetDelegate) ):
            delegate.setGridPen(gridPen)
    
    def setColumnHidden( self, column, state ):
        """
        Sets the hidden state for the inputed column.
        
        :param      column | <int>
                    state  | <bool>
        """
        super(XTreeWidget, self).setColumnHidden(column, state)
        
        if ( not self.signalsBlocked() ):
            self.columnHiddenChanged.emit(column, state)
            self.executeDelayedItemsLayout()
    
    def setHeaderMenu(self, menu):
        """
        Sets the menu to be displayed for this tree's header menu request.
        
        :return     menu | <QtGui.QMenu> || None
        """
        self._headerMenu = menu
    
    def setHoverBackground( self, brush ):
        """
        Sets the default hover background for this tree widget.
        
        :param      brush | <QtGui.QBrush> || None
        """
        self._hoverBackground = QtGui.QBrush(brush)
        
    def setHoverForeground( self, brush ):
        """
        Sets the default hover foreground for this tree widget.
        
        :param      brush | <QtGui.QBrush> || None
        """
        self._hoverForeground = QtGui.QBrush(brush)
    
    def setHoverMode( self, mode ):
        """
        Sets the hover mode for this tree widget.
        
        :param      mode | <XTreeWidget.HoverMode>
        """
        self._hoverMode = mode
    
    def setHiddenColumns(self, hidden):
        """
        Sets the columns that should be hidden based on the inputed list of \
        names.
        
        :param      columns | [<str>, ..]
        """
        colnames = self.columns()
        for c, column in enumerate(colnames):
            self.setColumnHidden(c, column in hidden)
    
    def setHint( self, hint ):
        """
        Sets the hint text that will be rendered when no items are present.
        
        :param      hint | <str>
        """
        self._hint = hint
    
    def setHintColor( self, color ):
        """
        Sets the color used for the hint rendering.
        
        :param      color | <QtGui.QColor>
        """
        self._hintColor = color
    
    def setMaximumFilterLevel( self, level ):
        """
        Sets the maximum level from which the filtering of this tree's \
        items should finish.
        
        :param     level | <int> || None
        """
        self._maximumFilterLevel = level
    
    def setResizeToContentsInteractive(self, state=True):
        self._resizeToContentsInteractive = state
        if state:
            self.header().setResizeMode(self.header().ResizeToContents)
    
    def setShowGrid( self, state ):
        """
        Sets whether or not this delegate should draw its grid lines.
        
        :param      state | <bool>
        """
        delegate = self.itemDelegate()
        if ( isinstance(delegate, XTreeWidgetDelegate) ):
            delegate.setShowGrid(state)
    
    def setShowGridColumns( self, state ):
        """
        Sets whether or not columns should be rendered when drawing the grid.
        
        :param      state | <bool>
        """
        delegate = self.itemDelegate()
        if ( isinstance(delegate, XTreeWidgetDelegate) ):
            delegate.setShowGridColumns(state)
    
    def setShowGridRows( self, state ):
        """
        Sets whether or not the grid rows should be rendered when drawing the \
        grid.
        
        :param      state | <bool>
        """
        delegate = self.itemDelegate()
        if ( isinstance(delegate, XTreeWidgetDelegate) ):
            delegate.setShowGridRows(state)
    
    def setShowHighlights(self, state):
        """
        Sets whether or not to displa the highlighted color scheme for
        the items in this widget.
        
        :param      state | <bool>
        """
        self.itemDelegate().setShowHighlights(state)
    
    def setShowRichText( self, state ):
        """
        Sets whether or not the delegate should render rich text information \
        as HTML when drawing the contents of the item.
        
        :param      state | <bool>
        """
        delegate = self.itemDelegate()
        if isinstance(delegate, XTreeWidgetDelegate):
            delegate.setShowRichText(state)
    
    def setVisibleColumns(self, visible):
        """
        Sets the list of visible columns for this widget.  This method will
        take any column in this tree's list NOT found within the inputed column
        list and hide them.
        
        :param      columns | [<str>, ..]
        """
        colnames = self.columns()
        for c, column in enumerate(colnames):
            self.setColumnHidden(c, column not in visible)
    
    def setUseDragPixmaps( self, state ):
        """
        Returns whether or not to use the drag pixmaps when dragging.
        
        :param     state | <bool>
        """
        self._useDragPixmaps = state
    
    def setUsePopupToolTip( self, state ):
        """
        Sets whether or not the XPopupWidget should be used when displaying 
        a tool tip vs. the standard tooltip.
        
        :param      state | <bool>
        """
        self._usePopupToolTip = state
    
    def showGrid( self ):
        """
        Returns whether or not this delegate should draw its grid lines.
        
        :return     <bool>
        """
        delegate = self.itemDelegate()
        if ( isinstance(delegate, XTreeWidgetDelegate) ):
            return delegate.showGrid()
        return False
    
    def showGridColumns( self ):
        """
        Returns whether or not this delegate should draw columns when \
        rendering the grid.
        
        :return     <bool>
        """
        delegate = self.itemDelegate()
        if ( isinstance(delegate, XTreeWidgetDelegate) ):
            return delegate.showGridColumns()
        return False
    
    def showGridRows( self ):
        """
        Returns whether or not this delegate should draw rows when rendering \
        the grid.
        
        :return     <bool>
        """
        delegate = self.itemDelegate()
        if ( isinstance(delegate, XTreeWidgetDelegate) ):
            return delegate.showGridRows()
        return None
    
    def showHeaderMenu( self, pos):
        """
        Displays the header menu for this tree widget.
        
        :param      pos | <QtCore.QPoint> || None
        """
        header = self.header()
        index  = header.logicalIndexAt(pos)
        self._headerIndex = index
        
        # show a pre-set menu
        if self._headerMenu:
            menu = self._headerMenu
        else:
            menu = self.createHeaderMenu(index)
        
        # determine the point to show the menu from
        if pos is not None:
            point = header.mapToGlobal(pos)
        else:
            point = QtGui.QCursor.pos()
        
        self.headerMenuAboutToShow.emit(menu, index)
        menu.exec_(point)
    
    def showHighlights(self):
        """
        Returns whether or not to displa the highlighted color scheme for
        the items in this widget.
        
        :return     <bool>
        """
        return self.itemDelegate().showHighlights()
    
    def showRichText( self ):
        """
        Returns whether or not the tree is holding richtext information and \
        should render HTML when drawing the data.
        
        :return     <bool>
        """
        delegate = self.itemDelegate()
        if ( isinstance(delegate, XTreeWidgetDelegate) ):
            return delegate.showRichText()
        return None
    
    def smartResizeColumnsToContents( self ):
        """
        Resizes the columns to the contents based on the user preferences.
        """
        self.blockSignals(True)
        self.setUpdatesEnabled(False)
        
        header = self.header()
        header.blockSignals(True)
        
        columns = range(self.columnCount())
        sizes = [self.columnWidth(c) for c in columns]
        header.resizeSections(header.ResizeToContents)
        
        for col in columns:
            width = self.columnWidth(col)
            if ( width < sizes[col] ):
                self.setColumnWidth(col, sizes[col])
        
        header.blockSignals(False)
        
        self.setUpdatesEnabled(True)
        self.blockSignals(False)
    
    def sortByColumn(self, column, order=QtCore.Qt.AscendingOrder):
        """
        Overloads the default sortByColumn to record the order for later \
        reference.
        
        :param      column | <int>
                    order  | <QtCore.Qt.SortOrder>
        """
        super(XTreeWidget, self).sortByColumn(column, order)
        self._sortOrder = order
    
    def sortByColumnName(self, name, order=QtCore.Qt.AscendingOrder):
        """
        Sorts the tree by the inputed column name's index and the given order.
        
        :param      name    | <str>
                    order   | <QtCore.Qt.SortOrder>
        """
        self.setSortingEnabled(True)
        self.sortByColumn(self.column(name), order)
    
    def sortOrder( self ):
        """
        Returns the sort order used by this tree widget.
        
        :return     <QtCore.Qt.SortOrder>
        """
        return self._sortOrder
    
    def startDrag( self, supportedActions ):
        """
        Starts a new drag event for this tree widget.  Overloading from the
        default QTreeWidget class to define a better pixmap option when
        dragging many items.
        
        :param      supportedActions | <QtCore.Qt.DragActions>
        """
        if ( not self.useDragPixmaps() ):
            return super(XTreeWidget, self).startDrag(supportedActions)
        
        filt  = lambda x: x.flags() & QtCore.Qt.ItemIsDragEnabled
        items = filter(filt, self.selectedItems())
        if ( not items ):
            return
        
        data = self.mimeData(items)
        if ( not data ):
            return
        
        if ( len(items) > 1 ):
            pixmap = self.dragMultiPixmap()
        else:
            pixmap = self.dragSinglePixmap()
        
        # create the drag event
        drag = QtGui.QDrag(self)
        drag.setMimeData(data)
        drag.setPixmap(pixmap)
        
        drag.exec_(supportedActions, QtCore.Qt.MoveAction)
    
    def toggleColumnByAction( self, action ):
        """
        Toggles whether or not the column at the inputed action's name should \
        be hidden.
        `
        :param      action | <QAction>
        """
        if ( action.text() == 'Show All' ):
            self.blockSignals(True)
            self.setUpdatesEnabled(False)
            for col in range(self.columnCount()):
                self.setColumnHidden(col, False)
            self.setUpdatesEnabled(True)
            self.blockSignals(False)
            
            self.setColumnHidden(0, False)
            
        elif ( action.text() == 'Hide All' ):
            self.blockSignals(True)
            self.setUpdatesEnabled(False)
            for col in range(self.columnCount()):
                self.setColumnHidden(col, True)
                
            # ensure we have at least 1 column visible
            self.blockSignals(False)
            self.setUpdatesEnabled(True)
            
            self.setColumnHidden(0, False)
            
        else:
            col     = self.column(action.text())
            state   = not action.isChecked()
            self.setColumnHidden(col, state)
            if ( state ):
                self.resizeColumnToContents(col)
            
            # ensure we at least have 1 column visible
            found = False
            for col in range(self.columnCount()):
                if ( not self.isColumnHidden(col) ):
                    found = True
                    break
            
            if not found:
                self.setColumnHidden(0, False)
        
        self.resizeToContents()
        self.update()
    
    def topLevelItems(self):
        """
        Returns the list of top level nodes for this tree.
        
        :return     [<QtGui.QTreeWidgetItem>, ..]
        """
        try:
            for i in xrange(self.topLevelItemCount()):
                yield self.topLevelItem(i)
        except RuntimeError:
            # can be raised when iterating on a deleted tree widget.
            return
    
    def traverseItems(self,
                      mode=TraverseMode.DepthFirst,
                      parent=None):
        """
        Generates a tree iterator that will traverse the items of this tree
        in either a depth-first or breadth-first fashion.
        
        :param      mode | <XTreeWidget.TraverseMode>
                    recurse | <bool>
        
        :return     <generator>
        """
        try:
            if parent:
                count = parent.childCount()
                func = parent.child
            else:
                count = self.topLevelItemCount()
                func = self.topLevelItem
        except RuntimeError:
            # can be raised when iterating on a deleted tree widget.
            return
        
        next = []
        for i in range(count):
            try:
                item = func(i)
            except RuntimeError:
                # can be raised when iterating on a deleted tree widget
                return
            else:
                yield item
                if mode == XTreeWidget.TraverseMode.DepthFirst:
                    for child in self.traverseItems(mode, item):
                        yield child
                else:
                    next.append(item)
        
        for item in next:
            for child in self.traverseItems(mode, item):
                yield child

    def useDragPixmaps( self ):
        """
        Returns whether or not to use the drag pixmaps when dragging.
        
        :return     <bool>
        """
        return self._useDragPixmaps
    
    def usePopupToolTip( self ):
        """
        Returns whether or not the tooltips should be the standard one or
        the XPopupWidget.
        
        :return     <bool>
        """
        return self._usePopupToolTip
    
    def visibleColumns(self):
        """
        Returns a list of the visible column names for this widget.
        
        :return     [<str>, ..]
        """
        return [self.columnOf(c) for c in range(self.columnCount()) \
                if not self.isColumnHidden(c)]
    
    def visibleTopLevelItemCount(self):
        """
        Returns the number of visible top level items.
        
        :return     <int>
        """
        return sum(int(not item.isHidden()) for item in self.topLevelItems())
    
    def visualRect(self, index):
        """
        Returns the visual rectangle for the inputed index.
        
        :param      index | <QModelIndex>
        
        :return     <QtCore.QRect>
        """
        rect = super(XTreeWidget, self).visualRect(index)
        item = self.itemFromIndex(index)
        if not rect.isNull() and item and item.isFirstColumnSpanned():
            vpos = self.viewport().mapFromParent(QtCore.QPoint(0, 0))
            rect.setX(vpos.x())
            rect.setWidth(self.width())
            return rect
        return rect
    
    # define Qt properties
    x_arrowStyle        = Property(bool, isArrowStyle, setArrowStyle)
    x_defaultItemHeight = Property(int,  defaultItemHeight, setDefaultItemHeight)
    x_hint              = Property(str,  hint, setHint)
    x_showGrid          = Property(bool, showGrid, setShowGrid)
    x_showGridRows      = Property(bool, showGridRows, setShowGridRows)
    x_showRichText      = Property(bool, showRichText, setShowRichText)
    x_editable          = Property(bool, isEditable, setEditable)
    x_extendsTree       = Property(bool, extendsTree,  setExtendsTree)
    x_useDragPixmaps    = Property(bool, useDragPixmaps, setUseDragPixmaps)
    x_usePopupToolTip   = Property(bool, 
                                       usePopupToolTip, 
                                       setUsePopupToolTip)
    x_showGridColumns   = Property(bool, 
                                       showGridColumns, 
                                       setShowGridColumns)
    x_showHighlights    = Property(bool, showHighlights, setShowHighlights)

    x_resizeToContentsInteractive = Property(bool,
                                             isResizeToContentsInteractive,
                                             setResizeToContentsInteractive)
    x_maximumFilterLevel = Property(int, 
                                        maximumFilterLevel, 
                                        setMaximumFilterLevel)

# define the designer properties
__designer_plugins__ = [XTreeWidget]
