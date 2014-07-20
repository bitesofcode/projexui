#!/usr/bin/python

""" Defines a reusable widget that can be linked to a text edit to search \
    its contents. """

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

from projexui.qt.QtCore import QRegExp,\
                               Qt

from projexui.qt.QtGui import QWidget,\
                              QToolButton,\
                              QAction,\
                              QCheckBox,\
                              QHBoxLayout,\
                              QKeySequence,\
                              QIcon,\
                              QTextDocument,\
                              QTextCursor,\
                              QColor

try:
    from projexui.qt.QtWebKit import QWebPage
except ImportError:
    QWebPage = None

from projexui import resources
from projexui.widgets.xlineedit import XLineEdit

class XFindWidget(QWidget):
    """ """
    __designer_icon__ = resources.find('img/search.png')
    
    def __init__( self, parent = None ):
        super(XFindWidget, self).__init__( parent )
        
        # define custom properties
        self._textEdit   = None
        self._webView    = None
        self._lastCursor = QTextCursor()
        self._lastText = ''
        
        self._closeButton = QToolButton(self)
        self._closeButton.setIcon(QIcon(resources.find('img/close.png')))
        self._closeButton.setAutoRaise(True)
        self._closeButton.setToolTip('Hide the Find Field.')
        
        self._searchEdit = XLineEdit(self)
        self._searchEdit.setHint('search for...')
        
        self._previousButton = QToolButton(self)
        self._previousButton.setIcon(QIcon(resources.find('img/back.png')))
        self._previousButton.setAutoRaise(True)
        self._previousButton.setToolTip('Find Previous')
        
        self._nextButton = QToolButton(self)
        self._nextButton.setIcon(QIcon(resources.find('img/forward.png')))
        self._nextButton.setAutoRaise(True)
        self._nextButton.setToolTip('Find Next')
        
        self._caseSensitiveCheckbox = QCheckBox(self)
        self._caseSensitiveCheckbox.setText('Case Sensitive')
        
        self._wholeWordsCheckbox = QCheckBox(self)
        self._wholeWordsCheckbox.setText('Whole Words Only')
        
        self._regexCheckbox = QCheckBox(self)
        self._regexCheckbox.setText('Use Regex')
        
        self._findAction = QAction(self)
        self._findAction.setText('Find...')
        self._findAction.setIcon(QIcon(resources.find('img/search.png')))
        self._findAction.setToolTip('Find in Text')
        self._findAction.setShortcut(QKeySequence('Ctrl+F'))
        self._findAction.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        
        # layout the widgets
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget( self._closeButton )
        layout.addWidget( self._searchEdit )
        layout.addWidget( self._previousButton )
        layout.addWidget( self._nextButton )
        layout.addWidget( self._caseSensitiveCheckbox )
        layout.addWidget( self._wholeWordsCheckbox )
        layout.addWidget( self._regexCheckbox )
        
        self.setLayout(layout)
        
        # create connections
        self._findAction.triggered.connect(          self.show )
        self._searchEdit.textChanged.connect(        self.findNext )
        self._closeButton.clicked.connect(           self.hide )
        self._previousButton.clicked.connect(        self.findPrev )
        self._nextButton.clicked.connect(            self.findNext )
        self._caseSensitiveCheckbox.clicked.connect( self.findNext )
        self._wholeWordsCheckbox.clicked.connect(    self.findNext )
        self._searchEdit.returnPressed.connect(      self.findNext )
        self._regexCheckbox.clicked.connect(         self.findNext )
    
    def find( self, flags = 0 ):
        """
        Looks throught the text document based on the current criteria.  The \
        inputed flags will be merged with the generated search flags.
        
        :param      flags | <QTextDocument.FindFlag>
        
        :return     <bool> | success
        """
        # check against the web and text views
        if ( not (self._textEdit or self._webView) ):
            fg = QColor('darkRed')
            bg = QColor('red').lighter(180)
            
            palette = self.palette()
            palette.setColor(palette.Text, fg)
            palette.setColor(palette.Base, bg)
            
            self._searchEdit.setPalette(palette)
            self._searchEdit.setToolTip( 'No Text Edit is linked.' )
            
            return False
        
        if ( self._caseSensitiveCheckbox.isChecked() ):
            flags |= QTextDocument.FindCaseSensitively
        
        if ( self._textEdit and self._wholeWordsCheckbox.isChecked() ):
            flags |= QTextDocument.FindWholeWords
        
        terms = self._searchEdit.text()
        if ( terms != self._lastText ):
            self._lastCursor = QTextCursor()
        
        if ( self._regexCheckbox.isChecked() ):
            terms = QRegExp(terms)
        
        palette = self.palette()
        
        # search on a text edit
        if ( self._textEdit ):
            cursor  = self._textEdit.document().find(terms, 
                                                 self._lastCursor, 
                                                 QTextDocument.FindFlags(flags))
            found   = not cursor.isNull()
            self._lastCursor = cursor
            self._textEdit.setTextCursor(cursor)
        
        elif ( QWebPage ):
            flags = QWebPage.FindFlags(flags)
            flags |= QWebPage.FindWrapsAroundDocument
            
            found = self._webView.findText(terms, flags)
        
        self._lastText = self._searchEdit.text()
        
        if ( not terms or found ):
            fg = palette.color(palette.Text)
            bg = palette.color(palette.Base)
        else:
            fg = QColor('darkRed')
            bg = QColor('red').lighter(180)
        
        palette.setColor(palette.Text, fg)
        palette.setColor(palette.Base, bg)
        
        self._searchEdit.setPalette(palette)
        
        return found
    
    def findNext( self ):
        """
        Looks for the search terms that come up next based on the criteria.
        
        :return     <bool> | success
        """
        return self.find()
    
    def findPrev( self ):
        """
        Looks for the search terms that come up last based on the criteria.
        
        :return     <bool> | success
        """
        return self.find(QTextDocument.FindBackward)
        
    def setTextEdit( self, textEdit ):
        """
        Sets the text edit that this find widget will use to search.
        
        :param      textEdit | <QTextEdit>
        """
        if ( self._textEdit ):
            self._textEdit.removeAction(self._findAction)
            
        self._textEdit = textEdit
        if ( textEdit ):
            textEdit.addAction(self._findAction)
    
    def setWebView( self, webView ):
        """
        Sets the web view edit that this find widget will use to search.
        
        :param      webView | <QWebView>
        """
        if ( self._webView ):
            self._webView.removeAction(self._findAction)
        
        self._webView = webView
        if ( webView ):
            webView.addAction(self._findAction)
    
    def show( self ):
        """
        Sets this widget visible and then makes the find field have focus.
        """
        super(XFindWidget, self).show()
        
        self._searchEdit.setFocus()
    
    def textEdit( self ):
        """
        Returns the text edit linked with this find widget.
        
        :return     <QTextEdit>
        """
        return self._textEdit
    
    def webView( self ):
        """
        Returns the text edit linked with this find widget.
        
        :return     <QWebView>
        """
        return self._webView

__designer_plugins__ = [XFindWidget]