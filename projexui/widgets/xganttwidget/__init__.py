#!/usr/bin/python

""" Defines a gantt chart widget for use in scheduling applications. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2012, Projex Software'
__license__         = 'LGPL'

# maintenance information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'


#------------------------------------------------------------------------------

from projexui.widgets.xganttwidget.xganttwidget     import XGanttWidget
from projexui.widgets.xganttwidget.xganttviewitem   import XGanttViewItem
from projexui.widgets.xganttwidget.xganttwidgetitem import XGanttWidgetItem

__designer_plugins__ = [XGanttWidget]