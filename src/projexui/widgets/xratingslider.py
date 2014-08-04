""" Defines a subclass of a slider for manipulating ratings. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, '
__license__         = 'LGPL'

__maintainer__      = 'Projex Software, LLC'
__email__           = 'team@projexsoftware.com'


#------------------------------------------------------------------------------

from projexui.qt.QtCore import Qt,\
                               QSize

from projexui.qt.QtGui import QSlider,\
                              QPixmap

from projexui.xpainter import XPainter
from projexui import resources

class XRatingSlider(QSlider):
    """ """
    def __init__( self, parent = None ):
        super(XRatingSlider, self).__init__( parent )
        
        # define custom properties
        self._emptyPixmap = QPixmap(resources.find('img/star_gray.png'))
        self._fullPixmap  = QPixmap(resources.find('img/star.png'))
        self._alignment   = Qt.AlignCenter
        self._pixmapSize  = QSize(16, 16)
        
        # set default properties
        self.setOrientation(Qt.Horizontal)
        self.setMinimum(0)
        self.setMaximum(10)
        self.setPixmapSize(QSize(16, 16))
        
        # create connections
    
    def adjustMinimumWidth( self ):
        """
        Modifies the minimum width to factor in the size of the pixmaps and the
        number for the maximum.
        """
        pw = self.pixmapSize().width()
        
        # allow 1 pixel space between the icons
        self.setMinimumWidth(pw * self.maximum() + 3 * self.maximum())
    
    def alignment( self ):
        """
        Returns the alignment for this widget.
        
        :return     <Qt.Alignment>
        """
        return self._alignment
    
    def emptyPixmap( self ):
        """
        Returns the empty pixmap for this slider.
        
        :return     <QPixmap>
        """
        return self._emptyPixmap
    
    def fullPixmap( self ):
        """
        Returns the full pixmap for this slider.
        
        :return     <QPixmap>
        """
        return self._fullPixmap
    
    def mousePressEvent( self, event ):
        """
        Sets the value for the slider at the event position.
        
        :param      event | <QMouseEvent>
        """
        self.setValue(self.valueAt(event.pos().x()))
    
    def mouseMoveEvent( self, event ):
        """
        Sets the value for the slider at the event position.
        
        :param      event | <QMouseEvent>
        """
        self.setValue(self.valueAt(event.pos().x()))
    
    def paintEvent(self, event):
        """
        Paints the widget based on its values
        
        :param      event | <QPaintEvent>
        """
        with XPainter(self) as painter:
            count   = self.maximum() - self.minimum()
            value   = self.value()
            
            w       = self.pixmapSize().width()
            h       = self.pixmapSize().height()
            x       = 2
            y       = (self.height() - h) / 2
            delta_x = (self.width() - 4 - (w * count - 1)) / (count - 1)
            
            full_pixmap  = self.fullPixmap().scaled(w, h)
            empty_pixmap = self.emptyPixmap().scaled(w, h)
            
            for i in range(count):
                if ( i < value ):
                    painter.drawPixmap(x, y, full_pixmap)
                else:
                    painter.drawPixmap(x, y, empty_pixmap)
                
                x += w + delta_x
    
    def pixmapSize( self ):
        """
        Returns the pixmap size for this slider.
        
        :return     <QSize>
        """
        return self._pixmapSize
    
    def setMaximum( self, value ):
        """
        Sets the maximum value for this slider - this will also adjust the
        minimum size value to match the width of the icons by the number for
        the maximu.
        
        :param      value | <int>
        """
        super(XRatingSlider, self).setMaximum(value)
        
        self.adjustMinimumWidth()
    
    def setPixmapSize( self, size ):
        """
        Sets the pixmap size to the inputed value.
        
        :param      size | <QSize>
        """
        self._pixmapSize = size
        self.setMinimumHeight(size.height())
        self.adjustMinimumWidth()
    
    def valueAt( self, pos ):
        """
        Returns the value for the slider at the inputed position.
        
        :param      pos | <int>
        
        :return     <int>
        """
        if ( self.orientation() == Qt.Horizontal ):
            perc = (self.width() - 4 - pos) / float(self.width())
        else:
            perc = (self.height() - 4 - pos) / float(self.height())
        
        start = self.minimum()
        end   = self.maximum()
        
        return round((end - start) * (1 - perc))
    
__designer_plugins__ = [XRatingSlider]