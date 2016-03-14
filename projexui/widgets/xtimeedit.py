""" Creates an update to the standard QTimeEdit widget. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

#----------------------------------------------------------------------

from xqt import QtCore, QtGui

class XTimeEdit(QtGui.QWidget):
    def __init__(self, parent=None):
        super(XTimeEdit, self).__init__(parent)

        # define custom properties
        self._editable = False
        self._showSeconds = False
        self._showMinutes = True
        self._showHours = True
        self._militaryTime = False

        # define the ui
        self._hourCombo = QtGui.QComboBox(self)
        self._hourSeparator = QtGui.QLabel(':', self)
        self._minuteCombo = QtGui.QComboBox(self)
        self._minuteSeparator = QtGui.QLabel(':', self)
        self._secondCombo = QtGui.QComboBox(self)
        self._timeOfDayCombo = QtGui.QComboBox(self)

        self._secondCombo.hide()
        self._minuteSeparator.hide()

        # define default UI settings
        self._hourCombo.addItems(['{0}'.format(i+1) for i in xrange(12)])
        self._minuteCombo.addItems(['{0:02d}'.format(i) for i in xrange(0, 60, 5)])
        self._secondCombo.addItems(['{0:02d}'.format(i) for i in xrange(0, 60, 5)])
        self._timeOfDayCombo.addItems(['am', 'pm'])

        # setup combo properties
        for combo in (self._hourCombo, self._minuteCombo, self._secondCombo, self._timeOfDayCombo):
            combo.setInsertPolicy(combo.NoInsert)
            combo.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

        # layout the widgets
        h_layout = QtGui.QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)
        h_layout.addWidget(self._hourCombo)
        h_layout.addWidget(self._hourSeparator)
        h_layout.addWidget(self._minuteCombo)
        h_layout.addWidget(self._minuteSeparator)
        h_layout.addWidget(self._secondCombo)
        h_layout.addWidget(self._timeOfDayCombo)

        self.setLayout(h_layout)

        # assign the default time
        self.setTime(QtCore.QDateTime.currentDateTime().time())

    def isEditable(self):
        """
        Returns whether or not the combo boxes within the edit are editable.

        :return     <bool>
        """
        return self._editable

    def isMilitaryTime(self):
        """
        Returns whether or not the clock is in military (24 hour) mode.

        :return     <bool>
        """
        return self._militaryTime

    def setEditable(self, state):
        """
        Sets whether or not this combo box is editable.

        :param      state | <bool>
        """
        self._editable = state
        self._hourCombo.setEditable(state)
        self._minuteCombo.setEditable(state)
        self._secondCombo.setEditable(state)
        self._timeOfDayCombo.setEditable(state)

    def setFont(self, font):
        """
        Assigns the font to this widget and all of its children.

        :param      font | <QtGui.QFont>
        """
        super(XTimeEdit, self).setFont(font)

        # update the fonts for the time combos
        self._hourCombo.setFont(font)
        self._minuteCombo.setFont(font)
        self._secondCombo.setFont(font)
        self._timeOfDayCombo.setFont(font)

    def setMilitaryTime(self, state=True):
        """
        Sets whether or not this widget will be displayed in military time.  When in military time, the hour options
        will go from 01-24, when in normal mode, the hours will go 1-12.

        :param      state   | <bool>
        """
        time = self.time()

        self._militaryTime = state
        self._hourCombo.clear()

        if state:
            self._timeOfDayCombo.hide()
            self._hourCombo.addItems(['{0:02d}'.format(i+1) for i in xrange(24)])
        else:
            self._timeOfDayCombo.show()
            self._hourCombo.addItems(['{0}'.format(i+1) for i in xrange(12)])

        self.setTime(time)

    def setShowHours(self, state=True):
        """
        Sets whether or not to display the hours combo box for this widget.

        :param      state | <bool>
        """
        self._showHours = state
        if state:
            self._hourSeparator.show()
            self._hourCombo.show()
        else:
            self._hourSeparator.hide()
            self._hourCombo.hide()

    def setShowMinutes(self, state=True):
        """
        Sets whether or not to display the minutes combo box for this widget.

        :param      state | <bool>
        """
        self._showMinutes = state
        if state:
            self._minuteCombo.show()
        else:
            self._minuteCombo.hide()

    def setShowSeconds(self, state=True):
        """
        Sets whether or not to display the seconds combo box for this widget.

        :param      state | <bool>
        """
        self._showSeconds = state
        if state:
            self._minuteSeparator.show()
            self._secondCombo.show()
        else:
            self._minuteSeparator.hide()
            self._secondCombo.hide()

    def setTime(self, time):
        """
        Sets the current time for this edit.

        :param     time | <QtCore.QTime>
        """
        hour = time.hour()
        minute = time.minute()
        second = time.second()

        if not self.isMilitaryTime():
            if hour > 12:
                hour -= 12
                self._timeOfDayCombo.setCurrentIndex(1)
            else:
                self._timeOfDayCombo.setCurrentIndex(0)
            hour = str(hour)
        else:
            hour = '{0:02d}'.format(hour)

        nearest = lambda x: int(round(x/5.0)*5.0)

        self._hourCombo.setCurrentIndex(self._hourCombo.findText(hour))
        self._minuteCombo.setCurrentIndex(self._minuteCombo.findText('{0:02d}'.format(nearest(minute))))
        self._secondCombo.setCurrentIndex(self._secondCombo.findText('{0:02d}'.format(nearest(second))))

    def showHours(self):
        """
        Returns whether or not the hours combo should be visible.

        :return     <bool>
        """
        return self._showHours

    def showMinutes(self):
        """
        Returns whether or not the minutes combo should be visible.

        :return     <bool>
        """
        return self._showMinutes

    def showSeconds(self):
        """
        Returns whether or not the seconds combo should be visible.

        :return     <bool>
        """
        return self._showSeconds

    def time(self):
        """
        Returns the current time for this edit.

        :return     <QtCore.QTime>
        """
        if self.isMilitaryTime():
            format = 'hh:mm:ss'
            time_of_day = ''
        else:
            format = 'hh:mm:ssap'
            time_of_day = self._timeOfDayCombo.currentText().lower()

        try:
            hour = int(self._hourCombo.currentText()) if self.showHours() else 1
        except ValueError:
            hour = 1

        try:
            minute = int(self._minuteCombo.currentText()) if self.showMinutes() else 0
        except ValueError:
            minute = 0

        try:
            second = int(self._secondCombo.currentText()) if self.showSeconds() else 0
        except ValueError:
            second = 0

        combined = '{0:02}:{1:02}:{2:02}{3}'.format(hour, minute, second, time_of_day)
        return QtCore.QTime.fromString(combined, format)

    x_time = QtCore.Property(QtCore.QTime, time, setTime)
    x_militaryTime = QtCore.Property(bool, isMilitaryTime, setMilitaryTime)
    x_showHours = QtCore.Property(bool, showHours, setShowHours)
    x_showMinutes = QtCore.Property(bool, showMinutes, setShowMinutes)
    x_showSeconds = QtCore.Property(bool, showSeconds, setShowSeconds)

__designer_plugins__ = [XTimeEdit]
