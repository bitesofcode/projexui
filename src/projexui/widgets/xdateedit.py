""" Creates an update to the standard QDateEdit widget. """

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

from projexui.qt.QtCore import QDate
from projexui.qt.QtGui import QDateEdit

class XDateEdit(QDateEdit):
    def __init__(self, parent=None):
        super(XDateEdit, self).__init__(parent)
        
        # define custom properties
        self.setCalendarPopup(True)
        self.setDate(QDate.currentDate())

__designer_plugins__ = [XDateEdit]