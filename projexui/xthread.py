#!/usr/bin/python

""" 
[DEPRECATED]
Subclasses the QThread to control global enable/disable switches.
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

#------------------------------------------------------------------------------

import os
import logging

from projexui.qt.QtCore import QThread

log = logging.getLogger(__name__)

class XThread(QThread):
    _globalThreadingEnabled = os.environ.get('XTHREADING_DISABLED') != '1'
    
    def __init__( self, *args ):
        super(XThread, self).__init__(*args)
        
        self._localThreadingEnabled = True
        log.error('XThread is a deprecated class!')
    
    def localThreadingEnabled( self ):
        """
        Returns whether or not the local threading for this particular instance
        is enabled.  For a thread to be executed outside the main loop, both
        the local and global threading need to be enabled.
        
        :return     <bool>
        """
        return self._localThreadingEnabled
    
    def setLocalThreadingEnabled( self, state ):
        """
        Sets whether or not the local threading for this particular instance
        is enabled.  For a thread to be executed outside the main loop, both the
        local and global threading need to be enabled.
        
        :param     state | <bool>
        """
        self._localThreadingEnabled = state
    
    def start( self ):
        """
        Starts the thread in its own event loop if the local and global thread
        options are true, otherwise runs the thread logic in the main event
        loop.
        """
        if ( self.localThreadingEnabled() and self.globalThreadingEnabled() ):
            super(XThread, self).start()
        else:
            self.run()
            self.finished.emit()
    
    @staticmethod
    def globalThreadingEnabled():
        """
        Returns whether or not global threading is enabled.
        
        :return     <bool>
        """
        return XThread._globalThreadingEnabled
    
    @staticmethod
    def setGlobalThreadingEnabled(state):
        """
        Sets whether or not global threading is enabled.
        
        :param      state | <bool>
        """
        XThread._globalThreadingEnabled = state

