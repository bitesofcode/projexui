#!/usr/bin/python

"""
Defines the base chart item instance that can be used for plotting information.
"""

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2013, Projex Software'
__license__         = 'LGPL'

# maintenance information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

#------------------------------------------------------------------------------

import random

from projex.text import nativestring
from projexui.qt.QtGui import QColor

class XChartDataset(object):
    """ """
    def __init__(self, **options):
        # define custom properties
        self._name        = options.get('name', '')
        self._color       = QColor(options.get('color', self.randomColor()))
        self._colorMap    = {}
        self._plot        = options.get('plot', [])
        self._visible     = True
        self._dragData    = {}
    
    def __len__(self):
        return self.count()
    
    def color(self, key=None):
        """
        Returns the color for this data set.
        
        :return     <QColor>
        """
        if key is not None:
            return self._colorMap.get(nativestring(key), self._color)
        return self._color
    
    def count(self):
        """
        Returns the number of points for this data set.
        
        :return     <int>
        """
        return len(self._plot)
    
    def dragData(self, key=None, default=None):
        """
        Returns the drag data associated with this data set.  This will be 
        used when the user attempts to drag & drop a data set from the
        chart somewhere.  If no key is supplied, then the full data dictionary
        is returned.
        
        :param      key     | <str> || None
                    default | <variant>
        
        :return     (<variant> drag value, <dict> where values)
        """
        if key is None:
            return self._dragData
        
        return self._dragData.get(nativestring(key), default)
    
    def randomColor(self):
        """
        Returns a random color for this dataset.
        
        :return     <QColor>
        """
        return QColor(random.randint(90, 200),
                      random.randint(90, 200),
                      random.randint(90, 200))
    
    def isVisible(self):
        """
        Returns whether or not this dataset is visible.
        
        :return     <bool>
        """
        return self._visible
    
    def name(self):
        """
        Returns the name for this dataset to the inputed name.
        
        :return     <str>
        """
        return self._name
    
    def plot(self, **points):
        """
        Plots a given value at the given point.
        
        :param      **kwds | axis_name=value
        """
        self._plot.append(points)
    
    def setDragData(self, key, value):
        """
        Sets the drag data associated with this data set.  This will be 
        used when the user attempts to drag & drop a data set from the
        chart somewhere.  If no key is supplied, then the full data dictionary
        is returned.  The drag data key will be joined as:
        
            application/x-[key]
        
        :param      key     | <str> || None
                    value   | <variant>
        """
        self._dragData[nativestring(key)] = value
    
    def setColor(self, color, key=None):
        """
        Sets the color for this data set.
        
        :param      color | <QColor>
        """
        self._color = QColor(color)
        if key is not None:
            self._colorMap[nativestring(key)] = self._color
    
    def setName(self, name):
        """
        Sets the name for this dataset to the inputed name.
        
        :param      name | <str>
        """
        self._name = name
    
    def setVisible(self, state):
        """
        Sets whether or not this dataset item is visible or not.
        
        :param      state | <bool>
        """
        self._visible = state
    
    def sum(self, axis):
        """
        Returns the sum of the values for this dataset for the given axis.
        
        :param      axis | <XChartAxis>
        
        :return     <int>
        """
        return axis.sum(self.values(axis.name()))
    
    def values(self, axis=None):
        """
        Returns the values for this dataset.
        
        :return     [{<str> axis: <variant> value, ..}, ..]
        """
        if axis is None:
            return self._plot
        else:
            return [value.get(axis) for value in self._plot]