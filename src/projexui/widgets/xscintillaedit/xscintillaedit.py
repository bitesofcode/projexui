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

import logging
import os
import sys

from projexui.qt import Signal
from projexui.qt.QtCore   import Qt,\
                                 QDir,\
                                 QFile
                           
from projexui.qt.QtGui    import QFileDialog,\
                                 QFont,\
                                 QFontMetrics,\
                                 QMessageBox,\
                                 QPixmap,\
                                 QApplication

from projex.text import nativestring
from projex.enum    import enum

from projexui.widgets.xscintillaedit.xscintillaeditoptions \
                                               import XScintillaEditOptions
from projexui.widgets.xscintillaedit.xscintillaeditcolorset \
                                               import XScintillaEditColorSet
from projexui.widgets.xscintillaedit.xlanguage import XLanguage

import projexui.resources

logger = logging.getLogger(__name__)

from projexui.qt import Qsci
if not Qsci:
    from projexui.qt.QtGui import QTextEdit as QsciScintilla
else:
    QsciScintilla = Qsci.QsciScintilla

class XScintillaEdit(QsciScintilla):
    """ Creates some convenience methods on top of the QsciScintilla class. """
    
    __designer_icon__ = projexui.resources.find('img/ui/codeedit.png')
    
    breakpointsChanged = Signal()
    fontSizeChanged    = Signal(int)
    
    def __init__( self, parent, filename = '', lineno = 0 ):
        super(XScintillaEdit, self).__init__(parent)
        
        # create custom properties
        self._filename              = ''
        self._dirty                 = False
        self._marginsFont           = QFont()
        self._saveOnClose           = True
        self._colorSet              = None
        self._language              = None
        
        # define markers
        breakpoint_ico = projexui.resources.find('img/debug/break.png')
        debug_ico      = projexui.resources.find('img/debug/current.png')
        
        self._breakpointMarker      = self.markerDefine(QPixmap(breakpoint_ico))
        self._currentDebugMarker    = self.markerDefine(QPixmap(debug_ico))
        
        # set one time properties
        self.setFolding(            QsciScintilla.BoxedTreeFoldStyle )
        self.setBraceMatching(      QsciScintilla.SloppyBraceMatch )
        self.setContextMenuPolicy(  Qt.NoContextMenu )
        
        # load the inputed filename
        self.initOptions(XScintillaEditOptions())
        self.load(filename, lineno)
    
    def addBreakpoint( self, lineno = -1 ):
        """
        Adds a breakpoint for the given line number to this edit.
        
        :note       The lineno is 0-based, while the editor displays lines as
                    a 1-based system.  So, if you want to put a breakpoint at
                    visual line 3, you would pass in lineno as 2
        
        :param      lineno | <int>
        """
        if ( lineno == -1 ):
            lineno, colno = self.getCursorPosition()
            
        self.markerAdd(lineno, self._breakpointMarker)
        
        if ( not self.signalsBlocked() ):
            self.breakpointsChanged.emit()
    
    def breakpoints( self ):
        """
        Returns a list of lines that have breakpoints for this edit.
        
        :return     [<int>, ..]
        """
        lines = []
        result = self.markerFindNext(0, self._breakpointMarker + 1)
        while ( result != -1 ):
            lines.append(result)
            result = self.markerFindNext(result + 1, self._breakpointMarker + 1)
        return lines
    
    def colorSet( self ):
        """
        Returns the color set for this edit.
        
        :return     <XScintillaEditColorSet> || None
        """
        return self._colorSet
    
    def clearBreakpoints( self ):
        """
        Clears the file of all the breakpoints.
        """
        self.markerDeleteAll(self._breakpointMarker)
        
        if ( not self.signalsBlocked() ):
            self.breakpointsChanged.emit()
    
    def clearCurrentDebugLine( self ):
        """
        Clears the current debug line for this edit.
        """
        self.markerDeleteAll(self._currentDebugMarker)
    
    def closeEvent( self, event ):
        """
        Overloads the close event for this widget to make sure that the data \
        is properly saved before exiting.
        
        :param      event | <QCloseEvent>
        """
        if ( not (self.saveOnClose() and self.checkForSave()) ):
            event.ignore()
        else:
            super(XScintillaEdit, self).closeEvent(event)
    
    def checkForSave( self ):
        """
        Checks to see if the current document has been modified and should \
        be saved.
        
        :return     <bool>
        """
        # if the file is not modified, then save is not needed
        if ( not self.isModified() ):
            return True
        
        options     = QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        question    = 'Would you like to save your changes to %s?' % \
                                            self.windowTitle()
                                            
        answer      = QMessageBox.question( None, 
                                            'Save Changes', 
                                            question, 
                                            options )
        
        if ( answer == QMessageBox.Yes ):
            return self.save()
        elif ( answer == QMessageBox.Cancel ):
            return False
        return True
    
    def currentLine( self ):
        """
        Returns the current line number.
        
        :return     <int>
        """
        return self.getCursorPosition()[0]
    
    def filename( self ):
        """
        Returns the filename that is associated with this edit.
        
        :return     <str>
        """
        return self._filename
    
    def findNext( self, 
                  text, 
                  wholeWords    = False, 
                  caseSensitive = False, 
                  regexed       = False,
                  wrap          = True ):
        """
        Looks up the next iteration fot the inputed search term.
        
        :param      text            | <str>
                    wholeWords      | <bool>
                    caseSensitive   | <bool>
                    regexed         | <bool>
        
        :return     <bool>
        """
        return self.findFirst( text,
                               regexed,
                               caseSensitive,
                               wholeWords,
                               wrap,
                               True )
    
    def findPrev( self,
                  text,
                  wholeWords    = False,
                  caseSensitive = False,
                  regexed       = False,
                  wrap          = True ):
        """
        Looks up the previous iteration for the inputed search term.
        
        :param      text            | <str>
                    wholeWords      | <bool>
                    caseSensitive   | <bool>
                    regexed         | <bool>
                    wrap            | <bool>
        
        :return     <bool>
        """
        lineFrom, indexFrom, lineTo, indexTo = self.getSelection()
        
        return self.findFirst( text,
                               regexed,
                               caseSensitive,
                               wholeWords,
                               wrap,
                               False,
                               lineFrom,
                               indexFrom )
                               
    def findRepl( self, 
                  text,
                  repl,
                  caseSensitive = False,
                  replaceAll    = False ):
        """
        Looks for the inputed text and replaces it with the given replacement \
        text.
        
        :param      text            | <str>
                    repl            | <str>
                    caseSensitive   | <bool>
                    replaceAll      | <bool>
        
        :return     <int> number of items replace
        """
        # make sure something is selected
        if ( not text ):
            return 0
        
        # make sure we have some text selected to replace
        if ( self.selectedText() != text ):
            found = self.findNext( text,
                                   False,
                                   caseSensitive,
                                   False,
                                   True )
            
            if ( not found ):
                return 0
        
        sel     = self.getSelection()
        alltext = self.text()
        
        # replace all instances
        if ( replaceAll ):
            sensitivity = Qt.CaseInsensitive
            if ( caseSensitive ):
                sensitivity = Qt.CaseSensitive
                
            count = alltext.count(text, sensitivity)
            alltext.replace(text, repl, sensitivity)
            
        else:
            count    = 1
            startpos = self.positionFromLineIndex(sel[0], sel[1])
            alltext.replace(startpos, len(text), repl)
            
        self.setText(alltext)
        
        if ( count == 1 ):
            sel = list(sel)
            sel[3] += len(repl) - len(text)
            
            self.setSelection(*sel)
        else:
            self.findNext( repl,
                           False,
                           caseSensitive,
                           False,
                           True )
        
        return count
        
    def initOptions(self, options):
        """
        Initializes the edit with the inputed options data set.
        
        :param      options | <XScintillaEditOptions>
        """
        self.setAutoIndent(             options.value('autoIndent'))
        self.setIndentationsUseTabs(    options.value('indentationsUseTabs'))
        self.setTabIndents(             options.value('tabIndents'))
        self.setTabWidth(               options.value('tabWidth'))
        
        self.setCaretLineVisible(       options.value('showCaretLine'))
        self.setShowWhitespaces(        options.value('showWhitespaces'))
        self.setMarginLineNumbers( 0,   options.value('showLineNumbers'))
        self.setIndentationGuides(      options.value('showIndentations'))
        self.setEolVisibility(          options.value('showEndlines'))
        
        if options.value('showLimitColumn'):
            self.setEdgeMode(self.EdgeLine)
            self.setEdgeColumn(options.value('limitColumn'))
        else:
            self.setEdgeMode(self.EdgeNone)
        
        if options.value('showLineWrap'):
            self.setWrapMode(self.WrapWord)
        else:
            self.setWrapMode(self.WrapNone)
        
        # set the autocompletion source
        if options.value('autoComplete'):
            self.setAutoCompletionSource(QsciScintilla.AcsAll)
        else:
            self.setAutoCompletionSource(QsciScintilla.AcsNone)
        
        self.setAutoCompletionThreshold(options.value('autoCompleteThreshold'))
        
        # update the font information
        font = options.value('documentFont')
        font.setPointSize(options.value('documentFontSize'))
        self.setFont(font)
        
        # udpate the lexer
        lexer = self.lexer()
        if lexer:
            lexer.setFont(font)
        
        # create the margin font option
        mfont = options.value('documentMarginFont')
        mfont.setPointSize(font.pointSize() - 2)
        self.setMarginsFont(mfont)
        self.setMarginWidth(0, QFontMetrics(mfont).width('0000000') + 5)
    
    def insertComments( self, comment = None ):
        """
        Inserts comments into the editor based on the current selection.\
        If no comment string is supplied, then the comment from the language \
        will be used.
        
        :param      comment | <str> || None
        
        :return     <bool> | success
        """
        if ( not comment ):
            lang = self.language()
            if ( lang ):
                comment = lang.lineComment()
        
        if ( not comment ):
            return False
        
        startline, startcol, endline, endcol = self.getSelection()
        line, col = self.getCursorPosition()
        
        for lineno in range(startline, endline+1 ):
            self.setCursorPosition(lineno, 0)
            self.insert(comment)
        
        self.setSelection(startline, startcol, endline, endcol)
        self.setCursorPosition(line, col)
        return True
    
    def keyPressEvent( self, event ):
        """
        Overloads the keyPressEvent method to support backtab operations.
        
        :param      event | <QKeyPressEvent>
        """
        if ( event.key() == Qt.Key_Backtab ):
            self.unindentSelection()
        else:
            super(XScintillaEdit, self).keyPressEvent(event)
    
    def language( self ):
        """
        Returns the language that this edit is being run in.
        
        :return     <XLanguage> || None
        """
        return self._language
    
    def load( self, filename, lineno = 0 ):
        """
        Loads the inputed filename as the current document for this edit.
        
        :param      filename | <str>
                    lineno   | <int>
        
        :return     <bool> | success
        """
        filename = nativestring(filename)
        
        if ( not (filename and os.path.exists(filename)) ):
            return False
        
        # load the file
        docfile = QFile(filename)
        if ( not docfile.open(QFile.ReadOnly) ):
            return False
            
        success = self.read(docfile)
        docfile.close()
        
        if ( not success ):
            return False
        
        self._filename = nativestring(filename)
        ext = os.path.splitext(filename)[1]
        self.setCurrentLine(lineno)
        
        lang = XLanguage.byFileType(ext)
        if ( lang != self.language() ):
            self.setLanguage(lang)
        
        self.setModified(False)
        
        return True
    
    def removeComments( self, comment = None ):
        """
        Inserts comments into the editor based on the current selection.\
        If no comment string is supplied, then the comment from the language \
        will be used.
        
        :param      comment | <str> || None
        
        :return     <bool> | success
        """
        if ( not comment ):
            lang = self.language()
            if ( lang ):
                comment = lang.lineComment()
        
        if ( not comment ):
            return False
        
        startline, startcol, endline, endcol = self.getSelection()
        len_comment = len(comment)
        line, col = self.getCursorPosition()
        
        for lineno in range(startline, endline+1 ):
            self.setSelection(lineno, 0, lineno, len_comment)
            if ( self.selectedText() == comment ):
                self.removeSelectedText()
        
        self.setSelection(startline, startcol, endline, endcol)    
        self.setCursorPosition(line, col)
        
        return True
    
    def removeBreakpoint( self, lineno = -1 ):
        """
        Removes the breakpoint at the inputed line number.  If the lineno is -1,
        then the current line number will be used
        
        :note       The lineno is 0-based, while the editor displays lines as
                    a 1-based system.  So, if you remove a breakpoint at
                    visual line 3, you would pass in lineno as 2
        
        :param      lineno | <int>
        """
        if ( lineno == -1 ):
            lineno, colno = self.getCursorPosition()
        
        self.markerDelete(lineno, self._breakpointMarker)
        
        if ( not self.signalsBlocked() ):
            self.breakpointsChanged.emit()
    
    def save( self ):
        """
        Saves the current document out to its filename.
        
        :sa     saveAs
        
        :return     <bool> | success
        """
        return self.saveAs( self.filename() )
    
    def saveAs( self, filename = '' ):
        """
        Saves the current document to the inputed filename.  If no filename \
        is supplied, then the user will be prompted to supply a filename.
        
        :param      filename | <str>
        
        :return     <bool> | success
        """
        if ( not (filename and isinstance(filename, basestring)) ):
            langTypes = XLanguage.pluginFileTypes()
            filename = QFileDialog.getSaveFileName( None,
                                                    'Save File As...',
                                                    QDir.currentPath(),
                                                    langTypes)
            
            if type(filename) == tuple:
                filename = nativestring(filename[0])
        
        if ( not filename ):
            return False
        
        docfile = QFile(filename)
        if ( not docfile.open(QFile.WriteOnly) ):
            logger.warning('Could not open %s for writing.' % filename)
            return False
        
        success = self.write(docfile)
        docfile.close()
        
        if success:
            filename = nativestring(filename)
            self._filename = filename
            
            self.setModified(False)
            
            # set the language
            lang = XLanguage.byFileType(os.path.splitext(filename)[1])
            if ( lang != self.language() ):
                self.setLanguage(lang)
        
        return success
    
    def saveOnClose( self ):
        """
        Returns whether or not this widget should check for save before \
        closing.
        
        :return     <bool>
        """
        return self._saveOnClose
    
    def setBreakpoints( self, breakpoints ):
        """
        Sets the breakpoints for this edit to the inputed list of breakpoints.
        
        :param      breakpoints | [<int>, ..]
        """
        self.clearBreakpoints()
        for breakpoint in breakpoints:
            self.addBreakpoint(breakpoint)
    
    def setColorSet( self, colorSet ):
        """
        Sets the color set for this edit to the inputed set.
        
        :param      colorSet | <XColorSet>
        """
        self._colorSet = colorSet
        
        if ( not colorSet ):
            return
        
        palette = self.palette()
        palette.setColor( palette.Base, colorSet.color('Background'))
        self.setPalette(palette)
        
        # set the global colors
        self.setCaretForegroundColor(
                                colorSet.color('CaretForeground'))
        self.setMarginsBackgroundColor(
                                colorSet.color('MarginsBackground'))
        self.setMarginsForegroundColor(
                                colorSet.color('MarginsForeground'))
        self.setPaper(          colorSet.color('Background'))
        self.setSelectionBackgroundColor(
                                colorSet.color('SelectionBackground'))
        self.setSelectionForegroundColor(
                                colorSet.color('SelectionForeground'))
        self.setFoldMarginColors(colorSet.color('FoldMarginsForeground'),
                                 colorSet.color('FoldMarginsBackground'))
        self.setCallTipsBackgroundColor(
                                colorSet.color('CallTipsBackground'))
        self.setCallTipsForegroundColor(
                                colorSet.color('CallTipsForeground'))
        self.setCallTipsHighlightColor(
                                colorSet.color('CallTipsHighlight'))
        self.setEdgeColor(      colorSet.color('Edge'))
        self.setMarkerBackgroundColor(
                                colorSet.color('MarkerBackground'))
        self.setMarkerForegroundColor(
                                colorSet.color('MarkerForeground'))
        self.setMatchedBraceBackgroundColor(
                                colorSet.color('MatchedBraceBackground'))
        self.setMatchedBraceForegroundColor(
                                colorSet.color('MatchedBraceForeground'))
        self.setUnmatchedBraceBackgroundColor(
                                colorSet.color('UnmatchedBraceBackground'))
        self.setUnmatchedBraceForegroundColor(
                                colorSet.color('UnmatchedBraceForeground'))
        self.setColor(          colorSet.color('Text'))
        
        self.setIndentationGuidesBackgroundColor(
                                    colorSet.color('IndentBackground'))
        self.setIndentationGuidesForegroundColor(
                                colorSet.color('IndentForeground'))
        
        # backwards support
        if ( hasattr(self, 'setCaretBackgroundColor') ):
            self.setCaretBackgroundColor(
                                    colorSet.color('CaretBackground'))
        elif ( hasattr(self, 'setCaretLineBackgroundColor') ):
            self.setCaretLineBackgroundColor(
                                    colorSet.color('CaretBackground'))
                                    
        
        # supported in newer QScintilla versions
        if ( hasattr(self, 'setIndicatorForegroundColor') ):
            self.setIndicatorForegroundColor(
                                    colorSet.color('IndicatorForeground'))
            self.setIndicatorOutlineColor(
                                    colorSet.color('IndicatorOutline'))
        
        # set the language and lexer colors
        lang  = self.language()
        lexer = self.lexer()
        
        if ( lang and lexer ):
            lang.setColorSet(lexer, colorSet)
    
    def setCurrentDebugLine( self, lineno ):
        """
        Returns the line number for the documents debug line.
        
        :param      lineno | <int>
        """
        self.markerDeleteAll(self._currentDebugMarker)
        self.markerAdd(lineno, self._currentDebugMarker)
        self.setCurrentLine(lineno)
        
    def setCurrentLine( self, lineno ):
        """
        Sets the current line number for the edit to the inputed line number.
        
        :param      lineno | <int>
        """
        self.setCursorPosition(lineno, 0)
        self.ensureLineVisible(lineno)
    
    def setLanguage(self, language):
        self._language = language
        self._dirty = True
        
    def setLineMarginWidth( self, width ):
        self.setMarginWidth( self.SymbolMargin, width )
    
    def setSaveOnClose( self, state ):
        """
        Sets whether or not this widget should check for save before closing.
        
        :param      state | <bool>
        """
        self._saveOnClose = state
    
    def setShowFolding( self, state ):
        if ( state ):
            self.setFolding( self.BoxedTreeFoldStyle )
        else:
            self.setFolding( self.NoFoldStyle )
    
    def setShowLineNumbers( self, state ):
        self.setMarginLineNumbers( self.SymbolMargin, state )
    
    def setShowWhitespaces( self, state ):
        if ( state ):
            self.setWhitespaceVisibility( QsciScintilla.WsVisible )
        else:
            self.setWhitespaceVisibility( QsciScintilla.WsInvisible )
    
    def showEvent(self, event):
        super(XScintillaEdit, self).showEvent(event)
        
        if self._dirty:
            self._dirty = False
            
            language = self.language()
            self.setLexer(None)
            
            # grab the language from the lang module if it is a string
            if language and type(language) != XLanguage:
                language = XLanguage.byName(language)
            
            # collect the language's lexer
            if not language:
                return
            
            if language.tabWidth():
                self.setTabWidth(language.tabWidth())
            
            lexer = language.createLexer(self, self._colorSet)
            if not lexer:
                return
            
            # update the margins font
            mfont = QFont(self.font())
            mfont.setPointSize(mfont.pointSize() - 2)
            self.setMarginsFont(mfont)
            
            QApplication.sendPostedEvents(self, -1)
            
            # hack to force update the colors
            for i in range(100):
                lexer.setColor(lexer.color(i), i)
    
    def showFolding( self ):
        return self.folding() != self.NoFoldStyle
    
    def showLineNumbers( self ):
        return self.marginLineNumbers( self.SymbolMargin )
    
    def showWhitespaces( self ):
        return self.whitespaceVisibility() == QsciScintilla.WsVisible
    
    def unindentSelection( self ):
        """
        Unindents the current selected text.
        """
        sel = self.getSelection()
        
        for line in range(sel[0], sel[2] + 1):
            self.unindent(line)
    
    def wheelEvent( self, event ):
        # scroll the font up and down with the wheel event
        if ( event.modifiers() == Qt.ControlModifier ):
            font            = self.font()
            lexer           = self.lexer()
            if ( lexer ):
                font = lexer.font(0)
            
            pointSize = font.pointSize()
            
            if ( event.delta() > 0 ):
                pointSize += 1
            else:
                pointSize -= 1
            
            if ( pointSize < 5 ):
                pointSize = 5
            
            font.setPointSize( pointSize )
            mfont = QFont(font)
            mfont.setPointSize(pointSize - 2)
            
            # set the font size
            self.setMarginsFont(mfont)
            self.setFont(font)
            if ( lexer ):
                lexer.setFont(font)
            
            self.fontSizeChanged.emit(pointSize)
            event.accept()
        else:
            super(XScintillaEdit,self).wheelEvent(event)
    
    def windowTitle( self ):
        """
        Returns the window title for this edit based on its filename and \
        modified state.
        
        :return     <str>
        """
        output = os.path.basename(self._filename)
        if ( not output ):
            output = 'New Document'
        
        if ( self.isModified() ):
            output += '*'
        
        return output