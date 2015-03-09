""" Defines the XViewProfileToolBar class """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software, LLC'
__license__         = 'LGPL'

__maintainer__      = 'Projex Software, LLC'
__email__           = 'team@projexsoftware.com'

import os.path

from projex.text import nativestring

from projexui.qt import Signal,\
                        Slot,\
                        Property,\
                        PyObject,\
                        wrapVariant,\
                        unwrapVariant
from projexui.qt.QtCore import Qt,\
                               QSize

from projexui.qt.QtGui import QAction,\
                              QActionGroup,\
                              QApplication,\
                              QCursor,\
                              QIcon,\
                              QMenu,\
                              QMessageBox,\
                              QFileDialog,\
                              QToolBar,\
                              QWidgetAction

from xml.etree          import ElementTree
from xml.parsers.expat  import ExpatError

import projex.text

from projexui import resources
from projexui.widgets.xtoolbar import XToolBar
from projexui.widgets.xtoolbutton import XToolButton
from projexui.widgets.xviewwidget.xviewprofile import XViewProfile
from projexui.widgets.xviewwidget.xviewprofiledialog import XViewProfileDialog

class XViewProfileAction(QWidgetAction):
    def __init__(self, profile, parent=None):
        super(XViewProfileAction, self).__init__(parent)
        
        # create custom properties
        self._profile = None
        
        # set default options
        self.setCheckable(True)
        self.setProfile(profile)
    
    def createWidget(self, parent):
        btn = XToolButton(parent)
        btn.setDefaultAction(self)
        btn.setCheckable(self.isCheckable())
        btn.setChecked(self.isChecked())
        return btn
    
    def profile(self):
        """
        Returns the profile linked with this action.
        
        :return     <projexui.widgets.xviewwidget.XViewProfile>
        """
        return self._profile
    
    def setProfile(self, profile):
        """
        Sets the profile linked with this action.
        
        :param      profile | <projexui.widgets.xviewwidget.XViewProfile>
        """
        self._profile = profile
        
        # update the interface
        self.setIcon(profile.icon())
        self.setText(profile.name())
        self.setToolTip(profile.description())

#------------------------------------------------------------------------------

