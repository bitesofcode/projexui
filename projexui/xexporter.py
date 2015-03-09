#!/usr/bin/python

""" Defines common commands that can be used to streamline ui development. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

import projex
from projex.enum import enum
from projex.decorators import abstractmethod

from projexui.exporters import __plugins__

class XExporter(object):
    Flags = enum('SupportsTree')
    
    _plugins = []
    
    def __init__(self, name, filetype):
        self._name = name
        self._filetype = filetype
        self._flags = 0
    
    @abstractmethod()
    def exportTree(self, tree, filename):
        """
        Exports the tree information to the given filename.
        
        :param      tree     | <QTreeWidget>
                    filename | <str>
        
        :return     <bool> | success
        """
        return False
    
    def filetype(self):
        """
        Returns the filetype associated with this exporter.
        
        :return     <str>
        """
        return self._filetype
    
    def flags(self):
        """
        Returns the flags associated with this plugin.
        
        :return     <XExporter.Flags>
        """
        return self._flags
    
    def name(self):
        """
        Returns the name of this exporter.
        
        :return     <str>
        """
        return self._name
    
    def setFlag(self, flag, state=True):
        """
        Sets whether or not the given flag is enabled or disabled.
        
        :param      flag | <XExporter.Flags>
        """
        has_flag = self.testFlag(flag)
        if has_flag and not state:
            self.setFlags(self.flags() ^ flag)
        elif not has_flag and state:
            self.setFlags(self.flags() | flag)
    
    def setFlags(self, flags):
        """
        Sets the flags for this plugin.
        
        :param      flags | <XExporter.Flags>
        """
        self._flags = flags
    
    def testFlag(self, flag):
        """
        Tests to see if the inputed flag is applied for this plugin.
        
        :param      flag | <XExporter.Flags>
        """
        return (self.flags() & flag) != 0
    
    @staticmethod
    def init():
        """
        Initializes the exporter system.
        """
        projex.importmodules(__plugins__)
    
    @staticmethod
    def plugins(flags=None):
        """
        Returns the plugins registered for the exporter.  If the optional
        flags are set then only plugins with the inputed flags will be
        returned.
        
        :param      flags | <XExporter.Flags>
        """
        XExporter.init()
        
        plugs = XExporter._plugins[:]
        if flags is not None:
            return filter(lambda x: x.testFlag(flags), plugs)
        return plugs
        
    @staticmethod
    def register(plugin):
        """
        Registers the inputed plugin to the system.
        
        :param      <XExporter>
        """
        XExporter._plugins.append(plugin)