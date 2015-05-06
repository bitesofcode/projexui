#!/usr/bin/python

"""
Defines a subclass and root for applications within the ProjexUI framework.
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

import os
import sys
import weakref

from projex.text import nativestring

import projexui
from projexui.qt import QtCore, QtGui
from projexui.widgets.xloggersplashscreen import XLoggerSplashScreen
from projexui.xsettings import XSettings

class XApplication(QtGui.QApplication):
    def __init__(self, argv):
        super(XApplication, self).__init__(argv)
        
        # define custom properties
        self._trayIcon = None
        self._splash = None
        self._autoCreateTrayIcon = True
        self._storagePaths = {}
        self._userSettings = None
        self._systemSettings = None
        self._topLevelWindows = []
        self._walkthroughs = []
        
        # setup the application preferences
        plugpath = os.path.join(os.path.dirname(QtCore.__file__), 'plugins')
        self.addLibraryPath(plugpath)
        
        # set default value
        projexui.stylize(self)
        
        self.setQuitOnLastWindowClosed(True)

    def autoCreateTrayIcon(self):
        """
        Returns whether or not this application should auto-create
        tray icon for the main window of this application.
        
        :return     <bool>
        """
        return self._autoCreateTrayIcon

    def cachePath(self):
        """
        Returns the cache location for this application.
        
        :return     <str>
        """
        return self.storagePath(QtGui.QDesktopServices.CacheLocation)

    def dataPath(self):
        """
        Returns the location for local user data for this application.
        
        :return     <str>
        """
        return self.storagePath(QtGui.QDesktopServices.DataLocation)

    def desktopPath(self):
        """
        Returns the location for the desktop for this user.
        
        :return     <str>
        """
        return self.storagePath(QtGui.QDesktopServices.DesktopLocation)

    def documentsPath(self):
        """
        Returns the location for the documents for this user.
        
        :return     <str>
        """
        return self.storagePath(QtGui.QDesktopServices.DocumentsLocation)

    def exec_(self):
        """
        Runs the main application for this instance and returns the
        success value.
        
        :return     <int>
        """
        # create the tray icon
        if self.autoCreateTrayIcon() and not self.trayIcon():
            try:
                window = self.topLevelWindows()[0]
            except IndexError:
                pass
            else:
                # create the menu
                menu = QtGui.QMenu(window)
                
                if self.applicationName():
                    act = menu.addAction('Quit {0}'.format(self.applicationName()))
                else:
                    act = menu.addAction('Quit')
                
                act.triggered.connect(self.quit)
                
                # create the tray icon
                icon = QtGui.QSystemTrayIcon()
                icon.setIcon(self.windowIcon())
                icon.setObjectName('trayIcon')
                icon.setContextMenu(menu)
                icon.setToolTip(self.applicationName())
                icon.show()
                
                self._trayIcon = icon
        
        result = super(XApplication, self).exec_()
        
        # save the settings before exiting
        self.saveSettings()
        return result

    def findWalkthrough(self, name):
        """
        Looks up the walkthrough based on the given name.
        
        :param      name | <str>
        """
        for walkthrough in self._walkthroughs:
            if walkthrough.name() == name:
                return walkthrough
        return None

    def fontsPath(self):
        """
        Returns the location for the fonts for this system.
        
        :return     <str>
        """
        return self.storageLocation(QtGui.QDesktopServices.FontsLocation)

    def homePath(self):
        """
        Returns the home directory for this user.
        
        :return     <str>
        """
        return self.homePath(QtGui.QDesktopServices.HomeLocation)

    def isCompiled(self):
        """
        Returns whether or not this application is running from a compiled
        version.
        
        :return     <bool>
        """
        return getattr(sys, 'frozen', False)

    def moviesPath(self):
        """
        Returns the path to the user's movies directory.
        
        :sa         storagePath
        
        :return     <str>
        """
        return self.storagePath(QtGui.QDesktopServices.MoviesLocation)

    def musicPath(self):
        """
        Returns the path to the user's music directory.
        
        :sa         storagePath
        
        :return     <str>
        """
        return self.storagePath(QtGui.QDesktopServices.MusicLocation)

    def picturesPath(self):
        """
        Returns the path to the user's pictures directory.
        
        :sa         storagePath
        
        :return     <str>
        """
        return self.storagePath(QtGui.QDesktopServices.PicturesLocation)

    def registerTopLevelWindow(self, window):
        """
        Registers a top level window for this application.
        
        :param      window | <QtGui.QMainWindow>
        """
        # set the main window for this instance
        if not self._topLevelWindows:
            self.setPalette(window.palette())
            self.setWindowIcon(window.windowIcon())
            
            if self.splash():
                self.splash().finish(window)
        
        self._topLevelWindows.append(weakref.ref(window))

    def registerWalkthrough(self, walkthrough):
        """
        Registers the inputed walkthrough to the system.
        
        :param      walkthrough | <XWalkthrough>
        """
        if not walkthrough in self._walkthroughs:
            self._walkthroughs.append(walkthrough)

    def restoreSettings(self):
        """
        Saves the settings for this application.
        """
        pass

    def saveSettings(self):
        """
        Saves the settings for this application.
        """
        pass

    def setupSplash(self, pixmap, align=None, color='white', cls=None):
        """
        Sets up a splash screen for the application for the given pixmap.
        
        :param      pixmap | <QtGui.QPixmap>
                    align  | <QtCore.Qt.Alignment>
                    color  | <QtGui.QColor>
                    cls    | <subclass of QtGui.QSplashScreen>
        
        :return     <QtGui.QSplashScreen>
        """
        if cls is None:
            cls = XLoggerSplashScreen
        if align is None:
            align = QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom
        
        color = QtGui.QColor('white')
        pixmap = QtGui.QPixmap(pixmap)
        screen = cls(splash)
        screen.setTextColor(color)
        screen.setTextAlignment(align)
        screen.show()
        self.processEvents()
        self._splash = screen
        return screen

    def setAutoCreateTrayIcon(self, state):
        """
        Sets whether or not this application should create a tray icon for the
        main window of this application.
        
        :param      state | <bool>
        """
        self._autoCreateTrayIcon = state

    def setCachePath(self, path):
        """
        Sets the location for the user's cache directory for this application.
        
        :param      path | <str>
        """
        self.setStoragePath(QtGui.QDesktopServices.CacheLocation, path)

    def setDataPath(self, path):
        """
        Sets the location for the user's data directory for this application.
        
        :param      path | <str>
        """
        self.setStoragePath(QtGui.QDesktopServices.DataLocation, path)

    def setDesktopPath(self, path):
        """
        Sets the location for the user's desktop directory for this application.
        
        :param      path | <str>
        """
        self.setStoragePath(QtGui.QDesktopServices.DesktopLocation, path)

    def setDocumentsPath(self, path):
        """
        Sets the location for the user's documents directory for this application.
        
        :param      path | <str>
        """
        self.setStoragePath(QtGui.QDesktopServices.DocumentsLocation, path)

    def setFontsPath(self, path):
        """
        Sets the location for the user's fonts directory for this application.
        
        :param      path | <str>
        """
        self.setStoragePath(QtGui.QDesktopServices.FontsLocation, path)

    def setHomePath(self, path):
        """
        Sets the location for the user's home directory for this application.
        
        :param      path | <str>
        """
        self.setStoragePath(QtGui.QDesktopServices.HomeLocation, path)

    def setMoveisPath(self, path):
        """
        Sets the location for the user's movie directory for this application.
        
        :param      path | <str>
        """
        self.setStoragePath(QtGui.QDesktopServices.MoviesLocation, path)

    def setPicturesPath(self, path):
        """
        Sets the location for the user's picture directory for this application.
        
        :param      path | <str>
        """
        self.setStoragePath(QtGui.QDesktopServices.PicturesLocation, path)

    def setSplash(self, splash):
        """
        Sets the splash screen for this application to the inputed splash.
        
        :param      splash | <QtGui.QSplashScreen> || None
        """
        self._splash = splash

    def setTempPath(self, path):
        """
        Sets the location for the user's temp directory for this application.
        
        :param      path | <str>
        """
        self.setStoragePath(QtGui.QDesktopServices.TempLocation, path)

    def setTrayIcon(self, icon):
        """
        Sets the tray icon for this application to this instance.
        
        :param      icon | <QtGui.QIcon>
        """
        self._trayIcon = icon
    
    def setStoragePath(self, location, path):
        """
        Returns the path associated with this application and user for the
        given location.
        
        :param      location | <QtGui.QDesktopServices.StandardLocation>
                    path | <str> || None
        
        :return     <str>
        """
        if not path:
            self._storagePaths.pop(location, None)
        else:
            self._storagePaths[location] = path

    def setSystemSettings(self, settings):
        """
        Sets the settings to be used for the system for this application.
        
        :param      settings | <QtCore.QSettings>
        """
        self._systemSettings = settings

    def setUserSettings(self, settings):
        """
        Sets the user settings for this application to the inputed settings.
        
        :param      settings | <QtCore.QSettings>
        """
        self._userSettings = settings
    
    def showMessage(self,
                    title,
                    message,
                    icon=QtGui.QSystemTrayIcon.Information,
                    timeout=10000):
        """
        Displays a message to the user via the tray icon.
        
        :param      title   | <str>
                    message | <str>
                    icon    | <QtGui.QSystemTrayIcon.MessageIcon>
                    timeout | <int>
        """
        tray = self.trayIcon()
        if tray:
            tray.showMessage(title, message, icon, timeout)

    def showWalkthrough(self, walkthrough, force=False):
        """
        Emits the walkthroughRequested signal to display the given 
        walkthrough information.  This can be either a string name for a
        standard walkthrough, or an actual walkthrough instance.
        
        :param      walkthrough | <str> || <XWalkthrough>
        """
        if type(walkthrough) in (str, unicode):
            walkthrough = self.findWalkthrough(walkthrough)

        if walkthrough:
            self.walkthroughRequested.emit(walkthrough, force)

    def splash(self):
        """
        Returns the splash screen associated with this application.
        
        :return     <QtGui.QSplashScreen> || None
        """
        return self._splash

    def startup(self):
        """
        Finalizes any application settings that need to be done on
        startup.
        """
        self.restoreSettings()

    def storagePath(self, location):
        """
        Returns the path associated with this application and user for the
        given location.
        
        :param      location | <QtGui.QDesktopServices.StandardLocation>
        
        :return     <str>
        """
        default = nativestring(QtGui.QDesktopServices.storageLocation(location))
        return self._storagePaths.get(location, default)

    def systemSettings(self):
        """
        Returns the settings associated with this application for all users.
        
        :return     <projexui.xsettings.XSettings>
        """
        if not self._systemSettings:
            if self.isCompiled():
                settings = QtCore.QSettings(XSettings.IniFormat,
                                            XSettings.SystemScope,
                                            self.organizationName(),
                                            self.applicationName())
                rootpath = os.path.dirname(settings.fileName())
            else:
                rootpath = os.path.abspath('.')

            name = self.applicationName()
            filename = os.path.join(rootpath, '{0}.yaml'.format(name))

            self._systemSettings = XSettings(XSettings.YamlFormat,
                                             XSettings.SystemScope,
                                             self.organizationName(),
                                             self.applicationName(),
                                             filename=filename)

        return self._systemSettings

    def topLevelWindows(self):
        """
        Returns a list of the top level windows for this application.
        
        :return     [<QtGui.QMainWindow>, ..]
        """
        out = []
        clean = []
        for ref in self._topLevelWindows:
            window = ref()
            if window is not None:
                clean.append(ref)
                out.append(window)

        self._topLevelWindows = clean
        return out

    def unregisterWalkthrough(self, walkthrough):
        """
        Unregisters the inputed walkthrough from the application walkthroug
        list.
        
        :param      walkthrough | <XWalkthrough>
        """
        if type(walkthrough) in (str, unicode):
            walkthrough = self.findWalkthrough(walkthrough)

        try:
            self._walkthroughs.remove(walkthrough)
        except ValueError:
            pass

    def userSettings(self):
        """
        Returns the settings associated with this application per user.
        
        :return     <QtCore.QSettings>
        """
        if not self._userSettings:
            name = self.applicationName()
            if not self.isCompiled():
                name + '.dev'
            
            self._userSettings = XSettings(XSettings.YamlFormat,
                                           XSettings.UserScope,
                                           self.organizationName(),
                                           name)

        return self._userSettings

    def tempPath(self):
        """
        Returns the path to the user's temp directory.
        
        :return     <str>
        """
        return self.storagePath(QtGui.QDesktopServices.TempLocation)

    def trayIcon(self):
        """
        Returns the tray icon associated with this application.
        
        :return     <QtGui.QIcon>
        """
        return self._trayIcon

    def walkthroughs(self):
        """
        Returns a list of the walkthroughs that are availble for this application.
        
        :return     [<XWalkthrough>, ..]
        """
        return self._walkthroughs

