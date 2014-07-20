#!/usr/bin/python

""" Creates reusable resources for the gui systems """

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

# define globals
from projexui import qt
from projexui.xresourcemanager import XResourceManager
from .rc import __plugins__

mgr = XResourceManager('projexui',
                       os.path.dirname(__file__),
                       __plugins__,
                       defaults={'img': 'default'},
                       logger=logging.getLogger(__name__))

mgr.setup(globals())

