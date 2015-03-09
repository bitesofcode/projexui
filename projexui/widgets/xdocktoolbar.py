#!/usr/bin python

""" Defines a dock toolbar for generating expanding toolbar icons. """

# define authorship information
__authors__     = ['Eric Hulser']
__author__      = ','.join(__authors__)
__credits__     = []
__copyright__   = 'Copyright (c) 2011, Projex Software'

# maintanence information
__maintainer__  = 'Projex Software'
__email__       = 'team@projexsoftware.com'

from projexui.qt import Signal
from projexui.qt.QtCore import QRect,\
                               Qt,\
                               QSize,\
                               QPoint,\
                               QParallelAnimationGroup,\
                               QEasingCurve,\
                               QTimer

from projexui.qt.QtGui import QWidget,\
                              QBoxLayout,\
                              QLabel,\
                              QGraphicsDropShadowEffect,\
                              QAction,\
                              QCursor,\
                              QColor,\
                              QLinearGradient,\
                              QPainterPath

from projex.xpainter import XPainter
from projexui.xanimation import XObjectAnimation
from projexui import resources
from projex.enum import enum

class XDockActionLabel(QLabel):
    entered = Signal()
    exited = Signal()
    
    def __init__(self, action, pixmapSize, parent=None):
        super(XDockActionLabel, self).__init__(parent)
        
        # define custom properties
        self._action = action
        self._pixmapSize = pixmapSize
        self._position = XDockToolbar.Position.South
        self._padding = 6
        
        # setup default properties
        self.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        self.setPixmapSize(pixmapSize)
        self.setMouseTracking(True)
    
    def action(self):
        """
        Returns the action linked with this label.
        
        :return     <QAction>
        """
        return self._action
    
    def mousePressEvent(self, event):
        """
        Handles when the user presses this label.
        
        :param      event | <QEvent>
        """
        if event.button() == Qt.LeftButton:
            self.parent().actionTriggered.emit(self.action())
            self.parent().setSelectedAction(self.action())
        elif event.button() == Qt.MidButton:
            self.parent().actionMiddleTriggered.emit(self.action())
        elif event.button() == Qt.RightButton:
            self.parent().actionMenuRequested.emit(self.action(),
                                                   self.mapToParent(event.pos()))
        
        event.accept()
    
    def padding(self):
        """
        Returns the padding value for this label.
        
        :return     <int>
        """
        return self._padding
    
    def pixmapSize(self):
        """
        Returns the size of the pixmap for this widget.
        
        :return     <QSize>
        """
        return self._pixmapSize
    
    def position(self):
        """
        Returns the position associated with this label.
        
        :return     <XDockToolbar.Position>
        """
        return self._position
    
    def setPadding(self, padding):
        """
        Sets the padding information for this label.
        
        :param      padding | <int>
        """
        self._padding = padding
    
    def setPixmapSize(self, size):
        """
        Sets the pixmap size for this label.
        
        :param      size | <QSize>
        """
        self._pixmapSize = size
        self.setPixmap(self.action().icon().pixmap(size))
        
        max_size = self.parent().maximumPixmapSize()
        
        if self.position() in (XDockToolbar.Position.North,
                               XDockToolbar.Position.South):
            self.setFixedWidth(size.width() + self.padding())
            self.setFixedHeight(max_size.height() + self.padding())
        else:
            self.setFixedWidth(max_size.width() + self.padding())
            self.setFixedHeight(size.height() + self.padding())
    
    def setPosition(self, position):
        """
        Adjusts this label to match the given position.
        
        :param      <XDockToolbar.Position>
        """
        self._position = position
        
        if position == XDockToolbar.Position.North:
            self.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        elif position == XDockToolbar.Position.East:
            self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        elif position == XDockToolbar.Position.South:
            self.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        elif position == XDockToolbar.Position.West:
            self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

#----------------------------------------------------------------------

