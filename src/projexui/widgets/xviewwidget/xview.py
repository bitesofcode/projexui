#!/usr/bin python

""" Defines the base View plugin class for the ViewWidget system. """

# define authorship information
__authors__     = ['Eric Hulser']
__author__      = ','.join(__authors__)
__credits__     = []
__copyright__   = 'Copyright (c) 2011, Projex Software'

# maintanence information
__maintainer__  = 'Projex Software'
__email__       = 'team@projexsoftware.com'

from xml.etree import ElementTree

import weakref

import projexui
from projex.text import nativestring
from projexui.qt import Signal, SIGNAL
from projexui.qt.QtCore   import Qt,\
                                 QMimeData,\
                                 QObject,\
                                 QSettings,\
                                 QByteArray,\
                                 QTimer
                           
from projexui.qt.QtGui    import QApplication,\
                                 QGraphicsColorizeEffect,\
                                 QDrag,\
                                 QWidget,\
                                 QDialog,\
                                 QPixmap,\
                                 QVBoxLayout,\
                                 QCursor

from projexui.widgets.xloaderwidget import XLoaderWidget

from projex.enum        import enum
from projex.decorators  import wraps
from projexui           import resources

def xviewSlot(*typs, **opts):
    """
    Defines a method as being a slot for the XView system.  This will validate
    the method against the signal properties if it is triggered from the
    dispatcher, taking into account currency and grouping for the widget.  
    You can specify the optional policy keyword to define the specific signal
    policy for this slot, otherwise it will use its parent view's policy.
    
    :param      default | <variant> | default return value
                policy  | <XView.SignalPolicy> || None
                
    :usage      |from projexui.widgets.xviewwidget import xviewSlot
                |
                |class A(XView):
                |   @xviewSlot()
                |   def format( self ):
                |       print 'test'
    """
    default = opts.get('default')
    policy  = opts.get('policy')
    
    if typs:
        typ_count = len(typs)
    else:
        typ_count = 0
    
    def decorated(func):
        @wraps(func)
        def wrapped(*args, **kwds):
            if ( args and isinstance(args[0], XView) ):
                validated = args[0].validateSignal(policy)
            else:
                validated = True
            
            if ( validated ):
                new_args = args[:typ_count+1]
                return func(*new_args, **kwds)
            return default
        return wrapped
    return decorated

#------------------------------------------------------------------------------

class XViewDispatcher(QObject):
    """ Class to control signals and slots at a view level """
    
    def __init__( self, viewType ):
        super(XViewDispatcher, self).__init__()
        
        self._viewType = viewType
    
    def viewType(self):
        """
        Returns the view class type that this dispatcher is linked to.
        
        :return     <subclass of XView>
        """
        return self._viewType

#------------------------------------------------------------------------------

class XViewDispatch(QObject):
    def __init__(self, parent):
        super(XViewDispatch, self).__init__(parent)
        
        self._signals = set()
        self._blockedSignals = {}
    
    def blockSignal(self, signal, state):
        """
        Blocks the particular signal.
        
        :param      signal | <str>
                    state  | <bool>
        """
        signal = nativestring(signal)
        if state:
            self._blockedSignals.setdefault(signal, 0)
            self._blockedSignals[signal] += 1
        else:
            val = self._blockedSignals.get(signal, 0)
            val -= 1
            if val > 0:
                self._blockedSignals[signal] = val
            elif val == 0:
                self._blockedSignals.pop(signal)
    
    def connect(self, signal, slot):
        """
        Creates a connection for this instance for the given signal.
        
        :param      signal | <str>
                    slot   | <callable>
        """
        super(XViewDispatch, self).connect(self, SIGNAL(signal), slot)
    
    def emit(self, signal, *args):
        """
        Emits a signal through the dispatcher.
        
        :param      signal | <str>
                    *args  | additional arguments
        """
        if not (self.signalsBlocked() or self.signalBlocked(signal)):
            super(XViewDispatch, self).emit(SIGNAL(signal), *args)
    
    def registerSignal(self, signal):
        """
        Registers a single signal to the system.
        
        :param      signal | <str>
        """
        self._signals.add(signal)
    
    def registerSignals(self, signals):
        """
        Registers signals to the system.
        
        :param      signals | [<str>, ..]
        """
        self._signals = self._signals.union(signals)
    
    def signalBlocked(self, signal):
        """
        Returns whether or not the signal is blocked.
        
        :param      signal | <str>
        """
        return nativestring(signal) in self._blockedSignals
    
    def signals(self):
        return sorted(list(self._signals))

