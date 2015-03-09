""" 
Defines the hotspot class that is used to define connection points on nodes. 
"""

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software, LLC'
__license__         = 'LGPL'

__maintainer__      = 'Projex Software, LLC'
__email__           = 'team@projexsoftware.com'

from projex.text import nativestring

from projexui.qt.QtGui import QColor, QIcon, QToolTip, QCursor

from projex.enum import enum

class XNodeHotspot(object):
    Style = enum('Invisible', 'Square', 'Circle', 'Icon')
    VisibilityPolicy = enum('Always', 'Hover', 'Never', 'NodeHover')
    
    def __init__(self, rect, slot, name='', toolTip=''):
        self._rect        = rect
        self._slot        = slot
        self._name        = name
        self._hovered     = False
        self._enabled     = True
        self._customData  = {}
        self._toolTip     = toolTip
        self._style       = XNodeHotspot.Style.Invisible
        self._icon        = None
        self._hoverIcon   = None
        self._color       = QColor('white')
        self._borderColor = QColor('gray')
        self._visibilityPolicy = XNodeHotspot.VisibilityPolicy.Always
    
    def borderColor( self ):
        """
        Returns the border color for this hotspot.
        
        :return     <QColor>
        """
        return self._borderColor
    
    def color( self ):
        """
        Returns the color for this hotspot.
        
        :return     <QColor>
        """
        return self._color
    
    def customData( self, key, default = None ):
        """
        Returns the custom data linked to this hotspot for the inputed key.
        
        :param      key     | <str>
                    default | <variant>
        
        :return     <variant>
        """
        return self._customData.get(nativestring(key), default)
    
    def hoverEnterEvent(self, event):
        """
        Processes when this hotspot is entered.
        
        :param      event | <QHoverEvent>
        
        :return     <bool> | processed
        """
        self._hovered = True
        if self.toolTip():
            QToolTip.showText(QCursor.pos(), self.toolTip())
            return True
        
        return self.style() == XNodeHotspot.Style.Icon
    
    def hoverIcon(self):
        """
        Returns the hover icon for this instance, if one is set.
        
        :return     <QIcon> || None
        """
        return self._hoverIcon
    
    def hoverLeaveEvent(self, event):
        """
        Processes when this hotspot is entered.
        
        :param      event | <QHoverEvent>
        
        :return     <bool> | processed
        """
        self._hovered = False
        if self.toolTip():
            QToolTip.hideText()
        
        return self.style() == XNodeHotspot.Style.Icon
    
    def icon(self):
        """
        Returns the icon for this instance.
        
        :return     <QIcon> || None
        """
        return self._icon
    
    def isEnabled(self):
        """
        Returns whether or not this hotspot is enabled.
        
        :return     <bool>
        """
        if callable(self._enabled):
            return self._enabled()
        return self._enabled
    
    def name(self):
        """
        Returns the name of this hotspot.
        
        :return     <str>
        """
        return self._name
    
    def rect(self):
        """
        Returns the rectangle for this hotspot.
        
        :return     <QRectF>
        """
        return self._rect
    
    def render(self, painter, node=None):
        """
        Draws this node based on its style information
        
        :param      painter | <QPainter>
        """
        policy = self.visibilityPolicy()
        
        if policy == XNodeHotspot.VisibilityPolicy.Never:
            return
        elif policy == XNodeHotspot.VisibilityPolicy.Hover and \
            not self._hovered:
            return
        elif policy == XNodeHotspot.VisibilityPolicy.NodeHover and \
            not (node and node.isHovered()):
            return
        
        # initialize the look
        painter.setPen(self.borderColor())
        painter.setBrush(self.color())
        
        # draw a circle
        if self.style() == XNodeHotspot.Style.Circle:
            painter.drawEllipse(self.rect())
        
        # draw a square
        elif self.style() == XNodeHotspot.Style.Square:
            painter.drawRect(self.rect())
        
        # draw an icon
        elif self.style() == XNodeHotspot.Style.Icon:
            rect = self.rect()
            x = int(rect.x())
            y = int(rect.y())
            w = int(rect.size().width())
            h = int(rect.size().height())
            
            icon = self.icon()
            hicon = self.hoverIcon()
            
            if not self.isEnabled():
                pixmap = icon.pixmap(w, h, QIcon.Disabled)
            elif not self._hovered:
                pixmap = icon.pixmap(w, h)
            elif hicon:
                pixmap = hicon.pixmap(w, h)
            else:
                pixmap = icon.pixmap(w, h, QIcon.Selected)
            
            painter.drawPixmap(x, y, pixmap)
    
    def setBorderColor(self, color):
        """
        Sets the border color for this hotspot to the inputed color.
        
        :param      color | <QColor>
        """
        self._borderColor = color
    
    def setColor(self, color):
        """
        Sets the background color for this hotspot.
        
        :param      color | <QColor>
        """
        self._color = color
    
    def setCustomData(self, key, value):
        """
        Sets the custom data for this hotspot to the inputed value.
        
        :param      key     | <str>
                    value   | <variant>
        """
        self._customData[nativestring(key)] = value
    
    def setHoverIcon(self, icon):
        """
        Sets the icon that will be used when this hotspot is hovered.
        
        :param      icon | <QIcon> || None
        """
        icon = QIcon(icon)
        if not icon.isNull():
            self._hoverIcon = QIcon(icon)
        else:
            self._hoverIcon = None
    
    def setIcon(self, icon):
        """
        Sets the icon for this hotspot.  If this method is called with a valid
        icon, then the style will automatically switch to Icon, otherwise,
        the style will be set to Invisible.
        
        :param      icon | <QIcon> || <str> || None
        """
        icon = QIcon(icon)
        if icon.isNull():
            self._icon = None
            self._style = XNodeHotspot.Style.Invisible
        else:
            self._icon = icon
            self._style = XNodeHotspot.Style.Icon
    
    def setEnabled(self, state=True):
        """
        Sets whether or not this hotspot is enabled.
        
        :return     state | <bool>
        """
        self._enabled = state
    
    def setName(self, name):
        """
        Sets the name of this hotspot to the given name.
        
        :param      name | <str>
        """
        self._name = name
    
    def setRect( self, rect ):
        """
        Sets the render rectangle for this hotspot to the inputed hotspot.
        
        :param      rect | <QRectF>
        """
        self._rect = rect
    
    def setSlot( self, slot ):
        """
        Sets the callable slot for this hotspot to the inputed slot mehtod.
        
        :param      slot | <method> || <function>
        """
        self._slot = slot
    
    def setStyle( self, style ):
        """
        Sets the style of this hotspot to the inputed style.
        
        :param      style | <XNodeHotspot.Style>
        """
        self._style = style
    
    def setToolTip( self, toolTip ):
        """
        Sets the tooltip for this hotspot to the inputed tip.
        
        :param      toolTip | <str>
        """
        self._toolTip = toolTip
    
    def setVisibilityPolicy(self, policy):
        """
        Sets the visibility policy for this hotspot.
        
        :param      policy | <XNodeHotspot.VisibilityPolicy>
        """
        self._visibilityPolicy = policy
    
    def slot(self):
        """
        Returns the slot method linked with this hotspot.
        
        :return         <method> || <function>
        """
        return self._slot
    
    def style( self ):
        """
        Returns the hotstpot style for this hotspot.
        
        :return         <XNodeHotspot.Style>
        """
        return self._style
    
    def toolTip( self ):
        """
        Returns the tooltip for this hotspot.
        
        :return         <str>
        """
        return self._toolTip
    
    def visibilityPolicy(self):
        """
        Returns the visibility policy for this hotspot.
        
        :return     <XNodeHotspot.VisibilityPolicy>
        """
        return self._visibilityPolicy


