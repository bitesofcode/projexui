#!/usr/bin/python

"""
Subclasses the QSettings instance to support additional functionality,
including registerFormat syntax, which by default is not supported in
Python.
"""

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

import cPickle
import os
import logging

import projex.text
from projex.text import nativestring

from projexui.qt import wrapVariant, unwrapVariant, QtCore, QtGui
from xml.etree import ElementTree
from xml.parsers.expat import ExpatError

try:
    import yaml
except ImportError:
    yaml = None

log = logging.getLogger(__name__)

class XSettingsFormat(object):
    def __init__(self, extension):
        self._extension = extension

    def allKeys(self):
        """
        Returns a list of all the keys associated with this format.
        
        :return     [<str>, ..]
        """
        raise NotImplementedError

    def beginGroup(self, prefix):
        """
        Begins a new group for this format.
        
        :param      prefix | <str>
        """
        raise NotImplementedError

    def endGroup(self):
        """
        Ends the current group for this format.
        """
        raise NotImplementedError

    def extension(self):
        """
        Returns the extension associated with this format.
        
        :return     <str>
        """
        return self._extension

    def load(self, filename):
        """
        Loads the data for this settings format from the given filename.
        
        :param      filename | <str>
        
        :return     <bool> | success
        """
        raise NotImplementedError

    def remove(self, key):
        raise NotImplementedError

    def save(self, filename):
        """
        Saves the data for this settings format from the given filename.
        
        :param      filename | <str>
        
        :return     <bool> | success
        """
        raise NotImplementedError

#----------------------------------------------------------------------

class XmlFormat(XSettingsFormat):
    def __init__(self):
        super(XmlFormat, self).__init__('xml')
        
        # define custom properties
        self._xroot = ElementTree.Element('settings')
        self._xroot.set('version', '1.0')
        self._xstack = [self._xroot]
        self._encoding = 'UTF-8'
    
    def beginGroup(self, prefix):
        """
        Starts a new group for the given prefix.
        
        :param      prefix | <str>
        """
        curr = self._xstack[-1]
        next = curr.find(prefix)
        if next is None:
            next = ElementTree.SubElement(curr, prefix)
        self._xstack.append(next)
    
    def clear(self):
        """
        Clears the settings for this XML format.
        """
        self._xroot = ElementTree.Element('settings')
        self._xroot.set('version', '1.0')
        self._xstack = [self._xroot]
    
    def encoding(self):
        """
        Returns the encoding for this XML.
        
        :return     <str>
        """
        return self._encoding
    
    def load(self, filename):
        """
        Loads the settings from the inputed filename.
        
        :param      filename | <str>
        """
        try:
            self._xroot = ElementTree.parse(filename).getroot()
            self._xstack = [self._xroot]
        except ExpatError:
            self.clear()
        
        return self._xroot is not None
    
    def endGroup(self):
        """
        Pops the latest xml element off the group stack.
        """
        if len(self._xstack) > 1:
            self._xstack.pop()
    
    def restoreValue(self, xelem):
        """
        Stores the value for the inptued instance to the given xml element.
        
        :param      xelem | <xml.etree.Element>
        
        :return     <variant>
        """
        typ = xelem.get('type')
        
        if typ == 'color':
            return QtGui.QColor(xelem.text)
        
        elif typ == 'point':
            return QtCore.QPoint(*map(int, xelem.text.split(',')))
        
        elif typ == 'pointf':
            return QtCore.QPointF(*map(float, xelem.text.split(',')))
        
        elif typ == 'rect':
            return QtCore.QRectF(*map(int, xelem.text.split(',')))
        
        elif typ == 'rectf':
            return QtCore.QRectF(*map(float, xelem.text.split(',')))
        
        elif typ == 'bytea':
            return QtCore.QByteArray(cPickle.loads(xelem.text))
        
        elif typ == 'pickle':
            return cPickle.loads(xelem.text)
        
        elif typ == 'xml':
            return xelem[0]
        
        elif typ in ('str', 'unicode'):
            return xelem.text
        
        else:
            try:
                return eval('{0}({1})'.format(typ, xelem.text))
            except:
                return None

    def remove(self, key):
        curr = self._xstack[-1]
        if key:
            curr.clear()
        else:
            parts = nativestring(key).split('/')
            for part in parts[:-1]:
                next = curr.find(part)
                if next is None:
                    return
                curr = next

            try:
                curr.remove(curr.find(parts[-1]))
            except StandardError:
                pass

    def save(self, filename):
        """
        Saves the settings to the inputed filename.
        
        :param      filename | <str>
        """
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        
        projex.text.xmlindent(self._xroot)
        xtree = ElementTree.ElementTree(self._xroot)
        xtree.write(filename, encoding=self.encoding(), xml_declaration=True)
        return True

    def setValue(self, key, value):
        """
        Saves the inputed key to the inputed value.
        
        :param      key | <str>
                    value | <variant>
        """
        parts = nativestring(key).split('/')
        curr = self._xstack[-1]
        for part in parts[:-1]:
            next = curr.find(part)
            if next is None:
                next = ElementTree.SubElement(curr, part)
            curr = next
        
        xval = curr.find(parts[-1])
        if xval is None:
            xval = ElementTree.SubElement(curr, parts[-1])
        
        self.storeValue(xval, value)

    def setEncoding(self, encoding):
        """
        Sets the encoding format to use for this settings.
        
        :param      encoding | <str>
        """
        self._encoding = encoding
    
    def storeValue(self, xelem, value):
        """
        Stores the value for the inptued instance to the given xml element.
        
        :param      xelem | <xml.etree.Element>
                    value | <variant>
        """
        typ = type(value)
        
        if typ == QtGui.QColor:
            xelem.set('type', 'color')
            xelem.text = nativestring(value.name())
        
        elif typ == QtCore.QPoint:
            xelem.set('type', 'point')
            xelem.text = '{0},{1}'.format(value.x(), value.y())
        
        elif typ == QtCore.QPointF:
            xelem.set('type', 'pointf')
            xelem.text = '{0},{1}'.format(value.x(), value.y())
        
        elif typ == QtCore.QRect:
            xelem.set('type', 'rect')
            xelem.text = '{0},{1},{2},{3}'.format(value.x(),
                                                  value.y(),
                                                  value.width(),
                                                  value.height())
        
        elif typ == QtCore.QRectF:
            xelem.set('type', 'rectf')
            xelem.text = '{0},{1},{2},{3}'.format(value.x(),
                                                  value.y(),
                                                  value.width(),
                                                  value.height())
        
        elif typ == QtCore.QByteArray:
            xelem.set('type', 'bytea')
            xelem.text = cPickle.dumps(nativestring(value))
        
        elif typ == ElementTree.Element:
            xelem.set('type', 'xml')
            xelem.append(value)
        
        elif typ in (list, tuple, dict):
            xelem.set('type', 'pickle')
            xelem.text = cPickle.dumps(value)
        
        else:
            if not typ in (str, unicode):
                value_text = nativestring(value)
            else:
                value_text = value
            
            xelem.set('type', typ.__name__)
            xelem.text = value_text

    def value(self, key, default=None):
        """
        Returns the inputed key to the inputed value.
        
        :param      key | <str>
        
        :return     <variant>
        """
        parts = nativestring(key).split('/')
        curr = self._xstack[-1]
        for part in parts[:-1]:
            next = curr.find(part)
            if next is None:
                next = ElementTree.SubElement(curr, part)
            curr = next
        
        xval = curr.find(parts[-1])
        if xval is None:
            return default
        
        return self.restoreValue(xval)

