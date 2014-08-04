#!/usr/bin/python

""" 
Extends the base QTreeWidget class with additional methods.
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

import projex.text
import re
import weakref

from projex.text import nativestring
from projexui import resources
from xqt import QtCore, QtGui
from projexui.xpainter import XPainter

DATATYPE_FILTER_EXPR = re.compile('((\w+):([\w,\*]+|"[^"]+"?))')

class XListWidgetItem(QtGui.QListWidgetItem):
    def __eq__(self, other):
        # Qt does not define equality for this item...
        return id(self) == id(other)

    def __init__( self, *args ):
        super(XListWidgetItem, self).__init__(*args)
        
        # define custom properties
        self._filterData = {}
        self._movie = None
    
    def _updateFrame(self):
        """
        Updates the frame for the given sender.
        """
        mov = self.movie()
        if mov:
            self.setIcon(QtGui.QIcon(mov.currentPixmap()))
    
    def cleanup(self):
        mov = self.movie()
        if mov:
            mov.frameChanged.disconnect(self._updateFrame)
    
    def filterData(self, key):
        """
        Returns the filter data for the given key.
        
        :param      key | <str>
        
        :return     <str>
        """
        if key == 'text':
            default = nativestring(self.text())
        else:
            default = ''
        return self._filterData.get(key, default)
    
    def movie(self):
        """
        Returns the movie that is playing for this item.
        
        :return     <QtCore.QMovie> || None
        """
        return self._movie
        
    def setFilterData(self, key, value):
        """
        Sets the filtering information for the given key to the inputed value.
        
        :param      key | <str>
                    value | <str>
        """
        self._filterData[nativestring(key)] = nativestring(value)

    def setMovie(self, movie):
        """
        Sets the movie that will play for the given column.
        
        :param      movie  | <QtGui.QMovie> || None
        """
        mov = self.movie()
        if mov is not None:
            mov.frameChanged.disconnect(self._updateFrame)
        
        if movie is not None:
            self._movie = movie
            self.setIcon(QtGui.QIcon(movie.currentPixmap()))
            
            movie.frameChanged.connect(self._updateFrame)
            
            widget = self.listWidget()
            widget.destroyed.connect(self.cleanup)
        else:
            self._movie = None

#----------------------------------------------------------------------

class XListGroupItem(QtGui.QListWidgetItem):
    def __init__(self, parent):
        super(XListGroupItem, self).__init__(parent)
        
        # define the text property
        self._text = ''
        self._expanded = True
        self._children = set()
        
        # define the widget for this item
        lwidget = self.listWidget()
        
        btn = QtGui.QToolButton(lwidget)
        btn.setAutoRaise(True)
        btn.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        btn.setSizePolicy(QtGui.QSizePolicy.Expanding,
                          QtGui.QSizePolicy.Preferred)
        
        ico = 'img/treeview/triangle_down.png'
        btn.setIcon(QtGui.QIcon(resources.find(ico)))
        
        font = btn.font()
        font.setBold(True)
        btn.setFont(font)
        
        lwidget.setItemWidget(self, btn)
        
        # create connections
        btn.clicked.connect(self.toggle)

    def addChild(self, item):
        """
        Adds the inputed item to this group.
        
        :param      item | <QtGui.QListWidgetItem>
        """
        self._children.add(weakref.ref(item))

    def children(self):
        """
        Returns the children in this group.
        
        :return     [<QtGui.QListWidgetItem>, ..]
        """
        new_refs = set()
        output = []
        for ref in self._children:
            item = ref()
            if item is not None:
                output.append(item)
                new_refs.add(ref)
        
        self._children = new_refs
        return output

    def isExpanded(self):
        """
        Returns whether or not this item is currently expanded to show its
        children.
        
        :return     <bool>
        """
        return self._expanded

    def foreground(self):
        """
        Returns the foreground color for this group item.
        
        :return     <QtGui.QColor>
        """
        widget = self.widget()
        if widget:
            palette = widget.palette()
            return palette.color(palette.WindowText)
        else:
            return QtGui.QColor()

    def setExpanded(self, state):
        """
        Expands this group item to the inputed state.
        
        :param      state | <bool>
        """
        if state == self._expanded:
            return
        
        self._expanded = state
        
        # update the button
        btn = self.widget()
        if btn:
            if state:
                ico = 'img/treeview/triangle_down.png'
            else:
                ico = 'img/treeview/triangle_right.png'
            btn.setIcon(QtGui.QIcon(resources.find(ico)))
        
        # update the children
        for child in self.children():
            child.setHidden(not state)

    def setHidden(self, state):
        """
        Marks this item as hidden based on the state.  This will affect all
        its children as well.
        
        :param      state | <bool>
        """
        super(XListGroupItem, self).setHidden(state)
        
        for child in self.children():
            child.setHidden(state or not self.isExpanded())

    def setForeground(self, color):
        """
        Sets the foreground color for this group item to the inputed color.
        
        :param      color | <QtGui.QColor>
        """
        btn = self.widget()
        if btn:
            palette = btn.palette()
            palette.setColor(palette.WindowText, color)
            btn.setPalette(palette)

    def setText(self, text):
        """
        Sets the text for this item.
        
        :param      text | <str>
        """
        self._text = text
        
        # update the label
        btn = self.widget()
        if btn:
            btn.setText(text)

    def toggle(self):
        """
        Toggles whether or not this item is expanded.
        
        :sa     setExpanded
        """
        self.setExpanded(not self.isExpanded())

    def text(self):
        """
        Returns the text for this item.
        
        :return     <str>
        """
        return self._text

    def widget(self):
        return self.listWidget().itemWidget(self)

#------------------------------------------------------------------------------

class XListWidget(QtGui.QListWidget):
    """ Advanced QTreeWidget class. """
    
    __designer_icon__ = resources.find('img/ui/listbox.png')
    
    def __init__( self, *args ):
        super(XListWidget, self).__init__(*args)
        
        # define custom properties
        self._filteredDataTypes = ['text']
        self._autoResizeToContents = False
        self._hint = ''
        self._hintAlignment = QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft
        
        palette = self.palette()
        self._hintColor = palette.color(palette.Disabled, palette.Text)
        
        # create connections
        model = self.model()
        model.dataChanged.connect(self._resizeToContentsIfAuto)
        model.rowsInserted.connect(self._resizeToContentsIfAuto)
        model.rowsRemoved.connect(self._resizeToContentsIfAuto)
        model.layoutChanged.connect(self._resizeToContentsIfAuto)
    
    def __filterItems(self, 
                      terms, 
                      caseSensitive=False):
        """
        Filters the items in this tree based on the inputed keywords.
        
        :param      terms           | {<str> dataType: [<str> term, ..], ..}
                    caseSensitive   | <bool>
        
        :return     <bool> | found
        """
        found = False
        items = []
        
        # collect the items to process
        for i in range(self.count()):
            items.append(self.item(i))
        
        for item in items:
            if not isinstance(item, XListWidgetItem):
                continue
            
            # if there is no filter keywords, then all items will be visible
            if not any(terms.values()):
                found = True
                item.setHidden(False)
            
            else:
                # match all generic keywords
                generic         = terms.get('*', [])
                generic_found   = dict((key, False) for key in generic)
                
                # match all specific keywords
                dtype_found  = dict((col, False) for col in terms if col != '*')
                
                # look for any matches for any data type
                mfound = False
                
                for dataType in self._filteredDataTypes:
                    # determine the check text based on case sensitivity
                    if caseSensitive:
                        check = nativestring(item.filterData(dataType))
                    else:
                        check = nativestring(item.filterData(dataType)).lower()
                    
                    specific = terms.get(dataType, [])
                    
                    # make sure all the keywords match
                    for key in generic + specific:
                        if not key:
                            continue
                        
                        # look for exact keywords
                        elif key.startswith('"') and key.endswith('"'):
                            if key.strip('"') == check:
                                if key in generic:
                                    generic_found[key] = True
                                
                                if key in specific:
                                    dtype_found[dataType] = True
                        
                        # look for ending keywords
                        elif key.startswith('*') and not key.endswith('*'):
                            if check.endswith(key.strip('*')):
                                if key in generic:
                                    generic_found[key] = True
                                if key in specific:
                                    dtype_found[dataType] = True
                        
                        # look for starting keywords
                        elif key.endswith('*') and not key.startswith('*'):
                            if check.startswith(key.strip('*')):
                                if key in generic:
                                    generic_found[key] = True
                                if key in specific:
                                    dtype_found[dataType] = True
                        
                        # look for generic keywords
                        elif key.strip('*') in check:
                            if key in generic:
                                generic_found[key] = True
                            if key in specific:
                                dtype_found[dataType] = True
                    
                    mfound = all(dtype_found.values()) and \
                             all(generic_found.values())
                    if mfound:
                        break
                
                item.setHidden(not mfound)
                
                if mfound:
                    found = True
        
        return found
    
    def _resizeToContentsIfAuto(self):
        """
        Resizes this widget to fit its contents if auto resizing is enabled.
        """
        if self.autoResizeToContents():
            self.resizeToContents()
    
    def autoResizeToContents(self):
        """
        Sets whether or not this widget should automatically resize to its
        contents.
        
        :return     <bool>
        """
        return self._autoResizeToContents
    
    def filteredDataTypes( self ):
        """
        Returns the data types that are used for filtering for this tree.
        
        :return     [<str>, ..]
        """
        return self._filteredDataTypes
    
    @QtCore.Slot(str)
    def filterItems(self, 
                    terms, 
                    caseSensitive=False):
        """
        Filters the items in this tree based on the inputed text.
        
        :param      terms           | <str> || {<str> datatype: [<str> opt, ..]}
                    caseSensitive   | <bool>
        """
        # create a dictionary of options
        if type(terms) != dict:
            terms = {'*': nativestring(terms)}
        
        # validate the "all search"
        if '*' in terms and type(terms['*']) != list:
            sterms = nativestring(terms['*'])
            
            if not sterms.strip():
                terms.pop('*')
            else:
                dtype_matches = DATATYPE_FILTER_EXPR.findall(sterms)
                
                # generate the filter for each data type
                for match, dtype, values in dtype_matches:
                    sterms = sterms.replace(match, '')
                    terms.setdefault(dtype, [])
                    terms[dtype] += values.split(',')
                
                keywords = sterms.replace(',', '').split()
                while '' in keywords:
                    keywords.remove('')
                
                terms['*'] = keywords
        
        # filter out any data types that are not being searched
        filtered_dtypes = self.filteredDataTypes()
        filter_terms = {}
        for dtype, keywords in terms.items():
            if dtype != '*' and not dtype in filtered_dtypes:
                continue
            
            if not caseSensitive:
                keywords = [nativestring(keyword).lower() for keyword in keywords]
            else:
                keywords = map(nativestring, keywords)
            
            filter_terms[dtype] = keywords
        
        self.__filterItems(filter_terms, caseSensitive)
    
    def hint(self):
        """
        Returns the hint for this list widget.
        
        :return     <str>
        """
        return self._hint
    
    def hintAlignment( self ):
        """
        Returns the alignment used for the hint rendering.
        
        :return     <QtCore.Qt.Alignment>
        """
        return self._hintAlignment
    
    def hintColor( self ):
        """
        Returns the color used for the hint rendering.
        
        :return     <QtGui.QColor>
        """
        return self._hintColor
    
    def paintEvent(self, event):
        """
        Overloads the paint event to support rendering of hints if there are
        no items in the tree.
        
        :param      event | <QPaintEvent>
        """
        super(XListWidget, self).paintEvent(event)
        
        if not self.visibleCount() and self.hint():
            text    = self.hint()
            rect    = self.rect()
            
            # modify the padding on the rect
            w = min(250, rect.width() - 30)
            x = (rect.width() - w) / 2
            
            rect.setX(x)
            rect.setY(rect.y() + 15)
            rect.setWidth(w)
            rect.setHeight(rect.height() - 30)
            
            align = int(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
            
            # setup the coloring options
            clr     = self.hintColor()
            
            # paint the hint
            with XPainter(self.viewport()) as painter:
                painter.setPen(clr)
                painter.drawText(rect, align | QtCore.Qt.TextWordWrap, text)
    
    def resizeEvent(self, event):
        super(XListWidget, self).resizeEvent(event)
        
        # resize the group items
        width = event.size().width()
        for i in range(self.count()):
            item = self.item(i)
            if isinstance(item, XListGroupItem):
                item.setSizeHint(QtCore.QSize(width, 24))
        
        # auto-resize based on the contents
        if self.autoResizeToContents():
            self.resizeToContents()
    
    @QtCore.Slot()
    def resizeToContents(self):
        """
        Resizes the list widget to fit its contents vertically.
        """
        if self.count():
            item = self.item(self.count() - 1)
            rect = self.visualItemRect(item)
            height = rect.bottom() + 8
            height = max(28, height)
            self.setFixedHeight(height)
        else:
            self.setFixedHeight(self.minimumHeight())
    
    def setAutoResizeToContents(self, state):
        """
        Sets whether or not this widget should automatically resize its
        height based on its contents.
        
        :param      state | <bool>
        """
        self._autoResizeToContents = state
        
        if state:
            self.resizeToContents()
            self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        else:
            self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
            self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
    
    def setHint(self, hint):
        """
        Sets the hint for this list widget.
        
        :param     hint | <str>
        """
        self._hint = hint
    
    def setHintAlignment( self, align ):
        """
        Sets the alignment used for the hint rendering.
        
        :param      align | <QtCore.Qt.Alignment>
        """
        self._hintAlignment = align
    
    def setHintColor( self, color ):
        """
        Sets the color used for the hint rendering.
        
        :param      color | <QtGui.QColor>
        """
        self._hintColor = color
    
    def setFilteredDataTypes( self, dataTypes ):
        """
        Sets the data types that will be used for filtering of this 
        tree's items.
        
        :param      data types | [<str>, ..]
        """
        self._filteredDataTypes = dataTypes
    
    def visibleCount(self):
        """
        Returns the number of visible items in this list.
        
        :return     <int>
        """
        return sum(int(not self.item(i).isHidden()) for i in range(self.count()))
    
    x_autoResizeToContents = QtCore.Property(bool,
                                      autoResizeToContents,
                                      setAutoResizeToContents)
    
    x_hint = QtCore.Property(str, hint, setHint)
    
# define the designer properties
__designer_plugins__ = [XListWidget]