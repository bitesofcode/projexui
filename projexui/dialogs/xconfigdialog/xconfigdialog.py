#!/usr/bin/python

""" Creates a reusable configuration system for projects. """

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

from projexui.qt import uic

from projexui.qt.QtCore import Qt, QSize
from projexui.qt.QtGui  import QDialog,\
                               QIcon,\
                               QWidget

from projexui.widgets.xtreewidget import XTreeWidgetItem

from projexui import resources

class PluginItem(XTreeWidgetItem):
    def __init__( self, plugin ):
        super(PluginItem, self).__init__([plugin.title()])
        
        self.setFixedHeight(22)
        self.setIcon(0, QIcon(plugin.iconFile()))
        
        self._plugin = plugin
        self._widget = None
    
    def plugin( self ):
        return self._plugin
    
    def setWidget( self, widget ):
        self._widget = widget
    
    def widget( self ):
        return self._widget

#------------------------------------------------------------------------------

class XConfigDialog( QDialog ):
    _instance = None
    
    def __init__( self, parent = None ):
        super(XConfigDialog,self).__init__(parent)
        
        # load the ui
        uifile = os.path.join(os.path.dirname(__file__),'ui/xconfigdialog.ui')
        uic.loadUi( uifile, self )
        
        self._plugins = []
        
        # create connections
        self.uiPluginTREE.itemSelectionChanged.connect( self.showConfig )
        self.uiResetBTN.clicked.connect(    self.reset )
        self.uiSaveBTN.clicked.connect(     self.save )
        self.uiSaveExitBTN.clicked.connect( self.accept )
        self.uiCancelBTN.clicked.connect(   self.reject )
    
    def accept( self ):
        """
        Saves all the current widgets and closes down.
        """
        for i in range(self.uiConfigSTACK.count()):
            widget = self.uiConfigSTACK.widget(i)
            if ( not widget ):
                continue
            
            if ( not widget.save() ):
                self.uiConfigSTACK.setCurrentWidget(widget)
                return False
        
        # close all the widgets in the stack
        for i in range(self.uiConfigSTACK.count()):
            widget = self.uiConfigSTACK.widget(i)
            if ( not widget ):
                continue
            
            widget.close()
        
        if ( self == XConfigDialog._instance ):
            XConfigDialog._instance = None
            
        super(XConfigDialog, self).accept()
    
    def closeEvent( self, event ):
        """
        Manages the close event for the current dialog.
        
        :param      event | <QCloseEvent>
        """
        if ( XConfigDialog._instance == self ):
            XConfigDialog._instance = None
        
        super(XConfigDialog, self).closeEvent(event)
    
    def currentPlugin( self ):
        """
        Returns the currently selected plugin.
        
        :return     <XConfigPlugin> || None
        """
        item = self.uiPluginTREE.currentItem()
        if ( not item ):
            return None
        return item.plugin()
    
    def plugins( self ):
        """
        Returns the plugins used for this dialog.
        
        :return     [<XConfigPlugin>, ..]
        """
        return self._plugins
    
    def reject( self ):
        """
        Overloads the reject method to clear up the instance variable.
        """
        if ( self == XConfigDialog._instance ):
            XConfigDialog._instance = None
        
        super(XConfigDialog, self).reject()
    
    def reset( self ):
        """
        Resets the current widget's settings.
        """
        widget = self.uiConfigSTACK.currentWidget()
        if ( widget ):
            widget.reset()
    
    def save( self ):
        """
        Saves the current widget's settings.
        """
        widget = self.uiConfigSTACK.currentWidget()
        if ( widget ):
            widget.save()
    
    def setCurrentPlugin( self, plugin ):
        """
        Sets the current plugin item to the inputed plugin.
        
        :param      plugin | <XConfigPlugin> || None
        """
        if ( not plugin ):
            self.uiPluginTREE.setCurrentItem(None)
            return
            
        for i in range(self.uiPluginTREE.topLevelItemCount()):
            item = self.uiPluginTREE.topLevelItem(i)
            for c in range(item.childCount()):
                pitem = item.child(c)
                
                if ( pitem.plugin() == plugin ):
                    self.uiPluginTREE.setCurrentItem(pitem)
    
    def setPlugins( self, plugins ):
        """
        Loads the plugins for the inputed dialog.
        
        :param      plugins | [<XConfigPlugin>, ..]
        """
        plugins = sorted(plugins, key = lambda x: x.title())
        
        breakdown = {}
        for plugin in plugins:
            breakdown.setdefault(plugin.configGroup(), [])
            breakdown[plugin.configGroup()].append(plugin)
        
        for grp in sorted(breakdown.keys()):
            gitem = XTreeWidgetItem([grp])
            gitem.initGroupStyle()
            gitem.setFixedHeight(22)
            
            for plugin in breakdown[grp]:
                item = PluginItem(plugin)
                gitem.addChild(item)
            
            self.uiPluginTREE.addTopLevelItem(gitem)
            gitem.setExpanded(True)
    
    def setVisible( self, state ):
        """
        Overloads the setVisible method for the dialog to resize the contents \
        of the splitter properly.
        
        :param      state | <bool>
        """
        super(XConfigDialog, self).setVisible(state)
        
        if ( state ):
            mwidth = self.uiPluginTREE.minimumWidth()
            self.uiMainSPLT.setSizes([mwidth,
                                      self.uiMainSPLT.width() - mwidth])
    
    def showConfig( self ):
        """
        Show the config widget for the currently selected plugin.
        """
        item = self.uiPluginTREE.currentItem()
        if not isinstance(item, PluginItem):
            return
        
        plugin = item.plugin()
        widget = self.findChild(QWidget, plugin.uniqueName())
        
        if ( not widget ):
            widget = plugin.createWidget(self)
            widget.setObjectName(plugin.uniqueName())
            self.uiConfigSTACK.addWidget(widget)
            
        self.uiConfigSTACK.setCurrentWidget(widget)
    
    # define static methods
    @staticmethod
    def edit( plugins, parent = None, default = None, modal = True ):
        """
        Prompts the user to edit the config settings for the inputed config \
        plugins.
        
        :param      plugins | [<XConfigPlugin>, ..]
                    parent  | <QWidget>
                    default | <XConfigPlugin> || None
        
        :return     <bool> success
        """
        if ( XConfigDialog._instance ):
            XConfigDialog._instance.show()
            XConfigDialog._instance.activateWindow()
            return True
        
        dlg = XConfigDialog( parent )
        dlg.setPlugins(plugins)
        dlg.setCurrentPlugin(default)
        
        if ( not modal ):
            XConfigDialog._instance = dlg
            dlg.setAttribute(Qt.WA_DeleteOnClose)
            dlg.show()
            return True
            
        if ( dlg.exec_() ):
            return True
        return False