""" Defines a multi-taggable widget object, like a magnet board. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software, LLC'
__license__         = 'LGPL'

__maintainer__      = 'Projex Software, LLC'
__email__           = 'team@projexsoftware.com'

import projexui
from projex.text import nativestring
from projexui.qt import Signal, Slot, Property
from projexui.qt.QtCore import QSize,\
                               Qt,\
                               QMimeData

from projexui.qt.QtGui import QListWidgetItem,\
                              QItemDelegate,\
                              QFontMetrics,\
                              QPixmap,\
                              QLineEdit,\
                              QCompleter,\
                              QColor,\
                              QApplication

from projexui import resources
from projexui.widgets.xlistwidget import XListWidget

#------------------------------------------------------------------------------

class XMultiTagItem(QListWidgetItem):
    def __eq__(self, other):
        return id(self) == id(other)
    
    def __init__( self, text, parent ):
        super(XMultiTagItem, self).__init__(text)
        
        # set default properties
        self.setText(text)
        self.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setFlags(self.flags() | Qt.ItemIsEditable)
        
        palette = parent.palette()
        self.setForeground(palette.color(palette.ButtonText))
    
    def setText( self, text ):
        """
        Sets the text for this item and resizes it to fit the text and the
        remove button.
        
        :param      text | <str>
        """
        super(XMultiTagItem, self).setText(text)
        
        metrics = QFontMetrics(self.font())
        
        hint = QSize(metrics.width(text) + 24, 18)
        self.setSizeHint(hint)

#------------------------------------------------------------------------------

class XMultiTagCreateItem(QListWidgetItem):
    def __eq__(self, other):
        return id(self) == id(other)
    
    def __init__( self, parent ):
        super(XMultiTagCreateItem, self).__init__()
        
        self.setFlags( Qt.ItemIsEnabled | Qt.ItemIsEditable )
        self.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setSizeHint(QSize(100, 18))

#------------------------------------------------------------------------------

class XMultiTagDelegate(QItemDelegate):
    def createEditor( self, parent, option, index ):
        """
        Overloads the create editor method to assign the parent's completer to
        any line edit created.
        
        :param      parent | <QWidget>
                    option | <QStyleOption>
                    index  | <QModelIndex>
        
        :return     <QWidget> || None
        """
        multi_tag = projexui.ancestor(self, XMultiTagEdit)
        
        edit = QLineEdit(parent)
        edit.setFrame(False)
        edit.setCompleter(multi_tag.completer())
        edit.installEventFilter(multi_tag)
        
        return edit

    def drawDisplay( self, painter, option, rect, text ):
        """
        Handles the display drawing for this delegate.
        
        :param      painter | <QPainter>
                    option  | <QStyleOption>
                    rect    | <QRect>
                    text    | <str>
        """
        painter.setBrush(Qt.NoBrush)
        painter.drawText(rect.left() + 3,
                         rect.top(),
                         rect.width() - 3,
                         rect.height(), 
                         option.displayAlignment, 
                         text)

    def paint( self, painter, option, index ):
        """
        Overloads the paint method from Qt to perform some additional painting
        on items.
        
        :param      painter | <QPainter>
                    option  | <QStyleOption>
                    index   | <QModelIndex>
        """
        # draw the background
        edit = self.parent()
        item = edit.item(index.row())
        if ( not isinstance(item, XMultiTagCreateItem) ):
            if ( item.isSelected() ):
                painter.setBrush(edit.highlightColor())
            else:
                painter.setBrush(edit.tagColor())
            
            painter.drawRect(option.rect)
        
        painter.setBrush(Qt.NoBrush)
        painter.setPen(item.foreground().color())
        
        super(XMultiTagDelegate, self).paint(painter, option, index)
        
        # draw the border
        item = self.parent().item(index.row())
        if ( not isinstance(item, XMultiTagCreateItem) ):
            painter.setPen(edit.borderColor())
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(option.rect)
            painter.drawText(option.rect.right() - 14,
                             option.rect.top() + 1,
                             16,
                             16,
                             Qt.AlignCenter,
                             'x')

    def setModelData(self, editor, model, index):
        super(XMultiTagDelegate, self).setModelData(editor, model, index)
        
        multi_tag = projexui.ancestor(editor, XMultiTagEdit)
        multi_tag.setFocus()

#------------------------------------------------------------------------------

class XMultiTagEdit(XListWidget):
    tagCreated = Signal(str)
    tagRemoved = Signal(str)
    
    __designer_icon__ = resources.find('img/ui/tags.png')
    
    def __init__( self, parent = None ):
        super(XMultiTagEdit, self).__init__(parent)
        
        # define custom properties
        self._createItem     = None
        self._completer      = None
        self._itemsRemovable = True
        self._unique         = True
        self._highlightColor = QColor(181, 209, 244)
        self._tagColor       = QColor(181, 209, 244, 50)
        self._borderColor    = QColor(150, 178, 213)
        self._options        = None
        self._insertAllowed  = False
        self._editable       = True
        
        # make sure the highlighting works
        palette = self.palette()
        palette.setColor(palette.Highlight, self._highlightColor)
        self.setPalette(palette)
        
        # setup default options
        self.setItemDelegate(XMultiTagDelegate(self))
        self.setMinimumHeight(28)
        self.setMovement(XListWidget.Static)
        self.setResizeMode(XListWidget.Adjust)
        self.setDragDropMode(XListWidget.DragOnly) # handling drops internally
        self.setViewMode(XListWidget.IconMode)
        self.setEditTriggers(XListWidget.DoubleClicked | \
                             XListWidget.SelectedClicked | \
                             XListWidget.AnyKeyPressed )
        self.setSpacing(3)
        self.setAcceptDrops(True)
        self.clear()
        
        # track changes to items
        self.itemChanged.connect(self.handleTagChange)
    
    @Slot(str)
    def addTag( self, tag ):
        """
        Adds a new tag to the edit.
        
        :param      tag | <str>
        
        :return     <bool>
        """
        if ( not (tag and self.isTagValid(tag)) ):
            return False
        
        self.blockSignals(True)
        create_item = self.createItem()
        if create_item:
            self.insertItem(self.row(create_item), XMultiTagItem(tag, self))
            create_item.setText('')
        else:
            self.addItem(XMultiTagItem(tag, self))
        self.blockSignals(False)
        
        if ( not self.signalsBlocked() ):
            self.tagCreated.emit(tag)
        
        return False
    
    def borderColor( self ):
        """
        Returns the color used for the tag border.
        
        :return     <QColor>
        """
        return self._borderColor
    
    def clear( self ):
        """
        Clears the items for this edit.
        """
        super(XMultiTagEdit, self).clear()
        self._createItem = None
    
    def completer( self ):
        """
        Returns the completer instance linked with this edit.
        
        :return     <QCompleter> || None
        """
        return self._completer
    
    def copy( self ):
        """
        Copies the selected items to the clipboard.
        """
        text = []
        for item in self.selectedItems():
            text.append(nativestring(item.text()))
        
        QApplication.clipboard().setText(','.join(text))
    
    def createItem( self ):
        """
        Returns a reference to the create item that is used for this edit.
        
        :return     <XMultiTagCreateItem>
        """
        if not self.isEditable():
            return None
        
        if self._createItem is None:
            self.blockSignals(True)
            
            self._createItem = XMultiTagCreateItem(self)
            self.addItem(self._createItem)
            
            self.blockSignals(False)
        
        return self._createItem
    
    def dragEnterEvent( self, event ):
        """
        Handles the drag enter event.
        
        :param      event | <QDragEvent>
        """
        tags = nativestring(event.mimeData().text())
        
        if ( event.source() == self ):
            event.acceptProposedAction()
        elif ( tags ):
            event.acceptProposedAction()
        else:
            super(XMultiTagEdit, self).dragEnterEvent(event)
    
    def dragMoveEvent( self, event ):
        """
        Handles the drag move event.
        
        :param      event | <QDragEvent>
        """
        tags = nativestring(event.mimeData().text())
        
        if ( event.source() == self ):
            event.acceptProposedAction()
        elif ( tags ):
            event.acceptProposedAction()
        else:
            super(XMultiTagEdit, self).dragMoveEvent(event)
    
    def dropEvent( self, event ):
        """
        Handles the drop event.
        
        :param      event | <QDropEvent>
        """
        tags = nativestring(event.mimeData().text())
        
        # handle an internal move
        if event.source() == self:
            curr_item = self.selectedItems()[0]
            create_item = self.createItem()
            
            # don't allow moving of the creation item
            if curr_item == create_item:
                return
            
            targ_item = self.itemAt(event.pos())
            if not targ_item:
                targ_item = create_item
            
            curr_idx  = self.row(curr_item)
            targ_idx  = self.row(targ_item)
            if ( targ_idx == self.count() - 1 ):
                targ_idx -= 1
            
            # don't bother moving the same item
            if ( curr_idx == targ_idx ):
                return
            
            self.takeItem(self.row(curr_item))
            self.insertItem(targ_idx, curr_item)
            self.setCurrentItem(curr_item)
        
        elif ( tags ):
            for tag in tags.split(','):
                tag = tag.strip()
                if ( self.isTagValid(tag) ):
                    self.addTag(tag)
            
        else:
            event.accept()
    
    def eventFilter(self, object, event):
        """
        Filters the key press event on the editor object to look for backspace
        key strokes on blank editors to remove previous tags.
        
        :param      object | <QObject>
                    event | <QEvent>
        
        :return     <bool> | consumed
        """
        if event.type() == event.KeyPress:
            if event.key() == Qt.Key_Backspace:
                is_line_edit = isinstance(object, QLineEdit)
                if not (is_line_edit and object.text()):
                    if self.count() > 1:
                        self.takeItem(self.count() - 2)
                        object.setFocus()
            
            elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
                self.finishEditing(object.text())
                return True
        
            
        return False
    
    def finishEditing(self, tag):
        """
        Finishes editing the current item.
        """
        curr_item = self.currentItem()
        create_item = self.createItem()
        self.closePersistentEditor(curr_item)
        
        if curr_item == create_item:
            self.addTag(tag)
        
        elif self.isTagValid(tag):
            curr_item.setText(tag)
    
    def handleTagChange( self, item ):
        """
        Handles the tag change information for this widget.
        
        :param      item | <QListWidgetItem>
        """
        # :note PySide == operator not defined for QListWidgetItem.  In this
        #       in this case, we're just checking if the object is the exact
        #       same, so 'is' works just fine.
        create_item = self.createItem()
        if item is create_item:
            self.addTag(create_item.text())
        
        elif self.isTagValid(item.text()):
            item.setText(item.text())
    
    def hasTag( self, tag ):
        """
        Returns whether or not the inputed tag exists in this collection.
        
        :return     <bool>
        """
        return nativestring(tag) in self.tags()
    
    def highlightColor( self ):
        """
        Returns the highlight color for this edit.
        
        :return     <QColor>
        """
        return self._highlightColor
    
    def isEditable(self):
        """
        Returns whether or not the user can edit the items in the list by
        typing.
        
        :return     <bool>
        """
        return self._editable
    
    def isInsertAllowed( self ):
        """
        Returns the whether or not a user is able to insert new tags besides
        the ones in the options.
        
        :return     <bool>
        """
        return self._insertAllowed
    
    def isTagValid( self, tag ):
        """
        Checks to see if the inputed tag is valid or not.
        
        :param      tag | <str>
        
        :return     <bool>
        """
        if ( self._options is not None and \
             not nativestring(tag) in self._options \
             and not self.isInsertAllowed() ):
            return False
        
        elif ( self.isUnique() and self.hasTag(tag) ):
            return False
        
        return True
    
    def isUnique( self ):
        """
        Returns whether or not the tags for this edit should be unique.
        
        :return     <bool>
        """
        return self._unique
    
    def itemFromTag( self, tag ):
        """
        Returns the item assigned to the given tag.
        
        :param      tag | <str>
        
        :return     <XMultiTagItem> || None
        """
        for row in range(self.count() - 1):
            item = self.item(row)
            if ( item and item.text() == tag ):
                return item
        return None
    
    def itemsRemovable( self ):
        """
        Returns whether or not the items are able to be removed by the user.
        
        :return     <bool>
        """
        return self._itemsRemovable
    
    def keyPressEvent( self, event ):
        """
        Handles the Ctrl+C/Ctrl+V events for copy & paste.
        
        :param      event | <QKeyEvent>
        """
        if ( event.key() == Qt.Key_C and \
             event.modifiers() == Qt.ControlModifier ):
            self.copy()
            event.accept()
            return
            
        elif ( event.key() == Qt.Key_V and \
             event.modifiers() == Qt.ControlModifier ):
            self.paste()
            event.accept()
            return
        
        elif ( event.key() == Qt.Key_Delete ):
            indexes = map(self.row, self.selectedItems())
            for index in reversed(sorted(indexes)):
                self.takeItem(index)
            
            event.accept()
            return
        
        elif event.key() == Qt.Key_Backspace:
            if self.count() > 1:
                self.takeItem(self.count() - 2)
                self.setFocus()
        
        super(XMultiTagEdit, self).keyPressEvent(event)
    
    def mimeData( self, items ):
        """
        Creates the mime data for the different items.
        
        :param      items | [<QListWidgetItem>, ..]
        
        :return     <QMimeData>
        """
        text = []
        for item in items:
            text.append(nativestring(item.text()))
        
        data = QMimeData()
        data.setText(','.join(text))
        return data
    
    def mousePressEvent( self, event ):
        """
        Make sure on a mouse release event that we have a current item.  If
        no item is current, then our edit item will become current.
        
        :param      event | <QMouseReleaseEvent>
        """
        item = self.itemAt(event.pos())
        
        # set the tag creation item as active
        if item is None:
            create_item = self.createItem()
            if create_item:
                self.setCurrentItem(create_item)
                self.editItem(create_item)
        
        # check to see if we're removing a tag
        else:
            rect = self.visualItemRect(item)
            if ( rect.right() - 14 < event.pos().x()  ):
                # make sure the item is allowed to be removed via the widget
                if ( self.itemsRemovable() ):
                    self.takeItem(self.row(item))
                
                # emit the removed signal
                if ( not self.signalsBlocked() ):
                    self.tagRemoved.emit(item.text())
                
                event.ignore()
                return
        
        super(XMultiTagEdit, self).mousePressEvent(event)
    
    def options( self ):
        """
        Returns the list of options that are valid for this tag edit.
        
        :return     [<str>, ..]
        """
        if self._options is None:
            return []
        return self._options
    
    def paste( self ):
        """
        Pastes text from the clipboard.
        """
        text = nativestring(QApplication.clipboard().text())
        for tag in text.split(','):
            tag = tag.strip()
            if ( self.isTagValid(tag) ):
                self.addTag(tag)
    
    def resizeEvent(self, event):
        """
        Overloads the resize event to control if we are still editing.
        
        If we are resizing, then we are no longer editing.
        """
        curr_item = self.currentItem()
        self.closePersistentEditor(curr_item)
        
        super(XMultiTagEdit, self).resizeEvent(event)
    
    def setCompleter( self, completer ):
        """
        Sets the text completer for this tag widget to the inputed completer.
        
        :param      completer | <QCompleter>
        """
        if ( self._completer == completer ):
            return
        elif ( self._completer ):
            self._completer.activated.disconnect(self.finishEditing)
        
        self._completer = completer
        
        if ( completer ):
            completer.activated.connect(self.finishEditing)
    
    def setEditable(self, state):
        """
        Sets whether or not the user can edit the items in the list by
        typing.
        
        :param     state | <bool>
        """
        self._editable = state
        if state:
            self.setEditTriggers(self.AllEditTriggers)
        else:
            self.setEditTriggers(self.NoEditTriggers)
    
    def setInsertAllowed( self, state ):
        """
        Sets whether or not the insertion is allowed for tags not defined in 
        the options.
        
        :param      state | <bool>
        """
        self._insertAllowed = state
    
    def setItemsRemovable( self, state ):
        """
        Sets whether or not the items should be allowed to be removed by the
        user.
        
        :param      state | <bool>
        """
        self._itemsRemovable = state
    
    def setOptions( self, options ):
        """
        Sets the tag option list for this widget.  If used, tags need to be
        found within the list of options when added.
        
        :param      options | [<str>, ..]
        """
        self._options = map(str, options)
        
        if ( options ):
            completer = QCompleter(options, self)
            completer.setCompletionMode(QCompleter.InlineCompletion)
            self.setCompleter(completer)
        else:
            self.setCompleter(None)
    
    def setTags( self, tags ):
        """
        Sets the tags assigned to this item to the inputed list of tags.
        
        :param      tags | [<str>, ..]
        """
        self.setUpdatesEnabled(False)
        self.blockSignals(True)
        
        self.clear()
        for tag in tags:
            self.addItem(XMultiTagItem(tag, self))
        
        self.blockSignals(False)
        self.setUpdatesEnabled(True)
    
    def setUnique( self, state ):
        """
        Sets whether or not the tags on this edit should be unique.
        
        :param      state | <bool>
        """
        self._unique = state
    
    def setViewMode( self, viewMode ):
        """
        Sets the view mode for this widget to the inputed mode.
        
        :param      viewMode | <QListWidget.ViewMode>
        """
        ddrop_mode = self.dragDropMode()
        super(XMultiTagEdit, self).setViewMode(viewMode)
        self.setDragDropMode(ddrop_mode)
    
    def tagColor( self ):
        """
        Returns the color used for the tags of this edit.
        
        :return     <QColor>
        """
        return self._tagColor
    
    def tagItems( self ):
        """
        Returns a list of all the tag items assigned to this widget.
        
        :return     [<XMultiTagItem>, ..]
        """
        return [self.item(row) for row in range(self.count() - 1)]
    
    def tags( self ):
        """
        Returns a list of all the tags assigned to this widget.
        
        :return     [<str>, ..]
        """
        item  = self.item(self.count() - 1)
        count = self.count()
        if ( item is self._createItem ):
            count -= 1
        
        return [nativestring(self.item(row).text()) for row in range(count)]
    
    def takeTag( self, tag ):
        """
        Removes the inputed tag from the system.
        
        :param      tag | <str>
        
        :return     <XMultiTagItem> || None
        """
        for row in range(self.count() - 1):
            item = self.item(row)
            if ( item and item.text() == tag ):
                self.takeItem(row)
                if ( not self.signalsBlocked() ):
                    self.tagRemoved.emit(tag)
                return item
        return None
    
    x_editable       = Property(bool, isEditable, setEditable)
    x_unique         = Property(bool, isUnique, setUnique)
    x_insertAllowed  = Property(bool, isInsertAllowed, setInsertAllowed)
    x_itemsRemovable = Property(bool, itemsRemovable, setItemsRemovable)

__designer_plugins__ = [XMultiTagEdit]