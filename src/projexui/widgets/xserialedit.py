#!/usr/bin/python

""" Defines an editor that links multiple line edits together in succession. """

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

import string
from projex.text import nativestring

from projexui.qt import Property, Signal, Slot, QtGui, QtCore
from projexui.widgets.xlineedit import XLineEdit

class XSerialEdit(QtGui.QWidget):
    returnPressed = Signal()
    
    def __init__(self, parent=None):
        super(XSerialEdit, self).__init__(parent)
        
        # define custom properties
        self._sectionLength = 5
        self._readOnly = False
        self._editorHandlingBlocked = False
        
        # set standard values
        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.setLayout(layout)
        self.setSectionCount(4)
        self.setSizePolicy(QtGui.QSizePolicy.Expanding,
                           QtGui.QSizePolicy.Fixed)
        
    
    def blockEditorHandling(self, state):
        self._editorHandlingBlocked = state
    
    def clearSelection(self):
        """
        Clears the selected text for this edit.
        """
        first = None
        editors = self.editors()
        for editor in editors:
            if not editor.selectedText():
               continue
            
            first = first or editor
            editor.backspace()
        
        for editor in editors:
            editor.setFocus()
        
        if first:
            first.setFocus()
    
    @Slot()
    def copyAll(self):
        """
        Copies all of the text to the clipboard.
        """
        QtGui.QApplication.clipboard().setText(self.text())
    
    @Slot()
    def copy(self):
        """
        Copies the text from the serial to the clipboard.
        """
        QtGui.QApplication.clipboard().setText(self.selectedText())

    @Slot()
    def cut(self):
        """
        Cuts the text from the serial to the clipboard.
        """
        text = self.selectedText()
        for editor in self.editors():
            editor.cut()
        
        QtGui.QApplication.clipboard().setText(text)

    def currentEditor(self):
        """
        Returns the current editor or this widget based on the focusing.
        
        :return     <QtGui.QLineEdit>
        """
        for editor in self.editors():
            if editor.hasFocus():
                return editor
        return None

    def editors(self):
        """
        Returns the editors that are associated with this edit.
        
        :return     [<XLineEdit>, ..]
        """
        lay = self.layout()
        return [lay.itemAt(i).widget() for i in range(lay.count())]

    def editorAt(self, index):
        """
        Returns the editor at the given index.
        
        :param      index | <int>
        
        :return     <XLineEdit> || None
        """
        try:
            return self.layout().itemAt(index).widget()
        except AttributeError:
            return None

    def eventFilter(self, object, event):
        """
        Filters the events for the editors to control how the cursor
        flows between them.
        
        :param      object | <QtCore.QObject>
                    event  | <QtCore.QEvent>

        :return     <bool> | consumed
        """
        index = self.indexOf(object)
        pressed = event.type() == event.KeyPress
        released = event.type() == event.KeyRelease
        
        if index == -1 or \
           not (pressed or released) or \
           self.isEditorHandlingBlocked():
            return super(XSerialEdit, self).eventFilter(object, event)
        
        text = nativestring(event.text()).strip()
        
        # handle Ctrl+C (copy)
        if event.key() == QtCore.Qt.Key_C and \
           event.modifiers() == QtCore.Qt.ControlModifier and \
           pressed:
            self.copy()
            return True
        
        # handle Ctrl+X (cut)
        elif event.key() == QtCore.Qt.Key_X and \
             event.modifiers() == QtCore.Qt.ControlModifier and \
             pressed:
            if not self.isReadOnly():
                self.cut()
            return True
        
        # handle Ctrl+A (select all)
        elif event.key() == QtCore.Qt.Key_A and \
             event.modifiers() == QtCore.Qt.ControlModifier and \
             pressed:
            self.selectAll()
            return True
        
        # handle Ctrl+V (paste)
        elif event.key() == QtCore.Qt.Key_V and \
             event.modifiers() == QtCore.Qt.ControlModifier and \
             pressed:
            if not self.isReadOnly():
                self.paste()
            return True
        
        # ignore tab movements
        elif event.key() in (QtCore.Qt.Key_Tab, QtCore.Qt.Key_Backtab):
            pass
        
        # delete all selected text
        elif event.key() == QtCore.Qt.Key_Backspace:
            sel_text = self.selectedText()
            if sel_text and not self.isReadOnly():
                self.clearSelection()
                return True
        
        # ignore modified keys
        elif not released:
            return super(XSerialEdit, self).eventFilter(object, event)
        
        # move to the previous editor
        elif object.cursorPosition() == 0:
            if event.key() in (QtCore.Qt.Key_Backspace, QtCore.Qt.Key_Left):
                self.goBack()
        
        # move to next editor
        elif object.cursorPosition() == object.maxLength():
            valid_chars = string.ascii_letters + string.digits
            valid_text = text != '' and text in valid_chars
            
            if valid_text or event.key() == QtCore.Qt.Key_Right:
                self.goForward()
        
        return super(XSerialEdit, self).eventFilter(object, event)

    def goBack(self):
        """
        Moves the cursor to the end of the previous editor
        """
        index = self.indexOf(self.currentEditor())
        if index == -1:
            return
        
        previous = self.editorAt(index - 1)
        if previous:
            previous.setFocus()
            previous.setCursorPosition(self.sectionLength())
        
    def goForward(self):
        """
        Moves the cursor to the beginning of the next editor.
        """
        index = self.indexOf(self.currentEditor())
        if index == -1:
            return
        
        next = self.editorAt(index + 1)
        if next:
            next.setFocus()
            next.setCursorPosition(0)

    def hint(self):
        """
        Returns the hint that is used for the editors in this widget.
        
        :return     <str>
        """
        texts = []
        for editor in self.editors():
            text = editor.hint()
            if text:
                texts.append(nativestring(text))
        
        return ' '.join(texts)

    def indexOf(self, editor):
        """
        Returns the index of the inputed editor, or -1 if not found.
        
        :param      editor | <QtGui.QWidget>
        
        :return     <int>
        """
        lay = self.layout()
        for i in range(lay.count()):
            if lay.itemAt(i).widget() == editor:
                return i
        return -1

    def isEditorHandlingBlocked(self):
        return self._editorHandlingBlocked

    def isReadOnly(self):
        """
        Returns whether or not this edit is readonly.
        
        :return     <bool>
        """
        return self._readOnly

    @Slot()
    def paste(self):
        """
        Pastes text from the clipboard into the editors.
        """
        self.setText(QtGui.QApplication.clipboard().text())
    
    def showEvent(self, event):
        for editor in self.editors():
            editor.setFont(self.font())
            
        super(XSerialEdit, self).showEvent(event)
    
    def sectionCount(self):
        """
        Returns the number of editors that are a part of this serial edit.
        
        :return     <int>
        """
        return self.layout().count()
    
    def sectionLength(self):
        """
        Returns the number of characters available for each editor.
        
        :return     <int>
        """
        return self._sectionLength
    
    def selectedText(self):
        """
        Returns the selected text from the editors.
        
        :return     <str>
        """
        texts = []
        for editor in self.editors():
            text = editor.selectedText()
            if text:
                texts.append(nativestring(text))
        
        return ' '.join(texts)
    
    @Slot()
    def selectAll(self):
        """
        Selects the text within all the editors.
        """
        self.blockEditorHandling(True)
        for editor in self.editors():
            editor.selectAll()
        self.blockEditorHandling(False)
    
    def setHint(self, text):
        """
        Sets the hint to the inputed text.   The same hint will be used for
        all editors in this widget.
        
        :param      text | <str>
        """
        texts = nativestring(text).split(' ')
        
        for i, text in enumerate(texts):
            editor = self.editorAt(i)
            if not editor:
                break
            
            editor.setHint(text)

    def setReadOnly(self, state):
        """
        Sets whether or not this edit is read only.
        
        :param      state | <bool>
        """
        self._readOnly = state
        
        for editor in self.editors():
            editor.setReadOnly(state)

    def setSectionCount(self, count):
        """
        Sets the number of editors that the serial widget should have.
        
        :param      count | <int>
        """
        # cap the sections at 10
        count = max(1, min(count, 10))
        
        # create additional editors
        while self.layout().count() < count:
            editor = XLineEdit(self)
            editor.setFont(self.font())
            editor.setReadOnly(self.isReadOnly())
            editor.setHint(self.hint())
            editor.setAlignment(QtCore.Qt.AlignCenter)
            editor.installEventFilter(self)
            editor.setSizePolicy(QtGui.QSizePolicy.Expanding,
                                 QtGui.QSizePolicy.Expanding)
            editor.setMaxLength(self.sectionLength())
            editor.returnPressed.connect(self.returnPressed)
            self.layout().addWidget(editor)
        
        # remove unnecessary editors
        while count < self.layout().count():
            widget = self.layout().itemAt(0).widget()
            widget.close()
            widget.setParent(None)
            widget.deleteLater()

    def setSectionLength(self, length):
        """
        Sets the number of characters per section that are allowed.
        
        :param      length | <int>
        """
        self._sectionLength = length
        for editor in self.editors():
            editor.setMaxLength(length)

    @Slot()
    def setText(self, text):
        """
        Sets the text for this serial edit to the inputed text.
        
        :param      text | <str>
        """
        texts = nativestring(text).split(' ')
        
        for i, text in enumerate(texts):
            editor = self.editorAt(i)
            if not editor:
                break
            
            editor.setText(text)

    def text(self):
        """
        Returns the text from all the serials as text separated by a spacer.
        
        :return     <str>
        """
        texts = []
        for editor in self.editors():
            text = editor.text()
            if text:
                texts.append(nativestring(text))
        
        return ' '.join(texts)
    
    x_readOnly = Property(bool, isReadOnly, setReadOnly)
    x_sectionCount = Property(int, sectionCount, setSectionCount)
    x_sectionLength = Property(int, sectionLength, setSectionLength)
    x_hint = Property(str, hint, setHint)
    x_text = Property(str, text, setText)
    
__designer_plugins__ = [XSerialEdit]