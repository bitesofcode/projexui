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

import projex.wikitext
from projexui.qt import QtGui, QtCore

alignments = {}
alignments['top left'] = QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft
alignments['top center'] = QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter
alignments['top right'] = QtCore.Qt.AlignTop | QtCore.Qt.AlignRight
alignments['center left'] = QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft
alignments['center'] = QtCore.Qt.AlignCenter
alignments['center right'] = QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight
alignments['bottom left'] = QtCore.Qt.AlignBottom | QtCore.Qt.AlignLeft
alignments['bottom center'] = QtCore.Qt.AlignBottom | QtCore.Qt.AlignHCenter
alignments['bottom right'] = QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight

class XWalkthroughGraphic(QtGui.QGraphicsItemGroup):
    _plugins = {}
    
    def __init__(self, parent=None):
        super(XWalkthroughGraphic, self).__init__(parent)
        
        # define custom properties
        self._properties = {}
        self._parsers = {}
        
        # define parser system
        self._parsers['align'] = lambda x: alignments.get(x, QtCore.Qt.AlignCenter)
        self._parsers['pos'] = lambda x: QtCore.QPoint(*map(int, x.split()))
        self._parsers['offset'] = lambda x: QtCore.QPointF(*map(float, x.split()))
        self._parsers['crop'] = lambda x: QtCore.QRect(*map(int, x.split()))
        self._parsers['scaled'] = lambda x: float(x)
        self._parsers['direction'] = lambda x: getattr(QtGui.QBoxLayout,
                                                       x,
                                                       QtGui.QBoxLayout.TopToBottom)
        
        # define default options
        self.setProperty('direction', QtGui.QBoxLayout.TopToBottom)
        self.setProperty('align', QtCore.Qt.AlignCenter)
    
    def addToGroup(self, item):
        """
        Adds the inputed item to this group.
        
        :param      item | <QtGui.QGraphicsItem>
        """
        effect = QtGui.QGraphicsDropShadowEffect(self.scene())
        effect.setColor(QtGui.QColor('black'))
        effect.setOffset(0, 0)
        effect.setBlurRadius(40)
        item.setGraphicsEffect(effect)
        
        item.setParentItem(self)
        super(XWalkthroughGraphic, self).addToGroup(item)
    
    def addPixmap(self, pixmap):
        """
        Adds a pixmap to this graphics item.
        
        :param      pixmap | <QtGui.QPixmap>
        """
        # add the item to the group
        item = QtGui.QGraphicsPixmapItem(pixmap)
        self.addToGroup(item)
        return item
    
    def addText(self, text, width=None):
        """
        Adds a simple text item to this group.
        
        :param      text            | <str>
                    maximumWidth    | <float> || None
                    maximumHeight   | <float> || None
        """
        item = QtGui.QGraphicsTextItem()
        
        font = item.font()
        font.setFamily('Arial')
        font.setPointSize(12)
        item.setFont(font)
        
        item.setHtml(text)
        item.setDefaultTextColor(QtGui.QColor('white'))
        self.addToGroup(item)
        item.graphicsEffect().setBlurRadius(8)
        
        if width:
            item.setTextWidth(width)
        
        return item
    
    def autoLayout(self, size):
        """
        Lays out this widget within the graphics scene.
        """
        # update the children alignment
        direction = self.property('direction', QtGui.QBoxLayout.TopToBottom)
        x = 0
        y = 0
        base_off_x = 0
        base_off_y = 0
        
        for i, child in enumerate(self.childItems()):
            off_x = 6 + child.boundingRect().width()
            off_y = 6 + child.boundingRect().height()
            
            if direction == QtGui.QBoxLayout.TopToBottom:
                child.setPos(x, y)
                y += off_y
            
            elif direction == QtGui.QBoxLayout.BottomToTop:
                y -= off_y
                child.setPos(x, y)
                if not base_off_y:
                    base_off_y = off_y
            
            elif direction == QtGui.QBoxLayout.LeftToRight:
                child.setPos(x, y)
                x += off_x
                
            else:
                x -= off_x
                child.setPos(x, y)
                if not base_off_x:
                    base_off_x = off_x
        
        #----------------------------------------------------------------------
        
        pos = self.property('pos')
        align = self.property('align')
        offset = self.property('offset')
        rect = self.boundingRect()
        
        if pos:
            x = pos.x()
            y = pos.y()
        
        elif align == QtCore.Qt.AlignCenter:
            x = (size.width() - rect.width()) / 2.0
            y = (size.height() - rect.height()) / 2.0
        
        else:
            if align & QtCore.Qt.AlignLeft:
                x = 0
            elif align & QtCore.Qt.AlignRight:
                x = (size.width() - rect.width())
            else:
                x = (size.width() - rect.width()) / 2.0
            
            if align & QtCore.Qt.AlignTop:
                y = 0
            elif align & QtCore.Qt.AlignBottom:
                y = (size.height() - rect.height())
            else:
                y = (size.height() - rect.height()) / 2.0
        
        if offset:
            x += offset.x()
            y += offset.y()
        
        x += base_off_x
        y += base_off_y
        
        self.setPos(x, y)
    
    def load(self, graphic):
        """
        Loads information for this item from the xml data.
        
        :param      graphic | <XWalkthroughItem>
        """
        for prop in graphic.properties():
            key = prop.name()
            value = prop.value()
            
            if key == 'caption':
                value = projex.wikitext.render(value.strip())
            
            self.setProperty(key, value)
            for attr, attr_value in prop.attributes().items():
                self.setProperty('{0}_{1}'.format(key, attr), attr_value)
        
        self.prepare()
    
    def findReference(self, name, cls=QtGui.QWidget):
        """
        Looks up a reference from the widget based on its object name.
        
        :param      name | <str>
                    cls  | <subclass of QtGui.QObject>
        
        :return     <QtGui.QObject> || None
        """
        return self.scene().findReference(name, cls)
    
    def prepare(self):
        """
        Prepares this graphic item to be displayed.
        """
        text = self.property('caption')
        if text:
            capw = int(self.property('caption_width', 0))
            item = self.addText(text, capw)
    
    def property(self, name, default=None):
        """
        Returns the property for the given value for this graphic.
        
        :param      name | <str>
        
        :return     <variant>
        """
        return self._properties.get(name, default)
    
    def referenceWidget(self):
        """
        Returns the reference widget that this graphic item will access.
        
        :return     <QtGui.QWidget> || None
        """
        return self.scene().referenceWidget()
    
    def setProperty(self, name, value):
        """
        Sets the property for this item to the inputed value for the given name.
        
        :param      name | <str>
                    value | <variant>
        """
        if type(value) in (unicode, str):
            try:
                value = self._parsers[name](value)
            except StandardError:
                pass
        
        self._properties[name] = value
    
    @staticmethod
    def find(typ):
        """
        Returns a graphic for the given type.
        
        :param      typ | <str>
        
        :return     <subclass of XWalkthroughGrpahic> || None
        """
        return XWalkthroughGraphic._plugins.get(typ)
    
    @staticmethod
    def register(typ, cls):
        """
        Registers a graphic type for a given class.
        
        :param      typ | <str>
                    cls | <subclass of XWalkthroughGraphic>
        """
        XWalkthroughGraphic._plugins[typ] = cls

