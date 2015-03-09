#!/usr/bin/python

""" Defines the XScintillaEditOptions class for quickly setting up user 
    options. """

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

from projexui.qt.QtGui import QFont
from projex.dataset import DataSet

class XScintillaEditOptions(DataSet):
    def __init__( self ):
        super(XScintillaEditOptions, self).__init__()
        
        self.define('autoComplete',         True)
        self.define('autoCompleteThreshold',0)
        self.define('autoIndent',           True)
        self.define('tabIndents',           True)
        self.define('tabWidth',             4)
        self.define('indentationsUseTabs',  False)
        self.define('limitColumn',          80)
        
        self.define('showLimitColumn',      False)
        self.define('showLineWrap',         False)
        self.define('showEndlines',         False)
        self.define('showCaretLine',        False)
        self.define('showLineNumbers',      True)
        self.define('showWhitespaces',      False)
        self.define('showIndentations',     False)
        
        self.define('documentFont',         QFont('Courier New', 9))
        self.define('documentFontSize',     9)
        self.define('documentMarginFont',   QFont('Courier New', 7))