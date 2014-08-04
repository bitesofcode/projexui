
""" Defines a more robust tab widget. """

# define authorship information
__authors__     = ['Eric Hulser']
__author__      = ','.join(__authors__)
__credits__     = []
__copyright__   = 'Copyright (c) 2011, Projex Software'

from xqt import QtCore, QtGui
from projexui.xpainter import XPainter

class XNumberArea(QtGui.QWidget):
    def __init__(self, editor):
        super(XNumberArea, self).__init__(editor)
        
        self._codeEditor = editor
        
        # set default properties
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setFamily('Courier New')
        self.setFont(font)

    def codeEditor(self):
        return self._codeEditor

    def paintEvent(self, event):
        with XPainter(self) as painter:
            painter.fillRect(event.rect(), QtGui.QColor('lightGray'))
            
            edit = self.codeEditor()
            block = edit.firstVisibleBlock()
            blockNumber = block.blockNumber()
            top = edit.blockBoundingGeometry(block).translated(edit.contentOffset()).top()
            bottom = top + edit.blockBoundingRect(block).height()
            textHeight = edit.fontMetrics().height()

            painter.setFont(self.font())
            painter.setPen(QtGui.QColor('black'))
            while block.isValid() and top <= event.rect().bottom():
                if block.isVisible() and bottom >= event.rect().top():
                    painter.drawText(0,
                                     top,
                                     self.width() - 6,
                                     textHeight,
                                     QtCore.Qt.AlignRight,
                                     str(blockNumber + 1))

                block = block.next()
                top = bottom
                bottom = top + edit.blockBoundingRect(block).height()
                blockNumber += 1

    def sizeHint(self):
        return QtCore.QSize(self.codeEditor().numberAreaWidth(), 0)