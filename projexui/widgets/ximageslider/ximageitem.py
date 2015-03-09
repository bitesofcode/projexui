""" [desc] """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

from projexui.qt.QtCore import Qt
from projexui.qt.QtGui import QGraphicsPixmapItem,\
                              QColor,\
                              QLinearGradient,\
                              QPixmap,\
                              QImage,\
                              QBitmap,\
                              QApplication,\
                              QGraphicsDropShadowEffect

#----------------------------------------------------------------------

class XGraphicsDropShadowEffect(QGraphicsDropShadowEffect):
    def boundingRectFor(self, rect):
        return rect.adjusted(0, 0, 0, rect.height())

class XImageItem(QGraphicsPixmapItem):
    def __init__(self, pixmap):
        super(XImageItem, self).__init__()
        
        # define the mirror instance
        self._basePixmap = pixmap
        
        # set the pixmap
        palette = QApplication.palette()
        color = palette.color(palette.Highlight)
        effect = XGraphicsDropShadowEffect()
        effect.setOffset(0)
        effect.setBlurRadius(6)
        effect.setColor(color)
        
        self.setGraphicsEffect(effect)
        self.graphicsEffect().setEnabled(False)
        self.setFlags(self.ItemIsSelectable)
    
    def angle(self):
        return self.scene().angle(self)
    
    def basePixmap(self):
        """
        Returns the base pixmap for this image item.  This will represent the
        image for this item before any transformations for the slider takes
        place.
        
        :return     <QPixmap>
        """
        return self._basePixmap
    
    def boundingRectFor(self, rect):
        return rect.adjusted(0, 0, 0, rect.height())
    
    def paint(self, painter, option, widget):
        widget = self.scene()._slider
        pixmap = self.pixmap()
        
        palette = widget.palette()
        base = palette.color(palette.Base)
        
        # draw the reflection
        painter.save()
        painter.setPen(Qt.NoPen)
        
        transform = painter.transform()
        transform.translate(pixmap.width() / 2.0, 0)
        transform.rotate(self.angle(), Qt.YAxis)
        transform.translate(-pixmap.width() / 2.0, 0)
        painter.setTransform(transform)
        
        self.graphicsEffect().setEnabled(self.isSelected())
        
        painter.drawPixmap(0, 0, pixmap)
        
        painter.setBrush(Qt.NoBrush)
        painter.setOpacity(0.2)
        painter.scale(1, -1)
        painter.translate(0, -(pixmap.height()) * 2)
        painter.drawPixmap(0, 0, pixmap)
        
        painter.setOpacity(1)
        
        grad = QLinearGradient()
        grad.setStart(0, 0)
        grad.setFinalStop(0, pixmap.height())
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        grad.setColorAt(0.2, base)
        grad.setColorAt(0.0, base)
        
        painter.setBrush(grad)
        painter.drawRect(0, 0, pixmap.width(), pixmap.height())
        
        painter.restore()