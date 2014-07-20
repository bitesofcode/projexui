""" Creates an update to the standard QDateTimeEdit widget. """

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

from projexui.qt.QtCore import QDateTime
from projexui.qt.QtGui import QDateTimeEdit

class XDateTimeEdit(QDateTimeEdit):
    def __init__(self, parent=None):
        super(XDateTimeEdit, self).__init__(parent)
        
        # define custom properties
        self.setCalendarPopup(True)
        self.setDateTime(QDateTime.currentDateTime())

__designer_plugins__ = [XDateTimeEdit]