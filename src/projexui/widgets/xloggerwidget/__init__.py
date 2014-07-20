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

#------------------------------------------------------------------------------

from .xloggerwidget import XLoggerWidget
from .xloggertreewidget import XLoggerTreeWidget
from .xloggercontrols import XLoggerControls
from .xloggerwidgethandler import XLoggerWidgetHandler
from .xloggercolorset import XLoggerColorSet

__designer_plugins__ = [XLoggerWidget, XLoggerTreeWidget]