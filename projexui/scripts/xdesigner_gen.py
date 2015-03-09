#!/usr/bin/python

""" Generates designer plugins for a given path. """

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

import logging
import projexui.designer
import sys

if __name__ == '__main__':
    widgetPath, buildPath = (None, None)
    if len(sys.argv) > 1:
        widgetPath = sys.argv[1]
    if len(sys.argv) > 2:
        buildPath = sys.argv[2]
    
    logging.basicConfig()
    projexui.designer.generatePlugins(widgetPath, buildPath)