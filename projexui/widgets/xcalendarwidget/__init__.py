#!/usr/bin/python

""" 
Defines a calendar widget similar to the ones found in outlook or ical.
"""

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

from projexui.widgets.xcalendarwidget.xcalendarwidget import XCalendarWidget
from projexui.widgets.xcalendarwidget.xcalendarscene  import XCalendarScene
from projexui.widgets.xcalendarwidget.xcalendaritem   import XCalendarItem

__designer_plugins__ = [XCalendarWidget]