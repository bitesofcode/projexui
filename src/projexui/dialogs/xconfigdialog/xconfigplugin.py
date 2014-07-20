#!/usr/bin/python

""" Defines the base plugin system for the config structure. """

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

from projex.text import nativestring

import projexui
from projexui.qt.QtCore import QObject
from projexui.qt import Signal
from projexui.dialogs.xconfigdialog.xconfigwidget import XConfigWidget

class XConfigPlugin(QObject):
    _plugins = {}
    
    saveFinished    = Signal()
    resetFinished   = Signal()
    restoreFinished = Signal()
    
    """ Defines a basic configuration plugin for the config system. """
    def __init__( self, 
                  configGroup = 'Basic', 
                  title       = '',
                  dataSet     = None,
                  uifile      = '',
                  iconfile    = '' ):
        
        super(XConfigPlugin, self).__init__()
        
        self._configGroup   = configGroup
        self._title         = title
        self._dataSet       = dataSet
        self._uifile        = uifile
        self._iconfile      = iconfile
        self._widgetClass   = XConfigWidget
        
    def configGroup( self ):
        """
        Returns the configuration group that is linked to this plugin.
        
        :return     <str>
        """
        return self._configGroup
    
    def createWidget( self, parent ):
        """
        Creates a new widget for this plugin for the inputed parent.
        
        :param      parent | <QWidget>
        
        :return     <QWidget>
        """
        widget = self.widgetClass()(parent, self.uiFile())
        widget.setPlugin(self)
        return widget
    
    def dataSet( self ):
        """
        Returns the data set information for the plugin.
        
        :return     <projex.dataset.DataSet>
        """
        return self._dataSet
    
    def iconFile( self ):
        """
        Returns the icon file that is linked that to this plugin.
        
        :return     <str>
        """
        return self._iconfile
    
    def reset( self ):
        """
        Resets the plugin data for current data set.
        """
        if ( not self.signalsBlocked() ):
            self.resetFinished.emit()
    
    def restoreSettings( self, settings ):
        """
        Restores the settings from the inputed settings instance.
        
        :param      settings | <QSettings>
        
        :return     <bool> success
        """
        dataSet = self.dataSet()
        if ( not dataSet ):
            return False
        
        projexui.restoreDataSet( settings,
                                 self.uniqueName(),
                                 dataSet )
        
        if ( not self.signalsBlocked() ):
            self.restoreFinished.emit()
        
        return True
    
    def save( self ):
        """
        Saves the plugin data for the current data set.
        
        :return     <bool> saved
        """
        if ( not self.signalsBlocked() ):
            self.saveFinished.emit()
            
        return True
    
    def saveSettings( self, settings ):
        """
        Saves the plugin data to the inputed settings system.
        
        :param      settings | <QSettings>
        
        :return     <bool> success
        """
        dataSet = self.dataSet()
        if ( not dataSet ):
            return False
        
        projexui.saveDataSet( settings, 
                              self.uniqueName(),
                              dataSet )
        
        return True
    
    def setConfigGroup( self, groupName ):
        """
        Sets the config group for this plugin.
        
        :param      groupName | <str>
        """
        self._configGroup = groupName
    
    def setDataSet( self, dataSet ):
        """
        Sets the data set that will be used by this plugin.
        
        :param      dataSet | <projex.dataset.DataSet> || None
        """
        self._dataSet = dataSet
    
    def setIconFile( self, filename ):
        """
        Sets the icon file that is linked to this plugin.
        
        :param      filename | <str>
        """
        self._iconfile = filename
    
    def setTitle( self, title ):
        """
        Sets the title for this widget to use when shown in the config dialog.
        
        :param      title | <str>
        """
        self._title = title
    
    def setUiFile( self, filename ):
        """
        Sets the ui filename that is linked to this plugin.
        
        :param      filename | <str>
        """
        self._uifile = filename
    
    def setWidgetClass( self, widgetClass ):
        """
        Sets the widget class instance that will be used when loading up the \
        config plugin to the system.
        
        :param      widgetClass | <subclass of XConfigWidget>
        """
        self._widgetClass = widgetClass
    
    def title( self ):
        """
        Returns the title that will be shown for this plugin in the config \
        dialog when used.
        
        :return     <str>
        """
        return self._title
    
    def uiFile( self ):
        """
        Returns the ui file that is linked to this plugin.
        
        :return     <str>
        """
        return self._uifile
    
    def uniqueName( self ):
        """
        Returns the path to this plugin based on its group and title.
        
        :return     <str>
        """
        return '%s/%s' % (self.configGroup(), self.title())
    
    def widgetClass( self ):
        """
        Returns the widget instance that will be used when loading up the \
        config plugin to the system.
        
        :return      <subclass of XConfigWidget>
        """
        return self._widgetClass
    
    @staticmethod
    def find( name ):
        """
        Finds a particular configuration plugin based on its name.
        
        :param      name | <str> || None
        """
        return XConfigPlugin._plugins.get(nativestring(name))
    
    @staticmethod
    def register( plugin ):
        """
        Registers a particular plugin to the global system at the given name.
        
        :param      plugin  | <XConfigPlugin>
        """
        XConfigPlugin._plugins[plugin.uniqueName()] = plugin
    
    @staticmethod
    def plugins():
        """
        Returns a list of the plugins that are registered.
        
        :return     [<XConfigPlugin>, ..]
        """
        return XConfigPlugin._plugins.values()