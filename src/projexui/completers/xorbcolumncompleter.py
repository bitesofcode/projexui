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

from projexui.qt.QtGui import QStandardItemModel,\
                              QStandardItem

from projexui.completers.xjoinercompleter import XJoinCompleter

class XOrbColumnCompleter(XJoinCompleter):
    def __populate(self, columns, parent=None, processed=None):
        if not processed:
            processed = []
        
        columns.sort(key=lambda x: x.name().strip('_'))
        for col in columns:
            item = QStandardItem(col.name().strip('_'))
            parent.appendRow(item)
            if not col.isReference():
                continue
            
            ref = col.referenceModel()
            if ref in processed:
                continue
            
            processed.append(ref)
            self.__populate(ref.schema().columns(), item, processed)
        
    def __init__(self, tableType, parent):
        # generate a model based on orb columns
        items = {}
        model = QStandardItemModel(parent)
        
        if tableType:
            self.__populate(tableType.schema().columns(), model)
        
        self._tableType = tableType
        
        super(XOrbColumnCompleter, self).__init__(model, parent)
        
    def tableType(self):
        """
        Returns the table type associated with this completer.
        
        :return     <subclass of orb.TableType>
        """
        return self._tableType