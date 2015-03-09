#!/usr/bin python

""" Defines a more feature rich toolbar. """

# define authorship information
__authors__     = ['Eric Hulser']
__author__      = ','.join(__authors__)
__credits__     = []
__copyright__   = 'Copyright (c) 2011, Projex Software'

# maintanence information
__maintainer__  = 'Projex Software'
__email__       = 'team@projexsoftware.com'

from projex.lazymodule import LazyModule
from projexui.qt import Signal, Slot, QtCore, QtGui, Property

xtoolbar = LazyModule('projexui.widgets.xtoolbar')

CLICKABLE_SHEET = """\
QToolButton,
QToolButton:hover,
QToolButton:checked {
    border: none;
    background: transparent;
    padding: 2px;
}
QToolButton:pressed {
    border: none;
    background: transparent;
    margin-top: 2px;
    margin-left: 2px;
    padding: 3px;
}
"""

UNCLICKABLE_SHEET = """\
QToolButton,
QToolButton:hover,
QToolButton:pressed,
QToolButton:checked {
    border: none;
    background: transparent;
    padding: 2px;
}"""

class XToolButton(QtGui.QToolButton):
    def __init__(self, *args):
        super(XToolButton, self).__init__(*args)
        
        # define custom properties
        self._colored           = False
        self._shadowed          = False
        self._shadowRadius      = 20
        self._clickable         = True
        self._angle             = 0
        self._flipVertical      = False
        self._flipHorizontal    = False
        self._movie             = None
        self._blinking          = False
        self._blinkInterval     = 500 # msecs
        self._hoverable         = False
        self._hoverIcon         = None
        
        # assign this toolbutton on a XToolBar class
        if len(args) > 0:
            parent = args[0]
            if isinstance(parent, xtoolbar.XToolBar):
                palette = self.parent().palette()
                self.setPalette(palette)
                
                self.setToolButtonStyle(parent.toolButtonStyle())
                self.triggered.connect(parent.actionTriggered)
                self.setShadowed(parent.isShadowed())
                self.setColored(parent.isColored())
        
        # update the ui when it is toggled
        self.toggled.connect(self.updateUi)

    def _updateFrame(self):
        """
        Sets the icon for this button to the frame at the given number.
        """
        self.setIcon(QtGui.QIcon(self._movie.currentPixmap()))

    def angle(self):
        """
        Returns the angle that this button should be rotated.
        
        :return     <int>
        """
        return self._angle
    
    def blink(self, state=True):
        """
        Starts or stops the blinking state for this button.  This only
        works for when the toolbutton is in Shadowed or Colored mode.
        
        :param      state | <bool>
        
        :return     <bool> | success
        """
        if self._blinking == state:
            return True
        elif not self.graphicsEffect():
            return False
        else:
            self._blinking = state
            if state:
                self.startTimer(self.blinkInterval())
    
    def blinkInterval(self):
        """
        Returns the number of milliseconds that this button will blink for
        when it is in the blinking state.
        
        :return     <int>
        """
        return self._blinkInterval
    
    def cleanup(self):
        """
        Cleanup references to the movie when this button is destroyed.
        """
        if self._movie is not None:
            self._movie.frameChanged.disconnect(self._updateFrame)
            self._movie = None
    
    def enterEvent(self, event):
        if self.isHoverable():
            super(XToolButton, self).setIcon(self._hoverIcon)

        if self.isShadowed():
            if self.isClickable() and self.isEnabled():
                effect = self.graphicsEffect()
                palette = self.palette()
                clr = palette.color(palette.Shadow)
                effect.setColor(clr)
        
        elif self.isColored():
            if self.isClickable() and self.isEnabled():
                effect = self.graphicsEffect()
                effect.setStrength(1)
            
        else:
            super(XToolButton, self).enterEvent(event)

    def flipHorizontal(self):
        """
        Returns whether or not the button should be flipped horizontally.
        
        :return     <bool>
        """
        return self._flipHorizontal
    
    def flipVertical(self):
        """
        Returns whether or not the button should be flipped horizontally.
        
        :return     <bool>
        """
        return self._flipVertical
    
    def movie(self):
        """
        Returns the movie instance associated with this button.
        
        :return     <QtGui.QMovie> || None
        """
        return self._movie
    
    def isBlinking(self):
        """
        Returns whether or not this button is currently blinking.
        
        :return     <bool>
        """
        return self._blinking
    
    def isClickable(self):
        return self._clickable

    def isColored(self):
        return self._colored

    def isHoverable(self):
        """
        Returns whether or not this button should hide its icon when not hovered.

        :return     <bool>
        """
        return self._hoverable

    def isShadowed(self):
        return self._shadowed

    def leaveEvent(self, event):
        if self.isHoverable():
            super(XToolButton, self).setIcon(QtGui.QIcon())

        if self.isShadowed() or self.isColored():
            self.updateUi()
        else:
            super(XToolButton, self).leaveEvent(event)

    def paintEvent(self, event):
        """
        Overloads the paint even to render this button.
        """
        if self.isHoverable() and self.icon().isNull():
            return

        # initialize the painter
        painter = QtGui.QStylePainter()
        painter.begin(self)
        try:
            option = QtGui.QStyleOptionToolButton()
            self.initStyleOption(option)

            # generate the scaling and rotating factors
            x_scale = 1
            y_scale = 1

            if self.flipHorizontal():
                x_scale = -1
            if self.flipVertical():
                y_scale = -1

            center = self.rect().center()
            painter.translate(center.x(), center.y())
            painter.rotate(self.angle())
            painter.scale(x_scale, y_scale)
            painter.translate(-center.x(), -center.y())

            painter.drawComplexControl(QtGui.QStyle.CC_ToolButton, option)
        finally:
            painter.end()
        
    def setAngle(self, angle):
        """
        Sets the angle that this button should be rotated.
        
        :param      angle | <int>
        """
        self._angle = angle
    
    def setBlinkInterval(self, msecs):
        """
        Sets the number of milliseconds that this button will blink for
        when it is in the blinking state.
        
        :param      msecs | <int>
        """
        self._blinkInterval = msecs
    
    def setClickable(self, state):
        self._clickable = state
        
        if not state:
            self.setStyleSheet(UNCLICKABLE_SHEET)
        elif self.isShadowed() or self.isColored():
            self.setStyleSheet(CLICKABLE_SHEET)
        else:
            self.setStyleSheet('')

    def setColored(self, state):
        self._colored = state
        if state:
            self._shadowed = False
            palette = self.palette()
            
            effect = QtGui.QGraphicsColorizeEffect(self)
            effect.setStrength(0)
            effect.setColor(palette.color(palette.Highlight))
            
            self.setGraphicsEffect(effect)
            if self.isClickable():
                self.setStyleSheet(CLICKABLE_SHEET)
            else:
                self.setStyleSheet(UNCLICKABLE_SHEET)
            self.updateUi()
        else:
            self.setStyleSheet('')
            self.setGraphicsEffect(None)
            self.blink(False)

    def setHoverable(self, state):
        """
        Sets whether or not this is a hoverable button.  When in a hoverable state, the icon will only
        be visible when the button is hovered on.

        :param      state | <bool>
        """
        self._hoverable = state
        self._hoverIcon = self.icon()

    def setIcon(self, icon):
        super(XToolButton, self).setIcon(icon)

        if self.isHoverable():
            self._hoverIcon = icon

    def setEnabled(self, state):
        """
        Updates the drop shadow effect for this widget on enable/disable
        state change.
        
        :param      state | <bool>
        """
        super(XToolButton, self).setEnabled(state)
        
        self.updateUi()
    
    def setFlipHorizontal(self, state):
        """
        Sets whether or not the button should be flipped horizontally.
        
        :param      state | <bool>
        """
        self._flipHorizontal = state
    
    def setFlipVertical(self, state):
        """
        Sets whether or not the button should be flipped vertically.
        
        :param      state | <bool>
        """
        self._flipVertical = state
    
    def setMovie(self, movie):
        """
        Sets the movie instance for this button.
        
        :param      movie | <QtGui.QMovie>
        """
        if self._movie is not None:
            self._movie.frameChanged.disconnect(self._updateFrame)
        
        self._movie = movie
        
        if movie is not None:
            self._updateFrame()
            self._movie.frameChanged.connect(self._updateFrame)
            self.destroyed.connect(self.cleanup)
    
    def setPalette(self, palette):
        """
        Sets the palette for this button to the inputed palette.  This will
        update the drop shadow to the palette's Shadow color property if
        the shadowed mode is on.
        
        :param      palette | <QtGui.QPalette>
        """
        super(XToolButton, self).setPalette(palette)
        self.updateUi()
    
    def setShadowRadius(self, radius):
        self._shadowRadius = radius

    def setShadowed(self, state):
        self._shadowed = state
        if state:
            self._colored = False
            
            effect = QtGui.QGraphicsDropShadowEffect(self)
            effect.setColor(QtGui.QColor(0, 0, 0, 0))
            effect.setOffset(0, 0)
            effect.setBlurRadius(self.shadowRadius())
            
            self.setGraphicsEffect(effect)
            if self.isClickable():
                self.setStyleSheet(CLICKABLE_SHEET)
            else:
                self.setStyleSheet(UNCLICKABLE_SHEET)
            self.updateUi()
        else:
            self.setStyleSheet('')
            self.setGraphicsEffect(None)
            self.blink(False)
    
    def shadowRadius(self):
        return self._shadowRadius

    def showEvent(self, event):
        super(XToolButton, self).showEvent(event)

        if self.isHoverable():
            super(XToolButton, self).setIcon(QtGui.QIcon())

    def timerEvent(self, event):
        effect = self.graphicsEffect()
        if not (effect and self.isBlinking()):
            self.killTimer(event.timerId())
        
        elif isinstance(effect, QtGui.QGraphicsDropShadowEffect):
            palette = self.palette()
            transparent = QtGui.QColor(0, 0, 0, 0)
            clr = palette.color(palette.Shadow)
            if effect.color() == transparent:
                effect.setColor(clr)
            else:
                effect.setColor(transparent)
        
        elif isinstance(effect, QtGui.QGraphicsColorizeEffect):
            effect.setStrength(int(not effect.strength()))

    def updateUi(self):
        if not self.isClickable():
            return
        
        effect = self.graphicsEffect()
        
        if isinstance(effect, QtGui.QGraphicsDropShadowEffect):
            palette = self.palette()
            transparent = QtGui.QColor(0, 0, 0, 0)
            clr = palette.color(palette.Shadow)
            show = self.isChecked() and self.isEnabled()
            effect.setColor(transparent if not show else clr)
        
        elif isinstance(effect, QtGui.QGraphicsColorizeEffect):
            effect.setStrength(1 if self.isChecked() else 0)
    
    # define properties
    x_angle          = Property(int, angle, setAngle)
    x_clickable = Property(bool, isClickable, setClickable)
    x_colored = Property(bool, isColored, setColored)
    x_flipHorizontal = Property(bool, flipHorizontal, setFlipHorizontal)
    x_flipVertical   = Property(bool, flipVertical, setFlipVertical)
    x_shadowRadius = Property(int, shadowRadius, setShadowRadius)
    x_shadowed = Property(bool, isShadowed, setShadowed)
    

__designer_plugins__ = [XToolButton]