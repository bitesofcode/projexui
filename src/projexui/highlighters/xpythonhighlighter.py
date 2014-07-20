""" Defines the hook required for the PyInstaller to use projexui with it. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

from .xcodehighlighter import XCodeHighlighter

class XPythonHighlighter(XCodeHighlighter):
    def __init__(self, parent=None):
        super(XPythonHighlighter, self).__init__(parent)
        
        # define additional highlighting rules
        self.definePattern(self.Style.Class, r'class (\w+)')
        self.definePattern(self.Style.Function, r'def (\w+)')
        self.definePattern(self.Style.Comment, r'#[^\n]*')
        self.definePattern(self.Style.String, r'\"[^\"]*\"')
        self.definePattern(self.Style.String, r"'[^']*'")
        self.defineMultiline(self.Style.String, r'"""', r'"""')
        self.setKeywords(('def', 'if', 'elif', 'else', 'class', 'exec', 'eval',
                          'return', 'for', 'while', 'break', 'yield', 'import',
                          'from', 'with', 'print', 'is', 'not', 'in', 'self',
                          'super'))

XPythonHighlighter.setFileTypes('.py')
XCodeHighlighter.registerAddon('Python', XPythonHighlighter)
