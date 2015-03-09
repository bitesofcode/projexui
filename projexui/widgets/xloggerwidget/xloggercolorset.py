#!/usr/bin/python

""" Creates a widget for monitoring logger information. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

from xqt import QtGui
from projexui.xcolorset import XColorSet

class XLoggerColorSet(XColorSet):
    def __init__( self, *args, **defaults ):
        super(XLoggerColorSet, self).__init__(*args, **defaults)
        
        self.setColorGroups(['Default'])
        
        self.setColor('Standard',     QtGui.QColor('black'))
        self.setColor('Debug',        QtGui.QColor('gray'))
        self.setColor('Info',         QtGui.QColor('blue'))
        self.setColor('Success',      QtGui.QColor('darkGreen'))
        self.setColor('Warning',      QtGui.QColor('orange').darker(150))
        self.setColor('Error',        QtGui.QColor('darkRed'))
        self.setColor('Critical',     QtGui.QColor('darkRed'))
        self.setColor('Background',   QtGui.QColor(250, 250, 250))
        self.setColor('String',       QtGui.QColor('darkRed'))
        self.setColor('Number',       QtGui.QColor('orange').darker(150))
        self.setColor('Comment',      QtGui.QColor('green'))
        self.setColor('Keyword',      QtGui.QColor('blue'))
    
    @staticmethod
    def lightScheme():
        return XLoggerColorSet()
    
    @staticmethod
    def darkScheme():
        out = XLoggerColorSet()
        out.setColor('Standard',    QtGui.QColor('white'))
        out.setColor('Debug',       QtGui.QColor(220, 220, 220))
        out.setColor('Info',        QtGui.QColor('cyan'))
        out.setColor('Success',     QtGui.QColor('green'))
        out.setColor('Warning',     QtGui.QColor('yellow'))
        out.setColor('Error',       QtGui.QColor('red'))
        out.setColor('Critical',    QtGui.QColor('red'))
        out.setColor('Background',  QtGui.QColor(40, 40, 40))
        out.setColor('String',      QtGui.QColor('orange'))
        out.setColor('Number',      QtGui.QColor('red'))
        out.setColor('Comment',     QtGui.QColor(140, 255, 140))
        out.setColor('Keyword',     QtGui.QColor('cyan'))
        
        return out

# needed for save/load using the datatype system
XLoggerColorSet.registerToDataTypes()
