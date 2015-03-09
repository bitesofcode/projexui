#!/usr/bin python

""" Defines the menu that will be used when a ViewPanel is being modified. """

# define authorship information
__authors__     = ['Eric Hulser']
__author__      = ','.join(__authors__)
__credits__     = []
__copyright__   = 'Copyright (c) 2011, Projex Software'

# maintanence information
__maintainer__  = 'Projex Software'
__email__       = 'team@projexsoftware.com'

from projexui.qt import wrapVariant, unwrapVariant
from projexui.qt.QtCore import Qt
from projexui.qt.QtGui import QActionGroup,\
                              QMenu,\
                              QIcon,\
                              QInputDialog,\
                              QLineEdit,\
                              QSplitter,\
                              QAction

from projexui.menus.xmenu import XMenu

from projexui import resources

class XViewBaseMenu(XMenu):
    def __init__(self, viewWidget, mode='panel'):
        # initialize the super class
        super(XViewBaseMenu, self).__init__(viewWidget)
        
        # define custom properties
        self._viewWidget    = viewWidget
        self._currentPanel  = None
        
        self.setupActions()
    
    def addPanel(self, action):
        panel = self.currentPanel()
        if not panel:
            return
        
        direction = action.text()
        
        if direction in ('Row Above', 'Row Below'):
            orientation = Qt.Vertical
        else:
            orientation = Qt.Horizontal
        
        if direction in ('Row Below', 'Column Right'):
            before = False
        else:
            before = True
        
        panel.addPanel(orientation, before)
    
    def addView(self, action):
        panel = self.currentPanel()
        
        if panel is None:
            return False
        
        viewType = self._viewWidget.viewType(action.text())
        return panel.addView(viewType)
    
    def assignGroup(self, action):
        """
        Assigns the group for the given action to the current view.
        
        :param      action | <QAction>
        """
        grp  = unwrapVariant(action.data())
        view = self._currentPanel.currentView()
        view.setViewingGroup(grp)
    
    def closePanel(self):
        """
        Closes the current panel within the view widget.
        """
        panel = self.currentPanel()
        if panel is not None:
            return panel.closePanel()
        return False
    
    def closeView(self):
        """
        Closes the current view within the panel.
        """
        panel = self.currentPanel()
        if panel is not None:
            return panel.closeView()
        return False
    
    def currentPanel(self):
        """
        Returns the current panel widget.
        
        :return     <XViewPanel>
        """
        return self._currentPanel
    
    def detachPanel(self):
        """
        Detaches the current panel as a floating window.
        """
        from projexui.widgets.xviewwidget import XViewDialog
        
        dlg = XViewDialog(self._viewWidget, self._viewWidget.viewTypes())
        size = self._currentPanel.size()
        dlg.viewWidget().currentPanel().snagViewFromPanel(self._currentPanel)
        dlg.resize(size)
        dlg.show()
    
    def detachPanelCopy(self):
        """
        Detaches the current panel as a floating window.
        """
        from projexui.widgets.xviewwidget import XViewDialog
        
        dlg = XViewDialog(self._viewWidget, self._viewWidget.viewTypes())
        size = self._currentPanel.size()
        view = self._currentPanel.currentView()
        
        # duplicate the current view
        if view:
            new_view = view.duplicate(dlg.viewWidget().currentPanel())
            view_widget = dlg.viewWidget()
            view_panel = view_widget.currentPanel()
            view_panel.addTab(new_view, new_view.windowTitle())
            
        dlg.resize(size)
        dlg.show()
        
    def gotoNext(self):
        """
        Goes to the next panel tab.
        """
        index = self._currentPanel.currentIndex() + 1
        if ( self._currentPanel.count() == index ):
            index = 0
            
        self._currentPanel.setCurrentIndex(index)
    
    def gotoPrevious(self):
        """
        Goes to the previous panel tab.
        """
        index = self._currentPanel.currentIndex() - 1
        if index < 0:
            index = self._currentPanel.count() - 1
        
        self._currentPanel.setCurrentIndex(index)
    
    def newPanelTab(self):
        """
        Creates a new panel with a copy of the current widget.
        """
        view = self._currentPanel.currentView()
        
        # duplicate the current view
        if view:
            new_view = view.duplicate(self._currentPanel)
            self._currentPanel.addTab(new_view, new_view.windowTitle())
    
    def renamePanel(self):
        """
        Prompts the user for a custom name for the current panel tab.
        """
        index = self._currentPanel.currentIndex()
        title = self._currentPanel.tabText(index)
        
        new_title, accepted = QInputDialog.getText( self,
                                                    'Rename Tab',
                                                    'Name:',
                                                    QLineEdit.Normal,
                                                    title )
        
        if accepted:
            widget = self._currentPanel.currentView()
            widget.setWindowTitle(new_title)
            self._currentPanel.setTabText(index, new_title)
    
    def reset(self):
        """
        Clears the current views from the system
        """
        self._viewWidget.reset()
    
    def setCurrentPanel(self, panel):
        self._currentPanel = panel
    
    def setupActions(self):
        pass
    
    def splitVertical(self):
        panel = self.currentPanel()
        if panel is not None:
            return panel.splitVertical()
        return None
        
    def splitVerticalAdvanced(self):
        panel = self.currentPanel()
        if panel is None:
            return
            
        count, accepted = QInputDialog.getInt(None,
                                              'Split Vertical',
                                              'Number of Rows:',
                                              2,
                                              2)
        
        if accepted:
            panel.splitVertical(count)
        
    def splitHorizontal(self):
        panel = self.currentPanel()
        if panel is not None:
            return panel.splitHorizontal()
        return None
        
    def splitHorizontalAdvanced(self):
        panel = self.currentPanel()
        if panel is None:
            return
            
        count, accepted = QInputDialog.getInt(None,
                                              'Split Horizontal',
                                              'Number of Columns:',
                                              2,
                                              2)
        
        if accepted:
            panel.splitHorizontal(count)
        
    def switchPanels(self, action):
        direction = action.text()
        
        if direction in ('Row Up', 'Row Down'):
            orientation = Qt.Vertical
        else:
            orientation = Qt.Horizontal
        
        widget = self.currentPanel()
        if not widget:
            return
        
        # look up the splitter for the widget
        splitter = widget.parent()
        while widget and isinstance(splitter, QSplitter):
            if splitter.orientation() == orientation:
                break
            
            widget = splitter
            splitter = splitter.parent()
        
        if not isinstance(splitter, QSplitter):
            return
        
        self._viewWidget.setUpdatesEnabled(False)
        
        # determine the new location for the panel
        index = splitter.indexOf(widget)
        if direction in ('Row Down', 'Column Right'):
            new_index = index
            widget    = splitter.widget(index + 1)
        else:
            new_index = index - 1
        
        if widget and 0 <= new_index and new_index < splitter.count():
            splitter.insertWidget(new_index, widget)
        
        self._viewWidget.setUpdatesEnabled(True)
    
    def swapTabType(self, action):
        """
        Swaps the current tab view for the inputed action's type.
        
        :param      action | <QAction>
        """
        # for a new tab, use the add tab slot
        if not self._currentPanel.count():
            self.addView(action)
            return
        
        # make sure we're not trying to switch to the same type
        viewType = self._viewWidget.viewType(action.text())
        view = self._currentPanel.currentView()
        if type(view) == viewType:
            return
        
        # create a new view and close the old one
        self._viewWidget.setUpdatesEnabled(False)
        self._currentPanel.blockSignals(True)
        
        # create the new view
        view.close()
        
        index       = self._currentPanel.currentIndex()
        new_view    = viewType.createInstance(self._viewWidget,
                                              self._viewWidget)
        
        # add the new view
        self._currentPanel.insertTab(index,
                                     new_view, 
                                     new_view.windowTitle())
        
        self._currentPanel.blockSignals(False)
        self._currentPanel.setCurrentIndex(index)
        self._viewWidget.setUpdatesEnabled(True)
        
    def viewWidget(self):
        return self._viewWidget

