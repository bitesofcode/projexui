""" Defines the XPagesWidget """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software, LLC'
__license__         = 'LGPL'

__maintainer__      = 'Projex Software, LLC'
__email__           = 'team@projexsoftware.com'


#------------------------------------------------------------------------------

from projex.text import nativestring

from projexui.qt import Signal, Slot, Property
from projexui.qt.QtCore import Qt

from projexui.qt.QtGui import QWidget,\
                              QLabel,\
                              QHBoxLayout,\
                              QToolButton,\
                              QSizePolicy,\
                              QSpinBox

from projexui.widgets.xcombobox import XComboBox

class XPagesWidget(QWidget):
    """ """
    currentPageChanged = Signal(int)
    pageSizeChanged    = Signal(int)
    pageCountChanged   = Signal(int)
    
    def __init__( self, parent = None ):
        super(XPagesWidget, self).__init__( parent )
        
        # define custom properties
        self._currentPage       = 1
        self._pageCount         = 10
        self._itemCount         = 0
        self._pageSize          = 50
        self._itemsTitle        = 'items'
        
        self._pagesSpinner  = QSpinBox()
        self._pagesSpinner.setMinimum(1)
        self._pagesSpinner.setMaximum(10)
        
        self._pageSizeCombo = XComboBox(self)
        self._pageSizeCombo.setHint('all')
        self._pageSizeCombo.addItems(['', '25', '50', '75', '100'])
        self._pageSizeCombo.setCurrentIndex(2)
        
        self._nextButton    = QToolButton(self)
        self._nextButton.setAutoRaise(True)
        self._nextButton.setArrowType(Qt.RightArrow)
        self._nextButton.setFixedWidth(16)
        
        self._prevButton    = QToolButton(self)
        self._prevButton.setAutoRaise(True)
        self._prevButton.setArrowType(Qt.LeftArrow)
        self._prevButton.setFixedWidth(16)
        self._prevButton.setEnabled(False)
        
        self._pagesLabel = QLabel('of 10 for ', self)
        self._itemsLabel = QLabel(' items per page', self)
        
        # define the interface
        layout = QHBoxLayout()
        layout.addWidget(QLabel('Page', self))
        layout.addWidget(self._prevButton)
        layout.addWidget(self._pagesSpinner)
        layout.addWidget(self._nextButton)
        layout.addWidget(self._pagesLabel)
        layout.addWidget(self._pageSizeCombo)
        layout.addWidget(self._itemsLabel)
        layout.addStretch(1)
        
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # create connections
        self._pageSizeCombo.currentIndexChanged.connect(self.pageSizePicked)
        self._nextButton.clicked.connect(self.gotoNext)
        self._prevButton.clicked.connect(self.gotoPrevious)
        self._pagesSpinner.editingFinished.connect(self.assignCurrentPage)
    
    def assignCurrentPage( self ):
        """
        Assigns the page for the spinner to be current.
        """
        self.setCurrentPage(self._pagesSpinner.value())
    
    def currentPage( self ):
        """
        Reutrns the current page for this widget.
        
        :return     <int>
        """
        return self._currentPage
    
    @Slot()
    def gotoFirst( self ):
        """
        Goes to the first page.
        
        :sa     setCurrentPage
        """
        self.setCurrentPage(1)
    
    @Slot()
    def gotoLast( self ):
        """
        Goes to the last page.
        
        :sa     setCurrentPage
        """
        self.setCurrentPage(self.pageCount())
    
    @Slot()
    def gotoNext( self ):
        """
        Goes to the next page.
        
        :sa     setCurrentPage
        """
        next_page = self.currentPage() + 1
        if ( next_page > self.pageCount() ):
            return
        
        self.setCurrentPage(next_page)
    
    @Slot()
    def gotoPrevious( self ):
        """
        Goes to the previous page.
        
        :sa     setCurrentPage
        """
        prev_page = self.currentPage() - 1
        if ( prev_page == 0 ):
            return
        
        self.setCurrentPage(prev_page)
    
    def itemCount( self ):
        """
        Returns the total number of items this widget holds.  If no item count
        is defined, it will not be displayed in the label, otherwise it will
        show.
        
        :return     <int>
        """
        return self._itemCount
    
    def itemsTitle( self ):
        """
        Returns the items title for this instance.
        
        :return     <str>
        """
        return self._itemsTitle
    
    def pageCount( self ):
        """
        Returns the number of pages that this widget holds.
        
        :return     <int>
        """
        return self._pageCount
    
    def pageSize( self ):
        """
        Returns the number of items that should be visible in a page.
        
        :return     <int>
        """
        return self._pageSize
    
    def pageSizeOptions( self ):
        """
        Returns the list of options that will be displayed for this default
        size options.
        
        :return     [<str>, ..]
        """
        return map(str, self._pageSizeCombo.items())
    
    def pageSizePicked( self, pageSize ):
        """
        Updates when the user picks a page size.
        
        :param      pageSize | <str>
        """
        try:
            pageSize = int(self._pageSizeCombo.currentText())
        except ValueError:
            pageSize = 0
        
        self.setPageSize(pageSize)
        self.pageSizeChanged.emit(pageSize)
    
    def refreshLabels( self ):
        """
        Refreshes the labels to display the proper title and count information.
        """
        itemCount = self.itemCount()
        title = self.itemsTitle()
        
        if ( not itemCount ):
            self._itemsLabel.setText(' %s per page' % title)
        else:
            msg = ' %s per page, %i %s total' % (title, itemCount, title)
            self._itemsLabel.setText(msg)
    
    @Slot(int)
    def setCurrentPage( self, pageno ):
        """
        Sets the current page for this widget to the inputed page.
        
        :param      pageno | <int>
        """
        if ( pageno == self._currentPage ):
            return
        
        if ( pageno <= 0 ):
            pageno = 1
        
        self._currentPage = pageno
        
        self._prevButton.setEnabled(pageno > 1)
        self._nextButton.setEnabled(pageno < self.pageCount())
        
        self._pagesSpinner.blockSignals(True)
        self._pagesSpinner.setValue(pageno)
        self._pagesSpinner.blockSignals(False)
        
        if ( not self.signalsBlocked() ):
            self.currentPageChanged.emit(pageno)
    
    @Slot(int)
    def setItemCount( self, itemCount ):
        """
        Sets the item count for this page to the inputed value.
        
        :param      itemCount | <int>
        """
        self._itemCount = itemCount
        self.refreshLabels()
    
    @Slot(str)
    def setItemsTitle( self, title ):
        """
        Sets the title that will be displayed when the items labels are rendered
        
        :param      title | <str>
        """
        self._itemsTitle = nativestring(title)
        self.refreshLabels()
    
    @Slot(int)
    def setPageCount( self, pageCount ):
        """
        Sets the number of pages that this widget holds.
        
        :param      pageCount | <int>
        """
        if ( pageCount == self._pageCount ):
            return
        
        pageCount = max(1, pageCount)
        
        self._pageCount = pageCount
        self._pagesSpinner.setMaximum(pageCount)
        self._pagesLabel.setText('of %i for ' % pageCount)
        
        if ( pageCount and self.currentPage() <= 0 ):
            self.setCurrentPage(1)
        
        elif ( pageCount < self.currentPage() ):
            self.setCurrentPage(pageCount)
        
        if ( not self.signalsBlocked() ):
            self.pageCountChanged.emit(pageCount)
        
        self._prevButton.setEnabled(self.currentPage() > 1)
        self._nextButton.setEnabled(self.currentPage() < pageCount)
    
    @Slot(int)
    def setPageSize( self, pageSize ):
        """
        Sets the number of items that should be visible in a page.  Setting the
        value to 0 will use all sizes
        
        :return     <int>
        """
        if self._pageSize == pageSize:
            return
        
        self._pageSize = pageSize
        
        # update the display size
        ssize = nativestring(pageSize)
        if ( ssize == '0' ):
            ssize = ''
        
        self._pageSizeCombo.blockSignals(True)
        index = self._pageSizeCombo.findText(ssize)
        self._pageSizeCombo.setCurrentIndex(index)
        self._pageSizeCombo.blockSignals(False)
    
    def setPageSizeOptions( self, options ):
        """
        Sets the options that will be displayed for this default size.
        
        :param      options | [<str>,. ..]
        """
        self._pageSizeCombo.blockSignals(True)
        self._pageSizeCombo.addItems(options)
        
        ssize = nativestring(self.pageSize())
        if ( ssize == '0' ):
            ssize = ''
        
        index = self._pageSizeCombo.findText()
        self._pageSizeCombo.setCurrentIndex(index)
        self._pageSizeCombo.blockSignals(False)
    
    x_itemsTitle = Property(str, itemsTitle, setItemsTitle)
    x_pageCount = Property(int, pageCount, setPageCount)
    x_pageSize = Property(int, pageSize, setPageSize)
    x_pageSizeOptions = Property(list, pageSizeOptions, setPageSizeOptions)
    
__designer_plugins__ = [XPagesWidget]