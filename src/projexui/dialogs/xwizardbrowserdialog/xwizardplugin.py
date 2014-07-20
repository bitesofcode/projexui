#!/usr/bin/python

""" Defines the base plugin system for the wizard structure. """

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
import zipfile
from xml.etree import ElementTree

from projex.text import nativestring
from projexui.wizards.xscaffoldwizard import XScaffoldWizard

import projex
import projexui

from projex.decorators import abstractmethod

class XWizardPlugin(object):
    _plugins    = None
    _groupIcons = None
    
    """ Defines a basic plugin for the wizard system. """
    def __init__( self, 
                  wizardType      = 'Python',
                  wizardGroup     = 'Basic', 
                  title           = '',
                  iconFile        = '' ):
        
        self._wizardType      = wizardType
        self._wizardGroup     = wizardGroup
        self._title           = title
        self._iconFile        = iconFile
        self._description     = ''
    
    def description( self ):
        """
        Returns the description for this wizard.
        
        :return     <str>
        """
        return self._description
    
    def iconFile( self ):
        """
        Returns the icon file that is linked that to this plugin.
        
        :return     <str>
        """
        if not os.path.isfile(self._iconFile):
            return projexui.resources.find(self._iconFile)
        return self._iconFile
    
    @abstractmethod
    def runWizard( self, parent ):
        """
        Runs the wizard for this plugin.
        
        :param      parent | <QWidget>
        
        :return     <bool> accepted
        """
        return False
    
    def setDescription( self, description ):
        """
        Sets the description that will be used for this wizard.
        
        :param      description | <str>
        """
        self._description = description
    
    def setWizardGroup( self, groupName ):
        """
        Sets the wizard group for this plugin.
        
        :param      groupName | <str>
        """
        self._wizardGroup = groupName
    
    def setWizardType( self, typ ):
        """
        Sets the type group that this wizard plugin will be in.
        
        :param      typ | <str>
        """
        self._wizardType = typ
    
    def setIconFile( self, filename ):
        """
        Sets the icon file that is linked to this plugin.
        
        :param      filename | <str>
        """
        self._iconFile = filename
    
    def setTitle( self, title ):
        """
        Sets the title for this widget to use when shown in the wizard dialog.
        
        :param      title | <str>
        """
        self._title = title
    
    def title( self ):
        """
        Returns the title that will be shown for this plugin in the wizard \
        dialog when used.
        
        :return     <str>
        """
        return self._title
    
    def uniqueName( self ):
        """
        Returns the path to this plugin based on its group and title.
        
        :return     <str>
        """
        return '%s/%s/%s' % (self.wizardType(), 
                             self.wizardGroup(), 
                             self.title())
    
    def wizardGroup( self ):
        """
        Returns the wizard group that is linked to this plugin.
        
        :return     <str>
        """
        return self._wizardGroup
    
    def wizardType( self ):
        """
        Returns the wizard type that is linked to this plugin.
        
        :return     <str>
        """
        return self._wizardType
    
    @classmethod
    def groupIcon( cls, groupName, default = None ):
        """
        Returns the icon for the inputed group name.
        
        :param      groupName | <str>
                    default   | <str> || None
        
        :return     <str>
        """
        if ( cls._groupIcons is None ):
            cls._groupIcons = {}
            
        if ( not default ):
            default = projexui.resources.find('img/settings_32.png')
        
        return cls._groupIcons.get(nativestring(groupName), default)
    
    @classmethod
    def find( cls, name ):
        """
        Finds a particular wizard plugin based on its name.
        
        :param      name | <str> || None
        """
        if ( cls._plugins is None ):
            cls._plugins = {}
            
        return cls._plugins.get(nativestring(name))
    
    @classmethod
    def plugins( cls ):
        """
        Returns a list of the plugins linked to this class.
        
        :return     [<XWizardPlugin>, ..]
        """
        if ( cls._plugins is None ):
            cls._plugins = {}
            
        return cls._plugins.values()
    
    @classmethod
    def setGroupIcon( cls, groupName, icon ):
        """
        Sets the group icon for the wizard plugin to the inputed icon.
        
        :param      groupName | <str>
                    icon      | <str>
        """
        if ( cls._groupIcons is None ):
            cls._groupIcons = {}
            
        cls._groupIcons[nativestring(groupName)] = icon
    
    @classmethod
    def register( cls, plugin ):
        """
        Registers a particular plugin to the global system at the given name.
        
        :param      plugin  | <XWizardPlugin>
        """
        if ( not plugin ):
            return
            
        if ( cls._plugins is None ):
            cls._plugins = {}
            
        cls._plugins[plugin.uniqueName()] = plugin

#----------------------------------------------------------------------

class XScaffoldWizardPlugin(XWizardPlugin):
    """ Utilizes the scaffolding system from projex to create plugins. """
    def __init__(self, scaffold):
        super(XScaffoldWizardPlugin, self).__init__(scaffold.language(), 
                                                    scaffold.group(), 
                                                    scaffold.name(), 
                                                    scaffold.icon())
        
        self._scaffold = scaffold

    def runWizard(self, parent):
        """
        Runs the wizard instance for this plugin.
        
        :param      parent | <QWidget>
        
        :return     <bool> | success
        """
        wizard = XScaffoldWizard(self._scaffold, parent)
        return wizard.exec_()

