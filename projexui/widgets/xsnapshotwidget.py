""" Defines an interface for creating desktop snapshots. """

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

import time

from projex.text import nativestring

from projexui.qt.QtCore import Qt, QRect, QPoint
from projexui.qt.QtGui  import QWidget,\
                               QApplication,\
                               QFileDialog,\
                               QPen,\
                               QColor,\
                               QBrush,\
                               QPixmap,\
                               QRegion

class XSnapshotWidget(QWidget):
    def __init__(self, parent=None):
        super(XSnapshotWidget, self).__init__(parent)
        
        # define custom properties
        self._region = QRect()
        self._filepath = ''
        
        # define custom properties
        palette = self.palette()
        palette.setColor(palette.Window, QColor('white'))
        self.setPalette(palette)
        self.setWindowOpacity(0.5)
        self.setWindowFlags(Qt.SplashScreen)
        self.setFocus()
    
    def accept(self):
        """
        Prompts the user for the filepath to save and then saves the image.
        """
        filetypes = 'PNG Files (*.png);;JPG Files (*.jpg);;All Files (*.*)'
        filename = QFileDialog.getSaveFileName(None,
                                               'Save Snapshot',
                                               self.filepath(),
                                               filetypes)
        
        if type(filename) == tuple:
            filename = filename[0]
        
        filename = nativestring(filename)
        if not filename:
            self.reject()
        else:
            self.setFilepath(filename)
            self.save()
    
    def filepath(self):
        """
        Returns the filepath that is going to be asved for this snapshot widget.
        
        :return     <str>
        """
        return self._filepath
    
    def hideWindow(self):
        """
        Sets the window to hide/show while taking the snapshot.
        
        :param      window | <QMainWindow> || <QDialog>
        """
        return self._hideWindow
    
    def keyPressEvent(self, event):
        """
        Listens for the escape key to cancel out from this snapshot.
        
        :param      event | <QKeyPressEvent>
        """
        # reject on a cancel
        if event.key() == Qt.Key_Escape:
            self.reject()
        
        super(XSnapshotWidget, self).keyPressEvent(event)
    
    def mousePressEvent(self, event):
        """
        Starts the selection process for this widget and snapshot area.
        
        :param      event | <QMousePressEvent>
        """
        self._region.setX(event.pos().x())
        self._region.setY(event.pos().y())
        super(XSnapshotWidget, self).mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """
        Drags the selection view for this widget.
        
        :param      event | <QMouseMoveEvent>
        """
        w = event.pos().x() - self._region.x()
        h = event.pos().y() - self._region.y()
        
        self._region.setWidth(w)
        self._region.setHeight(h)
        self.repaint()
        
        super(XSnapshotWidget, self).mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """
        Finishes the selection event.
        
        :param      event | <QMouseReleaseEvent>
        """
        self.accept()
        super(XSnapshotWidget, self).mouseReleaseEvent(event)
    
    def paintEvent(self, event):
        """
        Handles the drawing for this widget and its selection region.
        
        :param      event | <QPaintEvent>
        """
        pen = QPen(Qt.DashLine)
        pen.setColor(QColor('red'))
        with XPainter(self) as painter:
            painter.setPen(pen)
            clr = QColor('black')
            clr.setAlpha(100)
            painter.setBrush(clr)
            
            painter.drawRect(self._region)
    
    def reject(self):
        """
        Rejects the snapshot and closes the widget.
        """
        if self.hideWindow():
            self.hideWindow().show()
            
        self.close()
        self.deleteLater()
    
    def region(self):
        """
        Returns the selection region defined by the rectangle for snapshoting.
        
        :return     <QRect>
        """
        return self._region
    
    def save(self):
        """
        Saves the snapshot based on the current region.
        """
        # close down the snapshot widget
        if self.hideWindow():
            self.hideWindow().hide()
        
        self.hide()
        QApplication.processEvents()
        time.sleep(1)
        
        # create the pixmap to save
        wid = QApplication.desktop().winId()
        
        if not self._region.isNull():
            x = self._region.x()
            y = self._region.y()
            w = self._region.width()
            h = self._region.height()
        else:
            x = self.x()
            y = self.y()
            w = self.width()
            h = self.height()
        
        pixmap = QPixmap.grabWindow(wid, x, y, w, h)
        pixmap.save(self.filepath())
        
        self.close()
        self.deleteLater()
        if self.hideWindow():
            self.hideWindow().show()
    
    def show(self):
        """
        Shows this widget and hides the specified window if necessary.
        """
        super(XSnapshotWidget, self).show()
        
        if self.hideWindow():
            self.hideWindow().hide()
            QApplication.processEvents()
    
    def setFilepath(self, filepath):
        """
        Sets the filepath that will be saved for this snapshot.
        
        :param      filepath | <str>
        """
        self._filepath = filepath
    
    def setHideWindow(self, window):
        """
        Sets the window that will be hidden while this snapshot is being
        taken.
        
        :param      window | <QMainWindow>
        """
        self._hideWindow = window
    
    def setRegion(self, rect):
        """
        Sets the region rectangle to the inputed rect.
        
        :param      rect | <QRect>
        """
        if rect is not None:
            self._region = rect
    
    @staticmethod
    def capture(rect=None, filepath='', prompt=True, hideWindow=None):
        """
        Prompts the user to capture the screen.
        
        :param      rect     | <QRect>
                    filepath | <str>
                    prompt   | <bool>
        
        :return     (<str> filepath, <bool> accepted)
        """
        widget = XSnapshotWidget(QApplication.desktop())
        widget.setRegion(rect)
        widget.setHideWindow(hideWindow)
        widget.setFilepath(filepath)
        widget.move(1, 1)
        widget.resize(QApplication.desktop().size())
        
        if prompt or not filepath:
            widget.show()
        else:
            widget.save()