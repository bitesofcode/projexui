#!/usr/bin/python

"""
Extends the base XPopupButton to specifically handle Orb records and widgets.
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

#------------------------------------------------------------------------------

from projexui.qt import Signal

from projexui.widgets.xpopupbutton     import XPopupButton
from projexui.widgets.xorbrecordwidget import XOrbRecordWidget

class XOrbPopupButton(XPopupButton):
    __designer_group__ = 'ProjexUI - ORB'
    
    saved = Signal()
    
    def setCentralWidget(self, widget, createsNew=True, autoCommit=True):
        """
        Sets the central widget for this popup button.  If createsNew is set
        to True, then the about to show signal from the popup will be linked to
        the widget's reset slot.  If autoCommit is set to True, then the widget
        will commit it's information to the database.
        
        :param      widget | <prjexui.widgets.xorbrecordwidget.XOrbRecordWidget>
                    createsNew | <bool>
                    autoCommit | <boo>
        
        :return     <bool> | success
        """
        if not isinstance(widget, XOrbRecordWidget):
            return False
        
        # assign the widget
        super(XOrbPopupButton, self).setCentralWidget(widget)
        
        # setup widget options
        widget.setAutoCommitOnSave(autoCommit)
        
        # setup popup options
        popup = self.popupWidget()
        popup.setAutoCloseOnAccept(False)
        
        if createsNew and widget.multipleCreateEnabled():
            btn = popup.addButton('Save && Create Another')
            btn.clicked.connect(widget.saveSilent)
        
        # create connections
        popup.accepted.connect(widget.save)
        widget.saved.connect(popup.close)
        widget.saved.connect(self.saved)
        
        if createsNew:
            popup.aboutToShow.connect(widget.reset)
        
        return True
    
__designer_plugins__ = [XOrbPopupButton]