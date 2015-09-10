""" [desc] """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software, LLC'
__license__         = 'LGPL'

__maintainer__      = 'Projex Software, LLC'
__email__           = 'team@projexsoftware.com'


#------------------------------------------------------------------------------

from projexui.qt.QtGui import QDialog, QMessageBox

import projexui
from projex.text import nativestring
from projexui import resources

from projexui.widgets.xviewwidget.xviewprofile import XViewProfile

class XViewProfileDialog(QDialog):
    """ """
    def __init__( self, parent = None ):
        super(XViewProfileDialog, self).__init__( parent )
        
        # load the user interface
        projexui.loadUi(__file__, self)
        
        # define custom properties
        self._profile = None
        
    def accept( self ):
        """
        Saves the data to the profile before closing.
        """
        if ( not self.uiNameTXT.text() ):
            QMessageBox.information(self,
                                   'Invalid Name',
                                   'You need to supply a name for your layout.')
            return
        
        prof = self.profile()
        if ( not prof ):
            prof = XViewProfile()
        
        prof.setName(nativestring(self.uiNameTXT.text()))
        prof.setVersion(self.uiVersionSPN.value())
        prof.setDescription(nativestring(self.uiDescriptionTXT.toPlainText()))
        prof.setIcon(self.uiIconBTN.filepath())
        
        super(XViewProfileDialog, self).accept()
    
    def profile( self ):
        """
        Returns the profile linked with this dialog.
        
        :return     <projexui.widgets.xviewwidget.XViewProfile> || None
        """
        return self._profile
    
    def setProfile( self, profile ):
        """
        Sets the profile instance for this dialog to the inputed profile.
        
        :param      profile | <projexui.widgets.xviewwidget.XViewProfile>
        """
        self._profile = profile
        
        if not profile:
            self.uiNameTXT.setText('')
            self.uiVersionSPN.setValue(1.0)
            self.uiDescriptionTXT.setText('')
            self.uiIconBTN.setFilepath(resources.find('img/profile_48.png'))
        else:
            self.uiNameTXT.setText(profile.name())
            self.uiVersionSPN.setValue(profile.version())
            self.uiDescriptionTXT.setText(profile.description())
            
            filepath = profile.icon()
            if ( not filepath ):
                filepath = resources.find('img/profile_48.png')
            self.uiIconBTN.setFilepath(filepath)
    
    def setVisible( self, state ):
        """
        Handles the visibility operation for this dialog.
        
        :param      state | <bool>
        """
        super(XViewProfileDialog, self).setVisible(state)
        
        if ( state ):
            self.activateWindow()
            self.uiNameTXT.setFocus()
            self.uiNameTXT.selectAll()
    
    @staticmethod
    def edit(parent, profile):
        """
        Edits the given profile.
        
        :param      parent  | <QWidget>
                    profile | <projexui.widgets.xviewwidget.XViewProfile>
        
        :return     <bool>
        """
        dlg = XViewProfileDialog(parent)
        dlg.setProfile(profile)
        if ( dlg.exec_() ):
            return True
        return False
