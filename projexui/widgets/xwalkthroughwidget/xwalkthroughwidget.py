#!/usr/bin/python

""" Creates reusable Qt widgets for various applications. """

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

from projexui.qt import QtGui, QtCore, Signal
from projexui.widgets.xstackedwidget import XStackedWidget
from .xwalkthroughscene import XWalkthroughScene
from .xwalkthrough import XWalkthrough, XWalkthroughSlide

class XWalkthroughButton(QtGui.QPushButton):
    def __init__(self, text, parent=None):
        super(XWalkthroughButton, self).__init__(text, parent)
        
        font = self.font()
        font.setBold(True)
        self.setFont(font)
        
        palette = self.palette()
        palette.setColor(palette.Highlight, QtGui.QColor('#3EBDFF'))
        palette.setColor(palette.HighlightedText, QtGui.QColor('white'))
        palette.setColor(palette.Button, QtGui.QColor('#4070FF'))
        palette.setColor(palette.ButtonText, QtGui.QColor('white'))
        
        self.setPalette(palette)
        self.setFont(font)
        self.setFixedSize(150, 30)

#----------------------------------------------------------------------

class XWalkthroughWidget(QtGui.QWidget):
    finished = Signal()
    
    def __init__(self, parent):
        super(XWalkthroughWidget, self).__init__(parent)
        
        # setup the properties
        self.setAutoFillBackground(True)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setMouseTracking(True)
        
        # install the event filter
        parent.installEventFilter(self)
        
        # define child widgets
        self._direction = QtGui.QBoxLayout.TopToBottom
        self._slideshow = XStackedWidget(self)
        self._previousButton = XWalkthroughButton('Previous', self)
        self._nextButton = XWalkthroughButton('Finish', self)
        self._previousButton.hide()
        
        self.resize(parent.size())
        
        # setup look for the widget
        clr = QtGui.QColor('black')
        clr.setAlpha(120)
        
        palette = self.palette()
        palette.setColor(palette.Window, clr)
        palette.setColor(palette.WindowText, QtGui.QColor('white'))
        self.setPalette(palette)
        
        # create connections
        self._slideshow.currentChanged.connect(self.updateUi)
        self._previousButton.clicked.connect(self.goBack)
        self._nextButton.clicked.connect(self.goForward)

    def addSlide(self, slide):
        """
        Adds a new slide to the widget.
        
        :param      slide | <XWalkthroughSlide>
        
        :return     <QtGui.QGraphicsView>
        """
        # create the scene
        scene = XWalkthroughScene(self)
        scene.setReferenceWidget(self.parent())
        scene.load(slide)
        
        # create the view
        view = QtGui.QGraphicsView(self)
        view.setCacheMode(view.CacheBackground)
        view.setScene(scene)
        view.setStyleSheet('background: transparent')
        view.setFrameShape(view.NoFrame)
        view.setInteractive(False)
        view.setFocusPolicy(QtCore.Qt.NoFocus)
        view.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        view.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        
        # add the slide
        self._slideshow.addWidget(view)
        self.updateUi()
        
        return view

    def autoLayout(self):
        """
        Automatically lays out the contents for this widget.
        """
        try:
            direction = self.currentSlide().scene().direction()
        except AttributeError:
            direction = QtGui.QBoxLayout.TopToBottom
        
        size = self.size()
        self._slideshow.resize(size)
        
        prev = self._previousButton
        next = self._nextButton
        
        if direction == QtGui.QBoxLayout.BottomToTop:
            y = 9
        else:
            y = size.height() - prev.height() - 9
        
        prev.move(9, y)
        next.move(size.width() - next.width() - 9, y)
        
        # update the layout for the slides
        for i in range(self._slideshow.count()):
            widget = self._slideshow.widget(i)
            widget.scene().autoLayout(size)

    def cancel(self):
        """
        Hides/exits the walkthrough.
        """
        self.hide()

    def clear(self):
        """
        Clears the content for this widget.
        """
        for i in range(self._slideshow.count()):
            widget = self._slideshow.widget(0)
            widget.close()
            widget.setParent(None)
            widget.deleteLater()
        
        self.updateUi()

    def currentSlide(self):
        """
        Returns the current slide that is being displayed for this walkthrough.
        
        :return     <QtGui.QGraphicsView>
        """
        return self._slideshow.currentWidget()

    def eventFilter(self, obj, event):
        """
        Filters the parent object for its resize event.
        
        :param      obj     | <QtCore.QObject>
                    event   | <QtCore.QEvent>
        
        :return     <bool> | consumed
        """
        if event.type() == event.Resize:
            self.resize(event.size())
        
        return False

    def goBack(self):
        """
        Moves to the previous slide.
        """
        self._slideshow.slideInPrev()

    def goForward(self):
        """
        Moves to the next slide or finishes the walkthrough.
        """
        if self._slideshow.currentIndex() == self._slideshow.count() - 1:
            self.finished.emit()
        else:
            self._slideshow.slideInNext()

    def keyPressEvent(self, event):
        """
        Listens for the left/right keys and the escape key to control
        the slides.
        
        :param      event | <QtCore.Qt.QKeyEvent>
        """
        if event.key() == QtCore.Qt.Key_Escape:
            self.cancel()
        elif event.key() == QtCore.Qt.Key_Left:
            self.goBack()
        elif event.key() == QtCore.Qt.Key_Right:
            self.goForward()
        elif event.key() == QtCore.Qt.Key_Home:
            self.restart()
        
        super(XWalkthroughWidget, self).keyPressEvent(event)

    def load(self, walkthrough):
        """
        Loads the XML text for a new walkthrough.
        
        :param      walkthrough | <XWalkthrough> || <str> || <xml.etree.ElementTree.Element>
        """
        if type(walkthrough) in (str, unicode):
            walkthrough = XWalkthrough.load(walkthrough)
        
        self.setUpdatesEnabled(False)
        self.clear()
        for slide in walkthrough.slides():
            self.addSlide(slide)
        self.setUpdatesEnabled(True)
        self.updateUi()

    def restart(self):
        """
        Restarts this walkthrough from the beginning.
        """
        self._slideshow.setCurrentIndex(0)

    def resizeEvent(self, event):
        """
        Moves the widgets around the system.
        
        :param      event | <QtGui.QResizeEvent>
        """
        super(XWalkthroughWidget, self).resizeEvent(event)
        
        if self.isVisible():
            self.autoLayout()

    def updateUi(self):
        """
        Updates the interface to show the selection buttons.
        """
        index = self._slideshow.currentIndex()
        count = self._slideshow.count()
        
        self._previousButton.setVisible(index != 0)
        self._nextButton.setText('Finish' if index == count - 1 else 'Next')
        self.autoLayout()

    def mouseReleaseEvent(self, event):
        """
        Moves the slide forward when clicked.
        
        :param      event | <QtCore.QMouseEvent>
        """
        if event.button() == QtCore.Qt.LeftButton:
            if event.modifiers() == QtCore.Qt.ControlModifier:
                self.goBack()
            else:
                self.goForward()
        
        super(XWalkthroughWidget, self).mouseReleaseEvent(event)

    def showEvent(self, event):
        """
        Raises this widget when it is shown.
        
        :param      event | <QtCore.QShowEvent>
        """
        super(XWalkthroughWidget, self).showEvent(event)
        
        self.autoLayout()
        self.restart()
        self.setFocus()
        self.raise_()

