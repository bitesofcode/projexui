#!/usr/bin/python

""" Defines the document config plugin for the system. """

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

from projexui.qt import wrapVariant

from projexui.qt.QtGui import QFontComboBox,\
                              QHBoxLayout,\
                              QLabel,\
                              QSpinBox,\
                              QSizePolicy,\
                              QVBoxLayout

from projexui           import resources
from projexui.xscheme   import XScheme
from projexui.xcolorset import XPaletteColorSet

from projexui.dialogs.xconfigdialog     import XConfigPlugin,\
                                               XConfigWidget
                                               
from projexui.widgets.xcolortreewidget  import XColorTreeWidget
from projexui.widgets.xcolorbutton      import XColorButton

class XSchemeConfigWidget(XConfigWidget):
    def __init__( self, parent, uifile = '' ):
        uifile = ''
        
        super(XSchemeConfigWidget, self).__init__(parent, uifile)
        
        # define the font widgets
        self._applicationFont     = QFontComboBox(self)
        self._applicationFont.setProperty('dataName', wrapVariant('font'))
        self._applicationFont.setSizePolicy( QSizePolicy.Expanding,
                                             QSizePolicy.Preferred )
                                           
        self._applicationFontSize = QSpinBox(self)
        self._applicationFontSize.setProperty('dataName', wrapVariant('fontSize'))
        
        self._colorButton = XColorButton(self)
        
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel('Font:', self))
        hbox.addWidget(self._applicationFont)
        hbox.addWidget(QLabel('Size:', self))
        hbox.addWidget(self._applicationFontSize)
        hbox.addWidget(QLabel('Quick Color:', self))
        hbox.addWidget(self._colorButton)
        
        # define the color tree
        self._colorTree = XColorTreeWidget(self)
        self._colorTree.setProperty('dataName', wrapVariant('colorSet'))
        
        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self._colorTree)
        
        self.setLayout(vbox)
        
        # create connections
        self._colorButton.colorChanged.connect( self._colorTree.setQuickColor )
    
#------------------------------------------------------------------------------

class XSchemeConfig(XConfigPlugin):
    def __init__( self, 
                  configGroup = 'User Interface', 
                  title       = 'Scheme',
                  dataSet     = None,
                  uifile      = '',
                  iconfile    = '' ):
        
        if ( not dataSet ):
            dataSet = XScheme()
        
        if ( not iconfile ):
            iconfile = resources.find('img/scheme.png')
        
        super(XSchemeConfig, self).__init__(
            configGroup,
            title,
            dataSet,
            uifile,
            iconfile)
        
        self.setWidgetClass(XSchemeConfigWidget)
        
        self.saveFinished.connect(self.apply)
        self.restoreFinished.connect(self.apply)
    
    def apply( self ):
        """
        Applies the current plugin information to the config system.
        """
        dataSet = self.dataSet()
        if ( dataSet ):
            dataSet.apply()
    
    def reset( self ):
        """
        Resets the colors to the default settings.
        """
        dataSet = self.dataSet()
        if ( not dataSet ):
            dataSet = XScheme()
        
        dataSet.reset()