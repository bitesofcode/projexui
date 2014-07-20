#!/usr/bin python

""" Manages multiple profiles for the system. """

# define authorship information
__authors__     = ['Eric Hulser']
__author__      = ','.join(__authors__)
__credits__     = []
__copyright__   = 'Copyright (c) 2011, Projex Software'

# maintanence information
__maintainer__  = 'Projex Software'
__email__       = 'team@projexsoftware.com'

from projexui.qt import Signal, unwrapVariant, wrapVariant, PyObject
from projexui.qt.QtCore import QPoint,\
                               Qt

from projexui.qt.QtGui import QComboBox, \
                              QToolButton,\
                              QHBoxLayout,\
                              QIcon,\
                              QWidget

from projexui import resources
from projexui.widgets.xviewwidget.xviewprofile   import XViewProfile
from projexui.widgets.xviewwidget.xviewprofilemanagermenu \
                                import XViewProfileManagerMenu

class XViewProfileManager(QWidget):
    currentProfileChanged = Signal(PyObject)
    optionsMenuRequested  = Signal(QPoint)
    
    def __init__(self, parent=None):
        super(XViewProfileManager, self).__init__(parent)
        
        # define custom properties
        self._profiles           = []
        self._optionsMenuPolicy  = Qt.DefaultContextMenu
        self._viewWidget         = None
        
        # define the interface
        self._profileCombo  = QComboBox(self)
        self._optionsButton = QToolButton(self)
        self._optionsButton.setAutoRaise(True)
        self._optionsButton.setToolTip('Advanced Options')
        self._optionsButton.setIcon(QIcon(resources.find('img/advanced.png')))
        
        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addWidget(self._profileCombo)
        layout.addWidget(self._optionsButton)
        
        self.setLayout(layout)
        
        # create connections
        self._profileCombo.currentIndexChanged.connect(self.handleProfileChange)
        self._optionsButton.clicked.connect(self.showOptionsMenu)
    
    def addProfile(self, profile):
        """
        Adds the inputed profile to the system.
        
        :param      profile | <XViewProfile>
        """
        if ( profile in self._profiles ):
            return
        
        self._profiles.append(profile)
        self._profileCombo.blockSignals(True)
        self._profileCombo.addItem(profile.name())
        self._profileCombo.setCurrentIndex(self._profileCombo.count()-1)
        self._profileCombo.blockSignals(False)
    
    def currentProfile(self):
        """
        Returns the currently selected profile from the system.
        
        :return     <XViewProfile>
        """
        index = self._profileCombo.currentIndex()
        
        if 0 <= index and index < len(self._profiles):
            return self._profiles[index]
        return None
    
    def handleProfileChange(self):
        """
        Emits that the current profile has changed.
        """
        # restore the profile settings
        prof    = self.currentProfile()
        vwidget = self.viewWidget()
        if vwidget:
            prof.restore(vwidget)
        
        if not self.signalsBlocked():
            self.currentProfileChanged.emit(self.currentProfile())
    
    def optionsMenuPolicy(self):
        """
        Returns the option menu policy for this widget.
        
        :return     <Qt.MenuPolicy>
        """
        return self._optionsMenuPolicy
    
    def profiles(self):
        """
        Returns a list of all the profiles for this system.
        
        :return     [<XViewProfile>, ..]
        """
        return self._profiles
    
    def removeProfile(self, profile):
        """
        Adds the inputed profile to the system.
        
        :param      profile | <XViewProfile>
        """
        if not profile in self._profiles:
            return
        
        index = self._profiles.index(profile)
        self._profiles.remove(profile)
        self._profileCombo.blockSignals(True)
        self._profileCombo.takeItem(index)
        self._profileCombo.blockSignals(False)
    
    def restoreSettings(self, settings):
        """
        Restores settings from the application.
        
        :param      settings | <QSettings>
        """
        settings.beginGroup(self.objectName())
        
        curr_prof = None
        curr_name = unwrapVariant(settings.value('current'))
        
        profiles = []
        for prof_name in settings.childGroups():
            settings.beginGroup(prof_name)
            
            prof_str = unwrapVariant(settings.value('profile'))
            profile  = XViewProfile.fromString(prof_str)
            profile.setName(prof_name)
            
            if prof_name == curr_name:
                curr_prof = profile
            
            profiles.append(profile)
            
            settings.endGroup()
        
        self.blockSignals(True)
        self._profileCombo.blockSignals(True)
        self.setProfiles(profiles)
        
        if curr_prof:
            self.setCurrentProfile(curr_prof)
        
        self._profileCombo.blockSignals(False)
        self.blockSignals(False)
        
        settings.endGroup()
    
    def saveSettings(self, settings):
        """
        Saves the settings for this widget to the application
        
        :param      settings | <QSettings>
        """
        settings.beginGroup(self.objectName())
        
        curr_prof = self.currentProfile()
        if curr_prof:
            settings.setValue('current', curr_prof.name())
        
        for profile in self.profiles():
            settings.beginGroup(profile.name())
            settings.setValue('profile', wrapVariant(profile.toString()))
            settings.endGroup()
        
        settings.endGroup()
    
    def setCurrentProfile(self, profile):
        """
        Sets the current profile to the inputed profile.
        
        :param      profile | <XViewProfile>
        """
        try:
            index = self._profiles.index(profile)
        except ValueError:
            index = -1
        
        self._profileCombo.setCurrentIndex(index)
    
    def setOptionsMenuPolicy(self, menuPolicy):
        """
        Sets the options menu policy for this item.
        
        :param      menuPolicy | <Qt.MenuPolicy>
        """
        self._optionsMenuPolicy = menuPolicy
    
    def setProfiles(self, profiles):
        """
        Sets a list of profiles to be the options for the manager.
        
        :param      profiles | [<XViewProfile>, ..]
        """
        self.blockSignals(True)
        self._profileCombo.blockSignals(True)
        
        self._profiles = profiles[:]
        self._profileCombo.clear()
        self._profileCombo.addItems(map(lambda x: x.name(), profiles))
        
        self._profileCombo.blockSignals(False)
        self.blockSignals(False)
    
    def setViewWidget(self, viewWidget):
        """
        Sets the view widget instance linked with this manager.
        
        :param      viewWidget | <XViewWidget>
        """
        self._viewWidget = viewWidget
    
    def showOptionsMenu(self):
        """
        Displays the options menu.  If the option menu policy is set to 
        CustomContextMenu, then the optionMenuRequested signal will be emitted,
        otherwise the default context menu will be displayed.
        """
        point        = QPoint(0, self._optionsButton.height())
        global_point = self._optionsButton.mapToGlobal(point)
        
        # prompt the custom context menu
        if self.optionsMenuPolicy() == Qt.CustomContextMenu:
            if not self.signalsBlocked():
                self.optionsMenuRequested.emit(global_point)
            return
        
        # use the default context menu
        menu = XViewProfileManagerMenu(self)
        menu.exec_(global_point)
    
    def viewWidget(self):
        """
        Returns the view widget that is associated with this manager.
        
        :return     <XViewWidget>
        """
        return self._viewWidget