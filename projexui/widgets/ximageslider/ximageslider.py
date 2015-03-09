""" [desc] """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

#------------------------------------------------------------------------------

import glob

from projexui.qt.QtCore import Qt
from projexui.qt.QtGui import QGraphicsView,\
                              QPixmap

import projexui
from projexui import resources

from .ximagescene import XImageScene
from .ximageitem  import XImageItem

class XImageSlider(QGraphicsView):
    """ """
    def __init__( self, parent = None ):
        super(XImageSlider, self).__init__( parent )
        
        # define custom properties
        self._spacing = 6
        
        # set default properties
        self.setAlignment(Qt.AlignCenter)
        self.setScene(XImageScene(self))
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(self.FullViewportUpdate)
        
        # create connections
        
        # load default data
        
    def addPixmap(self, pixmap):
        """
        Adds the pixmap to the list for this slider.
        
        :param      pixmap | <QPixmap> || <str>
        """
        scene = self.scene()
        scene.addItem(XImageItem(pixmap))
        self.recalculate()
    
    def calculateSceneWidth(self):
        """
        Returns the total width for all the pixmaps for this widget.
        
        :return     <int>
        """
        widths = []
        
        w = self.width() / 2.0
        h = self.height() / 2.0
        
        for item in self.scene().items():
            pixmap = item.basePixmap()
            thumb = pixmap.scaled(pixmap.width(), h, Qt.KeepAspectRatio)
            widths.append(thumb.width())
            item.setPixmap(thumb)
        
        return sum(widths) + self.spacing() * (self.count() - 1) + w
    
    def clear(self):
        """
        Clears the pixmaps from the scene.
        """
        self.scene().clear()
    
    def count(self):
        """
        Returns the number of pixmaps this widget contains.
        
        :return     <int>
        """
        return len(self.scene().items())
    
    def pixmap(self, index):
        """
        Returns the pixmap at the inputed index from this widget.
        
        :param      index | <int>
        
        :return     <QPixmap> || None
        """
        try:
            return self.items()[index].basePixmap()
        except IndexError:
            return None
    
    def pixmaps(self):
        """
        Returns a list of the pixmaps for this slider.
        
        :return     [<QPixmap>, ..]
        """
        return map(lambda x: x.basePixmap(), self.items())
    
    def recalculate(self):
        """
        Recalcualtes the slider scene for this widget.
        """
        # recalculate the scene geometry
        scene = self.scene()
        w = self.calculateSceneWidth()
        scene.setSceneRect(0, 0, w, self.height())
        
        # recalculate the item layout
        spacing = self.spacing()
        x = self.width() / 4.0
        y = self.height() / 2.0
        for item in self.items():
            pmap = item.pixmap()
            item.setPos(x, y - pmap.height() / 1.5)
            x += pmap.size().width() + spacing
    
    def removePixmap(self, pixmap):
        """
        Removes the pixmap from this widgets list of pixmaps.
        
        :param      pixmap | <QPixmap>
        """
        scene = self.scene()
        for item in self.items():
            if item.basePixmap() == pixmap:
                scene.removeItem(item)
                break
    
    def resizeEvent(self, event):
        """
        Hooks into the resize event for the slider widget to update the scene
        with the latest witdth.
        
        :param      event | <QResizeEvent>
        """
        super(XImageSlider, self).resizeEvent(event)
        
        self.recalculate()
    
    def setPixmaps(self, pixmaps):
        """
        Sets the pixmaps for this widget to the inputed list of images.
        
        :param      pixmaps | [<QPixmap>, ..]
        """
        self.clear()
        scene = self.scene()
        
        for pmap in pixmaps:
            scene.addItem(XImageItem(pmap))
        
        self.recalculate()
    
    def setSpacing(self, spacing):
        """
        Sets the spacing to use between pixmaps in this slider.
        
        :param      spacing | <int>
        """
        self._spacing = spacing
        self.recalculate()
    
    def spacing(self):
        """
        Returns the spacing amount to be used between pixmaps in this slider.
        
        :return     <int>
        """
        return self._spacing
    
__designer_plugins__ = [XImageSlider]