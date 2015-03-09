#!/usr/bin/python

""" Defines a Document Editing widget based on the Qt Scintilla wrapper """

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

from projexui.widgets.xscintillaedit.xscintillaedit import XScintillaEdit
from projexui.widgets.xscintillaedit.xlanguage      import XLanguage

from projexui.widgets.xscintillaedit.xscintillaeditoptions  import XScintillaEditOptions
from projexui.widgets.xscintillaedit.xscintillaeditcolorset import XScintillaEditColorSet

__designer_plugins__ = [XScintillaEdit]