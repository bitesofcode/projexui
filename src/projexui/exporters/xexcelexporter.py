#!/usr/bin/python

""" Defines the XExcelExporter class for exporting data to Excel files. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

import logging

from projex.text import nativestring

from projexui.qt import unwrapVariant
from projexui.qt.QtCore import Qt
from projexui.xexporter import XExporter

logger = logging.getLogger(__name__)

try:
    import xlwt
except ImportError:
    xlwt = None

class XExcelExporter(XExporter):
    def __init__(self):
        super(XExcelExporter, self).__init__('Excel spreadsheet', '.xls')
        
        self._currrow = 0
        
        # set default information
        self.setFlag(XExporter.Flags.SupportsTree)
    
    def exportTree(self, tree, filename):
        """
        Exports the inputed tree object to the given excel file.
        
        :param      tree     | <QTreeWidget>
                    filename | <str>
        
        :return     <bool>
        """
        book = xlwt.Workbook()
        
        # determine the title for the sheet to export
        title = nativestring(tree.windowTitle())
        if not title:
            title = nativestring(tree.objectName())
        if not title:
            title = 'Sheet 1'
        
        sheet = book.add_sheet(title)
        
        # determine visible columns to export
        cols = [c for c in range(tree.columnCount()) \
                if not tree.isColumnHidden(c)]
        
        # export the column headers
        hitem = tree.headerItem()
        for c, col in enumerate(cols):
            sheet.write(0, c, nativestring(hitem.text(col)))
        
        self._currrow = 1
        for i in range(tree.topLevelItemCount()):
            self.exportTreeItem(sheet, cols, tree.topLevelItem(i))
        
        book.save(filename)
        return True
    
    def exportTreeItem(self, sheet, cols, item):
        """
        Exports the inputed item to the given Excel worksheet for the
        given visible columns.
        
        :param      sheet | <xlwt.WorkSheet>
                    cols  | [<int>, ..]
                    item  | <QTreeWidgetItem>
        """
        # export item information
        for c, col in enumerate(cols):
            data = unwrapVariant(item.data(Qt.EditRole, col))
            if data:
                sheet.write(self._currrow, c, nativestring(data))
            else:
                sheet.write(self._currrow, c, nativestring(item.text(col)))
        
        self._currrow += 1
        
        # export children as rows
        for c in range(item.childCount()):
            self.exportTreeItem(sheet, cols, item.child(c))

# only register if we have a valid excel library installed
if xlwt:
    XExporter.register(XExcelExporter())
else:
    logger.debug('xlwt is required for exporting.')