#!/usr/bin/python

""" 
Extends the base QTableWidget class with additional methods.
"""

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

import weakref

from projex.text import nativestring
from projexui.qt.QtCore   import Qt
from projexui.qt.QtGui    import QTableWidget

import projexui.resources

class XTableWidget(QTableWidget):
    """ Advanced QTableWidget class. """
    __designer_icon__ = projexui.resources.find('img/ui/table.png')
    
    def __init__( self, parent = None ):
        super(XTableWidget, self).__init__(parent)
        
        # create custom properties
        self._dataCollectorRef      = None
        self._dragDropFilterRef     = None
        
        # setup header
        for header in (self.verticalHeader(), self.horizontalHeader()):
            header.setContextMenuPolicy( Qt.CustomContextMenu )
    
    def column( self, name ):
        """
        Returns the index of the column at the given name.
        
        :param      name | <str>
        
        :return     <int> (-1 if not found)
        """
        columns = self.columns()
        if ( name in columns ):
            return columns.index(name)
        return -1
    
    def columnNameAt( self, index ):
        """
        Returns the name of the column at the inputed index.
        
        :param      index | <int>
        
        :return     <str>
        """
        columns = self.columns()
        if ( 0 <= index and index < len(columns) ):
            return columns[index]
        return ''
    
    def columns( self ):
        """
        Returns the list of column names for this table widget's columns.
        
        :return     [<str>, ..]
        """
        output = []
        for c in range(self.columnCount()):
            hitem  = self.horizontalHeaderItem(c)
            text = nativestring(hitem.text())
            if ( not text ):
                text = nativestring(hitem.toolTip())
            output.append(text)
        return output
    
    def dataCollector( self ):
        """
        Returns a method or function that will be used to collect mime data \
        for a list of tablewidgetitems.  If set, the method should accept a \
        single argument for a list of items and then return a QMimeData \
        instance.
        
        :usage      |from projexui.qt.QtCore import QMimeData, QWidget
                    |from projexui.widgets.xtablewidget import XTableWidget
                    |
                    |def collectData(table, items):
                    |   data = QMimeData()
                    |   data.setText(','.join(map(lambda x: x.text(0), items)))
                    |   return data
                    |
                    |class MyWidget(QWidget):
                    |   def __init__( self, parent ):
                    |       super(MyWidget, self).__init__(parent)
                    |       
                    |       self._table = XTableWidget(self)
                    |       self._table.setDataCollector(collectData)
                    
        
        :return     <function> || <method> || None
        """
        func = None
        if ( self._dataCollectorRef ):
            func = self._dataCollectorRef()
        
        if ( not func ):
            self._dataCollectorRef = None
        
        return func
    
    def dragEnterEvent( self, event ):
        """
        Processes the drag drop event using the filter set by the \
        setDragDropFilter
        
        :param      event | <QDragEvent>
        """
        filt = self.dragDropFilter()
        if ( filt and filt(self, event) ):
            return
            
        super(XTableWidget, self).dragEnterEvent(event)
        
    def dragMoveEvent( self, event ):
        """
        Processes the drag drop event using the filter set by the \
        setDragDropFilter
        
        :param      event | <QDragEvent>
        """
        filt = self.dragDropFilter()
        if ( filt and filt(self, event) ):
            return
        
        super(XTableWidget, self).dragMoveEvent(event)
        
    def dragDropFilter( self ):
        """
        Returns a drag and drop filter method.  If set, the method should \
        accept 2 arguments: a QWidget and a drag/drop event and process it.
        
        :usage      |from projexui.qt.QtCore import QEvent
                    |
                    |class MyWidget(QWidget):
                    |   def __init__( self, parent ):
                    |       super(MyWidget, self).__init__(parent)
                    |       
                    |       self._table = XTableWidget(self)
                    |       self._table.setDragDropFilter(self.handleDragDrop)
                    |
                    |   def handleDragDrop(self, object, event):
                    |       if ( event.type() == QEvent.DragEnter ):
                    |           event.acceptProposedActions()
                    |       elif ( event.type() == QEvent.Drop ):
                    |           print 'dropping'
        
        :return     <function> || <method> || None
        """
        filt = None
        if ( self._dragDropFilterRef ):
            filt = self._dragDropFilterRef()
            
        if ( not filt ):
            self._dragDropFilterRef = None
            
        return filt
     
    def dropEvent( self, event ):
        """
        Processes the drag drop event using the filter set by the \
        setDragDropFilter
        
        :param      event | <QDropEvent>
        """
        filt = self.dragDropFilter()
        if ( filt and not filt(self, event) ):
            return
        
        super(XTableWidget, self).dropEvent(event)
    
    def mimeData( self, items ):
        """
        Returns the mime data for dragging for this instance.
        
        :param      items | [<QTableWidgetItem>, ..]
        """
        func = self.dataCollector()
        if ( func ):
            return func(self, items)
            
        return super(XTableWidget, self).mimeData(items)
        
    def setColumns( self, columns ):
        """
        Sets the column count and list of columns to the inputed column list.
        
        :param      columns | [<str>, ..]
        """
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
    
    def setDataCollector( self, collector ):
        """
        Sets the method that will be used to collect mime data for dragging \
        items from this table.
        
        :warning    The data collector is stored as a weak-reference, so using \
                    mutable methods will not be stored well.  Things like \
                    instancemethods will not hold their pointer after they \
                    leave the scope that is being used.  Instead, use a \
                    classmethod or staticmethod to define the collector.
        
        :param      collector | <function> || <method> || None
        """
        if ( collector ):
            self._dataCollectorRef = weakref.ref(collector)
        else:
            self._dataCollectorRef = None
    
    def setDragDropFilter( self, ddFilter ):
        """
        Sets the drag drop filter for this widget.
        
        :warning    The dragdropfilter is stored as a weak-reference, so using \
                    mutable methods will not be stored well.  Things like \
                    instancemethods will not hold their pointer after they \
                    leave the scope that is being used.  Instead, use a \
                    classmethod or staticmethod to define the dragdropfilter.
        
        :param      ddFilter | <function> || <method> || None
        """
        if ( ddFilter ):
            self._dragDropFilterRef = weakref.ref(ddFilter)
        else:
            self._dragDropFilterRef = None

__designer_plugins__ = [XTableWidget]