#----------------------------------------------------------------------

class YamlFormat(XSettingsFormat):
    def __init__(self):
        super(YamlFormat, self).__init__('yaml')
        
        # define custom properties
        self._root = {}
        self._stack = [self._root]

    def allKeys(self):
        """
        Returns the keys for this group level.
        
        :return     [<str>, ..]
        """
        return self._root.keys()

    def childKeys(self):
        """
        Returns the keys for this group level.
        
        :return     [<str>, ..]
        """
        return self._stack[-1].keys()

    def beginGroup(self, prefix):
        """
        Starts a new group for the given prefix.
        
        :param      prefix | <str>
        """
        curr = self._stack[-1]
        next = curr.get(prefix, {})
        curr.setdefault(prefix, next)
        self._stack.append(next)
    
    def clear(self):
        """
        Clears the settings for this Yaml format.
        """
        self._root.clear()
        self._stack = [self._root]

    def load(self, filename):
        """
        Loads the settings from the inputed filename.
        
        :param      filename | <str>
        
        :return     <bool> | success
        """
        if not os.path.exists(filename):
            return False
        
        data = None
        with open(filename, 'r') as f:
            data = f.read()
        
        try:
            root = yaml.load(data)
        except StandardError:
            root = None
        
        if root is None:
            root = {}
        
        self._root = root
        self._stack = [self._root]
        
        return len(self._root) != 0

    def endGroup(self):
        """
        Pops the latest group from the stack
        """
        if len(self._stack) > 1:
            self._stack.pop()

    def remove(self, key):
        curr = self._stack[-1]
        if not key:
            curr.clear()
        else:
            curr.pop(key, None)

    def setValue(self, key, value):
        """
        Sets the value for this settings key to the inputed value.
        
        :param      key     | <str>
                    value   | <variant>
        """
        curr = self._stack[-1]
        curr[key] = value

    def save(self, filename):
        """
        Saves the data for this settings instance to the given filename.
        
        :param      filename | <str>
        """
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        
        try:
            f = open(filename, 'w')
        except StandardError:
            log.error('Failed to access file: {0}'.format(filename))
            return False
        
        try:
            f.write(yaml.dump(self._root, default_flow_style=False))
        except StandardError:
            log.error('Failed to save settings: {0}'.format(filename))
            return False
        finally:
            f.close()
        
        return True
    
    def value(self, key, default=None):
        """
        Returns the value from the current settings.
        
        :param      key     | <str>
                    default | <variant>
        
        :return     <variant>
        """
        curr = self._stack[-1]
        return curr.get(key, default)

