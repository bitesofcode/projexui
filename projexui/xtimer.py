#!/usr/bin/python

"""
Defines the <XTimer> class, a QTimer wrapper class 
that is thread safe.
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

from xqt import QtCore

class XTimer(QtCore.QObject):
    """
    The default <QtCore.QTimer> is not threadable -- you cannot call
    start or stop from a different thread.  It must always reside on the
    thread that created it.  The XTimer is a wrapper over the
    default <QtCore.QTimer> class instance that allows the ability to
    call the start or stop slots from any thread.
    
    :usage  |>>> from xqt import QtCore
            |>>> thread = QtCore.QThread()
            |>>> thread.start()
            |>>> 
            |>>> # non-thread safe calls
            |>>> qtimer = QtCore.QTimer()
            |>>> qtimer.moveToThread(thread)
            |>>> qtimer.start()
            |QObject::startTimer: timers cannot be started from another thread
            |>>> qtimer.stop()
            |QObject::killTimer: timers cannot be stopped from another thread
            |>>> 
            |>>> # thread safe calls
            |>>> from projexui.xtimer import XTimer
            |>>> ttimer = XTimer()
            |>>> ttimer.moveToThread(thread)
            |>>> ttimer.start()
            |>>> ttimer.stop()
            |>>> 
    """
    _singleShotChanged = QtCore.Signal(bool)
    _intervalChanged = QtCore.Signal(int)
    _startRequested = QtCore.Signal(int)
    _stopRequested = QtCore.Signal()
    
    timeout = QtCore.Signal()
    
    def __init__(self, parent=None):
        super(XTimer, self).__init__(parent)
        
        # define custom properties
        self.__timer = None
        self.__active = False
        self.__singleShot = False
        self.__interval = 0
        self.__lock = QtCore.QReadWriteLock()
        
        # create connections
        self._singleShotChanged.connect(self._setTimerSingleShot, QtCore.Qt.QueuedConnection)
        self._intervalChanged.connect(self._setTimerInterval, QtCore.Qt.QueuedConnection)
        self._startRequested.connect(self._startTimer, QtCore.Qt.QueuedConnection)
        self._stopRequested.connect(self._stopTimer, QtCore.Qt.QueuedConnection)

    def _clearTimer(self):
        self.__timer = None

    def _setTimerInterval(self, interval):
        """
        Sets the internal timer's interval.
        
        :param      interval | <int>
        """
        try:
            self.__timer.setInterval(interval)
        except AttributeError:
            pass

    def _setTimerSingleShot(self, state):
        """
        Sets the internal timer's single shot state.
        
        :param      state | <bool>
        """
        try:
            self.__timer.setSingleShot(state)
        except AttributeError:
            pass

    def _startTimer(self, interval):
        """
        Starts the internal timer.
        
        :param      interval | <int>
        """
        if not self.__timer:
            self.__timer = QtCore.QTimer(self)
            self.__timer.setSingleShot(self.__singleShot)
            self.__timer.setInterval(interval)
            self.__timer.timeout.connect(self.timeout)
            self.__timer.destroyed.connect(self._clearTimer)

            # ensure to stop this timer when the app quits
            QtCore.QCoreApplication.instance().aboutToQuit.connect(self.__timer.stop, QtCore.Qt.QueuedConnection)
        
        self.__timer.start(interval)

    def _stopTimer(self):
        """
        Stops the internal timer, if one exists.
        
        :param      stop | <int>
        """
        try:
            self.__timer.stop()
        except AttributeError:
            pass

    def interval(self):
        """
        Returns the interval in milliseconds for this timer.
        
        :return     <int> | msecs
        """
        with QtCore.QReadLocker(self.__lock):
            return self.__interval

    def isActive(self):
        """
        Returns whether or not this timer is currently active.
        
        :return     <bool>
        """
        try:
            return self.__timer.isActive()
        except AttributeError:
            return False

    def isSingleShot(self):
        """
        Returns whether or not this timer should operate only a single time.
        
        :return     <bool>
        """
        with QtCore.QReadLocker(self.__lock):
            return self.__singleShot

    def setInterval(self, msecs):
        """
        Sets the interval in milliseconds for this timer.
        
        :param      msecs | <int>
        """
        with QtCore.QWriteLocker(self.__lock):
            self.__interval = msecs
            self._intervalChanged.emit(msecs)

    def setSingleShot(self, state):
        """
        Sets whether or not this timer is setup for a single entry or not.
        
        :param      state | <bool>
        """
        with QtCore.QWriteLocker(self.__lock):
            self.__singleShot = state
            self._singleShotChanged.emit(state)

    def start(self, interval=None):
        """
        Emits the start requested signal for this timer, effectively starting
        its internal timer.
        
        :param      interval | <int>
        """
        # update the interval value
        with QtCore.QReadLocker(self.__lock):
            if interval is None:
                interval = self.__interval
            else:
                self.__interval = interval
        
        # request the timer to start
        self._startRequested.emit(interval)

    def stop(self):
        """
        Emits the stop requested signal for this timer, effectivly stopping its
        internal timer.
        """
        self._stopRequested.emit()

    singleShot = QtCore.QTimer.singleShot

