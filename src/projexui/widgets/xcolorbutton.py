#!/usr/bin/python

"""
Extends the base QPushButton class to support color selection.
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

from projexui.qt        import Signal, Property
from projexui.qt.QtGui  import QPushButton,\
                               QColor,\
                               QColorDialog

class XColorButton(QPushButton):    """    The XColorButton class is a simple extension to the standard QPushButton    that will control color settings.  When teh user clicks on the button, the    QColorDialog will be displayed, prompting the user to select a new color.    Colors are stored internally can can be accessed by etter and setter     methods, as well as the colorChanged signal.        As the color is modified, either through code or by a user, the background    color for the button will automatically update to match.        == Example ==        |>>> from projexui.widgets.xcolorbutton import XColorButton    |>>> import projexui    |    |>>> # create the widget    |>>> btn = projexui.testWidget(XColorButton)    |    |>>> # click around, change the color    |>>> from projexui.qt.QtGui import QColor    |>>> print btn.color().red(), btn.color().green(), btn.color().blue()    |255 170 0    |>>> btn.setColor(QColor('red'))    |    |>>> # create connections    |>>> def printColor(clr): print clr.red(), clr.green(), clr.blue()    |>>> btn.colorChanged.connect(printColor)    |    |>>> # prompt the user to select a color for that button    |>>> btn.pickColor()    """
    colorChanged = Signal(QColor)
    
    def __init__( self, parent ):
        super(XColorButton, self).__init__(parent)
        
        # initialize the color
        color       = QColor('black')
        self._color = color
        palette     = self.palette()
        palette.setColor(palette.Button, color)
        self.setPalette(palette)
        
        # create connections
        self.clicked.connect(self.pickColor)
    
    def color( self ):
        """
        Returns the color value for this button.
        
        :return     <QColor>
        """
        return self._color
    
    def pickColor( self ):
        """
        Prompts the user to select a color for this button.
        """
        color = QColorDialog.getColor( self.color(), self )
        
        if ( color.isValid() ):
            self.setColor(color)
    
    def setColor( self, color ):
        """
        Sets the color value for this button to the given color.
        
        :param      color | <QColor>
        """
        self._color = color
        palette     = self.palette()
        palette.setColor(palette.Button, color)
        self.setPalette(palette)
        
        if ( not self.signalsBlocked() ):
            self.colorChanged.emit(color)
    
    x_color = Property(QColor, color, setColor)
    
__designer_plugins__ = [XColorButton]