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

from projex.text import nativestring
from projexui.qt.QtGui import QMenu,\
                              QIcon,\
                              QMessageBox,\
                              QInputDialog

from projexui import resources

class XViewProfileManagerMenu(QMenu):
    def __init__( self, manager ):
        super(XViewProfileManagerMenu, self).__init__(manager)
        
        # create actions
        act = self.addAction('Save Profile')
        act.setIcon(QIcon(resources.find('img/save.png')))
        act.setEnabled(manager.currentProfile() is not None)
        act.triggered.connect( self.saveProfile )
        
        act = self.addAction('Save Profile as...')
        act.setIcon(QIcon(resources.find('img/save_as.png')))
        act.setEnabled(manager.viewWidget() is not None)
        act.triggered.connect( self.saveProfileAs )
        
        self.addSeparator()
        act = self.addAction('Remove Profile')
        act.setIcon(QIcon(resources.find('img/remove.png')))
        act.setEnabled(manager.currentProfile() is not None)
        act.triggered.connect( self.removeProfile )
    
    def removeProfile( self ):
        """
        Removes the current profile from the system.
        """
        manager  = self.parent()
        prof     = manager.currentProfile()
        opts     = QMessageBox.Yes | QMessageBox.No
        question = 'Are you sure you want to remove "%s"?' % prof.name()
        answer   = QMessageBox.question( self, 'Remove Profile', question, opts)
        
        if ( answer == QMessageBox.Yes ):
            manager.removeProfile(prof)
    
    def saveProfile( self ):
        """
        Saves the current profile to the current settings from the view widget.
        """
        manager = self.parent()
        prof    = manager.currentProfile()
        
        # save the current profile
        save_prof = manager.viewWidget().saveProfile()
        prof.setXmlElement(save_prof.xmlElement())
    
    def saveProfileAs( self ):
        """
        Saves the current profile as a new profile to the manager.
        """
        name, ok = QInputDialog.getText(self, 'Create Profile', 'Name:')
        if ( not name ):
            return
        
        manager = self.parent()
        prof    = manager.viewWidget().saveProfile()
        prof.setName(nativestring(name))
        self.parent().addProfile(prof)
    