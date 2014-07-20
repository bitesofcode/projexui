#!/usr/bin/python

""" 
Adds additional quick-input options to the QInputDialog
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

from projexui.qt.QtCore import Qt

from projexui.qt.QtGui  import QInputDialog,\
                               QLabel,\
                               QVBoxLayout,\
                               QTextEdit,\
                               QDialogButtonBox,\
                               QDialog

class XInputDialog(QInputDialog):
    @staticmethod
    def getPlainText( parent, title, caption, text = '' ):
        """
        Prompts the user for more advanced text input.
        
        :param      parent  | <QWidget> || None
                    title   | <str>
                    caption | <str>
                    text    | <str>
        
        :return     (<str>, <bool> accepted)
        """
        dlg = QDialog(parent)
        dlg.setWindowTitle(title)
        
        label = QLabel(dlg)
        label.setText(caption)
        
        edit = QTextEdit(dlg)
        edit.setText(text)
        edit.selectAll()
        
        opts = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        btns = QDialogButtonBox(opts, Qt.Horizontal, dlg)
        
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        
        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(edit)
        layout.addWidget(btns)
        
        dlg.setLayout(layout)
        dlg.adjustSize()
        
        if ( dlg.exec_() ):
            return (edit.toPlainText(), True)
        return ('', False)