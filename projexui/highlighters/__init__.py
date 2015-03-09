""" Defines the hook required for the PyInstaller to use projexui with it. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

import projex
from . import __plugins__
projex.importmodules(__plugins__)