#----------------------------------------------------------------------

class XViewPanelMenu(XViewBaseMenu):
    def setupActions(self):
        # initialize the menu
        viewWidget = self.viewWidget()
        
        self.setTitle('Panel Options')
        self.addSection('Panels')
        act = self.addAction('Split Panel Left/Right')
        act.setIcon(QIcon(resources.find('img/view/split_horizontal.png')))
        act.triggered.connect(self.splitHorizontal)
        
        split_adv = QAction(self)
        split_adv.setIcon(QIcon(resources.find('img/advanced.png')))
        split_adv.setToolTip('Specify number of columns for split')
        split_adv.triggered.connect(self.splitHorizontalAdvanced)
        self.setAdvancedAction(act, split_adv)
        
        act = self.addAction('Split Panel Top/Bottom')
        act.setIcon(QIcon(resources.find('img/view/split_vertical.png')))
        act.triggered.connect(self.splitVertical)
        
        split_adv = QAction(self)
        split_adv.setIcon(QIcon(resources.find('img/advanced.png')))
        split_adv.setToolTip('Specify number of rows for split')
        split_adv.triggered.connect(self.splitVerticalAdvanced)
        self.setAdvancedAction(act, split_adv)
        
        self.addSeparator()
        
        menu = self.addMenu('Add...')
        menu.setIcon(QIcon(resources.find('img/view/add.png')))
        
        act = menu.addAction('Row Above')
        act.setIcon(QIcon(resources.find('img/view/up.png')))
        act = menu.addAction('Row Below')
        act.setIcon(QIcon(resources.find('img/view/down.png')))
        menu.addSeparator()
        act = menu.addAction('Column Left')
        act.setIcon(QIcon(resources.find('img/view/left.png')))
        act = menu.addAction('Column Right')
        act.setIcon(QIcon(resources.find('img/view/right.png')))
        
        menu.triggered.connect(self.addPanel)
        
        # create pane options menu
        menu = self.addMenu('Move...')
        menu.setIcon(QIcon(resources.find('img/view/switch.png')))
        
        act = menu.addAction('Row Up')
        act.setIcon(QIcon(resources.find('img/view/up.png')))
        act = menu.addAction('Row Down')
        act.setIcon(QIcon(resources.find('img/view/down.png')))
        menu.addSeparator()
        act = menu.addAction('Column Left')
        act.setIcon(QIcon(resources.find('img/view/left.png')))
        act = menu.addAction('Column Right')
        act.setIcon(QIcon(resources.find('img/view/right.png')))
        
        menu.triggered.connect(self.switchPanels)
        
        self.addSeparator()
        
        act = self.addAction('Close Section (All Tabs)')
        act.setIcon(QIcon(resources.find('img/view/close.png')))
        act.triggered.connect( self.closePanel )
        

