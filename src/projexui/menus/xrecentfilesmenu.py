#!/usr/bin/python

""" Defines reusable menu's for Qt applications """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

#------------------------------------------------------------------------------

import os.path

from projex.text import nativestring

from projexui.qt import Signal, wrapVariant, unwrapVariant
from projexui.qt.QtGui import QMenu

class XRecentFilesMenu(QMenu):
    fileTriggered = Signal(str)
    
    def __init__( self, parent ):
        super(XRecentFilesMenu, self).__init__(parent)
        
        # set menu properties
        self.setTitle('Recent Files')
        
        # set custom properties
        self._maximumLength = 10
        self._filenames     = []
        
        self.triggered.connect( self.emitFileTriggered )
        
    def addFilename( self, filename ):
        """
        Adds a new filename to the top of the list.  If the filename is \
        already loaded, it will be moved to the front of the list.
        
        :param          filename | <str>
        """
        filename = os.path.normpath(nativestring(filename))
        
        if filename in self._filenames:
            self._filenames.remove(filename)
        
        self._filenames.insert(0, filename)
        self._filenames = self._filenames[:self.maximumLength()]
        
        self.refresh()

    def emitFileTriggered( self, action ):
        """
        Emits that the filename has been triggered for the inputed action.
        
        :param      action | <QAction>
        """
        if not self.signalsBlocked():
            filename = nativestring(unwrapVariant(action.data()))
            self.fileTriggered.emit(filename)
    
    def filenames( self ):
        """
        Returns a list of filenames that are currently being cached for this \
        recent files menu.
        
        :return     [<str>, ..]
        """
        return self._filenames
    
    def maximumLength( self ):
        """
        Returns the maximum number of files to cache for this menu at one time.
        
        :return     <int>
        """
        return self._maximumLength
    
    def refresh( self ):
        """
        Clears out the actions for this menu and then loads the files.
        """
        self.clear()
        
        for i, filename in enumerate(self.filenames()):
            name   = '%i. %s' % (i+1, os.path.basename(filename))
            action = self.addAction(name)
            action.setData(wrapVariant(filename))
    
    def restoreSettings(self, settings):
        """
        Restores the files for this menu from the settings.
        
        :param      settings | <QSettings>
        """
        value = unwrapVariant(settings.value('recent_files'))
        if value:
            self.setFilenames(value.split(os.path.pathsep))
    
    def saveSettings(self, settings):
        """
        Saves the files for this menu to the settings.
        
        :param      settings | <QSettings>
        """
        value = wrapVariant(os.path.pathsep.join(self.filenames()))
        settings.setValue('recent_files', value)
    
    def setFilenames( self, filenames ):
        """
        Sets the list of filenames that will be used for this menu to the \
        inputed list.
        
        :param      filenames | [<str>, ..]
        """
        mapped = []
        for filename in filenames:
            filename = nativestring(filename)
            if ( not filename ):
                continue
            
            mapped.append(filename)
            if ( len(mapped) == self.maximumLength() ):
                break
        
        self._filenames = mapped
        self.refresh()
    
    def setMaximumLength( self, length ):
        """
        Sets the maximum number of files to be cached when loading.
        
        :param      length | <int>
        """
        self._maximumLength = length
        self._filenames = self._filenames[:length]
        self.refresh()