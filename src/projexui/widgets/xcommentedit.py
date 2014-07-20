#!/usr/bin python

""" Defines a generic comments widget. """

# define authorship information
__authors__     = ['Eric Hulser']
__author__      = ','.join(__authors__)
__credits__     = []
__copyright__   = 'Copyright (c) 2011, Projex Software'

# maintanence information
__maintainer__  = 'Projex Software'
__email__       = 'team@projexsoftware.com'

import os.path

from projex.text import nativestring

from projexui.qt import Property, Signal, Slot
from projexui.qt.QtCore import Qt, QSize
from projexui.qt.QtGui import QToolBar,\
                              QPushButton,\
                              QSizePolicy,\
                              QWidget,\
                              QToolButton,\
                              QIcon,\
                              QFileDialog

from projexui import resources
from projexui.widgets.xtextedit import XTextEdit
from projexui.widgets.xmultitagedit import XMultiTagEdit

class XCommentEdit(XTextEdit):
    attachmentRequested = Signal()
    
    def __init__(self, parent=None):
        super(XCommentEdit, self).__init__(parent)
        
        # define custom properties
        self._attachments = {}
        self._showAttachments = True
        
        # create toolbar
        self._toolbar = QToolBar(self)
        self._toolbar.setMovable(False)
        self._toolbar.setFixedHeight(30)
        self._toolbar.setAutoFillBackground(True)
        self._toolbar.setFocusProxy(self)
        self._toolbar.hide()
        
        # create toolbar buttons
        self._attachButton = QToolButton(self)
        self._attachButton.setIcon(QIcon(resources.find('img/attach.png')))
        self._attachButton.setToolTip('Add Attachment')
        self._attachButton.setAutoRaise(True)
        self._attachButton.setIconSize(QSize(24, 24))
        self._attachButton.setFixedSize(26, 26)
        
        self._submitButton = QPushButton(self)
        self._submitButton.setText('Submit')
        self._submitButton.setFocusProxy(self)
        
        # create attachments widget
        self._attachmentsEdit = XMultiTagEdit(self)
        self._attachmentsEdit.setAutoResizeToContents(True)
        self._attachmentsEdit.setFrameShape(XMultiTagEdit.NoFrame)
        self._attachmentsEdit.setViewMode(XMultiTagEdit.ListMode)
        self._attachmentsEdit.setEditable(False)
        self._attachmentsEdit.setFocusProxy(self)
        self._attachmentsEdit.hide()
        
        # define toolbar layout
        spacer = QWidget(self)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        self._attachAction = self._toolbar.addWidget(self._attachButton)
        self._toolbar.addWidget(spacer)
        self._toolbar.addWidget(self._submitButton)
        
        # set standard properties
        self.setAutoResizeToContents(True)
        self.setHint('add comment')
        self.setFocusPolicy(Qt.StrongFocus)
        self.setRequireShiftForNewLine(True)
        
        # create connections
        self._attachButton.clicked.connect(self.attachmentRequested)
        self._submitButton.clicked.connect(self.acceptText)
        self._attachmentsEdit.tagRemoved.connect(self.removeAttachment)
        self.focusChanged.connect(self.setToolbarVisible)
    
    def addAttachment(self, title, attachment):
        """
        Adds an attachment to this comment.
        
        :param      title      | <str>
                    attachment | <variant>
        """
        self._attachments[title] = attachment
        self.resizeToContents()
    
    def attachments(self):
        """
        Returns a list of attachments that have been linked to this widget.
        
        :return     {<str> title: <variant> attachment, ..}
        """
        return self._attachments.copy()
    
    def attachButton(self):
        """
        Returns the attach button from the toolbar for this widget.
        
        :return     <QToolButton>
        """
        return self._attachButton
    
    @Slot()
    def clear(self):
        """
        Clears out this widget and its attachments.
        """
        # clear the attachment list
        self._attachments.clear()
        
        super(XCommentEdit, self).clear()
    
    def isToolbarVisible(self):
        """
        Returns whether or not the toolbar for this comment edit is currently
        visible to the user.
        
        :return     <bool>
        """
        return self._toolbar.isVisible()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.clear()
            event.accept()
        else:
            super(XCommentEdit, self).keyPressEvent(event)
    
    @Slot()
    def pickAttachment(self):
        """
        Prompts the user to select an attachment to add to this edit.
        """
        filename = QFileDialog.getOpenFileName(self.window(),
                                               'Select Attachment',
                                               '',
                                               'All Files (*.*)')
        
        if type(filename) == tuple:
            filename = nativestring(filename[0])
        
        filename = nativestring(filename)
        if filename:
            self.addAttachment(os.path.basename(filename), filename)
    
    def removeAttachment(self, title):
        """
        Removes the attachment from the given title.
        
        :param      title | <str>
        
        :return     <variant> | attachment
        """
        attachment = self._attachments.pop(nativestring(title), None)
        
        if attachment:
            self.resizeToContents()
        
        return attachment
    
    def resizeEvent(self, event):
        super(XCommentEdit, self).resizeEvent(event)
        
        self._toolbar.resize(self.width() - 4, 30)
        edit = self._attachmentsEdit
        edit.resize(self.width() - 4, edit.height())
    
    def resizeToContents(self):
        """
        Resizes this toolbar based on the contents of its text.
        """
        if self._toolbar.isVisible():
            doc = self.document()
            h = doc.documentLayout().documentSize().height()
            
            offset = 34
            
            # update the attachments edit
            edit = self._attachmentsEdit
            if self._attachments:
                edit.move(2, self.height() - edit.height() - 31)
                edit.setTags(sorted(self._attachments.keys()))
                edit.show()
                
                offset = 34 + edit.height()
            else:
                edit.hide()
                offset = 34
            
            self.setFixedHeight(h + offset)
            self._toolbar.move(2, self.height() - 32)
        else:
            super(XCommentEdit, self).resizeToContents()
    
    def setAttachments(self, attachments):
        """
        Sets the attachments for this widget to the inputed list of attachments.
        
        :param      attachments | {<str> title: <variant> attachment, ..}
        """
        self._attachments = attachments
        self.resizeToContents()
    
    def setSubmitText(self, text):
        """
        Sets the submission text for this edit.
        
        :param      text | <str>
        """
        self._submitButton.setText(text)

    def setShowAttachments(self, state):
        """
        Sets whether or not to show the attachments for this edit.
        
        :param      state | <bool>
        """
        self._showAttachments = state
        self._attachAction.setVisible(state)

    def setToolbarVisible(self, state):
        """
        Sets whether or not the toolbar is visible.
        
        :param      state | <bool>
        """
        self._toolbar.setVisible(state)
        
        self.resizeToContents()
    
    def showAttachments(self):
        """
        Returns whether or not to show the attachments for this edit.
        
        :return     <bool>
        """
        return self._showAttachments
    
    def submitButton(self):
        """
        Returns the submit button for this edit.
        
        :return     <QPushButton>
        """
        return self._submitButton
    
    def submitText(self):
        """
        Returns the submission text for this edit.
        
        :return     <str>
        """
        return self._submitButton.text()

    def toolbar(self):
        """
        Returns the toolbar widget for this comment edit.
        
        :return     <QToolBar>
        """
        return self._toolbar
    
    x_showAttachments = Property(bool, showAttachments, setShowAttachments)
    x_submitText = Property(str, submitText, setSubmitText)

__designer_plugins__ = [XCommentEdit]