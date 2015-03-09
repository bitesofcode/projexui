#!/usr/bin/python

""" Defines a generic widget to handle popup controls. """

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

from projex.text import nativestring

from projexui.qt import Property
from projexui.qt.QtGui import QPushButton, QLabel

class XPushButton(QPushButton):
    def __init__(self, *args, **kwds):
        super(XPushButton, self).__init__(*args, **kwds)
        
        # sets whether or not this button will display rich text
        self._showRichText  = False
        self._richTextLabel = None
        self._text          = ''
    
    def eventFilter(self, object, event):
        """
        Ignore all events for the text label.
        
        :param      object | <QObject>
                    event  | <QEvent>
        """
        if object == self._richTextLabel:
            if event.type() in (event.MouseButtonPress,
                                event.MouseMove,
                                event.MouseButtonRelease,
                                event.MouseButtonDblClick):
                event.ignore()
                return True
        return False
    
    def resizeEvent(self, event):
        """
        Overloads the resize event to auto-resize the rich text label to the
        size of this QPushButton.
        
        :param      event | <QResizeEvent>
        """
        super(XPushButton, self).resizeEvent(event)
        
        if self._richTextLabel:
            self._richTextLabel.resize(event.size())
        
    def richTextLabel(self):
        """
        Returns the label that is used for drawing the rich text to this button.
        
        :return     <QLabel>
        """
        if not self._richTextLabel:
            self._richTextLabel = QLabel(self)
            self._richTextLabel.installEventFilter(self)
            self._richTextLabel.setMargin(10)
        return self._richTextLabel
    
    def setShowRichText(self, state):
        """
        Sets whether or not to display rich text for this button.
        
        :param      state | <bool>
        """
        self._showRichText = state
        text = self.text()
        
        if state:
            label = self.richTextLabel()
            label.setText(text)
            label.show()
            super(XPushButton, self).setText('')
        else:
            if self._richTextLabel:
                self._richTextLabel.hide()
            
            super(XPushButton, self).setText(text)
    
    def setText(self, text):
        """
        Sets the text for this button.  If it is set to show rich text, then
        it will update the label text, leaving the root button text blank, 
        otherwise it will update the button.
        
        :param      text | <str>
        """
        self._text = nativestring(text)
        if self.showRichText():
            self.richTextLabel().setText(text)
        else:
            super(XPushButton, self).setText(text)
    
    def showRichText(self):
        """
        Returns whether or not rich text is visible for this button.
        
        :return     <bool>
        """
        return self._showRichText
    
    def text(self):
        """
        Returns the source text for this button.
        
        :return     <str>
        """
        return self._text

    x_showRichText = Property(bool, showRichText, setShowRichText)

__designer_plugins__ = [XPushButton]