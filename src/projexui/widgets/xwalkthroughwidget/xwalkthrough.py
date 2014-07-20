#!/usr/bin/python

""" Creates reusable Qt widgets for various applications. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'


from xml.etree import ElementTree

#----------------------------------------------------------------------

class XWalkthroughProperty(object):
    def __init__(self, name='', value='', **attrib):
        self.__name = name
        self.__value = value
        self.__attrib = attrib

    def attributes(self):
        """
        Returns the attributes for this property.
        
        :return     <dict>
        """
        return self.__attrib

    def name(self):
        """
        Returns the name of this property.
        
        :return     <str>
        """
        return self.__name

    def setName(self, name):
        """
        Sets the name of this property to the inputed name.
        
        :param      name | <str>
        """
        self.__name = name

    def setValue(self, value):
        """
        Sets the value of this property to the inputed value.
        
        :param      value | <variant>
        """
        self.__value = value

    def value(self):
        """
        Returns the value for this property.
        
        :return     <variant>
        """
        return self.__value

#----------------------------------------------------------------------

class XWalkthroughItem(object):
    def __init__(self, **attrib):
        self.__attrib = attrib
        self.__properties = []
    
    def addProperty(self, prop):
        self.__properties.append(prop)
    
    def attributes(self):
        return self.__attrib
    
    def property(self, name):
        for prop in self.__properties:
            if prop.name() == name:
                return prop
        return None
    
    def properties(self):
        return self.__properties
    
    @staticmethod
    def fromXml(xml):
        item = XWalkthroughItem(**xml.attrib)
        
        # set hierarchy information
        for xprop in xml:
            item.addProperty(XWalkthroughProperty(xprop.tag,
                                                  xprop.text,
                                                  **xprop.attrib))
        
        return item

#------------------------------------------------------------------------------

class XWalkthroughSlide(object):
    def __init__(self, **attrib):
        self.__attrib = attrib
        self.__items = []
    
    def addItem(self, item):
        self.__items.append(item)
    
    def attributes(self):
        return self.__attrib
    
    def count(self):
        return len(self.__items)
    
    def itemAt(self, index):
        try:
            self.__items[index]
        except IndexError:
            return None
    
    def items(self):
        return self.__items
    
    def removeItem(self, item): 
        try:
            self.__items.remove(item)
        except ValueError:
            pass
    
    @staticmethod
    def fromXml(xml):
        """
        Creates a new slide from XML.
        
        :return     <XWalkthroughSlide>
        """
        slide = XWalkthroughSlide(**xml.attrib)
        
        # create the items
        for xgraphic in xml:
            slide.addItem(XWalkthroughItem.fromXml(xgraphic))
        
        return slide
    
#----------------------------------------------------------------------

class XWalkthrough(object):
    def __init__(self, name='', version='0.0'):
        self.__name = name
        self.__version = version
        self.__slides = []

    def addSlide(self, slide):
        """
        Adds a new slide to this walkthrough widget.
        
        :param      slide | <XWalkthroughSlide>
        """
        self.__slides.append(slide)

    def count(self):
        """
        Returns the number of slides associated with this walkthrough.
        
        :return     <int>
        """
        return len(self.__slides)

    def name(self):
        """
        Returns the walkthrough's name.
        
        :return     <str>
        """
        return self.__name

    def removeSlide(self, slide):
        """
        Removes the slide from this walkthrough.
        
        :param      slide | <XWalkthroughSlide>
        """
        try:
            self.__slides.remove(slide)
        except ValueError:
            pass

    def slideAt(self, index):
        """
        Returns the slide at the given index.
        
        :param      index | <int>
        
        :return     <XWalkthroughSlide> || None
        """
        try:
            return self.__slides[index]
        except IndexError:
            return None

    def slides(self):
        return self.__slides

    def version(self):
        """
        Returns the walkthrough's version.
        
        :return     <str>
        """
        return self.__version

    @staticmethod
    def load(xmlstr):
        """
        Loads the contents for this walkthrough from XML.
        
        :param      xmlstr | <str>
        
        :return     <XWalkthrough> || None
        """
        try:
            xml = ElementTree.fromstring(xmlstr)
        except StandardError:
            return None

        return XWalkthrough.fromXml(xml)

    @staticmethod
    def fromXml(xml):
        """
        Creates a new walkthrough element from XML
        
        :param      xml | <xml.etree.ElementTree.Element>
        
        :return     <XWalkthrough> || None
        """
        walkthrough = XWalkthrough(name=xml.get('name', ''),
                                   version=xml.get('version'))
        
        for xslide in xml:
            walkthrough.addSlide(XWalkthroughSlide.fromXml(xslide))
        
        return walkthrough


