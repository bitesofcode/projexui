""" Defines a button that can be used to toggle on/off based on a switch. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

import os
from projexui import resources
from projexui.xpainter import XPainter
from xqt import QtCore, QtGui

class XSwitchButton(QtGui.QAbstractButton):
    __designer_group__ = 'ProjexUI'
    __designer_icon__ = resources.find('img/ui/switch_on.png')
    
    def __init__(self, *args):
        super(XSwitchButton, self).__init__(*args)
        
        # create the pixmaps
        self._onPixmap = QtGui.QPixmap(resources.find('img/switch/switch_on.png'))
        self._offPixmap = QtGui.QPixmap(resources.find('img/switch/switch_off.png'))
        
        # set the check state for this button
        self.setCheckable(True)
        self.setChecked(True)
        self.resize(self.sizeHint())
    
    def currentPixmap(self):
        """
        Returns the current pixmap for this switch button.  When the button
        is checked, the ON pixmap is returned, and when the button is
        unchecked the OFF pixmap is returned.
        
        :return     <QtGui.QPixmap>
        """
        if self.isChecked():
            return self.onPixmap()
        return self.offPixmap()
    
    def currentPixmapRect(self):
        """
        Returns the rect that defines the boundary for the current pixmap
        based on the size of the button and the size of the pixmap.
        
        :return     <QtCore.QRect>
        """
        pixmap = self.currentPixmap()
        rect   = self.rect()
        size   = pixmap.size()
        
        x = rect.center().x() - (size.width() / 2.0)
        y = rect.center().y() - (size.height() / 2.0)
        
        return QtCore.QRect(x, y, size.width(), size.height())
    
    def hitButton(self, pos):
        """
        Returns whether or not the position is within the clickable area
        for this button.
        
        :param      pos | <QPoint>
        """
        return self.currentPixmapRect().contains(pos)
    
    def offPixmap(self):
        """
        Returns the OFF pixmap.
        
        :return     <QtGui.QPixmap>
        """
        return self._offPixmap
        
    def onPixmap(self):
        """
        Returns the ON pixmap.
        
        :return     <QtGui.QPixmap>
        """
        return self._onPixmap
    
    def paintEvent(self, event):
        """
        Draws the pixmap for this widget.
        
        :param      event | <QPaintEvent>
        """
        pixmap = self.currentPixmap()
        rect   = self.currentPixmapRect()
        
        with XPainter(self) as painter:
            painter.drawPixmap(rect.x(), rect.y(), pixmap)
    
    def setOffPixmap(self, pixmap):
        """
        Sets the off pixmap that will be used for this button to the
        given pixmap.  This can be a QPixmap instance, or a string for where
        to load the pixmap from.
        
        :param      pixmap | <QtGui.QPixmap> || <str>
        """
        pmap = QtGui.QPixmap(pixmap)
        self._offPixmap = pmap.scaled(self.width(), self.height(),
                                      QtCore.Qt.KeepAspectRatio,
                                      QtCore.Qt.SmoothTransformation)
    
    def setOnPixmap(self, pixmap):
        """
        Sets the on pixmap that will be used for this button to the given
        pixmap.  THis can be a QPixmap instance, or a string for where to load
        the pixmap from.
        
        :param      pixmap | <QtGui.QPixmap> || <str>
        """
        pmap = QtGui.QPixmap(pixmap)
        self._onPixmap = pmap.scaled(self.width(), self.height(),
                                     QtCore.Qt.KeepAspectRatio,
                                     QtCore.Qt.SmoothTransformation)
    
    def sizeHint(self):
        """
        Returns the size hint for this button based on the pixmap that
        is being used.
        
        :return     <QSize>
        """
        return self.onPixmap().size()
    
    x_onPixmap = QtCore.Property('QPixmap', onPixmap, setOnPixmap)
    x_offPixmap = QtCore.Property('QPixmap', offPixmap, setOffPixmap)

__designer_plugins__ = [XSwitchButton]