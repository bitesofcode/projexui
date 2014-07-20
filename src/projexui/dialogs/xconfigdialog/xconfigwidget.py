#!/usr/bin/python

""" Defines a basic config widget that can be used with additional plugins. """

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

from projexui.qt import uic, unwrapVariant
from projexui.qt.QtCore import QDir
from projexui.qt.QtGui import QWidget

import projexui

class XConfigWidget(QWidget):
    def __init__( self, parent, uifile = '' ):
        super(XConfigWidget, self).__init__(parent)
        
        # load the ui if specified
        if ( uifile ):
            curr_dir = QDir.currentPath()
            QDir.setCurrent(os.path.dirname(uifile))
            uic.loadUi(uifile, self)
            QDir.setCurrent(curr_dir)
        
        self._plugin  = None
    
    def dataSet( self ):
        """
        Returns the dataset linked to this config widget.
        
        :return     <projex.dataset.DataSet> || None
        """
        return self.plugin().dataSet()
    
    def plugin( self ):
        """
        Returns the plugin instance linked to this widget.
        
        :return     <XConfigPlugin>
        """
        return self._plugin
    
    def refreshUi( self ):
        """
        Load the plugin information to the interface.
        """
        dataSet = self.dataSet()
        if not dataSet:
            return False
            
        # lookup widgets based on the data set information
        for widget in self.findChildren(QWidget):
            prop = unwrapVariant(widget.property('dataName'))
            if prop is None:
                continue
            
            # update the data for the widget
            prop_name = nativestring(prop)
            if prop_name in dataSet:
                value = dataSet.value(prop_name)
                projexui.setWidgetValue(widget, value)
        
        return True
    
    def reset( self ):
        """
        Resets the ui information to the default data for the widget.
        """
        if not self.plugin():
            return False
        
        self.plugin().reset()
        self.refreshUi()
        
        return True
    
    def save( self ):
        """
        Saves the ui information to the data for this widget's data set.
        
        :return     <bool> saved
        """
        dataSet = self.dataSet()
        if ( not dataSet ):
            return True
        
        # lookup widgets based on the data set information
        for widget in self.findChildren(QWidget):
            prop = unwrapVariant(widget.property('dataName'))
            if prop is None:
                continue
            
            # update the data for the dataset
            value, success = projexui.widgetValue(widget)
            if not success:
                continue
                
            dataSet.setValue(prop, value)
        
        return self.plugin().save()
    
    def setPlugin( self, plugin ):
        """
        Sets the plugin instance used for this widget.
        
        :param      plugin | <XConfigPlugin>
        """
        self._plugin = plugin
        self.refreshUi()