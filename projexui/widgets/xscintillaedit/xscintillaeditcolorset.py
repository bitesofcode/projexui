#!/usr/bin/python

""" Defines the XScintillaEditColorSet class for quickly setting up user 
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

from projexui.qt.QtGui import QColor
from projexui.xcolorset import XColorSet

class XScintillaEditColorSet(XColorSet):
    def __init__( self, *args, **defaults ):
        super(XScintillaEditColorSet, self).__init__(*args, **defaults)
        
        self.setColorGroups(['Default'])
        
        self.setColor('SelectionBackground',   QColor('white'))
        self.setColor('SelectionForeground',   QColor('black'))
        self.setColor('CaretForeground',       QColor('black'))
        self.setColor('CaretBackground',       QColor('white'))
        self.setColor('IndentBackground',      QColor('white'))
        self.setColor('IndentForeground',      QColor('black'))
        self.setColor('MarginsBackground',     QColor('gray'))
        self.setColor('MarginsForeground',     QColor('black'))
        self.setColor('Background',            QColor('white'))
        self.setColor('SelectionBackground',   QColor('cyan'))
        self.setColor('SelectionForeground',   QColor('black'))
        self.setColor('FoldMarginsBackground', QColor('gray'))
        self.setColor('FoldMarginsForeground', QColor('black'))
        self.setColor('CallTipsBackground',    QColor('yellow'))
        self.setColor('CallTipsForeground',    QColor('black'))
        self.setColor('CallTipsHighlight',     QColor('cyan'))
        self.setColor('Edge',                  QColor('black'))
        self.setColor('IndicatorForeground',   QColor('black'))
        self.setColor('IndicatorBackground',   QColor('white'))
        self.setColor('IndicatorOutline',      QColor('white'))
        self.setColor('MarkerBackground',      QColor('gray'))
        self.setColor('MarkerForeground',      QColor('black'))
        
        self.setColor('MatchedBraceBackground',   QColor('white'))
        self.setColor('MatchedBraceForeground',   QColor('black'))
        self.setColor('UnmatchedBraceBackground', QColor('white'))
        self.setColor('UnmatchedBraceForeground', QColor('red'))
        self.setColor('WhitespaceBackground',     QColor('white'))
        self.setColor('WhitespaceForeground',     QColor('black'))
        self.setColor('Method',                   QColor('blue'))
        self.setColor('Comment',                  QColor('green'))
        self.setColor('Number',                   QColor('red'))
        self.setColor('Misc',                     QColor('red'))
        self.setColor('Keyword',                  QColor('blue'))
        self.setColor('Operator',                 QColor('red'))
        self.setColor('String',                   QColor('orange'))
        self.setColor('Regex',                    QColor('red'))
        self.setColor('Attribute',                QColor('red'))
        self.setColor('Entity',                   QColor('blue'))
        self.setColor('Tag',                      QColor('red'))
        self.setColor('Error',                    QColor('red'))
        self.setColor('Text',                     QColor('black'))

XScintillaEditColorSet.registerToDataTypes()