class XViewProfileToolBar(XToolBar):
    profileCreated              = Signal(PyObject)
    profileChanged              = Signal(PyObject)
    profileRemoved              = Signal(PyObject)
    profilesChanged             = Signal()
    currentProfileChanged       = Signal(PyObject)
    loadProfileFinished         = Signal(PyObject)
    newWindowProfileRequested   = Signal(PyObject)
    
    def __init__(self, parent):
        super(XViewProfileToolBar, self).__init__(parent)
        
        # create custom properties
        self._editingEnabled    = True
        self._viewWidget        = None
        self._profileText       = 'Profile'
        self._profileGroup      = QActionGroup(self)
        self._currentProfile    = None
        
        # set the default options
        self.setIconSize(QSize(48, 48))
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # create connections
        self.actionTriggered.connect(self.handleActionTrigger)
        self.customContextMenuRequested.connect(self.showProfileMenu)
        
    def addProfile(self, profile):
        """
        Adds the inputed profile as an action to the toolbar.
        
        :param      profile | <projexui.widgets.xviewwidget.XViewProfile>
        """
        # use the existing version
        for exist in self.profiles():
            if exist.name() == profile.name():
                if exist.version() < profile.version():
                    exist.setProfile(profile)
                
                return
        
        # otherwise create a new profile 
        act = XViewProfileAction(profile, self)
        self._profileGroup.addAction(act)
        self.addAction(act)
        return act
    
    def clearActive(self):
        # clear the GUI
        self.blockSignals(True)
        for act in self.actions():
            act.blockSignals(True)
            act.setChecked(False)
            act.blockSignals(False)
        self.blockSignals(False)
        
        self._currentProfile = None
        
        # reset the layout
        widget = self.viewWidget()
        if self.sender() != widget:
            widget.reset(force=True)
            widget.setLocked(False)
        
        self.currentProfileChanged.emit(None)

    def currentProfile(self):
        """
        Returns the current profile for this toolbar.
        
        :return     <projexui.widgets.xviewwidget.XViewProfile> || None
        """
        return self._currentProfile
    
    def createProfile(self, profile=None, clearLayout=True):
        """
        Prompts the user to create a new profile.
        """
        if profile:
            prof = profile
        elif not self.viewWidget() or clearLayout:
            prof = XViewProfile()
        else:
            prof = self.viewWidget().saveProfile()
        
        blocked = self.signalsBlocked()
        self.blockSignals(False)
        changed = self.editProfile(prof)
        self.blockSignals(blocked)
        
        if not changed:
            return
        
        act = self.addProfile(prof)
        act.setChecked(True)
        
        # update the interface
        if self.viewWidget() and (profile or clearLayout):
            self.viewWidget().restoreProfile(prof)
        
        if not self.signalsBlocked():
            self.profileCreated.emit(prof)
            self.profilesChanged.emit()
    
    @Slot(PyObject)
    def editProfile(self, profile):
        """
        Prompts the user to edit the given profile.
        
        :param      profile | <projexui.widgets.xviewwidget.XViewProfile>
        """
        mod = XViewProfileDialog.edit(self.window(), profile)
        if not mod:
            return False
        
        # update the action interface
        for act in self._profileGroup.actions():
            if act.profile() == profile:
                act.setProfile(profile)
                break
        
        # signal the change
        if not self.signalsBlocked():
            self.profileChanged.emit(profile)
            self.profilesChanged.emit()
        
        return True
    
    def exportProfile(self, profile, filename=None):
        """
        Exports this toolbar to the given filename.
        
        :param      profile  | <XViewProfile>
                    filename | <str> || None
        """
        if not filename:
            filename = QFileDialog.getSaveFileName(self,
                                                   'Export Profile',
                                                   '',
                                                   'XML Files (*.xml)')
            if type(filename) == tuple:
                filename = nativestring(filename[0])
        
        if not filename:
            return False
        
        profile.save(filename)
        return True
    
    def handleActionTrigger(self, action):
        """
        Handles when an action has been triggered.  If the inputed action is a 
        XViewProfileAction, then the currentProfileChanged signal will emit.
        
        :param      action | <QAction>
        """
        # trigger a particular profile
        if isinstance(action, XViewProfileAction):
            # if the user CTRL+Clicks on the action, then attempt
            # to load it in a new window
            if QApplication.keyboardModifiers() == Qt.ControlModifier:
                self.newWindowProfileRequested.emit(action.profile())
                self.setCurrentProfile(self.currentProfile())
                return
            else:
                self.setCurrentProfile(action.profile())
    
    def importProfile(self, filename=None):
        """
        Imports the profiles from the given filename.
        
        :param      filename | <str> || None
        """
        if not filename:
            filename = QFileDialog.getOpenFileName( self,
                                                    'Import Perspective',
                                                    '',
                                                    'XML Files (*.xml)')
            
            if type(filename) == tuple:
                filename = nativestring(filename[0])
            
        if not (filename and os.path.exists(filename)):
            return False
        
        prof = XViewProfile.load(filename)
        if prof:
            self.addProfile(prof)
    
    def isEditingEnabled(self):
        """
        Sets whether or not the create is enabled for this toolbar.
        
        :return     <bool>
        """
        return self._editingEnabled
    
    def isEmpty(self):
        """
        Returns whether or not this toolbar is empty.
        
        :return     <bool>
        """
        return len(self._profileGroup.actions()) == 0
    
    def loadString(self, profilestr, merge=False, loadProfile=True):
        """
        Loads the information for this toolbar from the inputed string.
        
        :param      profilestr | <str>
        """
        try:
            xtoolbar = ElementTree.fromstring(nativestring(profilestr))
        except ExpatError, e:
            return
        
        if not merge:
            self.clear()
        
        self.blockSignals(True)
        for xprofile in xtoolbar:
            prof = XViewProfile.fromXml(xprofile)
            
            if merge:
                self.removeProfile(prof.name(), silent=True)
            
            self.addProfile(prof)

        self.setCurrentProfile(xtoolbar.get('current'))
        
        self.blockSignals(False)
        self.profilesChanged.emit()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MidButton:
            action = self.actionAt(event.pos())
            if action:
                self.newWindowProfileRequested.emit(action.profile())
    
    def profiles(self):
        """
        Returns a list of profiles for this toolbar.
        
        :return     <projexui.widgets.xviewwidget.XViewProfile>
        """
        output = []
        for act in self.actions():
            if ( isinstance(act, XViewProfileAction) ):
                output.append(act.profile())
        return output
    
    def profileText(self):
        """
        Returns the display text to use for the word "Profile" not all
        applications will refer to profiles in the same fashion.
        
        :return     <str>
        """
        return self._profileText
    
    def restoreSettings(self, settings, merge=False, loadProfile=True):
        """
        Restores this profile from settings.
        
        :param      settings | <QSettings>
        """
        value = unwrapVariant(settings.value('profile_toolbar'))
        if not value:
            return
        
        self.loadString(value, merge, loadProfile=loadProfile)
    
    @Slot(PyObject)
    def removeProfile(self, profile, silent=False):
        """
        Removes the given profile from the toolbar.
        
        :param      profile | <projexui.widgets.xviewwidget.XViewProfile>
        """
        if not profile:
            return
        
        if not silent:
            title = 'Remove {0}'.format(self.profileText())
            opts  = QMessageBox.Yes | QMessageBox.No
            quest = 'Are you sure you want to remove "%s" from the toolbar?'
            quest %= profile.name() if isinstance(profile, XViewProfile) else profile
            answer = QMessageBox.question(self.window(), title, quest, opts)
        else:
            answer = QMessageBox.Yes
        
        if answer == QMessageBox.Yes:
            reset = profile == self.currentProfile()
            if not reset:
                try:
                    reset = profile == self.currentProfile().name()
                except AttributeError:
                    reset = False
            
            if reset and self.viewWidget():
                self.viewWidget().reset(True)
            
            # remove the actions from this toolbar
            removed = []
            for act in self.actions():
                if not isinstance(act, XViewProfileAction):
                    continue
                if not profile in (act.profile(), act.text()):
                    continue
                
                removed.append(act.profile())
                self.removeAction(act)
                self._profileGroup.removeAction(act)
                act.deleteLater()
            
            if not self.signalsBlocked() and removed:
                for prof in removed:
                    self.profileRemoved.emit(prof)
                self.profilesChanged.emit()
    
    def setEditingEnabled(self, state):
        """
        Sets whether or not the creation is enabled for this toolbar.
        
        :param      state | <bool>
        """
        self._editingEnabled = state
    
    def setViewWidget(self, viewWidget):
        """
        Sets the view widget linked with this toolbar.
        
        :param      viewWidget | <XViewWidget>
        """
        self._viewWidget = viewWidget
        if viewWidget:
            viewWidget.resetFinished.connect(self.clearActive)
    
    def saveSettings(self, settings):
        """
        Saves these profiles as settings.
        
        :param      settings | <QSettings>
        """
        settings.setValue('profile_toolbar', wrapVariant(self.toString()))
    
    def saveProfileAs(self):
        self.createProfile(clearLayout=False)
    
    def saveProfileLayout(self, profile):
        """
        Saves the profile layout to the inputed profile.
        
        :param      profile | <projexui.widgets.xviewwidget.XViewProfile>
        """
        if not self.viewWidget():
            text = self.profileText()
            QMessageBox.information(self.window(), 
                                    'Could Not Save {0}'.format(text),
                                    'Error saving layout, '\
                                    'No View Widget Assigned')
            return
        
        # save the profile from the view widget
        prof = self.viewWidget().saveProfile()
        profile.setXmlElement(prof.xmlElement())
        
        if not self.signalsBlocked():
            self.profileChanged.emit(profile)
    
    @Slot(PyObject)
    def setCurrentProfile(self, prof):
        """
        Sets the current profile for this toolbar to the inputed profile.
        
        :param      prof | <projexui.widgets.xviewwidget.XViewProfile> || <str>
        """
        if prof is None:
            self.clearActive()
            return
        
        # loop through the profiles looking for a match
        profile = None
        blocked = self.signalsBlocked()
        self.blockSignals(True)
        for act in self._profileGroup.actions():
            if prof in (act.profile(), act.profile().name()):
                act.setChecked(True)
                profile = act.profile()
            else:
                act.setChecked(False)
        self.blockSignals(blocked)
        
        # update the current profile
        if profile == self._currentProfile and not self._viewWidget.isEmpty():
            return
        
        self._currentProfile = profile
        if self._viewWidget and profile and not blocked:
            self._viewWidget.restoreProfile(profile)
        
        if not blocked:
            self.loadProfileFinished.emit(profile)
            self.currentProfileChanged.emit(profile)
    
    def setProfileText(self, text):
        """
        Defines the display text to use for the word "Profile" not all
        applications will refer to profiles in the same fashion.
        
        :param      text | <str>
        """
        self._profileText = text
    
    def showProfileMenu(self, point):
        """
        Prompts the user for profile menu options.  Editing needs to be enabled
        for this to work.
        """
        if not self.isEditingEnabled():
            return
        
        trigger = self.actionAt(point)
        if (isinstance(trigger, XViewProfileAction)):
            prof = trigger.profile()
        else:
            prof = None
        
        # define the menu
        menu = QMenu(self)
        acts = {}
        text = self.profileText()
        
        # user right clicked on a profile
        if prof:
            acts['edit'] = menu.addAction('Edit {0}...'.format(text))
            acts['save'] = menu.addAction('Save Layout')
            
            menu.addSeparator()
            
            acts['copy'] = menu.addAction('Copy {0}'.format(text))
            acts['export'] = menu.addAction('Export {0}...'.format(text))
            
            menu.addSeparator()
            
            acts['remove'] = menu.addAction('Delete {0}'.format(text))
        
        # show toolbar options
        else:
            acts['new'] = menu.addAction('New Layout'.format(text))
            
            menu.addSeparator()
            
            acts['save_as'] = menu.addAction('Save Layout as...')
            
            if QApplication.clipboard().text():
                acts['paste'] = menu.addAction('Paste {0}'.format(text))
            acts['import'] = menu.addAction('Import {0}...'.format(text))
        
        for key, act in acts.items():
            act.setIcon(QIcon(resources.find('img/{0}.png'.format(key))))
        
        # run the menu
        act = menu.exec_(QCursor.pos())
        
        # create a new profile
        if act is None:
            return
        
        elif act == acts.get('new'):
            self.clearActive()
        
        # create a new clear profile
        elif act == acts.get('save_as'):
            self.saveProfileAs()
        
        # edit an existing profile
        elif act == acts.get('edit'):
            self.editProfile(prof)
        
        # save or create a new profile
        elif act == acts.get('save'):
            self.saveProfileLayout(prof)
            
        # copy profile
        elif act == acts.get('copy'):
            QApplication.clipboard().setText(prof.toString())
        
        # export
        elif act == acts.get('export'):
            self.exportProfile(prof)
        
        # export
        elif act == acts.get('import'):
            self.importProfile()
        
        # paste profile
        elif act == acts.get('paste'):
            text = QApplication.clipboard().text()
            try:
                prof = XViewProfile.fromString(text)
            except:
                prof = None
                QMessageBox.information(self.window(),
                                        'Invalid {0}'.format(text),
                                        'The clipboard text does not contain '\
                                        'a properly formated {0}'.format(text))
                
            if prof and not prof.isEmpty():
                self.createProfile(profile=prof)
        
        # paste as profile
        elif act == acts.get('paste_as'):
            text = QApplication.clipboard().text()
            prof = XViewProfile.fromString(text)
            if not prof.isEmpty():
                if XViewProfileDialog.edit(self, prof):
                    self.createProfile(profile=prof)
        
        # remove the profile
        elif act == acts.get('remove'):
            self.removeProfile(prof)
    
    def toString(self):
        """
        Saves this profile toolbar as string information.
        
        :return     <str>
        """
        return ElementTree.tostring(self.toXml())
    
    def toXml(self):
        """
        Saves this profile toolbar as XML information.
        
        :return     <xml.etree.ElementTree.Element>
        """
        xtoolbar = ElementTree.Element('toolbar')
        
        prof = self._currentProfile
        if prof is not None:
            xtoolbar.set('current', prof.name())
        
        for profile in self.profiles():
            profile.toXml(xtoolbar)
        
        return xtoolbar
    
    def viewWidget(self):
        """
        Returns the view widget linked with this toolbar.
        
        :return     <projexui.widgets.xviewwidget.XViewWidget>
        """
        return self._viewWidget
    
    x_editingEnabled = Property(bool, isEditingEnabled, setEditingEnabled)
