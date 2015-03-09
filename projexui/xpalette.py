#!/usr/bin/python

""" Defines the root QGraphicsScene class for the node system. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

from xqt import QtGui

class XPaletteType(QtGui.QPalette.__class__):
    def __new__(mcs, name, bases, attrs):
        """
        Manages the creation of database model classes, reading
        through the creation attributes and generating table
        schemas based on the inputed information.  This class
        never needs to be expressly defined, as any class that
        inherits from the Table class will be passed through this
        as a constructor.
        
        :param      mcs         <TableBase>
        :param      name        <str>
        :param      bases       <tuple> (<object> base,)
        :param      attrs       <dict> properties
        
        :return     <type>
        """
        # determine if this is a definition, or a specific schema
        new_class = super(XPaletteType, mcs).__new__(mcs, name, bases, attrs)
        
        # add new custom roles
        curr = 50 + len(new_class.CustomRoles)
        custom = attrs.pop('__custom_roles__', [])
        for role in custom:
            if not role in new_class.CustomRoles:
                setattr(new_class, role, QtGui.QPalette.ColorRole(curr))
                curr += 1
        
        # update the global set of custom roles
        new_class.CustomRoles.update(custom)
        return new_class

#----------------------------------------------------------------------

class XPalette(QtGui.QPalette):
    """
    Subclass of the QPalette to support additional roles
    """
    __metaclass__ = XPaletteType
    
    CustomRoles = set()
    
    def __init__(self, *args):
        super(XPalette, self).__init__(*args)
        
        # initialize the custom color roles
        dc = QtGui.QColor()
        roles = self.CustomRoles
        self._custom = {
            QtGui.QPalette.Active:   {getattr(self, k): dc for k in roles},
            QtGui.QPalette.Inactive: {getattr(self, k): dc for k in roles},
            QtGui.QPalette.Disabled: {getattr(self, k): dc for k in roles},
        }

    def color(self, *args):
        # group, role
        if len(args) == 2:
            group, role = args
        else:
            group, role = QtGui.QPalette.Active, args[0]

        try:
            return self._custom[group][role]
        except KeyError:
            return super(XPalette, self).color(group, role)

    def setColor(self, *args):
        # group, role, color
        if len(args) == 3:
            group, role, color = args
        # role, color
        else:
            role, color = args
            group = QtGui.QPalette.Active
        
        if role in self._custom[group]:
            self._custom[group][role] = color
        else:
            super(XPalette, self).color(group, role)

