#!/usr/bin/python

""" Defines a Time Delta widget. """

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

import os.path
from projexui.qt.QtGui import QFrame,\
                              QComboBox,\
                              QHBoxLayout,\
                              QSpinBox,\
                              QPalette,\
                              QSizePolicy

from projexui import resources

COMBO_STYLE = """\
QComboBox {border: none;}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 16px;
    border: none;
}
QComboBox::down-arrow {image: url("%s");}
QComboBox::down-arrow:hover { background: palette(Mid); }
""" % resources.find('img/treeview/triangle_down.png').replace('\\', '/')

class XTimeDeltaEdit(QFrame):
    def __init__(self, parent=None):
        super(XTimeDeltaEdit, self).__init__(parent)
        
        # define custom properties
        self.setStyleSheet(COMBO_STYLE)
        
        self._numberSpinner = QSpinBox(self)
        self._numberSpinner.setRange(0, 100000)
        self._numberSpinner.setFrame(False)
        self._numberSpinner.setButtonSymbols(QSpinBox.NoButtons)
        self._numberSpinner.setSizePolicy(QSizePolicy.Expanding,
                                          QSizePolicy.Expanding)
        
        self._unitCombo = QComboBox(self)
        self._unitCombo.setEditable(True)
        self._unitCombo.setInsertPolicy(QComboBox.NoInsert)
        self._unitCombo.setFrame(False)
        self._unitCombo.addItems(['year(s)',
                                  'month(s)',
                                  'week(s)',
                                  'day(s)',
                                  'hour(s)',
                                  'minute(s)',
                                  'second(s)'])
        
        self._unitCombo.setCurrentIndex(3)
        self._unitCombo.setSizePolicy(QSizePolicy.Expanding,
                                      QSizePolicy.Expanding)
        
        self._directionCombo = QComboBox(self)
        self._directionCombo.addItems(['ago', 'from now'])
        self._directionCombo.setEditable(True)
        self._directionCombo.setInsertPolicy(QComboBox.NoInsert)
        self._directionCombo.setFrame(False)
        self._directionCombo.setSizePolicy(QSizePolicy.Expanding,
                                           QSizePolicy.Expanding)
        
        # setup ui
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Sunken)
        self.setBackgroundRole(QPalette.Base)
        self.setAutoFillBackground(True)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        layout.addWidget(self._numberSpinner)
        layout.addWidget(self._unitCombo)
        layout.addWidget(self._directionCombo)
        self.setLayout(layout)
        
    def delta(self):
        """
        Returns a delta based on this widget's information.
        
        :return     <datetime.timedelta>
        """
        number      = self._numberSpinner.value()
        unit        = self._unitCombo.currentText()
        direction   = self._directionCombo.currentText()
        
        # use past tense
        if direction == 'ago':
            number = -number
        
        if unit == 'year(s)':
            return datetime.timedelta(number * 365)
        elif unit == 'month(s)':
            return datetime.timedelta(number * 30)
        elif unit == 'week(s)':
            return datetime.timedelta(number * 7)
        elif unit == 'day(s)':
            return datetime.timedelta(number)
        elif unit == 'hour(s)':
            return datetime.timedelta(0, number * 3600)
        elif unit == 'minute(s)':
            return datetime.timedelta(0, number * 60)
        else:
            return datetime.timedelta(0, number)
    
    def setDelta(self, delta):
        """
        Sets the time delta for this widget to the inputed delta.
        
        :param      delta | <datetime.timedelta>
        """
        days = int(delta.days)
        secs = int(delta.total_seconds())
        
        direction = 'from now'
        if secs < 0:
            direction = 'ago'
        
        if days and days % 365 == 0:
            number = days / 365
            unit = 'year(s)'
        elif days and days % 30 == 0:
            number = days / 30
            unit = 'month(s)'
        elif days and days % 7 == 0:
            number = days / 7
            unit = 'week(s)'
        elif days:
            number = days
            unit = 'day(s)'
        elif secs % 3600 == 0:
            number = secs / 3600
            unit = 'hour(s)'
        elif secs % 60 == 0:
            number = secs / 60
            unit = 'minute(s)'
        else:
            number = secs
            unit = 'second(s)'
        
        self._numberSpinner.setValue(abs(int(number)))
        self._unitCombo.setCurrentIndex(self._unitCombo.findText(unit))
        index = self._directionCombo.findText(direction)
        self._directionCombo.setCurrentIndex(index)

__designer_plugins__ = [XTimeDeltaEdit]