""" 
Defines an extension to the standard QStackedWidget 

This is a python port of the example code from the 
[http://www.developer.nokia.com/Community/Wiki/Extending_QStackedWidget_for_sliding_page_animations_in_Qt Qt wiki].

"""

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software, LLC'
__license__         = 'GPL'

__maintainer__      = 'Projex Software, LLC'
__email__           = 'team@projexsoftware.com'

from projexui.qt import Signal, Slot, Property
from projexui.qt.QtCore import QEasingCurve,\
                               QPoint,\
                               QPropertyAnimation,\
                               QParallelAnimationGroup

from projexui.qt.QtGui import QStackedWidget

from projex.enum import enum

class XStackedWidget(QStackedWidget):
    __designer_container__ = True
    __designer_xml__ = """\
<widget class="XStackedWidget" name="stackedWidget">
    <property name="geometry">
        <rect>
            <x>100</x>
            <y>60</y>
            <width>321</width>
            <height>391</height>
        </rect>
    </property>
    <widget class="QWidget" name="page"/>
    <widget class="QWidget" name="page_2"/>
</widget>"""
    
    animationFinished = Signal()
    
    Direction = enum('LeftToRight',
                     'RightToLeft',
                     'TopToBottom',
                     'BottomToTop',
                     'Automatic')
    
    def __init__(self, parent=None):
        super(XStackedWidget, self).__init__(parent)
        
        # define custom properties
        self._animationType = QEasingCurve.Linear
        self._vertical = False
        self._wrap = False
        self._active = False
        self._speed = 250
        self._nextIndex = 0
        self._lastIndex = 0
        self._lastPoint = None
    
    def _finishAnimation(self):
        """
        Cleans up post-animation.
        """
        self.setCurrentIndex(self._nextIndex)
        self.widget(self._lastIndex).hide()
        self.widget(self._lastIndex).move(self._lastPoint)
        self._active = False
        
        if not self.signalsBlocked():
            self.animationFinished.emit()
    
    def animationType(self):
        """
        Returns the animation curve type for this widget.
        
        :return     <QEasingCurve.Type>
        """
        return self._animationType
    
    def clear(self):
        """
        Clears out the widgets from this stack.
        """
        for i in range(self.count() - 1, -1, -1):
            w = self.widget(i)
            if w:
                self.removeWidget(w)
                w.close()
                w.deleteLater()
    
    def isVerticalMode(self):
        """
        Returns whether or not the animation will play vertically or not.
        
        :return     <bool>
        """
        return self._vertical
    
    @Slot(QEasingCurve.Type)
    def setAnimationType(self, animationType):
        """
        Sets the animation curve type for this widget.
        
        :param      animationType | <QEasingCurve.Type>
        """
        self._animationType = animationType
    
    @Slot(int)
    def setSpeed(self, speed):
        """
        Sets the speed for this widget.
        
        :param      speed | <int>
        """
        self._speed = speed
    
    @Slot(bool)
    def setVerticalMode(self, state=True):
        """
        Sets whether or not the animation will play vertically or not.
        
        :param      state | <bool>
        """
        self._vertical = state
    
    @Slot(bool)
    def setWrap(self, state=True):
        """
        Sets whether or not the stacked widget will wrap during the animation.
        
        :param      state | <bool>
        """
        self._wrap = state
    
    @Slot(int)
    def slideIn(self, index, direction=Direction.Automatic):
        """
        Slides in the panel at the inputed index in the given
        direction for this widget.
        
        :param      index | <int>
                    direction | <XStackedWidget.Direction>
        
        :return     <bool> | success
        """
        # do not allow multiple slides while it is active
        if self._active:
            return False
        
        # determine the proper index to calculate
        invert = False
        if self.count() <= index:
            if not self.wrap():
                return False
            index = self.count() % index
            invert = True
        elif index < 0:
            if not self.wrap():
                return False
            index = self.count() + index
            invert = True
        
        # define the direction information
        if index == self.currentIndex():
            return False
        elif self.currentIndex() < index:
            if direction == XStackedWidget.Direction.Automatic:
                if self.isVerticalMode():
                    direction = XStackedWidget.Direction.BottomToTop
                else:
                    direction = XStackedWidget.Direction.RightToLeft
        else:
            if direction == XStackedWidget.Direction.Automatic:
                if self.isVerticalMode():
                    direction = XStackedWidget.Direction.TopToBottom
                else:
                    direction = XStackedWidget.Direction.LeftToRight
        
        # invert the animation if we are wrapping
        if invert:
            if direction == XStackedWidget.Direction.BottomToTop:
                direction = XStackedWidget.Direction.TopToBottom
            elif direction == XStackedWidget.Direction.TopToBottom:
                direction = XStackedWidget.Direction.BottomToTop
            elif direction == XStackedWidget.Direction.LeftToRight:
                direction = XStackedWidget.Direction.RightToLeft
            else:
                direction = XStackedWidget.Direction.LeftToRight
        
        self._active = True
        offset_x = self.frameRect().width()
        offset_y = self.frameRect().height()
        
        next_widget = self.widget(index)
        curr_widget = self.widget(self.currentIndex())
        
        next_widget.setGeometry(0, 0, offset_x, offset_y)
        
        if direction == XStackedWidget.Direction.BottomToTop:
            offset_x = 0
            offset_y = -offset_y
        elif direction == XStackedWidget.Direction.TopToBottom:
            offset_x = 0
        elif direction == XStackedWidget.Direction.RightToLeft:
            offset_x = -offset_x
            offset_y = 0
        elif direction == XStackedWidget.Direction.LeftToRight:
            offset_y = 0
        
        next_point = next_widget.pos()
        curr_point = curr_widget.pos()
        
        self._nextIndex = index
        self._lastIndex = self.currentIndex()
        self._lastPoint = QPoint(curr_point)
        
        next_widget.move(next_point.x()-offset_x, next_point.y()-offset_y)
        next_widget.raise_()
        next_widget.show()
        
        curr_anim = QPropertyAnimation(curr_widget, 'pos')
        curr_anim.setDuration(self.speed())
        curr_anim.setEasingCurve(self.animationType())
        curr_anim.setStartValue(curr_point)
        curr_anim.setEndValue(QPoint(curr_point.x()+offset_x,
                                     curr_point.y()+offset_y))
        
        next_anim = QPropertyAnimation(next_widget, 'pos')
        next_anim.setDuration(self.speed())
        next_anim.setEasingCurve(self.animationType())
        next_anim.setStartValue(QPoint(next_point.x()-offset_x,
                                       next_point.y()-offset_y))
        next_anim.setEndValue(next_point)
        
        anim_group = QParallelAnimationGroup(self)
        anim_group.addAnimation(curr_anim)
        anim_group.addAnimation(next_anim)
        
        anim_group.finished.connect(self._finishAnimation)
        anim_group.finished.connect(anim_group.deleteLater)
        anim_group.start()
        
        return True
    
    @Slot()
    def slideInNext(self):
        """
        Slides in the next slide for this widget.
        
        :return     <bool> | success
        """
        return self.slideIn(self.currentIndex() + 1)
    
    @Slot()
    def slideInPrev(self):
        """
        Slides in the previous slide for this widget.
        
        :return     <bool> | success
        """
        return self.slideIn(self.currentIndex() - 1)
    
    def speed(self):
        """
        Returns the speed property for this stacked widget.
        
        :return     <int>
        """
        return self._speed
    
    def wrap(self):
        """
        Returns whether or not the stacked widget will wrap during the
        animation.
        
        :return     <bool>
        """
        return self._wrap
    
    x_animationType = Property(QEasingCurve.Type,
                               animationType,
                               setAnimationType)
    
    x_speed = Property(int, speed, setSpeed)
    x_verticalMode = Property(bool, isVerticalMode, setVerticalMode)
    x_wrap = Property(bool, wrap, setWrap)

__designer_plugins__ = [XStackedWidget]