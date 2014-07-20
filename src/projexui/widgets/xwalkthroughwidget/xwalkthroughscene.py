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

from projexui.qt import QtGui

from .xwalkthroughgraphics import *

class XWalkthroughScene(QtGui.QGraphicsScene):
    def __init__(self, view):
        super(XWalkthroughScene, self).__init__(view)
        
        # define custom properties
        self._view = view
        self._direction = QtGui.QBoxLayout.TopToBottom
        self._referenceWidget = None

    def addGraphic(self, typ='basic'):
        """
        Adds a new graphic to the scene.
        
        :param      typ | <str>
        
        :return     <XWalkthroughGraphic> || None
        """
        cls = XWalkthroughGraphic.find(typ)
        if not cls:
            return None

        graphic = cls()
        self.addItem(graphic)
        
        return graphic

    def autoLayout(self, size=None):
        """
        Updates the layout for the graphics within this scene.
        """
        if size is None:
            size = self._view.size()
        
        self.setSceneRect(0, 0, size.width(), size.height())
        for item in self.items():
            if isinstance(item, XWalkthroughGraphic):
                item.autoLayout(size)

    def direction(self):
        """
        Returns the direction this slide will be in.
        
        :return     <QtGui.QBoxLayout.Direction>
        """
        return self._direction

    def findReference(self, name, cls=QtGui.QWidget):
        """
        Looks up a reference from the widget based on its object name.
        
        :param      name | <str>
                    cls  | <subclass of QtGui.QObject>
        
        :return     <QtGui.QObject> || None
        """
        ref_widget = self._referenceWidget
        if not ref_widget:
            return None
        
        if ref_widget.objectName() == name:
            return ref_widget
        return ref_widget.findChild(cls, name)

    def prepare(self):
        """
        Prepares the items for display.
        """
        for item in self.items():
            if isinstance(item, XWalkthroughGraphic):
                item.prepare()

    def load(self, slide):
        """
        Loads the inputed slide to the scene.
        
        :param      slide | <XWalkthroughSlide>
        """
        self._direction = getattr(QtGui.QBoxLayout,
                                  slide.attributes().get('direction', 'TopToBottom'),
                                  QtGui.QBoxLayout.TopToBottom)
        
        for item in slide.items():
            graphic = self.addGraphic(item.attributes().get('type', 'basic'))
            if graphic is not None:
                graphic.load(item)

    def referenceWidget(self):
        """
        Returns the reference widget that this graphic item will access.
        
        :return     <QtGui.QWidget> || None
        """
        return self._referenceWidget
    
    def setReferenceWidget(self, widget):
        """
        Sets the reference widget that this graphic item will access.  This
        widget will be defined as the parent of the XWalkthroughWidget that
        this graphic is a part of.
        
        :param      widget | <QtGui.QWidget> || None
        """
        self._referenceWidget = widget



