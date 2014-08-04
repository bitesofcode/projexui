#!/usr/bin python
# -*- coding=utf-8

""" Defines a more robust tab widget. """

# define authorship information
__authors__     = ['Eric Hulser']
__author__      = ','.join(__authors__)
__credits__     = []
__copyright__   = 'Copyright (c) 2011, Projex Software'

# maintanence information
__maintainer__  = 'Projex Software'
__email__       = 'team@projexsoftware.com'

from projexui.qt import Property, Slot, Signal
from projexui.qt.QtCore import Qt
from projexui.qt.QtGui import QTextEdit,\
                              QColor,\
                              QApplication,\
                              QDialog,\
                              QVBoxLayout,\
                              QLabel,\
                              QDialogButtonBox

import projex.text
from projexui.xpainter import XPainter

class XTextEdit(QTextEdit):
    focusEntered = Signal()
    focusChanged = Signal(bool)
    focusExited = Signal()
    returnPressed = Signal()
    textEntered = Signal(str)
    htmlEntered = Signal(str)
    
    def __init__(self, parent=None):
        super(XTextEdit, self).__init__(parent)
        
        # define custom properties
        self._autoResizeToContents = False
        self._hint = ''
        self._encoding = 'utf-8'
        self._tabsAsSpaces = False
        self._requireShiftForNewLine = False
        self._richTextEditEnabled = True
        
        palette = self.palette()
        self._hintColor = palette.color(palette.AlternateBase).darker(130)
    
    def acceptText(self):
        """
        Emits the editing finished signals for this widget.
        """
        if not self.signalsBlocked():
            self.textEntered.emit(self.toPlainText())
            self.htmlEntered.emit(self.toHtml())
            self.returnPressed.emit()
    
    def autoResizeToContents(self):
        """
        Returns whether or not this text edit should automatically resize
        itself to fit its contents.
        
        :return     <bool>
        """
        return self._autoResizeToContents
    
    @Slot()
    def clear(self):
        """
        Clears the text for this edit and resizes the toolbar information.
        """
        super(XTextEdit, self).clear()
        
        self.textEntered.emit('')
        self.htmlEntered.emit('')
        
        if self.autoResizeToContents():
            self.resizeToContents()
    
    def encoding(self):
        """
        Returns the encoding format that will be used for this text edit.  All
        text that is pasted into this edit will be automatically converted
        to this format.
        
        :return     <str>
        """
        return self._encoding
    
    def focusInEvent(self, event):
        """
        Processes when this widget recieves focus.
        
        :param      event | <QFocusEvent>
        """
        if not self.signalsBlocked():
            self.focusChanged.emit(True)
            self.focusEntered.emit()
        
        return super(XTextEdit, self).focusInEvent(event)
    
    def focusOutEvent(self, event):
        """
        Processes when this widget loses focus.
        
        :param      event | <QFocusEvent>
        """
        if not self.signalsBlocked():
            self.focusChanged.emit(False)
            self.focusExited.emit()
        
        return super(XTextEdit, self).focusOutEvent(event)
    
    def hint( self ):
        """
        Returns the hint that will be rendered for this tree if there are no
        items defined.
        
        :return     <str>
        """
        return self._hint
    
    def hintColor( self ):
        """
        Returns the color used for the hint rendering.
        
        :return     <QColor>
        """
        return self._hintColor
    
    def isRichTextEditEnabled(self):
        """
        Returns whether or not this widget should accept rich text or not.
        
        :return     <bool>
        """
        return self._richTextEditEnabled
    
    def keyPressEvent(self, event):
        """
        Processes user input when they enter a key.
        
        :param      event | <QKeyEvent>
        """
        # emit the return pressed signal for this widget
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and \
           event.modifiers() == Qt.ControlModifier:
            self.acceptText()
            event.accept()
            return
        
        elif event.key() == Qt.Key_Tab:
            if self.tabsAsSpaces():
                count = 4 - (self.textCursor().columnNumber() % 4)
                self.insertPlainText(' ' * count)
                event.accept()
                return
        
        elif event.key() == Qt.Key_V and event.modifiers() == Qt.ControlModifier:
            self.paste()
            event.accept()
            return
        
        super(XTextEdit, self).keyPressEvent(event)
        
        if self.autoResizeToContents():
            self.resizeToContents()
    
    def paintEvent(self, event):
        """
        Overloads the paint event to support rendering of hints if there are
        no items in the tree.
        
        :param      event | <QPaintEvent>
        """
        super(XTextEdit, self).paintEvent(event)
        
        if self.document().isEmpty() and self.hint():
            text    = self.hint()
            rect    = self.rect()
            
            # modify the padding on the rect
            rect.setX(4)
            rect.setY(4)
            align = int(Qt.AlignLeft | Qt.AlignTop)
            
            # setup the coloring options
            clr = self.hintColor()
            
            # paint the hint
            with XPainter(self.viewport()) as painter:
                painter.setPen(clr)
                painter.drawText(rect, align | Qt.TextWordWrap, text)
    
    @Slot()
    def paste(self):
        """
        Pastes text from the clipboard into this edit.
        """
        html = QApplication.clipboard().text()
        if not self.isRichTextEditEnabled():
            self.insertPlainText(projex.text.toAscii(html))
        else:
            super(XTextEdit, self).paste()
    
    def requireShiftForNewLine(self):
        """
        Returns whether or not the shift modifier is required for new lines.
        When this is True, then Return/Enter key presses will not create
        new lines in the edit, but instead trigger the returnPressed,
        textEntered and htmlEntered signals.
        
        :return     <bool>
        """
        return self._requireShiftForNewLine
    
    def resizeEvent(self, event):
        """
        Processes when this edit has been resized.
        
        :param      event | <QResizeEvent>
        """
        super(XTextEdit, self).resizeEvent(event)
        
        if self.autoResizeToContents():
            self.resizeToContents()
    
    @Slot()
    def resizeToContents(self):
        """
        Resizes this widget to fit the contents of its text.
        """
        doc = self.document()
        h = doc.documentLayout().documentSize().height()
        self.setFixedHeight(h + 4)
    
    def setAutoResizeToContents(self, state):
        """
        Sets whether or not this text edit should automatically resize itself
        to fit its contents.
        
        :param      state | <bool>
        """
        self._autoResizeToContents = state
        if state:
            self.resizeToContents()
    
    def setEncoding(self, encoding):
        """
        Sets the encoding format that will be used for this text edit.  All
        text that is pasted into this edit will be automatically converted
        to this format.
        
        :param      encoding | <str>
        """
        self._encoding = encoding
    
    def setHint(self, hint):
        """
        Sets the hint text that will be rendered when no items are present.
        
        :param      hint | <str>
        """
        self._hint = hint
    
    def setHintColor(self, color):
        """
        Sets the color used for the hint rendering.
        
        :param      color | <QColor>
        """
        self._hintColor = QColor(color)
    
    def setRequireShiftForNewLine(self, state):
        """
        Sets whether or not the shift modifier is required for new lines.
        When this is True, then Return/Enter key presses will not create
        new lines in the edit, but instead trigger the returnPressed,
        textEntered and htmlEntered signals.
        
        :param     state | <bool>
        """
        self._requireShiftForNewLine = state
    
    def setRichTextEditEnabled(self, state):
        """
        Sets whether or not rich text editing is enabled for this editor.
        
        :param      state | <bool>
        """
        self._richTextEditEnabled = state
    
    def setTabsAsSpaces(self, state):
        """
        Sets whether or not tabs as spaces are used instead of tab characters.
        
        :param      state | <bool>
        """
        self._tabsAsSpaces = state
    
    def setText(self, text):
        """
        Sets the text for this instance to the inputed text.
        
        :param      text | <str>
        """
        super(XTextEdit, self).setText(projex.text.toAscii(text))
    
    def tabsAsSpaces(self):
        """
        Returns whether or not tabs as spaces are being used.
        
        :return     <bool>
        """
        return self._tabsAsSpaces
    
    @classmethod
    def getText(cls,
                parent=None,
                windowTitle='Get Text',
                label='',
                text='',
                plain=True,
                wrapped=True):
        """
        Prompts the user for a text entry using the text edit class.
        
        :param      parent | <QWidget>
                    windowTitle | <str>
                    label       | <str>
                    text        | <str>
                    plain       | <bool> | return plain text or not
        
        :return     (<str> text, <bool> accepted)
        """
        # create the dialog
        dlg = QDialog(parent)
        dlg.setWindowTitle(windowTitle)
        
        # create the layout
        layout = QVBoxLayout()
        
        # create the label
        if label:
            lbl = QLabel(dlg)
            lbl.setText(label)
            layout.addWidget(lbl)
        
        # create the widget
        widget = cls(dlg)
        widget.setText(text)
        
        if not wrapped:
            widget.setLineWrapMode(XTextEdit.NoWrap)
        
        layout.addWidget(widget)
        
        # create the buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
                                Qt.Horizontal,
                                dlg)
        layout.addWidget(btns)
        
        dlg.setLayout(layout)
        dlg.adjustSize()
        
        # create connections
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        
        if dlg.exec_():
            if plain:
                return (widget.toPlainText(), True)
            else:
                return (widget.toHtml(), True)
        else:
            return ('', False)
        
    
    x_autoResizeToContents = Property(bool,
                                      autoResizeToContents,
                                      setAutoResizeToContents)
    
    x_encoding = Property(str, encoding, setEncoding)
    
    x_requireShiftForNewLine = Property(bool,
                                      requireShiftForNewLine,
                                      setRequireShiftForNewLine)
    
    x_hint = Property(str, hint, setHint)
    x_tabsAsSpaces = Property(bool, tabsAsSpaces, setTabsAsSpaces)
    x_richTextEditEnabled = Property(bool, isRichTextEditEnabled, setRichTextEditEnabled)

__designer_plugins__ = [XTextEdit]