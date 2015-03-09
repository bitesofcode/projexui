#!/usr/bin/python

""" Defines some additions the Qt Animation framework. """

from projex.enum import enum
from projexui.qt.QtCore import QSize
from projexui.qt.QtGui import QIcon, QColor, QPixmap

class XColorIcon(QIcon):
    Style = enum('Plain')
    
    def __init__(self, icon, style=Style.Plain):
        if type(icon) in (str, unicode):
            icon = QColor(icon)
        
        if isinstance(icon, QColor):
            icon = self.generatePixmap(icon, style)
            
        super(XColorIcon, self).__init__(icon)
    
    @staticmethod
    def generatePixmap(color, style=Style.Plain, size=None):
        """
        Generates a new pixmap for the inputed color and style.  If no
        size is provided, then the default 32x32 will be used.
        
        :return     <QPixmap>
        """
        if size is None:
            size = QSize(32, 32)
        
        pixmap = QPixmap(size)
        
        # create a plain pixmap
        if style == XColorIcon.Style.Plain:
            pixmap.fill(color)
        
        return pixmap