#----------------------------------------------------------------------

class XWalkthroughSnapshot(XWalkthroughGraphic):
    def __init__(self, parent=None):
        super(XWalkthroughSnapshot, self).__init__(parent)
        
        self._parsers['overlay'] = lambda x: eval(x)
        
    def prepare(self):
        """
        Prepares the information for this graphic.
        """
        # determine if we already have a snapshot setup
        pixmap = self.property('pixmap')
        if pixmap is not None:
            return super(XWalkthroughSnapshot, self).prepare()
        
        # otherwise, setup the snapshot
        widget = self.property('widget')
        if type(widget) in (unicode, str):
            widget = self.findReference(widget)
            if not widget:
                return super(XWalkthroughSnapshot, self).prepare()
        
        # test if this is an overlay option
        if self.property('overlay') and widget.parent():
            ref = self.referenceWidget()
            if ref == widget:
                pos = QtCore.QPoint(0, 0)
            else:
                glbl_pos = widget.mapToGlobal(QtCore.QPoint(0, 0))
                pos = ref.mapFromGlobal(glbl_pos)
            
            self.setProperty('pos', pos)
        
        # crop out the options
        crop = self.property('crop', QtCore.QRect(0, 0, 0, 0))
        
        if crop:
            rect = widget.rect()
            if crop.width():
                rect.setWidth(crop.width())
            if crop.height():
                rect.setHeight(crop.height())
            if crop.x():
                rect.setX(rect.width() - crop.x())
            if crop.y():
                rect.setY(rect.height() - crop.y())
            
            pixmap = QtGui.QPixmap.grabWidget(widget, rect)
        else:
            pixmap = QtGui.QPixmap.grabWidget(widget)
        
        scaled = self.property('scaled')
        if scaled:
            pixmap = pixmap.scaled(pixmap.width() * scaled,
                                   pixmap.height() * scaled,
                                   QtCore.Qt.KeepAspectRatio,
                                   QtCore.Qt.SmoothTransformation)
        
        kwds = {}
        kwds['whatsThis'] = widget.whatsThis()
        kwds['toolTip'] = widget.toolTip()
        kwds['windowTitle'] = widget.windowTitle()
        kwds['objectName'] = widget.objectName()
        
        self.setProperty('caption', self.property('caption', '').format(**kwds))
        self.setProperty('pixmap', pixmap)
        self.addPixmap(pixmap)
        
        return super(XWalkthroughSnapshot, self).prepare()

#----------------------------------------------------------------------

XWalkthroughGraphic.register('basic',       XWalkthroughGraphic)
XWalkthroughGraphic.register('snapshot',    XWalkthroughSnapshot)

