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

import projexui

from projex.text import nativestring

from projexui.qt.QtCore   import Qt,\
                                 QMimeData,\
                                 QSize,\
                                 QByteArray,\
                                 QTimer
                           
from projexui.qt.QtGui    import QApplication,\
                                 QBoxLayout, \
                                 QCursor, \
                                 QDrag,\
                                 QGridLayout, \
                                 QMenu, \
                                 QPixmap,\
                                 QScrollArea, \
                                 QSizePolicy, \
                                 QStyleOptionTabWidgetFrame,\
                                 QTabBar,\
                                 QWidget

from projexui.widgets.xdropzonewidget    import XDropZoneWidget
from projexui.widgets.xtabwidget         import XTabWidget
from projexui.widgets.xviewwidget.xview  import XView
from projexui.widgets.xsplitter          import XSplitter

MAX_INT = 2**16

class XViewPanel(XTabWidget):
    def __init__(self, parent, locked=True):
        # initialize the super class
        super(XViewPanel,self).__init__(parent)
        
        # create custom properties
        self._locked = locked
        self._hideTabsWhenLocked = True
        
        # set the size policy for this widget to always maximize space
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        
        self.setSizePolicy(sizePolicy)
        self.setAcceptDrops(True)
        
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
        self.tabBar().installEventFilter(self)
        self.tabBar().setAcceptDrops(True)
        self.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        
        # create connections
        self.tabCloseRequested.connect(self.closeView)
        self.addRequested.connect(self.showAddMenu)
        self.currentChanged.connect(self.markCurrentChanged)
        self.optionsRequested.connect(self.showOptionsMenu)
        
        self.tabBar().customContextMenuRequested.connect(self.showTabMenu)
    
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
            layout  = splitter.layout()
            w       = widget.width()
            h       = widget.height()
            
            if orientation == Qt.Horizontal:
                size = w / 2
            else:
                size = h / 2
            
            parent = splitter
            splitter = widget
            
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
            
            sizePolicy = QSizePolicy(QSizePolicy.Expanding, 
                                     QSizePolicy.Expanding)
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
    
    def addTab( self, view, title ):
        """
        Adds a new view tab to this panel.
        
        :param      view    | <XView>
                    title   | <str>
        
        :return     <bool> | success
        """
        if not isinstance(view, XView):
            return False
        
        super(XViewPanel, self).addTab(view, title)
        
        # create connections
        try:
            view.windowTitleChanged.connect(self.refreshTitles,
                                            Qt.UniqueConnection)
            view.sizeConstraintChanged.connect(self.adjustSizeConstraint,
                                            Qt.UniqueConnection)
            view.poppedOut.connect(self.disconnectView,
                                   Qt.UniqueConnection)
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
        
        if self.tabBar().isVisible():
            offh += 20 # tab bar height
        
        minw = min(widget.minimumWidth() + offw,   MAX_INT)
        minh = min(widget.minimumHeight() + offh,  MAX_INT)
        maxw = min(widget.maximumWidth() + offw,   MAX_INT)
        maxh = min(widget.maximumHeight() + offh,  MAX_INT)
        
        self.setMinimumSize(minw, minh)
        self.setMaximumSize(maxw, maxh)
        self.setSizePolicy(widget.sizePolicy())
    
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
        for i in range(self.count()):
            self.widget(0).close()
        
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
                        old_widget = viewWidget.takeWidget()
                    else:
                        old_widget = viewWidget.widget()
                        old_widget.setParent(None)
                        old_widget.close()
                        old_widget.deleteLater()
                        QApplication.instance().processEvents()
                    
                    viewWidget.setWidget(widget)
            else:
                container.setParent(None)
                container.close()
                container.deleteLater()
        
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
                panel = self.split(Qt.Horizontal, before=True, autoCreateView=False)
                panel.snagViewFromPanel(event.source(), index)
            
            elif area == 'left':
                panel = self.addPanel(Qt.Horizontal, before=True)
                panel.snagViewFromPanel(event.source(), index)
            
            elif area == 'right':
                panel = self.addPanel(Qt.Horizontal)
                panel.snagViewFromPanel(event.source(), index)
            
            elif area == 'split_right':
                panel = self.split(Qt.Horizontal, autoCreateView=False)
                panel.snagViewFromPanel(event.source(), index)
            
            elif area == 'top':
                panel = self.addPanel(Qt.Vertical, before=True)
                panel.snagViewFromPanel(event.source(), index)
            
            elif area == 'split_up':
                panel = self.split(Qt.Vertical, before=True, autoCreateView=False)
                panel.snagViewFromPanel(event.source(), index)
            
            elif area == 'bottom':
                panel = self.addPanel(Qt.Vertical)
                panel.snagViewFromPanel(event.source(), index)
            
            elif area == 'split_down':
                panel = self.split(Qt.Vertical, autoCreateView=False)
                panel.snagViewFromPanel(event.source(), index)
        
        elif data.hasFormat('x-application/xview/floating_view'):
            view = event.source()
            view.setWindowFlags(Qt.Widget)
            
            if area == 'center':
                self.addTab(view, view.windowTitle())
            
            elif area == 'split_left':
                panel = self.split(Qt.Horizontal, before=True, autoCreateView=False)
                panel.addTab(view, view.windowTitle())
            
            elif area == 'left':
                panel = self.addPanel(Qt.Horizontal, before=True)
                panel.addTab(view, view.windowTitle())
            
            elif area == 'split_right':
                panel = self.split(Qt.Horizontal, autoCreateView=False)
                panel.addTab(view, view.windowTitle())
            
            elif area == 'right':
                panel = self.addPanel(Qt.Horizontal)
                panel.addTab(view, view.windowTitle())
            
            elif area == 'split_up':
                panel = self.split(Qt.Vertical, before=True, autoCreateView=False)
                panel.addTab(view, view.windowTitle())
            
            elif area == 'top':
                panel = self.addPanel(Qt.Vertical, before=True)
                panel.addTab(view, view.windowTitle())
            
            elif area == 'split_down':
                panel = self.split(Qt.Vertical, autoCreateView=False)
                panel.addTab(view, view.windowTitle())
            
            elif area == 'bottom':
                panel = self.addPanel(Qt.Vertical)
                panel.addTab(view, view.windowTitle())
    
    def eventFilter(self, object, event):
        if event.type() == event.MouseButtonPress:
            if self.isLocked():
                return False
            
            if event.button() == Qt.MidButton or \
               (event.button() == Qt.LeftButton and \
                event.modifiers() == Qt.ShiftModifier):
                index = self.tabBar().tabAt(event.pos())
                view  = self.widget(index)
                pixmap = QPixmap.grabWidget(view)
                drag = QDrag(self)
                data = QMimeData()
                data.setData('x-application/xview/tabbed_view',
                             QByteArray(str(index)))
                drag.setMimeData(data)
                drag.setPixmap(pixmap)
                view.hide()
                if not drag.exec_():
                    cursor = QCursor.pos()
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
                    view.setWindowFlags(Qt.Widget)
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
        
        self.adjustSizeConstraint()
    
    def refreshTitles(self):
        """
        Refreshes the titles for each view within this tab panel.
        """
        for index in range(self.count()):
            widget = self.widget(index)
            self.setTabText(index, widget.windowTitle())
            
        self.adjustButtons()
    
    def removeTab(self, index):
        """
        Removes the view at the inputed index and disconnects it from the \
        panel.
        
        :param      index | <int>
        """
        view = self.widget(index)
        if ( isinstance(view, XView) ):
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
        layout  = parent.layout()
        w       = self.width()
        h       = self.height()
        
        if orientation == Qt.Horizontal:
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
                
                if before:
                    splitter.insertWidget(0, new_panel)
                else:
                    splitter.addWidget(new_panel)
                sizes.append(size)
            
            sizePolicy = QSizePolicy(QSizePolicy.Expanding, 
                                     QSizePolicy.Expanding)
            sizePolicy.setHorizontalStretch(1)
            sizePolicy.setVerticalStretch(1)
            
            splitter.setSizePolicy(sizePolicy)
            splitter.setSizes(sizes)
            
            # insert the splitter into the parent
            parent.insertWidget(index, splitter)
            parent.setSizes(psizes)
        
        # split a scroll area
        elif isinstance(parent, QWidget) and \
             isinstance(parent.parent(), QScrollArea):
            
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
                
                if before:
                    splitter.insertWidget(0, new_panel)
                else:
                    splitter.addWidget(new_panel)
                sizes.append(size)
            
            splitter.setSizes(sizes)
            
            sizePolicy = QSizePolicy(QSizePolicy.Expanding, 
                                     QSizePolicy.Expanding)
            sizePolicy.setHorizontalStretch(1)
            sizePolicy.setVerticalStretch(1)
            
            splitter.setSizePolicy(sizePolicy)
            
            area.setWidget(splitter)
        
        window.setUpdatesEnabled(True)
        return new_panel
        
    def splitVertical(self, count=2, before=False, autoCreateView=True):
        self.split(Qt.Vertical, count, before, autoCreateView)
        
    def splitHorizontal(self, count=2, before=False, autoCreateView=True):
        self.split(Qt.Horizontal, count, before, autoCreateView)
    
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
        
        self.addButton().setVisible(not state)
        self.optionsButton().setVisible(not state)
        self.setTabsClosable(not state)
        self.setMovable(not state)
        
        self.adjustButtons()
        self.adjustSizeConstraint()
    
    def setView(self, viewType):
        self.setUpdatesEnabled(False)
        
        curr_view = self.currentView()
        if self.insertView(self.currentIndex(), curr_view) and curr_view:
            curr_view.close()
            
        self.setUpdatesEnabled(True)
    
    def showEvent(self, event):
        super(XViewPanel, self).showEvent(event)
        
        # start a delay option to initialize this panel
        self.startTimer(50)
    
    def showAddMenu(self, point):
        if self.isLocked():
            return
            
        self.viewWidget().showPluginMenu(self, point)
    
    def showTabMenu(self, point=None):
        if self.isLocked():
            return
            
        if not point:
            point = QCursor.pos()
            
        self.viewWidget().showTabMenu(self, point)
    
    def showOptionsMenu(self, point=None):
        if self.isLocked():
            return
        
        if point is None:
            point = QCursor.pos()
            
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
    
    def timerEvent(self, event):
        self.killTimer(event.timerId())
        self.setLocked(self.isLocked(), force=True)
    
    def viewWidget(self):
        from projexui.widgets.xviewwidget.xviewwidget import XViewWidget
        
        parent = self.parent()
        while (parent and not isinstance(parent, XViewWidget)):
            parent = parent.parent()
        return parent