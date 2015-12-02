#!/usr/bin/python

""" Creates reusable resources for the gui systems """

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

import cStringIO
import os
import logging
import projex
import projex.text
import subprocess
import sys

from xml.etree import ElementTree

from projex.text import nativestring
import projexui
import projexui.qt
from projexui.qt import QtCore

# define globals
log = logging.getLogger(__name__)

class XResourceManager(object):
    def __init__(self,
                 name,
                 path,
                 plugins,
                 resourcePath=None,
                 defaults=None,
                 useFilepath=None,
                 logger=None):
        
        # define defaults
        if defaults is None:
            defaults = {}
        
        # define use filepath
        if useFilepath is None:
            disabled = os.environ.get('DISABLE_FILE_RSC', 'True') == 'True'
            useFilepath = 'python' in sys.executable and not disabled
            
            # always use the filepath for the PyQt4 system
            if 'PyQt4' in sys.executable and \
                sys.executable.endswith('designer.exe'):
                useFilepath = True
        
        # define resource path
        if resourcePath is None:
            for i in range(2, 4):
                rcpath = os.path.join(path, *['..']*i+['resources'])
                if os.path.exists(rcpath):
                    resourcePath = os.path.abspath(rcpath)
                    break
        
        # define custom properties
        self._name = name
        self._plugins = plugins
        self._basePath = path
        self._resourcePath = resourcePath
        self._pluginPath = os.path.dirname(plugins.__file__)
        self._defaults = defaults
        self._useFilepath = useFilepath
        self._logger = logger
        self._initialized = False

    def basePath(self):
        """
        Returns the base path for this resource instance.
        
        :return     <str>
        """
        return self._basePath

    def build(self, force=False):
        """
        Generates the resource file and module for the given path.
        
        :param      force | <bool>
        """
        basepath = self.resourcePath()
        if basepath is None:
            return
        
        outpath = self.pluginPath()
        logger = self.logger()
        
        for rsc in os.listdir(basepath):
            rscpath = os.path.join(basepath, rsc)
            if os.path.isfile(rscpath):
                continue

            opts = (projexui.qt.QT_WRAPPER.lower(), rsc)
            xml_file = os.path.join(basepath, '{1}.qrc'.format(*opts))
            py_file = os.path.join(outpath, '{0}_{1}_rc.py'.format(*opts))
            
            # determine the update for the build system
            if os.path.exists(py_file):
                modtime = os.path.getmtime(py_file)
                outdated = force
            else:
                modtime = None
                outdated = True
            
            # generate the XML data for the filepath
            basepath = os.path.normpath(os.path.abspath(basepath))
            rscpath = os.path.join(basepath, rsc)
            xroot = ElementTree.Element('RCC')
            for root, folders, files in os.walk(rscpath):
                if not files:
                    continue
                
                xresource = ElementTree.SubElement(xroot, 'qresource')
                opts = [rsc, root[len(rscpath)+1:].replace(os.path.sep, '/')]
                xresource.set('prefix', '{0}/{1}'.format(*opts).strip('/'))
                
                # add the files to the resource file
                for file in files:
                    filename = os.path.join(root, file)
                    if not outdated and modtime < os.path.getmtime(filename):
                        outdated = True
                    
                    xfile = ElementTree.SubElement(xresource, 'file')
                    xfile.set('alias', file)
                    xfile.text = os.path.relpath(filename, basepath)
            
            # if the resource file is out dated, then save and generate it
            if outdated and len(xroot):
                logger.info('Generating {0} resource file..'.format(xml_file))
                projex.text.xmlindent(xroot)
                ElementTree.ElementTree(xroot).write(xml_file)
                
                projexui.buildResourceFile(xml_file, py_file)

    def default(self, key, default=''):
        """
        Returns a key value pairing for default
        values when requesting a resource.
        
        :param      key | <str>
                    default | <value>
        
        :return     <str>
        """
        return self._defaults.get(key, default)

    def exists(self, relpath, rsc=None, useFilepath=None):
        """
        Checks to see if the inputed path represents an existing file or directory.

        :param      relpath     | <str>
                    rsc         | <str>
                    useFilepath | <bool> or None
        """
        path = self.find(relpath, rsc, useFilepath)
        if path.startswith(':'):
            return QtCore.QResource(path).isValid()
        else:
            return os.path.exists(path)

    def find(self, relpath, rsc=None, useFilepath=None):
        """
        Looks up the path for the resource based on the inputed relative path.
        
        :param      relpath | <str>
        
        :return     <str>
        """
        self.init()
        
        # load the default resource information
        if rsc is None:
            try:
                key = relpath.replace('\\', '/').split('/')[0]
                rsc = self.default(key)
            except IndexError:
                return ''
        
        # determine the filepath location
        relpath = os.path.normpath(nativestring(relpath))
        rscpath = self.resourcePath()
        
        if useFilepath is None:
            useFilepath = self.useFilepath()
        
        # return from the filesystem
        if useFilepath and rscpath:
            if rsc and isinstance(rsc, XResourceManager):
                return rsc.find(relpath, useFilepath=useFilepath)
            elif rsc:
                filepath = os.path.join(rscpath, rsc, relpath)
            else:
                filepath = os.path.join(rscpath, relpath)
            
            if os.path.exists(filepath):
                return filepath
        
        # return resource
        if isinstance(rsc, XResourceManager):
            return rsc.find(relpath, useFilepath=useFilepath)
        elif rsc:
            return ':{0}/{1}'.format(rsc, relpath.replace(os.path.sep, '/'))
        else:
            return ':{0}'.format(relpath.replace(os.path.sep, '/'))

    def listdir(self, relpath, rsc=None):
        """
        Returns a list of the files within a path.  When compiled, it will
        list the files within a QResource, otherwise will list the files
        within the directory.
        
        :param      relpath | <str>
                    rsc     | <str> || None
        
        :return     [<str>, ..]
        """
        filepath = self.find(relpath, rsc)
        
        # parse a resource object
        if filepath.startswith(':'):
            resource = QtCore.QResource(filepath)
            
            # load the resource
            return map(str, resource.children())
        
        # parse a filepath
        elif os.path.isdir(filepath):
            return os.listdir(filepath)
        
        return []

    def init(self):
        """
        Initializes the plugins for this resource manager.
        """
        # import any compiled resource modules
        if not self._initialized:
            self._initialized = True
            wrap = projexui.qt.QT_WRAPPER.lower()
            ignore = lambda x: not x.split('.')[-1].startswith(wrap)
            projex.importmodules(self.plugins(), ignore=ignore)

    def isdir(self, relpath, rsc=None):
        """
        Returns whether or not the resource is a directory.
        
        :return     <bool>
        """
        filepath = self.find(relpath, rsc)
        if filepath.startswith(':'):
            resource = QtCore.QResource(filepath)
            return not resource.isFile()
        else:
            return os.path.isdir(filepath)

    def isfile(self, relpath, rsc=None):
        """
        Returns whether or not the resource is a directory.
        
        :return     <bool>
        """
        filepath = self.find(relpath, rsc)
        if filepath.startswith(':'):
            resource = QtCore.QResource(filepath)
            return resource.isFile() and resource.isValid()
        else:
            return os.path.isfile(filepath)

    def load(self, relpath, rsc=None, mode='r', useFilepath=None):
        """
        Opens a file like object for reading for the given relpath.
        
        :param      relpath | <str>
        
        :return     <File> || <QFile> || None
        """
        filepath = self.find(relpath, rsc, useFilepath=useFilepath)
        
        # parse a resource object
        if filepath.startswith(':'):
            return QtCore.QFile(filepath)
        
        # parse a filepath
        elif os.path.isfile(filepath):
            return open(filepath, mode)
        
        # return an unknown object
        else:
            return None

    def logger(self):
        """
        Returns the logger associated with this resource manager.
        
        :return     <logging.Logger>
        """
        if self._logger is None:
            return log
        return self._logger

    def name(self):
        """
        Returns the name for this resource manager.
        
        :return     <str>
        """
        return self._name

    def plugins(self):
        """
        Returns the module containing the plugins for this resource manager.
        
        :return     <module>
        """
        return self._plugins

    def pluginPath(self):
        """
        Returns the plugin path for this manager.  This will be the path
        where all generated resources will go.
        
        :return     <str>
        """
        return self._pluginPath

    def read(self, relpath, rsc=None, mode='r', useFilepath=None):
        """
        Reads the contents for a given relative filepath.  This will call
        the load function and do a full read on the file contents.
        
        :param      relpath | <str>
                    rsc     | <str> || None
                    mode    | <str> | 'r' or 'rb'
        
        :return     <str>
        """
        f = self.load(relpath, rsc, mode, useFilepath=useFilepath)
        if f is None:
            return ''
        
        # use a QFile
        if isinstance(f, QtCore.QFile):
            if f.open(QtCore.QFile.ReadOnly):
                data = nativestring(f.readAll())
                f.close()
            else:
                data = ''
        else:
            data = f.read()
            f.close()
        
        return data

    def resourcePath(self):
        """
        Returns the resources path for this manager.  This will be the path
        where all generated resources will go.
        
        :return     <str>
        """
        return self._resourcePath

    def walk(self, root):
        """
        Walks the path for a returning the folders and roots for the
        files found, similar to os.walk.
        
        :param      path | <str>
        """
        files = []
        folders = []
        
        for relpath in self.listdir(root):
            if self.isfile(root + '/' + relpath):
                files.append(relpath)
            else:
                folders.append(relpath)
        
        yield root, folders, files
        
        for folder in folders:
            folderpath = root + '/' + folder
            for sub_root, sub_folders, sub_files in self.walk(folderpath):
                yield sub_root, sub_folders, sub_files

    def setup(self, glbls):
        """
        Sets up the resource manager as modular functions.
        
        :param      glbls | <dict>
        """
        if not self.pluginPath() in sys.path:
            log.debug(self.pluginPath())
            sys.path.append(self.pluginPath())
        
        glbls['find'] = self.find
        glbls['listdir'] = self.listdir
        glbls['load'] = self.load
        glbls['read'] = self.read
        glbls['exists'] = self.exists
        glbls['setdefault'] = self.setDefault
        glbls['basePath'] = self.basePath
        glbls['setBasePath'] = self.setBasePath
        glbls['walk'] = self.walk
        glbls['isdir'] = self.isdir
        glbls['isfile'] = self.isfile
        glbls['init'] = self.init
        
        # setup the build system
        if 'python' in sys.executable and not self.useFilepath():
            self.build()

    def setBasePath(self, path):
        """
        Sets the base path for the module to the inputed path.
        
        :param      path | <str>
        """
        self._basePath = path

    def setDefault(self, key, value):
        """
        Sets the default for a given key to the value.
        
        :param      key | <str>
                    value | <str> || <XResourceManager>
        """
        if value is None:
            self._defaults.pop(key, None)
        else:
            self._defaults[key] = value

    def useFilepath(self):
        """
        Returns whether or not to use the filepath when loading resources.
        
        :return     <bool>
        """
        return self._useFilepath

