#!/usr/bin/python

""" [desc] """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintenance information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

from xqt import QtCore, QtGui, unwrapVariant

import datetime

from projex.lazymodule import LazyModule
from projex.text import nativestring
from projexui import resources

from .xtreewidgetitem import XTreeWidgetItem
xtreewidget = LazyModule('projexui.widgets.xtreewidget')

class XTreeWidgetDelegate(QtGui.QItemDelegate):
    """ Delegate for additional features to the XTreeWidget. """
    def __init__(self, parent):
        super(XTreeWidgetDelegate, self).__init__(parent)
        
        # set custom properties
        self._gridPen           = QtGui.QPen()
        self._showGrid          = True
        self._showGridColumns   = True
        self._showGridRows      = True
        self._extendsTree       = True
        self._showRichText      = False
        self._displayMappers    = {}
        self._foreground        = {}
        self._background        = {}
        self._headerIndex       = 0
        self._currentOverlay    = None
        self._currentDisplay    = None
        self._showHighlights    = True
        self._disabledEditingColumns = set()
        
        self._datetimeFormat    = '%m/%d/%y @ %I:%M%p'
        self._timeFormat        = '%I:%M%p'
        self._dateFormat        = '%m/%d/%y'
        
        self._hoverBackground   = None
        self._hoverForeground   = None
        self._hoverIcon         = None
        self._expandIcon        = None
        
        self._useCheckMaps      = True
        self._checkOnMap        = resources.find('img/check_on.png')
        self._checkPartialMap   = resources.find('img/check_part.png')
        self._checkOffMap       = resources.find('img/check_off.png')
        
        # setup defaults
        palette     = parent.palette()
        base_clr    = palette.color(palette.Base)
        avg         = (base_clr.red() + base_clr.green() + base_clr.blue())/3.0
        
        if avg < 80:
            grid_clr = base_clr.lighter(200)
        elif avg < 140:
            grid_clr = base_clr.lighter(140)
        else:
            grid_clr = base_clr.darker(140)
            
        self.setGridPen(grid_clr)

    def background(self, column, default=None):
        """
        Returns the background brush for the given column of this delegate.
        
        :param      column | <int>
                    default | <variant>
        
        :return     <QtGui.QBrush> || None
        """
        return self._background.get(column, default)

    def checkPartialMap(self):
        """
        Returns the pixmap to use when rendering a check in the partial state.
        
        :return     <QtGui.QPixmap> || None
        """
        return self._checkPartialMap
    
    def checkOffMap(self):
        """
        Returns the pixmap to use when rendering a check in the off state.
        
        :return     <QtGui.QPixmap> || None
        """
        return self._checkOffMap
    
    def checkOnMap(self):
        """
        Returns the pixmap to use when rendering a check on state.
        
        :return     <QtGui.QPixmap> || None
        """
        return self._checkOnMap
    
    def createEditor(self, parent, option, index):
        """
        Creates a new editor for the given index parented to the inputed widget.
        
        :param      parent | <QWidget>
                    option | <QStyleOption>
                    index  | <QModelIndex>
        
        :return     <QWidget> || None
        """
        if index.column() in self._disabledEditingColumns:
            return None
        
        editor = super(XTreeWidgetDelegate, self).createEditor(parent,
                                                               option,
                                                               index)
        
        if isinstance(editor, QtGui.QDateTimeEdit):
            editor.setCalendarPopup(True)
        
        return editor
    
    def datetimeFormat(self):
        """
        Returns the datetime format for this delegate.
        
        :return     <str>
        """
        return self._datetimeFormat
    
    def dateFormat(self):
        """
        Returns the date format for this delegate.
        
        :return     <str>
        """
        return self._dateFormat
    
    def disableColumnEditing(self, column):
        """
        Adds the given column to the disabled list for editing.
        
        :param      column | <int>
        """
        self._disabledEditingColumns.add(column)
    
    def displayMapper( self, column ):
        """
        Returns the display mapper for this column.
        
        :param      column | <int>
        
        :return     <callable> || None
        """
        return self._displayMappers.get(column)
    
    def drawBackground( self, painter, opt, rect, brush ):
        """
        Make sure the background extends to 0 for the first item.
        
        :param      painter | <QtGui.QPainter>
                    rect    | <QtCore.QRect>
                    brush   | <QtGui.QBrush>
        """
        if not brush:
            return
        
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(brush)
        painter.drawRect(rect)
    
    def drawCheck( self, painter, option, rect, state ):
        """
        Renders a check indicator within the rectangle based on the inputed \
        check state.
        
        :param      painter | <QtGui.QPainter>
                    option  | <QtGui.QStyleOptionViewItem>
                    rect    | <QtGui.QRect>
                    state   | <QtCore.Qt.CheckState>
        """
        if not self.useCheckMaps():
            return super(XTreeWidgetDelegate, self).drawCheck(painter,
                                                              option,
                                                              rect,
                                                              state)
        
        pixmap = None
        if state == QtCore.Qt.Checked:
            pixmap = self.checkOnMap()
        elif state == QtCore.Qt.PartiallyChecked:
            pixmap = self.checkPartialMap()
        elif state == QtCore.Qt.Unchecked:
            pixmap = self.checkOffMap()
        
        if type(pixmap) in (str, unicode):
            pixmap = QtGui.QPixmap(pixmap)
        
        if not pixmap:
            return
        
        x = rect.x() + (rect.width() - 16) / 2.0
        y = rect.y() + (rect.height() - 16) / 2.0
        
        painter.drawPixmap(int(x), int(y), pixmap)
    
    def drawDisplay(self, painter, option, rect, text):
        """
        Overloads the drawDisplay method to render HTML if the rich text \
        information is set to true.
        
        :param      painter | <QtGui.QPainter>
                    option  | <QtGui.QStyleOptionItem>
                    rect    | <QtCore.QRect>
                    text    | <str>
        """
        if self.showRichText():
            # create the document
            doc = QtGui.QTextDocument()
            doc.setTextWidth(float(rect.width()))
            doc.setHtml(text)
            
            # draw the contents
            painter.translate(rect.x(), rect.y())
            doc.drawContents(painter, QtCore.QRectF(0, 
                                                    0, 
                                                    float(rect.width()), 
                                                    float(rect.height())))
                                             
            painter.translate(-rect.x(), -rect.y())
        else:
            if type(text).__name__ not in ('str', 'unicode', 'QString'):
                text = nativestring(text)
            
            metrics = QtGui.QFontMetrics(option.font)
            text = metrics.elidedText(text,
                                      QtCore.Qt.TextElideMode(option.textElideMode),
                                      rect.width())
            
            painter.setFont(option.font)
            painter.drawText(rect, int(option.displayAlignment), text)
    
    def drawOverlay(self, painter, option, rect, icon):
        """
        Draws the overlay pixmap for this item.
        
        :param      painter | <QtGui.QPainter>
                    option  | <QtGui.QSylteOptionIndex>
                    rect    | <QtCore.QRect>
                    pixmap  | <QtGui.QIcon>
        """
        if icon and not icon.isNull():
            painter.drawPixmap(rect, icon.pixmap(rect.width(), rect.height()))
    
    def drawGrid(self, painter, opt, rect, index):
        """
        Draws the grid lines for this delegate.
        
        :param      painter | <QtGui.QPainter>
                    opt     | <QtGui.QStyleOptionItem>
                    rect    | <QtCore.QRect>
                    index   | <QtGui.QModelIndex>
        """
        if not self.showGrid():
            return
        
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.setPen(self.gridPen())
        
        size = self.gridPen().width() + 1
        
        # draw the lines
        lines = []
        
        # add the column line
        if self.showGridColumns():
            lines.append(QtCore.QLine(rect.width() - size, 
                                      0, 
                                      rect.width() - size, 
                                      rect.height() - size))
        
        # add the row line
        if (self.showGridRows()):
            lines.append(QtCore.QLine(0, 
                                      rect.height() - size, 
                                      rect.width() - size, 
                                      rect.height() - size))
        
        painter.drawLines(lines)

    def enableColumnEditing(self, column):
        """
        Removes the given column from the disabled list for editing.
        
        :param      column | <int>
        """
        try:
            self._disabledEditingColumns.remove(column)
        except KeyError:
            pass
    
    def foreground(self, column, default=None):
        """
        Returns the foreground brush for the given column of this delegate.
        
        :param      column | <int>
                    default | <variant>
        
        :return     <QtGui.QBrush> || None
        """
        return self._foreground.get(column, default)

    def gridPen( self ):
        """
        Returns the pen that will be used when drawing the grid lines.
        
        :return     <QtGui.QPen>
        """
        return self._gridPen
    
    def extendsTree( self ):
        """
        Returns whether or not the grid lines should extend through the tree \
        area or not.
        
        :return <bool>
        """
        return self._extendsTree
    
    def paint(self, painter, opt, index):
        """
        Overloads the paint method to draw the grid and other options for \
        this delegate.
        
        :param      painter | <QtGui.QPainter>
                    opt     | <QtGui.QStyleOptionItem>
                    index   | <QtGui.QModelIndex>
        """
        # prepare the painter
        painter.save()
        painter.resetTransform()
        
        # extract data from the tree
        tree         = self.parent()
        column       = index.column()
        item         = tree.itemFromIndex(index)
        is_xtreeitem = isinstance(item, XTreeWidgetItem)
        hovered      = False
        font         = item.font(index.column())
        opt.font     = font
        palette      = tree.palette()
        
        painter.translate(opt.rect.x(), opt.rect.y())
        rect_w = opt.rect.width()
        rect_h = opt.rect.height()
        
        painter.setClipRect(0, 0, rect_w, rect_h)
        
        # grab the check information
        checkState = None
        size       = opt.decorationSize
        value      = unwrapVariant(index.data(QtCore.Qt.CheckStateRole))
        
        if value is not None:
            checkState = item.checkState(index.column())
            check_size = min(size.width(), size.height())
            check_size = min(14, check_size)
            checkRect  = QtCore.QRect(2, 
                                     (rect_h - check_size) / 2.0, 
                                      check_size, 
                                      check_size)
        else:
            checkRect = QtCore.QRect()
        
        # determine hovering options
        if tree.hoverMode() != xtreewidget.XTreeWidget.HoverMode.NoHover and \
           item.flags() & XTreeWidgetItem.ItemIsHoverable:
            
            # hover particular columns
            if tree.hoverMode() == xtreewidget.XTreeWidget.HoverMode.HoverItems and \
               item == tree.hoveredItem() and \
               column == tree.hoveredColumn():
                hovered = True
            
            # hover particular items
            elif tree.hoverMode() == xtreewidget.XTreeWidget.HoverMode.HoverRows and \
                 id(item) == id(tree.hoveredItem()):
                hovered = True
        
        # setup the decoration information
        if item.isExpanded() and is_xtreeitem and item.expandedIcon(column):
            icon = item.expandedIcon(column)
        
        elif hovered and tree.hoveredColumn() == column and \
             is_xtreeitem and \
             item.hoverIcon(column):
            icon = item.hoverIcon(column)
        
        else:
            icon = item.icon(column)
        
        if icon and not icon.isNull():
            size    = icon.actualSize(opt.decorationSize)
            pixmap  = icon.pixmap(size)
            
            if checkRect:
                x = checkRect.right() + 2
            else:
                x = 0
            
            y = 0
            w = opt.decorationSize.width()
            h = opt.decorationSize.height()
            
            x += 2
            y += (rect_h - size.height()) / 2.0
            
            decorationRect  = QtCore.QRect(x, y, w, h)
        else:
            pixmap          = QtGui.QPixmap()
            overlay         = QtGui.QIcon()
            decorationRect  = QtCore.QRect()
        
        if is_xtreeitem:
            overlay = item.iconOverlay(column)
            dec_w = decorationRect.width()
            dec_h = decorationRect.height()
            over_w = int(dec_w / 1.7)
            over_h = int(dec_h / 1.7)
            overlayRect = QtCore.QRect(decorationRect.right() - over_w,
                                       decorationRect.bottom() - over_h,
                                       over_w,
                                       over_h)
        else:
            overlay = QtGui.QPixmap()
            overlayRect = QtCore.QRect()
        
        # setup the coloring information
        bg = None
        fg = None
        
        if self.showHighlights() and tree.selectionModel().isSelected(index):
            palette = tree.palette()
            bg = QtGui.QBrush(palette.color(palette.Highlight))
            fg = QtGui.QBrush(palette.color(palette.HighlightedText))
        
        elif hovered:
            bg = tree.hoverBackground()
            fg = tree.hoverForeground()
            
            if is_xtreeitem:
                bg = item.hoverBackground(column, bg)
                fg = item.hoverForeground(column, fg)
        
        if not bg:
            bg_role = unwrapVariant(item.data(column, QtCore.Qt.BackgroundRole))
            if bg_role is not None:
                bg = item.background(column)
            else:
                bg = self.background(column)
        
        if not fg:
            fg_role = unwrapVariant(item.data(column, QtCore.Qt.ForegroundRole))
            if fg_role is not None:
                fg = item.foreground(column)
            else:
                fg = self.foreground(column)
        
        if not fg:
            fg = QtGui.QBrush(palette.color(palette.Text))
        
        # draw custom text
        mapper = self.displayMapper(column)
        if mapper:
            text = mapper(unwrapVariant(index.data(), ''))
        
        # draw specific type text
        else:
            data = unwrapVariant(index.data(QtCore.Qt.EditRole), None)
            
            # map the data to python
            if type(data) in (QtCore.QDate, QtCore.QDateTime, QtCore.QTime):
                data = data.toPython()
            
            # render a standard date format
            if type(data) == datetime.date:
                text = data.strftime(self.dateFormat())
            
            # render a standard datetime format
            elif type(data) == datetime.time:
                text = data.strftime(self.timeFormat())
            
            # render a standard datetime format
            elif type(data) == datetime.datetime:
                text = data.strftime(self.datetimeFormat())
            
            # draw standard text
            else:
                text = unwrapVariant(index.data(QtCore.Qt.DisplayRole), '')
        
        # display hint information
        if not text:
            hint = unwrapVariant(index.data(XTreeWidgetItem.HintRole))
            if hint:
                text = hint
                fg = QtGui.QBrush(palette.color(palette.Disabled, palette.Text))
        
        opt.displayAlignment = QtCore.Qt.Alignment(item.textAlignment(index.column()))
        if not opt.displayAlignment & (QtCore.Qt.AlignVCenter | \
                                       QtCore.Qt.AlignTop | QtCore.Qt.AlignBottom):
            opt.displayAlignment |= QtCore.Qt.AlignVCenter
        
        if decorationRect:
            x = decorationRect.right() + 5
        elif checkRect:
            x = checkRect.right() + 5
        else:
            x = 5
        
        w = rect_w - x - 5
        h = rect_h
        
        displayRect = QtCore.QRect(x, 0, w, h)
        
        # create the background rect
        backgroundRect = QtCore.QRect(0, 0, opt.rect.width(), opt.rect.height())
        
        # draw the item
        self.drawBackground(painter, opt, backgroundRect, bg)
        
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.setPen(fg.color())
        
        self.drawCheck(painter, opt, checkRect, checkState)
        self.drawDecoration( painter, opt, decorationRect, pixmap)
        self.drawOverlay(painter, opt, overlayRect, overlay)
        self.drawDisplay(painter, opt, displayRect, text)
        self.drawGrid(painter, opt, backgroundRect, index)
        
        painter.restore()
    
    def setBackground(self, column, brush):
        """
        Sets the default item foreground brush.
        
        :param      column | <int>
                    brush  | <QtGui.QBrush> || None
        """
        if brush:
            self._background[column] = QtGui.QBrush(brush)
        elif column in self._background:
            self._background.pop(column)
    
    def setCheckOffMap( self, pixmap ):
        """
        Sets the pixmap to be used when rendering a check state in the \
        off state.
        
        :param      pixmap | <QtGui.QPixmap> || <str> || None
        """
        self._checkOffMap = QtGui.QPixmap(pixmap)
    
    def setCheckOnMap( self, pixmap ):
        """
        Sets the pixmap to be used when rendering a check state in the \
        on state.
        
        :param      pixmap | <QtGui.QPixmap> || <str> || None
        """
        self._checkOnMap = QtGui.QPixmap(pixmap)
    
    def setCheckPartialMap( self, pixmap ):
        """
        Sets the pixmap to be used when rendering a check state in the \
        partial state.
        
        :param      pixmap | <QtGui.QPixmap> || <str> || None
        """
        self._checkPartialMap = QtGui.QPixmap(pixmap)
    
    def setDateFormat(self, format):
        """
        Sets the date format for this delegate.
        
        :param      format | <str>
        """
        self._dateFormat = nativestring(format)
    
    def setDatetimeFormat(self, format):
        """
        Sets the datetime format for this delegate.
        
        :param      format | <str>
        """
        self._datetimeFormat = format
    
    def setDisplayMapper( self, column, mapper ):
        """
        Sets the display mapper for this instance.
        
        :param      column | <int>
                    mapper | <callable>
        """
        self._displayMappers[column] = mapper
    
    def setExtendsTree( self, state ):
        """
        Set whether or not this delegate should render its row line through \
        the tree area.
        
        :return     <state>
        """
        self._extendsTree = state
    
    def setGridPen( self, gridPen ):
        """
        Sets the pen that will be used when drawing the grid lines.
        
        :param      gridPen | <QtGui.QPen> || <QtGui.QColor>
        """
        self._gridPen = QtGui.QPen(gridPen)
    
    def setForeground(self, column, brush):
        """
        Sets the default item foreground brush.
        
        :param      brush | <QtGui.QBrush> || None
        """
        if brush:
            self._foreground[column] = QtGui.QBrush(brush)
        elif column in self._background:
            self._foreground.pop(column)
    
    def setShowGrid( self, state ):
        """
        Sets whether or not this delegate should draw its grid lines.
        
        :param      state | <bool>
        """
        self._showGrid = state
    
    def setShowGridColumns( self, state ):
        """
        Sets whether or not columns should be rendered when drawing the grid.
        
        :param      state | <bool>
        """
        self._showGridColumns = state
    
    def setShowGridRows( self, state ):
        """
        Sets whether or not the grid rows should be rendered when drawing the \
        grid.
        
        :param      state | <bool>
        """
        self._showGridRows = state
    
    def setShowRichText( self, state ):
        """
        Sets whether or not the delegate should render rich text information \
        as HTML when drawing the contents of the item.
        
        :param      state | <bool>
        """
        self._showRichText = state
    
    def setShowHighlights(self, state):
        """
        Sets whether or not the highlights on this tree should be shown.  When
        off, the selected items in the tree will not look any different from
        normal.
        
        :param      state | <bool>
        """
        self._showHighlights = state
    
    def setTimeFormat(self, format):
        """
        Sets the time format for this delegate.
        
        :param      format | <str>
        """
        self._timeFormat = format
       
    def setUseCheckMaps( self, state ):
        """
        Sets whether or not this delegate should render checked states using \
        the assigned pixmaps or not.
        
        :param      state | <bool>
        """
        self._useCheckMaps = state
    
    def showGrid( self ):
        """
        Returns whether or not this delegate should draw its grid lines.
        
        :return     <bool>
        """
        return self._showGrid
    
    def showGridColumns( self ):
        """
        Returns whether or not this delegate should draw columns when \
        rendering the grid.
        
        :return     <bool>
        """
        return self._showGridColumns
    
    def showGridRows( self ):
        """
        Returns whether or not this delegate should draw rows when rendering \
        the grid.
        
        :return     <bool>
        """
        return self._showGridRows
    
    def showHighlights(self):
        """
        Returns whether or not this tree widget should show its highlights.
        
        :return     <bool>
        """
        return self._showHighlights
    
    def showRichText( self ):
        """
        Returns whether or not the tree is holding richtext information and \
        should render HTML when drawing the data.
        
        :return     <bool>
        """
        return self._showRichText
    
    def sizeHint(self, option, index):
        """
        Returns the size hint for the inputed index.
        
        :param      option  | <QStyleOptionViewItem>
                    index   | <QModelIndex>
        
        :return     <QtCore.QSize>
        """
        size = super(XTreeWidgetDelegate, self).sizeHint(option, index)
        
        tree = self.parent()
        item = tree.itemFromIndex(index)
        
        try:
            fixed_height = item.fixedHeight()
        except:
            fixed_height = 0
        
        if fixed_height:
            size.setHeight(fixed_height)
        
        return size
    
    def timeFormat(self):
        """
        Returns the time format for this delegate.
        
        :return     <str>
        """
        return self._timeFormat
    
    def useCheckMaps( self ):
        """
        Returns whether or not this delegate should render check maps using \
        the assigned check maps.
        
        :return     <bool>
        """
        return self._useCheckMaps
    