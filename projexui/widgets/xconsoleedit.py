#!/usr/bin/python

""" Defines an interactive python interpreter console. """

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

import __main__
import inspect
import logging
import os
import re
import sys

import projex.text
import projexui

from projex import hooks
from projexui.qt import Signal, Property, wrapVariant, unwrapVariant
from projexui.qt.QtCore import QObject,\
                               QPoint,\
                               Qt,\
                               QMutexLocker,\
                               QTimer
                         
from projexui.qt.QtGui import QApplication,\
                              QCursor,\
                              QFont,\
                              QTextCursor,\
                              QToolTip,\
                              QTreeWidget,\
                              QTreeWidgetItem,\
                              QFontMetrics,\
                              QSyntaxHighlighter,\
                              QTextCharFormat,\
                              QColor,\
                              QMessageBox

from projexui.highlighters.xpythonhighlighter import XPythonHighlighter

import projexui.resources

from projexui.widgets.xloggerwidget import XLoggerWidget

INPUT_EXPR = re.compile('^(>>> |... )([^#]*)')
KEYWORDS = ('def', 'import', 'from', 'with', 'if', 'elif', 'else', 'for',
            'while', 'class', 'None', 'not', 'is', 'in', 'print', 'return')

HEADER = """\
# Python {version} on {platform}"""

class XIOHook(QObject):
    _instance = None
    
    printed = Signal(str)
    errored = Signal(str)
    
    @staticmethod
    def cleanup():
        # destroy the global hook instance
        hook = XIOHook._instance
        if not hook:
            return
        
        XIOHook._instance = None
        
        # disconnect Qt hooks
        try:
            hook.printed.disconnect()
        except RuntimeError:
            pass # no connections have been made
        
        try:
            hook.errored.disconnect()
        except RuntimeError:
            pass # no connections have been made
        
        hook.deleteLater()
        
        # unregister from python hooks
        hooks.unregisterStdOut(XIOHook.stdout)
        hooks.unregisterStdErr(XIOHook.stderr)

    
    @staticmethod
    def stdout(text):
        XIOHook.instance().printed.emit(text)

    @staticmethod
    def stderr(text):
        XIOHook.instance().errored.emit(text)

    @staticmethod
    def instance():
        if XIOHook._instance is None:
            XIOHook._instance = XIOHook()
            
            # create the hook registration
            hooks.registerStdOut(XIOHook.stdout)
            hooks.registerStdErr(XIOHook.stderr)
            
            QApplication.instance().aboutToQuit.connect(XIOHook.cleanup)

        return XIOHook._instance

#----------------------------------------------------------------------

