#!/usr/bin/python

""" Defines a generic widget to handle popup controls. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2012, Projex Software'
__license__         = 'LGPL'

# maintenance information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

#------------------------------------------------------------------------------

import weakref

from projexui.qt import Signal, Slot
from projexui.qt.QtCore   import QSize,\
                                 Qt,\
                                 QPropertyAnimation
                           
from projexui.qt.QtGui    import QAbstractButton,\
                                 QBitmap,\
                                 QColor,\
                                 QCursor,\
                                 QHBoxLayout,\
                                 QIcon,\
                                 QPainterPath,\
                                 QPen,\
                                 QScrollArea,\
                                 QSizeGrip,\
                                 QVBoxLayout,\
                                 QToolButton,\
                                 QWidget,\
                                 QCursor,\
                                 QPalette,\
                                 QSizePolicy,\
                                 QDialogButtonBox,\
                                 QLabel,\
                                 QApplication,\
                                 QGraphicsDropShadowEffect,\
                                 QAbstractButton

from xqt import QtCore, QtGui

from projexui.xpainter import XPainter
from projex.enum import enum
from projex.decorators import deprecatedmethod

import projexui.resources

class XPopupWidget(QWidget):
    """ """
    Direction = enum('North', 'South', 'East', 'West')
    Mode      = enum('Popup', 'Dialog', 'ToolTip')
    Anchor    = enum('TopLeft',
                     'TopCenter',
                     'TopRight',
                     'LeftTop',
                     'LeftCenter',
                     'LeftBottom',
                     'RightTop',
                     'RightCenter',
                     'RightBottom',
                     'BottomLeft',
                     'BottomCenter',
                     'BottomRight')
    
    aboutToShow     = Signal()
    accepted        = Signal()
    closed          = Signal()
    rejected        = Signal()
    resetRequested  = Signal()
    shown           = Signal()
    buttonClicked   = Signal(QAbstractButton)
    
    def __init__(self, parent=None, buttons=None):
        super(XPopupWidget, self).__init__(parent)
        
        # define custom properties
        self._anchor                = XPopupWidget.Anchor.TopCenter
        self._autoCalculateAnchor   = False
        self._autoCloseOnAccept     = True
        self._autoCloseOnReject     = True
        self._autoCloseOnFocusOut   = False
        self._autoDefault           = True
        self._first                 = True
        self._animated              = False
        self._currentMode           = None
        self._positionLinkedTo      = []
        self._possibleAnchors       = XPopupWidget.Anchor.all()
        
        # define controls
        self._result        = 0
        self._resizable     = True
        self._popupPadding  = 10
        self._titleBarVisible = True
        self._buttonBoxVisible = True
        self._dialogButton  = QToolButton(self)
        self._closeButton   = QToolButton(self)
        self._scrollArea    = QScrollArea(self)
        self._sizeGrip      = QSizeGrip(self)
        self._sizeGrip.setFixedWidth(12)
        self._sizeGrip.setFixedHeight(12)
        
        self._leftSizeGrip  = QSizeGrip(self)
        self._leftSizeGrip.setFixedWidth(12)
        self._leftSizeGrip.setFixedHeight(12)
        
        if buttons is None:
            buttons = QDialogButtonBox.NoButton
        
        self._buttonBox     = QDialogButtonBox(buttons, Qt.Horizontal, self)
        self._buttonBox.setContentsMargins(3, 0, 3, 9)
        
        self._scrollArea.setWidgetResizable(True)
        self._scrollArea.setFrameShape(QScrollArea.NoFrame)
        self._scrollArea.setSizePolicy(QSizePolicy.Expanding,
                                       QSizePolicy.Expanding)
        
        palette = self.palette()
        self._scrollArea.setPalette(palette)
        
        self._dialogButton.setToolTip('Popout to Dialog')
        self._closeButton.setToolTip('Close Popup')
        
        for btn in (self._dialogButton, self._closeButton):
            btn.setAutoRaise(True)
            btn.setIconSize(QSize(14, 14))
            btn.setMaximumSize(16, 16)
        
        # setup the icons
        icon = QIcon(projexui.resources.find('img/dialog.png'))
        self._dialogButton.setIcon(icon)
        
        icon = QIcon(projexui.resources.find('img/close.png'))
        self._closeButton.setIcon(icon)
        
        # define the ui
        hlayout = QHBoxLayout()
        hlayout.setSpacing(0)
        hlayout.addStretch(1)
        hlayout.addWidget(self._dialogButton)
        hlayout.addWidget(self._closeButton)
        hlayout.setContentsMargins(0, 0, 0, 0)
        
        hlayout2 = QHBoxLayout()
        hlayout2.addWidget(self._buttonBox)
        hlayout2.setContentsMargins(0, 0, 3, 0)
        
        vlayout = QVBoxLayout()
        vlayout.addLayout(hlayout)
        vlayout.addWidget(self._scrollArea)
        vlayout.addLayout(hlayout2)
        vlayout.setContentsMargins(3, 2, 3, 2)
        vlayout.setSpacing(0)
        
        self.setLayout(vlayout)
        self.setPositionLinkedTo(parent)
        
        # set default properties
        self.setAutoFillBackground(True)
        self.setBackgroundRole(QPalette.Window)
        self.setWindowTitle('Popup')
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCurrentMode(XPopupWidget.Mode.Popup)
        
        # create connections
        self._dialogButton.clicked.connect(self.setDialogMode)
        self._closeButton.clicked.connect(self.reject)
        self._buttonBox.accepted.connect(self.accept)
        self._buttonBox.rejected.connect(self.reject)
        self._buttonBox.clicked.connect(self.handleButtonClick)
    
    def addButton(self, button, role=QDialogButtonBox.ActionRole):
        """
        Adds a custom button to the button box for this popup widget.
        
        :param      button | <QAbstractButton> || <str>
        
        :return     <button> || None (based on if a button or string was given)
        """
        return self._buttonBox.addButton(button, role)
    
    def adjustContentsMargins( self ):
        """
        Adjusts the contents for this widget based on the anchor and \
        mode.
        """
        anchor = self.anchor()
        mode   = self.currentMode()
        
        # margins for a dialog
        if ( mode == XPopupWidget.Mode.Dialog ):
            self.setContentsMargins(0, 0, 0, 0)
        
        # margins for a top anchor point
        elif ( anchor & (XPopupWidget.Anchor.TopLeft |
                         XPopupWidget.Anchor.TopCenter |
                         XPopupWidget.Anchor.TopRight) ):
            self.setContentsMargins(0, self.popupPadding() + 5, 0, 0)
        
        # margins for a bottom anchor point
        elif ( anchor & (XPopupWidget.Anchor.BottomLeft |
                         XPopupWidget.Anchor.BottomCenter |
                         XPopupWidget.Anchor.BottomRight) ):
            self.setContentsMargins(0, 0, 0, self.popupPadding())
        
        # margins for a left anchor point
        elif ( anchor & (XPopupWidget.Anchor.LeftTop |
                         XPopupWidget.Anchor.LeftCenter |
                         XPopupWidget.Anchor.LeftBottom) ):
            self.setContentsMargins(self.popupPadding(), 0, 0, 0)
        
        # margins for a right anchor point
        else:
            self.setContentsMargins(0, 0, self.popupPadding(), 0)
        
        self.adjustMask()
    
    def adjustMask(self):
        """
        Updates the alpha mask for this popup widget.
        """
        if self.currentMode() == XPopupWidget.Mode.Dialog:
            self.clearMask()
            return
        
        path = self.borderPath()
        bitmap = QBitmap(self.width(), self.height())
        bitmap.fill(QColor('white'))
        
        with XPainter(bitmap) as painter:
            painter.setRenderHint(XPainter.Antialiasing)
            pen = QPen(QColor('black'))
            pen.setWidthF(0.75)
            painter.setPen(pen)
            painter.setBrush(QColor('black'))
            painter.drawPath(path)
        
        self.setMask(bitmap)
    
    def adjustSize(self):
        """
        Adjusts the size of this popup to best fit the new widget size.
        """
        widget = self.centralWidget()
        if widget is None:
            super(XPopupWidget, self).adjustSize()
            return
        
        widget.adjustSize()
        hint = widget.minimumSizeHint()
        size = widget.minimumSize()
        
        width  = max(size.width(),  hint.width())
        height = max(size.height(), hint.height())
        
        width += 20
        height += 20
        
        if self._buttonBoxVisible:
            height += self.buttonBox().height() + 10
            
        if self._titleBarVisible:
            height += max(self._dialogButton.height(),
                          self._closeButton.height()) + 10
        
        curr_w = self.width()
        curr_h = self.height()
        
        # determine if we need to move based on our anchor
        anchor = self.anchor()
        if anchor & (self.Anchor.LeftBottom | self.Anchor.RightBottom | \
                       self.Anchor.BottomLeft | self.Anchor.BottomCenter | \
                       self.Anchor.BottomRight):
            delta_y = height - curr_h
        
        elif anchor & (self.Anchor.LeftCenter | self.Anchor.RightCenter):
            delta_y = (height - curr_h) / 2
        
        else:
            delta_y = 0
        
        if anchor & (self.Anchor.RightTop | self.Anchor.RightCenter | \
                       self.Anchor.RightTop | self.Anchor.TopRight):
            delta_x = width - curr_w
        
        elif anchor & (self.Anchor.TopCenter | self.Anchor.BottomCenter):
            delta_x = (width - curr_w) / 2
        
        else:
            delta_x = 0
        
        self.setMinimumSize(width, height)
        self.resize(width, height)
        
        pos = self.pos()
        pos.setX(pos.x() - delta_x)
        pos.setY(pos.y() - delta_y)
        
        self.move(pos)
    
    @Slot()
    def accept(self):
        """
        Emits the accepted signal and closes the popup.
        """
        self._result = 1
        
        if not self.signalsBlocked():
            self.accepted.emit()
        
        if self.autoCloseOnAccept():
            self.close()
    
    def anchor( self ):
        """
        Returns the anchor point for this popup widget.
        
        :return     <XPopupWidget.Anchor>
        """
        return self._anchor
    
    def autoCalculateAnchor( self ):
        """
        Returns whether or not this popup should calculate the anchor point
        on popup based on the parent widget and the popup point.
        
        :return     <bool>
        """
        return self._autoCalculateAnchor
    
    def autoCloseOnAccept( self ):
        """
        Returns whether or not this popup widget manages its own close on accept
        behavior.
        
        :return     <bool>
        """
        return self._autoCloseOnAccept
    
    def autoCloseOnReject( self ):
        """
        Returns whether or not this popup widget manages its own close on reject
        behavior.
        
        :return     <bool>
        """
        return self._autoCloseOnReject
    
    def autoCloseOnFocusOut(self):
        """
        Returns whether or not this popup widget should auto-close when the user
        clicks off the view.
        
        :return     <bool>
        """
        return self._autoCloseOnFocusOut
    
    def autoDefault(self):
        """
        Returns whether or not clicking enter should default to the accept key.
        
        :return     <bool>
        """
        return self._autoDefault
    
    def borderPath(self):
        """
        Returns the border path that will be drawn for this widget.
        
        :return     <QPainterPath>
        """
        
        path = QPainterPath()
        
        x = 1
        y = 1
        w = self.width() - 2
        h = self.height() - 2
        pad = self.popupPadding()
        anchor = self.anchor()
        
        # create a path for a top-center based popup
        if anchor == XPopupWidget.Anchor.TopCenter:
            path.moveTo(x, y + pad)
            path.lineTo(x + ((w/2) - pad), y + pad)
            path.lineTo(x + (w/2), y)
            path.lineTo(x + ((w/2) + pad), y + pad)
            path.lineTo(x + w, y + pad)
            path.lineTo(x + w, y + h)
            path.lineTo(x, y + h)
            path.lineTo(x, y + pad)
        
        # create a path for a top-left based popup
        elif anchor == XPopupWidget.Anchor.TopLeft:
            path.moveTo(x, y + pad)
            path.lineTo(x + pad, y)
            path.lineTo(x + 2 * pad, y + pad)
            path.lineTo(x + w, y + pad)
            path.lineTo(x + w, y + h)
            path.lineTo(x, y + h)
            path.lineTo(x, y + pad)
        
        # create a path for a top-right based popup
        elif anchor == XPopupWidget.Anchor.TopRight:
            path.moveTo(x, y + pad)
            path.lineTo(x + w - 2 * pad, y + pad)
            path.lineTo(x + w - pad, y)
            path.lineTo(x + w, y + pad)
            path.lineTo(x + w, y + h)
            path.lineTo(x, y + h)
            path.lineTo(x, y + pad)
        
        # create a path for a bottom-left based popup
        elif anchor == XPopupWidget.Anchor.BottomLeft:
            path.moveTo(x, y)
            path.lineTo(x + w, y)
            path.lineTo(x + w, y + h - pad)
            path.lineTo(x + 2 * pad, y + h - pad)
            path.lineTo(x + pad, y + h)
            path.lineTo(x, y + h - pad)
            path.lineTo(x, y)
        
        # create a path for a south based popup
        elif anchor == XPopupWidget.Anchor.BottomCenter:
            path.moveTo(x, y)
            path.lineTo(x + w, y)
            path.lineTo(x + w, y + h - pad)
            path.lineTo(x + ((w/2) + pad), y + h - pad)
            path.lineTo(x + (w/2), y + h)
            path.lineTo(x + ((w/2) - pad), y + h - pad)
            path.lineTo(x, y + h - pad)
            path.lineTo(x, y)
        
        # create a path for a bottom-right based popup
        elif anchor == XPopupWidget.Anchor.BottomRight:
            path.moveTo(x, y)
            path.lineTo(x + w, y)
            path.lineTo(x + w, y + h - pad)
            path.lineTo(x + w - pad, y + h)
            path.lineTo(x + w - 2 * pad, y + h - pad)
            path.lineTo(x, y + h - pad)
            path.lineTo(x, y)
        
        # create a path for a right-top based popup
        elif anchor == XPopupWidget.Anchor.RightTop:
            path.moveTo(x, y)
            path.lineTo(x + w - pad, y)
            path.lineTo(x + w, y + pad)
            path.lineTo(x + w - pad, y + 2 * pad)
            path.lineTo(x + w - pad, y + h)
            path.lineTo(x, y + h)
            path.lineTo(x, y)
        
        # create a path for a right-center based popup
        elif anchor == XPopupWidget.Anchor.RightCenter:
            path.moveTo(x, y)
            path.lineTo(x + w - pad, y)
            path.lineTo(x + w - pad, y + ((h/2) - pad))
            path.lineTo(x + w, y + (h/2))
            path.lineTo(x + w - pad, y + ((h/2) + pad))
            path.lineTo(x + w - pad, y + h)
            path.lineTo(x, y + h)
            path.lineTo(x, y)
        
        # create a path for a right-bottom based popup
        elif anchor == XPopupWidget.Anchor.RightBottom:
            path.moveTo(x, y)
            path.lineTo(x + w - pad, y)
            path.lineTo(x + w - pad, y + h - 2 * pad)
            path.lineTo(x + w, y + h - pad)
            path.lineTo(x + w - pad, y + h)
            path.lineTo(x, y + h)
            path.lineTo(x, y)
        
        # create a path for a left-top based popup
        elif anchor == XPopupWidget.Anchor.LeftTop:
            path.moveTo(x + pad, y)
            path.lineTo(x + w, y)
            path.lineTo(x + w, y + h)
            path.lineTo(x + pad, y + h)
            path.lineTo(x + pad, y + 2 * pad)
            path.lineTo(x, y + pad)
            path.lineTo(x + pad, y)
        
        # create a path for an left-center based popup
        elif anchor == XPopupWidget.Anchor.LeftCenter:
            path.moveTo(x + pad, y)
            path.lineTo(x + w, y)
            path.lineTo(x + w, y + h)
            path.lineTo(x + pad, y + h)
            path.lineTo(x + pad, y + ((h/2) + pad))
            path.lineTo(x, y + (h/2))
            path.lineTo(x + pad, y + ((h/2) - pad))
            path.lineTo(x + pad, y)
        
        # create a path for a left-bottom based popup
        elif anchor == XPopupWidget.Anchor.LeftBottom:
            path.moveTo(x + pad, y)
            path.lineTo(x + w, y)
            path.lineTo(x + w, y + h)
            path.lineTo(x + pad, y + h)
            path.lineTo(x, y + h - pad)
            path.lineTo(x + pad, y + h - 2 * pad)
            path.lineTo(x + pad, y)
        
        return path
    
    def buttonBox( self ):
        """
        Returns the button box that is used to control this popup widget.
        
        :return     <QDialogButtonBox>
        """
        return self._buttonBox
    
    def centralWidget( self ):
        """
        Returns the central widget that is being used by this popup.
        
        :return     <QWidget>
        """
        return self._scrollArea.widget()
    
    def close(self):
        """
        Closes the popup widget and central widget.
        """
        widget = self.centralWidget()
        if widget and not widget.close():
            return
            
        super(XPopupWidget, self).close()
    
    def closeEvent(self, event):
        widget = self.centralWidget()
        if widget and not widget.close() and \
           self.currentMode() != XPopupWidget.Mode.ToolTip:
            event.ignore()
        else:
            super(XPopupWidget, self).closeEvent(event)
        
        self.closed.emit()
    
    def currentMode( self ):
        """
        Returns the current mode for this widget.
        
        :return     <XPopupWidget.Mode>
        """
        return self._currentMode
    
    @deprecatedmethod('XPopupWidget', 
                      'Direction is no longer used, use anchor instead')
    def direction( self ):
        """
        Returns the current direction parameter for this widget.
        
        :return     <XPopupWidget.Direction>
        """
        anchor = self.anchor()
        if ( anchor & (XPopupWidget.Anchor.TopLeft |
                       XPopupWidget.Anchor.TopCenter |
                       XPopupWidget.Anchor.TopRight) ):
            return XPopupWidget.Direction.North
        
        elif ( anchor & (XPopupWidget.Anchor.BottomLeft |
                         XPopupWidget.Anchor.BottomCenter |
                         XPopupWidget.Anchor.BottomRight) ):
            return XPopupWidget.Direction.South
        
        elif ( anchor & (XPopupWidget.Anchor.LeftTop |
                         XPopupWidget.Anchor.LeftCenter |
                         XPopupWidget.Anchor.LeftBottom) ):
            return XPopupWidget.Direction.East
        
        else:
            return XPopupWidget.Direction.West
    
    def exec_(self, pos=None):
        self._result = 0
        self.setWindowModality(Qt.ApplicationModal)
        self.popup(pos)
        while self.isVisible():
            QApplication.processEvents()
        
        return self.result()
    
    def eventFilter(self, object, event):
        """
        Processes when the window is moving to update the position for the
        popup if in popup mode.
        
        :param      object | <QObject>
                    event  | <QEvent>
        """
        if not self.isVisible():
            return False
        
        links = self.positionLinkedTo()
        is_dialog = self.currentMode() == self.Mode.Dialog
        if object not in links:
            return False
        
        if event.type() == event.Close:
            self.close()
            return False
        
        if event.type() == event.Hide and not is_dialog:
            self.hide()
            return False
        
        if event.type() == event.Move and not is_dialog:
            deltaPos = event.pos() - event.oldPos()
            self.move(self.pos() + deltaPos)
            return False
        
        if self.currentMode() != self.Mode.ToolTip:
            return False
        
        if event.type() == event.Leave:
            pos = object.mapFromGlobal(QCursor.pos())
            if (not object.rect().contains(pos)):
                self.close()
                event.accept()
                return True
        
        if event.type() in (event.MouseButtonPress, event.MouseButtonDblClick):
            self.close()
            event.accept()
            return True
        
        return False
    
    @Slot(QAbstractButton)
    def handleButtonClick(self, button):
        """
        Handles the button click for this widget.  If the Reset button was
        clicked, then the resetRequested signal will be emitted.  All buttons
        will emit the buttonClicked signal.
        
        :param      button | <QAbstractButton>
        """
        if ( self.signalsBlocked() ):
            return
        
        if ( button == self._buttonBox.button(QDialogButtonBox.Reset) ):
            self.resetRequested.emit()
        
        self.buttonClicked.emit(button)
    
    def isAnimated(self):
        """
        Returns whether or not the popup widget should animate its opacity
        when it is shown.
        
        :return     <bool>
        """
        return self._animated

    def isPossibleAnchor(self, anchor):
        return bool(anchor & self._possibleAnchors)

    def isResizable(self):
        """
        Returns if this popup is resizable or not.
        
        :return     <bool>
        """
        return self._resizable
    
    def keyPressEvent( self, event ):
        """
        Looks for the Esc key to close the popup.
        
        :param      event | <QKeyEvent>
        """
        if ( event.key() == Qt.Key_Escape ):
            self.reject()
            event.accept()
            return
        
        elif ( event.key() in (Qt.Key_Return, Qt.Key_Enter) ):
            if self._autoDefault:
                self.accept()
                event.accept()
            return
        
        super(XPopupWidget, self).keyPressEvent(event)
    
    def mapAnchorFrom(self, widget, point):
        """
        Returns the anchor point that best fits within the given widget from
        the inputed global position.
        
        :param      widget      | <QWidget>
                    point       | <QPoint>
        
        :return     <XPopupWidget.Anchor>
        """
        screen_geom = QtGui.QDesktopWidget(self).screenGeometry()

        # calculate the end rect for each position
        Anchor = self.Anchor
        w = self.width()
        h = self.height()

        possible_rects = {
            # top anchors
            Anchor.TopLeft: QtCore.QRect(point.x(), point.y(), w, h),
            Anchor.TopCenter: QtCore.QRect(point.x() - w / 2, point.y(), w, h),
            Anchor.TopRight: QtCore.QRect(point.x() - w, point.y(), w, h),

            # left anchors
            Anchor.LeftTop: QtCore.QRect(point.x(), point.y(), w, h),
            Anchor.LeftCenter: QtCore.QRect(point.x(), point.y() - h / 2, w, h),
            Anchor.LeftBottom: QtCore.QRect(point.x(), point.y() - h, w, h),

            # bottom anchors
            Anchor.BottomLeft: QtCore.QRect(point.x(), point.y() - h, w, h),
            Anchor.BottomCenter: QtCore.QRect(point.x() - w / 2, point.y() - h, w, h),
            Anchor.BottomRight: QtCore.QRect(point.x() - w, point.y() - h, w, h),

            # right anchors
            Anchor.RightTop: QtCore.QRect(point.x() - self.width(), point.y(), w, h),
            Anchor.RightCenter: QtCore.QRect(point.x() - self.width(), point.y() - h / 2, w, h),
            Anchor.RightBottom: QtCore.QRect(point.x() - self.width(), point.y() - h, w ,h)
        }

        for anchor in (Anchor.TopCenter,
                       Anchor.BottomCenter,
                       Anchor.LeftCenter,
                       Anchor.RightCenter,
                       Anchor.TopLeft,
                       Anchor.LeftTop,
                       Anchor.BottomLeft,
                       Anchor.LeftBottom,
                       Anchor.TopRight,
                       Anchor.RightTop,
                       Anchor.BottomRight,
                       Anchor.RightBottom):

            if not self.isPossibleAnchor(anchor):
                continue

            rect = possible_rects[anchor]
            if screen_geom.contains(rect):
                return anchor

        return self.anchor()

    def popup(self, pos=None):
        """
        Pops up this widget at the inputed position.  The inputed point should \
        be in global space.
        
        :param      pos | <QPoint>
        
        :return     <bool> success
        """
        if self._first and self.centralWidget() is not None:
            self.adjustSize()
            self._first = False
        
        if not self.signalsBlocked():
            self.aboutToShow.emit()
        
        if not pos:
            pos = QCursor.pos()
        
        if self.currentMode() == XPopupWidget.Mode.Dialog and \
             self.isVisible():
            return False
        
        elif self.currentMode() == XPopupWidget.Mode.Dialog:
            self.setPopupMode()
        
        # auto-calculate the point
        if self.autoCalculateAnchor():
            self.setAnchor(self.mapAnchorFrom(self.parent(), pos))
        
        pad = self.popupPadding()
        
        # determine where to move based on the anchor
        anchor = self.anchor()
        
        # MODIFY X POSITION
        # align x-left
        if ( anchor & (XPopupWidget.Anchor.TopLeft |
                       XPopupWidget.Anchor.BottomLeft) ):
            pos.setX(pos.x() - pad)
        
        # align x-center
        elif ( anchor & (XPopupWidget.Anchor.TopCenter |
                         XPopupWidget.Anchor.BottomCenter) ):
            pos.setX(pos.x() - self.width() / 2)
        
        # align x-right
        elif ( anchor & (XPopupWidget.Anchor.TopRight |
                         XPopupWidget.Anchor.BottomRight) ):
            pos.setX(pos.x() - self.width() + pad)
        
        # align x-padded
        elif ( anchor & (XPopupWidget.Anchor.RightTop |
                         XPopupWidget.Anchor.RightCenter |
                         XPopupWidget.Anchor.RightBottom) ):
            pos.setX(pos.x() - self.width())
        
        # MODIFY Y POSITION
        # align y-top
        if ( anchor & (XPopupWidget.Anchor.LeftTop |
                       XPopupWidget.Anchor.RightTop) ):
            pos.setY(pos.y() - pad)
        
        # align y-center
        elif ( anchor & (XPopupWidget.Anchor.LeftCenter |
                         XPopupWidget.Anchor.RightCenter) ):
            pos.setY(pos.y() - self.height() / 2)
        
        # align y-bottom
        elif ( anchor & (XPopupWidget.Anchor.LeftBottom |
                         XPopupWidget.Anchor.RightBottom) ):
            pos.setY(pos.y() - self.height() + pad)
        
        # align y-padded
        elif ( anchor & (XPopupWidget.Anchor.BottomLeft |
                         XPopupWidget.Anchor.BottomCenter |
                         XPopupWidget.Anchor.BottomRight) ):
            pos.setY(pos.y() - self.height())
        
        self.adjustMask()
        self.move(pos)
        self.update()
        self.setUpdatesEnabled(True)
        
        if self.isAnimated():
            anim = QPropertyAnimation(self, 'windowOpacity')
            anim.setParent(self)
            anim.setStartValue(0.0)
            anim.setEndValue(self.windowOpacity())
            anim.setDuration(500)
            anim.finished.connect(anim.deleteLater)
            self.setWindowOpacity(0.0)
        else:
            anim = None
            
        
        self.show()
        
        if self.currentMode() != XPopupWidget.Mode.ToolTip:
            self.activateWindow()
            
            widget = self.centralWidget()
            if widget:
                self.centralWidget().setFocus()
            
        
        if anim:
            anim.start()
        
        if not self.signalsBlocked():
            self.shown.emit()
        
        return True
        
    def paintEvent(self, event):
        """
        Overloads the paint event to handle painting pointers for the popup \
        mode.
        
        :param      event | <QPaintEvent>
        """
        # use the base technique for the dialog mode
        if self.currentMode() == XPopupWidget.Mode.Dialog:
            super(XPopupWidget, self).paintEvent(event)
            return
        
        # setup the coloring options
        palette = self.palette()
        
        with XPainter(self) as painter:
            pen = QPen(palette.color(palette.Window).darker(130))
            pen.setWidthF(1.75)
            painter.setPen(pen)
            painter.setRenderHint(painter.Antialiasing)
            painter.setBrush(palette.color(palette.Window))
            painter.drawPath(self.borderPath())
    
    def popupPadding(self):
        """
        Returns the amount of pixels to pad the popup arrow for this widget.
        
        :return     <int>
        """
        return self._popupPadding

    def possibleAnchors(self):
        return self._possibleAnchors

    def positionLinkedTo(self):
        """
        Returns the widget that this popup is linked to for positional changes.
        
        :return     [<QWidget>, ..]
        """
        return self._positionLinkedTo
    
    @Slot()
    def reject(self):
        """
        Emits the accepted signal and closes the popup.
        """
        self._result = 0
        if not self.signalsBlocked():
            self.rejected.emit()
        
        if self.autoCloseOnReject():
            self.close()
    
    def result(self):
        return self._result
    
    def resizeEvent(self, event):
        """
        Resizes this widget and updates the mask.
        
        :param      event | <QResizeEvent>
        """
        self.setUpdatesEnabled(False)
        super(XPopupWidget, self).resizeEvent(event)
        
        self.adjustMask()
        self.setUpdatesEnabled(True)
        
        x = self.width() - self._sizeGrip.width()
        y = self.height() - self._sizeGrip.height()
        
        self._leftSizeGrip.move(0, y)
        self._sizeGrip.move(x, y)
    
    def scrollArea(self):
        """
        Returns the scroll area widget for this popup.
        
        :return     <QScrollArea>
        """
        return self._scrollArea
    
    def setAnimated(self, state):
        """
        Sets whether or not the popup widget should animate its opacity
        when it is shown.
        
        :param      state | <bool>
        """
        self._animated = state
        self.setAttribute(Qt.WA_TranslucentBackground, state)
    
    def setAutoCloseOnAccept( self, state ):
        """
        Sets whether or not the popup handles closing for accepting states.
        
        :param      state | <bool>
        """
        self._autoCloseOnAccept = state
    
    def setAutoCloseOnReject( self, state ):
        """
        Sets whether or not the popup handles closing for rejecting states.
        
        :param      state | <bool>
        """
        self._autoCloseOnReject = state
    
    def setAutoDefault(self, state):
        """
        Sets whether or not the buttons should respond to defaulting options
        when the user is interacting with it.
        
        :param      state | <bool>
        """
        self._autoDefault = state
        for button in self.buttonBox().buttons():
            button.setAutoDefault(state)
            button.setDefault(state)
    
    def setAnchor( self, anchor ):
        """
        Sets the anchor position for this popup widget to the inputed point.
        
        :param      anchor | <XPopupWidget.Anchor>
        """
        self._anchor = anchor
        self.adjustContentsMargins()
    
    def setAutoCalculateAnchor(self, state=True):
        """
        Sets whether or not this widget should auto-calculate the anchor point
        based on the parent position when the popup is triggered.
        
        :param      state | <bool>
        """
        self._autoCalculateAnchor = state
    
    def setAutoCloseOnFocusOut(self, state):
        """
        Sets whether or not this popup widget should auto-close when the user
        clicks off the view.
        
        :param     state | <bool>
        """
        self._autoCloseOnFocusOut = state
        self.updateModeSettings()
    
    def setCentralWidget( self, widget ):
        """
        Sets the central widget that will be used by this popup.
        
        :param      widget | <QWidget> || None
        """
        self._scrollArea.takeWidget()
        self._scrollArea.setWidget(widget)
        
        self.adjustSize()
    
    def setCurrentMode( self, mode ):
        """
        Sets the current mode for this dialog to the inputed mode.
        
        :param      mode | <XPopupWidget.Mode>
        """
        if ( self._currentMode == mode ):
            return
        
        self._currentMode = mode
        self.updateModeSettings()
    
    @Slot()
    def setDialogMode(self):
        """
        Sets the current mode value to Dialog.
        """
        self.setCurrentMode(XPopupWidget.Mode.Dialog)
    
    @deprecatedmethod('XPopupWidget',
                      'Direction is no longer used, use setAnchor instead')
    def setDirection( self, direction ):
        """
        Sets the direction for this widget to the inputed direction.
        
        :param      direction | <XPopupWidget.Direction>
        """
        if ( direction == XPopupWidget.Direction.North ):
            self.setAnchor(XPopupWidget.Anchor.TopCenter)
        
        elif ( direction == XPopupWidget.Direction.South ):
            self.setAnchor(XPopupWidget.Anchor.BottomCenter)
        
        elif ( direction == XPopupWidget.Direction.East ):
            self.setAnchor(XPopupWidget.Anchor.LeftCenter)
        
        else:
            self.setAnchor(XPopupWidget.Anchor.RightCenter)
    
    def setPalette(self, palette):
        """
        Sets the palette for this widget and the scroll area.
        
        :param      palette | <QPalette>
        """
        super(XPopupWidget, self).setPalette(palette)
        self._scrollArea.setPalette(palette)
    
    def setPopupMode( self ):
        """
        Sets the current mode value to Popup.
        """
        self.setCurrentMode(XPopupWidget.Mode.Popup)
    
    def setPopupPadding( self, padding ):
        """
        Sets the amount to pad the popup area when displaying this widget.
        
        :param      padding | <int>
        """
        self._popupPadding = padding
        self.adjustContentsMargins()

    def setPossibleAnchors(self, anchors):
        self._possibleAnchors = anchors

    def setPositionLinkedTo(self, widgets):
        """
        Sets the widget that this popup will be linked to for positional
        changes.
        
        :param      widgets | <QWidget> || [<QWidget>, ..]
        """
        if type(widgets) in (list, set, tuple):
            new_widgets = list(widgets)
        else:
            new_widgets = []
            widget = widgets
            while widget:
                widget.installEventFilter(self)
                new_widgets.append(widget)
                widget = widget.parent()
        
        self._positionLinkedTo = new_widgets
    
    def setResizable( self, state ):
        self._resizable = state
        self._sizeGrip.setVisible(state)
        self._leftSizeGrip.setVisible(state)
    
    def setShowButtonBox(self, state):
        self._buttonBoxVisible = state
        self.buttonBox().setVisible(state)
    
    def setShowTitleBar(self, state):
        self._titleBarVisible = state
        self._dialogButton.setVisible(state)
        self._closeButton.setVisible(state)
    
    def setToolTipMode(self):
        """
        Sets the mode for this popup widget to ToolTip
        """
        self.setCurrentMode(XPopupWidget.Mode.ToolTip)
    
    def setVisible(self, state):
        super(XPopupWidget, self).setVisible(state)
        widget = self.centralWidget()
        if widget:
            widget.setVisible(state)
    
    def timerEvent( self, event ):
        """
        When the timer finishes, hide the tooltip popup widget.
        
        :param      event | <QEvent>
        """
        if self.currentMode() == XPopupWidget.Mode.ToolTip:
            self.killTimer(event.timerId())
            event.accept()
            self.close()
        else:
            super(XPopupWidget, self).timerEvent(event)
        
    def updateModeSettings(self):
        mode = self.currentMode()
        is_visible = self.isVisible()
        
        # display as a floating dialog
        if mode == XPopupWidget.Mode.Dialog:
            self.setWindowFlags(Qt.Dialog | Qt.Tool)
            self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            self._closeButton.setVisible(False)
            self._dialogButton.setVisible(False)
        
        # display as a user tooltip
        elif mode == XPopupWidget.Mode.ToolTip:
            flags = Qt.Popup | Qt.FramelessWindowHint
            
            self.setWindowFlags(flags)
            self.setBackgroundRole(QPalette.Window)
            self.setAttribute(Qt.WA_TransparentForMouseEvents)
            self.setShowTitleBar(False)
            self.setShowButtonBox(False)
            self.setFocusPolicy(Qt.NoFocus)
            
            # hide the scrollbars
            policy = Qt.ScrollBarAlwaysOff
            self._scrollArea.setVerticalScrollBarPolicy(policy)
            self._scrollArea.setHorizontalScrollBarPolicy(policy)
        
        # display as a popup widget
        else:
            flags = Qt.Popup | Qt.FramelessWindowHint
            
            if not self.autoCloseOnFocusOut():
                flags |= Qt.Tool
            
            self.setWindowFlags(flags)
            self._closeButton.setVisible(self._titleBarVisible)
            self._dialogButton.setVisible(self._titleBarVisible)
            self.setBackgroundRole(QPalette.Window)
        
        self.adjustContentsMargins()
        
        if ( is_visible ):
            self.show()
    
    @staticmethod
    @deprecatedmethod('XPopupWidget',
                      'This method no longer has an effect as we are not '\
                      'storing references to the tooltip.')
    def hideToolTip(key = None):
        """
        Hides any existing tooltip popup widgets.
        
        :warning    This method is deprecated!
        """
        pass
    
    @staticmethod
    def showToolTip( text,
                     point      = None,
                     anchor     = None,
                     parent     = None,
                     background = None,
                     foreground = None,
                     key        = None,
                     seconds    = 5 ):
        """
        Displays a popup widget as a tooltip bubble.
        
        :param      text        | <str>
                    point       | <QPoint> || None
                    anchor      | <XPopupWidget.Mode.Anchor> || None
                    parent      | <QWidget> || None
                    background  | <QColor> || None
                    foreground  | <QColor> || None
                    key         | <str> || None
                    seconds     | <int>
        """
        if point is None:
            point = QCursor.pos()
            
        if parent is None:
            parent = QApplication.activeWindow()
        
        if anchor is None and parent is None:
            anchor = XPopupWidget.Anchor.TopCenter
        
        # create a new tooltip widget
        widget = XPopupWidget(parent)
        widget.setToolTipMode()
        widget.setResizable(False)
        
        # create the tooltip label
        label = QLabel(text, widget)
        label.setOpenExternalLinks(True)
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label.setMargin(3)
        label.setIndent(3)
        label.adjustSize()
    
        widget.setCentralWidget(label)
        
        # update the tip
        label.adjustSize()
        widget.adjustSize()
        
        palette = widget.palette()
        if not background:
            background = palette.color(palette.ToolTipBase)
        if not foreground:
            foreground = palette.color(palette.ToolTipText)
        
        palette.setColor(palette.Window,     QColor(background))
        palette.setColor(palette.WindowText, QColor(foreground))
        widget.setPalette(palette)
        widget.centralWidget().setPalette(palette)
        
        if anchor is None:
            widget.setAutoCalculateAnchor(True)
        else:
            widget.setAnchor(anchor)
        
        widget.setAutoCloseOnFocusOut(True)
        widget.setAttribute(Qt.WA_DeleteOnClose)
        widget.popup(point)
        widget.startTimer(1000 * seconds)
        
        return widget