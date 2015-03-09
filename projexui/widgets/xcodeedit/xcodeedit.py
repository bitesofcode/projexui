
""" Defines a more robust tab widget. """

# define authorship information
__authors__     = ['Eric Hulser']
__author__      = ','.join(__authors__)
__credits__     = []
__copyright__   = 'Copyright (c) 2011, Projex Software'

#------------------------------------------------------------------------------

import os
from projex.text import nativestring

from xqt import QtCore, QtGui
from projexui.highlighters.xcodehighlighter import XCodeHighlighter

from .xnumberarea import XNumberArea

class XCodeEdit(QtGui.QPlainTextEdit):
    """ """
    def __init__(self, parent=None):
        super(XCodeEdit, self).__init__(parent)
        
        # define custom properties
        self._filename = ''
        self._numberArea = XNumberArea(self)
        self._highlighter = None
        
        # set default properties
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setFamily('Courier New')
        self.setFont(font)
        self.setWordWrapMode(QtGui.QTextOption.NoWrap)
        
        # create connections
        self.blockCountChanged.connect(self.updateNumberAreaWidth)
        self.updateRequest.connect(self.updateNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        
        self.updateNumberAreaWidth(0)
        self.highlightCurrentLine()

    def filename(self):
        return self._filename

    def highlightCurrentLine(self):
        extra = []
        if not self.isReadOnly():
            lineColor = QtGui.QColor('yellow').lighter(160)
            
            selection = QtGui.QTextEdit.ExtraSelection()
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra.append(selection)

        self.setExtraSelections(extra)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Tab:
            self.insertPlainText(' ' * 4)
            event.accept()
        
        else:
            super(XCodeEdit, self).keyPressEvent(event)

    def load(self, filename=''):
        if not filename:
            filename = QtGui.QFileDialog.getOpenFileName(None, 'Open File')
            if type(filename) == tuple:
                filename = filename[0]
    
        if not filename:
            return False

        try:
            with open(str(filename), 'r') as f:
                data = f.read()
        except StandardError:
            return False
        
        self._filename = filename
        self.setPlainText(data)
        
        self._highlighter = None
        ext = os.path.splitext(self._filename)[1]
        for cls in XCodeHighlighter.addons().values():
            if cls.hasFileType(ext):
                self._highlighter = cls(self.document())
                break
        
        return True
    
    def save(self):
        return self.saveAs(self.filename())
    
    def saveAs(self, filename=''):
        if not filename:
            filename = QtGui.QFileDialog.getSaveFileName(None, 'Save File')
            if type(filename) == tuple:
                filename = filename[0]
    
        if not filename:
            return False

        text = nativestring(self.toPlainText())

        try:
            with open(str(filename), 'w') as f:
                f.write(text)
        except StandardError:
            return False
        
        self._filename = filename
        return True
    
    def setLanguage(self, language):
        """
        Sets the language for this code.
        
        :param      language | <str>
        """
        cls = XCodeHighlighter.byName(language)
        if cls:
            self._highlighter = cls(self.document())
    
    def resizeEvent(self, event):
        super(XCodeEdit, self).resizeEvent(event)
        
        rect = self.contentsRect()
        self.numberArea().setGeometry(rect.left(),
                                      rect.top(),
                                      self.numberAreaWidth(),
                                      rect.height())
    
    def numberArea(self):
        return self._numberArea
    
    def numberAreaWidth(self):
        digits = 1
        maxDigits = max(1, self.blockCount())
        while maxDigits >= 10:
            maxDigits /= 10
            digits += 1

        space = 12 + self.fontMetrics().width('9') * digits
        return space

    def updateNumberArea(self, rect, deltaY):
        if deltaY:
            self.numberArea().scroll(0, deltaY)
        else:
            self.numberArea().update(0,
                                     rect.y(),
                                     self.numberArea().width(),
                                     rect.height())
        
        if rect.contains(self.viewport().rect()):
            self.updateNumberAreaWidth(0)

    def updateNumberAreaWidth(self, blockCount):
        self.setViewportMargins(self.numberAreaWidth(), 0, 0, 0)
