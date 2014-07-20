#!/usr/bin/python

""" Creates a widget for managing navigational paths. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

#---------------------------------------------------------------------

from projex.text import nativestring
from projexui.qt import Signal, Slot, wrapVariant
from projexui.qt.QtCore import Qt,\
                               QSize
                         
from projexui.qt.QtGui import QButtonGroup,\
                              QCompleter,\
                              QCursor,\
                              QHBoxLayout,\
                              QLineEdit,\
                              QTreeView,\
                              QMenu,\
                              QScrollArea,\
                              QStandardItem,\
                              QStandardItemModel,\
                              QToolButton,\
                              QWidget

import projexui.resources

from projexui.widgets.xlineedit import XLineEdit

#------------------------------------------------------------------------------

class XNavigationItem(QStandardItem):
    def __init__( self, text = 'Root' ):
        super(XNavigationItem, self).__init__(text)
        
        # set custom properties
        self._initialized = False
        
        # set default parameters
        self.setSizeHint(QSize(80, 20))
    
    def initialize( self ):
        """
        Begins to load the item data for each tree level.
        
        :return     <bool> | success
        """
        if ( self._initialized ):
            return True
        
        self._initialized = True
        
        # load the item's children
        model = self.model()
        signalsBlocked = False
        if ( model ):
            signalsBlocked = model.signalsBlocked()
            model.blockSignals(True)
            
        state = self.loadContext()
        
        if ( model ):
            model.blockSignals(signalsBlocked)
        
        return state
    
    def loadContext( self ):
        """
        Loads the context for this particular item by adding children to this
        item's rows.  This method should be modified in a subclass to handle \
        sub-loading of contexts.
        
        :return     <bool> | success
        """
        return True
    
#------------------------------------------------------------------------------

class XNavigationModel(QStandardItemModel):
    def __init__( self, parent = None, root = None ):
        super(XNavigationModel, self).__init__(parent)
        
        # define custom properties
        self._separator = '/'
        
    def itemPath( self, item ):
        """
        Returns the path for the inputed item based on its hierarchy.
        
        :return     <str>
        """
        path = []
        while ( item ):
            path.insert(0, nativestring(item.text()))
            item = item.parent()
        
        sep = self.separator()
        return sep + sep.join(path)
    
    def itemByPath( self, path, includeRoot = False ):
        """
        Loads the items for the given path.
        
        :param      path        | <str>
                    includeRoot | <bool>
        """
        sep     = self.separator()
        path    = nativestring(path).strip(sep)
        if ( not path ):
            if ( includeRoot ):
                return self.invisibleRootItem()
            else:
                return None
            
        splt    = path.split(sep)
        item    = self.invisibleRootItem()
        for part in splt:
            next_item = None
            for row in range(item.rowCount()):
                child = item.child(row)
                if ( child.text() == part ):
                    next_item = child
                    break
            
            if ( not next_item ):
                item = None
                break
                
            item = next_item
            item.initialize()
        
        return item
    
    def setSeparator( self, separator ):
        """
        Sets the separator string to be used for this model.
        
        :param      separator | <str>
        """
        self._separator = separator
    
    def separator( self ):
        """
        Returns the separator that is going to be used for this model.
        
        :return     <str>
        """
        return self._separator
    
    def setTopLevelItems( self, items ):
        """
        Sets the root item for this model to the inputed item.
        
        :param      item | <XNavigationItem>
        """
        self.blockSignals(True)
        
        root = self.invisibleRootItem()
        for row in range(root.rowCount()):
            root.takeRow(row)
        
        for item in items:
            root.appendRow(item)
            
        self.blockSignals(False)
        
#------------------------------------------------------------------------------

class XNavigationCompleter(QCompleter):
    def __init__( self, model, parent ):
        super(XNavigationCompleter, self).__init__(model, parent)
        
        self.setCaseSensitivity(Qt.CaseInsensitive)
        
    def pathFromIndex( self, index ):
        """
        Returns the full path from the inputed index on.
        
        :param      index | <QModelIndex>
        
        :return     <str>
        """
        item = self.model().itemFromIndex(index)
        return self.model().itemPath(item)
        
    def splitPath( self, path ):
        """
        Splits the path into its components.
        
        :param      path | <str>
        
        :return     [<str>, ..]
        """
        sep = self.model().separator()
        splt = nativestring(path).lstrip(sep).split(sep)
        
        if ( splt and not splt[-1] ):
            self.model().itemByPath(path)
            
        return splt

#------------------------------------------------------------------------------

class XNavigationEdit(XLineEdit):
    """ """
    navigationChanged = Signal()
    
    __designer_icon__ = projexui.resources.find('img/ui/navigate.png')
    
    def __init__( self, parent = None ):
        super(XNavigationEdit, self).__init__( parent )
        
        # define custom properties
        self._separator             = '/'
        self._partsEditingEnabled   = True
        self._originalText          = ''
        self._scrollWidget          = QScrollArea(self)
        self._partsWidget           = QWidget(self._scrollWidget)
        self._buttonGroup           = QButtonGroup(self)
        self._scrollAmount          = 0
        self._navigationModel       = None
        
        # create the completer tree
        palette = self.palette()
        palette.setColor(palette.Base, palette.color(palette.Window))
        palette.setColor(palette.Text, palette.color(palette.WindowText))
        
        bg      = palette.color(palette.Highlight)
        abg     = bg.darker(115)
        fg      = palette.color(palette.HighlightedText)
        sbg     = 'rgb(%s, %s, %s)' % (bg.red(), bg.green(), bg.blue())
        sabg    = 'rgb(%s, %s, %s)' % (abg.red(), abg.green(), abg.blue())
        sfg     = 'rgb(%s, %s, %s)' % (fg.red(), fg.green(), fg.blue())
        style   = 'QTreeView::item:hover { '\
                  '     color: %s;'\
                  '     background: qlineargradient(x1:0,'\
                  '                                 y1:0,'\
                  '                                 x2:0,'\
                  '                                 y2:1,'\
                  '                                 stop: 0 %s,'\
                  '                                 stop: 1 %s);'\
                  '}' % (sfg, sbg, sabg)
        
        self._completerTree = QTreeView(self)
        self._completerTree.setStyleSheet(style)
        self._completerTree.header().hide()
        self._completerTree.setFrameShape(QTreeView.Box)
        self._completerTree.setFrameShadow(QTreeView.Plain)
        self._completerTree.setPalette(palette)
        self._completerTree.setEditTriggers(QTreeView.NoEditTriggers)
        self._completerTree.setWindowFlags(Qt.Popup)
        self._completerTree.installEventFilter(self)
        self._completerTree.setRootIsDecorated(False)
        self._completerTree.setItemsExpandable(False)
        
        # create the editing widget
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addStretch()
        
        self._scrollWidget.setFrameShape( QScrollArea.NoFrame )
        self._scrollWidget.setFocusPolicy(Qt.NoFocus)
        self._scrollWidget.setWidget(self._partsWidget)
        self._scrollWidget.setWidgetResizable(True)
        self._scrollWidget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scrollWidget.setAlignment(Qt.AlignTop | Qt.AlignRight)
        self._scrollWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scrollWidget.setContentsMargins(0, 0, 0, 0)
        self._scrollWidget.setViewportMargins(0, 0, 0, 0)
        self._scrollWidget.move(2, 2)
        
        self._partsWidget.setLayout(layout)
        self._partsWidget.setCursor(Qt.ArrowCursor)
        self._partsWidget.setAutoFillBackground(True)
        self._partsWidget.setFixedHeight(self.height() - 12)
        
        palette = self._partsWidget.palette()
        palette.setColor(palette.Background, palette.color(palette.Base))
        self._partsWidget.setPalette(palette)
        
        # create connections
        self._completerTree.clicked.connect( self.navigateToIndex )
        self._buttonGroup.buttonClicked.connect( self.handleButtonClick )
        self._scrollWidget.horizontalScrollBar().valueChanged.connect( 
                                                        self.scrollParts )
    
    def acceptEdit( self ):
        """
        Accepts the current text and rebuilds the parts widget.
        """
        
        if ( self._partsWidget.isVisible() ):
            return False
        
        use_completion = self.completer().popup().isVisible()
        completion     = self.completer().currentCompletion()
        
        self._completerTree.hide()
        self.completer().popup().hide()
        
        if ( use_completion ):
            self.setText(completion)
        else:
            self.rebuild()
            
        return True
    
    def cancelEdit( self ):
        """
        Rejects the current edit and shows the parts widget.
        """
        
        if ( self._partsWidget.isVisible() ):
            return False
            
        self._completerTree.hide()
        self.completer().popup().hide()
        
        self.setText(self._originalText)
        return True
    
    def currentItem( self ):
        """
        Returns the current navigation item from the current path.
        
        :return     <XNavigationItem> || None
        """
        model = self.navigationModel()
        if ( not model ):
            return None
        
        return model.itemByPath(self.text())
    
    def eventFilter( self, object, event ):
        """
        Filters the events for the inputed object through this edit.
        
        :param      object | <QObject>
                    event  | <QEvent>
        
        :return     <bool> | consumed
        """
        if ( event.type() == event.KeyPress ):
            if ( event.key() == Qt.Key_Escape ):
                self._completerTree.hide()
                self.completer().popup().hide()
                
                self.cancelEdit()
                
            elif ( event.key() in (Qt.Key_Return, Qt.Key_Enter) ):
                self.acceptEdit()
                return True
                
            elif ( event.key() == Qt.Key_Tab ):
                if ( self.completer().popup().isVisible() ):
                    text   = nativestring(self.completer().currentCompletion())
                    super(XNavigationEdit, self).setText(text)
                    return True
                else:
                    self.acceptEdit()
                    return False
            
        elif ( event.type() == event.MouseButtonPress ):
            if ( not self._completerTree.rect().contains(event.pos()) ):
                self._completerTree.hide()
                self.completer().popup().hide()
                
                self.cancelEdit()
        
        return False
    
    def focusOutEvent( self, event ):
        """
        Overloads the focus out event to cancel editing when the widget loses
        focus.
        
        :param      event | <QFocusEvent>
        """
        super(XNavigationEdit, self).focusOutEvent(event)
        
        self.cancelEdit()
    
    def handleButtonClick( self, button ):
        """
        Handle the event when a user clicks on one of the part buttons.
        
        :param      button | <QToolButton>
        """
        path            = button.property('path')
        is_completer    = button.property('is_completer')
        
        # popup a completion menu
        if ( unwrapVariant(is_completer) ):
            model = self.navigationModel()
            if ( not model ):
                return
            
            sep  = self.separator()
            path = nativestring(unwrapVariant(path))
            item = model.itemByPath(path, includeRoot = True)
            if ( not item ):
                return
            
            curr_path = nativestring(self.text()).strip(self.separator())
            curr_path = curr_path.replace(path, '').strip(self.separator())
            
            child_name = ''
            if ( curr_path ):
                child_name = curr_path.split(self.separator())[0]
            
            index = model.indexFromItem(item)
            
            self._completerTree.move(QCursor.pos())
            self._completerTree.setRootIndex(index)
            self._completerTree.verticalScrollBar().setValue(0)
            
            if ( child_name ):
                child_item = None
                for i in range(item.rowCount()):
                    child = item.child(i)
                    if ( child.text() == child_name ):
                        child_item = child
                        break
                
                if ( child_item ):
                    child_index = model.indexFromItem(child_item)
                    self._completerTree.setCurrentIndex(child_index)
                    self._completerTree.scrollTo(child_index)
            
            self._completerTree.show()
            self._completerTree.setUpdatesEnabled(True)
        else:
            self.setText(unwrapVariant(path))
    
    def keyPressEvent( self, event ):
        """
        Overloads the key press event to listen for escape calls to cancel the
        parts editing.
        
        :param      event | <QKeyPressEvent>
        """
        if ( self.scrollWidget().isHidden() ):
            if ( event.key() == Qt.Key_Escape ):
                self.cancelEdit()
                return
                
            elif ( event.key() in (Qt.Key_Return, Qt.Key_Enter) ):
                self.acceptEdit()
                return
            
        elif ( event.key() == Qt.Key_A and 
               event.modifiers() == Qt.ControlModifier ):
            self.startEdit()
        
        super(XNavigationEdit, self).keyPressEvent(event)
    
    def mouseDoubleClickEvent( self, event ):
        """
        Overloads the system to enable editing when a user double clicks.
        
        :param      event | <QMouseEvent>
        """
        super(XNavigationEdit, self).mouseDoubleClickEvent(event)
        
        self.startEdit()
    
    def navigationModel( self ):
        """
        Returns the navigation model linked with this edit.
        
        :return     <XNavigationModel> || None
        """
        return self._navigationModel
    
    def navigateToIndex( self, index ):
        """
        Navigates to the inputed action's path.
        
        :param      action | <QAction>
        """
        self._completerTree.hide()
        item = self._navigationModel.itemFromIndex(index)
        self.setText(self._navigationModel.itemPath(item))
    
    def parts( self ):
        """
        Returns the parts that are used for this system.
        
        :return     [<str>, ..]
        """
        path = nativestring(self.text()).strip(self.separator())
        if ( not path ):
            return []
        return path.split(self.separator())
    
    def partsWidget( self ):
        """
        Returns the widget that contains the parts system.
        
        :return     <QScrollArea>
        """
        return self._partsWidget
    
    def startEdit( self ):
        """
        Rebuilds the pathing based on the parts.
        """
        self._originalText = self.text()
        self.scrollWidget().hide()
        self.setFocus()
        self.selectAll()
    
    def rebuild( self ):
        """
        Rebuilds the parts widget with the latest text.
        """
        navitem = self.currentItem()
        if ( navitem ):
            navitem.initialize()
            
        self.setUpdatesEnabled(False)
        self.scrollWidget().show()
        self._originalText = ''
        
        partsw = self.partsWidget()
        for button in self._buttonGroup.buttons():
            self._buttonGroup.removeButton(button)
            button.close()
            button.setParent(None)
            button.deleteLater()
        
        # create the root button
        layout = partsw.layout()
        parts  = self.parts()
        
        button = QToolButton(partsw)
        button.setAutoRaise(True)
        button.setMaximumWidth(12)
        button.setArrowType(Qt.RightArrow)
        
        button.setProperty('path',          wrapVariant(''))
        button.setProperty('is_completer',  wrapVariant(True))
        last_button = button
            
        self._buttonGroup.addButton(button)
        layout.insertWidget(0, button)
        
        # check to see if we have a navigation model setup
        if ( self._navigationModel ):
            last_item = self._navigationModel.itemByPath(self.text())
            show_last =  last_item and last_item.rowCount() > 0
        else:
            show_last = False
        
        # load the navigation system
        count = len(parts)
        for i, part in enumerate(parts):
            path = self.separator().join(parts[:i+1])
            
            button = QToolButton(partsw)
            button.setAutoRaise(True)
            button.setText(part)
            
            if ( self._navigationModel ):
                item = self._navigationModel.itemByPath(path)
                if ( item ):
                    button.setIcon(item.icon())
                    button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            
            button.setProperty('path',         wrapVariant(path))
            button.setProperty('is_completer', wrapVariant(False))
            
            self._buttonGroup.addButton(button)
            layout.insertWidget((i * 2) + 1, button)
            
            # determine if we should show the final button
            if ( show_last or i < (count - 1) ):
                button = QToolButton(partsw)
                button.setAutoRaise(True)
                button.setMaximumWidth(12)
                button.setArrowType(Qt.RightArrow)
                
                button.setProperty('path',          wrapVariant(path))
                button.setProperty('is_completer',  wrapVariant(True))
            
                self._buttonGroup.addButton(button)
                layout.insertWidget((i * 2) + 2, button)
                
                last_button = button
        
        if ( self.scrollWidget().width() < partsw.width() ):
            self.scrollParts(partsw.width() - self.scrollWidget().width())
            
        self.setUpdatesEnabled(True)
        self.navigationChanged.emit()
    
    def resizeEvent( self, event ):
        """
        Resizes the current widget and its parts widget.
        
        :param      event | <QResizeEvent>
        """
        super(XNavigationEdit, self).resizeEvent(event)
        
        w = self.width()
        h = self.height()
        
        self._scrollWidget.resize(w - 4, h - 4)
        
        if ( self._scrollWidget.width() < self._partsWidget.width() ):
           self.scrollParts( self._partsWidget.width() - self._scrollWidget.width() )
    
    def scrollParts( self, amount ):
        """
        Scrolls the parts to offset the scrolling amount.
        
        :param      amount | <int>
        """
        change = self._scrollAmount - amount
        self._partsWidget.scroll(change, 0)
        self._scrollAmount = amount
    
    def scrollWidget( self ):
        """
        Returns the scrolling widget.
        
        :return     <QScrollArea>
        """
        return self._scrollWidget
    
    def separator( self ):
        """
        Returns the separation character that is used for this edit.
        
        :return     <str>
        """
        return self._separator
    
    def setTopLevelItems( self, items ):
        """
        Initializes the navigation system to start with the inputed root \
        item.
        
        :param      item | <XNavigationItem>
        """
        if ( not self._navigationModel ):
            self.setNavigationModel(XNavigationModel(self))
        
        self._navigationModel.setTopLevelItems(items)
    
    def setNavigationModel( self, model ):
        """
        Sets the navigation model for this edit.
        
        :param      model | <XNavigationModel>
        """
        self._navigationModel = model
        self._completerTree.setModel(model)
        
        if ( model ):
            model.setSeparator(self.separator())
            completer = XNavigationCompleter(model, self)
            self.setCompleter(completer)
            completer.popup().installEventFilter(self)
        else:
            self.setCompleter(None)
        
        self.rebuild()
    
    def setParts( self, parts ):
        """
        Sets the path for this edit widget by providing the parts to the path.
        
        :param      parts | [<str>, ..]
        """
        self.setText(self.separator().join(map(str, parts)))
    
    def setSeparator( self, separator ):
        """
        Sets the separator to the inputed character.
        
        :param      separator | <str>
        """
        self._separator = separator
        if ( self._navigationModel ):
            self._navigationModel.setSeparator(separator)
        self.rebuild()
    
    def setText( self, text ):
        """
        Sets the text for this edit to the inputed text.
        
        :param      text | <str>
        """
        super(XNavigationEdit, self).setText(text)
        
        self.scrollWidget().show()
        if ( text == '' or self._originalText != text ):
            self.rebuild()

__designer_plugins__ = [XNavigationEdit]