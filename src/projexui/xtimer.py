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
    timeout = QtCore.Signal()
    
    def __init__(self, parent=None):
        super(XTimer, self).__init__(parent)
        
        # define custom properties
        self.__active = False
        self.__singleShot = False
        self.__interval = 0
        self.__lock = QtCore.QReadWriteLock()

    def interval(self):
        """
        Returns the interval in milliseconds for this timer.
        
        :return     <int> | msecs
        """
        locker = QtCore.QReadLocker(self.__lock)
        return self.__interval

    def isActive(self):
        """
        Returns whether or not this timer is currently active.
        
        :return     <bool>
        """
        locker = QtCore.QReadLocker(self.__lock)
        return self.__active

    def isSingleShot(self):
        """
        Returns whether or not this timer should operate only a single time.
        
        :return     <bool>
        """
        locker = QtCore.QReadLocker(self.__lock)
        return self.__singleShot

    def setInterval(self, msecs):
        """
        Sets the interval in milliseconds for this timer.
        
        :param      msecs | <int>
        """
        self.__lock.lockForWrite()
        self.__interval = msecs
        self.__lock.unlock()

    def setSingleShot(self, state):
        """
        Sets whether or not this timer is setup for a single entry or not.
        
        :param      state | <bool>
        """
        self.__lock.lockForWrite()
        self.__singleShot = state
        self.__lock.unlock()

    def start(self, interval=None):
        """
        Emits the start requested signal for this timer, effectively starting
        its internal timer.
        """
        if interval is not None:
            self.setInterval(interval)
        
        self.__lock.lockForWrite()
        if self.__active:
            self.__lock.unlock()
            return
        else:
            self.__active = True
            self.__lock.unlock()
        
        QtCore.QTimer.singleShot(self.interval(), self.trigger)

    def stop(self):
        """
        Emits the stop requested signal for this timer, effectivly stopping its
        internal timer.
        """
        self.__lock.lockForWrite()
        self.__active = False
        self.__lock.unlock()

    def trigger(self):
        """
        Emits the timeout signal, provided this timer is still active.
        """
        # triggers the signal
        self.__lock.lockForRead()
        if not self.__active:
            return
        reify = not self.__singleShot
        self.__lock.unlock()
        
        try:
            self.timeout.emit()
        
        except StandardError:
            # reset the active flag
            self.__lock.lockForWrite()
            self.__active = False
            self.__lock.unlock()
            raise
        
        if reify:
            QtCore.QTimer.singleShot(self.interval(), self.trigger)

    singleShot = QtCore.QTimer.singleShot

