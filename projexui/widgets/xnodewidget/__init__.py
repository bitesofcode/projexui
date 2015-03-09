#!/usr/bin/python

""" 
Defines a node widget class that can be reused for generating 
various node systems. 
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

from projexui.widgets.xnodewidget.xnodepalette    import XNodePalette
from projexui.widgets.xnodewidget.xnodehotspot    import XNodeHotspot
from projexui.widgets.xnodewidget.xnodewidget     import XNodeWidget
from projexui.widgets.xnodewidget.xnodescene      import XNodeScene
from projexui.widgets.xnodewidget.xnodelayout     import XNodeLayout
from projexui.widgets.xnodewidget.xnode           import XNode, \
                                                         XNodeDispatcher,\
                                                         XNodeAnimation
                                                            
from projexui.widgets.xnodewidget.xnodeconnection import XNodeConnection, \
                                                         XConnectionLocation, \
                                                         XConnectionStyle

__designer_plugins__ = [XNodeWidget]