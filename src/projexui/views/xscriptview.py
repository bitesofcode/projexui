#!/usr/bin/python

""" Defines a reusable widget for the XConsoleEdit. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

from xml.etree import ElementTree
from xml.sax.saxutils import escape, unescape

from xqt import QtGui, QtCore
from projexui.widgets.xviewwidget import XView
from projexui.widgets.xcodeedit import XCodeEdit

class XScriptView(XView):
    def __init__(self, parent):
        super(XScriptView, self).__init__(parent)
        
        # define custom properties
        self._edit = XCodeEdit(self)
        self._edit.setLanguage('Python')
        
        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._edit)
        self.setLayout(layout)

    def edit(self):
        """
        Returns the edit for this view.
        
        :return     <projexui.widgets.xcodeedit.XCodeEdit>
        """
        return self._edit

    def keyPressEvent(self, event):
        """
        Handles the key press event.  When the user hits F5, the current
        code edit will be executed within the console's scope.
        
        :param      event | <QtCore.QKeyEvent>
        """
        if event.key() == QtCore.Qt.Key_F5 or \
           (event.key() == QtCore.Qt.Key_E and \
            event.modifiers() == QtCore.Qt.ControlModifier):
            code = str(self._edit.toPlainText())
            scope = self.viewWidget().codeScope()
            
            exec code in scope, scope
        else:
            super(XScriptView, self).keyPressEvent(event)

    def restoreXml(self, xml):
        """
        Restores the view's content from XML.
        
        :param      xml | <str>
        """
        xscript = xml.find('script')
        if xscript is not None and xscript.text is not None:
            self._edit.setPlainText(unescape(xscript.text))

    def saveXml(self, xml):
        """
        Saves this view's content to XML.
        
        :param      xml | <str>
        """
        xscript = ElementTree.SubElement(xml, 'script')
        xscript.text = escape(self._edit.toPlainText())

XScriptView.setViewName('Script')