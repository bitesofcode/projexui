#!/usr/bin/python

''' Auto-generated ui widget plugin '''

from projexui.qt.QtDesigner import QPyDesignerCustomWidgetPlugin
from projexui.qt.QtGui import QIcon

import projex.resources
from projexui.widgets.xorbquerywidget import XOrbQueryWidget as Base
setattr(Base, '__designer_mode__', True)

DEFAULT_XML = '''<ui language="c++" displayname="XOrbQueryWidget">
  <widget class="XOrbQueryWidget" name="XOrbQueryWidget"/>
  <customwidgets>
    <customwidget>
      <class>XOrbQueryWidget</class>
      <header>projexui.widgets.xorbquerywidget</header>
      <addpagemethod>%(addpagemethod)s</addpagemethod>
      <propertyspecifications>
        %(propertyspecs)s
      </propertyspecifications>
    </customwidget>
  </customwidgets>
</ui>'''

class XOrbQueryWidgetPlugin(QPyDesignerCustomWidgetPlugin):
    def __init__(self, parent=None):
        super(XOrbQueryWidgetPlugin, self).__init__(parent)
        
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
        return 'projexui.widgets.xorbquerywidget'
    
    def domXml( self ):
        opts = {}
        specs = []
        
        for prop, info in getattr(Base, '__designer_propspecs__', {}).items():
            xml  = '<%spropertyspecification name="%s" type="%s"/>'
            xml %= (info[0], prop, info[1])
            specs.append(xml)
        
        opts['addpagemethod'] = getattr(Base, '__designer_addpage__', '')
        opts['propertyspecs'] = ''.join(specs)
        default = DEFAULT_XML % opts
        return getattr(Base, '__designer_xml__', default)
