#!/usr/bin/python

""" Generates UI components for projexui (compiles qrc and ui files down). """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

import os

if __name__ == '__main__':
    import projexui
    import projexui.resources
    
    # generate the resource files
    rscpath = os.path.dirname(projexui.resources.__file__)
    projexui.generateResourceFile(os.path.join(rscpath, 'default'))
    
    # generate the ui files
    projexui.generateUiClasses(os.path.dirname(projexui.__file__))