#----------------------------------------------------------------------

class XViewPluginMenu(XViewBaseMenu):
    def setupActions(self):
        viewWidget = self.viewWidget()
        
        self.setTitle('Add View')
        
        # collect the views and groups
        sorter = lambda x: x.viewGroup() + '/' + x.viewName()
        views = sorted(viewWidget.viewTypes(), key=sorter)
        grps = set([view.viewGroup() for view in views])
        
        # for a non-hierarchical view setup, just add the views to this menu
        if len(grps) <= 1:
            for view in views:
                act = self.addAction(view.viewName())
                act.setIcon(QIcon(view.viewIcon()))
        
        # otherwise, add the views to a submenu system
        else:
            self.addSearchAction()
            self.addSeparator()
            menus = {}
            
            for view in views:
                # separate the grouping levels
                for grp in view.viewGroup().split(';'):
                    parts = grp.split('/')
                    menu = self
                    for i, part in enumerate(parts):
                        key = ('/'.join(parts[:i]) + '/' + part).strip('/')
                        menu = menus.get(key)
                        if not menu:
                            ico = QIcon(resources.find('img/folder.png'))
                            parent_key = '/'.join(parts[:i]).strip('/')
                            parent = menus.get(parent_key, self)
                            menu = parent.addMenu(part)
                            menu.setIcon(ico)
                            menus[key] = menu
                    
                    # add to the last item
                    act = menu.addAction(view.viewName())
                    act.setIcon(QIcon(view.viewIcon()))
        
        self.triggered.connect(self.addView)
        self.addSeparator()

#----------------------------------------------------------------------

