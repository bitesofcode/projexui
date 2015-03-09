#!/usr/bin/python

""" Defines an helper class for animating icons. """

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

from projexui.qt import Signal
from projexui.qt.QtCore import Qt,\
                               QObject

from projexui.qt.QtGui  import QIcon

class XAnimatedIconHelper(QObject):
    iconChanged = Signal(QIcon)
    
    def __init__( self, parent = None, movie = None ):
        super(XAnimatedIconHelper, self).__init__(parent)
        
        self._movie = movie
    
    def movie( self ):
        """
        Returns the movie linked with this icon.
        
        :return     <QMovie>
        """
        return self._movie
    
    def isNull( self ):
        """
        Returns whether or not this icon is a null icon.
        
        :return     <bool>
        """
        if ( self._movie ):
            return False
        return True
    
    def setMovie( self, movie ):
        """
        Sets the movie for this icon.
        
        :param      movie | <QMovie> || None
        """
        if ( self._movie ):
            self._movie.frameChanged.disconnect(self.updateIcon)
            
        self._movie = movie
        
        if ( self._movie ):
            self._movie.frameChanged.connect(self.updateIcon)
    
    def updateIcon( self ):
        if ( self._movie ):
            icon = QIcon(self._movie.currentPixmap())
            self.iconChanged.emit(icon)