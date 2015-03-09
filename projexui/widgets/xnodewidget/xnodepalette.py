#!/usr/bin/python

""" Defines the root QGraphicsScene class for the node system. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

from xqt import QtGui
from projexui.xpalette import XPalette

class XNodePalette(XPalette):
    __custom_roles__ = [
        'GridBackground',
        'GridForeground',
        'GridAlternateForeground',
        'GridCenterline',
        
        'NodeBackground',
        'NodeAlternateBackground',
        'NodeForeground',
        'NodeBorder',
        'NodeHighlight',
        'NodeHotspot',
        
        'Connection',
        'ConnectionHighlight'
    ]
    
    def __init__(self, *args):
        super(XNodePalette, self).__init__(*args)
        
        try:
            other = args[0] if isinstance(args[0], XNodePalette) else None
        except IndexError:
            other = None
        
        if other:
            grid_bg     = other.color(other.GridBackground)
            grid_fg     = other.color(other.GridForeground)
            grid_fg_alt = other.color(other.GridAlternateForeground)
            grid_ctr    = other.color(other.GridCenterline)
            
            node_bg     = other.color(other.NodeBackground)
            node_alt    = other.color(other.NodeAlternateBackground)
            node_fg     = other.color(other.NodeForeground)
            node_bg_d   = other.color(other.Disabled, other.NodeBackground)
            node_alt_d  = other.color(other.Disabled, other.NodeAlternateBackground)
            node_fg_d   = other.color(other.Disabled, other.NodeForeground)
            node_bdr    = other.color(other.NodeBorder)
            node_bdr_d  = other.color(other.Disabled, other.NodeBorder)
            node_hspt   = other.color(other.NodeHotspot)
            node_hlt    = other.color(other.NodeHighlight)
            
            con         = other.color(other.Connection)
            con_d       = other.color(other.Disabled, other.Connection)
            con_hlt     = other.color(other.ConnectionHighlight)
        else:
            grid_bg     = QtGui.QColor(200, 200, 200)
            grid_fg     = QtGui.QColor(180, 180, 180)
            grid_fg_alt = QtGui.QColor(190, 190, 190)
            grid_ctr    = QtGui.QColor(160, 160, 160)
            
            node_bg     = QtGui.QColor(255, 255, 255)
            node_alt    = QtGui.QColor(245, 245, 245)
            node_fg     = QtGui.QColor(90, 90, 90)
            node_bg_d   = QtGui.QColor(220, 220, 220)
            node_alt_d  = QtGui.QColor(210, 210, 210)
            node_fg_d   = QtGui.QColor(160, 160, 160)
            node_bdr    = QtGui.QColor(90, 90, 90)
            node_bdr_d  = QtGui.QColor(160, 160, 160)
            node_hspt   = QtGui.QColor(255, 255, 255)
            node_hlt    = QtGui.QColor(90, 90, 200)
            
            con         = QtGui.QColor(90, 90, 90)
            con_d       = QtGui.QColor(180, 180, 180)
            con_hlt     = QtGui.QColor(90, 90, 200)
        
        # setup grid coloring
        self.setColor(self.GridBackground, grid_bg)
        self.setColor(self.GridForeground, grid_fg)
        self.setColor(self.GridAlternateForeground, grid_fg_alt)
        self.setColor(self.GridCenterline, grid_ctr)
        
        # setup node coloring
        self.setColor(self.NodeBackground, node_bg)
        self.setColor(self.NodeAlternateBackground, node_alt)
        self.setColor(self.NodeForeground, node_fg)
        self.setColor(self.NodeBorder, node_bdr)
        self.setColor(self.NodeHighlight, node_hlt)
        self.setColor(self.NodeHotspot, node_hspt)
        
        self.setColor(self.Disabled, self.NodeBackground, node_bg_d)
        self.setColor(self.Disabled, self.NodeAlternateBackground, node_alt_d)
        self.setColor(self.Disabled, self.NodeForeground, node_fg_d)
        self.setColor(self.Disabled, self.NodeBorder, node_bdr_d)
        
        self.setColor(self.Connection, con)
        self.setColor(self.Disabled, self.Connection, con_d)
        self.setColor(self.ConnectionHighlight, con_hlt)

    

