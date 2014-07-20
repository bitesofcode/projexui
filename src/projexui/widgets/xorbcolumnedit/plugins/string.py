""" Defines the different plugins that will be used for this widget. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2012, Projex Software'
__license__         = 'LGPL'

# maintenance information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

#------------------------------------------------------------------------------

from orb import ColumnType
from projex.text import nativestring
from projexui.widgets.xorbcolumnedit import plugins
from projexui.widgets.xorbcolumnedit import IGNORED
from projexui.widgets.xscintillaedit import XScintillaEdit
from projexui.widgets.xfilepathedit  import XFilepathEdit
from projexui.widgets.xlineedit      import XLineEdit

from projexui.qt.QtGui import QTextEdit

#------------------------------------------------------------------------------

class PasswordEdit(XLineEdit):
    def __init__( self, parent ):
        super(PasswordEdit, self).__init__(parent)
        
        self.setEchoMode(XLineEdit.Password)
    
    def label( self ):
        return self.hint()
    
    def setLabel( self, label ):
        self.setHint(label)
    
    def setValue( self, value ):
        # ignore password values since they are encrypted and we don't want
        # to encrypt them multiple times
        if ( value ):
            value = IGNORED
        
        self.setText(nativestring(value))
    
    def value( self ):
        return nativestring(self.text())
        
#------------------------------------------------------------------------------

class StringEdit(XLineEdit):
    def label( self ):
        return self.hint()
    
    def setValue( self, value ):
        self.setText(nativestring(value))
    
    def setLabel( self, label ):
        self.setHint(label)
    
    def value( self ):
        return nativestring(self.text())

#------------------------------------------------------------------------------

class TextEdit(QTextEdit):
    def setValue( self, value ):
        self.setText(nativestring(value))
    
    def value( self ):
        return nativestring(self.toPlainText())

class RichTextEdit(QTextEdit):
    def setValue( self, value ):
        self.setText(nativestring(value))
    
    def value( self ):
        return nativestring(self.toHtml())

#------------------------------------------------------------------------------

class DirectoryEdit(XFilepathEdit):
    def __init__( self, parent ):
        super(DirectoryEdit, self).__init__(parent)
        
        self.setFilepathMode(XFilepathEdit.Mode.Path)
    
    def label( self ):
        return self.hint()
    
    def setLabel( self, label ):
        self.setHint(label)
    
    def setValue( self, value ):
        self.setFilepath(nativestring(value))
    
    def value( self ):
        return nativestring(self.filepath())

#------------------------------------------------------------------------------

class FilepathEdit(XFilepathEdit):
    def label( self ):
        return self.hint()
    
    def setLabel( self, label ):
        self.setHint(label)
    
    def setValue( self, value ):
        self.setFilepath(nativestring(value))
    
    def value( self ):
        return self.filepath(value)

#------------------------------------------------------------------------------

class XmlEdit(XScintillaEdit):
    def __init__( self, parent ):
        super(XmlEdit, self).__init__(parent)
        
        # intialize the edit
        self.setLanguage('XML')
        self.setSaveOnClose(False)
        self.setShowLineNumbers(False)
        
    def setValue( self, value ):
        self.setText(nativestring(value))
    
    def value( self ):
        return nativestring(self.text())

#------------------------------------------------------------------------------

class EmailEdit(XLineEdit):
    def __init__( self, parent ):
        super(EmailEdit, self).__init__(parent)
        
        self.setHint('user@domain.com')
    
    def label( self ):
        return self.hint()
    
    def setLabel( self, label ):
        self.setHint(label)
    
    def setValue( self, value ):
        self.setText(nativestring(value))
    
    def value( self ):
        return nativestring(self.text())
        
#------------------------------------------------------------------------------

class UrlEdit(XLineEdit):
    def __init__( self, parent ):
        super(UrlEdit, self).__init__(parent)
        
        self.setHint('http://')
    
    def label( self ):
        return self.hint()
    
    def setLabel( self, label ):
        self.setHint(label)
    
    def setValue( self, value ):
        self.setText(nativestring(value))
    
    def value( self ):
        return nativestring(self.text())

#------------------------------------------------------------------------------

plugins.widgets[ColumnType.String]      = StringEdit
plugins.widgets[ColumnType.Email]       = EmailEdit
plugins.widgets[ColumnType.Password]    = PasswordEdit
plugins.widgets[ColumnType.Url]         = UrlEdit
plugins.widgets[ColumnType.Filepath]    = FilepathEdit
plugins.widgets[ColumnType.Directory]   = DirectoryEdit
plugins.widgets[ColumnType.Text]        = TextEdit
plugins.widgets[ColumnType.Xml]         = XmlEdit