#!/usr/bin python

""" Defines the main panel widget. """

# define authorship information
__authors__     = ['Eric Hulser']
__author__      = ','.join(__authors__)
__credits__     = []
__copyright__   = 'Copyright (c) 2011, Projex Software'

# maintanence information
__maintainer__  = 'Projex Software'
__email__       = 'team@projexsoftware.com'

import logging
import projexui

from projexui import resources
from projexui.widgets.xdropzonewidget import XDropZoneWidget
from projexui.widgets.xviewwidget.xview import XView
from projexui.widgets.xsplitter import XSplitter
from projexui.widgets.xtoolbutton import XToolButton
from projexui.widgets.xlabel import XLabel
from projexui.widgets.xlabel import XLabel
from xqt import QtCore, QtGui

MAX_INT = 2**16
log = logging.getLogger(__name__)

class XViewPanelItem(QtGui.QWidget):
    def __init__(self, title, parent=None):
        super(XViewPanelItem, self).__init__(parent)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # define custom properties
        self._dragLabel = QtGui.QLabel(self)
        self._dragLabel.setFixedWidth(12)
        self._dragLabel.setToolTip(self.tr('Drag this view into another panel.'))

        self._spacer = QtGui.QWidget(self)
        self._spacer.setFixedWidth(12)

        self._titleLabel = XLabel(self)
        self._titleLabel.setText(title)
        self._titleLabel.setEditable(True)
        self._hovered = False

        palette = self.palette()
        palette.setColor(palette.Shadow, palette.color(palette.Window).darker(175))

        self._searchButton = XToolButton(self)
        self._searchButton.setIcon(QtGui.QIcon(resources.find('img/treeview/triangle_down.png')))
        self._searchButton.setIconSize(QtCore.QSize(10, 10))
        self._searchButton.setFixedWidth(16)
        self._searchButton.setShadowed(True)
        self._searchButton.setPalette(palette)
        self._searchButton.setHoverable(True)
        self._searchButton.setToolTip(self.tr('Switch the current view.'))

        self._closeButton = XToolButton(self)
        self._closeButton.setIcon(QtGui.QIcon(resources.find('img/remove_dark.png')))
        self._closeButton.setIconSize(QtCore.QSize(10, 10))
        self._closeButton.setFixedWidth(16)
        self._closeButton.setHoverable(True)
        self._closeButton.setShadowed(True)
        self._closeButton.setPalette(palette)
        self._closeButton.setToolTip(self.tr('Close down this view.'))

        # create the layout
        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0, 1, 0, 1)
        layout.setSpacing(0)
        layout.addWidget(self._dragLabel)
        layout.addWidget(self._searchButton)
        layout.addWidget(self._titleLabel)
        layout.addWidget(self._spacer)
        layout.addWidget(self._closeButton)
        self.setLayout(layout)

        # create connections
        self._closeButton.clicked.connect(self.closeTab)
        self._searchButton.clicked.connect(self.showTabMenu)

    def activate(self):
        """
        Activates this item.
        """
        self.parent().setCurrentItem(self)

    def closeTab(self):
        self.parent().closeTab(self)

    def enterEvent(self, event):
        """
        Mark the hovered state as being true.

        :param      event | <QtCore.QEnterEvent>
        """
        super(XViewPanelItem, self).enterEvent(event)

        # store the hover state and mark for a repaint
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        """
        Mark the hovered state as being false.

        :param      event | <QtCore.QLeaveEvent>
        """
        super(XViewPanelItem, self).leaveEvent(event)

        # store the hover state and mark for a repaint
        self._hovered = False
        self.update()

    def isActive(self):
        """
        Returns whether or not this is the active item.

        :return     <bool>
        """
        return self.parent().currentItem() == self

    def paintEvent(self, event):
        """
        Runs the paint event for this item.
        """
        painter = QtGui.QPainter()
        painter.begin(self)
        try:
            x = 0
            y = 2
            w = self.width() - 1
            h = self.height() - 3
            palette = self.palette()
            clr = palette.color(palette.WindowText)
            clr.setAlpha(100)
            painter.setPen(QtGui.QPen(clr))

            if not self.isActive() and not self._hovered:
                painter.setBrush(palette.color(palette.Button))
            else:
                painter.setBrush(palette.color(palette.Window))

            painter.fillRect(x, y, w, h, painter.brush())
            painter.drawLine(x, y, w, y)
            painter.drawLine(w, y, w, h + 2)

            if self.parent().indexOf(self) == 0:
                painter.drawLine(x, y, x, h + 2)


            # draw the drag buttons
            center = self._dragLabel.geometry().center()
            x = center.x()
            y = center.y()
            width = 3

            painter.setBrush(palette.color(palette.Window).lighter(120))

            painter.drawRect(x - width / 2, (y - width - 2) - width / 2, width, width)
            painter.drawRect(x - width / 2, y - width / 2, width, width)
            painter.drawRect(x - width / 2, (y + width + 2) - width / 2, width, width)

        finally:
            painter.end()

    def mousePressEvent(self, event):
        """
        Creates the mouse event for dragging or activating this tab.

        :param      event | <QtCore.QMousePressEvent>
        """
        if self._dragLabel.geometry().contains(event.pos()):
            tabbar = self.parent()
            panel = tabbar.parent()

            index = tabbar.indexOf(self)
            view = panel.widget(index)
            pixmap = QtGui.QPixmap.grabWidget(view)

            drag = QtGui.QDrag(panel)
            data = QtCore.QMimeData()
            data.setData('x-application/xview/tabbed_view',
                         QtCore.QByteArray(str(index)))
            drag.setMimeData(data)
            drag.setPixmap(pixmap)

            orig_parent = view.parent()
            reshow = False
            if self.isActive():
                view.hide()
                reshow = True

            if not drag.exec_():
                cursor = QtGui.QCursor.pos()
                geom = self.window().geometry()
                if not geom.contains(cursor):
                    view.popout()
                elif reshow:
                    view.show()
            elif reshow:
                view.show()

            #if view.parent() != orig_parent:
            #    self.parent().removeTab(index)
        else:
            self.activate()

        super(XViewPanelItem, self).mousePressEvent(event)

    def setFixedHeight(self, height):
        """
        Sets the fixed height for this item to the inputed height amount.

        :param      height | <int>
        """
        super(XViewPanelItem, self).setFixedHeight(height)

        self._dragLabel.setFixedHeight(height)
        self._titleLabel.setFixedHeight(height)
        self._searchButton.setFixedHeight(height)
        self._closeButton.setFixedHeight(height)

    def setText(self, text):
        """
        Sets the title for this panel item.

        :param      title | <str>
        """
        self._titleLabel.setText(text)

    def showTabMenu(self):
        point = self._searchButton.mapToGlobal(QtCore.QPoint(0, self._searchButton.height()))
        self.parent().showTabMenuRequested.emit(point)

    def text(self):
        """
        Returns the title with this item.

        :return     <str>
        """
        return self._titleLabel.text().strip()

