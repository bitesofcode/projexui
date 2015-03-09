#!/usr/bin/python

"""
Defines the XLocaleBox drop down widget for selecting locale based options.

This plugin requires the babel module to be installed.
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

import re
import logging

from projex.lazymodule import LazyModule
from projexui import resources
from xqt import QtGui, QtCore, wrapVariant
from .xcombobox import XComboBox

babel = LazyModule('babel')

log = logging.getLogger(__name__)

class XLocaleBox(XComboBox):
    __designer_icon__ = resources.find('img/flags/us.png')
    
    currentLocaleChanged = QtCore.Signal('QVariant')
    
    def __init__(self, parent=None):
        super(XLocaleBox, self).__init__(parent)
        
        # define custom properties
        self._allLocales = []
        self._dirty = True
        self._baseLocale = 'en_US'
        self._showLanguage = True
        self._showTerritory = True
        self._showScriptName = True
        self._translated = True
        self._availableLocales = [] # all locales

    def allLocales(self):
        """
        Returns all the locales that are defined within the babel
        architecture.
        
        :return     [<str>, ..]
        """
        if self._allLocales:
            return self._allLocales
        
        expr = re.compile('[a-z]+_[A-Z]+')
        locales = babel.core.localedata.locale_identifiers()
        babel_locales = {}
        for locale in locales:
            if expr.match(locale):
                babel_locale = babel.Locale.parse(locale)
                if babel_locale.territory and babel_locale.language:
                    babel_locales[babel_locale.territory] = babel_locale
        
        babel_locales = babel_locales.values()
        babel_locales.sort(key=str)
        self._allLocales = babel_locales
        return self._allLocales

    def availableLocales(self):
        """
        Returns a list of the available locales to use for displaying
        the locale information for.  This provides a way to filter the
        interface for only locales that you care about.
        
        :return     [<str>, ..]
        """
        return [str(locale) for locale in self._availableLocales]

    def baseLocale(self):
        """
        Returns the name to be used as the base name for the translation
        within the widget.  This will alter the language that is displaying
        the contents.
        
        :return     <str>
        """
        return self._baseLocale

    def currentLocale(self):
        """
        Returns the current locale for this box.
        
        :return     <babel.Locale> || None
        """
        try:
            return babel.Locale.parse(self.itemData(self.currentIndex()))
        except ImportError, err:
            log.error('babel is not installed.')
            return None

    def isTranslated(self):
        """
        Returns whether or not the locale will be translated.
        
        :return     <bool>
        """
        return self._translated

    def refresh(self):
        """
        Reloads the contents for this box based on the parameters.
        
        :return     <bool>
        """
        self.setDirty(False)
        self.blockSignals(True)
        self.setUpdatesEnabled(False)
        self.clear()
        
        locales = self._availableLocales
        if not locales:
            locales = self.allLocales()
        
        if not self.showLanguage():
            if self.isTranslated():
                sorter = lambda x: x.get_territory_name(base)
            else:
                sorter = lambda x: x.get_territory_name()
        else:
            if self.isTranslated():
                sorter = lambda x: x.get_language_name(base)
            else:
                sorter = lambda x: x.get_language_name()
        
        locales = sorted(locales, key=sorter)
        index = 0
        for i, locale in enumerate(locales):
            babel_locale = babel.Locale.parse(locale)
            code = '{0}_{1}'.format(babel_locale.language,
                                    babel_locale.territory)
            keys = {}
            if self.isTranslated():
                keys['lang'] = babel_locale.get_language_name(base)
                keys['territory'] = babel_locale.get_territory_name(base)
                keys['script'] = babel_locale.get_script_name(base)
            else:
                keys['lang'] = babel_locale.get_language_name()
                keys['territory'] = babel_locale.get_territory_name()
                keys['script'] = babel_locale.get_script_name()
            
            if self.showLanguage():
                opts = ''
                if self.showScriptName() and keys['script']:
                    opts += keys['script']
                if self.showTerritory() and keys['territory']:
                    if opts:
                        opts += ', '
                    opts += keys['territory']
                if opts:
                    opts = ' (' + opts + ')'
                
                label = keys['lang'] + opts
                
            elif self.showTerritory():
                label = keys['territory']
            else:
                label = code
            
            self.addItem(label)
            self.setItemData(i, wrapVariant(str(code)))
            
            name = babel_locale.territory.lower()
            ico = 'img/flags/{0}.png'.format(name)
            flag = QtGui.QIcon(resources.find(ico))
            if flag.isNull():
                ico = 'img/flags/_United Nations.png'
                flag = QtGui.QIcon(resources.find(ico))
            
            self.setItemIcon(i, flag)
            if code == self.baseLocale():
                index = i
        
        self.setCurrentIndex(index)
        self.setUpdatesEnabled(True)
        self.blockSignals(False)

    def showEvent(self, event):
        super(XLocaleBox, self).showEvent(event)
        
        if self._dirty:
            self.refresh()

    def setAvailableLocales(self, locales):
        """
        Sets a list of the available locales to use for displaying
        the locale information for.  This provides a way to filter the
        interface for only locales that you care about.
        
        :param     locales | [<str>, ..]
        """
        try:
            expr = re.compile('[a-z]+_[A-Z]+')
            babel_locales = []
            for locale in locales:
                if not expr.match(locale):
                    continue
                
                try:
                    babel_locale = babel.Locale.parse(str(locale))
                except (babel.UnknownLocaleError, StandardError):
                    continue
                
                if babel_locale.territory and babel_locale.language:
                    babel_locales.append(babel_locale)
            
            babel_locales.sort(key=str)
        except ImportError:
            babel_locales = []
        
        self._availableLocales = babel_locales
        self.setDirty()

    def setBaseLocale(self, locale):
        """
        Sets the base locale that is used with in this widget.  All displayed
        information will be translated to this locale.
        
        :param      locale | <str>
        """
        locale = str(locale)
        if self._baseLocale == locale:
            return
        
        try:
            babel.Locale.parse(locale)
        except (babel.UnknownLocaleError, StandardError):
            return False
        
        self._baseLocale = locale
        self.setCurrentLocale(locale)
        self.setDirty()
        return True

    def setCurrentLocale(self, locale):
        """
        Sets the current locale for this box to the inputed locale.
        
        :param      locale | <babel.Locale> || <str>
        
        :return     <bool>
        """
        locale = str(locale)
        for i in xrange(self.count()):
            if self.itemData(i) == locale:
                self.setCurrentIndex(i)
                return True
        return False

    def setDirty(self, state=True):
        self._dirty = state
        if state and self.isVisible():
            self.refresh()

    def setShowLanguage(self, state):
        """
        Sets the display mode for this widget to the inputed mode.
        
        :param      state | <bool>
        """
        if state == self._showLanguage:
            return
        
        self._showLanguage = state
        self.setDirty()

    def setShowScriptName(self, state):
        """
        Sets the display mode for this widget to the inputed mode.
        
        :param      state | <bool>
        """
        if state == self._showScriptName:
            return
        
        self._showScriptName = state
        self.setDirty()

    def setShowTerritory(self, state):
        """
        Sets the display mode for this widget to the inputed mode.
        
        :param      state | <bool>
        """
        if state == self._showTerritory:
            return
        
        self._showTerritory = state
        self.setDirty()

    def setTranslated(self, state):
        """
        Sets whether or not the locale will be translated.
        
        :param      state | <bool>
        """
        self._translated = state
        self.setDirty()

    def showLanguage(self):
        """
        Returns the display mode for this widget to the inputed mode.
        
        :return     <bool>
        """
        return self._showLanguage

    def showScriptName(self):
        """
        Returns the display mode for this widget to the inputed mode.
        
        :return     <bool>
        """
        return self._showScriptName

    def showTerritory(self):
        """
        Returns the display mode for this widget to the inputed mode.
        
        :return     <bool>
        """
        return self._showTerritory

    x_availableLocales = QtCore.Property('QStringList', availableLocales, setAvailableLocales)
    x_showLanguage = QtCore.Property(bool, showLanguage, setShowLanguage)
    x_showScriptName = QtCore.Property(bool, showScriptName, setShowScriptName)
    x_showTerritory = QtCore.Property(bool, showTerritory, setShowTerritory)
    x_baseLocale = QtCore.Property(str, baseLocale, setBaseLocale)
    x_translated = QtCore.Property(bool, isTranslated, setTranslated)

__designer_plugins__ = [XLocaleBox]

