#!/usr/bin/python

""" Creates a reusable wizard browser system for projects. """

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

from projexui.qt.QtCore import QSize, Qt
from projexui.qt.QtGui  import QDialog,\
                               QIcon,\
                               QLabel,\
                               QPixmap,\
                               QTableWidgetItem,\
                               QVBoxLayout,\
                               QWidget

import projexui
import projexui.resources
from projexui.widgets.xtreewidget import XTreeWidgetItem

class PluginWidget(QWidget):
    def __init__( self, parent, plugin ):
        super(PluginWidget, self).__init__(parent)
        
        self._icon = QLabel(self)
        pixmap = QPixmap(plugin.iconFile())
        if pixmap.isNull():
            pixmap = QPixmap(projexui.resources.find('img/plugin_48.png'))
        self._icon.setPixmap(pixmap)
        self._icon.setMinimumWidth(48)
        self._icon.setMinimumHeight(48)
        self._icon.setAlignment(Qt.AlignCenter)
        
        self._title = QLabel(plugin.title(), self)
        self._title.setAlignment(Qt.AlignCenter)
        
        font = self.font()
        font.setPointSize(7)
        
        self._title.setFont(font)
        
        vbox = QVBoxLayout()
        vbox.addStretch()
        vbox.addWidget(self._icon)
        vbox.addWidget(self._title)
        vbox.addStretch()
        
        self.setLayout(vbox)
        
        self._plugin = plugin
    
    def plugin( self ):
        """
        Returns the plugin instance linked to this widget.
        
        :return     <XWizardPlugin>
        """
        return self._plugin

#------------------------------------------------------------------------------