class XDockToolbar(QWidget):
    Position = enum('North', 'South', 'East', 'West')
    
    actionTriggered = Signal(object)
    actionMiddleTriggered = Signal(object)
    actionMenuRequested = Signal(object, QPoint)
    currentActionChanged = Signal(object)
    actionHovered = Signal(object)
    
    def __init__(self, parent=None):
        super(XDockToolbar, self).__init__(parent)
        
        # defines the position for this widget
        self._currentAction = -1
        self._selectedAction = None
        self._padding = 8
        self._position = XDockToolbar.Position.South
        self._minimumPixmapSize = QSize(16, 16)
        self._maximumPixmapSize = QSize(48, 48)
        self._hoverTimer = QTimer(self)
        self._hoverTimer.setSingleShot(True)
        self._hoverTimer.setInterval(1000)
        self._actionHeld = False
        self._easingCurve = QEasingCurve(QEasingCurve.InOutQuad)
        self._duration = 200
        self._animating = False
        
        # install an event filter to update the location for this toolbar
        layout = QBoxLayout(QBoxLayout.LeftToRight)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        layout.addStretch(1)
        layout.addStretch(1)
        
        self.setLayout(layout)
        self.setContentsMargins(2, 2, 2, 2)
        self.setMouseTracking(True)
        parent.window().installEventFilter(self)
        parent.window().statusBar().installEventFilter(self)
        
        self._hoverTimer.timeout.connect(self.emitActionHovered)
    
    def __markAnimatingFinished(self):
        self._animating = False
    
    def actionAt(self, pos):
        """
        Returns the action at the given position.
        
        :param      pos | <QPoint>
        
        :return     <QAction> || None
        """
        child = self.childAt(pos)
        if child:
            return child.action()
        return None
    
    def actionHeld(self):
        """
        Returns whether or not the action will be held instead of closed on
        leaving.
        
        :return     <bool>
        """
        return self._actionHeld
    
    def actionLabels(self):
        """
        Returns the labels for this widget.
        
        :return     <XDockActionLabel>
        """
        l = self.layout()
        return [l.itemAt(i).widget() for i in range(1, l.count() - 1)]
    
    def addAction(self, action):
        """
        Adds the inputed action to this toolbar.
        
        :param      action | <QAction>
        """
        super(XDockToolbar, self).addAction(action)
        
        label = XDockActionLabel(action, self.minimumPixmapSize(), self)
        label.setPosition(self.position())
        
        layout = self.layout()
        layout.insertWidget(layout.count() - 1, label)
    
    def clear(self):
        """
        Clears out all the actions and items from this toolbar.
        """
        # clear the actions from this widget
        for act in self.actions():
            act.setParent(None)
            act.deleteLater()
        
        # clear the labels from this widget
        for lbl in self.actionLabels():
            lbl.close()
            lbl.deleteLater()
    
    def currentAction(self):
        """
        Returns the currently hovered/active action.
        
        :return     <QAction> || None
        """
        return self._currentAction
    
    def duration(self):
        """
        Returns the duration value for the animation of the icons.
        
        :return     <int>
        """
        return self._duration
    
    def easingCurve(self):
        """
        Returns the easing curve that will be used for the animation of
        animated icons for this dock bar.
        
        :return     <QEasingCurve>
        """
        return self._easingCurve
    
    def emitActionHovered(self):
        """
        Emits a signal when an action is hovered.
        """
        if not self.signalsBlocked():
            self.actionHovered.emit(self.currentAction())
    
    def eventFilter(self, object, event):
        """
        Filters the parent objects events to rebuild this toolbar when
        the widget resizes.
        
        :param      object | <QObject>
                    event | <QEvent>
        """
        if event.type() in (event.Move, event.Resize):
            if self.isVisible():
                self.rebuild()
            elif object.isVisible():
                self.setVisible(True)
        
        return False
    
    def holdAction(self):
        """
        Returns whether or not the action should be held instead of clearing
        on leave.
        
        :return     <bool>
        """
        self._actionHeld = True
    
    def labelForAction(self, action):
        """
        Returns the label that contains the inputed action.
        
        :return     <XDockActionLabel> || None
        """
        for label in self.actionLabels():
            if label.action() == action:
                return label
        return None
    
    def leaveEvent(self, event):
        """
        Clears the current action for this widget.
        
        :param      event | <QEvent>
        """
        super(XDockToolbar, self).leaveEvent(event)
        
        if not self.actionHeld():
            self.setCurrentAction(None)
    
    def maximumPixmapSize(self):
        """
        Returns the maximum pixmap size for this toolbar.
        
        :return     <int>
        """
        return self._maximumPixmapSize
    
    def minimumPixmapSize(self):
        """
        Returns the minimum pixmap size that will be displayed to the user
        for the dock widget.
        
        :return     <int>
        """
        return self._minimumPixmapSize
    
    def mouseMoveEvent(self, event):
        """
        Updates the labels for this dock toolbar.
        
        :param      event | <XDockToolbar>
        """
        # update the current label
        self.setCurrentAction(self.actionAt(event.pos()))
    
    def padding(self):
        """
        Returns the padding value for this toolbar.
        
        :return     <int>
        """
        return self._padding
    
    def paintEvent(self, event):
        """
        Paints the background for the dock toolbar.
        
        :param      event | <QPaintEvent>
        """
        x = 1
        y = 1
        w = self.width()
        h = self.height()
        
        clr_a = QColor(220, 220, 220)
        clr_b = QColor(190, 190, 190)
        
        grad = QLinearGradient()
        grad.setColorAt(0.0, clr_a)
        grad.setColorAt(0.6, clr_a)
        grad.setColorAt(1.0, clr_b)
        
        # adjust the coloring for the horizontal toolbar
        if self.position() & (self.Position.North | self.Position.South):
            h = self.minimumPixmapSize().height() + 6
            
            if self.position() == self.Position.South:
                y = self.height() - h
                grad.setStart(0, y)
                grad.setFinalStop(0, self.height())
            else:
                grad.setStart(0, 0)
                grad.setFinalStart(0, h)
        
        # adjust the coloring for the vertical toolbar
        if self.position() & (self.Position.East | self.Position.West):
            w = self.minimumPixmapSize().width() + 6
            
            if self.position() == self.Position.West:
                x = self.width() - w
                grad.setStart(x, 0)
                grad.setFinalStop(self.width(), 0)
            else:
                grad.setStart(0, 0)
                grad.setFinalStop(w, 0)
        
        with XPainter(self) as painter:
            painter.fillRect(x, y, w, h, grad)
            
            # show the active action
            action = self.selectedAction()
            if action is not None and \
               not self.currentAction() and \
               not self._animating:
                for lbl in self.actionLabels():
                    if lbl.action() != action:
                        continue
                    
                    geom = lbl.geometry()
                    size = lbl.pixmapSize()
                    
                    if self.position() == self.Position.North:
                        x = geom.left()
                        y = 0
                        w = geom.width()
                        h = size.height() + geom.top() + 2
                    
                    elif self.position() == self.Position.East:
                        x = 0
                        y = geom.top()
                        w = size.width() + geom.left() + 2
                        h = geom.height()
                    
                    painter.setPen(QColor(140, 140, 40))
                    painter.setBrush(QColor(160, 160, 160))
                    painter.drawRect(x, y, w, h)
                    break
    
    def position(self):
        """
        Returns the position for this docktoolbar.
        
        :return     <XDockToolbar.Position>
        """
        return self._position
    
    def rebuild(self):
        """
        Rebuilds the widget based on the position and current size/location
        of its parent.
        """
        if not self.isVisible():
            return
        
        self.raise_()
        
        max_size = self.maximumPixmapSize()
        min_size = self.minimumPixmapSize()
        widget   = self.window()
        rect     = widget.rect()
        rect.setBottom(rect.bottom() - widget.statusBar().height())
        rect.setTop(widget.menuBar().height())
        offset   = self.padding()
        
        # align this widget to the north
        if self.position() == XDockToolbar.Position.North:
            self.move(rect.left(), rect.top())
            self.resize(rect.width(), min_size.height() + offset)
        
        # align this widget to the east
        elif self.position() == XDockToolbar.Position.East:
            self.move(rect.left(), rect.top())
            self.resize(min_size.width() + offset, rect.height())
        
        # align this widget to the south
        elif self.position() == XDockToolbar.Position.South:
            self.move(rect.left(), rect.top() - min_size.height() - offset)
            self.resize(rect.width(), min_size.height() + offset)
        
        # align this widget to the west
        else:
            self.move(rect.right() - min_size.width() - offset, rect.top())
            self.resize(min_size.width() + offset, rect.height())
    
    def resizeToMinimum(self):
        """
        Resizes the dock toolbar to the minimum sizes.
        """
        offset = self.padding()
        min_size = self.minimumPixmapSize()
        
        if self.position() in (XDockToolbar.Position.East,
                               XDockToolbar.Position.West):
            self.resize(min_size.width() + offset, self.height())
        
        elif self.position() in (XDockToolbar.Position.North,
                                 XDockToolbar.Position.South):
            self.resize(self.width(), min_size.height() + offset)

    def selectedAction(self):
        """
        Returns the action that was last selected.
        
        :return     <QAction>
        """
        return self._selectedAction

    def setActionHeld(self, state):
        """
        Sets whether or not this action should be held before clearing on
        leaving.
        
        :param      state | <bool>
        """
        self._actionHeld = state
    
    def setCurrentAction(self, action):
        """
        Sets the current action for this widget that highlights the size
        for this toolbar.
        
        :param      action | <QAction>
        """
        if action == self._currentAction:
            return
        
        self._currentAction = action
        self.currentActionChanged.emit(action)
        
        labels   = self.actionLabels()
        anim_grp = QParallelAnimationGroup(self)
        max_size = self.maximumPixmapSize()
        min_size = self.minimumPixmapSize()
        
        if action:
            label = self.labelForAction(action)
            index = labels.index(label)
            
            # create the highlight effect
            palette = self.palette()
            effect = QGraphicsDropShadowEffect(label)
            effect.setXOffset(0)
            effect.setYOffset(0)
            effect.setBlurRadius(20)
            effect.setColor(QColor(40, 40, 40))
            label.setGraphicsEffect(effect)
            
            offset = self.padding()
            if self.position() in (XDockToolbar.Position.East,
                                   XDockToolbar.Position.West):
                self.resize(max_size.width() + offset, self.height())
            
            elif self.position() in (XDockToolbar.Position.North,
                                     XDockToolbar.Position.South):
                self.resize(self.width(), max_size.height() + offset)
            
            w  = max_size.width()
            h  = max_size.height()
            dw = (max_size.width() - min_size.width()) / 3
            dh = (max_size.height() - min_size.height()) / 3
            
            for i in range(4):
                before = index - i
                after  = index + i
                
                if 0 <= before and before < len(labels):
                    anim = XObjectAnimation(labels[before],
                                            'setPixmapSize',
                                            anim_grp)
                    
                    anim.setEasingCurve(self.easingCurve())
                    anim.setStartValue(labels[before].pixmapSize())
                    anim.setEndValue(QSize(w, h))
                    anim.setDuration(self.duration())
                    anim_grp.addAnimation(anim)
                    
                    if i:
                        labels[before].setGraphicsEffect(None)
                
                if after != before and 0 <= after and after < len(labels):
                    anim = XObjectAnimation(labels[after],
                                            'setPixmapSize',
                                            anim_grp)
                    
                    anim.setEasingCurve(self.easingCurve())
                    anim.setStartValue(labels[after].pixmapSize())
                    anim.setEndValue(QSize(w, h))
                    anim.setDuration(self.duration())
                    anim_grp.addAnimation(anim)
                    
                    if i:
                        labels[after].setGraphicsEffect(None)
            
                w -= dw
                h -= dh
        else:
            offset = self.padding()
            for label in self.actionLabels():
                # clear the graphics effect 
                label.setGraphicsEffect(None)
                
                # create the animation
                anim = XObjectAnimation(label, 'setPixmapSize', self)
                anim.setEasingCurve(self.easingCurve())
                anim.setStartValue(label.pixmapSize())
                anim.setEndValue(min_size)
                anim.setDuration(self.duration())
                anim_grp.addAnimation(anim)
            
            anim_grp.finished.connect(self.resizeToMinimum)
        
        anim_grp.start()
        self._animating = True
        anim_grp.finished.connect(anim_grp.deleteLater)
        anim_grp.finished.connect(self.__markAnimatingFinished)
        
        if self._currentAction:
            self._hoverTimer.start()
        else:
            self._hoverTimer.stop()
    
    def setDuration(self, duration):
        """
        Sets the duration value for the animation of the icon.
        
        :param      duration | <int>
        """
        self._duration = duration
    
    def setEasingCurve(self, curve):
        """
        Sets the easing curve for this toolbar to the inputed curve.
        
        :param      curve | <QEasingCurve>
        """
        self._easingCurve = QEasingCurve(curve)
    
    def setMaximumPixmapSize(self, size):
        """
        Sets the maximum pixmap size for this toolbar.
        
        :param     size | <int>
        """
        self._maximumPixmapSize = size
        position = self.position()
        self._position = None
        self.setPosition(position)
    
    def setMinimumPixmapSize(self, size):
        """
        Sets the minimum pixmap size that will be displayed to the user
        for the dock widget.
        
        :param     size | <int>
        """
        self._minimumPixmapSize = size
        position = self.position()
        self._position = None
        self.setPosition(position)
    
    def setPadding(self, padding):
        """
        Sets the padding amount for this toolbar.
        
        :param      padding | <int>
        """
        self._padding = padding
    
    def setPosition(self, position):
        """
        Sets the position for this widget and its parent.
        
        :param      position | <XDockToolbar.Position>
        """
        if position == self._position:
            return
        
        self._position = position
        
        widget   = self.window()
        layout   = self.layout()
        offset   = self.padding()
        min_size = self.minimumPixmapSize()
        
        # set the layout to north
        if position == XDockToolbar.Position.North:
            self.move(0, 0)
            widget.setContentsMargins(0, min_size.height() + offset, 0, 0)
            layout.setDirection(QBoxLayout.LeftToRight)
        
        # set the layout to east
        elif position == XDockToolbar.Position.East:
            self.move(0, 0)
            widget.setContentsMargins(min_size.width() + offset, 0, 0, 0)
            layout.setDirection(QBoxLayout.TopToBottom)
        
        # set the layout to the south
        elif position == XDockToolbar.Position.South:
            widget.setContentsMargins(0, 0, 0, min_size.height() + offset)
            layout.setDirection(QBoxLayout.LeftToRight)
        
        # set the layout to the west
        else:
            widget.setContentsMargins(0, 0, min_size.width() + offset, 0)
            layout.setDirection(QBoxLayout.TopToBottom)
        
        # update the label alignments
        for label in self.actionLabels():
            label.setPosition(position)
        
        # rebuilds the widget
        self.rebuild()
        self.update()
    
    def setSelectedAction(self, action):
        """
        Sets the selected action instance for this toolbar.
        
        :param      action | <QAction>
        """
        self._hoverTimer.stop()
        self._selectedAction = action
    
    def setVisible(self, state):
        """
        Sets whether or not this toolbar is visible.  If shown, it will rebuild.
        
        :param      state | <bool>
        """
        super(XDockToolbar, self).setVisible(state)
        
        if state:
            self.rebuild()
            self.setCurrentAction(None)
    
    def unholdAction(self):
        """
        Unholds the action from being blocked on the leave event.
        """
        self._actionHeld = False
        
        point = self.mapFromGlobal(QCursor.pos())
        self.setCurrentAction(self.actionAt(point))
    
    def visualRect(self, action):
        """
        Returns the visual rect for the inputed action, or a blank QRect if
        no matching action was found.
        
        :param      action | <QAction>
        
        :return     <QRect>
        """
        for widget in self.actionLabels():
            if widget.action() == action:
                return widget.geometry()
        return QRect()