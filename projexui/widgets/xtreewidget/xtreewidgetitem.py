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

from xqt import QtGui, QtCore, unwrapVariant, wrapVariant

import projex.sorting
import projex.text
from projex.text import nativestring

from projexui import resources

class XTreeWidgetItem(QtGui.QTreeWidgetItem):
    SortRole        = QtCore.Qt.ItemDataRole(128)
    HintRole        = QtCore.Qt.ItemDataRole(129)
    ItemIsHoverable   = QtCore.Qt.ItemFlags(16777216)
    ItemIsExpandable  = QtCore.Qt.ItemFlags(16777217)
    ItemIsCollapsible = QtCore.Qt.ItemFlags(16777218)
    
    def __lt__(self, other):
        # make sure we're comparing apples to apples
        if not isinstance(other, QtGui.QTreeWidgetItem):
            return 0
            
        tree = self.treeWidget()
        if not tree:
            return 0
        
        col = tree.sortColumn()
        
        # compare sorting data
        mdata = unwrapVariant(self.data(col, self.SortRole))
        odata = unwrapVariant(other.data(col, self.SortRole))
        
        # compare editing data
        if mdata is None or odata is None:
            mdata = unwrapVariant(self.data(col, QtCore.Qt.EditRole))
            odata = unwrapVariant(other.data(col, QtCore.Qt.EditRole))
        
        if type(mdata) == type(odata) and not type(mdata) in (str, unicode):
            return mdata < odata
        
        # compare display data by natural sorting mechanisms on a string
        mdata = nativestring(self.text(col))
        odata = nativestring(other.text(col))
        
        return projex.sorting.natural(mdata, odata) == -1
    
    def __eq__(self, other):
        return id(self) == id(other)
    
    def __ne__(self, other):
        return id(self) != id(other)
    
    def __init__(self, *args):
        super(XTreeWidgetItem, self).__init__(*args)
        
        # sets the overlay information per column for this item
        self._iconOverlays      = {}
        self._hoverBackground   = {}
        self._hoverIcon         = {}
        self._hoverForeground   = {}
        self._expandedIcon      = {}
        self._dragData          = {}
        self._columnEditing     = {}
        self._movies            = {}
        self._fixedHeight       = 0
        
        # set whether or not the tree widget is editable
        flags = self.flags()
        flags |= QtCore.Qt.ItemIsEditable
        flags |= self.ItemIsExpandable
        flags |= self.ItemIsCollapsible
        flags &= ~QtCore.Qt.ItemIsDropEnabled
        self.setFlags(flags)
        
        tree = self.treeWidget()
        if tree:
            try:
                height = tree.defaultItemHeight()
            except StandardError:
                height = 0
            
            if height:
                self.setFixedHeight(height)
    
    def _updateFrame(self):
        """
        Updates the frame for the given sender.
        """
        for col, mov in self._movies.items():
            self.setIcon(col, QtGui.QIcon(mov.currentPixmap()))
    
    def adjustHeight(self, column):
        """
        Adjusts the height for this item based on the columna and its text.
        
        :param      column | <int>
        """
        tree = self.treeWidget()
        if not tree:
            return
        
        w = tree.width()
        if tree.verticalScrollBar().isVisible():
            w -= tree.verticalScrollBar().width()
        
        doc = QtGui.QTextDocument()
        doc.setTextWidth(w)
        doc.setHtml(self.text(0))
        height = doc.documentLayout().documentSize().height()
        self.setFixedHeight(height+2)
    
    def destroy(self):
        """
        Destroyes this item by disconnecting any signals that may exist.  This
        is called when the tree clears itself or is deleted.  If you are
        manually removing an item, you should call the destroy method yourself.
        This is required since Python allows for non-QObject connections, and
        since QTreeWidgetItem's are not QObjects', they do not properly handle
        being destroyed with connections on them.
        """
        try:
            tree = self.treeWidget()
            tree.destroyed.disconnect(self.destroy)
        except StandardError:
            pass
        
        for movie in set(self._movies.values()):
            try:
                movie.frameChanged.disconnect(self._updateFrame)
            except StandardError:
                pass
    
    def children(self, recursive=False):
        """
        Returns the list of child nodes for this item.
        
        :return     [<QtGui.QTreeWidgetItem>, ..]
        """
        for i in xrange(self.childCount()):
            child = self.child(i)
            yield child
            
            if recursive:
                for subchild in child.children(recursive=True):
                    yield subchild
    
    def dragData(self, format=None, default=None):
        """
        Returns the drag information that is associated with this tree
        widget item for the given format.
        
        :param      format | <str>
        
        :return     <variant>
        """
        if format is None:
            return self._dragData
        return self._dragData.get(nativestring(format), default)
    
    def ensureVisible(self):
        """
        Expands all the parents of this item to ensure that it is visible
        to the user.
        """
        parent = self.parent()
        while parent:
            parent.setExpanded(True)
            parent = parent.parent()
    
    def expandedIcon( self, column ):
        """
        Returns the icon to be used when the item is expanded.
        
        :param      column | <int>
        
        :return     <QtGui.QIcon> || None
        """
        return self._expandedIcon.get(column)
    
    def fixedHeight(self):
        """
        Returns the fixed height for this treewidget item.
        
        :return     <int>
        """
        return self._fixedHeight
    
    def hoverBackground( self, column, default = None ):
        """
        Returns the brush to use when coloring when the user hovers over
        the item for the given column.
        
        :param      column | <int>
        
        :return     <QtGui.QBrush> || None
        """
        return self._hoverBackground.get(column, default)
    
    def hoverIcon( self, column ):
        """
        Returns the icon to use when coloring when the user hovers over
        the item for the given column.
        
        :param      column | <int>
        
        :return     <QtGui.QIcon> || None
        """
        return self._hoverIcon.get(column)
    
    def hoverForeground( self, column, default = None ):
        """
        Returns the brush to use when coloring when the user hovers over
        the item for the given column.
        
        :param      column | <int>
        
        :return     <QtGui.QBrush> || None
        """
        return self._hoverForeground.get(column, default)
    
    def iconOverlay(self, column):
        """
        Returns the icon overlay for the given column.
        
        :return     <QtGui.QIcon> || None
        """
        return self._iconOverlays.get(column)
    
    def initGroupStyle(self, useIcons=True, columnCount=None):
        """
        Initialzes this item with a grouping style option.
        """
        flags      = self.flags()
        if flags & QtCore.Qt.ItemIsSelectable:
            flags ^= QtCore.Qt.ItemIsSelectable
            self.setFlags(flags)
        
        if useIcons:
            ico        = QtGui.QIcon(resources.find('img/treeview/triangle_right.png'))
            expand_ico = QtGui.QIcon(resources.find('img/treeview/triangle_down.png'))
            
            self.setIcon(0, ico)
            self.setExpandedIcon(0, expand_ico)
        
        palette = QtGui.QApplication.palette()
        
        line_clr = palette.color(palette.Mid)
        base_clr = palette.color(palette.Button)
        text_clr = palette.color(palette.ButtonText)
        
        gradient = QtGui.QLinearGradient()
        
        gradient.setColorAt(0.00, line_clr)
        gradient.setColorAt(0.03, line_clr)
        gradient.setColorAt(0.04, base_clr.lighter(105))
        gradient.setColorAt(0.25, base_clr)
        gradient.setColorAt(0.96, base_clr.darker(105))
        gradient.setColorAt(0.97, line_clr)
        gradient.setColorAt(1.00, line_clr)
        
        h = self._fixedHeight
        if not h:
            h = self.sizeHint(0).height()
        if not h:
            h = 18
        
        gradient.setStart(0.0, 0.0)
        gradient.setFinalStop(0.0, h)
        
        brush = QtGui.QBrush(gradient)
        
        tree = self.treeWidget()
        columnCount = columnCount or (tree.columnCount() if tree else self.columnCount())

        for i in range(columnCount):
            self.setForeground(i, text_clr)
            self.setBackground(i, brush)
    
    def isChecked(self, column):
        """
        Returns whether or not this item is checked for the given column.
        This is a convenience method on top of the checkState method.
        
        :return     <bool>
        """
        return self.checkState(column) == QtCore.Qt.Checked
    
    def isColumnEditingEnabled(self, column):
        """
        Sets whether or not the given column for this item should be editable.
        
        :param      column | <int>
        
        :return     <bool>
        """
        return self._columnEditing.get(column, True)
    
    def movie(self, column):
        """
        Returns the movie at the given column.
        
        :return     <QtGui.QMovie> || None
        """
        return self._movies.get(column)

    def requireCleanup(self):
        """
        If you intend to use any signal/slot connections on this QTreeWidgetItem, you will need
        to call the requireCleanup method and implement manual disconnections in the destroy method.

        QTreeWidgetItem's do not inherit from QObject, and as such do not utilize the memory cleanup
        associated with QObject connections.
        """
        try:
            tree.destroyed.connect(self.destroy, QtCore.Qt.UniqueConnection)
        except StandardError:
            pass

    def setColumnEditingEnabled(self, column, state=True):
        """
        Sets whether or not the given column for this item should be editable.
        
        :param      column | <int>
                    state  | <bool>
        """
        self._columnEditing[column] = state
    
    def setChecked(self, column, state):
        """
        Sets the check state of the inputed column based on the given bool
        state.  This is a convenience method on top of the setCheckState
        method.
        
        :param      column | <int>
                    state  | <bool>
        """
        self.setCheckState(column, QtCore.Qt.Checked if state else QtCore.Qt.Unchecked)
    
    def setDragData(self, format, value):
        """
        Sets the drag information that is associated with this tree
        widget item for the given format.
        
        :param      format | <str>
                    value  | <variant>
        """
        if value is None:
            self._dragData.pop(nativestring(format), None)
        else:
            self._dragData[nativestring(format)] = value
    
    def setExpanded(self, state):
        """
        Sets whether or not this item is in an expanded state.
        
        :param      state | <bool>
        """
        if (state and self.testFlag(self.ItemIsExpandable)) or \
           (not state and self.testFlag(self.ItemIsCollapsible)):
            super(XTreeWidgetItem, self).setExpanded(state)
    
    def setExpandedIcon( self, column, icon ):
        """
        Sets the icon to be used when the item is expanded.
        
        :param      column | <int>
                    icon   | <QtGui.QIcon> || None
        """
        self._expandedIcon[column] = QtGui.QIcon(icon)
    
    def setFlag(self, flag, state=True):
        """
        Sets whether or not the inputed flag is associated with this item.
        
        :param      flag  | <QtCore.Qt.ItemFlags>
                    state | <bool>
        """
        if state:
            self.setFlags(self.flags() | flag)
        else:
            self.setFlags(self.flags() & ~flag)
    
    def setFixedHeight(self, height):
        """
        Sets the fixed height for this item to the inputed height.
        
        :param      height | <int>
        """
        self._fixedHeight = height
    
    def setHtml(self, column, html):
        """
        Creates a label with the given HTML for this item and column.  This
        method requires the item to be a part of the tree.
        
        :param      column | <int>
                    html   | <unicode>
        
        :return     <bool> | success
        """
        tree = self.treeWidget()
        if not tree:
            return False
        
        lbl = tree.itemWidget(self, column)
        if not html and lbl:
            lbl.deleteLater()
            return True
        
        elif not lbl:
            lbl = QtGui.QLabel(tree)
            lbl.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
            lbl.setOpenExternalLinks(True)
            tree.setItemWidget(self, column, lbl)
        
        lbl.setText(html)
        return True
    
    def setHoverBackground( self, column, brush ):
        """
        Returns the brush to use when coloring when the user hovers over
        the item for the given column.
        
        :param      column | <int>
                    brush  | <QtGui.QBrush)
        """
        self._hoverBackground[column] = QtGui.QBrush(brush)
    
    def setHoverIcon( self, column, icon ):
        """
        Returns the icon to use when coloring when the user hovers over
        the item for the given column.
        
        :param      column | <int>
                    icon   | <QtGui.QIcon)
        """
        self._hoverIcon[column] = QtGui.QIcon(icon)
    
    def setHoverForeground( self, column, brush ):
        """
        Returns the brush to use when coloring when the user hovers over
        the item for the given column.
        
        :param      column | <int>
                    brush  | <QtGui.QBrush>
        """
        self._hoverForeground[column] = QtGui.QBrush(brush)
    
    def setIconOverlay(self, column, icon):
        """
        Sets the icon overlay for this item at the inputed column to the
        given icon.
        
        :param      column | <int>
                    icon   | <str> || <QtGui.QIcon>
        """
        self._iconOverlays[column] = QtGui.QIcon(icon)
    
    def setMovie(self, column, movie):
        """
        Sets the movie that will play for the given column.
        
        :param      column | <int>
                    movie  | <QtGui.QMovie> || None
        """
        curr = self._movies.get(column)
        if curr == movie:
            return True
        else:
            try:
                curr.frameChanged.disconnect(self._updateFrame)
            except StandardError:
                pass
        
        if movie is not None:
            self.requireCleanup()

            self._movies[column] = movie
            self.setIcon(column, QtGui.QIcon(movie.currentPixmap()))
            
            try:
                movie.frameChanged.connect(self._updateFrame,
                                           QtCore.Qt.UniqueConnection)
            except StandardError:
                pass
        else:
            self._movies.pop(column, None)
    
    def setSizeHint(self, column, hint):
        """
        Sets the size hint for this item to the inputed size.  This will also
        updated the fixed height property if the hieght of the inputed hint
        is larger than the current fixed height.
        
        :param      hint | <QtCore.QSize>
        """
        self._fixedHeight = max(hint.height(), self._fixedHeight)
        super(XTreeWidgetItem, self).setSizeHint(column, hint)
    
    def setSortData( self, column, data ):
        """
        Sets the sorting information for the inputed column to the given data.
        
        :param      column | <int>
                    data   | <variant>
        """
        self.setData(column, self.SortRole, wrapVariant(data))
    
    def sizeHint(self, column):
        """
        Returns the size hint for this column.  This will return the width
        for the given column, with the maximum height assigned with this item.
        
        :return     <QtCore.QSize>
        """
        hint = super(XTreeWidgetItem, self).sizeHint(column)
        hint.setHeight(max(hint.height(), self.fixedHeight()))
        return hint
    
    def sortData( self, column ):
        """
        Returns the data to be used when sorting.  If no sort data has been
        explicitly defined, then the value in the EditRole for this item's
        column will be used.
        
        :param      column | <int>
        
        :return     <variant>
        """
        value = unwrapVariant(self.data(column, self.SortRole))
        if value is None:
            return None
        return unwrapVariant(self.data(column, QtCore.Qt.EditRole))
    
    def takeFromTree(self):
        """
        Takes this item from the tree.
        """
        tree = self.treeWidget()
        parent = self.parent()
        
        if parent:
            parent.takeChild(parent.indexOfChild(self))
        else:
            tree.takeTopLevelItem(tree.indexOfTopLevelItem(self))

    def testFlag(self, flags):
        """
        Tests whether or not this item has the given flag.
        
        :param      flags | <QtCore.Qt.ItemFlags>
        
        :return     <bool>
        """
        return bool(self.flags() & flags)