#-----------------------------------------

class XViewPanelBar(QtGui.QWidget):
    addRequested = QtCore.Signal(QtCore.QPoint)
    optionsRequested = QtCore.Signal(QtCore.QPoint)
    currentIndexChanged = QtCore.Signal(int)
    splitVerticalRequested = QtCore.Signal()
    splitHorizontalRequested = QtCore.Signal()
    showTabMenuRequested = QtCore.Signal(QtCore.QPoint)
    tabCloseRequested = QtCore.Signal(int)

    def __init__(self, parent=None):
        super(XViewPanelBar, self).__init__(parent)

        # create the add button
        self.setFixedHeight(22)

        self._currentIndex = -1

        # create the split buttons
        palette = self.palette()
        palette.setColor(palette.Shadow, palette.color(palette.Window).darker(175))

        self._addButton = XToolButton(self)
        self._addButton.setIcon(QtGui.QIcon(resources.find('img/view/add_dark.png')))
        self._addButton.setShadowed(True)
        self._addButton.setFixedWidth(18)
        self._addButton.setIconSize(QtCore.QSize(16, 16))
        self._addButton.setPalette(palette)

        self._horizontalButton = XToolButton(self)
        self._horizontalButton.setIcon(QtGui.QIcon(resources.find('img/view/split_horizontal.png')))
        self._horizontalButton.setShadowed(True)
        self._horizontalButton.setIconSize(QtCore.QSize(16, 16))
        self._horizontalButton.setFixedWidth(18)
        self._horizontalButton.setPalette(palette)

        self._verticalButton = XToolButton(self)
        self._verticalButton.setIcon(QtGui.QIcon(resources.find('img/view/split_vertical.png')))
        self._verticalButton.setShadowed(True)
        self._verticalButton.setIconSize(QtCore.QSize(16, 16))
        self._verticalButton.setFixedWidth(18)
        self._verticalButton.setPalette(palette)

        # create the options button
        self._optionsButton = XToolButton(self)
        self._optionsButton.setIcon(QtGui.QIcon(resources.find('img/config.png')))
        self._optionsButton.setShadowed(True)
        self._optionsButton.setIconSize(QtCore.QSize(16, 16))
        self._optionsButton.setFixedWidth(18)
        self._optionsButton.setPalette(palette)

        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(6, 0, 6, 0)
        layout.addWidget(self._addButton)
        layout.setSpacing(0)
        layout.addStretch()
        layout.addWidget(self._horizontalButton)
        layout.addWidget(self._verticalButton)
        layout.addWidget(self._optionsButton)
        self.setLayout(layout)

        # create connections
        self._addButton.clicked.connect(self.requestAddMenu)
        self._optionsButton.clicked.connect(self.requestOptionsMenu)
        self._horizontalButton.clicked.connect(self.splitHorizontalRequested)
        self._verticalButton.clicked.connect(self.splitVerticalRequested)

    def addButton(self):
        return self._addButton

    def addTab(self, text):
        """
        Adds a new tab to this panel bar.

        :param      text | <str>

        :return     <int>
        """
        item = XViewPanelItem(text, self)
        item.setFixedHeight(self.height())

        index = len(self.items())
        self.layout().insertWidget(index, item)

        self.setCurrentIndex(index)

    def clear(self):
        """
        Clears out all the items from this tab bar.
        """
        self.blockSignals(True)
        items = list(self.items())
        for item in items:
            item.close()
        self.blockSignals(False)

        self._currentIndex = -1
        self.currentIndexChanged.emit(self._currentIndex)

    def closeTab(self, item):
        """
        Requests a close for the inputed tab item.

        :param      item | <XViewPanelItem>
        """
        index = self.indexOf(item)
        if index != -1:
            self.tabCloseRequested.emit(index)

    def count(self):
        """
        Returns the number of items within this panel.

        :return     <int>
        """
        return len(self.items())

    def currentIndex(self):
        """
        Returns the index of the active item.

        :return     <int>
        """
        return self._currentIndex

    def currentItem(self):
        """
        Returns the current item associated with this panel.

        :return     <XViewPanelItem> || None
        """
        try:
            return self.layout().itemAt(self.currentIndex()).widget()
        except StandardError:
            return None

    def indexOf(self, item):
        """
        Returns the index of the inputed item.

        :return     <int>
        """
        try:
            return list(self.items()).index(item)
        except StandardError:
            return -1

    def insertTab(self, index, text):
        """
        Adds a new tab to this panel bar.

        :param      text | <str>

        :return     <int>
        """
        item = XViewPanelItem(text, self)
        item.setFixedHeight(self.height())

        self.layout().insertWidget(index, item)

        self.setCurrentIndex(index)

    def items(self):
        """
        Returns a list of all the items associated with this panel.

        :return     [<XViewPanelItem>, ..]
        """
        output = []
        for i in xrange(self.layout().count()):
            item = self.layout().itemAt(i)
            try:
                widget = item.widget()
            except AttributeError:
                break

            if isinstance(widget, XViewPanelItem):
                output.append(widget)
            else:
                break
        return output

    def moveTab(self, fromIndex, toIndex):
        """
        Moves the tab from the inputed index to the given index.

        :param      fromIndex | <int>
                    toIndex   | <int>
        """
        try:
            item = self.layout().itemAt(fromIndex)
            self.layout().insertItem(toIndex, item.widget())
        except StandardError:
            pass

    def paintEvent(self, event):
        """
        Runs the paint event for this item.
        """
        painter = QtGui.QPainter()
        painter.begin(self)
        try:
            h = self.height() - 1
            palette = self.palette()
            clr = palette.color(palette.WindowText)
            clr.setAlpha(100)
            painter.setPen(QtGui.QPen(clr))
            painter.fillRect(0, 0, self.width() - 1, self.height() - 1, palette.color(palette.Button))
            painter.drawLine(3, h, self.width() - 5, h)

            try:
                geom = self.currentItem().geometry()
                painter.setPen(QtGui.QPen(palette.color(palette.Window)))
                painter.drawLine(geom.left(), h, geom.right(), h)
            except AttributeError:
                painter

        finally:
            painter.end()

    def removeTab(self, index):
        """
        Removes the tab at the inputed index.

        :param      index | <int>
        """
        curr_index = self.currentIndex()
        items = list(self.items())

        item = items[index]
        item.close()
        if index <= curr_index:
            self._currentIndex -= 1

    def requestAddMenu(self):
        """
        Emits the add requested signal.
        """
        point = QtCore.QPoint(self._addButton.width(), 0)
        point = self._addButton.mapToGlobal(point)
        self.addRequested.emit(point)

    def requestOptionsMenu(self):
        """
        Emits the options request signal.
        """
        point = QtCore.QPoint(0, self._optionsButton.height())
        point = self._optionsButton.mapToGlobal(point)
        self.optionsRequested.emit(point)

    def setCurrentIndex(self, index):
        """
        Sets the current item to the item at the inputed index.

        :param      index | <int>
        """
        if self._currentIndex == index:
            return

        self._currentIndex = index
        self.currentIndexChanged.emit(index)

    def setCurrentItem(self, item):
        """
        Sets the current item to the inputed widget.

        :param      item | <XViewPanelItem>
        """
        self.setCurrentIndex(self.layout().indexOf(item))

    def setFixedHeight(self, height):
        """
        Sets the fixed height for this bar to the inputed height.

        :param      height | <int>
        """
        super(XViewPanelBar, self).setFixedHeight(height)

        # update the layout
        if self.layout():
            for i in xrange(self.layout().count()):
                try:
                    self.layout().itemAt(i).widget().setFixedHeight(height)
                except StandardError:
                    continue

    def setTabText(self, index, text):
        """
        Returns the text for the tab at the inputed index.

        :param      index | <int>

        :return     <str>
        """
        try:
            self.items()[index].setText(text)
        except IndexError:
            pass

    def tabText(self, index):
        """
        Returns the text for the tab at the inputed index.

        :param      index | <int>

        :return     <str>
        """
        try:
            return self.items()[index].text()
        except IndexError:
            return ''

