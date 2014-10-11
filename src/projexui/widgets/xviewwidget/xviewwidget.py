#!/usr/bin python

""" Defines the main container widget for a view system. """

# define authorship information
__authors__     = ['Eric Hulser']
__author__      = ','.join(__authors__)
__credits__     = []
__copyright__   = 'Copyright (c) 2011, Projex Software'

# maintanence information
__maintainer__  = 'Projex Software'
__email__       = 'team@projexsoftware.com'

from projex.text import nativestring

from xqt import QtCore, QtGui, wrapVariant, unwrapVariant, PyObject

import projexui
import projexui.resources

from .xview          import XView
from .xviewpanel     import XViewPanel
from .xviewpanelmenu import XViewPanelMenu,\
                            XViewPluginMenu,\
                            XViewTabMenu
from .xviewprofile   import XViewProfile

class XViewWidget(QtGui.QScrollArea):
    __designer_icon__ = projexui.resources.find('img/ui/scrollarea.png')
    
    lockToggled = QtCore.Signal(bool)
    
    def __init__(self, parent):
        super(XViewWidget, self).__init__(parent)
        
        # define custom properties
        self._customData        = {}
        self._viewTypes         = []
        self._locked            = False
        self._tabMenu           = None
        self._pluginMenu        = None
        self._panelMenu         = None
        self._defaultProfile    = None
        self._scope             = None  # defines code execution scope for this widget
        self._hint = ''
        
        # intiailize the scroll area
        self.setBackgroundRole(QtGui.QPalette.Window)
        self.setFrameShape(QtGui.QScrollArea.NoFrame)
        self.setWidgetResizable(True)
        self.setWidget(XViewPanel(self, self.isLocked()))

        # update the current view
        app = QtGui.QApplication.instance()
        app.focusChanged.connect(self.updateCurrentView)
    
    def canClose(self):
        """
        Checks to see if the view widget can close by checking all of its \
        sub-views to make sure they're ok to close.
        
        :return     <bool>
        """
        for view in self.findChildren(XView):
            if not view.canClose():
                return False
        return True
    
    def closeEvent(self, event):
        views = self.findChildren(XView)
        for view in views:
            if not view.canClose():
                event.ignore()
                return
        
        for view in views:
            view.close()
        
        super(XViewWidget, self).closeEvent(event)
    
    def codeScope(self):
        """
        Returns the code execution scope for this widget.
        
        :return     <dict>
        """
        if self._scope is None:
            import __main__
            return __main__.__dict__
        else:
            return self._scope
    
    def createMenu(self, parent):
        """
        Creates a new menu for the inputed parent item.
        
        :param      parent | <QMenu>
        """
        menu = QtGui.QMenu(parent)
        menu.setTitle('&View')
        
        act = menu.addAction('Lock/Unlock Layout')
        act.setIcon(QtGui.QIcon(projexui.resources.find('img/view/lock.png')))
        act.triggered.connect(self.toggleLocked)
        
        menu.addSeparator()
        act = menu.addAction('Export Layout as...')
        act.setIcon(QtGui.QIcon(projexui.resources.find('img/view/export.png')))
        act.triggered.connect(self.exportProfile)
        
        act = menu.addAction('Import Layout from...')
        act.setIcon(QtGui.QIcon(projexui.resources.find('img/view/import.png')))
        act.triggered.connect(self.importProfile)
        
        menu.addSeparator()
        act = menu.addAction('Reset Layout')
        act.setIcon(QtGui.QIcon(projexui.resources.find('img/view/remove.png')))
        act.triggered.connect(self.reset)
        
        return menu
    
    def currentPanel(self):
        """
        Returns the currently active panel based on whether or not it has \
        focus.
        
        :return     <XViewPanel>  || None
        """
        panels = self.panels()
        for panel in panels:
            if panel.hasFocus():
                return panel
        
        if panels:
            return panels[0]
        
        return None
    
    def currentView(self):
        """
        Returns the current view for this widget.
        
        :return     <projexui.widgets.xviewwidget.XView> || NOne
        """
        panel = self.currentPanel()
        if panel:
            return panel.currentWidget()
        return None
    
    def customData(self, key, default=None):
        """
        Returns the custom data for the given key.
        
        :param      key     | <str>
                    default | <variant>
        
        :return     <variant>
        """
        return self._customData.get(nativestring(key), default)
    
    def defaultProfile(self):
        """
        Returns the default profile for this view widget.
        
        :return     <XViewProfile>
        """
        return self._defaultProfile
    
    def exportProfile(self, filename=''):
        """
        Exports the current profile to a file.
        
        :param      filename | <str>
        """
        if not (filename and isinstance(filename, basestring)):
            filename = QtGui.QFileDialog.getSaveFileName(self,
                                                         'Export Layout as...',
                                                         QtCore.QDir.currentPath(),
                                                         'XView (*.xview)')
            
            if type(filename) == tuple:
                filename = filename[0]
        
        filename = nativestring(filename)
        if not filename:
            return
        
        if not filename.endswith('.xview'):
            filename += '.xview'
        
        profile = self.saveProfile()
        profile.save(filename)
        
    def findViewType(self, viewTypeName):
        """
        Looks up the view type based on the inputed view type name.
        
        :param      viewTypeName | <str>
        """
        for viewType in self._viewTypes:
            if ( viewType.viewTypeName() == viewTypeName ):
                return viewType
        return None
    
    def importProfile(self, filename=''):
        """
        Exports the current profile to a file.
        
        :param      filename | <str>
        """
        if not (filename and isinstance(filename, basestring)):
            filename = QtGui.QFileDialog.getOpenFileName(self,
                                                         'Import Layout from...',
                                                         QtCore.QDir.currentPath(),
                                                         'XView (*.xview)')
            
            if type(filename) == tuple:
                filename = nativestring(filename[0])
        
        filename = nativestring(filename)
        if not filename:
            return
        
        if not filename.endswith('.xview'):
            filename += '.xview'
        
        profile = XViewProfile.load(filename)
        if not profile:
            return
            
        profile.restore(self)

    def hint(self):
        return self._hint

    def isEmpty(self):
        """
        Returns whether or not there are any XView widgets loaded for this
        widget.
        
        :return     <bool>
        """
        return len(self.findChildren(XView)) == 0
    
    def isLocked(self):
        """
        Returns whether or not this widget is in locked mode.
        
        :return     <bool>
        """
        return self._locked
    
    def panels(self):
        """
        Returns a lis of the panels that are assigned to this view widget.
        
        :return     [<XViewPanel>, ..]
        """
        return self.findChildren(XViewPanel)
    
    def registerViewType(self, cls, window=None):
        """
        Registers the inputed widget class as a potential view class.  If the \
        optional window argument is supplied, then the registerToWindow method \
        will be called for the class.
        
        :param          cls     | <subclass of XView>
                        window  | <QMainWindow> || <QDialog> || None
        """
        if ( not cls in self._viewTypes ):
            self._viewTypes.append(cls)
            
            if ( window ):
                cls.registerToWindow(window)
    
    @QtCore.Slot(PyObject)
    def restoreProfile(self, profile):
        """
        Restores the profile settings based on the inputed profile.
        
        :param      profile | <XViewProfile>
        """
        return profile.restore(self)
    
    def restoreSettings(self, settings):
        """
        Restores the current structure of the view widget from the inputed \
        settings instance.
        
        :param      settings | <QSettings>
        """
        key     = self.objectName()
        value   = unwrapVariant(settings.value('%s/profile' % key))
        
        if not value:
            self.reset(force = True)
            return False
            
        profile = value
        
        # restore the view type settings
        for viewType in self.viewTypes():
            viewType.restoreGlobalSettings(settings)
        
        # restore the profile
        self.restoreProfile(XViewProfile.fromString(profile))
        
        if not self.views():
            self.reset(force = True)
        
        return True
    
    def reset(self, force=False):
        """
        Clears out all the views and panels and resets the widget to a blank \
        parent.
        
        :return     <bool>
        """
        answer = QtGui.QMessageBox.Yes
        opts = QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
        
        if not force:
            answer = QtGui.QMessageBox.question(self,
                                                'Reset Layout',
                                                'Are you sure you want to reset?',
                                                opts)
        
        if answer == QtGui.QMessageBox.No:
            return
        
        widget = self.widget()
        
        # we should always have a widget, but double check
        if not widget:
            return False
        
        # make sure we can close the current view
        if not widget.close():
            return False
        
        # reset the system
        self.takeWidget()
        
        # restore a default profile
        prof = self.defaultProfile()
        if prof:
            return prof.restore(self)
        
        # otherwise create a new panel
        else:
            self.setWidget(XViewPanel(self, self.isLocked()))
        
        return True
    
    def saveProfile(self):
        """
        Saves the profile for the current state and returns it.
        
        :return     <XViewProfile>
        """
        return XViewProfile.record(self)
    
    def saveSettings(self, settings):
        """
        Records the current structure of the view widget to the inputed \
        settings instance.
        
        :param      settings | <QSettings>
        """
        # record the profile
        profile = self.saveProfile()
        key     = self.objectName()
        
        settings.setValue('%s/profile' % key, wrapVariant(profile.toString()))
        
        # record the view type settings
        for viewType in self.viewTypes():
            viewType.saveGlobalSettings(settings)
    
    def setCodeScope(self, scope):
        """
        Sets the code execution scope for this widget.  If the scope is
        set to None, then the global execution scope will be used.
        
        :param      scope | <dict> || None
        """
        self._scope = scope
    
    def setCurrent(self):
        """
        Sets this view widget as the current widget in case there are multiple
        ones.
        """
        for view in self.findChildren(XView):
            view.setCurrent()
    
    def setCustomData(self, key, value):
        """
        Sets the custom data for this instance to the inputed value.
        
        :param      key     | <str>
                    value   | <variant>
        """
        self._customData[nativestring(key)] = value
    
    def setDefaultProfile(self, profile):
        """
        Sets the default profile for this view to the inputed profile.
        
        :param      profile | <XViewProfile>
        """
        self._defaultProfile = profile

    def setHint(self, hint):
        self._hint = hint

    def setLocked(self, state):
        """
        Sets the locked state for this view widget.  When locked, a user no \
        longer has control over editing views and layouts.  A view panel with \
        a single entry will hide its tab bar, and if it has multiple views, it \
        will simply hide the editing buttons.
        
        :param      state | <bool>
        """
        changed = state != self._locked
        self._locked = state
        
        for panel in self.panels():
            panel.setLocked(state)
        
        if changed and not self.signalsBlocked():
            self.lockToggled.emit(state)
    
    def setViewTypes(self, viewTypes, window=None):
        """
        Sets the view types that can be used for this widget.  If the optional \
        window member is supplied, then the registerToWindow method will be \
        called for each view.
        
        :param      viewTypes | [<sublcass of XView>, ..]
                    window    | <QMainWindow> || <QDialog> || None
        """
        if window:
            for viewType in self._viewTypes:
                viewType.unregisterFromWindow(window)
        
        self._viewTypes = viewTypes[:]
        self._panelMenu = None
        self._pluginMenu = None
        
        if window:
            for viewType in viewTypes:
                viewType.registerToWindow(window)
    
    def showMenu(self, point=None):
        """
        Displays the menu for this view widget.
        
        :param      point | <QPoint>
        """
        menu = self.createMenu(self)
        menu.exec_(QtGui.QCursor.pos())
        menu.deleteLater()
    
    def showPanelMenu(self, panel, point=None):
        """
        Creates the panel menu for this view widget.  If no point is supplied,\
        then the current cursor position will be used.
        
        :param      panel   | <XViewPanel>
                    point   | <QPoint> || None
        """
        if not self._panelMenu:
            self._panelMenu = XViewPanelMenu(self)
        
        if point is None:
            point = QtGui.QCursor.pos()
        
        self._panelMenu.setCurrentPanel(panel)
        self._panelMenu.exec_(point)
    
    def showPluginMenu(self, panel, point=None):
        """
        Creates the interface menu for this view widget.  If no point is \
        supplied, then the current cursor position will be used.
        
        :param      panel | <XViewPanel>
                    point | <QPoint> || None
        """
        if not self._pluginMenu:
            self._pluginMenu = XViewPluginMenu(self)
        
        if point is None:
            point = QtGui.QCursor.pos()
        
        self._pluginMenu.setCurrentPanel(panel)
        self._pluginMenu.exec_(point)
    
    def showTabMenu(self, panel, point=None):
        """
        Creates the panel menu for this view widget.  If no point is supplied,\
        then the current cursor position will be used.
        
        :param      panel   | <XViewPanel>
                    point   | <QPoint> || None
        """
        if not self._tabMenu:
            self._tabMenu = XViewTabMenu(self)

        if point is None:
            point = QtGui.QCursor.pos()

        self._tabMenu.setCurrentPanel(panel)
        self._tabMenu.exec_(point)
    
    def toggleLocked(self):
        """
        Toggles whether or not this view is locked 
        """
        self.setLocked(not self.isLocked())
    
    def updateCurrentView(self, oldWidget, newWidget):
        """
        Updates the current view widget.
        
        :param      oldWidget | <QtGui.QWidget>
                    newWidget | <QtGui.QWidget>
        """
        view = projexui.ancestor(newWidget, XView)
        if view is not None:
            view.setCurrent()
    
    def unregisterViewType(self, cls, window=None):
        """
        Unregisters the view at the given name.  If the window option is \
        supplied then the unregisterFromWindow method will be called for the \
        inputed class.
        
        :param          cls    | <subclass of XView>    
                        window | <QMainWindow> || <QDialog> || None
        
        :return     <bool> changed
        """
        if ( cls in self._viewTypes ):
            self._viewTypes.remove(cls)
            
            if ( window ):
                cls.unregisterFromWindow(window)
                
            return True
        return False
    
    def views(self):
        """
        Returns a list of the current views associated with this view widget.
        
        :return     [<XView>, ..]
        """
        return self.findChildren(XView)
    
    def viewType(self, name):
        """
        Looks up the view class based on the inputd name.
        
        :param      name | <str>
        
        :return     <subclass of XView> || None
        """
        for view in self._viewTypes:
            if ( view.viewName() == name ):
                return view
        return None
    
    def viewTypes(self):
        """
        Returns a list of all the view types registered for this widget.
        
        :return     <str>
        """
        return sorted(self._viewTypes, key = lambda x: x.viewName())

    x_hint = QtCore.Property(unicode, hint, setHint)