#!/usr/bin/python

""" Provides some additional options to the default QMessageBox. """

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

from projexui.qt.QtGui import QMessageBox,\
                              QPushButton,\
                              QSizePolicy,\
                              QLayout,\
                              QTextEdit

class XMessageBox(QMessageBox):
    def setVisible( self, state ):
        """
        Updates the visible state for this message box.
        
        :param      state | <bool>
        """
        super(XMessageBox, self).setVisible(state)
        
        if ( state ):
            self.startTimer(100)
            self.layout().setSizeConstraint(QLayout.SetNoConstraint)
            self.resize( self.width() + 100, self.height() )
    
    def setDetailedText( self, text ):
        """
        Sets the details text for this message box to the inputed text.  \
        Overloading the default method to support HTML details.
        
        :param      text | <str>
        """
        super(XMessageBox, self).setDetailedText(text)
        
        if ( text ):
            # update the text edit
            widgets = self.findChildren(QTextEdit)
            widgets[0].setLineWrapMode(QTextEdit.NoWrap)
            widgets[0].setHtml(text)
            widgets[0].setMaximumHeight(1000)
            widgets[0].setSizePolicy(QSizePolicy.Expanding, 
                                     QSizePolicy.Expanding)
            
            # update push button
            buttons = self.findChildren(QPushButton)
            for button in buttons:
                if ( button.text() == 'Show Details...' ):
                    button.clicked.connect( self.updateSizeMode )
                    break
    
    def updateSizeMode( self ):
        """
        Updates the resizing option when the user pushes a button.
        """
        self.startTimer(100)
    
    def timerEvent( self, event ):
        """
        Updates the min and max sizes to allow this message box to be resizable.
        
        :param      event | <QTimerEvent>
        """
        self.killTimer(event.timerId())
        
        self.setMaximumWidth(10000)
        self.setMaximumHeight(10000)
    
    @classmethod
    def detailedInformation( cls, parent, title, info, details, buttons = None ):
        """
        Creates a new information dialog with detailed information and \
        presents it to the user.
        
        :param      parent  | <QWidget>
                    title   | <str>
                    info    | <str>
                    details | <str>
                    buttons | <QMessageBox.StandardButton>
        
        :return     <QMessageBox.StandardButton>
        """
        if ( buttons == None ):
            buttons = XMessageBox.Ok
        
        dlg = cls(parent)
        dlg.setWindowTitle(title)
        dlg.setText(info)
        dlg.setDetailedText(details)
        dlg.setStandardButtons(buttons)
        dlg.exec_()
        
        return dlg.clickedButton()