class XViewTabMenu(XViewBaseMenu):
    def __init__(self, parent):
        self._pluginMenu = None
        self._groupingMenu = None
        self._panelGroup    = QActionGroup(parent)
        self._groupingGroup = QActionGroup(parent)
        self._hideAction = None
        
        super(XViewTabMenu, self).__init__(parent)
        
    def setupActions(self):
        viewWidget = self.viewWidget()
        
        self.addSection('Views')
        self._pluginMenu = XViewPluginMenu(self.viewWidget())
        self._pluginMenu.setTitle('Switch View')
        self.addMenu(self._pluginMenu)
        self._pluginMenu.triggered.disconnect(self._pluginMenu.addView)
        self._pluginMenu.setIcon(QIcon(resources.find('img/view/switch.png')))
        self._pluginMenu.triggered.connect(self.swapTabType)
        
        # create view grouping options
        self._groupingMenu = self.addMenu('Set Group')
        icon = QIcon(resources.find('img/view/group.png'))
        self._groupingMenu.setIcon(icon)
        
        act = self._groupingMenu.addAction('No Grouping')
        act.setData(wrapVariant(0))
        act.setCheckable(True)
        self._groupingMenu.addSeparator()
        self._groupingGroup.addAction(act)
        
        for i in range(1, 6):
            act = self._groupingMenu.addAction('Group %i' % i)
            act.setData(wrapVariant(i))
            act.setCheckable(True)
            
            self._groupingGroup.addAction(act)
        
        self._groupingMenu.triggered.connect(self.assignGroup)
        
        self.setTitle('Tabs')
        self.addSection('Tabs')
        
        act = self.addAction('Rename Tab')
        act.setIcon(QIcon(resources.find('img/edit.png')))
        act.triggered.connect( self.renamePanel )
        
        act = self.addAction('Detach Tab')
        act.setIcon(QIcon(resources.find('img/view/detach.png')))
        act.triggered.connect( self.detachPanel )
        
        act = self.addAction('Detach Tab (as a Copy)')
        act.setIcon(QIcon(resources.find('img/view/detach_copy.png')))
        act.triggered.connect( self.detachPanelCopy )
        
        act = self.addAction('Close Tab')
        act.setIcon(QIcon(resources.find('img/view/tab_remove.png')))
        act.triggered.connect( self.closeView )
        
        self.addSeparator()
        
        act = self.addAction('Hide Tabs when Locked')
        act.triggered[bool].connect(self.setHideTabsWhenLocked)
        act.setCheckable(True)
        self._hideAction = act
        
        self.addSection('Panels')
        act = self.addAction('Split Panel Left/Right')
        act.setIcon(QIcon(resources.find('img/view/split_horizontal.png')))
        act.triggered.connect(self.splitHorizontal)
        
        split_adv = QAction(self)
        split_adv.setIcon(QIcon(resources.find('img/advanced.png')))
        split_adv.setToolTip('Specify number of columns for split')
        split_adv.triggered.connect(self.splitHorizontalAdvanced)
        self.setAdvancedAction(act, split_adv)
        
        act = self.addAction('Split Panel Top/Bottom')
        act.setIcon(QIcon(resources.find('img/view/split_vertical.png')))
        act.triggered.connect(self.splitVertical)
    
        split_adv = QAction(self)
        split_adv.setIcon(QIcon(resources.find('img/advanced.png')))
        split_adv.setToolTip('Specify number of rows for split')
        split_adv.triggered.connect(self.splitVerticalAdvanced)
        self.setAdvancedAction(act, split_adv)
        
    def setCurrentPanel(self, panel):
        super(XViewTabMenu, self).setCurrentPanel(panel)
        
        # update the current tab based on what view type it is
        viewType = ''
        grp = -1
        if panel is not None and panel.currentView():
            viewType = panel.currentView().viewName()
            grp = panel.currentView().viewingGroup()
        
        self._panelGroup.blockSignals(True)
        for act in self._panelGroup.actions():
            act.setChecked(viewType == act.text())
        self._panelGroup.blockSignals(False)
        
        self._groupingGroup.blockSignals(True)
        for act in self._groupingGroup.actions():
            act.setChecked(grp == unwrapVariant(act.data()))
        self._groupingGroup.blockSignals(False)
        
        self._pluginMenu.setCurrentPanel(panel)
        self._groupingMenu.setEnabled(grp != -1)
        
        if panel:
            self._hideAction.setChecked(panel.hideTabsWhenLocked())
            self._hideAction.setEnabled(True)
        else:
            self._hideAction.setEnabled(False)

    def setHideTabsWhenLocked(self, state):
        self.currentPanel().setHideTabsWhenLocked(state)
