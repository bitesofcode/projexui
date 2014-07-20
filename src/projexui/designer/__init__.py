#!/usr/bin/python

""" Auto-generates Qt ui designer plugins. """

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

import glob
import logging
import os
import sys

import projex
import projexui

logger = logging.getLogger(__name__)

WIDGET_PATH = os.path.pathsep.join((
                os.path.dirname(projexui.__file__) + '/widgets',
                os.environ.get('PROJEXUI_DESIGNER_WIDGETPATH', '')))
                
BUILD_PATH  = os.environ.get('PROJEXUI_DESIGNER_BUILDPATH', 
                             os.path.dirname(__file__) + '/build')

PLUGIN_DEF = """\
#!/usr/bin/python

''' Auto-generated ui widget plugin '''

from projexui.qt.QtDesigner import QPyDesignerCustomWidgetPlugin
from projexui.qt.QtGui import QIcon

import projex.resources
from %(module)s import %(class)s as Base
setattr(Base, '__designer_mode__', True)

DEFAULT_XML = '''\
<ui language="c++" displayname="%(class)s">
  <widget class="%(class)s" name="%(class)s"/>
  <customwidgets>
    <customwidget>
      <class>%(class)s</class>
      <header>%(module)s</header>
      <addpagemethod>%%(addpagemethod)s</addpagemethod>
      <propertyspecifications>
        %%(propertyspecs)s
      </propertyspecifications>
    </customwidget>
  </customwidgets>
</ui>'''

class %(class)sPlugin(QPyDesignerCustomWidgetPlugin):
    def __init__(self, parent=None):
        super(%(class)sPlugin, self).__init__(parent)
        
        self.initialized = False
    
    def initialize(self, core):
        if self.initialized:
            return
        
        self.initialized = True
    
    def isInitialized(self):
        return self.initialized
    
    def createWidget(self, parent):
        return Base(parent)
    
    def name(self):
        return getattr(Base, '__designer_name__', Base.__name__)
    
    def group(self):
        return getattr(Base, '__designer_group__', 'ProjexUI')
    
    def icon(self):
        default = projex.resources.find('img/logo_16.png')
        return QIcon(getattr(Base, '__designer_icon__', default))
    
    def toolTip( self ):
        docs = getattr(Base, '__doc__', '')
        if docs is None:
            docs = ''
        return getattr(Base, '__designer_tooltip__', docs)
    
    def whatsThis( self ):
        return ''
    
    def isContainer( self ):
        return getattr(Base, '__designer_container__', False)
    
    def includeFile( self ):
        return '%(module)s'
    
    def domXml( self ):
        opts = {}
        specs = []
        
        for prop, info in getattr(Base, '__designer_propspecs__', {}).items():
            xml  = '<%%spropertyspecification name="%%s" type="%%s"/>'
            xml %%= (info[0], prop, info[1])
            specs.append(xml)
        
        opts['addpagemethod'] = getattr(Base, '__designer_addpage__', '')
        opts['propertyspecs'] = ''.join(specs)
        default = DEFAULT_XML %% opts
        return getattr(Base, '__designer_xml__', default)
"""

def generatePlugins(widgetPath = None, buildPath = None):
    """
    Generates all the plugin files for the system and imports them.
    
    :param      widgetPath | <str> || None
                buildPath  | <str> || None
    """
    if widgetPath is None:
        widgetPath = WIDGET_PATH
        
    if buildPath is None:
        buildPath = BUILD_PATH
    
    for basepath in widgetPath.split(os.path.pathsep):
        if not basepath:
            continue
            
        # load packaged widgets
        for filepath in glob.glob(os.path.join(basepath, '*/__init__.py')):
            generatePlugins(os.path.dirname(filepath), buildPath)
        
        # load module widgets
        for filepath in glob.glob(os.path.join(basepath, '*.py')):
            generatePlugin(filepath, buildPath)

def generatePlugin(sourcePath, buildPath = None):
    """
    Generates a particular ui plugin for ths system and imports it.
    
    :param      widgetPath  | <str>
                buildPath   | <str> || None
    """
    if ( buildPath is None ):
        buildPath = BUILD_PATH
        
    pkg_name = projex.packageFromPath(sourcePath)
    module = os.path.basename(sourcePath).split('.')[0]
    if module != '__init__':
        pkg_name += '.' + module
    
    try:
        __import__(pkg_name)
    except ImportError, e:
        logging.exception(e)
        return
    
    module = sys.modules.get(pkg_name)
    if not module:
        return
        
    if not hasattr(module, '__designer_plugins__'):
        logger.info('%s has no __designer_plugins__ defined.' % pkg_name)
        return
    
    if not os.path.exists(buildPath):
        os.mkdir(buildPath)
    
    for plug in module.__designer_plugins__:
        output_path = os.path.join(buildPath, 
                                   '%splugin.py' % plug.__name__.lower())
        
        # generate the options
        options = {}
        options['module'] = pkg_name
        options['class']  = plug.__name__
        
        # save the plugin
        f = open(output_path, 'w')
        f.write(PLUGIN_DEF % options)
        f.close()

if __name__ == '__main__':
    widgetPath, buildPath = (None, None)
    if len(sys.argv) > 1:
        widgetPath = sys.argv[1]
    if len(sys.argv) > 2:
        buildPath = sys.argv[2]
    logging.basicConfig()
    logger.setLevel(logging.INFO)
    generatePlugins(widgetPath, buildPath)