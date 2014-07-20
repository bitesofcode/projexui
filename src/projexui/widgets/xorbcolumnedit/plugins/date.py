""" Defines the different plugins that will be used for this widget. """

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

import datetime

from orb import ColumnType
from projexui.widgets.xorbcolumnedit import plugins

from projexui.qt.QtCore import QDate, QTime, QDateTime

from projexui.qt.QtGui import QDateEdit,\
                              QTimeEdit,\
                              QDateTimeEdit

#------------------------------------------------------------------------------

class DatetimeEdit(QDateTimeEdit):
    def __init__( self, parent ):
        super(DatetimeEdit, self).__init__(parent)
        
        self.setCalendarPopup(True)
    
    def setValue( self, value ):
        self.setDateTime(QDateTime(value))
    
    def value( self ):
        return self.dateTime().toPyDateTime()

#------------------------------------------------------------------------------

class DateEdit(QDateEdit):
    def __init__( self, parent ):
        super(DateEdit, self).__init__(parent)
        
        self.setCalendarPopup(True)
    
    def setValue( self, value ):
        self.setDate(QDate(value))
    
    def value( self ):
        return self.date().toPyDate()

#------------------------------------------------------------------------------

class TimeEdit(QTimeEdit):
    def setValue( self, value ):
        self.setTime(QTime(value))
    
    def value( self ):
        return self.time().toPyTime()

#------------------------------------------------------------------------------

plugins.widgets[ColumnType.Datetime] = DatetimeEdit
plugins.widgets[ColumnType.Date]     = DateEdit
plugins.widgets[ColumnType.Time]     = TimeEdit