class XWizardBrowserDialog( QDialog ):
    def __init__( self, parent = None ):
        super(XWizardBrowserDialog,self).__init__(parent)
        
        # load the ui
        projexui.loadUi(__file__, self)
        
        self._plugins = []
        
        self.showWizards()
        
        # create connections
        self.uiPluginTREE.itemSelectionChanged.connect( self.showWizards )
        self.uiWizardTABLE.itemSelectionChanged.connect( self.showDescription )
        self.uiWizardTABLE.itemDoubleClicked.connect( self.runWizard )
    
    def currentPlugin( self ):
        """
        Returns the currently selected plugin.
        
        :return     <XWizardPlugin> || None
        """
        col    = self.uiWizardTABLE.currentColumn()
        row    = self.uiWizardTABLE.currentRow()
        item   = self.uiWizardTABLE.currentItem()
        widget = self.uiWizardTABLE.cellWidget(row, col)
        
        if ( not (widget and item and item.isSelected()) ):
            return None
            
        return widget.plugin()
    
    def plugins( self, typ = None, group = None ):
        """
        Returns the plugins used for this dialog.
        
        :param      typ      | <str> || None
                    group    | <str> || None
        
        :return     [<XWizardPlugin>, ..]
        """
        if ( typ is None ):
            output = []
            for wlang in self._plugins.values():
                for wgrp in wlang.values():
                    output += wgrp
            return output
            
        elif ( group is None ):
            output = []
            for wgrp in self._plugins.get(nativestring(typ), {}).values():
                output += wgrp
            return output
        
        else:
            return self._plugins.get(nativestring(typ), {}).get(nativestring(group), [])
    
    def runWizard( self ):
        """
        Runs the current wizard.
        """
        plugin = self.currentPlugin()
        if ( plugin and plugin.runWizard(self) ):
            self.accept()
        
    def setCurrentPlugin( self, plugin ):
        """
        Sets the current plugin item to the inputed plugin.
        
        :param      plugin | <XWizardPlugin> || None
        """
        item = self.uiWizardTABLE.currentItem()
        if ( not item ):
            return None
        
        return item.plugin()
    
    def setPlugins( self, plugins ):
        """
        Loads the plugins for the inputed dialog.
        
        :param      plugins | [<XWizardPlugin>, ..]
        """
        langs = {}
        icons = {}
        
        for plugin in plugins:
            wlang = plugin.wizardType()
            wgrp  = plugin.wizardGroup()
            
            langs.setdefault(wlang, {})
            langs[wlang].setdefault(wgrp, [])
            
            langs[wlang][wgrp].append( plugin )
            
            icons.setdefault(wgrp, plugin.groupIcon(wgrp))
        
        self._plugins = langs
        
        self.blockSignals(True)
        self.setUpdatesEnabled(False)
        self.uiPluginTREE.clear()
        
        folder = QIcon(projexui.resources.find('img/folder_32.png'))
        for wlang in sorted(langs.keys()):
            langitem = XTreeWidgetItem(self.uiPluginTREE, [wlang])
            langitem.setFixedHeight(28)
            langitem.initGroupStyle()
            langitem.setExpanded(True)
            
            for wgrp in sorted(langs[wlang].keys()):
                grpitem = XTreeWidgetItem(langitem, [wgrp])
                grpitem.setIcon(0, QIcon(icons[wgrp]))
                grpitem.setFixedHeight(26)

        self.blockSignals(False)
        self.setUpdatesEnabled(True)
    
    def setVisible( self, state ):
        """
        Overloads the setVisible method for the dialog to resize the contents \
        of the splitter properly.
        
        :param      state | <bool>
        """
        super(XWizardBrowserDialog, self).setVisible(state)
        
        if ( state ):
            mwidth = self.uiPluginTREE.minimumWidth()
            self.uiMainSPLT.setSizes([mwidth,
                                      self.uiMainSPLT.width() - mwidth])
    
    def showDescription( self ):
        """
        Shows the description for the current plugin in the interface.
        """
        plugin = self.currentPlugin()
        if ( not plugin ):
            self.uiDescriptionTXT.setText('')
        else:
            self.uiDescriptionTXT.setText(plugin.description())
    
    def showWizards( self ):
        """
        Show the wizards widget for the currently selected plugin.
        """
        self.uiWizardTABLE.clear()
        
        item = self.uiPluginTREE.currentItem()
        if ( not (item and item.parent()) ):
            plugins = []
        else:
            wlang   = nativestring(item.parent().text(0))
            wgrp    = nativestring(item.text(0))
            plugins = self.plugins(wlang, wgrp)
        
        if ( not plugins ):
            self.uiWizardTABLE.setEnabled(False)
            self.uiDescriptionTXT.setEnabled(False)
            return
        
        self.uiWizardTABLE.setEnabled(True)
        self.uiDescriptionTXT.setEnabled(True)
        
        # determine the number of columns
        colcount = len(plugins) / 2
        if ( len(plugins) % 2 ):
            colcount += 1
        
        self.uiWizardTABLE.setRowCount(2)
        self.uiWizardTABLE.setColumnCount( colcount )
        
        header = self.uiWizardTABLE.verticalHeader()
        header.setResizeMode(0, header.Stretch)
        header.setResizeMode(1, header.Stretch)
        header.setMinimumSectionSize(64)
        header.hide()
        
        header = self.uiWizardTABLE.horizontalHeader()
        header.setMinimumSectionSize(64)
        header.hide()
        
        col = -1
        row = 1
        for plugin in plugins:
            if ( row ):
                col += 1
            
            row     = int(not row)
            widget  = PluginWidget(self, plugin)
            
            self.uiWizardTABLE.setItem(row, col, QTableWidgetItem())
            self.uiWizardTABLE.setCellWidget(row, col, widget)
    
    # define static methods
    @staticmethod
    def browse( plugins, parent = None, default = None ):
        """
        Prompts the user to browse the wizards based on the inputed plugins \
        allowing them to launch any particular wizard of choice.
        
        :param      plugins | [<XWizardPlugin>, ..]
                    parent  | <QWidget>
                    default | <XWizardPlugin> || None
        
        :return     <bool> success
        """
        dlg = XWizardBrowserDialog( parent )
        dlg.setPlugins(plugins)
        dlg.setCurrentPlugin(default)
        if ( dlg.exec_() ):
            return True
        return False