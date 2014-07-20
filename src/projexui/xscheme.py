#!/usr/bin/python

""" Defines the scheme class type for interfaces. """

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

import logging

from projexui.qt import unwrapVariant
from projexui.qt.QtGui  import QApplication,\
                               QMdiArea

from projex.dataset     import DataSet
from projexui.xcolorset import XPaletteColorSet

logger = logging.getLogger(__name__)

class XScheme(DataSet):
    """ Defines a schema set of information. """
    def __init__( self, *args, **defaults ):
        defaults.setdefault('colorSet',  XPaletteColorSet())
        defaults.setdefault('font',      QApplication.font())
        defaults.setdefault('fontSize',  QApplication.font().pointSize())
        
        super(XScheme, self).__init__( *args, **defaults )
    
    def apply( self ):
        """
        Applies the scheme to the current application.
        """
        font = self.value('font')
        
        try:
            font.setPointSize(self.value('fontSize'))
        
        # errors in linux for some reason
        except TypeError:
            pass
        
        palette = self.value('colorSet').palette()
        
        if ( unwrapVariant(QApplication.instance().property('useScheme')) ):
            QApplication.instance().setFont(font)
            QApplication.instance().setPalette(palette)
            
            # hack to support MDI Areas
            for widget in QApplication.topLevelWidgets():
                for area in widget.findChildren(QMdiArea):
                    area.setPalette(palette)
        else:
            logger.debug('The application doesnt have the useScheme property.')
    
    def reset( self ):
        """
        Resets the values to the current application information.
        """
        self.setValue('colorSet', XPaletteColorSet())
        self.setValue('font',     QApplication.font())
        self.setValue('fontSize', QApplication.font().pointSize())