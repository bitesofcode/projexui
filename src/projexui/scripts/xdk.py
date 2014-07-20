#!/usr/bin/python

""" Launches the XDK window """

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

# define version information (major,minor,maintanence)
__depends__        = ['projex']
__version_info__   = (0, 0, 0)
__version__        = '%i.%i.%i' % __version_info__

#------------------------------------------------------------------------------

import glob
import os.path
import sys

import projex
projex.requires('projexui')

from projexui.qt.QtGui import QApplication
from projexui.windows.xdkwindow import XdkWindow

app = None

if ( __name__ == '__main__' ):
    app = QApplication.instance()
    if ( not app ):
        app = QApplication([])
        app.setStyle('plastique')
    
    window = XdkWindow()
    window.show()
    if ( len(sys.argv) > 1 ):
        filenames = sys.argv[1].split(os.path.pathsep)
        
        for filename in filenames:
            if ( '*' in filename ):
                searched = glob.glob(os.path.expanduser(filename))
            else:
                searched = [os.path.expanduser(filename)]
                
            for searched_file in searched:
                window.loadFilename(searched_file)
    
    if ( app ):
        app.exec_()