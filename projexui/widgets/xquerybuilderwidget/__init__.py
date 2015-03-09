#!/usr/bin/python

""" Defines an interface to allow users to build their queries on the fly. """

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

from projexui.widgets.xquerybuilderwidget.xqueryrule \
                                        import XQueryRule

from projexui.widgets.xquerybuilderwidget.xquerylinewidget \
                                        import XQueryLineWidget

from projexui.widgets.xquerybuilderwidget.xquerybuilderwidget \
                                       import XQueryBuilderWidget

__designer_plugins__ = [XQueryBuilderWidget]