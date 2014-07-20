#!/usr/bin/python

""" 
Defines a simple widget to control loading of files.
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

import os.path

from projex.text import nativestring

from projexui.qt import Signal, Slot, Property
from projexui.qt.QtCore import QDir, Qt

from projexui.qt.QtGui import QWidget,\
                              QHBoxLayout,\
                              QIcon,\
                              QColor,\
                              QToolButton,\
                              QFileDialog,\
                              QMenu,\
                              QApplication,\
                              QSizePolicy

from projexui.widgets.xlineedit import XLineEdit

from projex.enum import enum
import projexui.resources

class XFilepathEdit(QWidget):
    """
    The XFilepathEdit class provides a common interface to prompt the user to
    select a filepath from the filesystem.  It can be configured to load
    directories, point to a save file path location, or to an open file path
    location.  It can also be setup to color changed based on the validity
    of the existance of the filepath.
    
    == Example ==
    
    |>>> from projexui.widgets.xfilepathedit import XFilepathEdit
    |>>> import projexui
    |
    |>>> # create the edit
    |>>> edit = projexui.testWidget(XFilepathEdit)
    |
    |>>> # set the filepath
    |>>> edit.setFilepath('/path/to/file')
    |
    |>>> # prompt the user to select the filepath
    |>>> edit.pickFilepath()
    |
    |>>> # enable the coloring validation
    |>>> edit.setValidated(True)
    """
    
    __designer_icon__ = projexui.resources.find('img/file.png')
    
    Mode = enum('OpenFile', 'SaveFile', 'Path', 'OpenFiles')
    
    filepathChanged = Signal(str)
    
    def __init__( self, parent = None ):
        super(XFilepathEdit, self).__init__( parent )
        
        # define custom properties
        self._validated         = False
        self._validForeground   = QColor(0, 120, 0)
        self._validBackground   = QColor(0, 120, 0, 100)
        self._invalidForeground = QColor(255, 0, 0)
        self._invalidBackground = QColor(255, 0, 0, 100)
        self._normalizePath     = False
        
        self._filepathMode      = XFilepathEdit.Mode.OpenFile
        self._filepathEdit      = XLineEdit(self)
        self._filepathButton    = QToolButton(self)
        self._filepathTypes     = 'All Files (*.*)'
        
        # set default properties
        ico = projexui.resources.find('img/folder.png')
        self._filepathEdit.setReadOnly(False)
        self._filepathEdit.setSizePolicy(QSizePolicy.Expanding,
                                         QSizePolicy.Expanding)
        self._filepathButton.setText('...')
        self._filepathButton.setFixedSize(25, 23)
        self._filepathButton.setAutoRaise(True)
        self._filepathButton.setIcon(QIcon(ico))
        self._filepathEdit.setContextMenuPolicy(Qt.CustomContextMenu)
        
        self.setWindowTitle('Load File')
        self.setAcceptDrops(True)
        
        # define the layout
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._filepathEdit)
        layout.addWidget(self._filepathButton)
        self.setLayout(layout)
        
        # create connections
        self._filepathEdit.installEventFilter(self)
        
        self._filepathButton.clicked.connect(   self.pickFilepath )
        self._filepathEdit.textChanged.connect( self.emitFilepathChanged )
        self._filepathEdit.textChanged.connect( self.validateFilepath )
        self._filepathEdit.customContextMenuRequested.connect( self.showMenu )
    
    def autoRaise( self ):
        """
        Returns whether or not the tool button will auto raise.
        
        :return     <bool>
        """
        return self._filepathButton.autoRaise()
    
    @Slot()
    def clearFilepath( self ):
        """
        Clears the filepath contents for this path.
        """
        self.setFilepath('')
    
    @Slot()
    def copyFilepath( self ):
        """
        Copies the current filepath contents to the current clipboard.
        """
        clipboard = QApplication.instance().clipboard()
        clipboard.setText(self.filepath())
        clipboard.setText(self.filepath(), clipboard.Selection)
    
    def dragEnterEvent( self, event ):
        """
        Processes drag enter events.
        
        :param      event | <QDragEvent>
        """
        if ( event.mimeData().hasUrls() ):
            event.acceptProposedAction()
    
    def dragMoveEvent( self, event ):
        """
        Processes drag move events.
        
        :param      event | <QDragEvent>
        """
        if ( event.mimeData().hasUrls() ):
            event.acceptProposedAction()
    
    def dropEvent( self, event ):
        """
        Processes drop event.
        
        :param      event | <QDropEvent>
        """
        if event.mimeData().hasUrls():
            url      = event.mimeData().urls()[0]
            filepath = url.toLocalFile()
            if filepath:
                self.setFilepath(filepath)
    
    def emitFilepathChanged( self ):
        """
        Emits the filepathChanged signal for this widget if the signals are \
        not being blocked.
        """
        if ( not self.signalsBlocked() ):
            self.filepathChanged.emit(self.filepath())
    
    def eventFilter( self, object, event ):
        """
        Overloads the eventFilter to look for click events on the line edit.
        
        :param      object | <QObject>
                    event  | <QEvent>
        """
        if ( object == self._filepathEdit and \
             self._filepathEdit.isReadOnly() and \
             event.type() == event.MouseButtonPress and \
             event.button() == Qt.LeftButton ):
            self.pickFilepath()
            
        return False
    
    def filepath( self, validated = False ):
        """
        Returns the filepath for this widget.  If the validated flag is set \
        then this method will only return if the file or folder actually \
        exists for this path.  In the case of a SaveFile, only the base folder \
        needs to exist on the system, in other modes the actual filepath must \
        exist.  If not validated, the text will return whatever is currently \
        entered.
        
        :return     <str>
        """
        paths = self.filepaths()
        if not paths:
            return ''
        
        if not validated or self.isValid():
            return paths[0]
        return ''
    
    def filepaths(self):
        """
        Returns a list of the filepaths for this edit.
        
        :return     [<str>, ..]
        """
        return nativestring(self._filepathEdit.text()).split(os.path.pathsep)
    
    def filepathMode( self ):
        """
        Returns the filepath mode for this widget.
        
        :return     <XFilepathEdit.Mode>
        """
        return self._filepathMode
    
    def filepathModeText( self ):
        """
        Returns the text representation for this filepath mode.
        
        :return     <str>
        """
        return XFilepathEdit.Mode[self._filepathMode]
    
    def filepathTypes( self ):
        """
        Returns the filepath types that will be used for this widget.
        
        :return     <str>
        """
        return self._filepathTypes
    
    def hint( self ):
        """
        Returns the hint for this filepath.
        
        :return     <str>
        """
        return self._filepathEdit.hint()
    
    def icon( self ):
        """
        Returns the icon that is used for this filepath widget.
        
        :return     <QIcon>
        """
        return self._filepathButton.icon()
    
    def invalidBackground( self ):
        """
        Returns the invalid background color for this widget.
        
        :return     <QColor>
        """
        return self._invalidBackground
    
    def invalidForeground( self ):
        """
        Returns the invalid foreground color for this widget.
        
        :return     <QColor>
        """
        return self._invalidForeground
    
    def isValid( self ):
        """
        Returns whether or not the filepath exists on the system. \
        In the case of a SaveFile, only the base folder \
        needs to exist on the system, in other modes the actual filepath must \
        exist.
        
        :return     <bool>
        """
        check = nativestring(self._filepathEdit.text()).split(os.path.pathsep)[0]
        if ( self.filepathMode() == XFilepathEdit.Mode.SaveFile ):
            check = os.path.dirname(check)
        
        return os.path.exists(check)
    
    def isValidated( self ):
        """
        Set whether or not to validate the filepath as the user is working \
        with it.
        
        :return     <bool>
        """
        return self._validated
    
    def isReadOnly( self ):
        """
        Returns if the widget is read only for text editing or not.
        
        :return     <bool>
        """
        return self._filepathEdit.isReadOnly()
    
    def normalizePath(self):
        """
        Returns whether or not the path should be normalized for the current
        operating system.  When off, it will be defaulted to forward slashes
        (/).
        
        :return     <bool>
        """
        return self._normalizePath
    
    def pickFilepath( self ):
        """
        Prompts the user to select a filepath from the system based on the \
        current filepath mode.
        """
        mode = self.filepathMode()
        
        filepath = ''
        filepaths = []
        curr_dir = nativestring(self._filepathEdit.text())
        if ( not curr_dir ):
            curr_dir = QDir.currentPath()
        
        if mode == XFilepathEdit.Mode.SaveFile:
            filepath = QFileDialog.getSaveFileName( self,
                                                    self.windowTitle(),
                                                    curr_dir,
                                                    self.filepathTypes() )
                                                    
        elif mode == XFilepathEdit.Mode.OpenFile:
            filepath = QFileDialog.getOpenFileName( self,
                                                    self.windowTitle(),
                                                    curr_dir,
                                                    self.filepathTypes() )
        
        elif mode == XFilepathEdit.Mode.OpenFiles:
            filepaths = QFileDialog.getOpenFileNames( self,
                                                      self.windowTitle(),
                                                      curr_dir,
                                                      self.filepathTypes() )
        
        else:
            filepath = QFileDialog.getExistingDirectory( self,
                                                         self.windowTitle(),
                                                         curr_dir )
        
        if filepath:
            if type(filepath) == tuple:
                filepath = filepath[0]
            self.setFilepath(nativestring(filepath))
        elif filepaths:
            self.setFilepaths(map(str, filepaths))
    
    def setAutoRaise( self, state ):
        """
        Sets whether or not the tool button will auto raise.
        
        :param      state | <bool>
        """
        self._filepathButton.setAutoRaise(state)
    
    @Slot(int)
    def setFilepathMode( self, mode ):
        """
        Sets the filepath mode for this widget to the inputed mode.
        
        :param      mode | <XFilepathEdit.Mode>
        """
        self._filepathMode = mode
    
    @Slot(str)
    def setFilepathModeText( self, text ):
        """
        Sets the filepath mode for this widget based on the inputed text.
        
        :param      text | <str>
        
        :return     <bool> | success
        """
        try:
            self.setFilepathMode(XFilepathEdit.Mode[nativestring(text)])
            return True
        except KeyError:
            return False
    
    @Slot(str)
    def setFilepathTypes( self, filepathTypes ):
        """
        Sets the filepath type string that will be used when looking up \
        filepaths.
        
        :param      filepathTypes | <str>
        """
        self._filepathTypes = filepathTypes
    
    @Slot(str)
    def setFilepath(self, filepath):
        """
        Sets the filepath text for this widget to the inputed path.
        
        :param      filepath | <str>
        """
        if not filepath:
            self._filepathEdit.setText('')
            return
        
        if self.normalizePath():
            filepath = os.path.normpath(nativestring(filepath))
        else:
            filepath = os.path.normpath(nativestring(filepath)).replace('\\', '/')
            
        self._filepathEdit.setText(filepath)
    
    def setFilepaths(self, filepaths):
        """
        Sets the list of the filepaths for this widget to the inputed paths.
        
        :param      filepaths | [<str>, ..]
        """
        self.setFilepath(os.path.pathsep.join(filepaths))
    
    def setHint(self, hint):
        """
        Sets the hint for this filepath.
        
        :param      hint | <str>
        """
        if self.normalizePath():
            filepath = os.path.normpath(nativestring(hint))
        else:
            filepath = os.path.normpath(nativestring(hint)).replace('\\', '/')
            
        self._filepathEdit.setHint(hint)
    
    def setIcon( self, icon ):
        """
        Sets the icon that will be used for this widget's tool button.
        
        :param      icon | <QIcon> || <str>
        """
        self._filepathButton.setIcon(QIcon(icon))
    
    def setInvalidBackground( self, bg ):
        """
        Sets the invalid background color for this widget to the inputed widget.
        
        :param      bg | <QColor>
        """
        self._invalidBackground = QColor(bg)
    
    def setInvalidForeground( self, fg ):
        """
        Sets the invalid foreground color for this widget to the inputed widget.
        
        :param      fg | <QColor>
        """
        self._invalidForeground = QColor(fg)
    
    def setNormalizePath(self, state):
        """
        Sets whether or not the path should be normalized for the current
        operating system.  When off, it will be defaulted to forward slashes
        (/).
        
        :param      state | <bool>
        """
        self._normalizePath = state
    
    @Slot(bool)
    def setReadOnly( self, state ):
        """
        Sets whether or not this filepath widget is readonly in the text edit.
        
        :param      state | <bool>
        """
        self._filepathEdit.setReadOnly(state)
    
    @Slot(bool)
    def setValidated( self, state ):
        """
        Set whether or not to validate the path as the user edits it.
        
        :param      state | <bool>
        """
        self._validated = state
        palette = self.palette()
        
        # reset the palette to default, revalidate
        self._filepathEdit.setPalette(palette)
        self.validate()
    
    def setValidBackground( self, bg ):
        """
        Sets the valid background color for this widget to the inputed color.
        
        :param      bg | <QColor>
        """
        self._validBackground = QColor(bg)
    
    def setValidForeground( self, fg ):
        """
        Sets the valid foreground color for this widget to the inputed color.
        
        :param      fg | <QColor>
        """
        self._validForeground = QColor(fg)
    
    def showMenu( self, pos ):
        """
        Popups a menu for this widget.
        """
        menu = QMenu(self)
        menu.setAttribute(Qt.WA_DeleteOnClose)
        menu.addAction('Clear').triggered.connect(self.clearFilepath)
        menu.addSeparator()
        menu.addAction('Copy Filepath').triggered.connect(self.copyFilepath)
        
        menu.exec_(self.mapToGlobal(pos))
    
    def validBackground( self ):
        """
        Returns the valid background color for this widget.
        
        :return     <QColor>
        """
        return self._validBackground
    
    def validForeground( self ):
        """
        Returns the valid foreground color for this widget.
        
        :return     <QColor>
        """
        return self._validForeground
    
    def validateFilepath( self ):
        """
        Alters the color scheme based on the validation settings.
        """
        if ( not self.isValidated() ):
            return
        
        valid = self.isValid()
        if ( not valid ):
            fg = self.invalidForeground()
            bg = self.invalidBackground()
        else:
            fg = self.validForeground()
            bg = self.validBackground()
        
        palette = self.palette()
        palette.setColor(palette.Base, bg)
        palette.setColor(palette.Text, fg)
        self._filepathEdit.setPalette(palette)
    
    # map Qt properties
    x_autoRaise         = Property(bool, autoRaise,     setAutoRaise)
    x_filepathTypes     = Property(str,  filepathTypes, setFilepathTypes)
    x_filepath          = Property(str,  filepath,      setFilepath)
    x_readOnly          = Property(bool, isReadOnly,    setReadOnly)
    x_validated         = Property(bool, isValidated,   setValidated)
    x_hint              = Property(str,  hint,          setHint)
    x_icon              = Property('QIcon', icon,       setIcon)
    x_normalizePath     = Property(bool, normalizePath, setNormalizePath)
    
    x_invalidForeground = Property('QColor',
                                        invalidForeground,
                                        setInvalidForeground)
    
    x_invalidBackground = Property('QColor',
                                        invalidBackground,
                                        setInvalidBackground)
    
    x_validForeground   = Property('QColor',
                                        validForeground,
                                        setValidForeground)
    
    x_validBackground   = Property('QColor',
                                        validBackground,
                                        setValidBackground)
    
    x_filepathModeText  = Property(str, 
                                       filepathModeText, 
                                       setFilepathModeText)

__designer_plugins__ = [XFilepathEdit]