#----------------------------------------------------------------------

class XSettings(QtCore.QSettings):
    CustomFormat = XSettingsFormat

    def __init__(self, *args, **kwds):
        # replace the standard format with our custom format
        args = list(args)
        self._customFormat = None
        for i, arg in enumerate(args):
            try:
                if issubclass(arg, XSettings.CustomFormat):
                    self._customFormat = arg()
                    args[i] = QtCore.QSettings.Format(-1)
            except:
                continue
        
        super(XSettings, self).__init__(*args)
        
        self._filename = kwds.get('filename', '')

        # try to autoload the settings for a custom format
        if kwds.get('autoLoad', True):
            self.load()

    def allKeys(self):
        """
        Returns a list of all the keys for this settings instance.
        
        :return     [<str>, ..]
        """
        if self._customFormat:
            return self._customFormat.allKeys()
        else:
            return super(XSettings, self).allKeys()

    def childKeys(self):
        """
        Returns the list of child keys for this settings instance.
        
        :return     [<str>, ..]
        """
        if self._customFormat:
            return self._customFormat.childKeys()
        else:
            return super(XSettings, self).childKeys()

    def clear(self):
        """
        Clears out all the settings for this instance.
        """
        if self._customFormat:
            self._customFormat.clear()
        else:
            super(XSettings, self).clear()

    def customFormat(self):
        """
        Returns the custom formatter for this settings instance.
        
        :return     <XSettingsFormat> || None
        """
        return self._customFormat

    def beginGroup(self, prefix):
        """
        Begins a new group for this settings instance for the given
        settings.
        
        :param      prefix | <str>
        """
        if self._customFormat:
            self._customFormat.beginGroup(prefix)
        else:
            super(XSettings, self).beginGroup(prefix)

    def endGroup(self):
        """
        Ends the current group of xml data.
        """
        if self._customFormat:
            self._customFormat.endGroup()
        else:
            super(XSettings, self).endGroup()

    def load(self):
        """
        Loads the settings from disk for this XSettings object, if it is a custom format.
        """
        # load the custom format
        if self._customFormat and os.path.exists(self.fileName()):
            self._customFormat.load(self.fileName())

    def fileName(self):
        """
        Returns the filename.
        
        :return     <str>
        """
        if self._filename:
            return self._filename
        
        filename = nativestring(super(XSettings, self).fileName())
        if self._customFormat:
            filename, ext = os.path.splitext(filename)
            filename += '.' + self._customFormat.extension()
        return filename

    def remove(self, key):
        if self._customFormat:
            self._customFormat.remove(key)
        else:
            super(XSettings, self).remove(key)

    def setFileName(self, filename):
        """
        Sets the filename path for this settings instance.  If a blank string
        is provided, then the filename will be generated based on the
        default location information.
        
        :param      filename | <str>
        """
        self._filename = filename

    def setValue(self, key, value):
        """
        Sets the value for the given key to the inputed value.
        
        :param      key | <str>
                    value | <variant>
        """
        if self._customFormat:
            self._customFormat.setValue(key, value)
        else:
            super(XSettings, self).setValue(key, wrapVariant(value))

    def sync(self):
        """
        Syncs the information for this settings out to the file system.
        """
        if self._customFormat:
            self._customFormat.save(self.fileName())
        else:
            super(XSettings, self).sync()

    def value(self, key, default=None):
        """
        Returns the value for the given key for this settings instance.
        
        :return     <variant>
        """
        if self._customFormat:
            return self._customFormat.value(key, default)
        else:
            return unwrapVariant(super(XSettings, self).value(key))

    @staticmethod
    def registerFormat(extension, format):
        """
        Registers the given format class as an extension for this settings
        instance.
        
        :param      format | <XSettingsFormat>
        """
        setattr(XSettings, format.__name__, format)

XSettings.registerFormat('xml', XmlFormat)

if yaml is not None:
    XSettings.registerFormat('yaml', YamlFormat)