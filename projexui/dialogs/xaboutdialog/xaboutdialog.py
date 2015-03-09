#!/usr/bin/python

""" Defines a generic, reusable about dialog to show tool info """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = ['Eric Hulser']
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

#------------------------------------------------------------------------------

import os.path

from projex.text import nativestring

from projexui.qt       import uic
from projexui.qt.QtGui import QDialog, \
                              QPixmap

class XAboutDialog( QDialog ):
    """ Defines the base about dialog class. """
    def __init__( self, parent = None ):
        super(XAboutDialog, self).__init__(parent)
        
        # load the ui
        uifile = os.path.join( os.path.dirname(__file__),'ui/xaboutdialog.ui' )
        uic.loadUi( uifile, self )
    
    def setLogo( self, logo ):
        """
        Sets the logo image for this dialog
        
        :param      logo | <QPixmap> || <str>
        """
        if ( isinstance(logo, basestring) ):
            logo = QPixmap(logo)
        
        self.uiLogoLBL.setHidden(logo.isNull())
        self.uiLogoLBL.setPixmap(logo)
    
    def setInfo( self, info ):
        """
        Sets the information to be displayed in the about section.
        
        :param      info    | <str>
        """
        self.uiInfoTXT.setText(info)
    
    # define static methods
    @staticmethod
    def aboutModule( module, parent = None, logo = '' ):
        """
        Displays about information for an inputed module.
        
        :param      module  | <module>
                    parent  | <QWidget>
                    logo    | <QPixmap> || <str>
        """
        
        dlg = XAboutDialog( parent )
        dlg.setLogo( logo )
        dlg.setInfo( XAboutDialog.moduleInfo(module) )
        
        dlg.exec_()
    
    @staticmethod
    def about( info, parent = None, logo = '' ):
        """
        Displays about information in a popup dialog.
        
        :param      info    | <str>
                    parent  | <QWidget>
                    logo    | <QPixmap> || <str>
        """
        
        dlg = XAboutDialog(parent)
        dlg.setLogo(logo)
        dlg.setInfo(info)
        
        dlg.exec_()
    
    @staticmethod
    def moduleInfo( module ):
        """
        Generates HTML information to display for the about info for a module.
        
        :param      module  | <module>
        """
        data = module.__dict__
        
        html = []
        html.append( '<h2>%s</h2>' % data.get('__name__', 'Unknown') )
        html.append( '<hr/>' )
        ver = data.get('__version__', '0')
        html.append( '<small>version: %s</small>' % ver)
        html.append( '<br/>' )
        html.append( nativestring(data.get('__doc__', '')) )
        html.append( '<br/><br/><b>Authors</b><ul/>' )
        
        for author in data.get('__authors__', []):
            html.append( '<li>%s</li>' % author )
            
        html.append( '</ul>' )
        html.append( '<br/><br/><b>Depends on:</b>' )
        for depends in data.get('__depends__', []):
            html.append( '<li>%s</li>' % depends )
            
        html.append( '</ul>' )
        html.append( '' )
        html.append( '<br/><br/><b>Credits</b></ul>' )
        
        for credit in data.get('__credits__', []):
            html.append('<li>%s: %s</li>' % credit)
            
        html.append( '</ul>' )
        
        opts = (data.get('__maintainer__', ''), data.get('__email__', ''))
        html.append('<br/><br/><small>maintained by: %s email: %s</small>' % opts)
        
        opts = (data.get('__copyright__', ''), data.get('__license__', ''))
        html.append('<br/><small>%s | license: %s</small>' % opts)
        
        return '\n'.join(html)