#!/usr/bin/python

""" Creates reusable Qt window components. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

#---------------------------------------------------------------------------

import logging
import os.path
import shutil
import webbrowser
import zipfile

from projex.text import nativestring

import projex.text
from projexui.qt import Signal
from projexui.qt.QtCore import Qt, QDir, QUrl, QObject, QThread

from projexui.widgets.xtreewidget import XTreeWidgetItem
from projexui.qt.QtGui import QApplication,\
                              QFileDialog,\
                              QMainWindow,\
                              QTreeWidgetItem

from projexui.qt.QtWebKit import QWebView, \
                                 QWebPage

import projexui

from projexui.windows.xdkwindow.xdkitem         import XdkItem, XdkEntryItem

SEARCH_HTML = """
<html>
    <head>
        <style>
            * { outline: none !important; }
            
            body {
                margin: 0.5em;
                padding: 0.5em;
                font-family: Arial, Verdana !important;
                font-size: 14px !important;
                width:100%%;
                height:95%%;
            }

            table   { font-size: 14px; } 
            h1      { font-size: 20px; }
            h2      { font-size: 16px; }
            h3      { font-size: 14px; }
            small   { font-size: 11px; color: gray; }
            
            a {
                color: rgb(40,100,150);
                font-weight: bold;
                text-decoration: none;
            }
            a:hover {
                color: rgb(60,120,250);
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        %s
    </body>
</html>
"""

class XdkWorker(QObject):
    loadingFinished = Signal(str)
    def loadFile(self, filename):
        # creates the new XdkItem
        filename = nativestring(filename)
        basename = os.path.basename(filename)
        name     = os.path.splitext(basename)[0]
        
        temp_dir  = nativestring(QDir.tempPath())
        temp_path = os.path.join(temp_dir, 'xdk/%s' % name)
        
        # remove existing files from the location
        if os.path.exists(temp_path):
            try:
                shutil.rmtree(temp_path, True)
            except:
                pass
        
        # make sure we have the temp location available
        if not os.path.exists(temp_path):
            try:
                os.makedirs(temp_path)
            except:
                pass
        
        # extract the zip files to the temp location
        zfile = zipfile.ZipFile(filename, 'r')
        zfile.extractall(temp_path)
        zfile.close()
        
        # load the table of contents
        self.loadingFinished.emit(filename)

#----------------------------------------------------------------------

class XdkWindow(QMainWindow):
    """ """
    loadFileRequested = Signal(str)
    
    def __init__( self, parent = None ):
        super(XdkWindow, self).__init__( parent )
        
        # load the user interface
        projexui.loadUi(__file__, self)
        
        # define custom properties
        self._currentContentsIndex = -1
        self._worker = XdkWorker()
        self._workerThread = QThread()
        self._worker.moveToThread(self._workerThread)
        self._workerThread.start()
        
        # set default properties
        self.setAcceptDrops(True)
        self.setAttribute( Qt.WA_DeleteOnClose )
        self.uiFindNextBTN.setDefaultAction(self.uiFindNextACT)
        self.uiFindPrevBTN.setDefaultAction(self.uiFindPrevACT)
        self.uiFindWIDGET.setVisible(False)
        self.uiSearchWEB.page().setLinkDelegationPolicy(
                                            QWebPage.DelegateAllLinks)
        
        self.refreshUi()
        
        # connect widgets
        self.uiContentsTAB.currentChanged.connect(self.refreshUi)
        self.uiContentsTAB.tabCloseRequested.connect(self.closeContentsWidget)
        self.uiContentsTREE.itemExpanded.connect(self.loadItem)
        self.uiContentsTREE.itemSelectionChanged.connect(self.refreshContents)
        self.uiSearchTXT.returnPressed.connect(self.search)
        self.uiSearchWEB.linkClicked.connect(self.gotoUrl)
        self.uiIndexTREE.itemSelectionChanged.connect(self.refreshFromIndex)
        
        # connect find actions
        self.uiBackACT.triggered.connect(self.goBack)
        self.uiForwardACT.triggered.connect(self.goForward)
        self.uiHomeACT.triggered.connect(self.goHome )
        self.uiFindTXT.textChanged.connect( self.findNext )
        self.uiFindTXT.returnPressed.connect( self.findNext )
        self.uiFindNextACT.triggered.connect( self.findNext )
        self.uiFindPrevACT.triggered.connect( self.findPrev )
        self.uiFindACT.triggered.connect(self.showFind)
        self.uiFindCloseBTN.clicked.connect(self.uiFindWIDGET.hide)
        self.uiCopyTextACT.triggered.connect( self.copyText )
        
        # connect zoom actions
        self.uiZoomResetACT.triggered.connect( self.zoomReset )
        self.uiZoomInACT.triggered.connect( self.zoomIn )
        self.uiZoomOutACT.triggered.connect( self.zoomOut )
        
        # connect file actions
        self.uiLoadACT.triggered.connect( self.loadFilename )
        self.uiNewTabACT.triggered.connect( self.addContentsWidget )
        self.uiCloseTabACT.triggered.connect( self.closeContentsWidget )
        self.uiQuitACT.triggered.connect( self.close )
        
        # connect the signals
        self.loadFileRequested.connect(self._worker.loadFile)
        self._worker.loadingFinished.connect(self._addXdkItem)
        QApplication.instance().aboutToQuit.connect(self._cleanupWorker)
    
    def _addXdkItem(self, filename):
        item = XdkItem(filename)
        
        # add the xdk content item
        self.uiContentsTREE.addTopLevelItem(item)
        
        # add the index list items
        self.uiIndexTREE.blockSignals(True)
        self.uiIndexTREE.setUpdatesEnabled(False)
        for name, url in item.indexlist():
            item = XTreeWidgetItem([name])
            item.setToolTip(0, url)
            item.setFixedHeight(22)
            self.uiIndexTREE.addTopLevelItem(item)
        self.uiIndexTREE.blockSignals(False)
        self.uiIndexTREE.setUpdatesEnabled(True)
        self.uiIndexTREE.sortByColumn(0, Qt.AscendingOrder)
        
        self.unsetCursor()
    
    def _cleanupWorker(self):
        if self._workerThread is None:
            return
            
        self._workerThread.quit()
        self._workerThread.wait()
        
        self._worker.deleteLater()
        self._workerThread.deleteLater()
        
        self._worker = None
        self._workerThread = None
    
    def __gotoUrl(self, url):
        if url.toLocalFile():
            self.gotoUrl(url.toString())
        else:
            webbrowser.open(nativestring(url.toString()))
    
    def addContentsWidget( self ):
        """
        Adds a new contents widget tab into the contents tab.
        
        :return     <QWebView>
        """
        curr_widget = self.currentContentsWidget()
        widget = QWebView(self)
        page = widget.page()
        page.setLinkDelegationPolicy(page.DelegateAllLinks)
            
        self.uiContentsTAB.blockSignals(True)
        self.uiContentsTAB.addTab(widget, 'Documentation')
        self.uiContentsTAB.setCurrentIndex(self.uiContentsTAB.count() - 1)
        self.uiContentsTAB.blockSignals(False)
        
        self._currentContentsIndex = self.uiContentsTAB.count() - 1
        
        if curr_widget:
            widget.setUrl(curr_widget.url())
        
        widget.titleChanged.connect(self.refreshUi)
        widget.linkClicked.connect(self.__gotoUrl)
        
        return widget
    
    def closeContentsWidget( self ):
        """
        Closes the current contents widget.
        """
        widget = self.currentContentsWidget()
        if ( not widget ):
            return
            
        widget.close()
        widget.setParent(None)
        widget.deleteLater()
    
    def copyText( self ):
        """
        Copies the selected text to the clipboard.
        """
        view = self.currentWebView()
        QApplication.clipboard().setText(view.page().selectedText())
    
    def currentContentsIndex( self ):
        """
        Returns the last index used for the contents widgets.
        
        :return     <int>
        """
        return self._currentContentsIndex
    
    def currentContentsWidget( self, autoadd = False ):
        """
        Returns the current contents widget based on the cached index.  If \
        no widget is specified and autoadd is True, then a new widget will \
        be added to the tab.
        
        :param      autoadd | <bool>
        
        :return     <QWebView>
        """
        widget = self.uiContentsTAB.widget(self.currentContentsIndex())
        if ( not isinstance(widget, QWebView) ):
            widget = None
        
        if ( not widget and autoadd ):
            widget = self.addContentsWidget()
        
        return widget
    
    def currentWebView(self):
        return self.uiContentsTAB.currentWidget()
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
    
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                self.loadFilename(nativestring(url.toLocalFile()))
    
    def findNext( self ):
        """
        Looks for the previous occurance of the current search text.
        """
        text = self.uiFindTXT.text()
        view = self.currentWebView()
        
        options =  QWebPage.FindWrapsAroundDocument
        
        if ( self.uiCaseSensitiveCHK.isChecked() ):
            options |= QWebPage.FindCaseSensitively
        
        view.page().findText(text, options)
    
    def findPrev( self ):
        """
        Looks for the previous occurance of the current search text.
        """
        text = self.uiFindTXT.text()
        view = self.currentWebView()
        
        options =  QWebPage.FindWrapsAroundDocument
        options |= QWebPage.FindBackward
        
        if ( self.uiCaseSensitiveCHK.isChecked() ):
            options |= QWebPage.FindCaseSensitively
        
        view.page().findText(text, options)
    
    def findXdk( self, name ):
        """
        Looks up the xdk item based on the current name.
        
        :param      name | <str>
        
        :return     <XdkItem> || None
        """
        for i in range(self.uiContentsTREE.topLevelItemCount()):
            item = self.uiContentsTREE.topLevelItem(i)
            if ( item.text(0) == name ):
                return item
        return None
    
    def goBack( self ):
        widget = self.currentContentsWidget()
        if ( widget ):
            widget.page().history().back()
    
    def goForward( self ):
        widget = self.currentContentsWidget()
        if ( widget ):
            widget.page().history().forward()
    
    def goHome( self ):
        widget = self.currentContentsWidget()
        if ( widget ):
            widget.history().goHome()
    
    def gotoUrl(self, url):
        try:
            urlstr = url.toString()
        except:
            urlstr = nativestring(url)
        
        if not urlstr.endswith('.html'):
            self.gotoItem(urlstr)
            return
        
        if not QApplication.keyboardModifiers() == Qt.ControlModifier:
            widget = self.currentContentsWidget(autoadd = True)
        else:
            widget = self.addContentsWidget()
        
        index = self.uiContentsTAB.indexOf(widget)
        self.uiContentsTAB.setCurrentIndex(index)
        widget.setUrl(QUrl(url))
    
    def gotoItem(self, path):
        """
        Goes to a particular path within the XDK.
        
        :param      path | <str>
        """
        if not path:
            return
        
        sections = nativestring(path).split('/')
        check = projex.text.underscore(sections[0])
        
        for i in range(self.uiContentsTREE.topLevelItemCount()):
            item = self.uiContentsTREE.topLevelItem(i)
            if check in (projex.text.underscore(item.text(0)), item.text(1)):
                item.gotoItem('/'.join(sections[1:]))
                break
    
    def loadItem( self, item ):
        """
        Loads the inputed item.
        
        :param      item | <QTreeWidgetItem>
        """
        if isinstance(item, XdkEntryItem):
            item.load()
    
    def loadedFilenames( self ):
        """
        Returns a list of all the xdk files that are currently loaded.
        
        :return     [<str>, ..]
        """
        output = []
        for i in range(self.uiContentsTREE.topLevelItemCount()):
            item = self.uiContentsTREE.topLevelItem(i)
            output.append(nativestring(item.filepath()))
        return output
    
    def loadFilename( self, filename = '' ):
        """
        Loads a new XDK file into the system.
        
        :param      filename | <str>
        
        :return     <bool> | success
        """
        if ( not (filename and isinstance(filename, basestring)) ):
            filename = QFileDialog.getOpenFileName( self,
                                                    'Open XDK File',
                                                    QDir.currentPath(),
                                                    'XDK Files (*.xdk)' )
            
            if type(filename) == tuple:
                filename = nativestring(filename[0])
            
            if not filename:
                return False
        
        if not (filename and os.path.exists(filename)):
            return False
        
        elif filename in self.loadedFilenames():
            return False
        
        self.loadFileRequested.emit(filename)
        self.setCursor(Qt.WaitCursor)
        
        return True
    
    def refreshFromIndex( self ):
        """
        Refreshes the documentation from the selected index item.
        """
        item = self.uiIndexTREE.currentItem()
        if ( not item ):
            return
        
        self.gotoUrl(item.toolTip(0))
    
    def refreshContents( self ):
        """
        Refreshes the contents tab with the latest selection from the browser.
        """
        item = self.uiContentsTREE.currentItem()
        if not isinstance(item, XdkEntryItem):
           return
        
        item.load()
        url = item.url()
        if url:
            self.gotoUrl(url)
    
    def refreshUi( self ):
        """
        Refreshes the interface based on the current settings.
        """
        widget      = self.uiContentsTAB.currentWidget()
        is_content  = isinstance(widget, QWebView)
        
        if is_content:
            self._currentContentsIndex = self.uiContentsTAB.currentIndex()
            history = widget.page().history()
        else:
            history = None
        
        self.uiBackACT.setEnabled(is_content and history.canGoBack())
        self.uiForwardACT.setEnabled(is_content and history.canGoForward())
        self.uiHomeACT.setEnabled(is_content)
        self.uiNewTabACT.setEnabled(is_content)
        self.uiCopyTextACT.setEnabled(is_content)
        self.uiCloseTabACT.setEnabled(is_content and
                                      self.uiContentsTAB.count() > 2)
        
        for i in range(1, self.uiContentsTAB.count()):
            widget = self.uiContentsTAB.widget(i)
            self.uiContentsTAB.setTabText(i, widget.title())
    
    def search( self ):
        """
        Looks up the current search terms from the xdk files that are loaded.
        """
        QApplication.instance().setOverrideCursor(Qt.WaitCursor)
        
        terms = nativestring(self.uiSearchTXT.text())
        
        html = []
        
        entry_html = '<a href="%(url)s">%(title)s</a><br/>'\
                     '<small>%(url)s</small>'
        
        for i in range(self.uiContentsTREE.topLevelItemCount()):
            item = self.uiContentsTREE.topLevelItem(i)
            
            results = item.search(terms)
            results.sort(lambda x, y: cmp(y['strength'], x['strength']))
            for item in results:
                html.append( entry_html % item )
        
        if ( not html ):
            html.append('<b>No results were found for %s</b>' % terms)
        
        self.uiSearchWEB.setHtml(SEARCH_HTML % '<br/><br/>'.join(html))
        
        QApplication.instance().restoreOverrideCursor()
    
    def setFocus(self, focus):
        self.uiSearchTXT.setFocus()
    
    def showFind( self ):
        self.uiFindWIDGET.show()
        self.uiFindTXT.setFocus()
        self.uiFindTXT.selectAll()
    
    def zoomIn( self ):
        view = self.currentWebView()
        view.setZoomFactor(view.zoomFactor() + 0.1)
    
    def zoomOut( self ):
        view = self.currentWebView()
        view.setZoomFactor(view.zoomFactor() - 0.1)
    
    def zoomReset( self ):
        view = self.currentWebView()
        view.setZoomFactor(1)
    
    @staticmethod
    def browse( parent, filename = '' ):
        """
        Creates a new XdkWidnow for browsing an XDK file.
        
        :param      parent      | <QWidget>
                    filename    | <str>
        """
        dlg = XdkWindow(parent)
        dlg.show()
        
        if ( filename ):
            dlg.loadFilename(filename)