#-----------------------------------------

class XViewPanel(QtGui.QStackedWidget):
    def __init__(self, parent, locked=True):
        # initialize the super class
        super(XViewPanel, self).__init__(parent)

        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        # create custom properties
        self._tabBar = XViewPanelBar(self)
        self._tabBar.show()
        self._locked = locked
        self._hideTabsWhenLocked = True

        self._hintLabel = QtGui.QLabel(self)
        self._hintLabel.setAlignment(QtCore.Qt.AlignCenter)
        self._hintLabel.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self._hintLabel.setFocusPolicy(QtCore.Qt.NoFocus)
        self._hintLabel.setWordWrap(True)
        self._hintLabel.setMargin(10)

        # create actions
        add_tab_action = QtGui.QAction(self)
        add_tab_action.setShortcut(QtGui.QKeySequence('Ctrl+t'))
        add_tab_action.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
        self.addAction(add_tab_action)

        remove_tab_action = QtGui.QAction(self)
        remove_tab_action.setShortcut(QtGui.QKeySequence('Ctrl+w'))
        remove_tab_action.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
        self.addAction(remove_tab_action)

        close_panel_action = QtGui.QAction(self)
        close_panel_action.setShortcut(QtGui.QKeySequence('Ctrl+Shift+w'))
        close_panel_action.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
        self.addAction(close_panel_action)

        split_horizontal = QtGui.QAction(self)
        split_horizontal.setShortcut(QtGui.QKeySequence('Ctrl+Shift+h'))
        split_horizontal.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
        self.addAction(split_horizontal)

        split_vertical = QtGui.QAction(self)
        split_vertical.setShortcut(QtGui.QKeySequence('Ctrl+Shift+v'))
        split_vertical.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
        self.addAction(split_vertical)
        
        # set the size policy for this widget to always maximize space
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        
        self.setSizePolicy(sizePolicy)
        self.setAcceptDrops(True)
        self.setContentsMargins(6, self._tabBar.height(), 6, 6)
        
        # create the drop zone widget
        self._dropZone = XDropZoneWidget(self)
        self._dropZone.addRegion('top',          'Add Row',      0, 2)
        self._dropZone.addRegion('split_up',     'Split Above',  1, 2)
        self._dropZone.addRegion('left',         'Add Column',   2, 0)
        self._dropZone.addRegion('split_left',   'Split Left',   2, 1)
        self._dropZone.addRegion('center',       'Add Tab',      2, 2)
        self._dropZone.addRegion('split_right',  'Split Right',  2, 3)
        self._dropZone.addRegion('right',        'Add Column',   2, 4)
        self._dropZone.addRegion('split_down',   'Split Below',  3, 2)
        self._dropZone.addRegion('bottom',       'Add Row',      4, 2)
        self._dropZone.setRowStretch(2, 1)
        self._dropZone.setColumnStretch(2, 1)
        
        filt = lambda ev: (ev.mimeData().hasFormat('x-application/xview/tabbed_view') or \
                           ev.mimeData().hasFormat('x-application/xview/floating_view')) and \
                           ev.source().viewWidget() == self.viewWidget()
        
        self._dropZone.setFilter(filt)
        
        # update the tab bar
        self.currentChanged.connect(self.markCurrentChanged)
        self.widgetRemoved.connect(self.tabBar().removeTab)

        # connect tab bar
        self.tabBar().currentIndexChanged.connect(self.setCurrentIndex)
        self.tabBar().tabCloseRequested.connect(self.closeView)
        self.tabBar().addRequested.connect(self.showAddMenu)
        self.tabBar().optionsRequested.connect(self.showOptionsMenu)
        self.tabBar().splitHorizontalRequested.connect(self.splitHorizontal)
        self.tabBar().splitVerticalRequested.connect(self.splitVertical)
        self.tabBar().showTabMenuRequested.connect(self.showTabMenu)

        # connect actions
        add_tab_action.triggered.connect(self.showAddMenu)
        remove_tab_action.triggered.connect(self.closeView)
        split_vertical.triggered.connect(self.splitVertical)
        split_horizontal.triggered.connect(self.splitHorizontal)
        close_panel_action.triggered.connect(self.closePanel)
    
    def addPanel(self, orientation, before=False):
        # look up the splitter for the widget
        widget = self
        splitter = widget.parent()
        while widget and isinstance(splitter, XSplitter):
            if splitter.orientation() == orientation:
                break
            
            widget = splitter
            splitter = splitter.parent()
        
        # we've hit the top without finding a splitter with our orientation
        # so we need to create one
        if not isinstance(splitter, XSplitter):
            # split from a parent's layout
            w       = widget.width()
            h       = widget.height()
            
            if orientation == QtCore.Qt.Horizontal:
                size = w / 2
            else:
                size = h / 2
            
            parent = splitter
            
            area = parent.parent()
            area.takeWidget()
            
            # create the splitter
            splitter = XSplitter(orientation, parent)
            
            # split with a new view
            new_panel = XViewPanel(splitter, self.isLocked())
            
            if before:
                splitter.addWidget(new_panel)
                splitter.addWidget(widget)
            else:
                splitter.addWidget(widget)
                splitter.addWidget(new_panel)
            
            splitter.setSizes([size, size])
            
            sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,
                                           QtGui.QSizePolicy.Expanding)
            sizePolicy.setHorizontalStretch(1)
            sizePolicy.setVerticalStretch(1)
            
            splitter.setSizePolicy(sizePolicy)
            area.setWidget(splitter)
            return new_panel
        
        ewidgets = (self, self.parentWidget(), self.window())
        for w in ewidgets:
            w.setUpdatesEnabled(False)
        
        sizes = splitter.sizes()
        total = sum(sizes)
        if total == 0:
            total = 1
            
        percents    = [float(size)/total for size in sizes]
        newpercent  = 1.0/(len(sizes)+1)
        newsize     = newpercent * total
        newsizes    = []
        
        for i, percent in enumerate(percents):
            newsizes.append((total * percent) - sizes[i] * newpercent)
        
        newsizes.append(newsize)
        
        panel = XViewPanel(splitter, self.isLocked())
        
        # determine the new location for the panel
        index = splitter.indexOf(widget)
        if before:
            splitter.insertWidget(index, panel)
        else:
            splitter.insertWidget(index + 1, panel)
        
        splitter.setSizes(newsizes)
        
        for w in ewidgets:
            w.setUpdatesEnabled(True)
        
        return panel
    
    def addTab(self, view, title):
        """
        Adds a new view tab to this panel.
        
        :param      view    | <XView>
                    title   | <str>
        
        :return     <bool> | success
        """
        if not isinstance(view, XView):
            return False

        self._tabBar.addTab(title)
        self.addWidget(view)
        
        # create connections
        try:
            view.windowTitleChanged.connect(self.refreshTitles,
                                            QtCore.Qt.UniqueConnection)
            view.sizeConstraintChanged.connect(self.adjustSizeConstraint,
                                            QtCore.Qt.UniqueConnection)
            view.poppedOut.connect(self.disconnectView,
                                   QtCore.Qt.UniqueConnection)
        except RuntimeError:
            pass
        
        self.setCurrentIndex(self.count() - 1)
        
        return True
    
    def addView(self, viewType):
        """
        Adds a new view of the inputed view type.
        
        :param      viewType | <subclass of XView>
        
        :return     <XView> || None
        """
        if not viewType:
            return None
        
        view = viewType.createInstance(self, self.viewWidget())
        self.addTab(view, view.windowTitle())
        return view
    
    def adjustSizeConstraint(self):
        """
        Adjusts the min/max size based on the current tab.
        """
        widget = self.currentWidget()
        if not widget:
            return
            
        offw = 4
        offh = 4
        
        #if self.tabBar().isVisible():
        #    offh += 20 # tab bar height
        
        minw = min(widget.minimumWidth() + offw,   MAX_INT)
        minh = min(widget.minimumHeight() + offh,  MAX_INT)
        maxw = min(widget.maximumWidth() + offw,   MAX_INT)
        maxh = min(widget.maximumHeight() + offh,  MAX_INT)
        
        self.setMinimumSize(minw, minh)
        self.setMaximumSize(maxw, maxh)
        self.setSizePolicy(widget.sizePolicy())

    def closeEvent(self, event):
        # don't process anything after close
        self.currentChanged.disconnect()

        super(XViewPanel, self).closeEvent(event)

    def closeView(self, view=None):
        """
        Closes the inputed view.
        
        :param      view | <int> || <XView> || None
        """
        if type(view) == int:
            view = self.widget(view)
        elif view == None:
            view = self.currentView()
        
        index = self.indexOf(view)
        if index == -1:
            return False
        
        # close the view
        count = self.count()
        if count == 1:
            self.closePanel()
        else:
            view.close()

        return True
    
    def closePanel(self):
        """
        Closes a full view panel.
        """
        # make sure we can close all the widgets in the view first
        for i in range(self.count()):
            if not self.widget(i).canClose():
                return False

        container = self.parentWidget()
        viewWidget = self.viewWidget()

        # close all the child views
        for i in xrange(self.count() - 1, -1, -1):
            self.widget(i).close()

        self.tabBar().clear()

        if isinstance(container, XSplitter):
            parent_container = container.parentWidget()
            
            if container.count() == 2:
                if isinstance(parent_container, XSplitter):
                    sizes = parent_container.sizes()
                    widget = container.widget(int(not container.indexOf(self)))
                    index = parent_container.indexOf(container)
                    parent_container.insertWidget(index, widget)
                    
                    container.setParent(None)
                    container.close()
                    container.deleteLater()
                    
                    parent_container.setSizes(sizes)
                
                elif parent_container.parentWidget() == viewWidget:
                    widget = container.widget(int(not container.indexOf(self)))
                    widget.setParent(viewWidget)
                    
                    if projexui.QT_WRAPPER == 'PySide':
                        _ = viewWidget.takeWidget()
                    else:
                        old_widget = viewWidget.widget()
                        old_widget.setParent(None)
                        old_widget.close()
                        old_widget.deleteLater()
                        QtGui.QApplication.instance().processEvents()
                    
                    viewWidget.setWidget(widget)
            else:
                container.setParent(None)
                container.close()
                container.deleteLater()
        else:
            self.setFocus()

        self._hintLabel.setText(self.hint())
        self._hintLabel.show()

        return True
        
    def currentView(self):
        """
        Returns the current view for this panel.
        
        :return     <XView> || None
        """
        widget = self.currentWidget()
        if isinstance(widget, XView):
            return widget
        return None
    
    def disconnectView(self):
        view = self.sender()
        if not view:
            return
        
        try:
            view.windowTitleChanged.disconnect(self.refreshTitles)
            view.sizeConstraintChanged.disconnect(self.adjustSizeConstraint)
            view.poppedOut.disconnect(self.disconnectView)
        except RuntimeError:
            pass
        
        if not self.count():
            self.closePanel()
    
    def dragEnterEvent(self, event):
        data = event.mimeData()
        if data.hasFormat('x-application/xview/tabbed_view') or \
           data.hasFormat('x-application/xview/floating_view'):
            if event.source().viewWidget() == self.viewWidget():
                event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        data = event.mimeData()
        if data.hasFormat('x-application/xview/tabbed_view') or \
           data.hasFormat('x-application/xview/floating_view'):
            if event.source().viewWidget() == self.viewWidget():
                event.acceptProposedAction()
    
    def dropEvent(self, event):
        region = self._dropZone.currentRegion()
        if not region:
            area = 'center'
        else:
            area = region.objectName()
        
        data = event.mimeData()
        if data.hasFormat('x-application/xview/tabbed_view'):
            index = int(data.data('x-application/xview/tabbed_view'))
            
            if area == 'center':
                if event.source() != self:
                    self.snagViewFromPanel(event.source(), index)
            
            elif area == 'split_left':
                panel = self.split(QtCore.Qt.Horizontal, before=True, autoCreateView=False)
                panel.snagViewFromPanel(event.source(), index)
            
            elif area == 'left':
                panel = self.addPanel(QtCore.Qt.Horizontal, before=True)
                panel.snagViewFromPanel(event.source(), index)
            
            elif area == 'right':
                panel = self.addPanel(QtCore.Qt.Horizontal)
                panel.snagViewFromPanel(event.source(), index)
            
            elif area == 'split_right':
                panel = self.split(QtCore.Qt.Horizontal, autoCreateView=False)
                panel.snagViewFromPanel(event.source(), index)
            
            elif area == 'top':
                panel = self.addPanel(QtCore.Qt.Vertical, before=True)
                panel.snagViewFromPanel(event.source(), index)
            
            elif area == 'split_up':
                panel = self.split(QtCore.Qt.Vertical, before=True, autoCreateView=False)
                panel.snagViewFromPanel(event.source(), index)
            
            elif area == 'bottom':
                panel = self.addPanel(QtCore.Qt.Vertical)
                panel.snagViewFromPanel(event.source(), index)
            
            elif area == 'split_down':
                panel = self.split(QtCore.Qt.Vertical, autoCreateView=False)
                panel.snagViewFromPanel(event.source(), index)
        
        elif data.hasFormat('x-application/xview/floating_view'):
            view = event.source()
            view.setWindowFlags(QtCore.Qt.Widget)
            
            if area == 'center':
                self.addTab(view, view.windowTitle())
            
            elif area == 'split_left':
                panel = self.split(QtCore.Qt.Horizontal, before=True, autoCreateView=False)
                panel.addTab(view, view.windowTitle())
            
            elif area == 'left':
                panel = self.addPanel(QtCore.Qt.Horizontal, before=True)
                panel.addTab(view, view.windowTitle())
            
            elif area == 'split_right':
                panel = self.split(QtCore.Qt.Horizontal, autoCreateView=False)
                panel.addTab(view, view.windowTitle())
            
            elif area == 'right':
                panel = self.addPanel(QtCore.Qt.Horizontal)
                panel.addTab(view, view.windowTitle())
            
            elif area == 'split_up':
                panel = self.split(QtCore.Qt.Vertical, before=True, autoCreateView=False)
                panel.addTab(view, view.windowTitle())
            
            elif area == 'top':
                panel = self.addPanel(QtCore.Qt.Vertical, before=True)
                panel.addTab(view, view.windowTitle())
            
            elif area == 'split_down':
                panel = self.split(QtCore.Qt.Vertical, autoCreateView=False)
                panel.addTab(view, view.windowTitle())
            
            elif area == 'bottom':
                panel = self.addPanel(QtCore.Qt.Vertical)
                panel.addTab(view, view.windowTitle())
    
    def eventFilter(self, object, event):
        if event.type() == event.MouseButtonPress:
            if self.isLocked():
                return False
            
            if event.button() == QtCore.Qt.MidButton or \
               (event.button() == QtCore.Qt.LeftButton and \
                event.modifiers() == QtCore.Qt.ShiftModifier):
                index = self.tabBar().tabAt(event.pos())
                view  = self.widget(index)
                pixmap = QtGui.QPixmap.grabWidget(view)
                drag = QtGui.QDrag(self)
                data = QtCore.QMimeData()
                data.setData('x-application/xview/tabbed_view',
                             QtCore.QByteArray(str(index)))
                drag.setMimeData(data)
                drag.setPixmap(pixmap)
                view.hide()
                if not drag.exec_():
                    cursor = QtGui.QCursor.pos()
                    geom = self.window().geometry()
                    if not geom.contains(cursor):
                        view.popout()
                view.show()
                
                return True
        
        elif event.type() == event.DragEnter:
            data = event.mimeData()
            if data.hasFormat('x-application/xview/tabbed_view') or \
               data.hasFormat('x-application/xview/floating_view'):
                if event.source() != self and \
                   event.source().viewWidget() == self.viewWidget():
                    event.acceptProposedAction()
                    return True
        
        elif event.type() == event.Drop:
            data = event.mimeData()
            if data.hasFormat('x-application/xview/tabbed_view'):
                if event.source().viewWidget() == self.viewWidget():
                    index = int(data.data('x-application/xview/tabbed_view'))
                    self.snagViewFromPanel(event.source(), index)
                    return True
                
            elif data.hasFormat('x-application/xview/floating_view'):
                if event.source().viewWidget() == self.viewWidget():
                    view = event.source()
                    view.setWindowFlags(QtCore.Qt.Widget)
                    self.addTab(view, view.windowTitle())
                    return True
        
        return False
    
    def hideTabsWhenLocked(self):
        """
        Returns whether or not the tabs should be visible when the panel
        is locked down.  By default, this value will be True.
        
        :return     <bool>
        """
        return self._hideTabsWhenLocked

    def hint(self):
        """
        Returns the hint for this widget.

        :return     <str>
        """
        try:
            return self.viewWidget().hint()
        except AttributeError:
            return ''

    def insertTab(self, index, widget, title):
        """
        Inserts a new tab for this widget.

        :param      index  | <int>
                    widget | <QtGui.QWidget>
                    title  | <str>
        """
        self.insertWidget(index, widget)
        self.tabBar().insertTab(index, title)

    def insertView(self, index, viewType):
        if not viewType:
            return False
            
        self.insertTab(index, 
                       viewType.createInstance(self, self.viewWidget()), 
                       viewType.viewName())
        return True
    
    def isLocked(self):
        """
        Returns whether or not this panel is currently locked from user editing.
        
        :return     <bool>
        """
        return self._locked
    
    def markCurrentChanged(self):
        """
        Marks that the current widget has changed.
        """
        view = self.currentView()
        if view:
            view.setCurrent()
            self.setFocus()
            view.setFocus()
            self._hintLabel.hide()
        else:
            self._hintLabel.show()
            self._hintLabel.setText(self.hint())

        if not self.count():
            self.tabBar().clear()

        self.adjustSizeConstraint()

    def paintEvent(self, event):
        """
        Runs the paint event for this item.
        """
        painter = QtGui.QPainter()
        painter.begin(self)
        try:
            palette = self.palette()
            clr = palette.color(palette.WindowText)
            clr.setAlpha(100)
            painter.setPen(clr)
            painter.setBrush(palette.color(palette.Window))

            if self._tabBar.isVisible():
                painter.fillRect(0, 0, self.width() - 1, self.height() - 1, palette.color(palette.Button))
                x = y = 3
                w = self.width() - 7
                h = self.height() - 7
            else:
                x = y = 0
                w = self.width() - 1
                h = self.height() - 1

            painter.drawRect(x, y, w, h)

        finally:
            painter.end()

    def refreshTitles(self):
        """
        Refreshes the titles for each view within this tab panel.
        """
        for index in range(self.count()):
            widget = self.widget(index)
            self.setTabText(index, widget.windowTitle())

    def resizeEvent(self, event):
        super(XViewPanel, self).resizeEvent(event)

        self._tabBar.resize(event.size().width(), self._tabBar.height())

        if self._tabBar.isVisible():
            self._hintLabel.move(0, self._tabBar.height() + 3)
            self._hintLabel.resize(self.width(), self.height() - self._tabBar.height())
        else:
            self._hintLabel.move(0, 0)
            self._hintLabel.resize(self.width(), self.height())

    def removeTab(self, index):
        """
        Removes the view at the inputed index and disconnects it from the \
        panel.
        
        :param      index | <int>
        """
        view = self.widget(index)
        if isinstance(view, XView):
            try:
                view.windowTitleChanged.disconnect(self.refreshTitles)
                view.sizeConstraintChanged.disconnect(self.adjustSizeConstraint)
            except:
                pass
        
        return super(XViewPanel, self).removeTab(index)
    
    def split(self, orientation, count=2, before=False, autoCreateView=True):
        parent = self.parent()
        if not (parent and count):
            return False
        
        # split from a parent's layout
        w = self.width()
        h = self.height()
        
        if orientation == QtCore.Qt.Horizontal:
            size = w / count
        else:
            size = h / count
        
        window = self.window()
        window.setUpdatesEnabled(False)
        
        new_panel = None
        curr_view = self.currentView()

        # split a splitter
        if isinstance(parent, XSplitter):
            # remove the widget from the splitter
            psizes = parent.sizes()
            index = parent.indexOf(self)
            
            # create the splitter
            splitter = XSplitter(orientation, parent)
            self.setParent(splitter)
            splitter.addWidget(self)
            
            # split with a new view
            sizes = [size]
            for i in xrange(count - 1):
                new_panel = XViewPanel(splitter, self.isLocked())

                if curr_view and autoCreateView:
                    new_view = curr_view.duplicate(new_panel)
                    new_panel.addTab(new_view, new_view.windowTitle())

                # if the new view is the same as the old view, it is a singleton and the
                # tab needs to be cleared out
                #if new_view == curr_view:
                #    self.tabBar().removeTab(self.tabBar().currentIndex())

                if before:
                    splitter.insertWidget(0, new_panel)
                else:
                    splitter.addWidget(new_panel)
                sizes.append(size)
            
            sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,
                                           QtGui.QSizePolicy.Expanding)
            sizePolicy.setHorizontalStretch(1)
            sizePolicy.setVerticalStretch(1)
            
            splitter.setSizePolicy(sizePolicy)
            splitter.setSizes(sizes)
            
            # insert the splitter into the parent
            parent.insertWidget(index, splitter)
            parent.setSizes(psizes)
        
        # split a scroll area
        elif isinstance(parent, QtGui.QWidget) and \
             isinstance(parent.parent(), QtGui.QScrollArea):
            
            area = parent.parent()
            area.takeWidget()
            
            # create the splitter
            splitter = XSplitter(orientation, parent)
            splitter.addWidget(self)
            
            # split with a new view
            sizes = [size]
            for i in xrange(count - 1):
                new_panel = XViewPanel(splitter, self.isLocked())
                if curr_view and autoCreateView:
                    new_view = curr_view.duplicate(new_panel)
                    new_panel.addTab(new_view, new_view.windowTitle())

                # if the new view is the same as the old view, it is a singleton and the
                # tab needs to be cleared out
                #if new_view == curr_view:
                #    self.tabBar().removeTab(self.tabBar().currentIndex())

                if before:
                    splitter.insertWidget(0, new_panel)
                else:
                    splitter.addWidget(new_panel)
                sizes.append(size)
            
            splitter.setSizes(sizes)
            
            sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,
                                           QtGui.QSizePolicy.Expanding)
            sizePolicy.setHorizontalStretch(1)
            sizePolicy.setVerticalStretch(1)
            
            splitter.setSizePolicy(sizePolicy)
            
            area.setWidget(splitter)
        
        window.setUpdatesEnabled(True)
        return new_panel
        
    def splitVertical(self, count=2, before=False, autoCreateView=True):
        self.split(QtCore.Qt.Vertical, count, before, autoCreateView)
        
    def splitHorizontal(self, count=2, before=False, autoCreateView=True):
        self.split(QtCore.Qt.Horizontal, count, before, autoCreateView)
    
    def setHideTabsWhenLocked(self, state):
        """
        Sets whether or not tabs should be visible when the profile is locked
        down.  By default, this property will be True.
        
        :param      state | <bool>
        """
        self._hideTabsWhenLocked = state
    
    def setLocked(self, state, force=False):
        """
        Sets the locked state for this panel to the inputed state.
        
        :param      state | <bool>
        """
        if not force and state == self._locked:
            return
        
        self._locked = state
        tabbar = self.tabBar()
        if self.hideTabsWhenLocked():
            tabbar.setVisible(self.count() > 1 or not state)
        else:
            tabbar.setVisible(True)

        if tabbar.isVisible():
            self.setContentsMargins(6, tabbar.height(), 6, 6)
        else:
            self.setContentsMargins(1, 1, 1, 1)

        self.adjustSizeConstraint()

    def setTabText(self, index, text):
        """
        Sets the tab text for this instance to the inputed text.

        :param      index | <int>
                    text | <str>
        """
        self._tabBar.setTabText(index, text)

    def switchCurrentView(self, viewType):
        """
        Swaps the current tab view for the inputed action's type.

        :param      action | <QAction>
        """
        if not self.count():
            self.addView(viewType)
            return

        # make sure we're not trying to switch to the same type
        view = self.currentView()
        if type(view) == viewType:
            return

        # create a new view and close the old one
        self.blockSignals(True)
        self.setUpdatesEnabled(False)

        # create the new view
        index = self.indexOf(view)
        if not view.close():
            return False
        #else:
        #    self.tabBar().removeTab(index)

        index = self.currentIndex()
        new_view = viewType.createInstance(self.viewWidget(), self.viewWidget())

        # add the new view
        self.insertTab(index, new_view, new_view.windowTitle())

        self.blockSignals(False)
        self.setUpdatesEnabled(True)
        self.setCurrentIndex(index)
    
    def showEvent(self, event):
        super(XViewPanel, self).showEvent(event)
        
        # start a delay option to initialize this panel
        self.setLocked(self.isLocked(), force=True)

        self._hintLabel.setText(self.hint())
        self._hintLabel.setVisible(not bool(self.count()))
    
    def showAddMenu(self, point=None):
        if self.isLocked():
            return

        if point is None:
            add_btn = self.tabBar().addButton()
            point = add_btn.mapToGlobal(QtCore.QPoint(add_btn.width(), 0))

        self.viewWidget().showPluginMenu(self, point)
    
    def showTabMenu(self, point=None):
        if self.isLocked():
            return
            
        if not point:
            point = QtGui.QCursor.pos()
            
        self.viewWidget().showTabMenu(self, point)
    
    def showOptionsMenu(self, point=None):
        if self.isLocked():
            return
        
        if point is None:
            point = QtGui.QCursor.pos()
            
        self.viewWidget().showPanelMenu(self, point)
    
    def snagViewFromPanel(self, panel, index=None):
        """
        Removes the view from the inputed panel and adds it to this panel.
        
        :param      panel | <XViewPanel>
                    view  | <XView>
        """
        if index == None:
            index = panel.currentIndex()
            
        view = panel.widget(index)
        if not view:
            return
        
        count = panel.count()
        self.addTab(view, view.windowTitle())
        
        # when the panel gets moved and there are no more widgets within the 
        # panel, we'll close it out - but we cannot close it directly or we 
        # run into a segmentation fault here.  Better to provide a timer and
        # close it in a second.  It depends on which thread triggers this call
        # that sometimes causes it to error out. - EKH 01/25/12
        if count == 1:
            panel.closePanel()

    def tabBar(self):
        """
        Returns the tab bar associated with this panel.

        :return     <projexui.widgets.xviewwidget.xviewpanel.XViewPanelBar>
        """
        return self._tabBar

    def tabText(self, index):
        """
        Returns the text for the tab bar at the inputed index.

        :param      index | <int>

        :return     <str>
        """
        return self._tabBar.tabText(index)

    def viewWidget(self):
        from projexui.widgets.xviewwidget.xviewwidget import XViewWidget
        
        parent = self.parent()
        while (parent and not isinstance(parent, XViewWidget)):
            parent = parent.parent()
        return parent