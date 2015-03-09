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

from projexui.qt.QtGui import QCompleter,\
                              QStandardItemModel,\
                              QStandardItem

class XQueryCompleter(QCompleter):
    def __init__( self, terms, parent ):
        items = {}
        model = QStandardItemModel(parent)
        
        for term in terms:
            parts = nativestring(term).split('.')
            for i in range(len(parts)):
                parent_key  = '.'.join(parts[:i])
                item_key    = '.'.join(parts[:i+1])
                
                if ( item_key in items ):
                    continue
                
                parent_item = items.get(parent_key)
                
                item = QStandardItem(parts[i])
                if ( parent_item ):
                    parent_item.appendRow(item)
                else:
                    model.appendRow(item)
                
                items[item_key] = item
        
        self._model = model
        super(XQueryCompleter, self).__init__(model, parent)
    
    def pathFromIndex( self, index ):
        """
        Returns the joined path from the given model index.  This will
        join together the full path with periods.
        
        :param      index | <QModelIndex>
        
        :return     <str>
        """
        item = self._model.itemFromIndex(index)
        out  = []
        
        while ( item ):
            out.append(nativestring(item.text()))
            item = item.parent()
        
        return '.'.join(reversed(out))
    
    def splitPath( self, path ):
        """
        Returns a split path based on the inputed path.  This completer
        will split the given path by periods vs. a standard path split.
        
        :param      path | <str>
        
        :return     [<str>, ..]
        """
        return nativestring(path).split('.')