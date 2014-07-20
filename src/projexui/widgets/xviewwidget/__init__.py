#!/usr/bin python

""" Defines an event-driven user customizable GUI widget interfce. """

# define authorship information
__authors__     = ['Eric Hulser']
__author__      = ','.join(__authors__)
__credits__     = []
__copyright__   = 'Copyright (c) 2011, Projex Software'

# maintanence information
__maintainer__  = 'Projex Software'
__email__       = 'team@projexsoftware.com'

from projexui.widgets.xviewwidget.xviewwidget    import XViewWidget
from projexui.widgets.xviewwidget.xviewdialog    import XViewDialog
from projexui.widgets.xviewwidget.xviewprofile   import XViewProfile
from projexui.widgets.xviewwidget.xview          import XView,\
                                                        XViewDispatcher,\
                                                        xviewSlot

from projexui.widgets.xviewwidget.xviewprofiletoolbar \
                                import XViewProfileToolBar

from projexui.widgets.xviewwidget.xviewprofilemanagermenu \
                                import XViewProfileManagerMenu

from projexui.widgets.xviewwidget.xviewprofilemanager \
                                import XViewProfileManager

__designer_plugins__ = [XView,
                        XViewWidget,
                        XViewProfileManager,
                        XViewProfileToolBar]