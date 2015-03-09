#!/usr/bin/python

""" Creates a reusable wizard browsing system for projects. """

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

from projexui.dialogs.xwizardbrowserdialog.xwizardbrowserdialog import \
    XWizardBrowserDialog

from projexui.dialogs.xwizardbrowserdialog.xwizardplugin import \
    XWizardPlugin, XScaffoldWizardPlugin