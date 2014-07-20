#!/usr/bin/python

""" Creates a reusable configuration system for projects. """

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

from projexui.dialogs.xconfigdialog.xconfigdialog   import XConfigDialog
from projexui.dialogs.xconfigdialog.xconfigwidget   import XConfigWidget
from projexui.dialogs.xconfigdialog.xconfigplugin   import XConfigPlugin