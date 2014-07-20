#!/usr/bin/python

""" 
Defines a custom combobox class that supports advanced features such as an \
XLineEdit editor and multi-check options.
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

import weakref

try:
    from projex.text import nativestring
except ImportError:
    nativestring = str

from projexui.qt import Signal, Slot, Property
from projexui.qt.QtCore import Qt, QPoint
from projexui.qt.QtGui import QComboBox, QListView, QColor, QPainter, QPixmap

from projexui import resources
from projexui.widgets.xlineedit import XLineEdit

class XComboBox(QComboBox):
    """
    ~~>[img:widgets/xcombobox.png]
    The XComboBox class is a simple extension to the standard QComboBox
    that provides a couple enhancement features, namely the ability to 
    add a hint to the line edit and supporting multi-selection via checkable
    items.
    
    == Example ==
    
    |>>> from projexui.widgets.xcombobox import XComboBox
    |>>> import projexui
    |
    |>>> # create the combobox
    |>>> combo = projexui.testWidget(XComboBox)
    |
    |>>> # set the hint
    |>>> combo.setHint('select type')
    |
    |>>> # create items, make checkable
    |>>> combo.addItems(['A', 'B', 'C'])
    |>>> combo.setCheckable(True)
    |
    |>>> # set the checked items
    |>>> combo.setCheckedItems(['C'])
    |>>> combo.setCheckedIndexes([0, 2])
    |
    |>>> # retrieve checked items
    |>>> combo.checkedItems()
    |['A', 'C']
    |>>> combo.checkedIndexes()
    |[0, 2]
    |
    |>>> # connect to signals
    |>>> def printChecked(): print checked.checkedItems()
    |>>> combo.checkedIndexesChanged.connect(printChecked)
    |
    |>>> # modify selection and see the output
    """
    __designer_icon__ = resources.find('img/ui/combobox.png')
    
    checkedIndexesChanged = Signal(list)
    checkedItemsChanged   = Signal(list)
    
    def __init__(self, parent=None):
        # define custom properties
        self._checkable = False
        self._hint      = ''
        self._separator = ','
        self._autoRaise = False
        self._hovered = False
        self._lineEdit = None
        
        # setup the checkable popup widget
        self._checkablePopup = None
        
        # set default properties
        super(XComboBox, self).__init__(parent)
        self.setLineEdit(XLineEdit(self))
    
    def autoRaise(self):
        """
        Returns whether or not this combo box should automatically
        raise up.
        
        :return     <bool>
        """
        return self._autoRaise
    
    def adjustCheckState( self ):
        """
        Updates when new items are added to the system.
        """
        if self.isCheckable():
            self.updateCheckState()
    
    def checkablePopup( self ):
        """
        Returns the popup if this widget is checkable.
        
        :return     <QListView> || None
        """
        if not self._checkablePopup and self.isCheckable():
            popup = QListView(self)
            popup.setSelectionMode(QListView.NoSelection)
            popup.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            popup.setWindowFlags(Qt.Popup)
            popup.installEventFilter(self)
            popup.doubleClicked.connect(self.checkModelIndex)
            self._checkablePopup = popup
        
        return self._checkablePopup
    
    def checkModelIndex( self, modelIndex ):
        """
        Sets the current index as the checked index.
        
        :param      modelIndex | <QModelIndex>
        """
        self.checkablePopup().hide()
        
        if not self.isCheckable():
            return
        
        self.setCheckedIndexes([modelIndex.row()])
    
    def currentText(self):
        """
        Returns the current text for this combobox, including the hint option \
        if no text is set.
        """
        lineEdit = self.lineEdit()
        if lineEdit:
            return lineEdit.currentText()
        text = nativestring(super(XComboBox, self).currentText())
        if not text:
            return self._hint
        return text
    
    def checkedIndexes( self ):
        """
        Returns a list of checked indexes for this combobox.
        
        :return     [<int>, ..]
        """
        if ( not self.isCheckable() ):
            return []
        
        model  = self.model()
        return [i for i in range(self.count()) if model.item(i).checkState()]
        
    def checkedItems( self ):
        """
        Returns the checked items for this combobox.
        
        :return     [<str>, ..]
        """
        if not self.isCheckable():
            return []
        
        return [nativestring(self.itemText(i)) for i in self.checkedIndexes()]
    
    def enterEvent(self, event):
        self._hovered = True
        super(XComboBox, self).enterEvent(event)
        
        if self.autoRaise():
            try:
                self.lineEdit().show()
            except AttributeError:
                pass
    
    def eventFilter(self, object, event):
        """
        Filters events for the popup widget.
        
        :param      object | <QObject>
                    event  | <QEvent>
        """
        # popup the editor when clicking in the line edit for a checkable state
        if object == self.lineEdit() and self.isEnabled():
            if not self.isCheckable():
                return super(XComboBox, self).eventFilter(object, event)
            
            # show the popup when the user clicks on it
            elif event.type() == event.MouseButtonPress:
                self.showPopup()
            
            # eat the wheel event when the user is scrolling
            elif event.type() == event.Wheel:
                return True
            
        # make sure we're looking for the checkable popup
        elif object == self._checkablePopup:
            if event.type() == event.KeyPress and \
                 event.key() in (Qt.Key_Escape, Qt.Key_Return, Qt.Key_Enter):
                object.close()
            
            elif event.type() == event.MouseButtonPress:
                if not object.geometry().contains(event.pos()):
                    object.close()
        
        return super(XComboBox, self).eventFilter(object, event)
    
    def hint( self ):
        """
        Returns the hint for this combobox.
        
        :return     <str>
        """
        return self._hint
    
    def hintColor(self):
        """
        Returns the hint color for this combo box provided its line edit is
        an XLineEdit instance.
        
        :return     <QColor>
        """
        lineEdit = self.lineEdit()
        if isinstance(lineEdit, XLineEdit):
            return lineEdit.hintColor()
        return QColor()
    
    def isCheckable( self ):
        """
        Returns whether or not this combobox has checkable options.
        
        :return     <bool>
        """
        try:
            return self._checkable
        except AttributeError:
            return False
    
    def items( self ):
        """
        Returns the labels for the different items in this combo box.
        
        :return     [<str>, ..]
        """
        return [self.itemText(i) for i in range(self.count())]
    
    def leaveEvent(self, event):
        self._hovered = False
        super(XComboBox, self).leaveEvent(event)
        
        if self.autoRaise():
            try:
                self.lineEdit().hide()
            except AttributeError:
                pass
    
    def lineEdit(self):
        """
        Returns the line editor associated with this combobox.  This will
        return the object stored at the reference for the editor since
        sometimes the internal Qt process will raise a RuntimeError that
        the C/C++ object has been deleted.
        
        :return     <XLineEdit> || None
        """
        try:
            edit = self._lineEdit()
        except TypeError:
            edit = None

        if edit is None:
            self._edit = None
        return edit
    
    def paintEvent(self, event):
        """
        Paints this combobox based on whether or not it is visible.
        
        :param      event | <QPaintEvent>
        """
        if not self.autoRaise() or (self._hovered and self.isEnabled()):
            super(XComboBox, self).paintEvent(event)
            
            text = QComboBox.currentText(self)
            if not text and self._hint and not self.lineEdit():
                text = self._hint
                palette = self.palette()
                painter = QPainter(self)
                painter.setPen(palette.color(palette.Disabled, palette.Text))
                painter.drawText(5, 0, self.width(), self.height(),
                                 Qt.AlignLeft | Qt.AlignVCenter,
                                 self.currentText())
            
        else:
            palette = self.palette()
            painter = QPainter(self)
            text = QComboBox.currentText(self)
            if not text:
                text = self.hint()
                painter.setPen(palette.color(palette.Disabled,
                                             palette.WindowText))
            
            painter.drawText(5, 0, self.width(), self.height(),
                             Qt.AlignLeft | Qt.AlignVCenter, text)
            
            x = self.width() - 15
            y = 4
            pixmap = QPixmap(resources.find('img/treeview/triangle_down.png'))
            painter.drawPixmap(x, y, pixmap)
    
    def separator( self ):
        """
        Returns the separator that will be used for joining together 
        the options when in checked mode.  By default, this will be a comma.
        
        :return     <str>
        """
        return self._separator
    
    def setAutoRaise(self, state):
        """
        Sets whether or not this combo box should automatically
        raise up.
        
        :param      state | <bool>
        """
        self._autoRaise = state
        self.setMouseTracking(state)
        try:
            self.lineEdit().setVisible(not state)
        except AttributeError:
            pass
    
    def setCheckedIndexes(self, indexes):
        """
        Sets a list of checked indexes for this combobox.
        
        :param      indexes | [<int>, ..]
        """
        if not self.isCheckable():
            return
        
        model = self.model()
        model.blockSignals(True)
        for i in range(self.count()):
            if not self.itemText(i):
                continue
            
            item = model.item(i)
            
            if i in indexes:
                state = Qt.Checked
            else:
                state = Qt.Unchecked
                
            item.setCheckState(state)
        model.blockSignals(False)
        self.updateCheckedText()
    
    def setCheckedItems(self, items):
        """
        Returns the checked items for this combobox.
        
        :return     items | [<str>, ..]
        """
        if not self.isCheckable():
            return
        
        model = self.model()
        for i in range(self.count()):
            item_text = self.itemText(i)
            if not item_text:
                continue
            
            if nativestring(item_text) in items:
                state = Qt.Checked
            else:
                state = Qt.Unchecked
            
            model.item(i).setCheckState(state)
    
    def setCheckable( self, state ):
        """
        Sets whether or not this combobox stores checkable items.
        
        :param      state | <bool>
        """
        self._checkable = state
        
        # need to be editable to be checkable
        edit = self.lineEdit()
        if state:
            self.setEditable(True)
            edit.setReadOnly(True)
            
            # create connections
            model = self.model()
            model.rowsInserted.connect(self.adjustCheckState)
            model.dataChanged.connect(self.updateCheckedText)
        
        elif edit:
            edit.setReadOnly(False)
        
        self.updateCheckState()
        self.updateCheckedText()
    
    def setEditable( self, state ):
        """
        Sets whether or not this combobox will be editable, updating its \
        line edit to an XLineEdit if necessary.
        
        :param      state | <bool>
        """
        super(XComboBox, self).setEditable(state)
        
        if state:
            edit = self.lineEdit()
            if edit and isinstance(edit, XLineEdit):
                return
            elif edit:
                edit.setParent(None)
                edit.deleteLater()
            
            edit = XLineEdit(self)
            edit.setHint(self.hint())
            self.setLineEdit(edit)
    
    def setLineEdit(self, edit):
        """
        Sets the line edit for this widget.
        
        :warning    If the inputed edit is NOT an instance of XLineEdit, \
                    this method will destroy the edit and create a new \
                    XLineEdit instance.
        
        :param      edit | <XLineEdit>
        """
        if edit and not isinstance(edit, XLineEdit):
            edit.setParent(None)
            edit.deleteLater()
            
            edit = XLineEdit(self)
        
        if edit is not None:
            edit.installEventFilter(self)
            self._lineEdit = weakref.ref(edit)
        else:
            self._lineEdit = None
        
        super(XComboBox, self).setLineEdit(edit)
    
    def setHint( self, hint ):
        """
        Sets the hint for this line edit that will be displayed when in \
        editable mode.
        
        :param      hint | <str>
        """
        self._hint = hint
        
        lineEdit   = self.lineEdit()
        if isinstance(lineEdit, XLineEdit):
            lineEdit.setHint(hint)
    
    def setHintColor(self, color):
        """
        Sets the hint color for this combo box provided its line edit is
        an XLineEdit instance.
        
        :param      color | <QColor>
        """
        lineEdit = self.lineEdit()
        if isinstance(lineEdit, XLineEdit):
            lineEdit.setHintColor(color)
    
    @Slot(str)
    def setSeparator( self, separator ):
        """
        Sets the separator that will be used when joining the checked items
        for this combo in the display.
        
        :param      separator | <str>
        """
        self._separator = nativestring(separator)
        self.updateCheckedText()
    
    def showPopup( self ):
        """
        Displays a custom popup widget for this system if a checkable state \
        is setup.
        """
        if not self.isCheckable():
            return super(XComboBox, self).showPopup()
        
        if not self.isVisible():
            return
        
        # update the checkable widget popup
        point = self.mapToGlobal(QPoint(0, self.height() - 1))
        popup = self.checkablePopup()
        popup.setModel(self.model())
        popup.move(point)
        popup.setFixedWidth(self.width())
        
        height = (self.count() * 19) + 2
        if height > 400:
            height = 400
            popup.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        else:
            popup.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        popup.setFixedHeight(height)
        popup.show()
        popup.raise_()
    
    def updateCheckState( self ):
        """
        Updates the items to reflect the current check state system.
        """
        checkable = self.isCheckable()
        model     = self.model()
        flags     = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        
        for i in range(self.count()):
            item = model.item(i)
            
            if not (checkable and item.text()):
                item.setCheckable(False)
                item.setFlags(flags)
            
            # only allow checking for items with text
            else:
                item.setCheckable(True)
                item.setFlags(flags | Qt.ItemIsUserCheckable)
    
    def updateCheckedText(self):
        """
        Updates the text in the editor to reflect the latest state.
        """
        if not self.isCheckable():
            return
        
        indexes = self.checkedIndexes()
        items = self.checkedItems()
        self.lineEdit().setText(self.separator().join(items))
        
        if not self.signalsBlocked():
            self.checkedItemsChanged.emit(items)
            self.checkedIndexesChanged.emit(indexes)
    
    def toggleModelIndex(self, modelIndex):
        """
        Toggles the index's check state.
        
        :param      modelIndex | <QModelIndex>
        """
        if not self.isCheckable():
            return
            
        item = self.model().item(modelIndex.row())
        if item.checkState() == Qt.Checked:
            state = Qt.Unchecked
        else:
            state = Qt.Checked
        
        item.setCheckState(state)
    
    # define qt properties
    x_hint      = Property(str,  hint,        setHint)
    x_checkable = Property(bool, isCheckable, setCheckable)
    x_separator = Property(str,  separator,   setSeparator)
    x_autoRaise = Property(bool, autoRaise, setAutoRaise)

__designer_plugins__ = [XComboBox]