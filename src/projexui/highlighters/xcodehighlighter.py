""" Defines the hook required for the PyInstaller to use projexui with it. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

import re

from projex.text import nativestring
from projex.enum import enum
from projexui.qt import QtCore, QtGui

from projex.addon import AddonManager

class XCodeHighlighter(QtGui.QSyntaxHighlighter, AddonManager):
    Style = enum('Keyword',
                 'Comment',
                 'String',
                 'Class',
                 'Function')
    
    Theme = enum('Default',
                 'Dark')
    
    def __init__(self, parent=None):
        super(XCodeHighlighter, self).__init__(parent)
        
        # define the format options
        self._formats = {}
        self._patterns = []
        self._multiline = []
        self._theme = None
        
        self.setTheme(XCodeHighlighter.Theme.Default)

    def definePattern(self, style, pattern):
        """
        Defines a pattern for the given style.
        
        :param      style   | <XCodeHighlighter.Style>
                    pattern | <str>
        """
        self._patterns.append((style, pattern))
    
    def defineMultiline(self, style, openPattern, closePattern):
        """
        Defines a pattern that can span multiple styles.
        
        :param      style        | <XCodeHighlighter.Style>
                    openPattern  | <str>
                    closePattern | <str>
        """
        self._multiline.append((style, openPattern, closePattern))
    
    def highlightBlock(self, text):
        """
        Highlights the given text format based on this highlighters syntax
        rules.
        
        :param      text | <str>
        """
        text = nativestring(text)
        for pattern, format in self.patterns():
            for result in re.finditer(pattern, text):
                grps = result.groups()
                if grps:
                    for i in range(len(grps)):
                        start, end = result.span(i+1)
                        self.setFormat(start, end - start, format)
                else:
                    self.setFormat(result.start(),
                                   result.end() - result.start(),
                                   format)
        
        self.setCurrentBlockState(0)
        if self.previousBlockState() == 1:
            return
        
        for form, open, close in self._multiline:
            open = QtCore.QRegExp(open)
            close = QtCore.QRegExp(close)
            
            start = open.indexIn(text)
            processed = False
            
            while start >= 0:
                processed = True
                end = close.indexIn(text, start)

                if end == -1:
                    self.setCurrentBlockState(1)
                    length = len(text) - start
                else:
                    length = end - start + close.matchedLength()

                self.setFormat(start, length, form)
                start = open.indexIn(text, start + length)
            
            if processed:
                break

    def keywords(self):
        """
        Returns the list of keywords associated with this highlighter.
        
        :return     [<str>, ..]
        """
        return self._keywords
    
    def patterns(self):
        """
        Returns a list of highlighting rules for this highlighter.  This will
        join the list of keywords as a regular expression with the keyword
        format as well as any custom patterns that have been defined.
        
        :return     [(<str>, <QtGui.QTextCharFormat>), ..]
        """
        patterns = []
        
        # add keyword patterns
        form = self.styleFormat(XCodeHighlighter.Style.Keyword)
        for kwd in self.keywords():
            patterns.append((r'\b{0}\b'.format(kwd), form))
        
        # add additional patterns
        for style, pattern in self._patterns:
            form = self.styleFormat(style)
            if not form:
                continue
            
            patterns.append((pattern, form))
        
        return patterns

    def setStyleFormat(self, style, format):
        """
        Sets the character format for the given style for this highlighter.
        
        :param      style   | <XCodeHighlighter.Style>
                    format  | <QtGui.QTextCharFormat>
        """
        self._formats[style] = format
    
    def setKeywords(self, keywords):
        """
        Sets the keywords for this highlighter to the inputed list of keywords.
        
        :param      keywords | [<str>, ..]
        """
        self._keywords = keywords
    
    def setTheme(self, theme):
        if theme == XCodeHighlighter.Theme.Default:
            # create the default keyword format
            form = QtGui.QTextCharFormat()
            form.setForeground(QtGui.QColor('blue'))
            self._formats[XCodeHighlighter.Style.Keyword] = form
            
            # create the default comment format
            form = QtGui.QTextCharFormat()
            form.setForeground(QtGui.QColor('green'))
            self._formats[XCodeHighlighter.Style.Comment] = form
            
            # create the default string format
            form = QtGui.QTextCharFormat()
            form.setForeground(QtGui.QColor('brown'))
            self._formats[XCodeHighlighter.Style.String] = form
            
            # create the class format
            form = QtGui.QTextCharFormat()
            form.setForeground(QtGui.QColor('darkMagenta'))
            form.setFontWeight(QtGui.QFont.Bold)
            self._formats[XCodeHighlighter.Style.Class] = form
            
            # create the function format
            form = QtGui.QTextCharFormat()
            form.setForeground(QtGui.QColor('darkMagenta'))
            form.setFontWeight(QtGui.QFont.Bold)
            self._formats[XCodeHighlighter.Style.Function] = form
    
        elif theme == XCodeHighlighter.Theme.Dark:
            opts = []
            opts.append((self.Style.Keyword, '#2da4ff', False))
            opts.append((self.Style.String, 'orange', False))
            opts.append((self.Style.Comment, '#10ff00', False))
            opts.append((self.Style.Class, '#f7ffc1', True))
            opts.append((self.Style.Function, '#f7ffc1', True))
            
            for style, clr, bold in opts:
                form = QtGui.QTextCharFormat()
                form.setForeground(QtGui.QColor(clr))
                
                if bold:
                    form.setFontWeight(QtGui.QFont.Bold)
                
                self._formats[style] = form
    
    def styleFormat(self, style):
        """
        Returns the character format for the given style for this highlighter.
        
        :param      style | <XCodeHighlighter.Style>
        
        :return     <QtGui.QTextCharFormat> || None
        """
        return self._formats.get(style, None)

    @classmethod
    def fileTypes(cls):
        prop = '_{0}__filetypes'.format(cls.__name__)
        return getattr(cls, prop, '')

    @classmethod
    def hasFileType(cls, filetype):
        return filetype in cls.fileTypes().split(',')

    @classmethod
    def setFileTypes(cls, filetypes):
        prop = '_{0}__filetypes'.format(cls.__name__)
        setattr(cls, prop, filetypes)

