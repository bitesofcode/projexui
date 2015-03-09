#!/usr/bin/python

""" Defines some additions the Qt Animation framework. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

from projexui.qt import wrapVariant, unwrapVariant
from projexui.qt.QtCore import QVariantAnimation

class XObjectAnimation(QVariantAnimation):
    """
    Defines a class that will generically call a python object's setter
    method.  It will accept any python object, with a string for the name
    of the method on the object to call when the value for the animation
    is updated.
    """
    def __init__(self, targetObject, setter, parent=None):
        super(XObjectAnimation, self).__init__(parent)
        
        self._targetObject = targetObject
        self._setter = setter

    def setTargetObject(self, targetObject):
        """
        Sets the target object that will be called for this object animation.
        
        :param      object | <variant>
        """
        self._targetObject = targetObject

    def targetObject(self):
        """
        Returns the object linked with this animation.
        
        :return     <variant>
        """
        return self._targetObject

    def updateCurrentValue(self, value):
        """
        Implementation of QAbstractAnimation's abstract method, called when
        the value is changed internally and is supposed to update the 
        python object's value.
        
        :param      value | <QVariant> || <variant>
        """
        try:
            method = getattr(self._targetObject, self._setter)
        except AttributeError:
            return
        
        try:
            method(unwrapVariant(value))
        except:
            return