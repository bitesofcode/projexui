#!/usr/bin/python

""" Defines a completer for generating completions based on a '.' split """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

from projex.text import nativestring

from projexui.qt import unwrapVariant
from projexui.qt.QtGui import QCompleter

class XJoinCompleter(QCompleter):
    """ Create Qt completions based on a joining string """
    
    def __init__(self, model, parent, joiner='.'):
        self._model = model
        self._joiner = joiner
        
        super(XJoinCompleter, self).__init__(model, parent)
    
    def joiner(self):
        """
        Returns the joiner associated with this completer.
        
        :return     <str>
        """
        return self._joiner
    
    def pathFromIndex(self, index):
        """
        Returns the joined path from the given model index.  This will
        join together the full path with periods.
        
        :param      index | <QModelIndex>
        
        :return     <str>
        """
        out  = []
        while index and index.isValid():
            out.append(nativestring(unwrapVariant(index.data())))
            index = self._model.parent(index)
        
        return self.joiner().join(reversed(out))
    
    def setJoiner(self, joiner):
        """
        Defines the joiner string to use for the completion model.
        
        :param      joiner | <str>
        """
        self._joiner = joiner
    
    def splitPath(self, path):
        """
        Returns a split path based on the inputed path.  This completer
        will split the given path by periods vs. a standard path split.
        
        :param      path | <str>
        
        :return     [<str>, ..]
        """
        return nativestring(path).split(self.joiner())