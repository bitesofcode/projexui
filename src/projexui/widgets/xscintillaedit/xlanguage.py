#!/usr/bin/python

""" Defines a language class that will be used for the XScintillaEdit """

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
import re
import sys

from ConfigParser import ConfigParser

import projex

logger = logging.getLogger(__name__)

from projex.text import nativestring
from projexui.qt import Qsci, wrapVariant

#------------------------------------------------------------------------------

class XMethodDescriptor(object):
    def __init__( self, dtype, expr ):
        self.dtype      = dtype
        self.exprText   = expr
        try:
            self.expr   = re.compile(expr, re.DOTALL|re.MULTILINE)
        except:
            logger.exception('Invalid regex: %s' % expr)
            self.expr = None
    
    def search( self, text, startpos = -1 ):
        if ( not self.expr ):
            return None
        
        if ( startpos != -1 ):
            return self.expr.search(text,startpos)
        else:
            return self.expr.search(text)
        
#------------------------------------------------------------------------------

class XLanguage(object):
    _plugins = {}
    
    def __init__(self):
        self._name              = ''
        self._fileTypes         = []
        
        # lexer class information
        self._lexerType         = -1
        self._lexerTypeName     = ''
        self._lexerModule       = ''
        self._lexerColorTypes   = {}
        self._lexerProperties   = {}
        self._custom            = False
        self._sourcefile        = ''
        self._tabWidth          = 0
        self._colorStyles       = {}
        
        # comment information
        self._lineComment       = ''
        
        # method descriptors
        self._descriptors       = []
    
    def addDescriptor( self, type, expr ):
        self._descriptors.append( XMethodDescriptor(type,expr) )
    
    def createLexer( self, parent = None, colorSet = None ):
        # create an instance of the lexer
        cls = self.lexerType()
        if ( not cls ):
            return None
            
        output = cls(parent)
        if ( output and parent ):
            try:
                parent.setLexer(output)
            except AttributeError:
                pass
            
            # set lexer property options
            for key, value in self.lexerProperties().items():
                setter = getattr(output, 'set' + key[0].upper() + key[1:], None)
                if setter:
                    setter(value)
                else:
                    output.setProperty(key, wrapVariant(value))
            
            output.setFont(parent.font())
            
            if ( colorSet ):
                self.setColorSet(output, colorSet)
            
        return output
    
    def descriptors( self ):
        return self._descriptors
    
    def isCustom( self ):
        return self._custom
    
    def name( self ):
        return self._name
    
    def lexerColorTypes( self ):
        return self._lexerColorTypes
    
    def lineComment( self ):
        return self._lineComment
    
    def loadLexerType( self ):
        # use a custom lexer module
        if ( self._lexerModule ):
            # retrieve the lexer module
            module = sys.modules.get(self._lexerModule)
            
            # try to import the module
            if ( not module ):
                try:
                    __import__(self._lexerModule)
                    module = sys.modules.get(self._lexerModule)
                except:
                    err = 'Could not import %s module' % self._lexerModule
                    logger.exception(err)
                    self._lexerType = None
                    return None
        
        # otherwise, its in the Qsci module
        else:
            module = Qsci
            
        # retrieve the lexer class
        self._lexerType = module.__dict__.get(self._lexerTypeName)
        if ( not self._lexerType ):
            err = 'Lexer Error: No %s class in %s' % (self._lexerTypeName,
                                                      module.__name__)
            logger.warning(err)
    
    def fileTypes( self ):
        return self._fileTypes
    
    def lexerProperties(self):
        return self._lexerProperties
    
    def lexerType( self ):
        if ( self._lexerType == -1 ):
            self.loadLexerType()
        return self._lexerType
    
    def lexerTypeName( self ):
        return self._lexerTypeName
    
    def lexerModule( self ):
        return self._lexerModule
    
    def save( self, filename = '' ):
        if ( not filename ):
            filename = self.filename()
        if ( not filename ):
            return False
        
        parser = ConfigParser()
        parser.add_section('GLOBALS')
        parser.set( 'GLOBALS', 'name', self.name() )
        parser.set( 'GLOBALS', 'filetypes', ';'.join(self.fileTypes()) )
        parser.set( 'GLOBALS', 'linecomment', self.lineComment() )
        
        parser.add_section('LEXER')
        parser.set( 'LEXER', 'class', self.lexerTypeName() )
        parser.set( 'LEXER', 'module', self.lexerModule() )
        
        if self.lexerProperties():
            parser.add_section('LEXER_PROPERTIES')
            for i, (key, value) in enumerate(self.lexerProperties().items()):
                store = '{0}:{1}'.format(key, value)
                store_name = 'prop{0}'.format(i)
                parser.set('LEXER_PROPERTIES', store_name, store)
        
        parser.add_section('DESCRIPTORS')
        for i, desc in enumerate( self._descriptors ):
            parser.set('DESCRIPTORS','%s%i' % (desc.dtype,i),desc.exprText)
        
        parser.add_section('COLOR_TYPES')
        for key, value in self.lexerColorTypes().items():
            parser.set('COLOR_TYPES',key,','.join([nativestring(val) for val in value]))
        
        # save the language
        f = open(filename,'w')
        parser.write(f)
        f.close()
        
        self._sourcefile = filename
        return True
    
    def setColorSet( self, lexer, colorSet ):
        for colorKey, colorStyles in self._colorStyles.items():
            color = colorSet.color(colorKey)
            for colorStyle in colorStyles:
                lexer.setColor(color, colorStyle)
        
        lexer.setPaper(colorSet.color('Background'))
        lexer.setDefaultColor(colorSet.color('Text'))
        
    def setCustom( self, state ):
        self._custom = state
    
    def setFileTypes( self, fileTypes ):
        self._fileTypes = fileTypes
    
    def setLexerTypeName( self, className ):
        self._lexerTypeName = className
    
    def setLexerModule( self, module ):
        self._lexerModule = module
    
    def setLineComment( self, lineComment ):
        self._lineComment = lineComment
    
    def setLexerColorTypes( self, lexerColorTypes ):
        self._lexerColorTypes = lexerColorTypes
    
    def setLexerProperty(self, key, value):
        self._lexerProperties[nativestring(key)] = value

    def setLexerProperties(self, props):
        self._lexerProperties = props.copy()
    
    def setName( self, name ):
        self._name = name
    
    def setTabWidth(self, width):
        self._tabWidth = width
    
    def sourcefile( self ):
        return self._sourcefile
    
    def tabWidth(self):
        return self._tabWidth
    
    @staticmethod
    def byFileType( fileType ):
        """
        Looks up the language plugin by the inputed file type.
        
        :param      fileType | <str>
        
        :return     <XLanguage> || None
        """
        XLanguage.load()
        
        for lang in XLanguage._plugins.values():
            if ( fileType in lang.fileTypes() ):
                return lang
        return None
    
    @staticmethod
    def byLexer( lexer ):
        """
        Looks up the language plugin by the lexer class of the inputed lexer.
        
        :param      lexer | <QsciLexer>
        
        :return     <XLanguage> || None
        """
        XLanguage.load()
        
        lexerType = type(lexer)
        for lang in XLanguage._plugins.values():
            if ( lang.lexerType() == lexerType ):
                return lang
        return None
    
    @staticmethod
    def byName( name ):
        """
        Looks up the language plugin by the name of the language.
        
        :param      name | <str>
        
        :return     <XLanguage> || None
        """
        XLanguage.load()
        
        return XLanguage._plugins.get(nativestring(name))
    
    @staticmethod
    def fromConfig( filename ):
        parser = ConfigParser()
        
        if not parser.read(filename):
            return False
        
        plugin = XLanguage()
        plugin._name            = parser.get('GLOBALS','name')
        plugin._fileTypes       = parser.get('GLOBALS','filetypes').split(';')
        try:
            plugin._tabWidth = int(parser.get('GLOBALS', 'tabwidth'))
        except:
            pass
        
        try:
            colorKeys = parser.options('COLOR_TYPES')
        except:
            colorKeys = []
        
        colorStyles = {}
        for colorKey in colorKeys:
            values = parser.get('COLOR_TYPES', colorKey)
            if not values:
                continue
            
            colorStyles[colorKey.capitalize()] = map(int, values.split(','))
        
        plugin._colorStyles = colorStyles
        
        # try to load the line comment information
        try:
            plugin._lineComment = parser.get('GLOBALS','linecomment')
        except:
            pass
        
        # try to load the lexer information
        try:
            plugin._lexerTypeName   = parser.get('LEXER','class')
            plugin._lexerModule     = parser.get('LEXER','module')
        except:
            pass
        
        # try to load the lexer properties
        try:
            options = parser.options('LEXER_PROPERTIES')
        except:
            options = []

        props = {}
        for option in options:
            try:
                key, value = parser.get('LEXER_PROPERTIES', option).split(':')
            except:
                continue
            
            try:
                value = eval(value)
            except:
                pass
            
            props[key] = value
        
        plugin._lexerProperties = props
        
        # load the different descriptor options
        try:
            options = parser.options('DESCRIPTORS')
        except:
            options = []
        
        for option in options:
            expr = parser.get('DESCRIPTORS',option)
            option = re.match('([^\d]*)\d*',option).groups()[0]
            plugin._descriptors.append(XMethodDescriptor(option,expr))
        
        # load the different color map options
        try:
            options = parser.options('COLOR_TYPES')
        except:
            options = []
        
        for option in options:
            vals = []
            for val in parser.get('COLOR_TYPES',option).split(','):
                if not val:
                    continue
                
                try:
                    vals.append(int(val))
                except:
                    pass
            plugin._lexerColorTypes[option] = vals
        
        plugin._sourcefile = filename
        
        return plugin
    
    @staticmethod
    def loadPlugins(path, custom = False):
        path = projex.environ().expandvars(path)
        if ( not os.path.exists(path) ):
            return False
        
        files = glob.glob(os.path.join(path, '*.ini'))
        
        for file in files:
            plugin = XLanguage.fromConfig(file)
            
            if ( plugin ):
                plugin.setCustom(custom)
                XLanguage._plugins[plugin.name()] = plugin
            else:
                logger.warning('Could not import %s' % file)
    
    @staticmethod
    def load():
        if XLanguage._plugins:
            return
        
        # load the installed plugins
        XLanguage.loadPlugins(os.path.dirname(__file__) + '/lang')
        
        # load additional languages
        for key in os.environ.keys():
            if key.startswith('PROJEX_XLANG_PATH_'):
                XLanguage.loadPlugins(os.environ[key])
    
    @staticmethod
    def refresh():
        XLanguage._plugins.clear()
        XLanguage.load()
    
    @staticmethod
    def pluginLanguages():
        XLanguage.load()
        
        return sorted(XLanguage._plugins.keys())
    
    @staticmethod
    def pluginFileTypes():
        XLanguage.load()
        
        keys = sorted(XLanguage._plugins.keys())
        
        output = []
        output.append( 'All Files (*.*)' )
        output.append( 'Text Files (*.txt)' )
        
        for key in keys:
            ptypes = '*'+';*'.join(XLanguage._plugins[key].fileTypes())
            output.append( '%s Files (%s)' % (key, ptypes) )
        
        return ';;'.join(output)