#------------------------------------------------------------------------------

class XView(QWidget):
    activated               = Signal()
    deactivated             = Signal()
    currentStateChanged     = Signal(bool)
    windowTitleChanged      = Signal(str)
    sizeConstraintChanged   = Signal()
    initialized             = Signal()
    poppedOut               = Signal()
    shown                   = Signal()
    hidden                  = Signal()
    visibleStateChanged     = Signal(bool)
    
    _registry       = {}
    _globals        = {}
    
    # define static globals
    _dispatcher         = None
    _dispatch           = {}
    
    __designer_icon__ = resources.find('img/ui/view.png')
    
    SignalPolicy        = enum('BlockIfNotCurrent',
                               'BlockIfNotInGroup',
                               'BlockIfNotVisible',
                               'BlockIfNotInitialized',
                               'NeverBlock')
    
    def __init__(self, parent):
        super(XView, self).__init__(parent)
        
        # define custom properties
        self._current       = False
        self._initialized   = False
        self._viewWidget    = None
        self._viewingGroup  = 0
        self._signalPolicy  = XView.SignalPolicy.BlockIfNotInitialized | \
                              XView.SignalPolicy.BlockIfNotVisible | \
                              XView.SignalPolicy.BlockIfNotInGroup
        
        self._visibleState  = False  # storing this state for knowing if a
                                     # widget WILL be visible once Qt finishes
                                     # processing for purpose of signal
                                     # validation.
        
        # setup default properties
        self.setAutoFillBackground(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setWindowTitle(self.viewName())
        self.setFocus()
    
    def canClose(self):
        """
        Virtual method to determine whether or not this view can properly
        close.
        
        :return     <bool>
        """
        return True
    
    def closeEvent(self, event):
        """
        Determines whether or not this widget should be deleted after close.
        
        :param      event | <QtCore.QCloseEvent>
        """
        if not self.canClose():
            event.ignore()
            return

        elif not self.isViewSingleton():
            super(XView, self).closeEvent(event)
            QTimer.singleShot(0, self.deleteLater)

        else:
            super(XView, self).closeEvent(event)
    
    def dispatchConnect(self, signal, slot):
        """
        Connect the slot for this view to the given signal that gets
        emitted by the XView.dispatch() instance.
        
        :param      signal | <str>
                    slot   | <callable>
        """
        XView.dispatch().connect(signal, slot)
    
    def dispatchEmit(self, signal, *args):
        """
        Emits the given signal via the XView dispatch instance with the
        given arguments.
        
        :param      signal | <str>
                    args   | <tuple>
        """
        XView.setGlobal('emitGroup', self.viewingGroup())
        XView.dispatch().emit(signal, *args)
    
    def duplicate(self, parent):
        """
        Duplicates this current view for another.  Subclass this method to 
        provide any additional duplication options.
        
        :param      parent | <QWidget>
        
        :return     <XView> | instance of this class
        """
        # only return a single singleton instance
        if self.isViewSingleton():
            return self
            
        output = type(self).createInstance(parent, self.viewWidget())
        
        # save/restore the current settings
        xdata = ElementTree.Element('data')
        self.saveXml(xdata)
        new_name = output.objectName()
        output.setObjectName(self.objectName())
        output.restoreXml(xdata)
        output.setObjectName(new_name)
        
        return output
    
    def hideEvent(self, event):
        """
        Sets the visible state for this widget.  If it is the first time this
        widget will be visible, the initialized signal will be emitted.
        
        :param      state | <bool>
        """
        super(XView, self).hideEvent(event)
        
        # record the visible state for this widget to be separate of Qt's
        # system to know if this view WILL be visible or not once the 
        # system is done processing.  This will affect how signals are
        # validated as part of the visible slot delegation
        self._visibleState = False
        
        if not self.signalsBlocked():
            self.visibleStateChanged.emit(False)
            QTimer.singleShot(0, self.hidden.emit)
    
    def initialize(self, force=False):
        """
        Initializes the view if it is visible or being loaded.
        """
        if force or (self.isVisible() and \
                     not self.isInitialized() and \
                     not self.signalsBlocked()):
            
            self._initialized = True
            self.initialized.emit()
    
    def isCurrent(self):
        """
        Returns whether or not this view is current within its view widget.
        
        :return     <bool>
        """
        return self._current
    
    def isInitialized(self):
        """
        Returns whether or not this view has been initialized.  A view will
        be initialized the first time it becomes visible to the user.  You
        can use this to delay loading of information until it is needed by
        listening for the initialized signal.
        
        :return     <bool>
        """
        return self._initialized
    
    def mousePressEvent(self, event):
        btn  = event.button()
        mid  = btn == Qt.MidButton
        lft  = btn == Qt.LeftButton
        shft = event.modifiers() == Qt.ShiftModifier
        
        if self.windowFlags() & Qt.Dialog and \
           (mid or (lft and shft)):
            pixmap = QPixmap.grabWidget(self)
            drag = QDrag(self)
            data = QMimeData()
            data.setData('x-application/xview/floating_view',\
                         QByteArray(self.objectName()))
            drag.setMimeData(data)
            drag.setPixmap(pixmap)
            self.hide()
            drag.exec_()
            self.show()
        else:
            super(XView, self).mousePressEvent(event)
    
    def popout(self):
        self.setParent(self.window())
        self.setWindowFlags(Qt.Dialog)
        self.show()
        self.raise_()
        self.activateWindow()
        
        pos = QCursor.pos()
        w = self.width()
        
        self.move(pos.x() - w / 2.0, pos.y() - 10)
        
        # set the popup instance for this class to this widget
        key = '_{0}__popupInstance'.format(type(self).__name__)
        if not hasattr(type(self), key):
            setattr(type(self), key, weakref.ref(self))
        
        self.poppedOut.emit()
    
    def restoreXml(self, xml):
        """
        Restores the settings for this view from the inputed XML node.
        
        :param      xml | <xml.etree.ElementTree.Element>
        """
        pass
    
    def saveXml(self, xml):
        """
        Saves the settings for this view to the inputed XML node.
        
        :param      xml | <xml.etree.ElementTree.Element>
        """
        pass
    
    def settingsName(self):
        """
        Returns the default settings name for this view.
        
        :return     <str>
        """
        return 'Views/%s' % self.objectName()
    
    def setCurrent(self, state=True):
        """
        Marks this view as the current source based on the inputed flag.  \
        This method will return True if the currency changes.
        
        :return     <bool> | changed
        """
        if self._current == state:
            return False
        
        widget = self.viewWidget()
        if widget:
            for other in widget.findChildren(type(self)):
                if other.isCurrent():
                    other._current = False
                    if not other.signalsBlocked():
                        other.currentStateChanged.emit(state)
                        other.deactivated.emit()
        
        self._current = state
        
        if not self.signalsBlocked():
            self.currentStateChanged.emit(state)
            if state:
                self.activated.emit()
            else:
                self.deactivated.emit()
        return True
    
    def setFixedHeight(self, height):
        """
        Sets the maximum height value to the inputed height and emits the \
        sizeConstraintChanged signal.
        
        :param      height | <int>
        """
        super(XView, self).setFixedHeight(height)
        
        if ( not self.signalsBlocked() ):
            self.sizeConstraintChanged.emit()
    
    def setFixedWidth(self, width):
        """
        Sets the maximum width value to the inputed width and emits the \
        sizeConstraintChanged signal.
        
        :param      width | <int>
        """
        super(XView, self).setFixedWidth(width)
        
        if ( not self.signalsBlocked() ):
            self.sizeConstraintChanged.emit()
    
    def setMaximumHeight(self, height):
        """
        Sets the maximum height value to the inputed height and emits the \
        sizeConstraintChanged signal.
        
        :param      height | <int>
        """
        super(XView, self).setMaximumHeight(height)
        
        if ( not self.signalsBlocked() ):
            self.sizeConstraintChanged.emit()
    
    def setMaximumSize(self, *args):
        """
        Sets the maximum size value to the inputed size and emits the \
        sizeConstraintChanged signal.
        
        :param      *args | <tuple>
        """
        super(XView, self).setMaximumSize(*args)
        
        if ( not self.signalsBlocked() ):
            self.sizeConstraintChanged.emit()
    
    def setMaximumWidth(self, width):
        """
        Sets the maximum width value to the inputed width and emits the \
        sizeConstraintChanged signal.
        
        :param      width | <int>
        """
        super(XView, self).setMaximumWidth(width)
        
        if ( not self.signalsBlocked() ):
            self.sizeConstraintChanged.emit()
    
    def setMinimumHeight(self, height):
        """
        Sets the minimum height value to the inputed height and emits the \
        sizeConstraintChanged signal.
        
        :param      height | <int>
        """
        super(XView, self).setMinimumHeight(height)
        
        if ( not self.signalsBlocked() ):
            self.sizeConstraintChanged.emit()
    
    def setMinimumSize(self, *args):
        """
        Sets the minimum size value to the inputed size and emits the \
        sizeConstraintChanged signal.
        
        :param      *args | <tuple>
        """
        super(XView, self).setMinimumSize(*args)
        
        if ( not self.signalsBlocked() ):
            self.sizeConstraintChanged.emit()
    
    def setMinimumWidth(self, width):
        """
        Sets the minimum width value to the inputed width and emits the \
        sizeConstraintChanged signal.
        
        :param      width | <int>
        """
        super(XView, self).setMinimumWidth(width)
        
        if ( not self.signalsBlocked() ):
            self.sizeConstraintChanged.emit()
    
    def setSignalPolicy(self, policy):
        """
        Sets the signal delegation policy for this instance to the given 
        policy.  By default, signals will be delegates for groups or
        by currency if they are not in a group.  This will not directly
        affect signal propogation, only the result of the validateSignal
        method, so if you want to test against this, then you will need
        to check in your slot.
        
        :param      policy | <XView.SignalPolicy>
        """
        self._signalPolicy = policy
    
    def setViewingGroup(self, grp):
        """
        Sets the viewing group that this view is associated with.
        
        :param      grp | <int>
        """
        self._viewingGroup = grp
    
    def setViewWidget(self, widget):
        """
        Sets the view widget that is associated with this view item.
        
        :param      widget | <projexui.widgets.xviewwidget.XViewWidget>
        """
        self._viewWidget = widget
    
    def setWindowTitle(self, title):
        """
        Sets the window title for this view, and emits the windowTitleChanged \
        signal if the signals are not blocked.  Setting this title will update \
        the tab title for the view within the widget.
        
        :param      title | <str>
        """
        super(XView, self).setWindowTitle(title)
        if ( not self.signalsBlocked() ):
            self.windowTitleChanged.emit(title)
    
    def showActiveState(self, state):
        """
        Shows this view in the active state based on the inputed state settings.
        
        :param      state | <bool>
        """
        return
        
        palette = self.window().palette()
        clr = palette.color(palette.Window)
        avg = (clr.red() + clr.green() + clr.blue()) / 3
        
        if avg < 180 and state:
            clr = clr.lighter(105)
        elif not state:
            clr = clr.darker(105)
        
        palette.setColor(palette.Window, clr)
        self.setPalette(palette)
    
    def showEvent(self, event):
        """
        Sets the visible state for this widget.  If it is the first time this
        widget will be visible, the initialized signal will be emitted.
        
        :param      state | <bool>
        """
        super(XView, self).showEvent(event)
        
        # record the visible state for this widget to be separate of Qt's
        # system to know if this view WILL be visible or not once the 
        # system is done processing.  This will affect how signals are
        # validated as part of the visible slot delegation
        self._visibleState = True
        
        if not self.isInitialized():
            self.initialize()
        
        # after the initial time the view is loaded, the visibleStateChanged
        # signal will be emitted
        elif not self.signalsBlocked():
            self.visibleStateChanged.emit(True)
            QTimer.singleShot(0, self.shown.emit)
            
    def signalPolicy(self):
        """
        Returns the signal policy for this instance.
        
        :return     <XView.SignalPolicy>
        """
        return self._signalPolicy
    
    def rootWidget(self):
        widget = self
        while widget.parent():
            widget = widget.parent()
        return widget
    
    def viewWidget(self):
        """
        Returns the view widget that is associated with this instance.
        
        :return     <projexui.widgets.xviewwidget.XViewWidget>
        """
        return self._viewWidget
    
    def validateSignal(self, policy=None):
        """
        Validates that this view is part of the group that was emitting
        the signal.  Views that are not in any viewing group will accept
        all signals.
        
        :param      policy | <XView.SignalPolicy> || None
        
        :return     <bool>
        """
        # validate whether or not to process a signal
        if policy is None:
            policy = self.signalPolicy()
        
        group_check   = XView.getGlobal('emitGroup') == self.viewingGroup()
        current_check = self.isCurrent()
        
        # always delegate signals if they are not set to block,
        # or if the method is called directly (not from a signal)
        if not self.sender() or policy & XView.SignalPolicy.NeverBlock:
            return True
        
        # block delegation of the signal if the view is not initialized
        elif policy & XView.SignalPolicy.BlockIfNotInitialized and \
             not self.isInitialized():
            return False
        
        # block delegation if the view is not visible
        elif policy & XView.SignalPolicy.BlockIfNotVisible and \
            not self._visibleState:
            return False
        
        # block delegation if the view is not part of a group
        elif self.viewingGroup() and \
             policy & XView.SignalPolicy.BlockIfNotInGroup:
            return group_check
        
        # look for only currency releated connections
        elif policy & XView.SignalPolicy.BlockIfNotCurrent:
            return current_check
        
        else:
            return True
        
    def viewingGroup(self):
        """
        Returns the viewing group that this view is assigned to.
        
        :return     <int>
        """
        return self._viewingGroup
    
    @classmethod
    def currentView(cls, parent=None):
        """
        Returns the current view for the given class within a viewWidget.  If
        no view widget is supplied, then a blank view is returned.
        
        :param      viewWidget | <projexui.widgets.xviewwidget.XViewWidget> || None
        
        :return     <XView> || None
        """
        if parent is None:
            parent = projexui.topWindow()
        
        for inst in parent.findChildren(cls):
            if inst.isCurrent():
                return inst
        return None

    @classmethod
    def createInstance(cls, parent, viewWidget=None):
        singleton_key = '_{0}__singleton'.format(cls.__name__)
        singleton = getattr(cls, singleton_key, None)
        
        # assign the singleton instance
        if singleton is not None:
            singleton.setParent(parent)
            return singleton
        else:
            # determine if we need to store a singleton
            inst = cls(parent)
            inst.setObjectName(cls.uniqueName())
            inst.setViewWidget(viewWidget)
            
            if cls.isViewSingleton():
                setattr(cls, singleton_key, inst)
                inst.setAttribute(Qt.WA_DeleteOnClose, False)
            
            return inst
    
    @classmethod
    def destroySingleton(cls):
        """
        Destroys the singleton instance of this class, if one exists.
        """
        singleton_key = '_{0}__singleton'.format(cls.__name__)
        singleton = getattr(cls, singleton_key, None)
        
        if singleton is not None:
            setattr(cls, singleton_key, None)

            singleton.close()
            singleton.deleteLater()
    
    @classmethod
    def instances(cls, parent=None):
        """
        Returns all the instances that exist for a given parent.  If
        no parent exists, then a blank list will be returned.
        
        :param      parent | <QtGui.QWidget>
        
        :return     [<XView>, ..]
        """
        if parent is None:
            parent = projexui.topWindow()
        return parent.findChildren(cls)

    @classmethod
    def isViewSingleton(cls):
        return getattr(cls, '_{0}__viewSingleton'.format(cls.__name__), False)
    
    @classmethod
    def isPopupSingleton(cls):
        return getattr(cls, '_{0}__popupSingleton'.format(cls.__name__), True)
    
    @classmethod
    def popup(cls, parent=None, viewWidget=None):
        """
        Pops up this view as a new dialog.  If the forceDialog flag is set to \
        False, then it will try to activate the first instance of the view \
        within an existing viewwidget context before creating a new dialog.
        
        :param      parent      | <QWidget> || None
                    viewWidget  | <projexui.widgets.xviewwidget.XViewWidget> || None
        """
        if cls.isViewSingleton():
            inst = cls.createInstance(parent, viewWidget)
            inst.setWindowFlags(Qt.Dialog)
        else:
            inst = cls.popupInstance(parent, viewWidget)
        
        inst.showNormal()
        inst.setFocus()
        inst.raise_()
        inst.activateWindow()
    
    @classmethod
    def popupInstance(cls, parent, viewWidget=None):
        key = '_{0}__popupInstance'.format(cls.__name__)
        try:
            inst = getattr(cls, key, None)()
        except TypeError:
            inst = None
        
        if inst is not None:
            return inst
        
        # create a new instance for this popup
        inst = cls.createInstance(parent, viewWidget)
        inst.setWindowFlags(Qt.Dialog)
        if cls.isPopupSingleton():
            setattr(cls, key, weakref.ref(inst))
        
        return inst
    
    @classmethod
    def registerToWindow(cls, window):
        """
        Registers this view to the window to update additional menu items, \
        actions, and toolbars.
        
        :param      window | <QWidget>
        """
        pass
    
    @classmethod
    def restoreGlobalSettings(cls, settings):
        """
        Restores the global settings for the inputed view class type.
        
        :param      cls      | <subclass of XView>
                    settings | <QSettings>
        """
        pass
    
    @classmethod
    def saveGlobalSettings(cls, settings):
        """
        Saves the global settings for the inputed view class type.
        
        :param      cls      | <subclass of XView>
                    settings | <QSettings>
        """
        pass
    
    @classmethod
    def setViewGroup(cls, grp):
        setattr(cls, '_{0}__viewGroup'.format(cls.__name__), grp)
    
    @classmethod
    def setViewIcon(cls, icon):
        setattr(cls, '_{0}__viewIcon'.format(cls.__name__), icon)
    
    @classmethod
    def setViewName(cls, name):
        setattr(cls, '_{0}__viewName'.format(cls.__name__), name)
    
    @classmethod
    def setViewSingleton(cls, state):
        setattr(cls, '_{0}__viewSingleton'.format(cls.__name__), state)
    
    @classmethod
    def setPopupSingleton(cls, state):
        setattr(cls, '_{0}__popupSingleton'.format(cls.__name__), state)
    
    @classmethod
    def uniqueName(cls):
        key = '_{0}__serial'.format(cls.__name__)
        next = getattr(cls, key, 0) + 1
        setattr(cls, key, next)
        return '{0}{1:02}'.format(cls.viewName(), next)
    
    @classmethod
    def unregisterToWindow(cls, window):
        """
        Registers this view to the window to update additional menu items, \
        actions, and toolbars.
        
        :param      window | <QWidget>
        """
        pass
    
    @classmethod
    def viewGroup(cls):
        return getattr(cls, '_{0}__viewGroup'.format(cls.__name__), 'Default')
    
    @classmethod
    def viewIcon(cls):
        default = resources.find('img/view/view.png')
        return getattr(cls, '_{0}__viewIcon'.format(cls.__name__), default)
    
    @classmethod
    def viewName(cls):
        return getattr(cls, '_{0}__viewName'.format(cls.__name__), cls.__name__)
    
    @classmethod
    def viewTypeName(cls):
        """
        Returns the unique name for this view type by joining its group with \
        its name.
        
        :return     <str>
        """
        return '%s.%s' % (cls.viewGroup(), cls.viewName())
    
    #--------------------------------------------------------------------------
    
    @staticmethod
    def dispatch(location='Central'):
        """
        Returns the instance of the global view dispatching system.  All views \
        will route their signals through the central hub so no single view \
        necessarily depends on another.
        
        :return     <XViewDispatch>
        """
        dispatch = XView._dispatch.get(nativestring(location))
        if not dispatch:
            dispatch = XViewDispatch(QApplication.instance())
            XView._dispatch[nativestring(location)] = dispatch
        
        return dispatch
        
    @staticmethod
    def getGlobal(key, default=None):
        """
        Returns the global value for the inputed key.
        
        :param      key     | <str>
                    default | <variant>
        
        :return     <variant>
        """
        return XView._globals.get(key, default)
    
    @staticmethod
    def registeredView(viewName, location='Central'):
        """
        Returns the view that is registered to the inputed location for the \
        given name.
        
        :param      viewName | <str>
                    location | <str>
        
        :return     <subclass of XView> || None
        """
        loc = nativestring(location)
        return XView._registry.get(loc, {}).get(viewName, None)
    
    @staticmethod
    def registeredViews(location='Central'):
        """
        Returns all the views types that have bene registered to a particular \
        location.
        
        :param      location | <str>
        
        :return     [<subclass of XView>, ..]
        """
        return XView._registry.get(nativestring(location), {}).values()
        
    @staticmethod
    def registerView(viewType, location='Central'):
        """
        Registers the inputed view type to the given location.  The location \
        is just a way to group and organize potential view plugins for a \
        particular widget, and is determined per application.  This eases \
        use when building a plugin based system.  It has no relevance to the \
        XView class itself where you register a view.
        
        :param      viewType | <subclass of XView>
        """
        # update the dispatch signals
        sigs = getattr(viewType, '__xview_signals__', [])
        XView.dispatch(location).registerSignals(sigs)
        
        location = nativestring(location)
        XView._registry.setdefault(location, {})
        XView._registry[location][viewType.viewName()] = viewType
        XView.dispatch(location).emit('registeredView(QVariant)', viewType)
    
    @staticmethod
    def unregisterView(viewType, location='Central'):
        """
        Unregisteres the given view type from the inputed location.
        
        :param      viewType | <subclass of XView>
        """
        XView._registry.get(location, {}).pop(viewType.viewName(), None)
        XView.dispatch(location).emit('unregisteredView(QVariant)', viewType)
    
    @staticmethod
    def setGlobal(key, value):
        """
        Shares a global value across all views by setting the key in the \
        globals dictionary to the inputed value.
        
        :param      key     | <str> 
                    value   | <variant>
        """
        XView._globals[key] = value

