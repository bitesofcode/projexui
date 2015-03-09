#!/usr/bin/python

"""
Extends the base QLineEdit class to support some additional features like \
setting hints on line edits.
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

import logging

from projex.text import nativestring

from xml.etree          import ElementTree
from xml.parsers.expat  import ExpatError

from projexui.qt import unwrapVariant, wrapVariant
from projexui.qt.QtCore import QPoint,\
                               Qt,\
                               QTimer
                           
from projexui.qt.QtGui  import QCursor,\
                               QFontMetrics,\
                               QIcon,\
                               QMenu, \
                               QPainter,\
                               QToolButton,\
                               QToolTip,\
                               QLabel,\
                               QAction,\
                               QWidgetAction,\
                               QPixmap,\
                               QStyle,\
                               QWidget,\
                               QWidgetAction,\
                               QHBoxLayout

from projexui.xpainter import XPainter
from projexui.widgets.xtreewidget import XTreeWidget, XTreeWidgetItem
from projexui.widgets.xlineedit import XLineEdit
from projexui import resources

logger = logging.getLogger(__name__)

LABEL_STYLE = """\
QLabel:hover {
    background: palette(Highlight);
    border: 1px solid palette(WindowText);
}"""

#----------------------------------------------------------------------

class XAdvancedButton(QToolButton):
    pass

#----------------------------------------------------------------------

class XSearchActionWidget(QWidget):
    def __init__(self, parent, action):
        super(XSearchActionWidget, self).__init__(parent)
        
        # define custom properties
        self._initialized = False
        self._triggerText = ''
        
        # define the interface
        self._searchEdit = XLineEdit(self)
        self._searchEdit.setIcon(QIcon(resources.find('img/search.png')))
        self._searchEdit.setHint('enter search')
        self._searchEdit.setFixedHeight(24)
        
        # define the completer
        self._completer = XTreeWidget(self)
        self._completer.setHint('No actions were found.')
        self._completer.setWindowFlags(Qt.Popup)
        self._completer.setRootIsDecorated(False)
        self._completer.header().hide()
        self._completer.setSortingEnabled(True)
        self._completer.sortByColumn(0, Qt.AscendingOrder)
        self._completer.installEventFilter(self)
        self._completer.setFocusProxy(self._searchEdit)
        self._completer.setShowGrid(False)
        self._completer.setFrameShape(XTreeWidget.Box)
        self._completer.setFrameShadow(XTreeWidget.Plain)
        
        # match the look for the completer to the menu
        palette = self._completer.palette()
        palette.setColor(palette.Base, palette.color(palette.Window))
        palette.setColor(palette.Text, palette.color(palette.WindowText))
        palette.setColor(palette.WindowText, palette.color(palette.Mid))
        self._completer.setPalette(palette)
        
        # create the layout
        layout = QHBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self._searchEdit)
        self.setLayout(layout)
        
        # create connections
        self._searchEdit.textChanged.connect(self.filterOptions)
        self._completer.itemClicked.connect(self.triggerItem)
        parent.aboutToShow.connect(self.aboutToShow)
    
    def aboutToShow(self):
        """
        Processes the search widget when the menu is about to show.
        """
        self.clear()
        self._searchEdit.setFocus()
    
    def addItems(self, menus, processed=None):
        """
        Adds items to the completion tree from the menu.
        
        :param      menus | [<QMenu>, ..]
                    procesed | [<QAction>, ..] || None
        """
        if processed is None:
            processed = []
        
        for menu in menus:
            for action in menu.actions():
                # since we can have 1 action in more than 1 submenu, we
                # will want to make sure we're only adding a unique one
                # so we don't have duplicates
                text = nativestring(action.text())
                if text in processed or action.isSeparator():
                    continue
                
                processed.append(text)
                
                if text and unwrapVariant(action.data()) != 'menu':
                    item = XTreeWidgetItem(self._completer, [text])
                    item.setFixedHeight(20)
                    item.setIcon(0, action.icon())
                    item.setToolTip(0, action.toolTip())
                    item.setData(0, Qt.UserRole, wrapVariant(action))
    
    def clear(self):
        """
        Clears the text from the search edit.
        """
        self._searchEdit.blockSignals(True)
        self._searchEdit.setText('')
        self._searchEdit.blockSignals(False)
    
    def completer(self):
        """
        Returns the completion widget for this menu.
        
        :return     <projexui.widgets.xtreewidget.XTreeWidget>
        """
        return self._completer
    
    def eventFilter(self, object, event):
        """
        Listens for the key press event from the tree widget to pass along
        to the line edit.
        
        :param      object | <QWidget>
                    event  | <QEvent>
        
        :return     <bool> | consumed
        """
        if event.type() == event.KeyPress:
            if event.key() == Qt.Key_Escape:
                self._completer.hide()
                self._completer.setCurrentItem(None)

            elif event.key() in (Qt.Key_Enter, Qt.Key_Return):
                tree = self._completer
                item = tree.currentItem() or tree.itemAt(0, 0)
                self.triggerItem(item)

            self._searchEdit.keyPressEvent(event)

        return False

    def filterOptions(self, text):
        """
        Filters the searched actions based on the inputed text.
        
        :param      text | <str>
        """
        if not text:
            self._completer.hide()
            self._completer.setCurrentItem(None)
            return

        # block the signals
        self._completer.setUpdatesEnabled(False)
        self._completer.blockSignals(True)

        # initialize the actions
        menu = self.parent()
        if not self._initialized:
            self.addItems([menu] + menu.findChildren(QMenu))
            self._initialized = True

        # filter the actions in the search view
        visible_count = 0
        item_count = self._completer.topLevelItemCount()
        for i in range(item_count):
            item = self._completer.topLevelItem(i)
            check = nativestring(item.text(0)).lower()
            hidden = not nativestring(text).lower() in check
            item.setHidden(hidden)
            visible_count += 1 if not hidden else 0

        # show the popup widget if it is not visible
        if not self._completer.isVisible():
            point = QPoint(-1, self.height())
            width = menu.width()
            height = menu.height() - self.height() - 1
            height = max(height, 22 * min(visible_count, 5))
            
            self._completer.move(self.mapToGlobal(point))
            self._completer.resize(width, height)
            self._completer.show()

        # restore signals
        self._completer.setUpdatesEnabled(True)
        self._completer.blockSignals(False)

    def searchEdit(self):
        """
        Returns the line edit associated with this widget.
        
        :return     <projexui.widgets.xlineedit.XLineEdit>
        """
        return self._searchEdit
    
    def text(self):
        """
        Returns the text of the item that was triggered.
        
        :return     <str>
        """
        return self._triggerText
    
    def triggerItem(self, item):
        """
        Triggers the item by calling its action's toggled state to display or
        hide the dock panel.
        
        :param      item | <QtGui.QTreeWidgetItem>
        """
        if not item:
            return
        
        # emit the trigger action
        self._triggerText = item.text(0)
        self._completer.hide()
        self._completer.setCurrentItem(None)
        self.parent().hide()
        
        # trigger the action
        unwrapVariant(item.data(0, Qt.UserRole)).trigger()

#----------------------------------------------------------------------

class XSearchAction(QWidgetAction):
    def createWidget(self, parent):
        return XSearchActionWidget(parent, self)

#----------------------------------------------------------------------

class XMenu(QMenu):
    def __init__(self, parent=None):
        super(XMenu, self).__init__(parent)
        
        # define custom parameters
        self._acceptedAction = None
        self._showTitle     = True
        self._advancedMap   = {}
        self._customData    = {}
        self._titleHeight   = 24
        self._toolTipAction = None
        self._toolTipTimer  = QTimer(self)
        self._toolTipTimer.setInterval(1000)
        self._toolTipTimer.setSingleShot(True)
        # set default parameters
        self.setContentsMargins(0, self._titleHeight, 0, 0)
        self.setShowTitle(False)
        
        # create connections
        self.hovered.connect(self.startActionToolTip)
        self.aboutToShow.connect(self.clearAcceptedAction)
        self._toolTipTimer.timeout.connect(self.showActionToolTip)
    
    def acceptAdvanced(self):
        self._acceptedAction = self.sender().defaultAction()
        self.close()
    
    def acceptedAction(self):
        return self._acceptedAction
    
    def addMenu(self, submenu):
        """
        Adds a new submenu to this menu.  Overloads the base QMenu addMenu \
        method so that it will return an XMenu instance vs. a QMenu when \
        creating a submenu by passing in a string.
        
        :param      submenu | <str> || <QMenu>
        
        :return     <QMenu>
        """
        # create a new submenu based on a string input
        if not isinstance(submenu, QMenu):
            title = nativestring(submenu)
            submenu = XMenu(self)
            submenu.setTitle(title)
            submenu.setShowTitle(self.showTitle())
            super(XMenu, self).addMenu(submenu)
        else:
            super(XMenu, self).addMenu(submenu)
        
        submenu.menuAction().setData(wrapVariant('menu'))
        
        return submenu
    
    def addSearchAction(self):
        """
        Adds a search action that will allow the user to search through
        the actions and sub-actions within in this menu.
        
        :return     <XSearchAction>
        """
        action = XSearchAction(self)
        self.addAction(action)
        return action
    
    def addSection(self, section):
        """
        Adds a section to this menu.  A section will create a label for the
        menu to separate sections of the menu out.
        
        :param      section | <str>
        """
        label = QLabel(section, self)
        label.setMinimumHeight(self.titleHeight())
        
        # setup font
        font = label.font()
        font.setBold(True)
        
        # setup palette
        palette = label.palette()
        palette.setColor(palette.WindowText, palette.color(palette.Mid))
        
        # setup label
        label.setFont(font)
        label.setAutoFillBackground(True)
        label.setPalette(palette)
        
        # create the widget action
        action = QWidgetAction(self)
        action.setDefaultWidget(label)
        self.addAction(action)
        
        return action
    
    def adjustMinimumWidth( self ):
        """
        Updates the minimum width for this menu based on the font metrics \
        for its title (if its shown).  This method is called automatically \
        when the menu is shown.
        """
        if not self.showTitle():
            return
        
        metrics = QFontMetrics(self.font())
        width   = metrics.width(self.title()) + 20
        
        if self.minimumWidth() < width:
            self.setMinimumWidth(width)
        
    def clearAdvancedActions( self ):
        """
        Clears out the advanced action map.
        """
        self._advancedMap.clear()
        margins     = list(self.getContentsMargins())
        margins[2]  = 0
        self.setContentsMargins(*margins)
    
    def clearAcceptedAction(self):
        self._acceptedAction = None
    
    def customData( self, key, default = None ):
        """
        Returns data that has been stored on this menu.
        
        :param      key     | <str>
                    default | <variant>
        
        :return     <variant>
        """
        key     = nativestring(key)
        menu    = self
        while (not key in menu._customData and \
               isinstance(menu.parent(), XMenu)):
            menu = menu.parent()
        
        return menu._customData.get(nativestring(key), default)
    
    def paintEvent( self, event ):
        """
        Overloads the paint event for this menu to draw its title based on its \
        show title property.
        
        :param      event | <QPaintEvent>
        """
        super(XMenu, self).paintEvent(event)
        
        if self.showTitle():
            with XPainter(self) as painter:
                palette = self.palette()
                
                painter.setBrush(palette.color(palette.Button))
                painter.setPen(Qt.NoPen)
                painter.drawRect(1, 1, self.width() - 2, 22)
                
                painter.setBrush(Qt.NoBrush)
                painter.setPen(palette.color(palette.ButtonText))
                painter.drawText(1, 1, self.width() - 2, 22, 
                                 Qt.AlignCenter, self.title())
    
    def rebuildButtons(self):
        """
        Rebuilds the buttons for the advanced actions.
        """
        for btn in self.findChildren(XAdvancedButton):
            btn.close()
            btn.setParent(None)
            btn.deleteLater()
        
        for standard, advanced in self._advancedMap.items():
            rect    = self.actionGeometry(standard)
            btn     = XAdvancedButton(self)
            btn.setFixedWidth(22)
            btn.setFixedHeight(rect.height())
            btn.setDefaultAction(advanced)
            btn.setAutoRaise(True)
            btn.move(rect.right() + 1, rect.top())
            btn.show()
            
            if btn.icon().isNull():
                btn.setIcon(QIcon(resources.find('img/advanced.png')))
            
            btn.clicked.connect(self.acceptAdvanced)
    
    def setAdvancedAction(self, standardAction, advancedAction):
        """
        Links an advanced action with the inputed standard action.  This will \
        create a tool button alongside the inputed standard action when the \
        menu is displayed.  If the user selects the advanced action, then the \
        advancedAction.triggered signal will be emitted.
        
        :param      standardAction | <QAction>
                    advancedAction | <QAction> || None
        """
        if advancedAction:
            self._advancedMap[standardAction] = advancedAction
            margins     = list(self.getContentsMargins())
            margins[2]  = 22
            self.setContentsMargins(*margins)
            
        elif standardAction in self._advancedMap:
            self._advancedMap.pop(standardAction)
            if not self._advancedMap:
                margins     = list(self.getContentsMargins())
                margins[2]  = 22
                self.setContentsMargins(*margins)
    
    def setCustomData( self, key, value ):
        """
        Sets custom data for the developer on this menu instance.
        
        :param      key     | <str>
                    value | <variant>
        """
        self._customData[nativestring(key)] = value
        
    def setShowTitle( self, state ):
        """
        Sets whether or not the title for this menu should be displayed in the \
        popup.
        
        :param      state | <bool>
        """
        self._showTitle = state
        
        margins = list(self.getContentsMargins())
        if state:
            margins[1] = self.titleHeight()
        else:
            margins[1] = 0
        
        self.setContentsMargins(*margins)
    
    def showEvent(self, event):
        """
        Overloads the set visible method to update the advanced action buttons \
        to match their corresponding standard action location.
        
        :param      state | <bool>
        """
        super(XMenu, self).showEvent(event)
        
        self.adjustSize()
        self.adjustMinimumWidth()
        self.rebuildButtons()
    
    def setTitleHeight(self, height):
        """
        Sets the height for the title of this menu bar and sections.
        
        :param      height | <int>
        """
        self._titleHeight = height
    
    def showActionToolTip(self):
        """
        Shows the tool tip of the action that is currently being hovered over.
        
        :param      action | <QAction>
        """
        if ( not self.isVisible() ):
            return
            
        geom  = self.actionGeometry(self._toolTipAction)
        pos   = self.mapToGlobal(QPoint(geom.left(), geom.top()))
        pos.setY(pos.y() + geom.height())
        
        tip   = nativestring(self._toolTipAction.toolTip()).strip().strip('.')
        text  = nativestring(self._toolTipAction.text()).strip().strip('.')
        
        # don't waste time showing the user what they already see
        if ( tip == text ):
            return
        
        QToolTip.showText(pos, self._toolTipAction.toolTip())
    
    def showTitle( self ):
        """
        Returns whether or not this menu should show the title in the popup.
        
        :return     <bool>
        """
        return self._showTitle
    
    def startActionToolTip( self, action ):
        """
        Starts the timer to hover over an action for the current tool tip.
        
        :param      action | <QAction>
        """
        self._toolTipTimer.stop()
        QToolTip.hideText()
        
        if not action.toolTip():
            return
        
        self._toolTipAction = action
        self._toolTipTimer.start()
    
    def titleHeight(self):
        """
        Returns the height for the title of this menu bar and sections.
        
        :return     <int>
        """
        return self._titleHeight
    
    def updateCustomData( self, data ):
        """
        Updates the custom data dictionary with the inputed data.
        
        :param      data | <dict>
        """
        if ( not data ):
            return
            
        self._customData.update(data)
    
    @staticmethod
    def fromString( parent, xmlstring, actions = None ):
        """
        Loads the xml string as xml data and then calls the fromXml method.
        
        :param      parent | <QWidget>
                    xmlstring | <str>
                    actions     | {<str> name: <QAction>, .. } || None
        
        :return     <XMenu> || None
        """
        try:
            xdata = ElementTree.fromstring(xmlstring)
            
        except ExpatError, e:
            logger.exception(e)
            return None
        
        return XMenu.fromXml(parent, xdata, actions)
    
    @staticmethod
    def fromXml( parent, xml, actions = None ):
        """
        Generates an XMenu from the inputed xml data and returns the resulting \
        menu.  If no action dictionary is supplied, it will be generated based \
        on the parents actions.
        
        :param      parent      | <QWidget>
                    xml         | <xml.etree.ElementTree.Element>
                    actions     | {<str> name: <QAction>, } || None
        
        :return     <XMenu> || None
        """
        # generate the actions off the parent
        if ( actions is None ):
            actions = {}
            for action in parent.actions():
                key = nativestring(action.objectName())
                if not key:
                    key = nativestring(action.text())
                
                if not key:
                    continue
                
                actions[key] = action
        
        # create a new menu
        menu = XMenu(parent)
        menu.setIcon(QIcon(resources.find('img/folder.png')))
        menu.setTitle(xml.get('title', '')) 
        
        for xaction in xml:
            if xaction.tag == 'separator':
                menu.addSeparator()
            elif xaction.tag == 'menu':
                menu.addMenu(XMenu.fromXml(menu, xaction, actions))
            else:
                action = actions.get(xaction.get('name', ''))
                if action:
                    menu.addAction(action)
        
        return menu