#!/usr/bin/python

"""
Extends the base QLineEdit class to support some additional features like \
setting hints on line edits.
"""

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftwaurlre.com'

#------------------------------------------------------------------------------

import os.path
import urllib

from projex.text import nativestring

import projexui
from projexui.qt import Signal, Property
from projexui.qt.QtCore import QDir
from projexui.qt.QtGui import QPushButton,\
                              QFileDialog,\
                              QIcon

import projexui.resources

class XIconButton(QPushButton):
    """ """
    __designer_icon__ = projexui.resources.find('img/ui/icon.png')
    
    filepathChanged = Signal(str)
    
    def __init__( self, parent = None ):
        super(XIconButton, self).__init__( parent )
        
        # define custom properties
        self._filepath  = ''
        self._fileTypes = 'PNG Files (*.png);;All Files (*.*)'
        
        # set default properties
        self.setFixedWidth( 64 )
        self.setFixedHeight( 64 )
        self.setAcceptDrops(True)
        
        # create connections
        self.clicked.connect( self.pickFilepath )
    
    def filepath( self ):
        """
        Returns the filepath for this button.
        
        :return     <str>
        """
        return self._filepath
    
    def fileTypes( self ):
        """
        Returns the file types that will be used to filter this button.
        
        :return     <str>
        """
        return self._fileTypes
    
    def dragEnterEvent( self, event ):
        """
        Handles a drag enter event.
        
        :param      event | <QEvent>
        """
        if ( event.mimeData().hasUrls() ):
            event.acceptProposedAction()
    
    def dragMoveEvent( self, event ):
        """
        Handles a drag move event.
        
        :param      event | <QEvent>
        """
        if ( event.mimeData().hasUrls() ):
            event.acceptProposedAction()
    
    def dropEvent( self, event ):
        """
        Handles a drop event.
        """
        url  = event.mimeData().urls()[0]
        url_path = nativestring(url.toString())
        
        # download an icon from the web
        if ( not url_path.startswith('file:') ):
            filename = os.path.basename(url_path)
            temp_path = os.path.join(nativestring(QDir.tempPath()), filename)
            
            try:
                urllib.urlretrieve(url_path, temp_path)
            except IOError:
                return
            
            self.setFilepath(temp_path)
        else:
            self.setFilepath(url_path.replace('file://', ''))
    
    def pickFilepath( self ):
        """
        Picks the image file to use for this icon path.
        """
        filepath = QFileDialog.getOpenFileName( self,
                                                'Select Image File',
                                                QDir.currentPath(),
                                                self.fileTypes())
        
        if type(filepath) == tuple:
            filepath = nativestring(filepath[0])
        
        if ( filepath ):
            self.setFilepath(filepath)
    
    def setFilepath( self, filepath ):
        """
        Sets the filepath for this button to the inputed path.
        
        :param      filepath | <str>
        """
        self._filepath = nativestring(filepath)
        self.setIcon(QIcon(filepath))
        if ( not self.signalsBlocked() ):
            self.filepathChanged.emit(filepath)
    
    def setFileTypes( self, fileTypes ):
        """
        Sets the filetypes for this button to the inputed types.
        
        :param      fileTypes | <str>
        """
        self._fileTypes = fileTypes
    
    @staticmethod
    def buildIcon(icon):
        """
        Builds an icon from the inputed information.
        
        :param      icon | <variant>
        """
        if icon is None:
            return QIcon()
        
        if type(icon) == buffer:
            try:
                icon = QIcon(projexui.generatePixmap(icon))
            except:
                icon = QIcon()
        else:
            try:
                icon = QIcon(icon)
            except:
                icon = QIcon()
        
        return icon

    x_filepath  = Property(str, filepath, setFilepath)
    x_fileTypes = Property(str, fileTypes, setFileTypes)

__designer_plugins__ = [XIconButton]