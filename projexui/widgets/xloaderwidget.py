#!/usr/bin/python

"""
Extends the base QLineEdit class to support some additional features like \
setting hints on line edits.
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

import os

from projexui.qt.QtCore import Qt,\
                               QPoint

from projexui.qt.QtGui import QApplication,\
                              QColor,\
                              QLabel,\
                              QFrame,\
                              QMovie,\
                              QHBoxLayout,\
                              QProgressBar,\
                              QVBoxLayout,\
                              QWidget,\
                              QSplitter

from projexui.xpainter import XPainter
from projex.enum import enum
import projexui.resources

class XLoaderProgressBar(QProgressBar):
    def __init__( self, parent ):
        super(XLoaderProgressBar, self).__init__(parent)
        
        # set default properties
        self.setMaximumHeight(12)
        self.setTextVisible(False)
        self.setValue(0)
    
    def paintEvent( self, event ):
        with XPainter(self) as painter:
            x = 0
            y = 0
            w = self.width() - 1
            h = self.height() - 1
            
            # draw percent
            maximum = float(self.maximum())
            if not maximum:
                maximum = 1.0
            
            perc = self.value() / maximum
            painter.setBrush(Qt.gray)
            painter.drawRect(x,(self.height() - 8) / 2, w * perc, 8)
            
            # draw border
            painter.setBrush( Qt.NoBrush )
            painter.setPen( Qt.white )
            painter.drawRect( x, (self.height() - 8) / 2, w, 8)

#------------------------------------------------------------------------------

class XLoaderWidget(QWidget):
    """ """
    Mode    = enum('Spinner', 'Progress')
    MOVIE   = None
    
    def __init__( self, parent = None, style='gray' ):
        super(XLoaderWidget, self).__init__( parent )
        
        # define properties
        self._currentMode       = None
        self._showSubProgress   = False
        
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        # udpate the palette
        palette = self.palette()
        
        if style == 'white':
            palette.setColor( palette.Window, QColor(255, 255, 255, 180) )
        else:
            palette.setColor( palette.Window, QColor( 80, 80, 80, 180 ) )
        
        palette.setColor( palette.Base, Qt.gray )
        palette.setColor( palette.AlternateBase, Qt.lightGray )
        palette.setColor( palette.WindowText, Qt.gray )
        self.setPalette(palette)
        
        # create the movie label
        self._movieLabel = QLabel(self)
        self._movieLabel.setAlignment(Qt.AlignCenter)
        self._movieLabel.setMovie(XLoaderWidget.getMovie())
        self._movieLabel.setPalette(palette)
        
        self._smallMovieLabel = QLabel(self)
        self._smallMovieLabel.setAlignment(Qt.AlignCenter)
        self._smallMovieLabel.setMovie(XLoaderWidget.getMovie())
        self._smallMovieLabel.setPalette(palette)
        self._smallMovieLabel.hide()
        
        # create text label
        self._messageLabel = QLabel(self)
        self._messageLabel.setAlignment(Qt.AlignCenter)
        self._messageLabel.setText('Loading...')
        self._messageLabel.setPalette(palette)
        
        # create primary progress bar
        self._primaryProgressBar    = XLoaderProgressBar(self)
        self._subProgressBar        = XLoaderProgressBar(self)
        
        self._primaryProgressBar.setPalette(palette)
        self._subProgressBar.setPalette(palette)
        
        # create the loader widget
        self._loaderFrame = QFrame(self)
        self._loaderFrame.setFrameShape(QFrame.Box)
        self._loaderFrame.setAutoFillBackground(True)
        self._loaderFrame.setFixedWidth(160)
        self._loaderFrame.setFixedHeight(60)
        
        if style == 'white':
            palette.setColor(palette.Window, QColor('white'))
        else:
            palette.setColor(palette.Window, QColor(85, 85, 85))
        self._loaderFrame.setPalette(palette)
        
        layout = QVBoxLayout()
        layout.addWidget(self._movieLabel)
        layout.addWidget(self._primaryProgressBar)
        layout.addWidget(self._subProgressBar)
        layout.addStretch()
        layout.addWidget(self._messageLabel)
        self._loaderFrame.setLayout(layout)
        
        # set default properties
        self.setAutoFillBackground(True)
        
        # layout the controls
        layout = QVBoxLayout()
        layout.addStretch(1)
        layout.addWidget(self._loaderFrame)
        layout.addWidget(self._smallMovieLabel)
        layout.addStretch(1)
        
        hlayout = QHBoxLayout()
        hlayout.addStretch(1)
        hlayout.addLayout(layout)
        hlayout.addStretch(1)
        
        self.setLayout(hlayout)
        self.setCurrentMode(XLoaderWidget.Mode.Spinner)
        
        # create connections
    
    def currentMode( self ):
        """
        Returns the current mode that this loader's in.
        
        :return     <XLoaderWidget.Mode>
        """
        return self._currentMode
    
    def eventFilter( self, object, event ):
        """
        Resizes this widget with the parent when its resize event is triggered.
        
        :param      object | <QObject>
                    event  | <QEvent>
        
        :return     <bool> | consumed
        """
        if event.type() == event.Resize:
            self.resize(event.size())
            
        elif event.type() == event.Move:
            self.move(event.pos())
        
        elif event.type() == event.Close:
            self.setParent(None)
            self.deleteLater()
        
        return False
    
    def increment(self, amount=1):
        """
        Increments the main progress bar by amount.
        """
        self._primaryProgressBar.setValue(self.value() + amount)
        QApplication.instance().processEvents()
    
    def incrementSub(self, amount=1):
        """
        Increments the sub-progress bar by amount.
        """
        self._subProgressBar.setValue(self.subValue() + amount)
        QApplication.instance().processEvents()
    
    def message( self ):
        """
        Returns the current message being displayed in the loader.
        
        :return     <str>
        """
        return self._messageLabel.text()
    
    def movie(self):
        """
        Returns the movie linked with this loader.
        
        :return     <QMovie>
        """
        return self._movieLabel.movie()
    
    def resize(self, size):
        """
        Handles when the loader is too small for an area.
        
        :param      event | <QResizeEvent>
        """
        super(XLoaderWidget, self).resize(size)
        
        # show small loader
        if size.width() < self._loaderFrame.width() or \
           size.height() < self._loaderFrame.height():
            self._loaderFrame.hide()
            self._smallMovieLabel.show()
        
        # show regular loader
        else:
            self._loaderFrame.show()
            self._smallMovieLabel.hide()
    
    def subValue( self ):
        """
        Returns the value of the sub progress bar.
        
        :return     <int>
        """
        return self._subProgressBar.value()
    
    def setCurrentMode( self, mode ):
        """
        Sets what mode this loader will be in.
        
        :param      mode | <XLoaderWidget.Mode>
        """
        if ( mode == self._currentMode ):
            return
            
        self._currentMode = mode
        
        ajax = mode == XLoaderWidget.Mode.Spinner
        self._movieLabel.setVisible(ajax)
        self._primaryProgressBar.setVisible(not ajax)
        self._subProgressBar.setVisible(not ajax and self._showSubProgress)
    
    def setMessage( self, message ):
        """
        Sets the loading message to display.
        
        :param      message | <str>
        """
        self._messageLabel.setText(message)
    
    def setMovie( self, movie ):
        """
        Sets the movie for this loader to the inputed movie.
        
        :param      movie | <QMovie>
        """
        self._movieLabel.setMovie(movie)
        self._smallMovieLabel.setMovie(movie)
    
    def setTotal( self, amount ):
        """
        Sets the total amount for the main progress bar.
        
        :param      amount | <int>
        """
        self._primaryProgressBar.setValue(0)
        self._primaryProgressBar.setMaximum(amount)
        
        if amount:
            self.setCurrentMode(XLoaderWidget.Mode.Progress)
    
    def setSubTotal( self, amount ):
        """
        Sets the total value for the sub progress bar.
        
        :param      amount | <int>
        """
        self._subProgressBar.setValue(0)
        self._subProgressBar.setMaximum(amount)
        if amount:
            self.setShowSubProgress(True)
    
    def setSubValue( self, value ):
        """
        Sets the current value for the sub progress bar.
        
        :param      value | <int>
        """
        self._subProgressBar.setValue(value)
        
    def setShowSubProgress( self, state ):
        """
        Toggles whether or not the sub progress bar should be visible.
        
        :param      state | <bool>
        """
        ajax = self.currentMode() == XLoaderWidget.Mode.Spinner
        self._showSubProgress = state
        self._subProgressBar.setVisible(not ajax and state)
    
    def setValue(self, value):
        """
        Sets the current value for the primary progress bar.
        
        :param      value | <int>
        """
        self._primaryProgressBar.setValue(value)
    
    def showSubProgress( self ):
        """
        Returns whether or not the sub progress bar is visible when not in
        ajax mode.
        
        :return     <bool>
        """
        return self._showSubProgress
    
    def subValue( self ):
        """
        Returns the sub value for this loader.
        
        :return     <int>
        """
        return self._subProgressBar.value()
    
    def value( self ):
        """
        Returns the value for the primary progress bar.
        
        :return     <int>
        """
        return self._primaryProgressBar.value()
    
    @staticmethod
    def getMovie():
        """
        Returns the movie instance for the loader widget.
        
        :return     <QMovie>
        """
        if not XLoaderWidget.MOVIE:
            filename = projexui.resources.find('img/ajax_loader.gif')
            XLoaderWidget.MOVIE = QMovie()
            XLoaderWidget.MOVIE.setFileName(filename)
            XLoaderWidget.MOVIE.start()
        
        return XLoaderWidget.MOVIE
    
    @staticmethod
    def start(widget, processEvents=True, style=None, movie=None):
        """
        Starts a loader widget on the inputed widget.
        
        :param      widget          | <QWidget>
        
        :return     <XLoaderWidget>
        """
        if style is None:
            style = os.environ.get('PROJEXUI_LOADER_STYLE', 'gray')
        
        # there is a bug with the way the loader is handled in a splitter,
        # so bypass it
        parent = widget.parent()
        while isinstance(parent, QSplitter):
            parent = parent.parent()
        
        # retrieve the loader widget
        loader = getattr(widget, '_private_xloader_widget', None)
        if not loader:
            loader = XLoaderWidget(parent, style)
            
            # make sure that if the widget is destroyed, the loader closes
            widget.destroyed.connect(loader.deleteLater)
            
            setattr(widget, '_private_xloader_widget', loader)
            setattr(widget, '_private_xloader_count', 0)
            
            loader.move(widget.pos())
            if widget.isVisible():
                loader.show()
            
            if movie:
                loader.setMovie(movie)
            
            widget.installEventFilter(loader)
        else:
            count = getattr(widget, '_private_xloader_count', 0)
            setattr(widget, '_private_xloader_count', count + 1)
        
        loader.resize(widget.size())
        return loader
    
    @staticmethod
    def stop(widget, force=False):
        """
        Stops a loader widget on the inputed widget.
        
        :param      widget | <QWidget>
        """
        # make sure we have a widget to stop
        loader = getattr(widget, '_private_xloader_widget', None)
        if not loader:
            return
        
        # decrement the number of times this loader was created for the widget
        # to allow for stacked closure
        count = getattr(widget, '_private_xloader_count', 0)
        if force or count <= 1:
            # close out the loader widget
            setattr(widget, '_private_xloader_count', 0)
            setattr(widget, '_private_xloader_widget', None)
            
            loader.close()
            loader.setParent(None)
            loader.deleteLater()
        else:
            setattr(widget, '_private_xloader_count', count - 1)
    
    @staticmethod
    def stopAll(widget):
        """
        Stops all loader widgets from this parent down, cleaning out the \
        memory for them.
        
        :param      widget  | <QWidget>
        """
        for loader in widget.findChildren(XLoaderWidget):
            loader.setParent(None)
            loader.deleteLater()
    