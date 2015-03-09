""" Defines a help button class for the tool. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

import datetime
import os

from xqt import QtCore, QtGui

from projexui import resources

class XTimerLabel(QtGui.QLabel):
    __designer_group__ = 'ProjexUI'
    __designer_icon__ = resources.find('img/clock.png')

    ticked = QtCore.Signal()
    timeout = QtCore.Signal()

    def __init__(self, parent=None):
        super(XTimerLabel, self).__init__(parent)

        # create custom properties
        self._countdown = False
        self._starttime = None
        self._limit = 0
        self._elapsed = datetime.timedelta()
        self._delta = datetime.timedelta()
        self._format = '%(hours)02i:%(minutes)02i:%(seconds)02i'
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(500)
        
        # set the font for this instance to the inputed font
        font = self.font()
        font.setPointSize(12)
        self.setFont(font)

        # set default properties
        self.reset()
        self._timer.timeout.connect(self.increment)

    def countdown(self):
        """
        Returns whether or not this widget should display seconds as a
        countdown.
        
        :return     <bool>
        """
        return self._countdown

    def elapsed(self):
        """
        Returns the time delta from the beginning of the timer to now.

        :return     <datetime.timedelta>
        """
        return self._elapsed + self._delta

    def format(self):
        """
        Returns the format for the label that will be used for the timer
        display.

        :return     <str>
        """
        return self._format

    def hours(self):
        """
        Returns the elapsed number of hours for this timer.

        :return     <int>
        """
        seconds = self.elapsed().seconds
        if self.limit() and self.countdown():
            seconds = (self.limit() - self.elapsed().seconds)
        return seconds / 3600

    def increment(self):
        """
        Increments the delta information and refreshes the interface.
        """
        if self._starttime is not None:
            self._delta = datetime.datetime.now() - self._starttime
        else:
            self._delta = datetime.timedelta()
        
        self.refresh()
        self.ticked.emit()
    
    def interval(self):
        """
        Returns the number of milliseconds that this timer will run for.

        :return     <int>
        """
        return self._timer.interval()
        
    def isRunning(self):
        return self._timer.isActive()
        
    def limit(self):
        """
        Returns the limit for the amount of time to pass in seconds for this
        timer.  A limit of 0 would never timeout.  Otherwise, once the timer
        passes a certain number of seconds, then the timer will stop and the
        timeout signal will be emitted.
        
        :return     <int>
        """
        return self._limit

    def minutes(self):
        """
        Returns the elapsed number of minutes for this timer.

        :return     <int>
        """
        seconds = self.elapsed().seconds
        if self.limit() and self.countdown():
            seconds = (self.limit() - self.elapsed().seconds)
        return (seconds % 3600) / 60

    def refresh(self):
        """
        Updates the label display with the current timer information.
        """
        delta = self.elapsed()
        seconds = delta.seconds
        limit = self.limit()
        
        options = {}
        options['hours'] = self.hours()
        options['minutes'] = self.minutes()
        options['seconds'] = self.seconds()
        
        try:
            text = self.format() % options
        except ValueError:
            text = '#ERROR'

        self.setText(text)

        if limit and limit <= seconds:
            self.stop()
            self.timeout.emit()

    @QtCore.Slot()
    def reset(self):
        """
        Stops the timer and resets its values to 0.
        """
        self._elapsed = datetime.timedelta()
        self._delta = datetime.timedelta()
        self._starttime = datetime.datetime.now()
        
        self.refresh()

    @QtCore.Slot()
    def restart(self):
        """
        Resets the timer and then starts it again.
        """
        self.reset()
        self.start()

    def seconds(self):
        """
        Returns the elapsed number of seconds that this timer has been running.

        :return     <int>
        """
        seconds = self.elapsed().seconds
        if self.limit() and self.countdown():
            seconds = (self.limit() - self.elapsed().seconds)
        return (seconds % 3600) % 60

    def setCountdown(self, state):
        """
        Sets whether or not this widget should display the seconds as
        a countdown state.
        
        :param      state | <bool>
        """
        self._countdown = state
        self.refresh()

    def setLimit(self, limit):
        """
        Sets the number of seconds that this timer will process for.
        
        :param      limit | <int>
        """
        self._limit = limit
        self.refresh()

    def setFormat(self, format):
        """
        Sets the format for the label that will be used for the timer display.

        :param      format | <str>
        """
        self._format = str(format)
        self.refresh()

    def setInterval(self, interval):
        """
        Sets the number of milliseconds that this timer will run for.

        :param      interval | <int>
        """
        self._timer.setInterval(interval)

    @QtCore.Slot()
    def start(self):
        """
        Starts running the timer.  If the timer is currently running, then
        this method will do nothing.

        :sa     stop, reset
        """
        if self._timer.isActive():
            return

        self._starttime = datetime.datetime.now()
        self._timer.start()

    @QtCore.Slot()
    def stop(self):
        """
        Stops the timer.  If the timer is not currently running, then
        this method will do nothing.
        """
        if not self._timer.isActive():
            return

        self._elapsed += self._delta
        self._timer.stop()

    x_countdown = QtCore.Property(bool, countdown, setCountdown)
    x_limit = QtCore.Property(int, limit, setLimit)
    x_format = QtCore.Property(str, format, setFormat)
    x_interval = QtCore.Property(int, interval, setInterval)

__designer_plugins__ = [XTimerLabel]