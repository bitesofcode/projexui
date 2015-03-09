#!/usr/bin/python

""" Defines a gantt widget item class for adding items to the widget. """

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

from projex.enum import enum

import projexui
import projex.dates

from projex.text import nativestring

from projexui.qt import wrapVariant
from projexui.qt.QtCore   import QDate,\
                                 QRectF,\
                                 QSize,\
                                 QTime,\
                                 QDateTime,\
                                 Qt

from projexui.qt.QtGui import QIcon

from projexui.widgets.xtreewidget import XTreeWidgetItem

from projexui.widgets.xganttwidget.xganttviewitem import XGanttViewItem
from projexui.widgets.xganttwidget.xganttdepitem  import XGanttDepItem
from projexui.widgets.xganttwidget.xganttwidget   import XGanttWidget

#------------------------------------------------------------------------------

class XGanttWidgetItem(XTreeWidgetItem):
    """ 
    Defines the main widget item class that contains information for both the
    tree and view widget items.
    """
    
    ItemStyle = enum('Normal', 'Group', 'Milestone')
    
    def __init__(self, ganttWidget):
        super(XGanttWidgetItem, self).__init__()
        
        # set default properties
        self.setFixedHeight(ganttWidget.cellHeight())
        for i in range(1, 20):
            self.setTextAlignment(i, Qt.AlignCenter)
        
        # define custom properties
        self._blockedAdjustments        = {}
        self._viewItem                  = self.createViewItem()
        self._dateStart                 = QDate.currentDate()
        self._dateEnd                   = QDate.currentDate()
        self._allDay                    = True
        self._timeStart                 = QTime(0, 0, 0)
        self._timeEnd                   = QTime(23, 59, 59)
        self._name                      = ''
        self._properties                = {}
        self._itemStyle                 = XGanttWidgetItem.ItemStyle.Normal
        self._useGroupStyleWithChildren = True
        self._dependencies              = {}
        self._reverseDependencies       = {}
    
    def addChild(self, item):
        """
        Adds a new child item to this item.
        
        :param      item | <XGanttWidgetItem>
        """
        super(XGanttWidgetItem, self).addChild(item)
        
        item.sync()
    
    def addDependency(self, item):
        """
        Creates a dependency for this item to the next item.  This item will
        be treated as the source, the other as the target.
        
        :param      item | <QGanttWidgetItem>
        """
        if item in self._dependencies:
            return
        
        viewItem = XGanttDepItem(self, item)
        
        self._dependencies[item]        = viewItem
        item._reverseDependencies[self] = viewItem
        
        self.syncDependencies()
    
    def adjustmentsBlocked(self, key):
        """
        Returns whether or not hierarchy adjustments are being blocked.
        
        :param      key | <str>
        
        :return     <bool>
        """
        return self._blockedAdjustments.get(nativestring(key), False)
    
    def adjustChildren(self, delta, secs=False):
        """
        Shifts the children for this item by the inputed number of days.
        
        :param      delta | <int>
        """
        if self.adjustmentsBlocked('children'):
            return
            
        if self.itemStyle() != self.ItemStyle.Group:
            return
        
        if not delta:
            return
        
        for c in range(self.childCount()):
            child = self.child(c)
            child.blockAdjustments('range', True)
            if secs:
                dstart = child.dateTimeStart()
                dstart = dstart.addSecs(delta)
                child.setDateStart(dstart.date())
                child.setTimeStart(dstart.time())
            else:
                child.setDateStart(child.dateStart().addDays(delta))
            child.blockAdjustments('range', False)
    
    def adjustRange(self, recursive=True):
        """
        Adjust the start and end ranges for this item based on the limits from
        its children.  This method will only apply to group items.
        
        :param      recursive | <bool>
        """
        if ( self.adjustmentsBlocked('range') ):
            return
        
        if ( self.itemStyle() == self.ItemStyle.Group ):
            dateStart = self.dateStart()
            dateEnd   = self.dateEnd()
            first     = True
            
            for c in range(self.childCount()):
                child       = self.child(c)
                
                if ( first ):
                    dateStart = child.dateStart()
                    dateEnd   = child.dateEnd()
                    first     = False
                else:
                    dateStart   = min(child.dateStart(), dateStart)
                    dateEnd     = max(child.dateEnd(), dateEnd)
            
            self._dateStart = dateStart
            self._dateEnd   = dateEnd
            
            self.sync()
        
        if ( self.parent() and recursive ):
            self.parent().adjustRange(True)
    
    def blockAdjustments(self, key, state):
        """
        Blocks the inputed adjustments for the given key type.
        
        :param      key     | <str>
                    state   | <bool>
        """
        self._blockedAdjustments[nativestring(key)] = state
    
    def clearDependencies(self):
        """
        Clears out all the dependencies from the scene.
        """
        gantt = self.ganttWidget()
        if ( not gantt ):
            return
        
        scene = gantt.viewWidget().scene()
        
        for target, viewItem in self._dependencies.items():
            target._reverseDependencies.pop(self)
            scene.removeItem(viewItem)
        
        self._dependencies.clear()
    
    def createViewItem(self):
        """
        Returns a new XGanttViewItem to use with this item.
        
        :return     <XGanttViewItem>
        """
        return XGanttViewItem(self)
    
    def dateEnd(self):
        """
        Return the end date for this gantt item.
        
        :return     <QDate>
        """
        return self._dateEnd
    
    def dateStart(self):
        """
        Return the start date for this gantt item.
        
        :return     <QDate>
        """
        return self._dateStart
    
    def dateTimeEnd(self):
        """
        Returns a merging of data from the date end with the time end.
        
        :return     <QDateTime>
        """
        return QDateTime(self.dateEnd(), self.timeEnd())
    
    def dateTimeStart(self):
        """
        Returns a merging of data from the date end with the date start.
        
        :return     <QDateTime>
        """
        return QDateTime(self.dateStart(), self.timeStart())
    
    def dependencies(self):
        """
        Returns a list of all the dependencies linked with this item.
        
        :return     [<XGanttWidgetItem>, ..]
        """
        return self._dependencies.keys()
    
    def duration(self):
        """
        Returns the number of days this gantt item represents.
        
        :return     <int>
        """
        return 1 + self.dateStart().daysTo(self.dateEnd())
    
    def ganttWidget(self):
        """
        Returns the gantt widget that this item is linked to.
        
        :return     <XGanttWidget> || None
        """
        tree = self.treeWidget()
        if ( not tree ):
            return None
        
        from projexui.widgets.xganttwidget import XGanttWidget
        return projexui.ancestor(tree, XGanttWidget)
    
    def insertChild(self, index, item):
        """
        Inserts a new item in the given index.
        
        :param      index | <int>
                    item  | <XGanttWidgetItem>
        """
        super(XGanttWidgetItem, self).insertChild(index, item)
        item.sync()
    
    def isAllDay(self):
        """
        Returns whehter or not this item reflects an all day event.
        
        :return     <bool>
        """
        return self._allDay
    
    def itemStyle(self):
        """
        Returns the item style information for this item.
        
        :return     <XGanttWidgetItem.ItemStyle>
        """
        if ( self.useGroupStyleWithChildren() and self.childCount() ):
            return XGanttWidgetItem.ItemStyle.Group
        
        return self._itemStyle
    
    def name(self):
        """
        Returns the name for this gantt widget item.
        
        :return     <str>
        """
        return self._name
    
    def property(self, key, default=None):
        """
        Returns the custom data that is stored on this object.
        
        :param      key     | <str>
                    default | <variant>
        
        :return     <variant>
        """
        if key == 'Name':
            return self.name()
        elif key == 'Start':
            return self.dateStart()
        elif key == 'End':
            return self.dateEnd()
        elif key == 'Calendar Days':
            return self.duration()
        elif key == 'Work Days':
            return self.weekdays()
        elif key == 'Time Start':
            return self.timeStart()
        elif key == 'Time End':
            return self.timeEnd()
        elif key == 'All Day':
            return self.isAllDay()
        else:
            return self._properties.get(nativestring(key), default)
    
    def removeFromScene(self):
        """
        Removes this item from the view scene.
        """
        gantt = self.ganttWidget()
        if not gantt:
            return
        
        scene = gantt.viewWidget().scene()
        
        scene.removeItem(self.viewItem())
        for target, viewItem in self._dependencies.items():
            target._reverseDependencies.pop(self)
            scene.removeItem(viewItem)
    
    def setAllDay(self, state):
        """
        Sets whether or not this item is an all day event.
        
        :param      state | <bool>
        """
        self._allDay = state
    
    def setDateEnd(self, date):
        """
        Sets the date start value for this item.
        
        :param      dateStart | <QDate>
        """
        self._dateEnd = date
        
    def setDateStart(self, date):
        """
        Sets the date start value for this item.
        
        :param      dateStart | <QDate>
        """
        self._dateStart = date
    
    def setDateTimeEnd(self, dtime):
        """
        Sets the endiing date time for this gantt chart.
        
        :param      dtime | <QDateTime>
        """
        self._dateEnd = dtime.date()
        self._timeEnd = dtime.time()
        self._allDay = False
    
    def setDateTimeStart(self, dtime):
        """
        Sets the starting date time for this gantt chart.
        
        :param      dtime | <QDateTime>
        """
        self._dateStart = dtime.date()
        self._timeStart = dtime.time()
        self._allDay = False
    
    def setDuration(self, duration):
        """
        Sets the duration for this item to the inputed duration.
        
        :param      duration | <int>
        """
        if duration < 1:
            return False
        
        self.setDateEnd(self.dateStart().addDays(duration - 1))
        return True
    
    def setItemStyle(self, itemStyle):
        """
        Sets the item style that will be used for this widget.  If you are
        trying to set a style on an item that has children, make sure to turn 
        off the useGroupStyleWithChildren option, or it will always display as
        a group.
        
        :param      itemStyle | <XGanttWidgetItem.ItemStyle>
        """
        self._itemStyle = itemStyle
        
        # initialize the group icon for group style
        if itemStyle == XGanttWidgetItem.ItemStyle.Group and \
           self.icon(0).isNull():
            ico = projexui.resources.find('img/folder_close.png')
            expand_ico = projexui.resources.find('img/folder_open.png')
            self.setIcon(0, QIcon(ico))
            self.setExpandedIcon(0, QIcon(expand_ico))
    
    def setName(self, name):
        """
        Sets the name of this widget item to the inputed name.
        
        :param      name | <str>
        """
        self._name = name
        
        tree = self.treeWidget()
        if tree:
            col = tree.column('Name')
            if col != -1:
                self.setData(col, Qt.EditRole, wrapVariant(name))
    
    def setProperty(self, key, value):
        """
        Sets the custom property for this item's key to the inputed value.  If
        the widget has a column that matches the inputed key, then the value 
        will be added to the tree widget as well.
        
        :param      key     | <str>
                    value   | <variant>
        """
        if key == 'Name':
            self.setName(value)
        elif key == 'Start':
            self.setDateStart(value)
        elif key == 'End':
            self.setDateEnd(value)
        elif key == 'Calendar Days':
            self.setDuration(value)
        elif key == 'Time Start':
            self.setTimeStart(value)
        elif key == 'Time End':
            self.setTimeEnd(value)
        elif key == 'All Day':
            self.setAllDay(value)
        elif key == 'Workadys':
            pass
        else:
            self._properties[nativestring(key)] = value
            
            tree = self.treeWidget()
            if tree:
                col = tree.column(key)
                if col != -1:
                    self.setData(col, Qt.EditRole, wrapVariant(value))
    
    def setTimeEnd(self, time):
        """
        Sets the ending time that this item will use.  To properly use a timed
        item, you need to also set this item's all day property to False.
        
        :sa         setAllDay
        
        :param      time | <QTime>
        """
        self._timeEnd = time
        self._allDay = False
    
    def setTimeStart(self, time):
        """
        Sets the starting time that this item will use.  To properly use a timed
        item, you need to also set this item's all day property to False.
        
        :sa         setAllDay
        
        :param      time | <QTime>
        """
        self._timeStart = time
        self._allDay = False
    
    def setUseGroupStyleWithChildren(self, state):
        """
        Sets whether or not this item should display as group style when 
        it has children.  This will override whatever is set in the style
        property for the item.
        
        :return     <bool>
        """
        self._useGroupStyleWithChildren = state
    
    def sync(self, recursive=False):
        """
        Syncs the information from this item to the tree and view.
        """
        self.syncTree(recursive=recursive)
        self.syncView(recursive=recursive)

    def syncDependencies(self, recursive=False):
        """
        Syncs the dependencies for this item to the view.
        
        :param      recurisve | <bool>
        """
        scene = self.viewItem().scene()
        if not scene:
            return
        
        visible       = self.viewItem().isVisible()
        depViewItems  = self._dependencies.values() 
        depViewItems += self._reverseDependencies.values()
        
        for depViewItem in depViewItems:
            if not depViewItem.scene():
                scene.addItem(depViewItem)
            
            depViewItem.rebuild()
            depViewItem.setVisible(visible)
        
        if recursive:
            for c in range(self.childCount()):
                self.child(c).syncDependencies(recursive = True)
        
    def syncTree(self, recursive=False, blockSignals=True):
        """
        Syncs the information from this item to the tree.
        """
        tree = self.treeWidget()
        
        # sync the tree information
        if not tree:
            return
        
        items = [self]
        if recursive:
            items += list(self.children(recursive=True))
        
        if blockSignals and not tree.signalsBlocked():
            blocked = True
            tree.blockSignals(True)
        else:
            blocked = False
        
        date_format = self.ganttWidget().dateFormat()
        
        for item in items:
            for c, col in enumerate(tree.columns()):
                value = item.property(col, '')
                item.setData(c, Qt.EditRole, wrapVariant(value))
        
        if blocked:
            tree.blockSignals(False)
    
    def syncView(self, recursive=False):
        """
        Syncs the information from this item to the view.
        """
        # update the view widget
        gantt = self.ganttWidget()
        tree = self.treeWidget()
        
        if not gantt:
            return
        
        vwidget = gantt.viewWidget()
        scene = vwidget.scene()
        cell_w = gantt.cellWidth()
        
        tree_offset_y  = tree.header().height() + 1
        tree_offset_y += tree.verticalScrollBar().value()
        
        # collect the items to work on
        items = [self]
        if recursive:
            items += list(self.children(recursive=True))
        
        for item in items:
            # grab the view item from the gantt item
            vitem = item.viewItem()
            if not vitem.scene():
                scene.addItem(vitem)
            
            # make sure the item should be visible
            if item.isHidden() or not tree:
                vitem.hide()
                continue
            
            vitem.show()
            tree_rect = tree.visualItemRect(item)
            
            tree_y  = tree_rect.y() + tree_offset_y
            tree_h  = tree_rect.height()
            
            # check to see if this item is hidden
            if tree_rect.height() == 0:
                vitem.hide()
                continue
            
            if gantt.timescale() in (gantt.Timescale.Minute,
                                     gantt.Timescale.Hour, 
                                     gantt.Timescale.Day):
                dstart = item.dateTimeStart()
                dend   = item.dateTimeEnd()
                view_x = scene.datetimeXPos(dstart)
                view_r = scene.datetimeXPos(dend)
                view_w = view_r - view_x
            else:
                view_x = scene.dateXPos(item.dateStart())
                view_w = item.duration() * cell_w
            
                # determine the % off from the length based on this items time
                if not item.isAllDay():
                    full_day = 24 * 60 * 60 # full days worth of seconds
                    
                    # determine the start offset
                    start      = item.timeStart()
                    start_day  = (start.hour() * 60 * 60) 
                    start_day += (start.minute() * 60) 
                    start_day += (start.second())
                    
                    offset_start = (start_day / float(full_day)) * cell_w
                    
                    # determine the end offset
                    end         = item.timeEnd()
                    end_day     = (end.hour() * 60 * 60)
                    end_day    += (start.minute() * 60)
                    end_day    += (start.second() + 1) # forces at least 1 sec
                    
                    offset_end  = ((full_day - end_day) / float(full_day))
                    offset_end *= cell_w
                    
                    # update the xpos and widths
                    view_x += offset_start
                    view_w -= (offset_start + offset_end)
            
            view_w = max(view_w, 5)
            
            vitem.setSyncing(True)
            vitem.setPos(view_x, tree_y)
            vitem.setRect(0, 0, view_w, tree_h)
            vitem.setSyncing(False)
            
            # setup standard properties
            flags  = vitem.ItemIsSelectable 
            flags |= vitem.ItemIsFocusable
            
            if item.flags() & Qt.ItemIsEditable:
                flags |= vitem.ItemIsMovable
            
            vitem.setFlags(flags)
            item.syncDependencies()
    
    def takeChild(self, index):
        """
        Removes the child at the given index from this item.
        
        :param      index | <int>
        """
        item = super(XGanttWidgetItem, self).takeChild(index)
        
        if item:
            item.removeFromScene()
            
        return item
        
    def takeDependency(self, item):
        """
        Removes the dependency between the this item and the inputed target.
        
        :param      item | <XGanttWidgetItem>
        """
        if ( not item in self._dependencies ):
            return
        
        item._reverseDependencies.pop(self)
        viewItem = self._dependencies.pop(item)
        
        scene    = viewItem.scene()
        if ( scene ):
            scene.removeItem(viewItem)
    
    def timeEnd(self):
        """
        Returns the ending time that will be used for this item.  If it is an
        all day event, then the time returned will be 23:59:59.
        
        :return     <QTime>
        """
        if ( self.isAllDay() ):
            return QTime(23, 59, 59)
        return self._timeEnd
    
    def timeStart(self):
        """
        Returns the starting time that will be used for this item.  If it is
        an all day event, then the time returned will be 0:0:0
        
        :return     <QTime>
        """
        if ( self.isAllDay() ):
            return QTime(0, 0, 0)
        
        return self._timeStart
    
    def useGroupStyleWithChildren(self):
        """
        Returns whether or not this item should display as group style when 
        it has children.  This will override whatever is set in the style
        property for the item.
        
        :return     <bool>
        """
        return self._useGroupStyleWithChildren
    
    def viewChanged(self, start, end):
        """
        Called when the view item is changed by the user.
        
        :param      start | <QDate> || <QDateTime>
                    end   | <QDate> || <QDateTime>
        """
        if type(start) == QDate:
            delta           = self._dateStart.daysTo(start)
            self._dateStart = start
            self._dateEnd   = end
            self.adjustChildren(delta)

        else:
            delta = self._dateStart.secsTo(start)
            self._dateStart = start.date()
            self._timeStart = start.time()
            
            self._dateEnd = end.date()
            self._timeEnd = end.time()
            
            self.adjustChildren(delta, secs=True)
        
        self.adjustRange()
        
        self.syncDependencies()
        self.syncTree()
    
    def viewItem(self):
        """
        Returns the view item that is linked with this item.
        
        :return     <XGanttViewItem>
        """
        if type(self._viewItem).__name__ == 'weakref':
            return self._viewItem()
        return self._viewItem
    
    def weekdays(self):
        """
        Returns the number of weekdays this item has.
        
        :return     <int>
        """
        if self.itemStyle() == self.ItemStyle.Group:
            out = 0
            for i in range(self.childCount()):
                out += self.child(i).weekdays()
            return out
        else:
            dstart = self.dateStart().toPyDate()
            dend   = self.dateEnd().toPyDate()
            
            return projex.dates.weekdays(dstart, dend)