class XConsoleEdit(XLoggerWidget):
    __designer_icon__ = projexui.resources.find('img/ui/console.png')
    
    executeRequested = Signal(str)
    
    def __init__(self, parent):
        super(XConsoleEdit, self).__init__(parent)
        
        # create custom properties
        self._scope = __main__.__dict__
        self._initialized = False
        self._completerTree = None
        self._commandStack = []
        self._history = []
        self._currentHistoryIndex = 0
        self._waitingForInput = False
        self._commandLineInteraction = False
        self._highlighter = XPythonHighlighter(self.document())
        
        # setup the look for the console
        self.setReadOnly(False)
        self.waitForInput()
        self.setConfigurable(False)

    def _information(self, msg):
        locker = QMutexLocker(self._mutex)
        
        msg = projex.text.nativestring(msg)
        self.moveCursor(QTextCursor.End)
        self.setCurrentMode(logging.INFO)
        self.insertPlainText(msg)
        self.scrollToEnd()

    def _error(self, msg):
        locker = QMutexLocker(self._mutex)
        
        msg = projex.text.nativestring(msg)
        self.moveCursor(QTextCursor.End)
        self.setCurrentMode(logging.ERROR)
        self.insertPlainText(msg)
        self.scrollToEnd()
        
        if not self._waitingForInput:
            self._waitingForInput = True
            QTimer.singleShot(50, self.waitForInput)

    def acceptCompletion( self ):
        """
        Accepts the current completion and inserts the code into the edit.
        
        :return     <bool> accepted
        """
        tree = self._completerTree
        if not tree:
            return False
            
        tree.hide()
        
        item = tree.currentItem()
        if not item:
            return False
        
        # clear the previously typed code for the block
        cursor  = self.textCursor()
        text    = cursor.block().text()
        col     = cursor.columnNumber()
        end     = col
        
        while col:
            col -= 1
            if text[col] in ('.', ' '):
                col += 1
                break
        
        # insert the current text
        cursor.setPosition(cursor.position() - (end-col), cursor.KeepAnchor)
        cursor.removeSelectedText()
        self.insertPlainText(item.text(0))
        return True
    
    def applyCommand(self):
        """
        Applies the current line of code as an interactive python command.
        """
        # generate the command information
        cursor      = self.textCursor()
        cursor.movePosition(cursor.EndOfLine)
        
        line        = projex.text.nativestring(cursor.block().text())
        at_end      = cursor.atEnd()
        modifiers   = QApplication.instance().keyboardModifiers()
        mod_mode    = at_end or modifiers == Qt.ShiftModifier
        
        # test the line for information
        if mod_mode and line.endswith(':'):
            cursor.movePosition(cursor.EndOfLine)
            
            line = re.sub('^>>> ', '', line)
            line = re.sub('^\.\.\. ', '', line)
            count = len(line) - len(line.lstrip()) + 4
            
            self.insertPlainText('\n... ' + count * ' ')
            return False
        
        elif mod_mode and line.startswith('...') and \
            (line.strip() != '...' or not at_end):
            cursor.movePosition(cursor.EndOfLine)
            line = re.sub('^\.\.\. ', '', line)
            count = len(line) - len(line.lstrip())
            self.insertPlainText('\n... ' + count * ' ')
            return False
        
        # if we're not at the end of the console, then add it to the end
        elif line.startswith('>>>') or line.startswith('...'):
            # move to the top of the command structure
            line = projex.text.nativestring(cursor.block().text())
            while line.startswith('...'):
                cursor.movePosition(cursor.PreviousBlock)
                line = projex.text.nativestring(cursor.block().text())
            
            # calculate the command
            cursor.movePosition(cursor.EndOfLine)
            line = projex.text.nativestring(cursor.block().text())
            ended = False
            lines = []
            
            while True:
                # add the new block
                lines.append(line)
                
                if cursor.atEnd():
                    ended = True
                    break
                
                # move to the next line
                cursor.movePosition(cursor.NextBlock)
                cursor.movePosition(cursor.EndOfLine)
                
                line = projex.text.nativestring(cursor.block().text())
                
                # check for a new command or the end of the command
                if not line.startswith('...'):
                    break
            
            command = '\n'.join(lines)
            
            # if we did not end up at the end of the command block, then
            # copy it for modification
            if not (ended and command):
                self.waitForInput()
                self.insertPlainText(command.replace('>>> ', ''))
                cursor.movePosition(cursor.End)
                return False
        
        else:
            self.waitForInput()
            return False
        
        self.executeCommand(command)
        return True
    
    def cancelCompletion( self ):
        """
        Cancels the current completion.
        """
        if self._completerTree:
            self._completerTree.hide()
    
    def clear(self):
        """
        Clears the current text and starts a new input line.
        """
        super(XConsoleEdit, self).clear()
        self.waitForInput()

    def commandLineInteraction(self):
        """
        Returns whether or not the console is using interaction like the
        command line.
        
        :return     <bool>
        """
        return self._commandLineInteraction

    def completerTree( self ):
        """
        Returns the completion tree for this instance.
        
        :return     <QTreeWidget>
        """
        if not self._completerTree:
            self._completerTree = QTreeWidget(self)
            self._completerTree.setWindowFlags(Qt.Popup)
            self._completerTree.setAlternatingRowColors( True )
            self._completerTree.installEventFilter(self)
            self._completerTree.itemClicked.connect( self.acceptCompletion )
            self._completerTree.setRootIsDecorated(False)
            self._completerTree.header().hide()
            
        return self._completerTree
    
    def eventFilter(self, obj, event):
        """
        Filters particular events for a given QObject through this class. \
        Will use this to intercept events to the completer tree widget while \
        filtering.
        
        :param      obj     | <QObject>
                    event   | <QEvent>
        
        :return     <bool> consumed
        """
        if not obj == self._completerTree:
            return False
        
        if event.type() != event.KeyPress:
            return False
            
        if event.key() == Qt.Key_Escape:
            QToolTip.hideText()
            self.cancelCompletion()
            return False
        
        elif event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Tab):
            self.acceptCompletion()
            return False
        
        elif event.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_PageUp, Qt.Key_PageDown):
            return False
        
        else:
            self.keyPressEvent(event)
            
            # update the completer
            cursor   = self.textCursor()
            text     = projex.text.nativestring(cursor.block().text())
            text     = text[:cursor.columnNumber()].split(' ')[-1]
            text     = text.split('.')[-1]
            
            self._completerTree.blockSignals(True)
            self._completerTree.setUpdatesEnabled(False)
            
            self._completerTree.setCurrentItem(None)
            
            for i in range(self._completerTree.topLevelItemCount()):
                item = self._completerTree.topLevelItem(i)
                if projex.text.nativestring(item.text(0)).startswith(text):
                    self._completerTree.setCurrentItem(item)
                    break
            
            self._completerTree.blockSignals(False)
            self._completerTree.setUpdatesEnabled(True)
            
            return True
    
    def executeCommand(self, command):
        """
        Executes the inputed command in the global scope.
        
        :param      command | <unicode>
        
        :return     <variant>
        """
        if not command.strip():
            return self.waitForInput()
        
        # store the current block
        self._history.append(command)
        self._currentHistoryIndex = len(self._history)
        
        lines = []
        for line in command.split('\n'):
            line = re.sub('^>>> ', '', line)
            line = re.sub('^\.\.\. ', '', line)
            lines.append(line)
        
        command = '\n'.join(lines)
        
        # ensure we are at the end
        self.moveCursor(QTextCursor.End)
        self.scrollToEnd()
        self.insertPlainText('\n')
        cmdresult = None
        
        try:
            cmdresult = eval(command, self.scope(), self.scope())
        
        except SyntaxError:
            exec(command) in self.scope(), self.scope()
        
        else:
            if cmdresult is not None:
                # check to see if the command we executed actually caused
                # the destruction of this object -- if it did, then
                # the commands below will error
                if self.isDestroyed():
                    return
                
                try:
                    result = projex.text.nativestring(repr(cmdresult))
                except:
                    result = '<<< error formatting result to utf-8 >>>'
                
                self.information(result)
        
        finally:
            self.waitForInput()
    
    def dragEnterEvent(self, event):
        if event.keyboardModifiers() == Qt.ShiftModifier:
            event.acceptProposedAction()
        else:
            super(XConsoleEdit, self).dragEnterEvent(event)
    
    def dragMoveEvent(self, event):
        if event.keyboardModifiers() == Qt.ShiftModifier:
            event.acceptProposedAction()
        else:
            super(XConsoleEdit, self).dragMoveEvent(event)
    
    def dropEvent(self, event):
        if event.keyboardModifiers() == Qt.ShiftModifier:
            self.insertPlainText('\n' + projexui.formatDropEvent(event))
        else:
            super(XConsoleEdit, self).dropEvent(event)
    
    def highlighter(self):
        """
        Returns the console highlighter for this widget.
        
        :return     <XPythonHighlighter>
        """
        return self._highlighter

    def gotoHome(self):
        """
        Navigates to the home position for the edit.
        """
        mode = QTextCursor.MoveAnchor
        
        # select the home
        if QApplication.instance().keyboardModifiers() == Qt.ShiftModifier:
            mode = QTextCursor.KeepAnchor
        
        cursor = self.textCursor()
        block  = projex.text.nativestring(cursor.block().text())
        
        cursor.movePosition( QTextCursor.StartOfBlock, mode )
        if block.startswith('>>> '):
            cursor.movePosition(QTextCursor.Right, mode, 4)
        elif block.startswith('... '):
            match = re.match('...\s*', block)
            cursor.movePosition(QTextCursor.Right, mode, match.end())
        
        self.setTextCursor(cursor)

    def insertFromMimeData(self, source):
        """
        Inserts the information from the inputed source.
        
        :param      source | <QMimeData>
        """
        lines = projex.text.nativestring(source.text()).splitlines()
        for i in range(1, len(lines)):
            if not lines[i].startswith('... '):
                lines[i] = '... ' + lines[i]
        
        if len(lines) > 1:
            lines.append('... ')
        
        self.insertPlainText('\n'.join(lines))

    def insertNextCommand(self):
        """
        Inserts the previous command from history into the line.
        """
        self._currentHistoryIndex += 1
        if 0 <= self._currentHistoryIndex < len(self._history):
            cmd = self._history[self._currentHistoryIndex]
        else:
            cmd = '>>> '
            self._currentHistoryIndex = -1
        
        self.replaceCommand(cmd)
    
    def insertPreviousCommand(self):
        """
        Inserts the previous command from history into the line.
        """
        self._currentHistoryIndex -= 1
        if 0 <= self._currentHistoryIndex < len(self._history):
            cmd = self._history[self._currentHistoryIndex]
        else:
            cmd = '>>> '
            self._currentHistoryIndex = len(self._history)
        
        self.replaceCommand(cmd)
    
    def keyPressEvent(self, event):
        """
        Overloads the key press event to control keystroke modifications for \
        the console widget.
        
        :param      event | <QKeyEvent>
        """
        # enter || return keys will apply the command
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.applyCommand()
            event.accept()
        
        # home key will move the cursor to the home position
        elif event.key() == Qt.Key_Home:
            self.gotoHome()
            event.accept()
        
        elif event.key() in (Qt.Key_Backspace, Qt.Key_Delete):
            super(XConsoleEdit, self).keyPressEvent(event)
            
            # update the completer
            cursor   = self.textCursor()
            text     = projex.text.nativestring(cursor.block().text())
            text     = text[:cursor.columnNumber()].split(' ')[-1]
            
            if not '.' in text:
                self.cancelCompletion()
            
        # period key will trigger a completion popup
        elif event.key() == Qt.Key_Period or \
             (Qt.Key_A <= event.key() <= Qt.Key_Z):
            super(XConsoleEdit, self).keyPressEvent(event)
            self.startCompletion(force=event.key() == Qt.Key_Period)
        
        # space, tab, backspace and delete will cancel the completion
        elif event.key() == Qt.Key_Space:
            self.cancelCompletion()
            super(XConsoleEdit, self).keyPressEvent(event)
        
        # left parenthesis will start method help
        elif event.key() == Qt.Key_ParenLeft:
            self.cancelCompletion()
            self.showMethodToolTip()
            super(XConsoleEdit, self).keyPressEvent(event)
        
        # Ctrl+Up will load previous commands
        elif event.key() == Qt.Key_Up:
            if self.commandLineInteraction() or \
               event.modifiers() & Qt.ControlModifier:
                self.insertPreviousCommand()
                event.accept()
            else:
                super(XConsoleEdit, self).keyPressEvent(event)
        
        # Ctrl+Down will load future commands
        elif event.key() == Qt.Key_Down:
            if self.commandLineInteraction() or \
               event.modifiers() & Qt.ControlModifier:
                self.insertNextCommand()
                event.accept()
            else:
                super(XConsoleEdit, self).keyPressEvent(event)
        
        # otherwise, handle the event like normal
        else:
            super(XConsoleEdit, self).keyPressEvent(event)
    
    def objectAtCursor(self):
        """
        Returns the python object that the text is representing.
        
        :return     <object> || None
        """
        
        # determine the text block
        cursor   = self.textCursor()
        text     = projex.text.nativestring(cursor.block().text())
        position = cursor.positionInBlock() - 1
        
        if not text:
            return (None, '')
        
        symbol   = ''
        for match in re.finditer('[\w\.]+', text):
            if match.start() <= position <= match.end():
                symbol = match.group()
                break
        
        if not symbol:
            return (None, '')
        
        parts = symbol.split('.')
        if len(parts) == 1:
            return (self.scope(), parts[0])
        
        part = parts[0]
        obj = self.scope().get(part)
        for part in parts[1:-1]:
            try:
                obj = getattr(obj, part)
            except AttributeError:
                return (None, '')
        
        return (obj, parts[-1])

    def restoreSettings(self, settings):
        hist = []
        settings.beginGroup('console')
        for key in sorted(settings.childKeys()):
            hist.append(unwrapVariant(settings.value(key)))
        settings.endGroup()
        
        self._history = hist

    def saveSettings(self, settings):
        settings.beginGroup('console')
        for i, text in enumerate(self._history):
            settings.setValue('command_{0}'.format(i), wrapVariant(text))
        settings.endGroup()
    
    def showEvent(self, event):
        super(XConsoleEdit, self).showEvent(event)
        
        if not self._initialized:
            self._initialized = True
            
            # create connections
            if os.environ.get('XUI_DISABLE_CONSOLE') != '1':
                hook = XIOHook.instance()
                hook.printed.connect(self._information)
                hook.errored.connect(self._error)
            
            # setup the header
            opts = {'version': sys.version, 'platform': sys.platform}
            self.setText(HEADER.format(**opts))
            self.waitForInput()
    
    def showMethodToolTip(self):
        """
        Pops up a tooltip message with the help for the object under the \
        cursor.
        
        :return     <bool> success
        """
        self.cancelCompletion()
        
        obj, _ = self.objectAtCursor()
        if not obj:
            return False
        
        docs = inspect.getdoc(obj)
        if not docs:
            return False
        
        # determine the cursor position
        rect   = self.cursorRect()
        cursor = self.textCursor()
        point  = QPoint(rect.left(), rect.top() + 18)
        
        QToolTip.showText(self.mapToGlobal(point), docs, self)
        
        return True
    
    def replaceCommand(self, cmd):
        # move to the top of the command structure
        self.moveCursor(QTextCursor.End)
        cursor = self.textCursor()
        
        line = projex.text.nativestring(cursor.block().text())
        while line.startswith('...'):
            cursor.movePosition(cursor.PreviousBlock)
            line = projex.text.nativestring(cursor.block().text())
        
        # calculate the command
        cursor.movePosition(cursor.StartOfLine)
        cursor.movePosition(cursor.End, cursor.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertText(cmd)
        self.moveCursor(cursor.End)
    
    def scope(self):
        """
        Returns the dictionary scope that will be used when working
        with this editor.
        
        :return     <dict>
        """
        return self._scope
    
    def setCommandLineInteraction(self, state=True):
        """
        Sets whether or not the interaction should follow command-line
        standards (Up/Down navigation) or not (CTRL+Up/Down).
        
        :param      state | <bool>
        """
        self._commandLineInteraction = state
    
    def setScope(self, scope):
        """
        Sets the scope that will be used for this editor.
        
        :param      scope | <dict>
        """
        self._scope = scope
    
    def startCompletion(self, force=False):
        """
        Starts a new completion popup for the current object.
        
        :return     <bool> success
        """
        # add the top level items
        tree = self.completerTree()
        if not force and tree.isVisible():
            return
        
        tree.clear()
        
        # make sure we have a valid object
        obj, remain = self.objectAtCursor()
        
        if obj is None:
            tree.hide()
            return
        
        # determine the cursor position
        rect   = self.cursorRect()
        cursor = self.textCursor()
        point  = QPoint(rect.left(), rect.top() + 18)
        
        # compare the ids since some things might overload the __eq__
        # comparator
        if id(obj) == id(self._scope):
            o_keys = obj.keys()
        elif obj is not None:
            o_keys = dir(obj)
        
        keys = [key for key in sorted(o_keys) if not key.startswith('_')]
        if id(obj) == id(self._scope):
            if not remain:
                return False
            else:
                keys = filter(lambda x: x.startswith(remain[0]), keys)
        
        if not keys:
            return False
        
        for key in keys:
            tree.addTopLevelItem(QTreeWidgetItem([key]))
        
        tree.move(self.mapToGlobal(point))
        tree.show()
        return True
    
    def waitForInput(self):
        """
        Inserts a new input command into the console editor.
        """
        self._waitingForInput = False
        
        try:
            if self.isDestroyed() or self.isReadOnly():
                return
        except RuntimeError:
            return
        
        self.moveCursor(QTextCursor.End)
        if self.textCursor().block().text() == '>>> ':
            return
        
        # if there is already text on the line, then start a new line
        newln = '>>> '
        if projex.text.nativestring(self.textCursor().block().text()):
            newln = '\n' + newln
        
        # insert the text
        self.setCurrentMode('standard')
        self.insertPlainText(newln)
        self.scrollToEnd()
        
        self._blankCache = ''

    x_commandLineInteraction = Property(bool, commandLineInteraction,
                                              setCommandLineInteraction)

__designer_plugins__ = [XConsoleEdit]

