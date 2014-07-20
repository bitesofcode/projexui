#!/usr/bin/python

""" Defines an interface to allow users to build their queries on the fly. """

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

from projex.text import nativestring
from projexui.qt.QtGui import QLineEdit

#-------------------------------------------------------------------------------

class XQueryRule(object):
    def __init__( self,
                  term = '',
                  operators = None ):
                      
        self._term            = term
        self._completionTerms = []
        self._operators       = {}
        self._operatorMap     = {}
        
        if ( operators is None ):
            self._operators['is'] = QLineEdit
        else:
            self._operators.update(operators)
    
    def completionTerms( self ):
        """
        Returns the completion trems for this rule.
        
        :return     [<str>, ..]
        """
        return self._completionTerms
    
    def defineOperator( self, operator, widget = -1 ):
        """
        Adds a new operator for this rule.  If widget is supplied as -1, then \
        a QLineEdit will be used by default.
        
        :param      operator | <str>
                    widget   | <subclass of QWidget> || None || -1
        """
        if ( widget == -1 ):
            widget = QLineEdit
            
        self._operators[nativestring(operator)] = widget
    
    def defineTerm( self, term ):
        """
        Sets the query term that will be used for this rule.
        
        :param      term | <str>
        """
        self._term = nativestring(term)
    
    def defineOpMapper( self, label, operator ):
        """
        Defines a mapper from a database operator to a more useful visual name.
        
        :param      operator | <str>
                    label    | <str>
        """
        self._operatorMap[label] = operator
    
    def duplicate( self, term = '' ):
        """
        Duplicates this rule for the inputed term.
        
        :param      term | <str>
        
        :return     <XQueryRule>
        """
        return XQueryRule(term, self._operators)
    
    def editorType( self, operator ):
        """
        Returns the editor type that will be used for this query rule.  If you \
        define your own editor, you will need to provide a text and setText \
        method to use.  The query editing system will be based on a string \
        expression system, and you will need to provide string representation \
        for your data.
        
        :param      operator | <str>
        
        :return     <subclass of QWidget>
        """
        return self._operators.get(operator)
    
    def labelOperator( self, label ):
        """
        Returns the operator for the inputed label.
        
        :return     <str>
        """
        return self._operatorMap.get(label, label)
    
    def operatorLabel( self, operator ):
        """
        Returns the label for the inputed operator.
        
        :return     <str>
        """
        for key, value in self._operatorMap.items():
            if ( value == operator ):
                return key
        return operator
    
    def operators( self ):
        """
        Returns the list of operators that will be used for this term.
        
        :return     [<str>, ..]
        """
        return sorted(self._operators.keys())
    
    def setCompletionTerms( self, terms ):
        """
        Sets the completion trems for this rule.  These will be used in a
        completer for QLineEdit editor types.
        
        :param     terms | [<str>, ..]
        """
        self._completionTerms = terms
    
    def term( self ):
        """
        Returns the term that will be used for this rule.
        
        :return     <str>
        """
        return self._term