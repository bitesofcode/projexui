#!/usr/bin/python

"""
Extends the base QToolButton class to support popup widgets.
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

from projexui.qt          import Signal
from projexui.qt.QtCore   import QPoint, Qt
from projexui.qt.QtGui    import QDialogButtonBox,\
                                 QApplication

from projexui.widgets.xtoolbutton import XToolButton
from projexui.widgets.xpopupwidget  import XPopupWidget

class XPopupButton(XToolButton):
    popupAboutToShow = Signal()
    popupAccepted    = Signal()
    popupRejected    = Signal()
    popupReset       = Signal()
    
    Anchor = XPopupWidget.Anchor
    
    def __init__(self, parent, buttons=None):
        super(XPopupButton, self).__init__(parent)
        
        # define custom options
        if buttons is None:
            buttons  = QDialogButtonBox.Reset
            buttons |= QDialogButtonBox.Save
            buttons |= QDialogButtonBox.Cancel
        
        self._popupWidget   = XPopupWidget(self, buttons)
        self._defaultAnchor = 0
        self._popupShown    = False
        
        self.setEnabled(False)
        
        # create connections
        self.clicked.connect(self.clickAction)
        self.triggered.connect(self.togglePopupOnAction)
        
        self._popupWidget.accepted.connect(self.popupAccepted)
        self._popupWidget.rejected.connect(self.popupRejected)
        self._popupWidget.resetRequested.connect(self.popupReset)
    
    def centralWidget(self):
        """
        Returns the central widget from this tool button
        """
        return self._popupWidget.centralWidget()
    
    def clickAction(self):
        """
        Calls the triggered signal if there is no action for this widget.
        """
        if not self.defaultAction():
            self.triggered.emit(None)
    
    def defaultAnchor(self):
        """
        Returns the default anchor for this popup widget.
        
        :return     <XPopupWidget.Anchor>
        """
        return self._defaultAnchor
    
    def hideEvent(self, event):
        super(XPopupButton, self).hideEvent(event)
        
        self._popupShown = self.popupWidget().isVisible()
        if self.popupWidget().currentMode() != XPopupWidget.Mode.Dialog:
            self.popupWidget().hide()
    
    def popupWidget(self):
        """
        Returns the popup widget for this button.
        
        :return     <XPopupWidget>
        """
        return self._popupWidget
    
    def setCentralWidget(self, widget):
        """
        Sets the central widget for this button.
        
        :param      widget | <QWidget>
        """
        self.setEnabled(widget is not None)
        self._popupWidget.setCentralWidget(widget)
    
    def setDefaultAnchor(self, anchor):
        """
        Sets the default anchor for the popup on this button.
        
        :param      anchor | <XPopupWidget.Anchor>
        """
        self._defaultAnchor = anchor
    
    def showEvent(self, event):
        super(XPopupButton, self).showEvent(event)
        
        if self._popupShown and \
           self.popupWidget().currentMode() != XPopupWidget.Mode.Dialog:
            self.showPopup()
    
    def showPopupOnAction(self, action):
        """
        Shows the popup if the action is the current default action.
        
        :param      action | <QAction>
        """
        if ( action == self.defaultAction() ):
            self.showPopup()
    
    def showPopup(self):
        """
        Shows the popup for this button.
        """
        as_dialog = QApplication.keyboardModifiers()
        
        anchor = self.defaultAnchor()
        if anchor:
            self.popupWidget().setAnchor(anchor)
        else:
            anchor = self.popupWidget().anchor()
        
        if ( anchor & (XPopupWidget.Anchor.BottomLeft |
                       XPopupWidget.Anchor.BottomCenter |
                       XPopupWidget.Anchor.BottomRight) ):
            pos = QPoint(self.width() / 2, 0)
        else:
            pos = QPoint(self.width() / 2, self.height())
        
        pos = self.mapToGlobal(pos)
        
        if not self.signalsBlocked():
            self.popupAboutToShow.emit()
        self._popupWidget.popup(pos)
        
        if as_dialog:
            self._popupWidget.setCurrentMode(XPopupWidget.Mode.Dialog)
    
    def togglePopup(self):
        """
        Toggles whether or not the popup is visible.
        """
        if not self._popupWidget.isVisible():
            self.showPopup()
        elif self._popupWidget.currentMode() != self._popupWidget.Mode.Dialog:
            self._popupWidget.close()
    
    def togglePopupOnAction( self, action ):
        """
        Toggles the popup if the action is the current default action.
        
        :param      action | <QAction>
        """
        if action in (None, self.defaultAction()):
            self.togglePopup()

__designer_plugins__ = [XPopupButton]